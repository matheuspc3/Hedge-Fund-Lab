"""Contratos mínimos e execução comum da arena incremental.

Esta primeira versão executa apenas um ativo, long-only, sem margem ou
alavancagem. As escolhas científicas definitivas de lote, slippage e liquidez
continuam fora deste contrato técnico preliminar.
"""

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping, Protocol, cast

import pandas as pd

from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestResult, Trade

OrderSide = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class OrderIntent:
    """Decisão do participante, anterior a preço, custos e arredondamento.

    O intent descreve apenas o que o participante quer fazer em ``close(t)``.
    A elegibilidade de execução pertence ao executor, que associa a intenção à
    próxima abertura observada — se ela existir.
    """

    ticker: str
    side: OrderSide
    target_weight: float
    decision_time: pd.Timestamp

    def __post_init__(self) -> None:
        ticker = self.ticker.strip()
        decision_time = pd.Timestamp(self.decision_time)
        if not ticker:
            raise ValueError("ticker cannot be empty")
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"unsupported order side: {self.side}")
        if not math.isfinite(self.target_weight) or not 0 <= self.target_weight <= 1:
            raise ValueError(
                "target_weight must be finite and between 0 and 1; "
                "shorting and leverage are not supported"
            )
        if self.side == "BUY" and self.target_weight == 0:
            raise ValueError("BUY target_weight must be > 0")
        if pd.isna(decision_time):
            raise ValueError("decision_time cannot be NaT")
        object.__setattr__(self, "ticker", ticker)
        object.__setattr__(self, "decision_time", decision_time)


@dataclass(frozen=True)
class MarketObservation:
    """Informação observável no fechamento de uma sessão.

    Contém somente o que existe em ``t``. O participante não sabe se ainda há
    barra futura no recorte, portanto não consegue identificar o fim da amostra
    experimental por este contrato.
    """

    session: pd.Timestamp
    history: Mapping[str, pd.DataFrame]
    positions: Mapping[str, int]
    cash: float
    equity: float


class Participant(Protocol):
    """Participante que somente decide; não executa nem altera portfólio."""

    def decide(self, observation: MarketObservation) -> list[OrderIntent]: ...


class ExecutionEngine:
    """Executa intents long-only na abertura seguinte e marca equity no close."""

    def __init__(
        self,
        participant: Participant,
        data: Mapping[str, pd.DataFrame],
        initial_capital: float,
        cost_model: CostModel | None = None,
    ) -> None:
        if not data:
            raise ValueError("data cannot be empty")
        # ponytail: um ticker é o teto deliberado desta prova; a política
        # multi-ativo deve remover este guard quando for definida.
        if len(data) != 1:
            raise ValueError("the preliminary arena execution path supports one ticker")
        if initial_capital <= 0 or not math.isfinite(initial_capital):
            raise ValueError("initial_capital must be finite and > 0")

        ticker, frame = next(iter(data.items()))
        ticker = ticker.strip()
        if not ticker:
            raise ValueError("ticker cannot be empty")
        if frame.empty:
            raise ValueError(f"data for {ticker} cannot be empty")
        missing = {"abertura", "fechamento"} - set(frame.columns)
        if missing:
            raise ValueError(
                f"data for {ticker} missing columns: {', '.join(sorted(missing))}"
            )
        if not isinstance(frame.index, pd.DatetimeIndex):
            raise ValueError("data index must be a DatetimeIndex")
        if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
            raise ValueError("data index must be sorted and unique")
        prices = frame[["abertura", "fechamento"]].to_numpy(dtype=float)
        if not all(math.isfinite(value) and value > 0 for value in prices.flat):
            raise ValueError("open and close prices must be finite and > 0")

        self.participant = participant
        self.data = {ticker: frame.copy(deep=True)}
        self.ticker = ticker
        self.initial_capital = float(initial_capital)
        self.cost_model = cost_model or CostModel()

    def _execute(
        self,
        intent: OrderIntent,
        execution_time: pd.Timestamp,
        price: float,
        cash: float,
        position: int,
    ) -> tuple[float, int, Trade | None]:
        if intent.ticker != self.ticker:
            raise ValueError(f"intent references unknown ticker: {intent.ticker}")

        equity_at_open = cash + position * price
        target_quantity = math.floor(equity_at_open * intent.target_weight / price)

        if intent.side == "BUY":
            if target_quantity < position:
                raise ValueError("BUY intent cannot reduce the current position")
            quantity = min(
                target_quantity - position,
                self.cost_model.max_affordable_quantity(cash, price),
            )
            if quantity == 0:
                return cash, position, None
            notional = quantity * price
            cost = self.cost_model.apply_buy(notional)
            cash_after = cash - notional - cost
            if cash_after < -1e-9:
                raise RuntimeError("buy execution would make cash negative")
            cash = max(0.0, cash_after)
            position += quantity
        else:
            if target_quantity > position:
                raise ValueError("SELL intent cannot increase the current position")
            quantity = position - target_quantity
            if quantity == 0:
                return cash, position, None
            notional = quantity * price
            cost = self.cost_model.apply_sell(notional)
            cash_after = cash + notional - cost
            if cash_after < 0:
                raise ValueError("sell costs would make cash negative")
            cash = cash_after
            position -= quantity

        return (
            cash,
            position,
            Trade(
                date=execution_time,
                type=intent.side,
                price=price,
                quantity=quantity,
                cost=cost,
                ticker=intent.ticker,
            ),
        )

    def run(self) -> BacktestResult:
        """Executa ``close(t) -> intent -> open(t+1) -> trade -> close equity``."""
        frame = self.data[self.ticker]
        sessions = list(frame.index)
        cash = self.initial_capital
        position = 0
        pending: list[OrderIntent] = []
        trades: list[Trade] = []
        equity_values: list[float] = []

        for raw_session in sessions:
            session = cast(pd.Timestamp, raw_session)
            open_price = float(frame.loc[session, "abertura"])
            for intent in sorted(pending, key=lambda item: item.ticker):
                cash, position, trade = self._execute(
                    intent, session, open_price, cash, position
                )
                if trade is not None:
                    trades.append(trade)
            pending = []

            close_price = float(frame.loc[session, "fechamento"])
            equity = cash + position * close_price
            equity_values.append(equity)
            observation = MarketObservation(
                session=session,
                history=MappingProxyType(
                    {self.ticker: frame.loc[:session].copy(deep=True)}
                ),
                positions=MappingProxyType({self.ticker: position}),
                cash=cash,
                equity=equity,
            )
            intents = list(self.participant.decide(observation))
            if not all(isinstance(intent, OrderIntent) for intent in intents):
                raise TypeError("participant must return OrderIntent instances")
            if len({intent.ticker for intent in intents}) != len(intents):
                raise ValueError("participant returned duplicate intents for a ticker")
            for intent in intents:
                if intent.decision_time != session:
                    raise ValueError("intent decision_time must match observation session")
            # Intents da última sessão ficam pendentes e morrem sem execução:
            # não existe abertura observada para eles.
            pending = intents

        equity_curve = pd.Series(equity_values, index=frame.index, dtype=float)
        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            initial_capital=self.initial_capital,
            final_equity=float(equity_curve.iloc[-1]),
        )
