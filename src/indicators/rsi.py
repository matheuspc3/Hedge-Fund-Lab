"""Relative Strength Index (RSI) — função pura, suavização canônica de Wilder."""

import numpy as np
import pandas as pd

#: RSI quando a janela suavizada não tem ganho nem perda (0/0). **Convenção
#: local do projeto**, não de Wilder nem da StockCharts: a nota da planilha
#: ``cs-rsi.xls`` define só ``avg_loss = 0 → 100`` e ``avg_gain = 0 → 0``, e
#: aplicada à letra daria 100 para o 0/0. Aqui nenhum movimento em direção
#: nenhuma é o ponto neutro, e 50 não cruza nenhum dos limiares 30/70.
RSI_NO_MOVEMENT = 50.0


def _wilder_average(values: pd.Series, period: int) -> pd.Series:
    """Média de Wilder: semente simples, depois recursão ``1/period``.

    ``ewm(alpha=1/period, adjust=False)`` sozinho começaria no primeiro valor,
    não na média simples dos primeiros ``period``. Trocar o primeiro termo pela
    média simples torna a recursão do ``ewm`` exatamente a de Wilder::

        avg[period] = mean(values[1 .. period])
        avg[t]      = ((period - 1) * avg[t-1] + values[t]) / period
    """
    seeded = values.iloc[period:].copy()
    seeded.iloc[0] = values.iloc[1 : period + 1].mean()
    return seeded.ewm(alpha=1.0 / period, adjust=False).mean().reindex(values.index)


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calcula o RSI de Wilder (1978) com inicialização canônica.

    ``RSI = 100 · avg_gain / (avg_gain + avg_loss)``, algebricamente igual a
    ``100 - 100 / (1 + RS)`` sempre que ``avg_loss > 0`` e sem divisão por
    zero nos extremos:

    - ``avg_loss = 0`` e ``avg_gain > 0`` → 100;
    - ``avg_gain = 0`` e ``avg_loss > 0`` → 0;
    - ambos zero → :data:`RSI_NO_MOVEMENT`.

    Os primeiros ``period`` valores são NaN: antes de ``period`` variações não
    existe média inicial, e nenhum valor é inventado para o warm-up.

    Preço ausente (NaN) é recusado, não contornado: a média encolheria a
    semente para menos de ``period`` variações e a recursão repetiria o RSI
    anterior numa barra sem observação. O OHLCV validado do pipeline não tem
    NaN, então chegar aqui com um é violação de contrato.

    Args:
        series: Série de preços (fechamento).
        period: Período da suavização (default 14).

    Returns:
        Série com valores em [0, 100], NaN no warm-up.

    Raises:
        ValueError: Se period <= 0 ou se ``series`` contém NaN.
    """
    if period <= 0:
        raise ValueError(f"period must be > 0, got {period}")
    if series.isna().any():
        raise ValueError("series contains NaN; Wilder's RSI needs every close")

    result = pd.Series(np.nan, index=series.index, dtype=float)
    if len(series) <= period:
        return result

    delta = series.astype(float).diff()
    avg_gain = _wilder_average(delta.clip(lower=0.0), period)
    avg_loss = _wilder_average((-delta).clip(lower=0.0), period)
    total = avg_gain + avg_loss
    # NaN != 0 é verdadeiro, então o warm-up continua NaN; só o 0/0 vira 50.
    # ``(G / total) * 100`` e não ``(100 * G) / total``: a razão arredondada
    # nunca passa de 1, então o RSI nunca passa de 100 por erro de ponto flutuante.
    return ((avg_gain / total) * 100.0).where(total != 0, RSI_NO_MOVEMENT)
