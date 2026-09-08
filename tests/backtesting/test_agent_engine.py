import json

import pandas as pd
import pytest

from src.agents.graph import build_graph
from src.agents.llm_client import MockLLMClient
from src.agents.state import FinalDecision, RiskVerdict, TechnicalSignal
from src.agents.technical_analyst import AnalystEnsembleConfig
from src.backtesting.agent_engine import AgentBacktestEngine
from src.backtesting.costs import CostModel


class RecordingDecisionGraph:
    def __init__(self, decision="COMPRA", position_size=1.0):
        self.calls = []
        self.final_decision = FinalDecision(
            decision=decision,
            position_size=position_size,
            reasoning="decisão determinística",
        )

    async def ainvoke(self, state):
        self.calls.append(state)
        return {"final_decision": self.final_decision, "errors": []}


def market_data():
    dates = pd.bdate_range("2025-01-02", periods=4)
    return pd.DataFrame(
        {
            "abertura": [90.0, 91.0, 92.0, 77.0],
            "fechamento": [100.0, 101.0, 102.0, 103.0],
            "sma_50": [99.0, 99.5, 100.0, 100.5],
            "sma_200": [95.0, 95.0, 95.0, 95.0],
        },
        index=dates,
    )


def graph_for(signal="COMPRA", position_size=1.0):
    llm = MockLLMClient(
        {
            TechnicalSignal: {
                "signal": signal,
                "justification": "consenso",
                "confidence": 0.8,
            },
            RiskVerdict: {
                "verdict": "APROVADO",
                "analysis": "risco normal",
                "risk_metrics": {},
            },
            FinalDecision: {
                "decision": signal,
                "position_size": position_size,
                "reasoning": "executar",
            },
        }
    )
    return build_graph(
        llm,
        ensemble_config=AnalystEnsembleConfig(analyst_count=3, consensus_threshold=2 / 3),
    )


def test_agent_backtest_executes_next_day_open_with_costs():
    data = market_data()
    costs = CostModel(brokerage_fixed=1.0, spread_bps=10.0)
    result = AgentBacktestEngine(
        graph_for(),
        data,
        "WEGE3.SA",
        cost_model=costs,
        volatility_window=2,
    ).run()

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.date == data.index[3]
    assert trade.price == 77.0
    assert trade.cost == pytest.approx(costs.apply_buy(trade.price * trade.quantity))
    approved = [d for d in result.decisions if d.final_decision is not None]
    assert approved[-1].decision_date == data.index[2]
    assert approved[-1].target_session == data.index[3]
    assert approved[-1].status == "EXECUTED"
    assert approved[-1].execution_date == data.index[3]
    assert approved[-1].execution_price == 77.0
    assert len(approved[-1].technical_votes) == 3
    assert result.final_equity == result.equity_curve.iloc[-1]
    assert len(result.returns) == len(data) - 1


def test_agent_backtest_exports_complete_audit(tmp_path):
    result = AgentBacktestEngine(
        graph_for(), market_data(), "WEGE3.SA", volatility_window=2
    ).run()
    path = result.save_audit(tmp_path / "audit" / "run.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["trades"][0]["date"] == "2025-01-07"
    assert len(payload["decisions"][-1]["technical_votes"]) == 3
    executed = next(
        decision for decision in payload["decisions"] if decision["status"] == "EXECUTED"
    )
    assert executed["as_of"] == "2025-01-06"
    assert executed["target_session"] == "2025-01-07"
    assert executed["execution_date"] == "2025-01-07"
    assert executed["execution_price"] == 77.0
    assert payload["decisions"][-1]["execution_date"] is None


def test_agent_backtest_targets_next_observed_session_without_future_data():
    dates = pd.to_datetime(["2025-01-03", "2025-01-06"])
    data = pd.DataFrame(
        {"abertura": [99.0, 77.0], "fechamento": [100.0, 999.0]},
        index=dates,
    )
    graph = RecordingDecisionGraph()

    result = AgentBacktestEngine(graph, data, "X").run()

    executed, pending = result.decisions
    assert graph.calls[0]["date"] == "2025-01-03"
    assert graph.calls[0]["current_price"] == 100.0
    assert executed.target_session == pd.Timestamp("2025-01-06")
    assert executed.execution_date == pd.Timestamp("2025-01-06")
    assert executed.execution_price == 77.0
    assert executed.status == "EXECUTED"
    assert pending.decision_date == pd.Timestamp("2025-01-06")
    assert pending.target_session is None
    assert pending.execution_date is None
    assert pending.execution_price is None
    assert pending.status == "PREDICTED"


def test_last_prediction_is_pending_and_excluded_from_performance():
    data = market_data().tail(1)
    result = AgentBacktestEngine(
        RecordingDecisionGraph(), data, "X", initial_capital=1_000.0
    ).run()

    assert not result.trades
    assert result.final_equity == 1_000.0
    assert result.decisions[0].status == "PREDICTED"
    assert result.decisions[0].target_session is None
    assert result.decisions[0].execution_date is None


def test_keep_decision_is_completed_without_creating_an_order():
    result = AgentBacktestEngine(
        RecordingDecisionGraph("MANTER", 0.0), market_data().tail(1), "X"
    ).run()

    assert not result.trades
    assert result.decisions[0].status == "NO_ACTION"
    assert result.decisions[0].target_session is None


def test_agent_backtest_sell_uses_fraction_of_existing_position():
    engine = AgentBacktestEngine(graph_for("VENDA", 0.4), market_data(), "WEGE3.SA")
    cash, remaining, trade = engine._sell(0.0, 10, 50.0, 0.4)
    assert remaining == 6
    assert trade.quantity == 4
    assert cash == 200.0

    cash, remaining, trade = engine._sell(0.0, 1, 50.0, 0.4)
    assert (cash, remaining, trade) == (0.0, 1, None)


def test_agent_backtest_ignores_orders_too_small_for_one_share():
    engine = AgentBacktestEngine(graph_for(), market_data(), "X")
    cash, quantity, trade = engine._buy(100.0, 100.0, 0.001)
    assert (cash, quantity, trade) == (100.0, 0, None)


def test_agent_backtest_processes_sell_decision_without_existing_position():
    result = AgentBacktestEngine(
        graph_for("VENDA", 1.0),
        market_data(),
        "WEGE3.SA",
        volatility_window=2,
    ).run()
    assert not result.trades
    assert any(
        decision.final_decision and decision.final_decision.decision == "VENDA"
        for decision in result.decisions
    )
    assert any(decision.status == "REJECTED" for decision in result.decisions)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"data": pd.DataFrame()},
        {"data": pd.DataFrame({"fechamento": [1.0]})},
        {"initial_capital": 0},
        {"volatility_window": 1},
    ],
)
def test_agent_backtest_rejects_invalid_configuration(kwargs):
    params = {"graph": graph_for(), "data": market_data(), "ticker": "X"}
    params.update(kwargs)
    with pytest.raises(ValueError):
        AgentBacktestEngine(**params)


def test_agent_backtest_requires_sorted_unique_dates():
    data = market_data().iloc[::-1]
    with pytest.raises(ValueError, match="sorted and unique"):
        AgentBacktestEngine(graph_for(), data, "X")
