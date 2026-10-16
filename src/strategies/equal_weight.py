"""Estratégia Equal Weight — rebalanceamento periódico com pesos iguais.

ATENÇÃO: esta é uma estratégia multi-ativo conceitualmente. Para o
backtesting com um único ativo, o comportamento é idêntico ao Buy and Hold
com rebalanceamento apenas no primeiro dia.
"""

import logging

import pandas as pd

from src.strategies.base import Strategy

logger = logging.getLogger(__name__)


class EqualWeight(Strategy):
    """Equal Weight: distribui o capital igualmente entre N ativos.

    Para efeito de backtesting com 1 ativo, o peso é sempre 1.0 e o
    rebalanceamento (trimestral) apenas recalcula a posição — que não muda
    porque o peso é 1.0.

    Attributes:
        rebalance_freq: Dias úteis entre rebalanceamentos (default 63 ≈ 1 trimestre).
    """

    def __init__(self, rebalance_freq: int = 63):
        self.rebalance_freq = rebalance_freq
        logger.info("EqualWeight criada: rebalance_freq=%d", rebalance_freq)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty:
            return pd.Series([], dtype=int)

        if "fechamento" not in data.columns:
            raise ValueError("DataFrame must contain 'fechamento' column")

        signals = pd.Series(0, index=data.index, dtype=int)
        # Compra no primeiro dia
        signals.iloc[0] = 1
        logger.info(
            "EqualWeight: entrada inicial em %s a R$ %.2f",
            data.index[0],
            data["fechamento"].iloc[0],
        )

        # Rebalanceamento trimestral (reenvia sinal de COMPRA)
        n_rebal = 0
        for i in range(self.rebalance_freq, len(signals), self.rebalance_freq):
            signals.iloc[i] = 1
            n_rebal += 1
            logger.debug(
                "EqualWeight: rebalanceamento %d em %s (preço=%.2f)",
                n_rebal,
                data.index[i],
                data["fechamento"].iloc[i],
            )

        logger.info(
            "EqualWeight: 1 entrada + %d rebalanceamento(s) em %d dias",
            n_rebal,
            len(signals),
        )
        return signals

    def get_name(self) -> str:
        return "Equal Weight"
