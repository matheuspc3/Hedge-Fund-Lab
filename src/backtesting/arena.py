"""Contratos mínimos e execução comum da arena incremental.

O caminho comum executa participantes long-only, sem margem ou alavancagem,
sobre um ou mais ativos. As escolhas científicas definitivas de lote, slippage,
liquidez, suspensão e calendário continuam fora deste contrato técnico
preliminar.
"""

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol, cast

import pandas as pd

from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestResult, Trade

# Tolerância numérica única do caminho comum: resíduo de ponto flutuante em
# somas de pesos e comparações de peso alvo, nunca folga econômica.
WEIGHT_TOLERANCE = 1e-9


@dataclass(frozen=True)
class OrderIntent:
    """Posição alvo desejada, anterior a preço, custos e arredondamento.

    O intent descreve apenas *onde* o participante quer estar, decidido em
    ``close(t)``. Direção da negociação não é decisão do participante: comprar
    ou vender depende da posição e do preço observados na abertura seguinte,
    que o participante não conhece. A elegibilidade de execução também pertence
    ao executor, que associa a intenção à próxima abertura observada — se ela
    existir.
    """

    ticker: str
    target_weight: float
    decision_time: pd.Timestamp

    def __post_init__(self) -> None:
        ticker = self.ticker.strip()
        decision_time = pd.Timestamp(self.decision_time)
        if not ticker:
            raise ValueError("ticker cannot be empty")
        if not math.isfinite(self.target_weight) or not 0 <= self.target_weight <= 1:
            raise ValueError(
                "target_weight must be finite and between 0 and 1; "
                "shorting and leverage are not supported"
            )
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


