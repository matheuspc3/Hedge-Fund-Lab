"""Synthetic-only executable proposal; NOT registered, approved or a phase runner.

Run: .venv/Scripts/python.exe -B scripts/check_h2_v6_evaluation_proposal.py
No CLI input, price files, LLM clients, artifact writes or scientific executions.
"""

import hashlib
import json
import math
import socket
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.artifacts import canonical_json
from src.backtesting.arena import ExecutionEngine, MarketObservation, resolve_evaluation_window
from src.backtesting.costs import CostModel
from src.backtesting.engine import Trade
from src.backtesting.metrics import (
    periodic_returns,
    sharpe_components,
    sortino_ratio,
    total_transaction_cost,
)
from src.experiments.phases import PhaseWindow, require_execution_within_phase
from src.experiments.spec import ParticipantSpec
from src.indicators.bollinger import bollinger_bands
from src.indicators.sma import sma
from src.strategies.base import SignalParticipant
from src.strategies.buy_and_hold import BuyAndHoldParticipant

B = 5000
SEED = 20261008
MEAN_BLOCK = 10
COLUMNS = ("buy_and_hold", "llm_1", "llm_2", "llm_3")


class SMAProposal(SignalParticipant):
    def __init__(self, ticker: str, fast_window: int = 50, slow_window: int = 200):
        super().__init__(ticker)
        if not 0 < fast_window < slow_window:
            raise ValueError("require 0 < fast_window < slow_window")
        self.fast_window, self.slow_window = fast_window, slow_window

    def _signal(self, close):
        if len(close) < self.slow_window or not np.isfinite(close).all():
            raise ValueError("insufficient or invalid causal SMA history")
        return 1 if sma(close, self.fast_window).iloc[-1] > sma(close, self.slow_window).iloc[-1] else -1


class BollingerProposal(SignalParticipant):
    def __init__(self, ticker: str, window: int = 20, k: float = 2.0):
        super().__init__(ticker)
        if window < 2 or not math.isfinite(k) or k <= 0:
            raise ValueError("require window >= 2 and finite k > 0")
        self.window, self.k = window, k

    def _signal(self, close):
        if len(close) < self.window or not np.isfinite(close).all():
            raise ValueError("insufficient or invalid causal Bollinger history")
        upper, _, lower = bollinger_bands(close, self.window, self.k)
        if upper.iloc[-1] == lower.iloc[-1]:
            return 0  # Proposed tie rule: collapsed bands HOLD; requires approval.
        if close.iloc[-1] <= lower.iloc[-1]:
            return 1
        return -1 if close.iloc[-1] >= upper.iloc[-1] else 0


def aligned_returns(series):
    """Reject loss of sessions; never inner-join, fill or silently drop rows."""
    if tuple(series) != COLUMNS:
        raise ValueError("exactly one benchmark and three identified runs required")
    reference = series[COLUMNS[0]].index
    if not isinstance(reference, pd.DatetimeIndex) or reference.tz is not None:
        raise ValueError("require timezone-naive session dates")
    if len(reference) < 2 or reference.has_duplicates or not reference.is_monotonic_increasing:
        raise ValueError("require at least two unique ordered sessions")
    if not reference.equals(reference.normalize()):
        raise ValueError("session index must contain dates without times")
    for values in series.values():
        if not reference.equals(values.index):
            raise ValueError("returns must have identical session indices")
        sharpe_components(values)  # Canonical numeric validation, no implicit imputation.
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
        indices[t] = rng.integers(n) if rng.random() < 1 / MEAN_BLOCK else (indices[t - 1] + 1) % n
    return indices


def centered_basic(delta, roots):
    """Finite Monte Carlo inversion: strict p < 1/20 iff lower > 0, including ties."""
    roots = np.asarray(roots, dtype=float)
    if roots.shape != (B,) or not np.isfinite(roots).all() or not math.isfinite(delta):
        raise ValueError("require exactly B finite centered roots and finite delta")
    if np.ptp(roots) == 0:
        return {"status": "INCONCLUSIVE_DEGENERATE", "p": None, "lower95": None, "superiority": False}
    k = 19 * (B + 1) // 20 + 1  # 1-based rank 4751; no interpolated quantile.
    p = (1 + int(np.count_nonzero(roots >= delta))) / (B + 1)
    lower = float(delta - np.sort(roots)[k - 1])
    assert (p < 0.05) == (lower > 0)
    return {"status": "ESTIMABLE", "p": p, "lower95": lower,
            "superiority": bool(delta > 0 and p < 0.05 and lower > 0)}


