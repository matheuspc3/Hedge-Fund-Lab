"""Backtest sequencial do comitê multiagente sem vazamento temporal."""

import asyncio
import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, cast

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

logger = logging.getLogger("hedgefund.engine")

DecisionStatus = Literal["PREDICTED", "EXECUTED", "NO_ACTION", "REJECTED"]
DECISION_STATUSES = {"PREDICTED", "EXECUTED", "NO_ACTION", "REJECTED"}

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
    status: DecisionStatus
    errors: list[str] = field(default_factory=list)
    target_session: pd.Timestamp | None = None
    execution_date: pd.Timestamp | None = None
    execution_price: float | None = None
    status_reason: str | None = None


def decision_record_to_dict(record: AgentDecisionRecord) -> dict:
    return {
        "as_of": str(record.decision_date.date()),
        "decision_date": str(record.decision_date.date()),
        "target_session": (
            str(record.target_session.date())
            if record.target_session is not None
            else None
        ),
        "status": record.status,
        "execution_date": (
            str(record.execution_date.date())
            if record.execution_date is not None
            else None
        ),
        "execution_price": record.execution_price,
        "status_reason": record.status_reason,
        "technical_signal": (
            record.technical_signal.model_dump(mode="json")
            if record.technical_signal
            else None
        ),
        "technical_votes": [
            vote.model_dump(mode="json") for vote in record.technical_votes
        ],
        "consensus": (
            record.consensus.model_dump(mode="json") if record.consensus else None
        ),
        "risk_verdict": (
            record.risk_verdict.model_dump(mode="json") if record.risk_verdict else None
        ),
        "final_decision": (
            record.final_decision.model_dump(mode="json")
            if record.final_decision
            else None
        ),
        "errors": record.errors,
    }


def decision_record_from_dict(payload: dict) -> AgentDecisionRecord:
    status = str(payload["status"])
    if status not in DECISION_STATUSES:
        raise ValueError(f"invalid decision status: {status}")
    return AgentDecisionRecord(
        decision_date=pd.Timestamp(payload.get("as_of") or payload["decision_date"]),
        technical_signal=(
            TechnicalSignal.model_validate(payload["technical_signal"])
            if payload.get("technical_signal") is not None
            else None
        ),
        consensus=(
            TechnicalConsensus.model_validate(payload["consensus"])
            if payload.get("consensus") is not None
            else None
        ),
        technical_votes=[
            TechnicalVote.model_validate(vote)
            for vote in payload.get("technical_votes", [])
        ],
        risk_verdict=(
            RiskVerdict.model_validate(payload["risk_verdict"])
            if payload.get("risk_verdict") is not None
            else None
        ),
        final_decision=(
            FinalDecision.model_validate(payload["final_decision"])
            if payload.get("final_decision") is not None
            else None
        ),
        status=cast(DecisionStatus, status),
        errors=list(payload.get("errors", [])),
        target_session=(
            pd.Timestamp(payload["target_session"])
            if payload.get("target_session")
            else None
        ),
        execution_date=(
            pd.Timestamp(payload["execution_date"])
            if payload.get("execution_date")
            else None
        ),
        execution_price=payload.get("execution_price"),
        status_reason=payload.get("status_reason"),
    )


def build_decision_record(
    output: dict,
    decision_date: pd.Timestamp,
    target_session: pd.Timestamp | None,
) -> AgentDecisionRecord:
    """Converte a saída do grafo no contrato operacional auditável."""
    decision = output.get("final_decision")
    risk_verdict = output.get("risk_verdict")
    errors = list(output.get("errors", []))
    if decision is None:
        status: DecisionStatus = "REJECTED"
        status_reason = "; ".join(errors) or (
            risk_verdict.analysis
            if risk_verdict is not None and risk_verdict.verdict == "VETADO"
            else "Decisão final ausente"
        )
    elif decision.decision == "MANTER":
        status = "NO_ACTION"
        status_reason = decision.reasoning
    else:
        status = "PREDICTED"
        status_reason = None

    return AgentDecisionRecord(
        decision_date=decision_date,
        technical_signal=output.get("technical_signal"),
        consensus=output.get("technical_consensus"),
        technical_votes=list(output.get("technical_votes", [])),
        risk_verdict=risk_verdict,
        final_decision=decision,
        status=status,
        errors=errors,
        target_session=target_session if status == "PREDICTED" else None,
        status_reason=status_reason,
    )


