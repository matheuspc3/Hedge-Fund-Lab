"""Módulo de backtesting — motor, métricas, custos e portfólio multi-ativo."""

from src.backtesting.agent_engine import (
    AgentBacktestEngine,
    AgentBacktestResult,
    AgentDecisionRecord,
)
from src.backtesting.arena import (
    ExecutionEngine,
    MarketObservation,
    OrderIntent,
    Participant,
)
from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.costs import CostModel
from src.backtesting.daily_agent import (
    DailyAgentRunner,
    DailyAgentState,
    DailyRunOutcome,
)
from src.backtesting.engine import BacktestEngine, BacktestResult, Trade
from src.backtesting.metrics import (
    annualized_return,
    annualized_volatility,
    calmar_ratio,
    cumulative_return,
    drawdown_series,
    max_drawdown,
    max_drawdown_duration,
    performance_metrics,
    periodic_returns,
    sharpe_ratio,
    sortino_ratio,
    total_return,
    total_transaction_cost,
    turnover,
    validate_equity_curve,
)
from src.backtesting.portfolio import (
    EqualWeightPortfolio,
    MinVariancePortfolio,
    PortfolioBacktestEngine,
    PortfolioBacktestResult,
    PortfolioStrategy,
    PortfolioTrade,
)

__all__ = [
    "AgentBacktestEngine",
    "AgentBacktestResult",
    "AgentDecisionRecord",
    "B3Calendar",
    "BacktestEngine",
    "BacktestResult",
    "CostModel",
    "DailyAgentRunner",
    "DailyAgentState",
    "DailyRunOutcome",
    "ExecutionEngine",
    "EqualWeightPortfolio",
    "MinVariancePortfolio",
    "MarketObservation",
    "OrderIntent",
    "Participant",
    "PortfolioBacktestEngine",
    "PortfolioBacktestResult",
    "PortfolioStrategy",
    "PortfolioTrade",
    "Trade",
    "annualized_return",
    "annualized_volatility",
    "calmar_ratio",
    "cumulative_return",
    "drawdown_series",
    "max_drawdown",
    "max_drawdown_duration",
    "performance_metrics",
    "periodic_returns",
    "sharpe_ratio",
    "sortino_ratio",
    "total_return",
    "total_transaction_cost",
    "turnover",
    "validate_equity_curve",
]
