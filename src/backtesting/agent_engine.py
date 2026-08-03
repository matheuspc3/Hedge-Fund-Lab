"""Backtest sequencial do comitê multiagente sem vazamento temporal."""

import asyncio
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.agents.state import (
    FinalDecision,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
    TechnicalVote,
)
from src.backtesting.costs import CostModel
from src.backtesting.engine import Trade

INDICATOR_COLUMNS = (
    "sma_50",
    "sma_200",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "rsi",
    "macd",
    "macd_sinal",
)


@dataclass
class AgentDecisionRecord:
    decision_date: pd.Timestamp
    technical_signal: TechnicalSignal | None
    consensus: TechnicalConsensus | None
    technical_votes: list[TechnicalVote]
    risk_verdict: RiskVerdict | None
    final_decision: FinalDecision | None
    errors: list[str] = field(default_factory=list)
    execution_date: pd.Timestamp | None = None


@dataclass
class AgentBacktestResult:
    equity_curve: pd.Series
    trades: list[Trade]
    decisions: list[AgentDecisionRecord]
    initial_capital: float
    final_equity: float

    @property
    def returns(self) -> pd.Series:
        return self.equity_curve.pct_change().dropna()

    def save_audit(self, path: str | Path) -> Path:
        """Salva decisões, 30 votos, trades e curva em JSON de forma atômica."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "initial_capital": self.initial_capital,
            "final_equity": self.final_equity,
            "equity_curve": [
                {"date": str(pd.Timestamp(date).date()), "equity": value}
                for date, value in self.equity_curve.items()
            ],
            "trades": [
                {
                    "date": str(pd.Timestamp(trade.date).date()),
                    "type": trade.type,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "cost": trade.cost,
                }
                for trade in self.trades
            ],
            "decisions": [
                {
                    "decision_date": str(record.decision_date.date()),
                    "execution_date": (
                        str(record.execution_date.date())
                        if record.execution_date
                        else None
                    ),
                    "technical_signal": (
                        record.technical_signal.model_dump(mode="json")
                        if record.technical_signal
                        else None
                    ),
                    "technical_votes": [
                        vote.model_dump(mode="json") for vote in record.technical_votes
                    ],
                    "consensus": (
                        record.consensus.model_dump(mode="json")
                        if record.consensus
                        else None
                    ),
                    "risk_verdict": (
                        record.risk_verdict.model_dump(mode="json")
                        if record.risk_verdict
                        else None
                    ),
                    "final_decision": (
                        record.final_decision.model_dump(mode="json")
                        if record.final_decision
                        else None
                    ),
                    "errors": record.errors,
                }
                for record in self.decisions
            ],
        }
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
        return path


class AgentBacktestEngine:
    """Decide no fechamento de ``t`` e executa na abertura de ``t+1``."""

    def __init__(
        self,
        graph,
        data: pd.DataFrame,
        ticker: str,
        initial_capital: float = 100_000.0,
        cost_model: CostModel | None = None,
        volatility_window: int = 21,
        decision_frequency: int = 1,
        payoff_ratio: float = 1.0,
    ):
        required = {"abertura", "fechamento"}
        missing = required - set(data.columns)
        if data.empty:
            raise ValueError("data cannot be empty")
        if missing:
            raise ValueError(f"data missing columns: {', '.join(sorted(missing))}")
        if initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")
        if volatility_window < 2 or decision_frequency < 1 or payoff_ratio <= 0:
            raise ValueError("invalid engine parameter")
        if not data.index.is_monotonic_increasing or data.index.has_duplicates:
            raise ValueError("data index must be sorted and unique")

        self.graph = graph
        self.data = data
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.cost_model = cost_model or CostModel()
        self.volatility_window = volatility_window
        self.decision_frequency = decision_frequency
        self.payoff_ratio = payoff_ratio

    def _buy(
        self, cash: float, price: float, size: float
    ) -> tuple[float, int, Trade | None]:
        budget = cash * size
        proportional_cost = self.cost_model.spread_bps / 10_000 + self.cost_model.tax_rate
        available = max(0.0, budget - self.cost_model.brokerage_fixed)
        quantity = math.floor(available / ((1 + proportional_cost) * price))
        if quantity <= 0:
            return cash, 0, None
        value = quantity * price
        cost = self.cost_model.apply_buy(value)
        return cash - value - cost, quantity, Trade(pd.NaT, "BUY", price, quantity, cost)

    def _sell(
        self, cash: float, position: int, price: float, size: float
    ) -> tuple[float, int, Trade | None]:
        quantity = min(position, math.floor(position * size))
        if quantity <= 0:
            return cash, position, None
        value = quantity * price
        cost = self.cost_model.apply_sell(value)
        return (
            cash + value - cost,
            position - quantity,
            Trade(pd.NaT, "SELL", price, quantity, cost),
        )

    async def run_async(self) -> AgentBacktestResult:
        cash = self.initial_capital
        position = 0
        peak_equity = self.initial_capital
        equity_values: list[float] = []
        trades: list[Trade] = []
        decisions: list[AgentDecisionRecord] = []
        pending: tuple[FinalDecision, AgentDecisionRecord] | None = None

        for index, (date, row) in enumerate(self.data.iterrows()):
            if pending is not None:
                decision, record = pending
                execution_price = float(row["abertura"])
                trade = None
                if decision.decision == "COMPRA":
                    cash, bought, trade = self._buy(
                        cash, execution_price, decision.position_size
                    )
                    position += bought
                elif decision.decision == "VENDA":
                    cash, position, trade = self._sell(
                        cash, position, execution_price, decision.position_size
                    )
                if trade is not None:
                    trade.date = date
                    trades.append(trade)
                    record.execution_date = date
                pending = None

            close = float(row["fechamento"])
            equity = cash + position * close
            peak_equity = max(peak_equity, equity)
            equity_values.append(equity)

            if index == len(self.data) - 1 or index % self.decision_frequency:
                continue

            historical_close = self.data["fechamento"].iloc[: index + 1]
            returns = historical_close.pct_change().dropna().tail(self.volatility_window)
            volatility = None
            if len(returns) >= 2:
                volatility = float(returns.std(ddof=1) * math.sqrt(252))

            indicators = {
                column: float(row[column])
                for column in INDICATOR_COLUMNS
                if column in row and pd.notna(row[column])
            }
            agent_state = {
                "ticker": self.ticker,
                "date": str(pd.Timestamp(date).date()),
                "indicators": indicators,
                "cash": cash,
                "position": float(position),
                "current_price": close,
                "equity": equity,
                "recent_volatility": volatility,
                "current_drawdown": (peak_equity - equity) / peak_equity,
                "payoff_ratio": self.payoff_ratio,
                "errors": [],
            }
            output = await self.graph.ainvoke(agent_state)
            record = AgentDecisionRecord(
                decision_date=pd.Timestamp(date),
                technical_signal=output.get("technical_signal"),
                consensus=output.get("technical_consensus"),
                technical_votes=output.get("technical_votes", []),
                risk_verdict=output.get("risk_verdict"),
                final_decision=output.get("final_decision"),
                errors=output.get("errors", []),
            )
            decisions.append(record)
            decision = record.final_decision
            if decision is not None and decision.decision != "MANTER":
                pending = (decision, record)

        equity_curve = pd.Series(equity_values, index=self.data.index, dtype=float)
        return AgentBacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            decisions=decisions,
            initial_capital=self.initial_capital,
            final_equity=float(equity_curve.iloc[-1]),
        )

    def run(self) -> AgentBacktestResult:
        return asyncio.run(self.run_async())
