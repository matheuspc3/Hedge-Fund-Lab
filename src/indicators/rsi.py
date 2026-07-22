"""Relative Strength Index (RSI) — função pura.

Implementa o método de Wilder com suavização exponencial.
"""

import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calcula o Relative Strength Index (método de Wilder).

    Args:
        series: Série de preços (fechamento).
        period: Período para cálculo do RSI (default 14).

    Returns:
        Série com valores em [0, 100].

    Raises:
        ValueError: Se period <= 0.
    """
    if period <= 0:
        raise ValueError(f"period must be > 0, got {period}")

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()

    avg_loss = loss.replace(0, np.nan)
    rs = gain / avg_loss
    result = 100.0 - (100.0 / (1.0 + rs))
    result = result.fillna(100.0)
    result = result.clip(0.0, 100.0)
    return result
