"""Âncoras CAL-A/CAL-B, grade de CAL-A e a tranca de CAL-B no runner."""

from pathlib import Path

import pandas as pd
import pytest

from src.experiments import anchors, runner as runner_module
from src.experiments.anchors import (
    ANCHOR_DOMAIN_COUNT,
    ANCHOR_DOMAIN_SHA256,
    ANCHOR_SNAPSHOT_ID,
    ANCHOR_WINDOW,
    CAL_A_ANCHORS,
    CAL_A_BASELINE,
    CAL_A_COMMITMENT_SHA256,
    CAL_A_GRID,
    CAL_B_ANCHORS,
    CAL_B_COMMITMENT_SHA256,
    STRATA,
    digest,
    require_cal_b_locked,
    strata_of,
)
from src.experiments.context import RunContext
from src.experiments.hardening import H_REAL_SESSIONS
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import (
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import (
    DatasetSnapshot,
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)


def test_estratos_contiguos_e_tao_iguais_quanto_possivel() -> None:
    assert len(STRATA) == 30
    assert sum(s.size for s in STRATA) == ANCHOR_DOMAIN_COUNT
    assert {s.size for s in STRATA} == {50, 51}
    assert [s.stratum_id for s in STRATA] == list(range(1, 31))
    for left, right in zip(STRATA, STRATA[1:]):
        assert left.last < right.first
    for stratum in STRATA:
        assert stratum.first <= stratum.anchor <= stratum.last


def test_cal_a_20_cal_b_10_disjuntos_e_comprometidos() -> None:
    assert len(CAL_A_ANCHORS) == 20 and len(CAL_B_ANCHORS) == 10
    assert not set(CAL_A_ANCHORS) & set(CAL_B_ANCHORS)
    assert [s.stratum_id for s in STRATA if s.subset == "CAL-B"] == list(range(3, 31, 3))
    assert digest(CAL_A_ANCHORS) == CAL_A_COMMITMENT_SHA256
    assert digest(CAL_B_ANCHORS) == CAL_B_COMMITMENT_SHA256
    assert not set(H_REAL_SESSIONS) & (set(CAL_A_ANCHORS) | set(CAL_B_ANCHORS))


SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "data" / "snapshots" / ANCHOR_SNAPSHOT_ID


@pytest.mark.skipif(not SNAPSHOT_DIR.exists(), reason="snapshot is local (git-ignored)")
def test_ancoras_reproduziveis_a_partir_do_snapshot() -> None:
    snapshot = load_dataset_snapshot(SNAPSHOT_DIR)
    verify_snapshot_integrity(snapshot)
    assert snapshot.scientific_ready
    frame = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"]
    low, high = (pd.Timestamp(day) for day in ANCHOR_WINDOW)
    domain = [
        str(session.date())
        for i, session in enumerate(frame.index)
        if low <= session <= high and i + 1 >= 504 and str(session.date()) not in H_REAL_SESSIONS
    ]
    assert digest(domain) == ANCHOR_DOMAIN_SHA256
    assert strata_of(domain) == STRATA


def test_grade_cal_a_e_o_produto_pre_declarado_com_baseline() -> None:
    assert [c["config_id"] for c in CAL_A_GRID] == [1, 2, 3, 4, 5, 6]
    pairs = {(c["volatility_window"], c["risk_max_volatility"]) for c in CAL_A_GRID}
    assert pairs == {(w, v) for w in (21, 63) for v in (0.40, 0.50, 0.60)}
    assert (CAL_A_BASELINE["volatility_window"], CAL_A_BASELINE["risk_max_volatility"]) in pairs


def test_cal_b_trancada() -> None:
    assert anchors.CAL_B_AUTHORIZED is False
    with pytest.raises(ValueError, match="locked CAL-B"):
        require_cal_b_locked(CAL_B_ANCHORS[0], CAL_B_ANCHORS[0])
    with pytest.raises(ValueError, match="locked CAL-B"):
        require_cal_b_locked("2018-01-01", "2024-12-31")
    require_cal_b_locked(CAL_A_ANCHORS[0], CAL_A_ANCHORS[0])


def test_runner_recusa_janela_com_ancora_de_cal_b_antes_de_construir(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index
    locked = str(sessions[30].date())
    monkeypatch.setattr(anchors, "CAL_B_ANCHORS", (locked,))

    def explode(*args, **kwargs):
        raise AssertionError("participant must not be built for a locked CAL-B window")

    monkeypatch.setattr(runner_module, "build_participant", explode)
    spec = ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"}),
        initial_capital=100_000.0,
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start=locked, decision_end=locked, minimum_history_sessions=3
        ),
    )
    runner = ExperimentRunner(
        spec,
        context=RunContext("CALIBRATION", "cal-b-premature"),
        snapshot_dir=snapshot_dir,
        runs_dir=runs_dir,
        repository_dir=tmp_path,
    )
    with pytest.raises(ValueError, match="locked CAL-B"):
        runner.run()
