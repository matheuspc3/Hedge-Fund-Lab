"""Avanço diário persistente do participante multiagente."""

import asyncio
import json
import math
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, cast

import pandas as pd

from src.backtesting.agent_engine import (
    INDICATOR_COLUMNS,
    AgentDecisionRecord,
    build_decision_record,
    decision_record_from_dict,
    decision_record_to_dict,
    execute_agent_decision,
)
from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.costs import CostModel
from src.backtesting.engine import Trade

SCHEMA_VERSION = 1


def _timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError("timestamp cannot be NaT")
    return cast(pd.Timestamp, timestamp)


@dataclass
class DailyAgentState:
    ticker: str
    initial_capital: float
    cash: float
    costs: dict[str, float] = field(default_factory=dict)
    position: int = 0
    peak_equity: float = 0.0
    last_session: pd.Timestamp | None = None
    equity_curve: list[dict] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    decisions: list[AgentDecisionRecord] = field(default_factory=list)

    @property
    def pending_decision(self) -> AgentDecisionRecord | None:
        pending = [record for record in self.decisions if record.status == "PREDICTED"]
        if len(pending) > 1:
            raise ValueError("daily state contains more than one pending decision")
        return pending[0] if pending else None

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "ticker": self.ticker,
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "costs": self.costs,
            "position": self.position,
            "peak_equity": self.peak_equity,
            "last_session": (
                str(self.last_session.date()) if self.last_session is not None else None
            ),
            "equity_curve": self.equity_curve,
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

    @classmethod
    def from_dict(cls, payload: dict) -> "DailyAgentState":
        try:
            if payload["schema_version"] != SCHEMA_VERSION:
                raise ValueError("unsupported daily state schema")
            state = cls(
                ticker=str(payload["ticker"]),
                initial_capital=float(payload["initial_capital"]),
                cash=float(payload["cash"]),
                costs={
                    str(key): float(value)
                    for key, value in payload.get("costs", {}).items()
                },
                position=int(payload["position"]),
                peak_equity=float(payload["peak_equity"]),
                last_session=(
                    _timestamp(payload["last_session"])
                    if payload.get("last_session")
                    else None
                ),
                equity_curve=list(payload.get("equity_curve", [])),
                trades=[
                    Trade(
                        date=_timestamp(trade["date"]),
                        type=str(trade["type"]),
                        price=float(trade["price"]),
                        quantity=int(trade["quantity"]),
                        cost=float(trade.get("cost", 0.0)),
                    )
                    for trade in payload.get("trades", [])
                ],
                decisions=[
                    decision_record_from_dict(record)
                    for record in payload.get("decisions", [])
                ],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid daily agent state") from exc

        if (
            state.initial_capital <= 0
            or state.cash < 0
            or state.position < 0
            or state.peak_equity <= 0
            or not all(
                math.isfinite(value)
                for value in (
                    state.initial_capital,
                    state.cash,
                    state.peak_equity,
                    *state.costs.values(),
                )
            )
        ):
            raise ValueError("invalid daily portfolio values")
        pending = state.pending_decision
        if state.last_session is None:
            if state.decisions or state.equity_curve or state.trades:
                raise ValueError("uninitialized state contains history")
        elif (
            not state.decisions
            or state.decisions[-1].decision_date != state.last_session
            or not state.equity_curve
            or state.equity_curve[-1].get("date") != str(state.last_session.date())
        ):
            raise ValueError("daily state history is inconsistent")
        if pending is not None and (
            pending is not state.decisions[-1]
            or pending.target_session is None
            or state.last_session is None
            or pending.target_session <= state.last_session
        ):
            raise ValueError("pending decision has an invalid target session")
        return state

    @classmethod
    def load(cls, path: Path) -> "DailyAgentState":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read daily state: {path}") from exc
        if not isinstance(payload, dict):
            raise ValueError("invalid daily agent state")
        return cls.from_dict(payload)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                self.to_dict(),
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        temporary.replace(path)
        return path


@contextmanager
def _exclusive_state_lock(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"daily runner already active: {lock_path}") from exc

    # ponytail: lock exclusivo local é suficiente para um único host; quando o
    # runner for distribuído, substituir por lock transacional no banco.
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
            lock_file.write(str(os.getpid()))
        yield
    finally:
        lock_path.unlink(missing_ok=True)


@dataclass(frozen=True)
class DailyRunOutcome:
    state: DailyAgentState
    advanced: bool
    expected_session: pd.Timestamp


class DailyAgentRunner:
    """Reconcilia a abertura esperada e gera uma nova previsão no fechamento."""

    def __init__(
        self,
        graph,
        ticker: str,
        state_path: str | Path,
        initial_capital: float = 100_000.0,
        cost_model: CostModel | None = None,
        calendar: B3Calendar | None = None,
        volatility_window: int = 21,
        payoff_ratio: float = 1.0,
    ):
        if initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")
        if volatility_window < 2 or payoff_ratio <= 0:
            raise ValueError("invalid daily runner parameter")
        self.graph = graph
        self.ticker = ticker
        self.state_path = Path(state_path)
        self.initial_capital = initial_capital
        self.cost_model = cost_model or CostModel()
        self.calendar = calendar or B3Calendar()
        self.volatility_window = volatility_window
        self.payoff_ratio = payoff_ratio

    def _prepare_data(
        self, data: pd.DataFrame, as_of: pd.Timestamp | None
    ) -> pd.DataFrame:
        required = {"abertura", "fechamento"}
        missing = required - set(data.columns)
        if data.empty:
            raise ValueError("data cannot be empty")
        if missing:
            raise ValueError(f"data missing columns: {', '.join(sorted(missing))}")

        prepared = data.copy()
        index = pd.DatetimeIndex(pd.to_datetime(prepared.index))
        if index.tz is not None:
            index = index.tz_localize(None)
        prepared.index = pd.DatetimeIndex(
            [_timestamp(value).normalize() for value in index]
        )
        if not prepared.index.is_monotonic_increasing or prepared.index.has_duplicates:
            raise ValueError("data index must be sorted and unique")
        if as_of is not None:
            prepared = prepared.loc[: as_of.normalize()]
        if prepared.empty:
            raise ValueError("no data available at as_of")
        return prepared

    def _load_state(self) -> DailyAgentState:
        expected_costs = {
            "brokerage_fixed": self.cost_model.brokerage_fixed,
            "spread_bps": self.cost_model.spread_bps,
            "tax_rate": self.cost_model.tax_rate,
        }
        if not self.state_path.exists():
            return DailyAgentState(
                ticker=self.ticker,
                initial_capital=self.initial_capital,
                cash=self.initial_capital,
                costs=expected_costs,
                peak_equity=self.initial_capital,
            )
        state = DailyAgentState.load(self.state_path)
        if state.ticker != self.ticker:
            raise ValueError(
                f"state ticker {state.ticker!r} does not match {self.ticker!r}"
            )
        if state.initial_capital != self.initial_capital:
            raise ValueError("initial_capital does not match persisted state")
        if state.costs != expected_costs:
            raise ValueError("cost model does not match persisted state")
        return state

    def _session_to_process(
        self, state: DailyAgentState, data: pd.DataFrame
    ) -> tuple[pd.Timestamp, bool]:
        if state.last_session is None:
            session = _timestamp(data.index[-1])
            if not self.calendar.is_session(session.date()):
                raise ValueError(f"latest bar is not a B3 session: {session.date()}")
            return session, True

        expected = _timestamp(self.calendar.next_session(state.last_session.date()))
        if expected in data.index:
            return expected, True
        if _timestamp(data.index[-1]) > expected:
            raise ValueError(f"data missing expected B3 session: {expected.date()}")
        return expected, False

    def _agent_state(
        self,
        data: pd.DataFrame,
        session: pd.Timestamp,
        state: DailyAgentState,
        equity: float,
    ) -> dict:
        row = data.loc[session]
        historical_close = data.loc[:session, "fechamento"]
        returns = historical_close.pct_change().dropna().tail(self.volatility_window)
        volatility = None
        if len(returns) >= 2:
            volatility = float(returns.std(ddof=1) * math.sqrt(252))
        indicators = {
            column: float(row[column])
            for column in INDICATOR_COLUMNS
            if column in row and pd.notna(row[column])
        }
        return {
            "ticker": self.ticker,
            "date": str(session.date()),
            "indicators": indicators,
            "cash": state.cash,
            "position": float(state.position),
            "current_price": float(row["fechamento"]),
            "equity": equity,
            "recent_volatility": volatility,
            "current_drawdown": (state.peak_equity - equity) / state.peak_equity,
            "payoff_ratio": self.payoff_ratio,
            "errors": [],
        }

    async def run_async(
        self,
        data: pd.DataFrame,
        as_of: pd.Timestamp | None = None,
    ) -> DailyRunOutcome:
        prepared = self._prepare_data(data, as_of)
        with _exclusive_state_lock(self.state_path):
            state = self._load_state()
            session, available = self._session_to_process(state, prepared)
            if not available:
                return DailyRunOutcome(
                    state=state,
                    advanced=False,
                    expected_session=session,
                )

            row = prepared.loc[session]
            opening = float(row["abertura"])
            close = float(row["fechamento"])
            if any(not math.isfinite(value) or value <= 0 for value in (opening, close)):
                raise ValueError(f"invalid OHLC bar for {session.date()}")

            pending = state.pending_decision
            if pending is not None:
                if pending.target_session != session:
                    raise ValueError(
                        "pending target does not match the expected B3 session"
                    )
                state.cash, state.position, trade = execute_agent_decision(
                    pending,
                    state.cash,
                    state.position,
                    opening,
                    session,
                    self.cost_model,
                )
                if trade is not None:
                    state.trades.append(trade)

            equity = state.cash + state.position * close
            state.peak_equity = max(state.peak_equity, equity)
            agent_state = self._agent_state(prepared, session, state, equity)
            output = await self.graph.ainvoke(agent_state)
            target_session = _timestamp(self.calendar.next_session(session.date()))
            state.decisions.append(build_decision_record(output, session, target_session))
            state.equity_curve.append({"date": str(session.date()), "equity": equity})
            state.last_session = session
            state.save(self.state_path)
            return DailyRunOutcome(
                state=state,
                advanced=True,
                expected_session=target_session,
            )

    def run(
        self,
        data: pd.DataFrame,
        as_of: pd.Timestamp | None = None,
    ) -> DailyRunOutcome:
        return asyncio.run(self.run_async(data, as_of))
