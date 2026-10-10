"""A semântica de execução como configuração material e como gate de fase."""

import json
from pathlib import Path

import pytest

from src.agents.features import LLM_FEATURE_SCHEMA_VERSION, LLM_NUMERIC_PRECISION
from src.backtesting.arena import (
    EXECUTION_SEMANTICS,
    QUANTITY_MODE_FRACTIONAL_NOTIONAL,
    QUANTITY_MODE_INTEGER_SHARES,
)
from src.experiments.context import RunContext
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import (
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import PRICE_REPRESENTATION, DatasetSnapshot

BUY_AND_HOLD = ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"})
CAPITAL = 100_000.0


def spec_for(snapshot: DatasetSnapshot, mode: str) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=BUY_AND_HOLD,
        initial_capital=CAPITAL,
        execution=ExecutionSpec(quantity_mode=mode),
        evaluation=EvaluationSpec(
            decision_start="2020-02-03",
            decision_end="2020-02-07",
            minimum_history_sessions=3,
        ),
    )


def test_fase_cientifica_recusa_quantidade_inteira(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """SCIENTIFIC MODE REQUIRED, e o gate é fail-closed antes de executar."""
    runner = ExperimentRunner(
        spec_for(snapshot, QUANTITY_MODE_INTEGER_SHARES),
        context=RunContext("CALIBRATION"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="requires quantity_mode"):
        runner.run()

    assert not runs_dir.exists() or list(runs_dir.iterdir()) == []


def test_modo_tecnico_legado_continua_aceitando_quantidade_inteira(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """Sem fase declarada não há reivindicação científica — e nada é recusado."""
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

    assert spec.execution.quantity_mode == QUANTITY_MODE_INTEGER_SHARES
    assert all(float(trade.quantity).is_integer() for trade in result.trades)


def test_modo_de_quantidade_e_material_para_o_spec_hash(
    snapshot: DatasetSnapshot,
) -> None:
    """Duas semânticas de execução não podem compartilhar identidade."""
    inteiro = spec_for(snapshot, QUANTITY_MODE_INTEGER_SHARES)
    fracionário = spec_for(snapshot, QUANTITY_MODE_FRACTIONAL_NOTIONAL)

    assert inteiro.spec_hash != fracionário.spec_hash
    assert inteiro.to_dict()["execution"] == {"quantity_mode": "integer_shares"}


def test_manifest_publica_semantica_de_execucao_e_contrato_do_provedor(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """O artefato diz com que modelo os números foram produzidos."""
    _, path = ExperimentRunner(
        spec_for(snapshot, QUANTITY_MODE_FRACTIONAL_NOTIONAL),
        context=RunContext("CALIBRATION"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    ).run_and_persist()
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["execution"] == {
        "quantity_mode": QUANTITY_MODE_FRACTIONAL_NOTIONAL,
        "semantics": EXECUTION_SEMANTICS,
        "price_representation": PRICE_REPRESENTATION,
    }
    assert manifest["llm_contract"] == {
        "feature_schema_version": LLM_FEATURE_SCHEMA_VERSION,
        "numeric_precision": LLM_NUMERIC_PRECISION,
    }
    assert manifest["experiment_spec"]["execution"]["quantity_mode"] == (
        QUANTITY_MODE_FRACTIONAL_NOTIONAL
    )


def test_execucao_cientifica_publica_quantidade_fracionaria(
    snapshot: DatasetSnapshot, snapshot_dir: Path, runs_dir: Path, tmp_path: Path
) -> None:
    """A quantidade publicada é a unidade sintética, não uma ação inteira."""
    result, path = ExperimentRunner(
        spec_for(snapshot, QUANTITY_MODE_FRACTIONAL_NOTIONAL),
        context=RunContext("CALIBRATION"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    ).run_and_persist()

    assert result.trades, "a janela precisa produzir ao menos um trade"
    assert not any(float(trade.quantity).is_integer() for trade in result.trades)
    linhas = (path / "trades.csv").read_text(encoding="utf-8").splitlines()
    assert linhas[0].split(",") == [
        "date",
        "ticker",
        "type",
        "price",
        "quantity",
        "cost",
    ]
    assert "." in linhas[1].split(",")[4]
