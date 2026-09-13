"""Estratégia Buy and Hold — compra no primeiro dia e mantém."""

import logging

import pandas as pd

from src.backtesting.arena import MarketObservation, OrderIntent
from src.strategies.base import Strategy

logger = logging.getLogger(__name__)


class BuyAndHold(Strategy):
    """Buy and Hold: compra no T0 e nunca vende.

    Gera sinal 1 (COMPRA) no primeiro dia útil e 0 (MANTER) nos demais.
    """

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty:
            return pd.Series([], dtype=int)

        if "fechamento" not in data.columns:
            raise ValueError("DataFrame must contain 'fechamento' column")

        signals = pd.Series(0, index=data.index, dtype=int)
        if len(signals) > 0:
            signals.iloc[0] = 1
            logger.info(
                "BuyAndHold: entrada em %s a R$ %.2f",
                data.index[0],
                data["fechamento"].iloc[0],
            )
        return signals

    def get_name(self) -> str:
        return "Buy and Hold"


class BuyAndHoldParticipant:
    """Adapter Buy & Hold causal para o contrato incremental da arena."""

    def __init__(self, ticker: str) -> None:
        if not ticker.strip():
            raise ValueError("ticker cannot be empty")
        self.ticker = ticker.strip()

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        """Compra na primeira observação; não consulta sessão futura."""
        history = observation.history.get(self.ticker)
        if history is None:
            raise ValueError(f"observation missing ticker: {self.ticker}")
        if len(history) != 1:
            return []
        return [
            OrderIntent(
                ticker=self.ticker,
                target_weight=1.0,
                decision_time=observation.session,
            )
        ]
