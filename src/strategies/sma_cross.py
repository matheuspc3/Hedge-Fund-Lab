"""Estratégia de Cruzamento de Médias (SMA Cross).

Compra quando SMA rápida cruza acima da SMA lenta (golden cross).
Vende quando SMA rápida cruza abaixo da SMA lenta (death cross).
"""

import logging

import pandas as pd

from src.strategies.base import Strategy

logger = logging.getLogger(__name__)


class SMACross(Strategy):
    """Cruzamento de Médias Móveis.

    Attributes:
        fast_window: Janela da SMA rápida (default 50).
        slow_window: Janela da SMA lenta (default 200).
    """

    def __init__(self, fast_window: int = 50, slow_window: int = 200):
        if fast_window >= slow_window:
            raise ValueError(
                f"fast_window ({fast_window}) must be < slow_window ({slow_window})"
            )
        self.fast_window = fast_window
        self.slow_window = slow_window
        logger.info(
            "SMACross criada: fast=%d slow=%d", fast_window, slow_window
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty:
            return pd.Series([], dtype=int)

        if "fechamento" not in data.columns:
            raise ValueError("DataFrame must contain 'fechamento' column")

        close = data["fechamento"]
        sma_fast = close.rolling(window=self.fast_window).mean()
        sma_slow = close.rolling(window=self.slow_window).mean()

        signals = pd.Series(0, index=data.index, dtype=int)

        # Só gera sinais após a SMA lenta ter valor válido
        valid_start = self.slow_window
        if len(signals) <= valid_start:
            logger.debug("SMACross: dados insuficientes (%d < slow=%d)", len(signals), self.slow_window)
            return signals

        n_golden = 0
        n_death = 0

        for i in range(valid_start, len(signals)):
            if (
                not pd.isna(sma_fast.iloc[i])
                and not pd.isna(sma_slow.iloc[i])
                and not pd.isna(sma_fast.iloc[i - 1])
                and not pd.isna(sma_slow.iloc[i - 1])
            ):
                # Golden cross: fast cruza acima da slow
                if sma_fast.iloc[i - 1] <= sma_slow.iloc[i - 1] and sma_fast.iloc[i] > sma_slow.iloc[i]:
                    signals.iloc[i] = 1
                    n_golden += 1
                    logger.info(
                        "GOLDEN CROSS em %s: fast=%.2f slow=%.2f",
                        data.index[i], sma_fast.iloc[i], sma_slow.iloc[i],
                    )
                # Death cross: fast cruza abaixo da slow
                elif sma_fast.iloc[i - 1] >= sma_slow.iloc[i - 1] and sma_fast.iloc[i] < sma_slow.iloc[i]:
                    signals.iloc[i] = -1
                    n_death += 1
                    logger.info(
                        "DEATH CROSS em %s: fast=%.2f slow=%.2f",
                        data.index[i], sma_fast.iloc[i], sma_slow.iloc[i],
                    )

        logger.debug(
            "SMACross: %d golden cross(es), %d death cross(es) em %d dias",
            n_golden, n_death, len(signals),
        )
        return signals

    def get_name(self) -> str:
        return f"SMA Cross ({self.fast_window}/{self.slow_window})"
