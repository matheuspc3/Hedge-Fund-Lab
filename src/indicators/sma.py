"""Simple Moving Average (SMA) — função pura."""

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Calcula a Média Móvel Simples de *window* períodos.

    Args:
        series: Série de preços (fechamento).
        window: Número de períodos da janela (> 0).

    Returns:
        Série com a média móvel. Os primeiros (window - 1) valores são NaN.

    Raises:
        ValueError: Se window <= 0.
    """
    if window <= 0:
        raise ValueError(f"window must be > 0, got {window}")
    return series.rolling(window=window).mean()
