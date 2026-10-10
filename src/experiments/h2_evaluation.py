"""Provisional H2 v6 evaluation contracts; no approval, freeze or live runner.

Canonical financial formulas and execution remain in their historical modules.
"""

import hashlib
import math
from types import MappingProxyType

import numpy as np
import pandas as pd

from src.artifacts import canonical_json
from src.backtesting.engine import Trade
from src.backtesting.metrics import (
    SHARPE_MIN_STD,
    periodic_returns,
    sharpe_components,
    sortino_ratio,
    total_transaction_cost,
)
from src.experiments.phases import PhaseWindow
from src.experiments.spec import (
    CostSpec,
    EvaluationSpec,
    ExecutionSpec,
    MetricSpec,
    ParticipantSpec,
)
from src.indicators.bollinger import bollinger_bands
from src.indicators.sma import sma
from src.strategies.base import SignalParticipant
from src.strategies.buy_and_hold import BuyAndHoldParticipant

AMENDMENT_STATUS = "H2_V6 EVALUATION AMENDMENT PROPOSED — AWAITING AUTHOR APPROVAL"
QUALIFIED_STATUS = "H2_V6 EVALUATION LAYER QUALIFIED OFFLINE — AWAITING FORMAL APPROVAL AND SYSTEM FREEZE"
PARTICIPANT_SHA256 = "7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938"
RESERVED_SNAPSHOT = "20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a"
TICKER = "PETR4.SA"
CAPITAL = 100000.0
BASE_COSTS = CostSpec(brokerage_fixed=0, spread_bps=5, tax_rate=0.00032)
METRICS = MetricSpec(risk_free_rate=0, mar=0, periods_per_year=252)
EXECUTION = ExecutionSpec(quantity_mode="fractional_notional")
PHASE_WINDOWS = MappingProxyType(
    {
        "VALIDATION": PhaseWindow("VALIDATION", "2024-09-02", "2025-08-29"),
        "FINAL_TEST": PhaseWindow("FINAL_TEST", "2025-09-01", "2026-08-31"),
    }
)
EVALUATION_WINDOWS = MappingProxyType(
    {
        "VALIDATION": EvaluationSpec("2024-09-02", "2025-08-28", 504),
        "FINAL_TEST": EvaluationSpec("2025-09-01", "2026-08-28", 504),
    }
)
BENCHMARK_SPECS = (
    ParticipantSpec("buy_and_hold", {"ticker": TICKER}),
    ParticipantSpec(
        "sma_regime_h2_proposed",
        {"ticker": TICKER, "fast_window": 50, "slow_window": 200},
    ),
    ParticipantSpec(
        "bollinger_state_h2_proposed", {"ticker": TICKER, "window": 20, "k": 2.0}
    ),
)
COLUMNS = ("buy_and_hold", "llm_1", "llm_2", "llm_3")
B = 5000
SEED = 20261008
MEAN_BLOCK = 10
INVALID_COST_REPLAY = "COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID"


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class SMARegimeParticipant(SignalParticipant):
    def __init__(self, ticker: str, fast_window: int = 50, slow_window: int = 200):
        super().__init__(ticker)
        if (ticker, fast_window, slow_window) != (TICKER, 50, 200):
            raise ValueError("H2 SMA identity is fixed; no tuning")
        self.fast_window, self.slow_window = fast_window, slow_window

    def _signal(self, close):
        if len(close) < 200 or not np.isfinite(close).all():
            raise ValueError("insufficient or invalid causal SMA history")
        return 1 if sma(close, 50).iloc[-1] > sma(close, 200).iloc[-1] else -1


class BollingerStateParticipant(SignalParticipant):
    def __init__(self, ticker: str, window: int = 20, k: float = 2.0):
        super().__init__(ticker)
        if (ticker, window, k) != (TICKER, 20, 2.0):
            raise ValueError("H2 Bollinger identity is fixed; no tuning")
        self.window, self.k = window, k

    def _signal(self, close):
        if len(close) < 20 or not np.isfinite(close).all():
            raise ValueError("insufficient or invalid causal Bollinger history")
        upper, _, lower = bollinger_bands(close, 20, 2.0)
        if upper.iloc[-1] == lower.iloc[-1]:
            return 0
        if close.iloc[-1] <= lower.iloc[-1]:
            return 1
        return -1 if close.iloc[-1] >= upper.iloc[-1] else 0


BENCHMARK_FACTORIES = MappingProxyType(
    {
        "buy_and_hold": BuyAndHoldParticipant,
        "sma_regime_h2_proposed": SMARegimeParticipant,
        "bollinger_state_h2_proposed": BollingerStateParticipant,
    }
)


def aligned_returns(series, expected_sessions):
    if tuple(series) != COLUMNS:
        raise ValueError("exactly B&H and three identified LLM runs required")
    index = expected_sessions
    if (
        not isinstance(index, pd.DatetimeIndex)
        or index.tz is not None
        or len(index) < 2
        or index.has_duplicates
        or not index.is_monotonic_increasing
        or not index.equals(index.normalize())
    ):
        raise ValueError("require complete, unique, ordered session dates")
    for values in series.values():
        if not index.equals(values.index):
            raise ValueError(
                "session loss, mismatch or reordering; no inner join or filling"
            )
        sharpe_components(values)
    return pd.DataFrame(series).astype(float)