def weights_to_intents(
    observation: MarketObservation,
    target_weights: Mapping[str, float],
) -> list[OrderIntent]:
    """Converte um mapa de pesos alvo em intents, em ordem canônica.

    Nenhuma direção é decidida aqui: o intent declara apenas o peso desejado e
    o executor descobre, na abertura seguinte, se chegar nele exige comprar,
    vender ou nada.
    """
    return [
        OrderIntent(
            ticker=ticker,
            target_weight=float(target_weights[ticker]),
            decision_time=observation.session,
        )
        for ticker in sorted(target_weights)
    ]


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
        if initial_capital <= 0 or not math.isfinite(initial_capital):
            raise ValueError("initial_capital must be finite and > 0")

        frames: dict[str, pd.DataFrame] = {}
        for raw_ticker, frame in data.items():
            ticker = raw_ticker.strip()
            if not ticker:
                raise ValueError("ticker cannot be empty")
            if ticker in frames:
                raise ValueError(f"duplicate ticker in data: {ticker}")
            frames[ticker] = self._validate(ticker, frame)

        self.participant = participant
        self.tickers = sorted(frames)
        self.data = {ticker: frames[ticker] for ticker in self.tickers}
        # Calendário comum explícito por interseção, como no motor multi-ativo
        # legado: nenhuma barra é fabricada nem propagada por forward-fill.
        self.sessions = self._common_sessions()
        if self.sessions.empty:
            raise ValueError("data has no session shared by every ticker")
        self.initial_capital = float(initial_capital)
        self.cost_model = cost_model or CostModel()

    @staticmethod
    def _validate(ticker: str, frame: pd.DataFrame) -> pd.DataFrame:
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
        return frame.copy(deep=True)

    def _common_sessions(self) -> pd.DatetimeIndex:
        common: pd.DatetimeIndex | None = None
        for ticker in self.tickers:
            index = cast(pd.DatetimeIndex, self.data[ticker].index)
            common = (
                index
                if common is None
                else cast(pd.DatetimeIndex, common.intersection(index))
            )
        assert common is not None
        return common.sort_values()

    # ── Execução ─────────────────────────────────────────────────

    def _buy_total(
        self, quantities: Mapping[str, int], prices: Mapping[str, float]
    ) -> float:
        """Custo financeiro total de um conjunto de compras, via ``CostModel``."""
        total = 0.0
        for ticker in sorted(quantities):
            quantity = quantities[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            total += notional + self.cost_model.apply_buy(notional)
        return total

    def _scale_buys(
        self,
        wanted: Mapping[str, int],
        prices: Mapping[str, float],
        budget: float,
    ) -> dict[str, int]:
        """Dimensiona as compras em conjunto, sem privilegiar nenhum ticker.

        Quando o caixa não cobre todos os déficits, os alvos são escalonados
        pelo mesmo fator e truncados para baixo. O fator vem de uma busca
        binária sobre o custo real reportado pelo ``CostModel``, portanto o
        resultado não depende da ordem dos tickers nem assume a fórmula de custo.

        ponytail: o resíduo de caixa não é redistribuído; a política científica
        de lote e arredondamento continua TBD e deve substituir este truncamento.
        """
        if not wanted:
            return {}
        if self._buy_total(wanted, prices) <= budget:
            return dict(wanted)

        low, high = 0.0, 1.0
        best = dict.fromkeys(wanted, 0)
        for _ in range(64):
            middle = (low + high) / 2
            candidate = {
                ticker: math.floor(middle * quantity)
                for ticker, quantity in wanted.items()
            }
            if self._buy_total(candidate, prices) <= budget:
                low, best = middle, candidate
            else:
                high = middle
        return best

    def _settle(
        self,
        intents: list[OrderIntent],
        session: pd.Timestamp,
        prices: Mapping[str, float],
        cash: float,
        positions: dict[str, int],
    ) -> tuple[float, list[Trade]]:
        """Aplica os intents pendentes na abertura de ``session``.

        A direção nasce aqui: o peso alvo vira quantidade alvo sobre o
        patrimônio observado na abertura e é comparada com a posição corrente.
        Excesso vira ``SELL``, déficit vira ``BUY`` e uma posição já no alvo não
        gera trade — mesmo que, no fechamento anterior, o alvo apontasse para o
        lado oposto.
        """
        equity_at_open = cash + sum(
            positions[ticker] * prices[ticker] for ticker in self.tickers
        )
        targets = {intent.ticker: intent.target_weight for intent in intents}
        desired = {
            ticker: (
                math.floor(equity_at_open * targets[ticker] / prices[ticker])
                if ticker in targets
                else positions[ticker]
            )
            for ticker in self.tickers
        }

        trades: list[Trade] = []
        # Vendas primeiro: o caixa liberado financia as compras do rebalance.
        for ticker in self.tickers:
            quantity = positions[ticker] - desired[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            cost = self.cost_model.apply_sell(notional)
            if cash + notional - cost < 0:
                raise ValueError("sell costs would make cash negative")
            cash += notional - cost
            positions[ticker] -= quantity
            trades.append(
                Trade(
                    date=session,
                    type="SELL",
                    price=prices[ticker],
                    quantity=quantity,
                    cost=cost,
                    ticker=ticker,
                )
            )

        wanted = {
            ticker: desired[ticker] - positions[ticker]
            for ticker in self.tickers
            if desired[ticker] > positions[ticker]
        }
        quantities = self._scale_buys(wanted, prices, cash)
        spent = self._buy_total(quantities, prices)
        if spent > cash:
            raise RuntimeError("buy execution would make cash negative")
        for ticker in sorted(quantities):
            quantity = quantities[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            positions[ticker] += quantity
            trades.append(
                Trade(
                    date=session,
                    type="BUY",
                    price=prices[ticker],
                    quantity=quantity,
                    cost=self.cost_model.apply_buy(notional),
                    ticker=ticker,
                )
            )
        return cash - spent, trades

    def _validate_intents(
        self, intents: list[OrderIntent], observation: MarketObservation
    ) -> None:
        if not all(isinstance(intent, OrderIntent) for intent in intents):
            raise TypeError("participant must return OrderIntent instances")
        if len({intent.ticker for intent in intents}) != len(intents):
            raise ValueError("participant returned duplicate intents for a ticker")
        total_weight = 0.0
        for intent in intents:
            if intent.ticker not in self.data:
                raise ValueError(f"intent references unknown ticker: {intent.ticker}")
            if intent.decision_time != observation.session:
                raise ValueError("intent decision_time must match observation session")
            total_weight += intent.target_weight
        if total_weight > 1 + WEIGHT_TOLERANCE:
            raise ValueError(
                "target weights must sum to at most 1; leverage is not supported"
            )

    def run(self) -> BacktestResult:
        """Executa ``close(t) -> intent -> open(t+1) -> trade -> close equity``."""
        cash = self.initial_capital
        positions = dict.fromkeys(self.tickers, 0)
        pending: list[OrderIntent] = []
        trades: list[Trade] = []
        equity_values: list[float] = []

        for raw_session in self.sessions:
            session = cast(pd.Timestamp, raw_session)
            opens = {
                ticker: float(self.data[ticker].loc[session, "abertura"])
                for ticker in self.tickers
            }
            if pending:
                cash, settled = self._settle(pending, session, opens, cash, positions)
                trades.extend(settled)
            pending = []

            closes = {
                ticker: float(self.data[ticker].loc[session, "fechamento"])
                for ticker in self.tickers
            }
            equity = cash + sum(
                positions[ticker] * closes[ticker] for ticker in self.tickers
            )
            equity_values.append(equity)
            observation = MarketObservation(
                session=session,
                history=MappingProxyType(
                    {
                        ticker: self.data[ticker].loc[:session].copy(deep=True)
                        for ticker in self.tickers
                    }
                ),
                positions=MappingProxyType(dict(positions)),
                cash=cash,
                equity=equity,
            )
            intents = list(self.participant.decide(observation))
            self._validate_intents(intents, observation)
            # Intents da última sessão ficam pendentes e morrem sem execução:
            # não existe abertura observada para eles.
            pending = intents

        equity_curve = pd.Series(equity_values, index=self.sessions, dtype=float)
        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            initial_capital=self.initial_capital,
            final_equity=float(equity_curve.iloc[-1]),
        )
