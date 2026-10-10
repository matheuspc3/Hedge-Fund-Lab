"""Runnable offline qualification: generated prices, mocks and existing guards.

No price-file argument or live option. Optional report path is metadata only.
"""

# ruff: noqa: E402 -- standalone entry point establishes repository imports.

import argparse
import json
import socket
import sys
import tempfile
import time
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.agents.llm_client import MockLLMClient
from src.agents.state import PortfolioAction, RiskVerdict, TechnicalEvidenceResponse
from src.backtesting.arena import MarketObservation, resolve_evaluation_window
from src.backtesting.engine import BacktestResult, Trade
from src.backtesting.metrics import sharpe_components
from src.experiments import h2_evaluation as ev
from src.experiments.h2_evaluation_offline import (
    OfflineEvaluationBatch,
    no_network,
    source_hashes,
    synthetic_fixture,
)
from src.experiments.participants import PARTICIPANT_REGISTRY
from src.experiments.phases import require_execution_within_phase
from src.experiments.runner import ExperimentRunner
from src.experiments.spec import ParticipantSpec

CHECKS = []


def passed(name):
    CHECKS.append(name)
    print("PASS", name, flush=True)


def rejected(fn, error=Exception, text=None):
    try:
        fn()
    except error as exc:
        if text is not None:
            assert text in str(exc), str(exc)
        return exc
    raise AssertionError("invalid operation accepted")


class Factory:
    def __init__(self, signal="MANTER"):
        self.clients = []
        self.signal = signal

    def __call__(self, slot):
        signals = ["COMPRA", "VENDA"] if self.signal == "TRADE" else [self.signal]
        technical = [
            {
                "signal": signal,
                "confidence": 0.6,
                "evidence": [
                    {
                        "code": "RSI_CURRENT",
                        "role": "NEUTRAL" if signal == "MANTER" else f"SUPPORTS_{signal}",
                    }
                ],
            }
            for signal in signals
            for _ in range(5)
        ]
        mock = MockLLMClient(
            {
                TechnicalEvidenceResponse: technical,
                RiskVerdict: {
                    "verdict": "APROVADO",
                    "analysis": "Métricas atuais dentro dos limites informados.",
                },
                PortfolioAction: [
                    {
                        "decision": signal,
                        "reasoning": "Consenso e veto condicionais respeitados.",
                    }
                    for signal in signals
                ],
            }
        )
        self.clients.append(mock)
        return mock

    @property
    def calls(self):
        return sum(len(c.calls) for c in self.clients)


