import json
from datetime import date

import pandas as pd
import pytest

from src.agents.state import FinalDecision
from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.daily_agent import DailyAgentRunner, DailyAgentState


class RecordingGraph:
    def __init__(self, decision="COMPRA", position_size=0.5):
        self.calls = []
        self.decision = FinalDecision(
            decision=decision,
            position_size=position_size,
            reasoning="decisão diária determinística",
        )

    async def ainvoke(self, state):
        self.calls.append(state)
        return {"final_decision": self.decision, "errors": []}


def daily_data():
    return pd.DataFrame(
        {
            "abertura": [99.0, 100.0, 50.0],
            "fechamento": [100.0, 100.0, 55.0],
            "sma_50": [98.0, 99.0, 100.0],
        },
        index=pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06"]),
    )


def test_b3_calendar_handles_weekends_holidays_and_special_sessions():
    calendar = B3Calendar()

    assert calendar.next_session(date(2025, 1, 3)) == date(2025, 1, 6)
    assert calendar.next_session(date(2026, 2, 13)) == date(2026, 2, 18)
    assert calendar.is_session(date(2026, 7, 9))
    assert calendar.next_session(date(2026, 11, 19)) == date(2026, 11, 23)
    assert calendar.next_session(date(2026, 12, 23)) == date(2026, 12, 28)


def test_daily_runner_persists_executes_and_is_idempotent(tmp_path):
    graph = RecordingGraph()
    state_path = tmp_path / "daily.json"
    runner = DailyAgentRunner(
        graph,
        "X",
        state_path,
        initial_capital=1_000.0,
    )

    first = runner.run(daily_data().iloc[:2])

    assert first.advanced
    assert first.state.last_session == pd.Timestamp("2025-01-03")
    assert first.expected_session == pd.Timestamp("2025-01-06")
    assert first.state.pending_decision.status == "PREDICTED"
    assert first.state.pending_decision.target_session == pd.Timestamp("2025-01-06")
    assert graph.calls[0]["current_price"] == 100.0
    assert state_path.exists()
    assert not state_path.with_suffix(".json.tmp").exists()
    assert not state_path.with_suffix(".json.lock").exists()

    second = runner.run(daily_data())

    executed, pending = second.state.decisions
    assert second.advanced
    assert executed.status == "EXECUTED"
    assert executed.execution_date == pd.Timestamp("2025-01-06")
    assert executed.execution_price == 50.0
    assert second.state.cash == 500.0
    assert second.state.position == 10
    assert second.state.equity_curve[-1]["equity"] == 1_050.0
    assert pending.status == "PREDICTED"
    assert pending.target_session == pd.Timestamp("2025-01-07")
    assert graph.calls[1]["cash"] == 500.0
    assert graph.calls[1]["position"] == 10.0

    third = runner.run(daily_data())

    assert not third.advanced
    assert third.expected_session == pd.Timestamp("2025-01-07")
    assert len(graph.calls) == 2
    assert len(third.state.decisions) == 2
    assert len(third.state.trades) == 1

    reloaded = DailyAgentState.load(state_path)
    assert reloaded.cash == 500.0
    assert reloaded.pending_decision.target_session == pd.Timestamp("2025-01-07")
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["costs"]["spread_bps"] == 0.0


def test_daily_runner_advances_after_no_action_without_trade(tmp_path):
    runner = DailyAgentRunner(
        RecordingGraph("MANTER", 0.0),
        "X",
        tmp_path / "daily.json",
    )

    first = runner.run(daily_data().iloc[:2])
    second = runner.run(daily_data())

    assert first.state.decisions[0].status == "NO_ACTION"
    assert second.advanced
    assert len(second.state.decisions) == 2
    assert not second.state.trades


def test_daily_runner_rejects_a_gap_in_the_expected_session(tmp_path):
    runner = DailyAgentRunner(
        RecordingGraph(),
        "X",
        tmp_path / "daily.json",
    )
    runner.run(daily_data().iloc[:2])
    data_with_gap = daily_data().iloc[[0, 1]].copy()
    data_with_gap.loc[pd.Timestamp("2025-01-07")] = [101.0, 102.0, 100.0]

    with pytest.raises(ValueError, match="missing expected B3 session"):
        runner.run(data_with_gap)
