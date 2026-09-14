"""Estratégia baseada em Bandas de Bollinger.

Compra quando o preço cruza acima da banda inferior (sobrevendido).
Vende quando o preço cruza abaixo da banda superior (sobrecomprado).
"""

import logging
from typing import cast

import pandas as pd

from src.strategies.base import SignalParticipant, Strategy

logger = logging.getLogger(__name__)


class BollingerBandsStrategy(Strategy):
    """Estratégia de reversão à média com Bandas de Bollinger.

    Attributes:
        window: Janela da média móvel (default 20).
        k: Número de desvios-padrão (default 2.0).
    """

    def __init__(self, window: int = 20, k: float = 2.0):
        self.window = window
        self.k = k
        logger.info("BollingerBandsStrategy criada: window=%d k=%.1f", window, k)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty:
            return pd.Series([], dtype=int)

        if "fechamento" not in data.columns:
            raise ValueError("DataFrame must contain 'fechamento' column")

        close = data["fechamento"]
        middle = close.rolling(window=self.window).mean()
        std = close.rolling(window=self.window).std()
        upper = middle + self.k * std
        lower = middle - self.k * std

        signals = pd.Series(0, index=data.index, dtype=int)
        n_buy = 0
        n_sell = 0

        for i in range(1, len(signals)):
            if pd.isna(upper.iloc[i]) or pd.isna(lower.iloc[i]):
                continue

            # Preço estava dentro e saiu pra cima → VENDA
            if (
                not pd.isna(close.iloc[i - 1])
                and not pd.isna(close.iloc[i])
                and close.iloc[i - 1] <= upper.iloc[i - 1]
                and close.iloc[i] > upper.iloc[i]
            ):
                signals.iloc[i] = -1
                n_sell += 1
                logger.info(
                    "BB VENDA em %s: preço=%.2f > banda_sup=%.2f",
                    data.index[i],
                    close.iloc[i],
                    upper.iloc[i],
                )

            # Preço estava dentro e saiu pra baixo → COMPRA
            elif (
                not pd.isna(close.iloc[i - 1])
                and not pd.isna(close.iloc[i])
                and close.iloc[i - 1] >= lower.iloc[i - 1]
                and close.iloc[i] < lower.iloc[i]
            ):
                signals.iloc[i] = 1
                n_buy += 1
                logger.info(
                    "BB COMPRA em %s: preço=%.2f < banda_inf=%.2f",
                    data.index[i],
                    close.iloc[i],
                    lower.iloc[i],
                )

        logger.debug(
            "BB: %d compra(s), %d venda(s) em %d dias",
            n_buy,
            n_sell,
            len(signals),
        )
        return signals

    def get_name(self) -> str:
        return f"Bollinger Bands ({self.window},{self.k})"


class BollingerParticipant(SignalParticipant):
    """Adapter causal das Bandas de Bollinger para o contrato comum da arena.

    Compra quando o fechamento rompe a banda inferior e sai quando rompe a
    superior, sempre com bandas estimadas apenas até ``t``.

    ponytail: mesma janela recalculada por sessão que o ``SMACrossParticipant``;
    o teto é O(n) por passo.
    """

    def __init__(self, ticker: str, window: int = 20, k: float = 2.0):
        super().__init__(ticker)
        self.window = window
        self.k = k

    def _signal(self, close: pd.Series) -> int:
        if len(close) < 2:
            return 0

        middle = cast(pd.Series, close.rolling(window=self.window).mean())
        std = cast(pd.Series, close.rolling(window=self.window).std())
        upper = cast(pd.Series, middle + self.k * std)
        lower = cast(pd.Series, middle - self.k * std)
        if pd.isna(upper.iloc[-1]) or pd.isna(lower.iloc[-1]):
            return 0

        previous, current = close.iloc[-2], close.iloc[-1]
        if pd.isna(previous) or pd.isna(current):
            return 0
        # Comparações com banda NaN em t-1 são falsas, como no motor legado:
        # a primeira banda válida não produz rompimento.
        if previous <= upper.iloc[-2] and current > upper.iloc[-1]:
            return -1
        if previous >= lower.iloc[-2] and current < lower.iloc[-1]:
            return 1
        return 0