def metrics_and_benchmarks():
    dates = pd.bdate_range("2020-01-02", periods=247)
    rng = np.random.Generator(np.random.PCG64(73))
    market = rng.normal(0.0003, 0.01, len(dates))
    series = {ev.COLUMNS[0]: pd.Series(market, index=dates)}
    series.update(
        {
            name: pd.Series(market * scale + drift, index=dates)
            for name, scale, drift in zip(
                ev.COLUMNS[1:], (0.8, 0.9, 1.1), (0.0001, -0.0002, 0.0003), strict=True
            )
        }
    )
    frame = ev.aligned_returns(series, dates)
    stats = ev.phase_statistics("VALIDATION", series, dates)
    assert stats["confirmatory_contrasts"] == 0 and "p" not in stats
    assert stats["mean"] == np.mean(stats["sharpe_individual"])
    assert not np.isclose(
        stats["mean"], sharpe_components(frame.iloc[:, 1:].mean(axis=1))["sharpe"]
    )
    bad = dict(series)
    bad["llm_1"] = bad["llm_1"].iloc[1:]
    rejected(lambda: ev.aligned_returns(bad, dates))
    rejected(lambda: ev.aligned_returns(series, dates[:-1]))
    rejected(lambda: ev.aligned_returns({**series, "sma": series["llm_1"]}, dates))
    bad["llm_1"] = pd.Series(np.nan, index=dates)
    rejected(lambda: ev.aligned_returns(bad, dates))
    passed("SF-B1/B2/B3: exact 3 runs, mean Sharpes, complete temporal pairing")

    import check_h2_v6_evaluation_proposal as reference

    indices = ev.stationary_indices(
        len(frame), np.random.Generator(np.random.PCG64(ev.SEED))
    )
    np.testing.assert_array_equal(
        indices,
        reference.stationary_indices(
            len(frame), np.random.Generator(np.random.PCG64(ev.SEED))
        ),
    )
    np.testing.assert_array_equal(
        frame.iloc[indices].to_numpy(), frame.to_numpy()[indices, :]
    )
    first = ev.phase_statistics("FINAL_TEST", series, dates)
    second = ev.phase_statistics("FINAL_TEST", series, dates)
    assert first == second
    oracle = reference.bootstrap(series)
    for name in oracle:
        assert first[name] == oracle[name], name
    roots = np.arange(ev.B, dtype=float) / ev.B
    rank = roots[4750]
    assert ev.centered_basic(rank, roots)["lower95"] == 0
    assert ev.centered_basic(rank, roots)["p"] >= 0.05
    assert ev.centered_basic(np.nextafter(rank, np.inf), roots)["superiority"]
    assert not ev.centered_basic(-1, roots)["superiority"]
    roots[4750:] = rank
    assert not ev.centered_basic(rank, roots)["superiority"]
    assert ev.centered_basic(1, np.zeros(ev.B))["p"] is None
    passed(
        "SF-B4: A only, B5000, PCG64 determinism, paired indices, prototype equivalence, ties/p/CI"
    )

    sma = ev.SMARegimeParticipant(ev.TICKER)
    boll = ev.BollingerStateParticipant(ev.TICKER)
    assert sma._signal(pd.Series(np.arange(1, 201, dtype=float))) == 1
    assert sma._signal(pd.Series(np.ones(200))) == -1
    assert sma._signal(pd.Series(np.arange(200, 0, -1, dtype=float))) == -1
    low, high = pd.Series([100.0] * 19 + [80.0]), pd.Series([100.0] * 19 + [120.0])
    assert boll._signal(low) == 1 and boll._signal(high) == -1
    assert boll._signal(pd.Series([100.0] * 20)) == 0
    # Patch only indicator output in the test to exercise exact inclusive boundary.
    import src.experiments.h2_evaluation as module

    with patch.object(
        module,
        "bollinger_bands",
        return_value=(pd.Series([120.0]), pd.Series([110.0]), pd.Series([100.0])),
    ):
        assert boll._signal(pd.Series([100.0] * 20)) == 1
        assert boll._signal(pd.Series([120.0] * 20)) == -1

    def observation(close, session):
        return MarketObservation(
            session=session,
            history={ev.TICKER: pd.DataFrame({"fechamento": close})},
            positions={ev.TICKER: 0},
            cash=ev.CAPITAL,
            equity=ev.CAPITAL,
        )

    assert boll.decide(observation(low, dates[0]))[0].target_weight == 1
    assert boll.decide(observation(low, dates[1])) == []
    assert boll.decide(observation(pd.Series([100.0] * 20), dates[2])) == []
    assert boll.decide(observation(high, dates[3]))[0].target_weight == 0
    rejected(lambda: ev.SMARegimeParticipant(ev.TICKER, 49, 200))
    rejected(lambda: ev.BollingerStateParticipant(ev.TICKER, 21, 2))
    hashes = [ev.digest(s.to_dict()) for s in ev.BENCHMARK_SPECS]
    assert hashes == [
        "cbdb92508d9766c5668b2500eea837cce3f5384d117f08a61765765829be0ef1",
        "9fec52feb42a4dcea4ff7ca6973db348e03cf3efb92fe64252ac32e373f02bc5",
        "1ba8fddb165ec8b4bec5025f7be1ee38a8ff5e5e30d7e88c9b24958e2ec47345",
    ]
    passed(
        "SF-B5: regime, equality, collapsed bands, state, no rebalancing, specs/hashes, no tuning"
    )

    days = pd.bdate_range("2020-01-02", periods=4)
    positive = BacktestResult(
        pd.Series([1e5, 101000, 102000, 102000], index=days), [], ev.CAPITAL, 102000
    )
    result = ev.secondary_metrics(positive, days)
    assert (
        result["sortino"]["economic_value"] is None
        and result["sortino"]["technical_value"] == 0
    )
    negative = BacktestResult(
        pd.Series([1e5, 99000, 100980, 100980], index=days), [], ev.CAPITAL, 100980
    )
    assert np.isclose(
        ev.secondary_metrics(negative, days)["sortino"]["downside_deviation"],
        0.01 / np.sqrt(3),
    )
    negative.trades = [
        Trade(days[1], "BUY", 10, 100, 2, ev.TICKER),
        Trade(days[2], "SELL", 12, 100, 3, ev.TICKER),
    ]
    metrics = ev.secondary_metrics(negative, days)
    assert (
        metrics["turnover"] == 0.022
        and metrics["executed_orders"] == 2
        and metrics["total_cost"] == 5
    )
    negative.trades.append(Trade(days[2], "CANCELLED", 10, 1, 0, ev.TICKER))
    rejected(lambda: ev.secondary_metrics(negative, days))
    passed(
        "SF-B6: Sortino economic null, complete downside sample, executed notional and costs"
    )

    sessions = pd.bdate_range("2020-01-02", periods=508)
    window = resolve_evaluation_window(
        sessions,
        decision_start=sessions[503],
        decision_end=sessions[506],
        minimum_history_sessions=504,
    )
    assert window.warmup_sessions == 503 and window.available_history_sessions == 504
    rejected(
        lambda: resolve_evaluation_window(
            sessions,
            decision_start=sessions[502],
            decision_end=sessions[506],
            minimum_history_sessions=504,
        )
    )
    for phase, spec in ev.EVALUATION_WINDOWS.items():
        require_execution_within_phase(
            ev.PHASE_WINDOWS[phase].end, ev.PHASE_WINDOWS[phase]
        )
        rejected(
            lambda phase=phase: require_execution_within_phase(
                pd.Timestamp(ev.PHASE_WINDOWS[phase].end) + pd.Timedelta(days=3),
                ev.PHASE_WINDOWS[phase],
            )
        )
        assert spec.minimum_history_sessions == 504
    passed("phase boundaries and inclusive warmup 504=503+1")
    return {
        "synthetic_bootstrap": first,
        "benchmark_spec_sha256": dict(
            zip([s.kind for s in ev.BENCHMARK_SPECS], hashes, strict=True)
        ),
    }