def _buy_order(
    cash: float,
    price: float,
    size: float,
    cost_model: CostModel,
) -> tuple[float, int, Trade | None]:
    budget = cash * size
    proportional_cost = cost_model.spread_bps / 10_000 + cost_model.tax_rate
    available = max(0.0, budget - cost_model.brokerage_fixed)
    quantity = math.floor(available / ((1 + proportional_cost) * price))
    if quantity <= 0:
        return cash, 0, None
    value = quantity * price
    cost = cost_model.apply_buy(value)
    return cash - value - cost, quantity, Trade(pd.NaT, "BUY", price, quantity, cost)


def _sell_order(
    cash: float,
    position: int,
    price: float,
    size: float,
    cost_model: CostModel,
) -> tuple[float, int, Trade | None]:
    quantity = min(position, math.floor(position * size))
    if quantity <= 0:
        return cash, position, None
    value = quantity * price
    cost = cost_model.apply_sell(value)
    return (
        cash + value - cost,
        position - quantity,
        Trade(pd.NaT, "SELL", price, quantity, cost),
    )


def execute_agent_decision(
    record: AgentDecisionRecord,
    cash: float,
    position: int,
    execution_price: float,
    execution_date: pd.Timestamp,
    cost_model: CostModel,
) -> tuple[float, int, Trade | None]:
    """Resolve uma previsão na abertura elegível e atualiza seu lifecycle."""
    decision = record.final_decision
    if record.status != "PREDICTED" or decision is None:
        raise ValueError("only a predicted decision can be executed")

    trade = None
    if not math.isfinite(execution_price) or execution_price <= 0:
        record.status = "REJECTED"
        record.status_reason = "Ordem não executada: preço de abertura inválido"
    elif decision.decision == "COMPRA":
        cash, bought, trade = _buy_order(
            cash, execution_price, decision.position_size, cost_model
        )
        position += bought
    elif decision.decision == "VENDA":
        cash, position, trade = _sell_order(
            cash, position, execution_price, decision.position_size, cost_model
        )

    if trade is None:
        if record.status != "REJECTED":
            record.status = "REJECTED"
            record.status_reason = (
                "Ordem não executada: caixa, posição ou tamanho insuficiente"
            )
        return cash, position, None

    trade.date = execution_date
    record.execution_date = execution_date
    record.execution_price = execution_price
    record.status = "EXECUTED"
    record.status_reason = None
    return cash, position, trade


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

    def save_audit(self, path: str | Path, telemetry: list[dict] | None = None) -> Path:
        """Salva decisões, 30 votos, trades e curva em JSON de forma atômica."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "telemetry": telemetry or [],
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
            "decisions": [decision_record_to_dict(record) for record in self.decisions],
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
        return _buy_order(cash, price, size, self.cost_model)

    def _sell(
        self, cash: float, position: int, price: float, size: float
    ) -> tuple[float, int, Trade | None]:
        return _sell_order(cash, position, price, size, self.cost_model)

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
                cash, position, trade = execute_agent_decision(
                    record,
                    cash,
                    position,
                    execution_price,
                    pd.Timestamp(date),
                    self.cost_model,
                )
                if trade is not None:
                    trades.append(trade)
                pending = None

            close = float(row["fechamento"])
            equity = cash + position * close
            peak_equity = max(peak_equity, equity)
            equity_values.append(equity)

            is_last_day = index == len(self.data) - 1
            # ponytail: a última barra gera a previsão, mas não inventa a próxima sessão.
            if not is_last_day and index % self.decision_frequency != 0:
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
            record = build_decision_record(
                output,
                pd.Timestamp(date),
                (pd.Timestamp(self.data.index[index + 1]) if not is_last_day else None),
            )
            decisions.append(record)
            decision = record.final_decision

            date_str = str(pd.Timestamp(date).date())
            log_parts = [f"Data: {date_str}"]
            if record.consensus:
                signal = record.consensus.winning_signal or "NENHUM"
                conf = max(record.consensus.counts.values()) / max(
                    record.consensus.valid_votes, 1
                )
                log_parts.append(f"Técnicos: {signal} ({conf * 100:.0f}%)")
            if record.risk_verdict:
                log_parts.append(f"Risco: {record.risk_verdict.verdict}")
            if decision:
                reasoning = decision.reasoning.replace("\n", " ")
                log_parts.append(
                    f"PM: {decision.decision} "
                    f"({decision.position_size * 100:.0f}%) -> {reasoning}"
                )
            log_parts.append(f"Status: {record.status}")

            logger.info(" | ".join(log_parts))

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
