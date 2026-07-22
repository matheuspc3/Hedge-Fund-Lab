"""Bollinger Bands — função pura."""

import pandas as pd


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    k: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calcula as Bandas de Bollinger.

    Args:
        series: Série de preços (fechamento).
        window: Janela da média móvel (default 20).
        k: Número de desvios-padrão (default 2.0).

    Returns:
        Tupla (upper, middle, lower).

    Raises:
        ValueError: Se k < 0.
    """
    if k < 0:
        raise ValueError(f"k must be >= 0, got {k}")

    middle = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = middle + k * std
    lower = middle - k * std
    return upper, middle, lower
