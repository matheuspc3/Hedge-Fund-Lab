"""Métricas canônicas de desempenho para backtesting.

As funções retornam frações decimais, não percentuais. ``freq=252``, taxa livre
de risco zero e MAR zero são defaults técnicos configuráveis; não representam
parâmetros científicos congelados do experimento.
"""

import math
from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd


def validate_equity_curve(equity_curve: pd.Series) -> pd.Series:
    """Valida e devolve uma cópia ``float`` de uma equity curve canônica."""
    if equity_curve.empty:
        raise ValueError("equity_curve series is empty")
    if not isinstance(equity_curve.index, pd.DatetimeIndex):
        raise ValueError("equity_curve index must be a DatetimeIndex")
    if equity_curve.index.has_duplicates:
        raise ValueError("equity_curve index must not contain duplicates")
    if not equity_curve.index.is_monotonic_increasing:
        raise ValueError("equity_curve index must be sorted")

    try:
        curve = equity_curve.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("equity_curve values must be numeric") from exc
    if not np.isfinite(curve.to_numpy()).all():
        raise ValueError("equity_curve values must be finite")
    return curve


def _validated_returns(returns: pd.Series) -> pd.Series:
    if returns.empty:
        raise ValueError("returns series is empty")
    try:
        clean = returns.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("returns values must be numeric") from exc
    if not np.isfinite(clean.to_numpy()).all():
        raise ValueError("returns values must be finite")
    return clean


def periodic_returns(equity_curve: pd.Series) -> pd.Series:
    """Calcula retornos simples entre observações consecutivas da curva."""
    curve = validate_equity_curve(equity_curve)
    returns = curve.pct_change(fill_method=None).dropna()
    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("equity_curve produces non-finite periodic returns")
    return returns


def total_return(equity_curve: pd.Series) -> float:
    """Retorno total: ``final_equity / initial_equity - 1``."""
    curve = validate_equity_curve(equity_curve)
    if curve.iloc[0] == 0:
        raise ValueError("initial equity must be non-zero")
    return float(curve.iloc[-1] / curve.iloc[0] - 1.0)


def cumulative_return(equity_curve: pd.Series) -> float:
    """Alias compatível para :func:`total_return`."""
    return total_return(equity_curve)


def annualized_return(equity_curve: pd.Series, freq: int = 252) -> float:
    """CAGR técnico com ``freq`` observações por ano (default: 252)."""
    curve = validate_equity_curve(equity_curve)
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if len(curve) < 2:
        return 0.0
    ratio = curve.iloc[-1] / curve.iloc[0]
    if ratio < 0:
        raise ValueError("annualized return requires non-negative endpoint equity")
    return float(ratio ** (freq / (len(curve) - 1)) - 1.0)


def annualized_volatility(returns: pd.Series, freq: int = 252) -> float:
    """Volatilidade amostral anualizada (default técnico: 252 períodos)."""
    clean = _validated_returns(returns)
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if len(clean) < 2:
        return 0.0
    vol = clean.std(ddof=1)
    if vol < 1e-15 or np.isnan(vol):
        return 0.0
    return float(vol * np.sqrt(freq))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0, freq: int = 252) -> float:
    """Sharpe anualizado sobre excess returns.

    ``rf`` é uma taxa anual, convertida pelo default técnico ``rf / freq``.
    Retorna zero quando não há volatilidade amostral.
    """
    clean = _validated_returns(returns)
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if len(clean) < 2:
        return 0.0
    vol = clean.std(ddof=1)
    if vol < 1e-15 or np.isnan(vol):
        return 0.0
    excess = clean - rf / freq
    return float(excess.mean() / vol * np.sqrt(freq))


def sortino_ratio(
    returns: pd.Series, rf: float = 0.0, mar: float = 0.0, freq: int = 252
) -> float:
    """Sortino anualizado com downside deviation em relação ao MAR periódico.

    ``rf`` é anual e ``mar`` é periódico. Ambos são defaults técnicos
    configuráveis e ainda não constituem a política científica congelada.
    """
    clean = _validated_returns(returns)
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if len(clean) < 2:
        return 0.0
    downside = np.minimum(clean - mar, 0.0)
    downside_deviation = float(np.sqrt(np.mean(np.square(downside))))
    if downside_deviation < 1e-15:
        return 0.0
    excess = clean - rf / freq
    return float(excess.mean() / downside_deviation * np.sqrt(freq))


def drawdown_series(equity_curve: pd.Series) -> pd.Series:
    """Drawdown por observação, calculado diretamente da equity curve."""
    curve = validate_equity_curve(equity_curve)
    peak = curve.cummax()
    return (curve - peak) / peak


def max_drawdown(equity_curve: pd.Series) -> float:
    """Maior queda pico-vale como fração negativa."""
    return float(drawdown_series(equity_curve).min())


def max_drawdown_duration(equity_curve: pd.Series) -> int:
    """Maior número de observações consecutivas abaixo do pico anterior."""
    in_drawdown = drawdown_series(equity_curve) < 0
    max_duration = current_duration = 0
    for below_peak in in_drawdown:
        current_duration = current_duration + 1 if below_peak else 0
        max_duration = max(max_duration, current_duration)
    return max_duration


def turnover(weights_series: pd.DataFrame) -> float:
    """Mudança absoluta média dos pesos observados entre períodos.

    Esta é uma definição técnica legada; como pesos efetivos também variam por
    drift de mercado, ela ainda não é o turnover científico de ordens congelado.
    """
    if len(weights_series) < 2:
        return 0.0
    return float(weights_series.diff().abs().sum(axis=1).iloc[1:].mean())


def total_transaction_cost(trades: Iterable[Any]) -> float:
    """Soma ``trade.cost`` apenas dos trades efetivamente executados."""
    total = 0.0
    for trade in trades:
        try:
            cost = float(trade.cost)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("each trade must expose a numeric cost") from exc
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("trade cost must be finite and non-negative")
        total += cost
    return total


def performance_metrics(
    equity_curve: pd.Series,
    *,
    rf: float = 0.0,
    mar: float = 0.0,
    freq: int = 252,
) -> dict[str, float | int]:
    """Calcula o conjunto canônico atual a partir de uma única equity curve."""
    curve = validate_equity_curve(equity_curve)
    returns = periodic_returns(curve)
    return {
        "total_return": total_return(curve),
        "annualized_return": annualized_return(curve, freq=freq),
        "annualized_volatility": (
            annualized_volatility(returns, freq=freq) if not returns.empty else 0.0
        ),
        "sharpe_ratio": (
            sharpe_ratio(returns, rf=rf, freq=freq) if not returns.empty else 0.0
        ),
        "sortino_ratio": (
            sortino_ratio(returns, rf=rf, mar=mar, freq=freq)
            if not returns.empty
            else 0.0
        ),
        "max_drawdown": max_drawdown(curve),
        "max_drawdown_duration": max_drawdown_duration(curve),
    }


def calmar_ratio(returns: pd.Series, max_dd: float, freq: int = 252) -> float:
    """Calmar técnico: retorno composto anualizado dividido por ``|max_dd|``."""
    clean = _validated_returns(returns)
    if freq <= 0:
        raise ValueError("freq must be > 0")
    if max_dd == 0.0:
        return 0.0
    compounded = float((1.0 + clean).prod())
    if compounded <= 0:
        raise ValueError("calmar ratio requires a positive compounded return")
    ann_return = compounded ** (freq / len(clean)) - 1.0
    return ann_return / abs(max_dd)