def aggregate(frame):
    parts = [sharpe_components(frame[name], rf=0.0, freq=252) for name in COLUMNS]
    scores = np.array([p["sharpe"] for p in parts])
    return {
        "sharpe_individual": scores[1:].tolist(),
        "sharpe_buy_and_hold": float(scores[0]),
        "delta_individual": (scores[1:] - scores[0]).tolist(),
        "mean": float(scores[1:].mean()),
        "min": float(scores[1:].min()),
        "max": float(scores[1:].max()),
        "sd_between_runs_ddof1": float(scores[1:].std(ddof=1)),
        "delta": float(scores[1:].mean() - scores[0]),
        "sharpe_degenerate": any(p["convention_zero"] for p in parts),
    }


def stationary_indices(n, rng):
    indices = np.empty(n, dtype=np.int64)
    indices[0] = rng.integers(n)
    for t in range(1, n):
        indices[t] = (
            rng.integers(n) if rng.random() < 1 / MEAN_BLOCK else (indices[t - 1] + 1) % n
        )
    return indices


def centered_basic(delta, roots):
    roots = np.asarray(roots, dtype=float)
    if roots.shape != (B,) or not np.isfinite(roots).all() or not math.isfinite(delta):
        raise ValueError("require B finite centered roots and a finite contrast")
    if np.ptp(roots) == 0:
        return {
            "status": "INCONCLUSIVE_DEGENERATE",
            "p": None,
            "lower95": None,
            "superiority": False,
        }
    p = (1 + int(np.count_nonzero(roots >= delta))) / (B + 1)
    lower = float(delta - np.sort(roots)[4750])
    if (p < 0.05) != (lower > 0):
        raise ValueError("p/CI inversion inconsistent")
    return {
        "status": "ESTIMABLE",
        "p": p,
        "lower95": lower,
        "superiority": bool(delta > 0 and p < 0.05 and lower > 0),
    }


def bootstrap(frame):
    point = aggregate(frame)
    rng = np.random.Generator(np.random.PCG64(SEED))
    roots = np.empty(B)
    index_hash = hashlib.sha256()
    degenerate = 0
    # ponytail: O(B*n) literal canonical Sharpe, the offline reference is the
    # equivalence oracle for a future optimization; no alternative estimator.
    for b in range(B):
        indices = stationary_indices(len(frame), rng)
        index_hash.update(indices.astype("<i8").tobytes())
        sampled = aggregate(frame.iloc[indices])
        roots[b] = sampled["delta"] - point["delta"]
        degenerate += int(sampled["sharpe_degenerate"])
    result = centered_basic(point["delta"], roots)
    if point["sharpe_degenerate"] or degenerate:
        result = {
            "status": "INCONCLUSIVE_DEGENERATE",
            "p": None,
            "lower95": None,
            "superiority": False,
        }
    return {
        **point,
        **result,
        "degenerate_draws": degenerate,
        "confirmatory_contrasts": 1,
        "B": B,
        "seed": SEED,
        "mean_block": MEAN_BLOCK,
        "rank": 4751,
        "indices_sha256": index_hash.hexdigest(),
        "roots_sha256": hashlib.sha256(roots.astype("<f8").tobytes()).hexdigest(),
    }


def phase_statistics(phase, series, expected_sessions):
    if phase not in PHASE_WINDOWS:
        raise ValueError("only Validation or Final evaluation contracts exist")
    frame = aligned_returns(series, expected_sessions)
    if phase == "VALIDATION":
        return {
            **aggregate(frame),
            "confirmatory_contrasts": 0,
            "inference": "DESCRIPTIVE_ONLY",
        }
    return bootstrap(frame)


def secondary_metrics(backtest, expected_equity_sessions):
    if not backtest.equity_curve.index.equals(expected_equity_sessions):
        raise ValueError("incomplete or mismatched equity calendar")
    if (
        backtest.initial_capital != CAPITAL
        or float(backtest.equity_curve.iloc[0]) != CAPITAL
    ):
        raise ValueError("initial capital mismatch")
    returns = periodic_returns(backtest.equity_curve)
    technical = sortino_ratio(returns, rf=0.0, mar=0.0, freq=252)
    downside = float(np.sqrt(np.mean(np.minimum(returns, 0.0) ** 2)))
    reason = (
        "INSUFFICIENT_OBSERVATIONS"
        if len(returns) < 2
        else "ZERO_DOWNSIDE"
        if downside < SHARPE_MIN_STD
        else None
    )
    trades = backtest.trades
    for trade in trades:
        if (
            not isinstance(trade, Trade)
            or trade.type not in ("BUY", "SELL")
            or trade.ticker != TICKER
            or not all(math.isfinite(v) and v > 0 for v in (trade.price, trade.quantity))
            or pd.Timestamp(trade.date) not in expected_equity_sessions[1:]
        ):
            raise ValueError("only finite executed trades inside this phase count")
    notional = math.fsum(abs(t.price * t.quantity) for t in trades)
    if not math.isfinite(notional):
        raise ValueError("executed notional is not finite")
    return {
        "sortino": {
            "technical_value": technical,
            "economic_value": None if reason else technical,
            "degenerate": reason is not None,
            "reason": reason,
            "downside_deviation": downside,
            "observations": len(returns),
        },
        "turnover": notional / CAPITAL,
        "executed_notional": notional,
        "executed_orders": len(trades),
        "total_cost": total_transaction_cost(trades),
    }