def integration(root, cleanup):
    def batch(*args, **kwargs):
        result = OfflineEvaluationBatch(*args, **kwargs)
        cleanup.callback(result.close)
        return result

    original_registry = dict(PARTICIPANT_REGISTRY)
    snapshot = synthetic_fixture(root)
    factory = Factory()
    baseline = batch(root / "validation", snapshot, "VALIDATION", mock_factory=factory)
    rejected(
        lambda: OfflineEvaluationBatch(
            root / "premature_final", snapshot, "FINAL_TEST", mock_factory=Factory()
        ),
        text="Validation",
    )
    rejected(lambda: baseline.require_release(snapshot, source_hashes()), text="three")
    rejected(
        lambda: OfflineEvaluationBatch(
            root / "reserved",
            replace(snapshot, snapshot_id=ev.RESERVED_SNAPSHOT),
            "VALIDATION",
            mock_factory=Factory(),
        ),
        text="reserved",
    )
    with no_network():
        rejected(
            lambda: socket.create_connection(("generativelanguage.googleapis.com", 443)),
            text="forbids network",
        )
    passed("offline/reserved-data/provider guard and premature Final")

    # Fail after all R01 mock calls were durably banked, before publication.
    with patch.object(
        ExperimentRunner,
        "persist",
        side_effect=OSError("simulated interrupted persistence"),
    ):
        rejected(baseline.execute, OSError)
    before = factory.calls
    assert len(factory.clients) == 1 and before > 0
    assert (
        baseline.db.execute("SELECT state FROM slots WHERE slot='L01'").fetchone()[0]
        == "STARTED"
    )
    summary = baseline.execute()
    assert len(factory.clients) == 3
    assert (
        len(factory.clients[0].calls) == before
    )  # R01 recovered without a new inference.
    assert len({id(c) for c in factory.clients}) == 3
    assert summary["R"] == 3 and summary["statistics"]["confirmatory_contrasts"] == 0
    after = factory.calls
    assert baseline.execute() == summary and factory.calls == after
    assert PARTICIPANT_REGISTRY == original_registry
    passed(
        "R3 isolated calls, partial persistence, exact recovery, command idempotency, registry restored"
    )

    # Baseline B&H enters once; no fictional settlement sale.
    bh = baseline._load("buy_and_hold", baseline._spec(ev.BENCHMARK_SPECS[0]))
    assert len(bh["backtest"].trades) == 1 and bh["backtest"].trades[0].type == "BUY"
    assert bh["backtest"].trades[0].date > pd.Timestamp("2024-09-02")
    assert bh["backtest"].equity_curve.index[-1] == pd.Timestamp("2025-08-29")
    assert baseline.require_release(
        snapshot, source_hashes()
    )  # Inactive/degenerated LLM still releases on integrity.
    passed("B&H close/open settlement and release without a positive-performance gate")

    costs = baseline.cost_sensitivity()
    assert set(costs) == {"0", "5", "10", "20"}
    assert all(r["status"] == "BASELINE_REUSED" for r in costs["5"]["individual"])
    assert all(
        r["status"] == "COMPLETE_EXACT_REPLAY"
        for b in ("0", "10", "20")
        for r in costs[b]["individual"]
    )
    assert factory.calls == after
    assert baseline.cost_sensitivity() == costs and factory.calls == after
    assert (
        len(
            baseline.db.execute(
                "SELECT slot FROM slots WHERE state='COMPLETE'"
            ).fetchall()
        )
        == 24
    )
    passed(
        "all cost dispositions, baseline reuse, exact state replay, deterministic benchmarks once, no new mock inference"
    )

    final_factory = Factory()
    final = batch(
        root / "final",
        snapshot,
        "FINAL_TEST",
        mock_factory=final_factory,
        validation=baseline,
    )
    final_summary = final.execute()
    assert (
        len(final_factory.clients) == 3
        and final_summary["statistics"]["confirmatory_contrasts"] == 1
    )
    assert final_summary["statistics"]["status"] == "INCONCLUSIVE_DEGENERATE"
    assert final_summary["statistics"]["p"] is None
    passed(
        "synthetic Final only after complete matching Validation; one test, degeneracy preserved"
    )

    # Published output exists but its slot wasn't sealed (crash boundary).
    baseline.db.execute("UPDATE slots SET state='STARTED',seal=NULL WHERE slot='L01'")
    baseline.db.commit()
    old_bytes = (baseline._path("L01") / "llm_calls.jsonl").read_bytes()
    assert baseline.execute() == summary and factory.calls == after
    assert (baseline._path("L01") / "llm_calls.jsonl").read_bytes() == old_bytes
    passed(
        "crash after atomic publication recovers by exact verification without overwriting evidence"
    )

    bad_plan = dict(baseline.plan)
    baseline.plan["R"] = 4
    rejected(baseline.execute, text="identity changed")
    baseline.plan = bad_plan
    baseline.llm_spec = ParticipantSpec(
        "llm_agent", {**baseline.llm_spec.params, "risk_max_drawdown": 0.15}
    )
    rejected(baseline.execute, text="identity changed")
    baseline.llm_spec = ParticipantSpec(
        **json.loads((ROOT / "docs/evidence/cal_b4/protocol_freeze_v1.json").read_text())[
            "participant_spec"
        ]
    )
    path = baseline._path("L01") / "equity.csv"
    original = path.read_bytes()
    path.write_bytes(original + b"\n")
    rejected(lambda: final.execute(), text="artifact changed")
    path.write_bytes(original)
    assert baseline.require_release(snapshot, source_hashes())
    passed(
        "tuning/identity guards and corrupted Validation blocks Final regardless of performance"
    )

    # A genuinely partial call bank must not fill its missing suffix on rerun.
    class FailingMock(MockLLMClient):
        async def generate(self, *args, **kwargs):
            if self.calls:
                raise RuntimeError("synthetic partial scientific failure")
            return await super().generate(*args, **kwargs)

    failing_clients = []

    def failing_factory(slot):
        client = FailingMock(Factory()(slot).responses)
        failing_clients.append(client)
        return client

    broken = batch(root / "partial", snapshot, "VALIDATION", mock_factory=failing_factory)
    rejected(broken.execute)
    failed_calls = sum(len(c.calls) for c in failing_clients)
    rejected(broken.execute)
    assert (
        len(failing_clients) == 1
        and sum(len(c.calls) for c in failing_clients) == failed_calls
    )
    assert broken.db.execute("SELECT slot FROM slots").fetchall() == [("L01",)]
    rejected(lambda: broken.require_release(snapshot, source_hashes()))
    passed(
        "partial call failure: no replacement, no missing-call inference, no premature release"
    )

    # Holdings/drawdown change under costs; exact matching must be honored.
    buying_factory = Factory("TRADE")
    buying = batch(root / "buying", snapshot, "VALIDATION", mock_factory=buying_factory)
    buying_summary = buying.execute()
    buying_calls = buying_factory.calls
    buying_costs = buying.cost_sensitivity()
    invalid = [
        r
        for b in ("0", "10", "20")
        for r in buying_costs[b]["individual"]
        if r["status"] == ev.INVALID_COST_REPLAY
    ]
    assert invalid and buying_factory.calls == buying_calls
    for row in invalid:
        assert row["metrics"] is None and row["reason"] and row["affected_identity"]
    for spread in ("0", "10", "20"):
        if any(
            r["status"] == ev.INVALID_COST_REPLAY
            for r in buying_costs[spread]["individual"]
        ):
            assert buying_costs[spread]["statistics"] is None
    assert buying.require_release(snapshot, source_hashes())
    assert buying.summary() == buying_summary
    assert (
        buying.cost_sensitivity() == buying_costs and buying_factory.calls == buying_calls
    )
    passed(
        "divergent cost replay: identity/reason, no complete metrics, no subset average, baseline still releases"
    )
    assert PARTICIPANT_REGISTRY == original_registry
    return {
        "validation": summary,
        "final": final_summary,
        "costs_exact": costs,
        "costs_divergent": buying_costs,
        "invalid_cost_dispositions": len(invalid),
        "baseline_mock_calls": after,
        "buying_mock_calls": buying_calls,
    }


