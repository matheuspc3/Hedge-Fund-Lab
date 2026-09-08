"""Módulo de backtesting — motor, métricas, custos e portfólio multi-ativo."""

from src.backtesting.agent_engine import (
    AgentBacktestEngine,
    AgentBacktestResult,
    AgentDecisionRecord,
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
    annualized_volatility,
    calmar_ratio,
    cumulative_return,
    max_drawdown,
    max_drawdown_duration,
    sharpe_ratio,
    sortino_ratio,
    turnover,
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
    "EqualWeightPortfolio",
    "MinVariancePortfolio",
    "PortfolioBacktestEngine",
    "PortfolioBacktestResult",
    "PortfolioStrategy",
    "PortfolioTrade",
    "Trade",
    "annualized_volatility",
    "calmar_ratio",
    "cumulative_return",
    "max_drawdown",
    "max_drawdown_duration",
    "sharpe_ratio",
    "sortino_ratio",
    "turnover",
]
