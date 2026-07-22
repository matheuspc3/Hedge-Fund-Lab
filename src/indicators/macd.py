"""MACD (Moving Average Convergence Divergence) — função pura."""

import pandas as pd


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calcula o MACD, linha de sinal e histograma.

    Args:
        series: Série de preços (fechamento).
        fast: Período da EMA rápida (default 12).
        slow: Período da EMA lenta (default 26).
        signal: Período da linha de sinal (default 9).

    Returns:
        Tupla (macd_line, signal_line, histogram).

    Raises:
        ValueError: Se fast >= slow.
    """
    if fast >= slow:
        raise ValueError(f"fast ({fast}) must be < slow ({slow})")

    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
