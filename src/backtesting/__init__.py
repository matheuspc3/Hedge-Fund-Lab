"""Módulo de backtesting — motor, métricas, custos e portfólio multi-ativo."""

from src.backtesting.costs import CostModel
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
    "BacktestEngine",
    "BacktestResult",
    "Trade",
    "CostModel",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "max_drawdown_duration",
    "turnover",
    "cumulative_return",
    "annualized_volatility",
    "calmar_ratio",
    "PortfolioStrategy",
    "EqualWeightPortfolio",
    "MinVariancePortfolio",
    "PortfolioBacktestEngine",
    "PortfolioBacktestResult",
    "PortfolioTrade",
]