def bootstrap(series):
    frame = aligned_returns(series)
    point = aggregate(frame)
    rng = np.random.Generator(np.random.PCG64(SEED))
    roots = np.empty(B)
    degenerate = 0
    # ponytail: literal canonical Sharpe in each draw, O(B*n); optimize only
    # after approval, with equivalence checks against this offline reference.
    for b in range(B):
        sample = frame.iloc[stationary_indices(len(frame), rng)]
        sampled = aggregate(sample)
        roots[b] = sampled["delta"] - point["delta"]
        degenerate += int(sampled["sharpe_degenerate"])
    result = centered_basic(point["delta"], roots)
    if point["sharpe_degenerate"] or degenerate:
        result = {"status": "INCONCLUSIVE_DEGENERATE", "p": None, "lower95": None, "superiority": False}
    return {**point, **result, "degenerate_draws": degenerate,
            "confirmatory_contrasts": 1, "B": B, "seed": SEED, "mean_block": MEAN_BLOCK,
            "roots_sha256": hashlib.sha256(roots.astype("<f8").tobytes()).hexdigest()}


def sortino_evidence(returns):
    technical = sortino_ratio(returns, rf=0.0, mar=0.0, freq=252)
    downside = float(np.sqrt(np.mean(np.minimum(returns.astype(float), 0.0) ** 2)))
    reason = "INSUFFICIENT_OBSERVATIONS" if len(returns) < 2 else "ZERO_DOWNSIDE" if downside < 1e-15 else None
    return {"technical_value": technical, "economic_value": None if reason else technical,
            "degenerate": reason is not None, "reason": reason, "downside_deviation": downside}


def order_turnover(trades, initial_capital):
    if not math.isfinite(initial_capital) or initial_capital <= 0:
        raise ValueError("initial capital must be finite and positive")
    executed = list(trades)
    for trade in executed:
        if not isinstance(trade, Trade) or trade.type not in ("BUY", "SELL"):
            raise ValueError("executed Trade records only")
        if not all(math.isfinite(x) and x > 0 for x in (trade.price, trade.quantity)):
            raise ValueError("executed price and quantity must be finite and positive")
    notional = math.fsum(abs(t.price * t.quantity) for t in executed)
    if not math.isfinite(notional):
        raise ValueError("executed notional must be finite")
    return {"turnover": notional / initial_capital, "executed_notional": notional,
            "executed_orders": len(executed), "total_cost": total_transaction_cost(executed)}


