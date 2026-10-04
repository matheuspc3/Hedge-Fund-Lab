"""no_order_execution_may_cross_phase_boundary e o calendário de fases."""

from pathlib import Path

import pytest

from src.backtesting.b3_calendar import B3Calendar
from src.experiments import phases, runner as runner_module
from src.experiments.anchors import CAL_A_ANCHORS, CAL_B_ANCHORS
from src.experiments.context import RunContext
from src.experiments.phases import (
    SEQUENTIAL_DEV_GRID,
    SEQUENTIAL_DEV_REPETITIONS,
    SEQUENTIAL_DEVELOPMENT_END,
    SEQUENTIAL_DEVELOPMENT_LAST_DECISION,
    SEQUENTIAL_DEVELOPMENT_START,
    VALIDATION_START,
    PhaseWindow,
    phase_of,
    require_execution_within_phase,
)
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import (
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import DatasetSnapshot, load_snapshot_frames


def test_janela_congelada_e_coerente_com_o_calendario_b3() -> None:
    import datetime as dt

    calendar = B3Calendar()
    end = dt.date.fromisoformat(SEQUENTIAL_DEVELOPMENT_END)
    last = dt.date.fromisoformat(SEQUENTIAL_DEVELOPMENT_LAST_DECISION)
    assert calendar.next_session(last) == end
    assert calendar.next_session(end).isoformat() == VALIDATION_START
    assert SEQUENTIAL_DEVELOPMENT_START == "2024-03-01"
    first = dt.date.fromisoformat(SEQUENTIAL_DEVELOPMENT_START)
    decisions = [first]
    while decisions[-1] < last:
        decisions.append(calendar.next_session(decisions[-1]))
    assert len(decisions) == 127


def test_cal_b_e_cal_a_nao_tocam_a_janela() -> None:
    """CAL-B ∩ SequentialDevelopmentWindow = ∅ (e CAL-A também fica fora)."""
    window = [a for a in (*CAL_A_ANCHORS, *CAL_B_ANCHORS)
              if SEQUENTIAL_DEVELOPMENT_START <= a <= SEQUENTIAL_DEVELOPMENT_END]
    assert window == []


def test_grade_congelada() -> None:
    assert [(c["name"], c["risk_max_drawdown"]) for c in SEQUENTIAL_DEV_GRID] == [
        ("D01", 0.25), ("D02", 0.15), ("D03", 0.35)
    ]
    assert SEQUENTIAL_DEV_REPETITIONS == 3


def test_decisao_na_ultima_sessao_da_fase_executaria_na_validation() -> None:
    phase = phase_of(SEQUENTIAL_DEVELOPMENT_START, SEQUENTIAL_DEVELOPMENT_END)
    assert phase is not None and phase.name == "SEQUENTIAL_DEVELOPMENT"
    with pytest.raises(ValueError, match="no_order_execution_may_cross_phase_boundary"):
        require_execution_within_phase(VALIDATION_START, phase)
    require_execution_within_phase(SEQUENTIAL_DEVELOPMENT_END, phase)


def test_janela_que_atravessa_a_fronteira_e_recusada() -> None:
    with pytest.raises(ValueError, match="crosses"):
        phase_of("2024-08-01", "2024-09-10")
    assert phase_of("2018-02-21", "2018-02-21") is None  # âncoras não são fase sequencial


def spec(snapshot: DatasetSnapshot, start: str, end: str) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=snapshot.snapshot_id,
        participant=ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"}),
        initial_capital=100_000.0,
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(decision_start=start, decision_end=end, minimum_history_sessions=3),
    )


def test_runner_aplica_a_fronteira_e_nao_ve_dado_depois_da_fase(
    snapshot: DatasetSnapshot,
    snapshot_dir: Path,
    runs_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index
    start, phase_end = (str(sessions[i].date()) for i in (20, 30))
    monkeypatch.setattr(phases, "PHASES", (PhaseWindow("TEST_PHASE", start, phase_end),))

    def runner(end: str) -> ExperimentRunner:
        return ExperimentRunner(
            spec(snapshot, start, end),
            context=RunContext("CALIBRATION", "phase-boundary-test"),
            snapshot_dir=snapshot_dir,
            runs_dir=runs_dir,
            repository_dir=tmp_path,
            allow_dirty=True,
        )

    built: list[object] = []
    real_build = runner_module.build_participant
    monkeypatch.setattr(
        runner_module, "build_participant", lambda s: built.append(s) or real_build(s)
    )
    with pytest.raises(ValueError, match="no_order_execution_may_cross_phase_boundary"):
        runner(phase_end).run()
    assert built == []  # recusado antes de construir o participante

    result = runner(str(sessions[29].date())).run()
    assert result.evaluation.settlement_session == sessions[30]
    assert result.evaluation.data_end <= sessions[30]  # nada depois da fase chega ao motor
    assert result.equity_curve.index[-1] == sessions[30]
