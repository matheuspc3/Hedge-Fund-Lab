"""A janela avaliada atravessando o runner: gates, evidência e manifest.

O snapshot da fixture cobre 2020-01-02 a 2020-03-31 pelo calendário da B3 e
serve, sozinho, a todos os casos abaixo — que é exatamente a propriedade
desejada: **um snapshot amplo, várias janelas**, sem duplicar dados.
"""

import json
from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from src.backtesting.arena import (
    QUANTITY_MODE_FRACTIONAL_NOTIONAL,
    EvaluationWindowError,
)
from src.experiments.context import RunContext
from src.experiments.runner import (
    RUN_MANIFEST_SCHEMA_VERSION,
    ExperimentRunner,
    MissingRunContextError,
)
from src.experiments.spec import (
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import DatasetSnapshot, load_snapshot_frames

BUY_AND_HOLD = ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"})
CAPITAL = 100_000.0
#: Toda fase científica declara a semântica de execução científica.
SCIENTIFIC_EXECUTION = ExecutionSpec(quantity_mode=QUANTITY_MODE_FRACTIONAL_NOTIONAL)
#: Contexto padrão dos cenários que não estão testando a fase em si.
CALIBRATION = RunContext("CALIBRATION")


def sessions_of(snapshot: DatasetSnapshot) -> pd.DatetimeIndex:
    """Calendário efetivo do ativo usado nos testes."""
    frames = load_snapshot_frames(snapshot, ("PETR4.SA",))
    return pd.DatetimeIndex(frames["PETR4.SA"].index)


def at(sessions: pd.DatetimeIndex, position: int) -> pd.Timestamp:
    """Sessão numa posição, já tipada como ``Timestamp``."""
    return cast(pd.Timestamp, sessions[position])


def day(sessions: pd.DatetimeIndex, position: int) -> str:
    """Data ISO da sessão numa posição do calendário."""
    return at(sessions, position).date().isoformat()


def spec_for(
    snapshot: DatasetSnapshot,
    *,
    decision_start: str,
    decision_end: str,
    minimum_history_sessions: int = 3,
) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
        execution=SCIENTIFIC_EXECUTION,
        evaluation=EvaluationSpec(
            decision_start=decision_start,
            decision_end=decision_end,
            minimum_history_sessions=minimum_history_sessions,
        ),
    )


def runner_for(
    spec: ExperimentSpec,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    *,
    context: RunContext | None = CALIBRATION,
) -> ExperimentRunner:
    return ExperimentRunner(
        spec,
        context=context,
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    )


# ── Phase obrigatória antes da execução ──────────────────────────


def test_run_cientifico_exige_fase_declarada(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Declarar a janela é declarar um experimento; ele precisa de fase."""
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    with pytest.raises(MissingRunContextError, match="protocol phase"):
        ExperimentRunner(
            spec,
            snapshot_dir=snapshot_dir,
            runs_dir=runs_dir,
            repository_dir=tmp_path,
        )


def test_fase_e_congelada_na_construcao_do_runner(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """``persist()`` não recebe fase: ela já existia antes de executar."""
    import inspect

    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    runner = runner_for(spec, snapshot_dir, runs_dir, tmp_path)

    assert runner.context == RunContext("CALIBRATION")
    persist_params = set(inspect.signature(runner.persist).parameters)
    assert persist_params == {"result"}


def test_modo_tecnico_legado_dispensa_fase(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Sem janela declarada nenhuma fase científica foi reivindicada."""
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
    )
    result = ExperimentRunner(
        spec,
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    ).run()

    assert result.context is None
    assert result.evaluation.explicit is False
    assert result.evaluation.warmup_sessions == 0


# ── Gates pré-run, antes do participante ─────────────────────────