def preservation():
    import run_cal_b4 as cal

    freeze = cal.verify_freeze()
    target = cal.OUT / "run_20261008T221200Z"
    batch = cal.base.verify_seal(target)
    for anchor, sha in batch["anchor_seal_sha256"].items():
        assert cal.base.sha256_file(target / "anchors" / anchor / "sealed.json") == sha
    for name, sha in cal.read(target / "AUDIT_SEAL.json").items():
        assert cal.base.sha256_file(target / name) == sha
    gates = cal.read(target / "automatic_gates.json")["gates"]
    assert len(gates) == 12 and all(g["pass"] for g in gates.values())
    assert cal.read(target / "status.json")["status"] == cal.PASS
    assert (
        cal.base.sha256_file(target / "review/PRIMARY_AUTHOR.json")
        == "33db64913ace88d2b5c72bcdc2b37b608f939e4ade0e681b4a46dbbbb1474733"
    )
    passed(
        "frozen H2 v6 and CAL-B4: 6752 sources/artifacts, guards, raw seals, audit, review, status"
    )
    return {
        "baseline_files": len(freeze["source_and_scientific_artifact_sha256"]),
        "sealed_anchors": len(batch["anchor_seals"]),
        "automatic_PASS": len(gates),
        "participant_sha256": freeze["participant_spec_sha256"],
        "commitment_sha256": freeze["commitment_sha256"],
    }


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("qualification assertions require no -O")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    temp_root = ROOT / ".pytest_temp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root, prefix="h2-evaluation-") as folder:
        with no_network(), ExitStack() as cleanup:
            report = {
                "metrics": metrics_and_benchmarks(),
                "integration": integration(Path(folder), cleanup),
                "preservation": preservation(),
            }
    report.update(
        {
            "qualification_status": ev.QUALIFIED_STATUS,
            "amendment_status": ev.AMENDMENT_STATUS,
            "scientific_approval": False,
            "system_freeze_executed": False,
            "ready_for_validation": False,
            "validation_real_executed": False,
            "final_real_executed": False,
            "provider_calls": 0,
            "data": "GENERATED_SYNTHETIC_ONLY",
            "mock_run_artifacts": "TEMPORARY — REMOVED AFTER QUALIFICATION",
            "checks": CHECKS,
            "check_groups": len(CHECKS),
            "sources_sha256": source_hashes(),
            "elapsed_seconds": round(time.perf_counter() - started, 2),
        }
    )
    if args.report:
        destination = args.report.resolve()
        if not destination.is_relative_to(ROOT) or destination.is_relative_to(
            ROOT / "docs/evidence/cal_b4"
        ):
            raise SystemExit(
                "report must stay in workspace outside frozen CAL-B4 evidence"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise SystemExit("qualification report already exists; no overwrite")
        destination.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(ev.QUALIFIED_STATUS, flush=True)
