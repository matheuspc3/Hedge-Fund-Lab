"""Métricas de desempenho para backtesting.

Todas as funções são puras: recebem séries pandas e retornam valores numéricos.
"""

import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, freq: int = 252) -> float:
    """Sharpe Ratio anualizado.

    Args:
        returns: Série de retornos diários.
        rf: Taxa livre de risco anualizada (decimal).
        freq: Frequência de anualização (252 para dias úteis).

    Returns:
        Sharpe Ratio anualizado. Retorna 0 se volatilidade for zero.

    Raises:
        ValueError: Se a série for vazia.
    """
    if returns.empty:
        raise ValueError("returns series is empty")
    if len(returns) < 2:
        return 0.0

    excess = returns - (rf / freq)
    mean_excess = excess.mean()
    vol = returns.std(ddof=1)

    if vol < 1e-15 or np.isnan(vol):
        return 0.0

    return float((mean_excess / vol) * np.sqrt(freq))


def sortino_ratio(
    returns: pd.Series, rf: float = 0.0, mar: float = 0.0, freq: int = 252
) -> float:
    """Sortino Ratio anualizado.

    Considera apenas a volatilidade dos retornos negativos (downside deviation).

    Args:
        returns: Série de retornos diários.
        rf: Taxa livre de risco anualizada (decimal).
        mar: Retorno mínimo aceitável (MAR) diário.
        freq: Frequência de anualização.

    Returns:
        Sortino Ratio anualizado. Retorna 0 se downside deviation for zero.

    Raises:
        ValueError: Se a série for vazia.
    """
    if returns.empty:
        raise ValueError("returns series is empty")
    if len(returns) < 2:
        return 0.0

    excess = returns - (rf / freq)
    mean_excess = excess.mean()

    downside = returns[returns < mar]
    if len(downside) < 2:
        return 0.0

    downside_dev = downside.std(ddof=1)
    if downside_dev < 1e-15 or np.isnan(downside_dev):
        return 0.0

    return float((mean_excess / downside_dev) * np.sqrt(freq))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Máximo drawdown da curva de equity.

    Args:
        equity_curve: Série do patrimônio líquido ao longo do tempo.

    Returns:
        Drawdown máximo como fração negativa (ex: -0.20 = -20%).

    Raises:
        ValueError: Se a série for vazia.
    """
    if equity_curve.empty:
        raise ValueError("equity_curve series is empty")
    if len(equity_curve) < 2:
        return 0.0

    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()


def max_drawdown_duration(equity_curve: pd.Series) -> int:
    """Duração máxima do drawdown em períodos.

    Mede o maior número de períodos entre um pico e a recuperação
    (volta ao valor do pico anterior).

    Args:
        equity_curve: Série do patrimônio líquido.

    Returns:
        Número de períodos do drawdown mais longo.

    Raises:
        ValueError: Se a série for vazia.
    """
    if equity_curve.empty:
        raise ValueError("equity_curve series is empty")
    if len(equity_curve) < 2:
        return 0

    peak = equity_curve.expanding().max()
    in_drawdown = equity_curve < peak

    max_dur = 0
    current_dur = 0

    for i in range(len(in_drawdown)):
        if in_drawdown.iloc[i]:
            current_dur += 1
        else:
            if current_dur > max_dur:
                max_dur = current_dur
            current_dur = 0

    return max(max_dur, current_dur)


def turnover(weights_series: pd.DataFrame) -> float:
    """Turnover médio da carteira.

    Mede a soma absoluta das mudanças de peso entre períodos consecutivos.

    Args:
        weights_series: DataFrame com pesos ao longo do tempo
                       (colunas = ativos, index = tempo).

    Returns:
        Turnover médio diário.
    """
    if len(weights_series) < 2:
        return 0.0

    diffs = weights_series.diff().abs().sum(axis=1)
    return diffs.iloc[1:].mean()


def cumulative_return(equity_curve: pd.Series) -> float:
    """Retorno acumulado do período.

    Args:
        equity_curve: Série do patrimônio líquido.

    Returns:
        Retorno total como fração (ex: 0.50 = +50%).
    """
    if equity_curve.empty:
        return 0.0
    return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1.0


def annualized_volatility(returns: pd.Series, freq: int = 252) -> float:
    """Volatilidade anualizada dos retornos.

    Args:
        returns: Série de retornos diários.
        freq: Frequência de anualização.

    Returns:
        Volatilidade anualizada.

    Raises:
        ValueError: Se a série for vazia.
    """
    if returns.empty:
        raise ValueError("returns series is empty")
    if len(returns) < 2:
        return 0.0

    vol = returns.std(ddof=1)
    if vol < 1e-15 or np.isnan(vol):
        return 0.0
    return float(vol * np.sqrt(freq))


def calmar_ratio(returns: pd.Series, max_dd: float, freq: int = 252) -> float:
    """Calmar Ratio: retorno anualizado / |max_drawdown|.

    Args:
        returns: Série de retornos diários.
        max_dd: Maximum drawdown (negativo).
        freq: Frequência de anualização.

    Returns:
        Calmar Ratio. Retorna 0 se max_dd for 0.
    """
    if max_dd == 0.0:
        return 0.0

    total_ret = cumulative_return(pd.Series(np.exp(returns.cumsum())))
    # Anualiza o retorno total
    n_years = len(returns) / freq
    ann_return = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0.0

    return ann_return / abs(max_dd)
