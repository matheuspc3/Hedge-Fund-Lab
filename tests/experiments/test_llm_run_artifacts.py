"""Publicação da evidência de LLM junto do run científico.

O conteúdo de um registro e as regras de replay são provados em
``tests/agents/test_llm_trace.py``. Aqui se prova a integração com o runner: o
artefato existe no diretório do run, o manifest permite conferi-lo, os
clássicos continuam sem nada disso, e o run publicado é replayável sem rede.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from src.agents.llm_trace import (
    LLM_TRACE_FILENAME,
    LLM_TRACE_SCHEMA_VERSION,
    ReplayLLMClient,
)
from src.agents.participant import LLMParticipant
from src.backtesting.arena import ExecutionEngine
from src.backtesting.metrics import performance_metrics
from src.experiments.runner import ExperimentRunner, RunResult
from src.experiments.spec import CostSpec, ExperimentSpec, MetricSpec, ParticipantSpec
from src.pipeline.snapshot import DatasetSnapshot, load_snapshot_frames

TICKER = "PETR4.SA"

#: Mesma configuração técnica de ``test_llm_runner``: quorum pequeno e limites
#: abertos porque o alvo é a integração, não a calibração — que continua não
#: congelada.
LLM_PARAMS: dict[str, Any] = {
    "ticker": TICKER,
    "provider": "mock",
    "analyst_count": 2,
    "consensus_threshold": 1.0,
    "risk_max_volatility": 100.0,
    "decision_frequency": 5,
    "long_target_weight": 0.25,
}
LLM = ParticipantSpec("llm_agent", LLM_PARAMS)


def runner_for(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    repository_dir: Path,
    *,
    participant: ParticipantSpec = LLM,
) -> ExperimentRunner:
    return ExperimentRunner(
        ExperimentSpec(
            snapshot_id=snapshot.snapshot_id,
            participant=participant,
            initial_capital=100_000.0,
            costs=CostSpec(brokerage_fixed=1.0, spread_bps=15.0, tax_rate=0.001),
            metrics=MetricSpec(),
        ),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=repository_dir,
    )


def read_trace(path: Path) -> list[dict[str, Any]]:
    raw = (path / LLM_TRACE_FILENAME).read_text(encoding="utf-8")
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def eligible_sessions(result: RunResult) -> set[str]:
    """Sessões em que o participante pôde decidir, dado ``decision_frequency``."""
    frequency = int(LLM_PARAMS["decision_frequency"])
    return {
        str(pd.Timestamp(session).date())
        for index, session in enumerate(result.equity_curve.index)
        if index % frequency == 0
    }


# ── Publicação ───────────────────────────────────────────────────


def test_run_llm_publica_o_trace_ao_lado_da_curva_e_dos_trades(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A evidência sai do participante e vira artefato do diretório do run."""
    result, path = runner_for(
        snapshot, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert sorted(item.name for item in path.iterdir()) == [
        "equity.csv",
        LLM_TRACE_FILENAME,
        "manifest.json",
        "trades.csv",
    ]
    calls = read_trace(path)
    assert calls, "um run LLM com sessões elegíveis precisa registrar chamadas"
    assert {call["schema_version"] for call in calls} == {LLM_TRACE_SCHEMA_VERSION}
    assert {call["provider"] for call in calls} == {"mock"}
    assert {call["stage"] for call in calls} <= {
        "technical_analyst",
        "risk_manager",
        "portfolio_manager",
    }
    # Nenhuma chamada aparece fora de uma sessão em que decidir era permitido.
    assert {call["decision_session"] for call in calls} <= eligible_sessions(result)
    # Identidade sem ambiguidade: um call_id por chamada, sequência densa.
    assert len({call["call_id"] for call in calls}) == len(calls)
    assert [call["sequence"] for call in calls] == list(range(len(calls)))


def test_manifest_registra_caminho_versao_contagem_e_sha_do_trace(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Integridade conferível: o SHA é dos bytes efetivamente publicados."""
    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    entry = manifest["participant_artifacts"]["llm_calls"]
    published = (path / LLM_TRACE_FILENAME).read_bytes()
    assert entry["path"] == LLM_TRACE_FILENAME
    assert entry["schema_version"] == LLM_TRACE_SCHEMA_VERSION
    assert entry["call_count"] == len(read_trace(path))
    assert entry["sha256"] == hashlib.sha256(published).hexdigest()
    assert entry["bytes"] == len(published)
    # Contratos independentes: a versão do trace descreve o artefato e a do
    # manifest descreve o run; as duas evoluem em separado.
    assert manifest["schema_version"] >= 3


def test_trace_adulterado_depois_do_run_nao_confere_mais_com_o_manifest(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Manifest íntegro com artefato alterado é um estado detectável."""
    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    recorded = manifest["participant_artifacts"]["llm_calls"]["sha256"]
    target = path / LLM_TRACE_FILENAME
    assert hashlib.sha256(target.read_bytes()).hexdigest() == recorded

    target.write_bytes(target.read_bytes().replace(b"COMPRA", b"VENDA", 1))

    assert hashlib.sha256(target.read_bytes()).hexdigest() != recorded


def test_trace_publicado_nao_contem_segredo(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "sk-segredo-do-run")

    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    raw = (path / LLM_TRACE_FILENAME).read_text(encoding="utf-8")

    for forbidden in ("sk-segredo-do-run", "LLM_API_KEY", "Authorization", "Bearer"):
        assert forbidden not in raw


def test_trace_e_congelado_na_execucao_e_nao_reconsultado_ao_publicar(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """``persist()`` escreve a evidência capturada, não o estado posterior.

    Mesma regra do ``SnapshotEvidence``: o resultado já carrega os bytes, e
    publicar não volta a perguntar nada ao participante nem ao provedor.
    """
    runner = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path)
    result = runner.run()
    (artifact,) = result.artifacts
    frozen = artifact.content

    path = runner.persist(result)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert (path / LLM_TRACE_FILENAME).read_bytes() == frozen
    assert manifest["participant_artifacts"]["llm_calls"]["sha256"] == (
        hashlib.sha256(frozen).hexdigest()
    )


def test_estagio_de_portfolio_grava_o_schema_qualitativo(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """O estágio continua sendo ``portfolio_manager``; o contrato é que mudou.

    A identidade da chamada inclui ``response_schema_sha256``, então trocar
    ``FinalDecision`` por ``PortfolioAction`` muda a identidade — e é isso que
    se quer: são perguntas diferentes feitas ao provedor. Traces gravados com o
    schema antigo deixam de casar, o que é o comportamento correto, não uma
    regressão a ser contornada.
    """
    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()

    portfolio = [
        call for call in read_trace(path) if call["stage"] == "portfolio_manager"
    ]
    assert portfolio, "o cenário precisa chegar ao gestor de portfólio"
    assert {call["response_schema"] for call in portfolio} == {"PortfolioAction"}
    assert all(call["response_schema_sha256"] for call in portfolio)
    for call in portfolio:
        # Nenhuma quantidade financeira pedida, devolvida ou registrada.
        assert set(call["validated_response"]) == {"decision", "reasoning"}
        assert "position_size" not in call["user_prompt"]
        assert "max_position_size" not in call["user_prompt"]


def test_confidence_continua_auditavel_no_trace(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Tirar ``confidence`` do sizing não é apagá-la da evidência.

    Ela continua sendo saída do analista, continua no trace e continua
    disponível para calibração futura e análise — apenas não governa exposição.
    """
    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()

    technical = [
        call for call in read_trace(path) if call["stage"] == "technical_analyst"
    ]
    assert technical
    assert all("confidence" in call["validated_response"] for call in technical)


# ── Clássicos ────────────────────────────────────────────────────


@pytest.mark.parametrize("kind", ["sma_cross", "buy_and_hold", "bollinger"])
def test_classicos_nao_produzem_trace_nem_dependem_dessa_infraestrutura(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    kind: str,
) -> None:
    """Quem não implementa o contrato segue publicando exatamente o de sempre."""
    result, path = runner_for(
        snapshot,
        snapshot_dir,
        runs_dir,
        tmp_path,
        participant=ParticipantSpec(kind, {"ticker": TICKER}),
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.artifacts == ()
    assert manifest["participant_artifacts"] == {}
    assert not (path / LLM_TRACE_FILENAME).exists()
    assert sorted(item.name for item in path.iterdir()) == [
        "equity.csv",
        "manifest.json",
        "trades.csv",
    ]


# ── Replay do run publicado ──────────────────────────────────────


def test_replay_do_run_publicado_reproduz_decisoes_trades_equity_e_metricas(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RUN A grava; RUN B reexecuta a arena lendo o trace publicado, sem rede.

    Esta é a garantia forte de reprodução do projeto. Não é "mesma spec, mesma
    resposta do provedor" — que nenhum provedor externo promete — e sim "mesmo
    trace, mesmas decisões, mesmo resultado financeiro".
    """
    live_result, path = runner_for(
        snapshot, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()
    trace = (path / LLM_TRACE_FILENAME).read_bytes()

    def explode(*args: Any, **kwargs: Any):
        raise AssertionError("o replay não deve fazer chamada externa")

    monkeypatch.setattr("urllib.request.urlopen", explode)
    monkeypatch.setattr("urllib.request.Request", explode)
    monkeypatch.setattr("socket.create_connection", explode)
    monkeypatch.setattr("yfinance.download", explode)

    replay_client = ReplayLLMClient.from_trace(trace, provider="mock", requested_model="")
    replayed = LLMParticipant(
        llm_client=replay_client,
        **{key: value for key, value in LLM_PARAMS.items() if key != "provider"},
    )
    replay_result = ExecutionEngine(
        replayed,
        load_snapshot_frames(snapshot, (TICKER,)),
        live_result.initial_capital,
        live_result.spec.costs.build(),
    ).run()
    # Completeness: o trace foi consumido inteiro, nada sobrou.
    replay_client.assert_complete()

    assert live_result.equity_curve.equals(replay_result.equity_curve)
    assert [
        (str(trade.date), trade.ticker, trade.type, trade.quantity, trade.price)
        for trade in live_result.trades
    ] == [
        (str(trade.date), trade.ticker, trade.type, trade.quantity, trade.price)
        for trade in replay_result.trades
    ]
    assert live_result.trades, "o cenário precisa produzir operações"
    assert dict(live_result.metrics) == performance_metrics(
        replay_result.equity_curve,
        rf=live_result.spec.metrics.risk_free_rate,
        mar=live_result.spec.metrics.mar,
        freq=live_result.spec.metrics.periods_per_year,
    )
    assert replay_client.consumed == len(replay_client.records)