def test_gate_de_warmup_falha_antes_de_construir_o_participante(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nenhuma chamada paga pode acontecer antes de a janela ser aprovada."""
    import src.experiments.runner as runner_module

    built: list[object] = []
    original = runner_module.build_participant

    def spy(spec):
        built.append(spec)
        return original(spec)

    monkeypatch.setattr(runner_module, "build_participant", spy)

    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 2),
        decision_end=day(sessions, 5),
        minimum_history_sessions=40,
    )
    with pytest.raises(EvaluationWindowError, match="minimum_history_sessions"):
        runner_for(spec, snapshot_dir, runs_dir, tmp_path).run()

    assert built == [], "o participante não pode ser construído com janela inválida"


def test_gate_de_settlement_falha_antes_de_construir_o_participante(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.experiments.runner as runner_module

    built: list[object] = []
    original = runner_module.build_participant
    monkeypatch.setattr(
        runner_module,
        "build_participant",
        lambda spec: (built.append(spec), original(spec))[1],
    )

    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, -1),
    )
    with pytest.raises(EvaluationWindowError, match="no settlement session"):
        runner_for(spec, snapshot_dir, runs_dir, tmp_path).run()

    assert built == []


def test_data_fora_do_calendario_falha_no_runner(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """2020-01-01 é feriado: a janela não é alinhada em silêncio."""
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start="2020-01-01",
        decision_end=day(sessions, 15),
        minimum_history_sessions=1,
    )
    with pytest.raises(EvaluationWindowError, match="is not a session shared"):
        runner_for(spec, snapshot_dir, runs_dir, tmp_path).run()


def test_nenhum_run_e_publicado_quando_a_janela_falha(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 2),
        decision_end=day(sessions, 5),
        minimum_history_sessions=40,
    )
    with pytest.raises(EvaluationWindowError):
        runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()

    assert not runs_dir.exists() or not list(runs_dir.iterdir())


# ── Sequential evaluation ────────────────────────────────────────


def test_curva_avaliada_cobre_janela_mais_settlement(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    result = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run()

    assert list(result.equity_curve.index) == list(sessions[10:17])
    assert result.equity_curve.iloc[0] == pytest.approx(CAPITAL)
    assert result.evaluation.evaluated_sessions == 6
    assert result.evaluation.settlement_session == at(sessions, 16)


def test_warmup_maior_nao_altera_metricas_da_mesma_janela(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Mesma janela sobre o mesmo snapshot: warm-up maior não estica nada.

    O ``minimum_history_sessions`` diferente muda o ``spec_hash``, como deve —
    o que precisa ficar idêntico é o resultado, porque o que foi avaliado é o
    mesmo. Dias anteriores não podem virar período, duração ou CAGR.
    """
    sessions = sessions_of(snapshot)
    window = {
        "decision_start": day(sessions, 30),
        "decision_end": day(sessions, 35),
    }
    short = runner_for(
        spec_for(snapshot, **window, minimum_history_sessions=5),
        snapshot_dir,
        runs_dir,
        tmp_path,
    ).run()
    long = runner_for(
        spec_for(snapshot, **window, minimum_history_sessions=25),
        snapshot_dir,
        runs_dir,
        tmp_path,
    ).run()

    assert short.spec_hash != long.spec_hash
    pd.testing.assert_series_equal(short.equity_curve, long.equity_curve)
    assert short.metrics == long.metrics
    assert len(short.equity_curve) == len(long.equity_curve)


# ── Calibration Anchor ───────────────────────────────────────────


def test_ancora_unica_produz_uma_decisao_e_um_settlement(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    sessions = sessions_of(snapshot)
    anchor = day(sessions, 20)
    spec = spec_for(snapshot, decision_start=anchor, decision_end=anchor)
    result, path = runner_for(
        spec,
        snapshot_dir,
        runs_dir,
        tmp_path,
        context=RunContext("CALIBRATION", "calibration-anchor-01"),
    ).run_and_persist()

    assert result.evaluation.evaluated_sessions == 1
    assert list(result.equity_curve.index) == [at(sessions, 20), at(sessions, 21)]
    # Buy & Hold decide comprar em close(t); a execução acontece em open(t+1).
    assert [pd.Timestamp(trade.date) for trade in result.trades] == [at(sessions, 21)]

    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_context"] == {
        "phase": "CALIBRATION",
        "case_id": "calibration-anchor-01",
    }


def test_ancoras_distintas_compartilham_o_snapshot_e_diferem_no_hash(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Vários Calibration Cases, um único snapshot — sem duplicar dados."""
    sessions = sessions_of(snapshot)
    results = []
    for index in (20, 25, 30):
        anchor = day(sessions, index)
        spec = spec_for(snapshot, decision_start=anchor, decision_end=anchor)
        results.append(
            runner_for(
                spec,
                snapshot_dir,
                runs_dir,
                tmp_path,
                context=RunContext("CALIBRATION", f"calibration-case-{index}"),
            ).run()
        )

    assert len({result.spec_hash for result in results}) == 3
    assert len({result.snapshot.identity_digest for result in results}) == 1


# ── Manifest ─────────────────────────────────────────────────────


def test_manifest_separa_configuracao_contexto_e_evidencia(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
        minimum_history_sessions=8,
    )
    _, path = runner_for(
        spec,
        snapshot_dir,
        runs_dir,
        tmp_path,
        context=RunContext("VALIDATION", "validation-01"),
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["schema_version"] == RUN_MANIFEST_SCHEMA_VERSION

    # Configuração pedida: dentro da spec, dentro do hash.
    assert manifest["experiment_spec"]["evaluation"] == {
        "decision_start": day(sessions, 10),
        "decision_end": day(sessions, 15),
        "minimum_history_sessions": 8,
    }

    # Contexto metodológico: fora do hash.
    assert manifest["run_context"] == {"phase": "VALIDATION", "case_id": "validation-01"}

    # Evidência realizada: derivada do calendário executado.
    evidence = manifest["evaluation_evidence"]
    assert evidence["data_start"] == day(sessions, 0)
    assert evidence["data_end"] == day(sessions, -1)
    assert evidence["first_decision_session"] == day(sessions, 10)
    assert evidence["last_decision_session"] == day(sessions, 15)
    assert evidence["settlement_session"] == day(sessions, 16)
    assert evidence["warmup_sessions"] == 10
    assert evidence["available_history_sessions"] == 11
    assert evidence["evaluated_sessions"] == 6
    assert evidence["warmup_calendar_days"] == (at(sessions, 10) - at(sessions, 0)).days


def test_manifest_distingue_warmup_de_periodo_avaliado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A cobertura do snapshot não pode mais ser lida como período avaliado."""
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    _, path = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    coverage_start = manifest["snapshot"]["effective_start"]
    evaluated_start = manifest["evaluation_evidence"]["first_decision_session"]
    assert coverage_start != evaluated_start
    assert manifest["evaluation_evidence"]["warmup_sessions"] > 0


def test_modo_legado_publica_evidencia_honesta(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Sem janela, a evidência descreve a cobertura inteira e diz que não há
    settlement — nada é inventado para preencher o schema."""
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
    )
    _, path = ExperimentRunner(
        spec,
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    sessions = sessions_of(snapshot)

    assert manifest["experiment_spec"]["evaluation"] is None
    assert manifest["run_context"] == {"phase": None, "case_id": None}
    evidence = manifest["evaluation_evidence"]
    assert evidence["settlement_session"] is None
    assert evidence["warmup_sessions"] == 0
    assert evidence["first_decision_session"] == day(sessions, 0)
    assert evidence["last_decision_session"] == day(sessions, -1)


# ── Invariantes internos da evidência publicada ──────────────────


def test_evidencia_do_manifest_e_internamente_coerente(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Cada campo parecer certo não basta: as relações entre eles são o teste.

    Ordenação completa da janela, mais as duas identidades contadas —
    ``available = warmup + 1`` e ``evaluated = |[start, end]|`` — sobre o
    calendário efetivamente executado.
    """
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 12),
        decision_end=day(sessions, 27),
        minimum_history_sessions=10,
    )
    result, path = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    evidence = manifest["evaluation_evidence"]

    data_start = evidence["data_start"]
    first = evidence["first_decision_session"]
    last = evidence["last_decision_session"]
    settlement = evidence["settlement_session"]
    data_end = evidence["data_end"]

    assert data_start <= first <= last < settlement <= data_end
    assert (
        evidence["available_history_sessions"] == evidence["warmup_sessions"] + 1 == 13
    )
    assert evidence["evaluated_sessions"] == 16
    assert evidence["warmup_calendar_days"] >= evidence["warmup_sessions"]

    # A evidência descreve o mesmo calendário que a curva publicada.
    assert first == day(sessions, 12)
    assert last == day(sessions, 27)
    assert settlement == day(sessions, 28)
    curve = cast(pd.DatetimeIndex, result.equity_curve.index)
    assert at(curve, 0).date().isoformat() == first
    assert at(curve, -1).date().isoformat() == settlement


def test_manifest_conta_pontos_de_curva_e_sessoes_avaliadas_separadamente(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """``equity_points`` inclui o settlement; ``evaluated_sessions`` não.

    Os dois números diferem por exatamente uma sessão, e é essa diferença que o
    nome antigo (``sessions``) escondia.
    """
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    result, path = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    evaluated = manifest["evaluation_evidence"]["evaluated_sessions"]
    assert manifest["equity_points"] == len(result.equity_curve) == evaluated + 1
    assert "sessions" not in manifest


def test_modo_legado_conta_a_cobertura_inteira_sem_settlement(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Sem janela não há ponto extra: a curva é a cobertura, e nada mais."""
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
    )
    _, path = ExperimentRunner(
        spec,
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["evaluation_evidence"]["settlement_session"] is None
    assert manifest["equity_points"] == (
        manifest["evaluation_evidence"]["evaluated_sessions"]
    )


# ── Settlement através do runner ─────────────────────────────────


def test_custo_da_ultima_decisao_entra_no_resultado_publicado(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A execução do settlement não pode ficar fora de custo, curva ou manifest."""
    from src.experiments.spec import CostSpec

    sessions = sessions_of(snapshot)
    anchor = day(sessions, 20)
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
        costs=CostSpec(brokerage_fixed=12.5),
        execution=SCIENTIFIC_EXECUTION,
        evaluation=EvaluationSpec(
            decision_start=anchor,
            decision_end=anchor,
            minimum_history_sessions=3,
        ),
    )
    result, path = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert pd.Timestamp(trade.date) == at(sessions, 21)
    assert trade.cost == pytest.approx(12.5)
    assert manifest["trade_count"] == 1
    assert manifest["total_transaction_cost"] == pytest.approx(12.5)
    assert manifest["final_equity"] == pytest.approx(result.final_equity)
    # O patrimônio final é o do settlement, já líquido do custo cobrado nele.
    assert result.final_equity != pytest.approx(CAPITAL)
    assert result.final_equity == pytest.approx(result.equity_curve.iloc[-1])

    published = pd.read_csv(path / "trades.csv")
    assert published["date"].tolist() == [day(sessions, 21)]
    assert published["cost"].tolist() == [pytest.approx(12.5)]


def test_ancora_sem_intent_publica_run_valido_sem_trade(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Manter posição é decisão legítima; não vira falha de settlement.

    ``bollinger`` sobre esta âncora decide manter: uma decisão acontece, nenhum
    intent é emitido e a sessão seguinte é processada normalmente.
    """
    sessions = sessions_of(snapshot)
    anchor = day(sessions, 20)
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=ParticipantSpec(
            "bollinger", {"ticker": "PETR4.SA", "window": 10, "k": 4.0}
        ),
        initial_capital=CAPITAL,
        execution=SCIENTIFIC_EXECUTION,
        evaluation=EvaluationSpec(
            decision_start=anchor,
            decision_end=anchor,
            minimum_history_sessions=3,
        ),
    )
    result, path = runner_for(spec, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert result.trades == []
    assert manifest["trade_count"] == 0
    assert manifest["total_transaction_cost"] == pytest.approx(0.0)
    assert manifest["evaluation_evidence"]["settlement_session"] == day(sessions, 21)
    assert manifest["equity_points"] == 2
    assert result.final_equity == pytest.approx(CAPITAL)


# ── Fase não pode ser escolhida depois do resultado ──────────────


def test_fase_publicada_vem_do_resultado_nao_do_runner_no_momento_de_publicar(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Trocar o rótulo do runner depois de ``run()`` não reclassifica o run.

    O fluxo perigoso é ``run() -> ver resultado -> escolher phase -> persist()``.
    Ele não existe: o manifest lê ``result.context``, congelado dentro de um
    ``RunResult`` imutável no instante da execução.
    """
    from dataclasses import FrozenInstanceError

    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    runner = runner_for(
        spec, snapshot_dir, runs_dir, tmp_path, context=RunContext("CALIBRATION")
    )
    result = runner.run()

    # O resultado já carrega a fase, e ela não é reatribuível.
    assert result.context == RunContext("CALIBRATION")
    with pytest.raises(FrozenInstanceError):
        result.context = RunContext("FINAL_TEST")  # type: ignore[misc]

    # Mesmo trocando o rótulo do runner, o publicado é o que foi executado.
    runner.context = RunContext("FINAL_TEST")
    path = runner.persist(result)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_context"] == {"phase": "CALIBRATION", "case_id": None}


def test_persist_nao_aceita_fase(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Nem por parâmetro nomeado, nem por posicional."""
    sessions = sessions_of(snapshot)
    spec = spec_for(
        snapshot,
        decision_start=day(sessions, 10),
        decision_end=day(sessions, 15),
    )
    runner = runner_for(spec, snapshot_dir, runs_dir, tmp_path)
    result = runner.run()

    with pytest.raises(TypeError):
        runner.persist(result, phase="FINAL_TEST")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        runner.persist(result, RunContext("FINAL_TEST"))  # type: ignore[call-arg]
