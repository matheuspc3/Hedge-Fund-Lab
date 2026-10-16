"""Integração do participante LLM à camada experimental.

A correção causal e o comportamento de falha do participante pertencem a
``tests/agents/test_llm_participant.py``; aqui se prova a integração: registry,
identidade da spec, ausência de rede e o caminho ponta a ponta do runner.
"""

import json
from pathlib import Path

import pytest

from src.agents.participant import LLMParticipant
from src.experiments.participants import build_participant, required_tickers
from src.experiments.runner import DirtyRepositoryError, ExperimentRunner
from src.experiments.spec import (
    CostSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import DatasetSnapshot, SnapshotNotReadyError

TICKER = "PETR4.SA"

# Quorum pequeno e limites abertos: o E2E existe para provar a integração, não
# para calibrar o quorum — que continua não congelado.
LLM_PARAMS = {
    "ticker": TICKER,
    "provider": "mock",
    "analyst_count": 2,
    "consensus_threshold": 1.0,
    "risk_max_volatility": 100.0,
    # Frequência declarada explicitamente: ela é material e precisa aparecer no
    # spec_hash e no manifest. O valor aqui é técnico, não congelado.
    "decision_frequency": 5,
    # Sizing determinístico do caminho científico. Valor técnico: o alvo
    # definitivo é `TBD` no protocolo experimental v1.
    "long_target_weight": 0.25,
}
LLM = ParticipantSpec("llm_agent", LLM_PARAMS)


def spec_for(snapshot: DatasetSnapshot, participant: ParticipantSpec) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=participant,
        initial_capital=100_000.0,
        costs=CostSpec(brokerage_fixed=1.0, spread_bps=15.0, tax_rate=0.001),
        metrics=MetricSpec(),
    )


def runner_for(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    repository_dir: Path,
    *,
    participant: ParticipantSpec = LLM,
) -> ExperimentRunner:
    return ExperimentRunner(
        spec_for(snapshot, participant),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=repository_dir,
    )


# ── Registry ─────────────────────────────────────────────────────


def test_registry_resolve_llm_agent_sem_import_path() -> None:
    participant = build_participant(LLM)

    assert isinstance(participant, LLMParticipant)
    assert participant.ticker == TICKER
    # Single-asset: o universo do run é derivado do parâmetro, sem seleção
    # dinâmica dentro do participante.
    assert required_tickers(LLM) == (TICKER,)


def test_cada_run_recebe_uma_instancia_nova_sem_estado_compartilhado() -> None:
    first = build_participant(LLM)
    second = build_participant(LLM)

    assert first is not second
    assert first.graph is not second.graph  # type: ignore[attr-defined]
    assert first.client is not second.client  # type: ignore[attr-defined]

    first.decisions.append(None)  # type: ignore[attr-defined, arg-type]
    first._peak_equity = 123.0  # type: ignore[attr-defined]
    assert second.decisions == []  # type: ignore[attr-defined]
    assert second._peak_equity is None  # type: ignore[attr-defined]


def test_parametro_desconhecido_e_rejeitado_na_construcao() -> None:
    with pytest.raises(ValueError, match="invalid params"):
        build_participant(ParticipantSpec("llm_agent", {"ticker": TICKER, "seed": 7}))


def test_provider_real_exige_modelo_declarado() -> None:
    """Sem modelo explícito não há proveniência; o run não começa."""
    with pytest.raises(ValueError, match="requires an explicit model"):
        build_participant(
            ParticipantSpec(
                "llm_agent", {"ticker": TICKER, "provider": "agent_router"}
            )
        )


# ── Identidade da spec ───────────────────────────────────────────


@pytest.mark.parametrize(
    "override",
    [
        {"provider": "agent_router", "model": "openai/gpt-4o-mini"},
        {"model": "outro/modelo"},
        {"analyst_count": 7},
        {"consensus_threshold": 0.9},
        {"temperature_min": 0.4},
        {"temperature_max": 0.9},
        {"seed_base": 999},
        {"long_target_weight": 0.30},
        {"decision_frequency": 1},
        {"ticker": "VALE3.SA"},
    ],
    ids=[
        "provider",
        "model",
        "analyst_count",
        "consensus_threshold",
        "temperature_min",
        "temperature_max",
        "seed_base",
        "long_target_weight",
        "decision_frequency",
        "ticker",
    ],
)
def test_configuracao_material_do_llm_muda_o_spec_hash(
    snapshot: DatasetSnapshot, override: dict
) -> None:
    baseline = spec_for(snapshot, LLM)
    changed = spec_for(snapshot, ParticipantSpec("llm_agent", {**LLM_PARAMS, **override}))

    assert baseline.spec_hash != changed.spec_hash


