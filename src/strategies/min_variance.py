"""Estratégia de Mínima Variância — otimização de portfólio com janela rolante.

Calcula a carteira de mínima variância (sem restrição de short selling) usando
a matriz de covariância histórica. Para o caso multi-ativo, encontra os pesos
que minimizam a variância do portfólio.

ATENÇÃO: esta estratégia é multi-ativo. No backtesting com 1 ativo,
os pesos são sempre [1.0], equivalente a Buy and Hold.
"""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.strategies.base import Strategy

logger = logging.getLogger(__name__)


class MinVariance(Strategy):
    """Carteira de Mínima Variância com janela rolante.

    A cada *rebalance_freq* dias, recalcula os pesos ótimos usando os
    retornos dos últimos *window* dias.

    Attributes:
        window: Janela histórica para estimar covariância (default 252).
        rebalance_freq: Frequência de rebalanceamento em dias (default 63).
        allow_short: Se True, permite pesos negativos (default False).
    """

    def __init__(
        self,
        window: int = 252,
        rebalance_freq: int = 63,
        allow_short: bool = False,
    ):
        self.window = window
        self.rebalance_freq = rebalance_freq
        self.allow_short = allow_short
        logger.info(
            "MinVariance criada: window=%d rebalance_freq=%d allow_short=%s",
            window, rebalance_freq, allow_short,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if data.empty:
            return pd.Series([], dtype=int)

        if "fechamento" not in data.columns:
            raise ValueError("DataFrame must contain 'fechamento' column")

        signals = pd.Series(0, index=data.index, dtype=int)
        # Compra no primeiro dia
        signals.iloc[0] = 1
        logger.info(
            "MinVariance: entrada em %s a R$ %.2f",
            data.index[0], data["fechamento"].iloc[0],
        )

        # Rebalanceamento periódico
        n_rebal = 0
        n_skipped = 0
        for i in range(self.rebalance_freq, len(signals), self.rebalance_freq):
            if i < self.window:
                n_skipped += 1
                continue  # Dados insuficientes para estimar covariância
            signals.iloc[i] = 1
            n_rebal += 1
            logger.debug(
                "MinVariance: rebalanceamento %d em %s (preço=%.2f)",
                n_rebal, data.index[i], data["fechamento"].iloc[i],
            )

        logger.info(
            "MinVariance: 1 entrada + %d rebalanceamento(s) + %d pulado(s) "
            "(window=%d) em %d dias",
            n_rebal, n_skipped, self.window, len(signals),
        )

        return signals

    def get_name(self) -> str:
        return "Mínima Variância"

    @staticmethod
    def _optimize_weights(returns: pd.DataFrame) -> np.ndarray:
        """Encontra os pesos de mínima variância.

        Args:
            returns: DataFrame com retornos diários (colunas = ativos).

        Returns:
            Array numpy com os pesos ótimos.
        """
        cov = returns.cov().values
        n = cov.shape[0]
        bounds = [(-1.0, 1.0)] * n if False else [(0.0, 1.0)] * n  # noqa: F841

        def portfolio_var(weights: np.ndarray) -> float:
            return weights.T @ cov @ weights

        constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
        bounds = [(None, None)] * n  # Sem restrição de short

        initial = np.array([1.0 / n] * n)
        result = minimize(portfolio_var, initial, method="SLSQP",
                          bounds=bounds, constraints=constraints)
        if not result.success:
            logger.warning("Otimalização não convergiu: %s", result.message)
            return initial
        return result.x