def rejected(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("invalid input accepted")


def synthetic_checks():
    dates = pd.bdate_range("2020-01-02", periods=247)
    rng = np.random.Generator(np.random.PCG64(73))
    market = rng.normal(0.0003, 0.01, len(dates))
    series = {COLUMNS[0]: pd.Series(market, index=dates)}
    series.update({name: pd.Series(market * scale + drift, index=dates)
                   for name, scale, drift in zip(COLUMNS[1:], (0.8, 0.9, 1.1), (0.0001, -0.0002, 0.0003), strict=True)})
    frame = aligned_returns(series)
    point = aggregate(frame)
    assert point["mean"] == np.mean(point["sharpe_individual"])
    assert point["delta"] == point["mean"] - point["sharpe_buy_and_hold"]
    assert not math.isclose(point["mean"], sharpe_components(frame.iloc[:, 1:].mean(axis=1))["sharpe"])
    shifted = dict(series)
    shifted["llm_1"] = series["llm_1"].set_axis(dates + pd.Timedelta(days=1))
    rejected(lambda: aligned_returns(shifted))
    invalid = dict(series)
    invalid["llm_1"] = series["llm_1"].copy()
    invalid["llm_1"].iloc[0] = np.nan
    rejected(lambda: aligned_returns(invalid))
    rejected(lambda: aligned_returns({**series, "sma": series["llm_1"]}))
    indices = stationary_indices(len(dates), np.random.Generator(np.random.PCG64(SEED)))
    sampled = frame.iloc[indices]
    np.testing.assert_array_equal(sampled.to_numpy(), frame.to_numpy()[indices, :])
    assert all((0 <= indices) & (indices < len(dates)))
    first = bootstrap(series)
    assert first == bootstrap(series) and first["confirmatory_contrasts"] == 1
    roots = np.arange(B, dtype=float) / B
    at_rank = np.sort(roots)[4750]
    assert centered_basic(at_rank, roots)["p"] >= 0.05
    assert centered_basic(at_rank, roots)["lower95"] == 0
    assert centered_basic(np.nextafter(at_rank, np.inf), roots)["superiority"]
    assert not centered_basic(-1, roots)["superiority"]
    assert not centered_basic(0, np.zeros(B))["superiority"]
    assert centered_basic(1, np.zeros(B))["p"] is None
    ties = np.full(B, at_rank)
    ties[0] = 0
    assert not centered_basic(at_rank, ties)["superiority"]
    zeros = {name: pd.Series(np.zeros(3), index=dates[:3]) for name in COLUMNS}
    assert bootstrap(zeros)["status"] == "INCONCLUSIVE_DEGENERATE"
    positive = pd.Series([0.01, 0.02, 0.0])
    assert sortino_evidence(positive)["economic_value"] is None
    negative = pd.Series([-0.01, 0.02, 0.0])
    assert math.isclose(sortino_evidence(negative)["downside_deviation"], 0.01 / math.sqrt(3))
    assert not sortino_evidence(negative)["degenerate"]
    date = dates[0]
    trades = [Trade(date, "BUY", 10, 100, 2), Trade(date, "SELL", 12, 100, 3)]
    assert order_turnover(trades, 1000) == {"turnover": 2.2, "executed_notional": 2200,
                                          "executed_orders": 2, "total_cost": 5}
    assert order_turnover([], 1000)["turnover"] == 0
    rejected(lambda: order_turnover([Trade(date, "CANCELLED", 10, 100)], 1000))

    sma_proposal = SMAProposal("PETR4.SA")
    assert sma_proposal._signal(pd.Series(np.arange(1, 201, dtype=float))) == 1
    assert sma_proposal._signal(pd.Series(np.ones(200))) == -1
    assert sma_proposal._signal(pd.Series(np.arange(200, 0, -1, dtype=float))) == -1
    boll = BollingerProposal("PETR4.SA")
    low = pd.Series([100.0] * 19 + [80.0])
    high = pd.Series([100.0] * 19 + [120.0])
    assert boll._signal(low) == 1 and boll._signal(high) == -1
    assert boll._signal(pd.Series([100.0] * 20)) == 0
    # Two closes symmetric about the rolling mean: exact equality using k=1/sqrt(2).
    equal_lower = BollingerProposal("PETR4.SA", window=2, k=1 / math.sqrt(2))
    assert equal_lower._signal(pd.Series([102.0, 100.0])) == 1
    assert equal_lower._signal(pd.Series([100.0, 102.0])) == -1

    def observe(participant, close, offset):
        history = pd.DataFrame({"fechamento": close.to_numpy()},
                               index=pd.date_range("2019-01-01", periods=len(close)))
        observation = MarketObservation(session=dates[offset], history={"PETR4.SA": history},
                                        positions={"PETR4.SA": 0}, cash=100000, equity=100000)
        return participant.decide(observation)

    assert observe(boll, low, 0)[0].target_weight == 1
    assert observe(boll, low, 1) == []
    assert observe(boll, pd.Series([100.0] * 20), 2) == []
    assert observe(boll, high, 3)[0].target_weight == 0
    assert observe(boll, high, 4) == []
    assert observe(sma_proposal, pd.Series(np.arange(1, 201, dtype=float)), 0)[0].target_weight == 1
    assert observe(sma_proposal, pd.Series(np.arange(1, 201, dtype=float)), 1) == []
    assert observe(sma_proposal, pd.Series(np.ones(200)), 2)[0].target_weight == 0

    sessions = pd.bdate_range("2020-01-02", periods=508)
    price = np.linspace(100, 120, len(sessions))
    data = pd.DataFrame({"abertura": price, "fechamento": price + 0.1}, index=sessions)
    decision_start, decision_end, settlement = sessions[503], sessions[506], sessions[507]
    window = resolve_evaluation_window(sessions, decision_start=decision_start,
                                      decision_end=decision_end, minimum_history_sessions=504)
    assert window.warmup_sessions == 503 and window.available_history_sessions == 504
    phase = PhaseWindow("SYNTHETIC", str(decision_start.date()), str(settlement.date()))
    require_execution_within_phase(window.settlement_session, phase)
    rejected(lambda: require_execution_within_phase(settlement + pd.Timedelta(days=3), phase))
    rejected(lambda: resolve_evaluation_window(sessions, decision_start=decision_start,
                                              decision_end=settlement, minimum_history_sessions=504))
    costs = CostModel(brokerage_fixed=0, spread_bps=5, tax_rate=0.00032)
    for participant in (BuyAndHoldParticipant("PETR4.SA"), SMAProposal("PETR4.SA"), BollingerProposal("PETR4.SA")):
        result = ExecutionEngine(participant, {"PETR4.SA": data}, 100000, costs,
                                 decision_start=decision_start, decision_end=decision_end,
                                 minimum_history_sessions=504, quantity_mode="fractional_notional").run()
        assert result.equity_curve.index[0] == decision_start
        assert result.equity_curve.index[-1] == settlement
        assert len(periodic_returns(result.equity_curve)) == window.evaluated_sessions
        assert all(decision_start < t.date <= settlement for t in result.trades)
        if isinstance(participant, BuyAndHoldParticipant):
            assert len(result.trades) == 1 and result.trades[0].date == sessions[504]
            assert result.trades[0].type == "BUY"  # No invented final liquidation.
    return {"synthetic_checks": "PASS", "primary_candidate": "centered_basic_stationary_bootstrap",
            "bootstrap_draws_per_call": B, "network_calls": 0}


def preservation_checks():
    import run_cal_b4 as cal

    freeze = cal.verify_freeze()  # Existing guards; no audit/status execution.
    target = cal.OUT / "run_20261008T221200Z"
    batch = cal.base.verify_seal(target)  # Hash bytes only; no CAL-B4 outcomes.
    for anchor, digest in batch["anchor_seal_sha256"].items():
        assert cal.base.sha256_file(target / "anchors" / anchor / "sealed.json") == digest
    for name, digest in cal.read(target / "AUDIT_SEAL.json").items():
        assert cal.base.sha256_file(target / name) == digest
    gates = cal.read(target / "automatic_gates.json")["gates"]
    assert len(gates) == 12 and all(g["pass"] for g in gates.values())
    assert cal.base.sha256_file(target / "review/PRIMARY_AUTHOR.json") == "33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733"
    assert cal.read(target / "status.json")["status"] == cal.PASS
    assert freeze["participant_spec_sha256"] == "7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938"
    assert freeze["commitment_sha256"] == "35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7"
    specs = [ParticipantSpec("buy_and_hold", {"ticker": "PETR4.SA"}),
             ParticipantSpec("sma_regime_h2_proposed", {"ticker": "PETR4.SA", "fast_window": 50, "slow_window": 200}),
             ParticipantSpec("bollinger_state_h2_proposed", {"ticker": "PETR4.SA", "window": 20, "k": 2.0})]
    return {"baseline_files_verified": len(freeze["source_and_scientific_artifact_sha256"]),
            "cal_b4_anchors_sealed": len(batch["anchor_seals"]), "automatic_gates_pass": len(gates),
            "candidate_spec_sha256": {s.kind: hashlib.sha256(canonical_json(s.to_dict()).encode()).hexdigest() for s in specs}}


if __name__ == "__main__":
    if len(sys.argv) != 1 or not __debug__:
        raise SystemExit("synthetic self-check only; no arguments and no -O")
    with patch.object(socket, "socket", side_effect=AssertionError("network prohibited")), \
         patch.object(socket, "create_connection", side_effect=AssertionError("network prohibited")):
        report = {**synthetic_checks(), **preservation_checks()}
    print(json.dumps(report, indent=2))