def test_credencial_fica_fora_da_spec_e_nao_muda_o_spec_hash(
    snapshot: DatasetSnapshot, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chave é ambiente de execução, não parâmetro experimental."""
    spec = spec_for(snapshot, LLM)
    monkeypatch.setenv("LLM_API_KEY", "chave-a")
    first = spec.spec_hash
    monkeypatch.setenv("LLM_API_KEY", "chave-b")

    assert spec.spec_hash == first
    assert "LLM_API_KEY" not in json.dumps(spec.to_dict())
    assert "chave-" not in json.dumps(spec.to_dict())


def test_alvo_diferente_muda_o_spec_hash(snapshot: DatasetSnapshot) -> None:
    """``long_target_weight`` é configuração material: dois alvos, dois hashes.

    Sem isso, duas configurações que produzem carteiras diferentes se
    confundiriam no manifest e no diretório de runs.
    """
    hashes = {
        weight: spec_for(
            snapshot,
            ParticipantSpec("llm_agent", {**LLM_PARAMS, "long_target_weight": weight}),
        ).spec_hash
        for weight in (0.20, 0.30)
    }

    assert len(set(hashes.values())) == 2


def test_alvo_entra_na_spec_e_no_manifest(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    """Registrar não é congelar, mas o que governa a exposição tem de aparecer."""
    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    for block in (manifest["participant"], manifest["experiment_spec"]["participant"]):
        assert block["params"]["long_target_weight"] == 0.25


@pytest.mark.parametrize(
    "dead", ["kelly_fraction", "max_position_size", "portfolio_max_concentration", "payoff_ratio"]
)
def test_parametro_morto_de_kelly_nao_entra_na_spec_cientifica(dead: str) -> None:
    """Duas specs de comportamento idêntico não podem ter ``spec_hash`` diferente.

    Enquanto esses parâmetros existissem no ``llm_agent`` sem afetar nada, seria
    possível registrar como "configurações distintas" runs que decidem e
    executam exatamente igual. Recusá-los na construção fecha isso.
    """
    with pytest.raises(ValueError, match="invalid params"):
        build_participant(ParticipantSpec("llm_agent", {**LLM_PARAMS, dead: 0.5}))


@pytest.mark.parametrize(
    "weight", [0.0, -0.1, 1.5, 0.9], ids=["zero", "negativo", "acima_de_um", "acima_do_risco"]
)
def test_alvo_invalido_derruba_a_construcao_do_participante(weight: float) -> None:
    """Configuração inválida falha antes do run, não vira ``spec_hash``."""
    with pytest.raises(ValueError):
        build_participant(
            ParticipantSpec("llm_agent", {**LLM_PARAMS, "long_target_weight": weight})
        )


# ── Ponta a ponta pelo runner ────────────────────────────────────


def test_runner_executa_llm_com_mock_sem_tocar_a_rede(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O caminho inteiro roda offline: nem HTTP, nem download de dados."""

    def explode(*args, **kwargs):
        raise AssertionError("o run LLM não deve fazer chamada externa")

    monkeypatch.setattr("urllib.request.urlopen", explode)
    monkeypatch.setattr("yfinance.download", explode)
    monkeypatch.setattr(
        "src.pipeline.extract.DataExtractor.download", lambda *a, **k: explode()
    )

    result, path = runner_for(
        snapshot, snapshot_dir, runs_dir, tmp_path
    ).run_and_persist()

    assert result.universe == (TICKER,)
    assert result.final_equity > 0
    assert result.trades, "o mock determinístico precisa produzir operações"
    # Os trades vêm da arena: têm ticker, tipo derivado na abertura e custo do
    # CostModel da spec — nada disso é decidido pelo participante.
    assert {trade.ticker for trade in result.trades} == {TICKER}
    assert all(trade.type in {"BUY", "SELL"} for trade in result.trades)
    assert all(trade.cost > 0 for trade in result.trades)
    assert result.total_transaction_cost == pytest.approx(
        sum(trade.cost for trade in result.trades)
    )
    assert (path / "equity.csv").exists() and (path / "trades.csv").exists()


def test_manifest_registra_a_configuracao_do_llm_e_nenhum_segredo(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_API_KEY", "segredo-que-nao-pode-vazar")

    _, path = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run_and_persist()
    raw = (path / "manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(raw)

    assert manifest["participant"] == {"kind": "llm_agent", "params": LLM_PARAMS}
    params = manifest["experiment_spec"]["participant"]["params"]
    assert params["provider"] == "mock"
    assert params["decision_frequency"] == 5
    assert manifest["universe"] == [TICKER]
    assert "segredo-que-nao-pode-vazar" not in raw
    assert "LLM_API_KEY" not in raw
    assert "Authorization" not in raw


def test_metricas_do_run_llm_vem_da_implementacao_canonica(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    from src.backtesting.metrics import performance_metrics

    result = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run()

    assert dict(result.metrics) == performance_metrics(
        result.equity_curve, rf=0.0, mar=0.0, freq=252
    )


def test_run_llm_respeita_o_gate_cientifico_do_snapshot(
    incomplete_snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    with pytest.raises(SnapshotNotReadyError):
        runner_for(incomplete_snapshot, snapshot_dir, runs_dir, tmp_path).run()


def test_run_llm_respeita_o_guard_de_proveniencia_do_codigo(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prompts e agentes vivem no código; run sujo não é reproduzível."""
    import src.experiments.runner as runner_module

    monkeypatch.setattr(
        runner_module,
        "_git_metadata",
        lambda repository_dir: {"git_commit": "abc123", "git_dirty": True},
    )

    with pytest.raises(DirtyRepositoryError):
        runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run()


def test_dois_runs_da_mesma_spec_llm_sao_reproduziveis(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
) -> None:
    """Mock determinístico + participante novo por run = mesmo resultado."""
    first = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run()
    second = runner_for(snapshot, snapshot_dir, runs_dir, tmp_path).run()

    assert first.spec_hash == second.spec_hash
    assert first.run_id != second.run_id
    assert first.equity_curve.equals(second.equity_curve)
    assert [
        (str(trade.date), trade.type, trade.quantity, trade.price)
        for trade in first.trades
    ] == [
        (str(trade.date), trade.type, trade.quantity, trade.price)
        for trade in second.trades
    ]
