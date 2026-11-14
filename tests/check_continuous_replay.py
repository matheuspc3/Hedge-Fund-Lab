"""One assert-based check for retries, crash recovery, cap, causality and six books."""
import json
import sqlite3
import sys
import tempfile
import numpy as np
import pandas as pd
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuous_replay as c
from continuous_replay_runtime import Budget, BudgetStop, RecoveryStop, TestCrash


def runtime():
    get_weights = c.bind(c.MinVariancePortfolio.get_weights, minimize=c.numerical_minimize)
    dates = pd.bdate_range("2025-01-01", periods=253)
    angle = np.arange(252) * 2 * np.pi / 252
    solutions = []
    for factor in (0.01, 1, 3):
        returns = {"A": .03 * factor * np.cos(angle), "B": .01 * factor * np.sin(angle)}
        frames = {t: pd.DataFrame({"fechamento": np.r_[100, 100 * np.cumprod(1 + values)]}, index=dates) for t, values in returns.items()}
        weights = get_weights(c.MinVariancePortfolio(), frames, dates[-1])
        assert abs(weights["A"] - .1) < 1e-4 and abs(weights["B"] - .9) < 1e-4, weights
        solutions.append(weights)
    flat = {t: pd.DataFrame({"fechamento": np.ones(253) * 100}, index=dates) for t in ("A", "B")}
    assert get_weights(c.MinVariancePortfolio(), flat, dates[-1]) == {"A": .5, "B": .5}
    diagnostic = c.r.checked(c.ROOT / "optimizer_diagnostic.json")
    for sample in diagnostic["samples"]:
        cov = np.array(sample["covariance"])
        result = c.numerical_minimize(lambda w: float(w @ cov @ w), np.full(5, .2), method="SLSQP", bounds=[(0, 1)] * 5, constraints={"type": "eq", "fun": lambda w: w.sum() - 1})
        assert result.success and np.allclose(result.x, sample["scaled_reference"]["weights"], atol=1e-6)
        gradient = 2 * cov @ result.x / result.objective_scale
        active = result.x > 1e-6
        lagrange = np.mean(gradient[active])
        assert max(abs(gradient[active] - lagrange)) < 1e-3
        assert not (~active).any() or min(gradient[~active] - lagrange) > -1e-3
        assert result.unscaled_fun < sample["legacy"]["variance"] - 1e-12
    print("PASS numerical optimizer: analytical 10/90 solution, scale invariance, zero covariance, and past-data KKT checks on all three rebalances")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        calls = []
        def once(method, url, headers, body):
            calls.append(1)
            if len(calls) == 1:
                raise ConnectionResetError(10054, "explicit test reset")
            return c.radar.fake_gemini(method, url, headers, body)
        budget = Budget(root / "retry/budget.sqlite")
        result = c.committee(root / "retry", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=once)
        assert result["status"] == "COMPLETED" and len(calls) == 7
        assert budget.summary()["unknown_attempts"] == 1
        assert budget.summary()["uncertain_and_inflight_reserved_usd"] == "0.110592"
        c.committee(root / "retry", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=once)
        assert len(calls) == 7

        calls.clear()
        def fake(*args):
            calls.append(1)
            return c.radar.fake_gemini(*args)
        budget = Budget(root / "crash/budget.sqlite")
        try:
            c.committee(root / "crash", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=fake, crash=True)
        except TestCrash:
            pass
        else:
            assert False, "crash must happen after durable raw response"
        assert len(calls) == 1
        result = c.committee(root / "crash", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=fake)
        assert result["status"] == "COMPLETED" and len(calls) == 6
        assert budget.summary()["physical_attempts"] == 6

        budget = Budget(root / "cap/budget.sqlite")
        budget.reserve("prior", Decimal("34.70"), {})
        try:
            budget.reserve("next", Decimal("0.110592"), {})
        except BudgetStop:
            pass
        else:
            assert False, "cap must include unknown/in-flight and survive reopening"
        assert Budget(budget.path).summary()["exposure_usd"] == "34.70"
        assert Budget(budget.path).summary()["physical_attempts"] == 1
        try:
            c.committee(root / "cap", "2026-04-06", "2026-04-02", "PETR4", budget, True)
        except BudgetStop:
            pass
        else:
            assert False, "ensemble must not swallow an aggregate budget stop"
        assert budget.summary()["physical_attempts"] == 1

        budget = Budget(root / "exhausted/budget.sqlite")
        calls.clear()
        def fails(*args):
            calls.append(1)
            raise ConnectionResetError(10054, "explicit test reset")
        result = c.committee(root / "exhausted", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=fails)
        assert result["status"] == "NO_ANALYSIS" and len(calls) == 10  # five distinct votes, two attempts each
        c.committee(root / "exhausted", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=fails)
        assert len(calls) == 10 and budget.summary()["unknown_attempts"] == 10

        budget = Budget(root / "invalid/budget.sqlite")
        calls.clear()
        def invalid(*args):
            calls.append(1)
            return b'{"candidates":[]}'
        assert c.committee(root / "invalid", "2026-04-06", "2026-04-02", "PETR4", budget, True, transport=invalid)["status"] == "NO_ANALYSIS"
        assert len(calls) == 5, "five distinct votes; schema-invalid response never gets a replacement"
    print("PASS runtime: one bounded retry, unknown reservation, crash envelope recovery, aggregate cap, exhausted and invalid responses")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        m, assets, _ = c.prepare(root, offline=True, count=20)
        c.initialize(root, m, assets)
        wallet = c.r.wallets()["BUY_HOLD"]
        components = [e for e in c.dividends.entitlements(wallet, "2026-06-11") if e["ticker"] == "BBAS3" and e["payment_date"] == "2026-06-11"]
        assert len(components) == 2
        fields = ("ticker", "kind", "data_com", "payment_date", "quantity", "gross", "net")
        req = c.manual.request({"kind": "DIVIDEND", "wallet": wallet["id"], "dividend": {k: components[0][k] for k in fields}})
        assert c.manual.book_dividends([(req, {"legacy_test": True})])["booked"] == 1
        c.dividends.book_received("2026-06-11", wallets=[wallet])
        wallet = c.r.wallets()["BUY_HOLD"]
        paid = [e for e in wallet["dividends"] if e["ticker"] == "BBAS3" and e["payment_date"] == "2026-06-11"]
        assert len(paid) == 2 and sum((c.b.dec(e["net"]) for e in paid), c.b.ZERO) == Decimal("102.67")
        before = c.b.sha_file(c.manual.path())
        assert c.dividends.book_received("2026-06-11", wallets=[wallet])["booked"] == 0
        assert c.b.sha_file(c.manual.path()) == before
        expected, _ = c.dividends.on(c.dividends.entitlements(wallet, "2026-06-11"), "2026-06-11")
        assert c.b.dec(wallet["dividends_received"]) == expected
    print("PASS same-date B3 components: both JCP parcels, legacy partial receipt preserved, per-component rounding, idempotent cash")


def historical(root):
    m, assets, days = c.prepare(root, offline=c.r.checked(c.campaign_path(root))["mode"] == "OFFLINE_TEST_ONLY", count=len(c.r.checked(c.campaign_path(root))["sessions"]))
    initial = c.r.checked(root / "initialization.json")["wallets"]
    assert set(initial) == set(c.STRATEGIES)
    seed = initial["BUY_HOLD"]
    assert all(w["positions"] == seed["positions"] and w["cash"] == seed["cash"] and w["costs"] == "0.00" for w in initial.values())
    with c.closing(c.manual.connect()) as conn:
        histories = {w["strategy"]: c.manual.events(conn, w["id"]) for w in c.manual.catalog(conn)}
    for strategy, history in histories.items():
        wallet = c.manual.replay(history)
        assert c.b.dec(wallet["cash"]) >= 0
        for trade in wallet["trades"][5:]:
            raw = next(x for x in assets[trade["ticker"]]["rows"] if x["date"] == trade["economic_date"])
            assert c.b.dec(trade["price"]) == c.b.dec(str(raw["open"]))
            assert c.b.dec(trade["costs"]) == c.b.money(c.b.money(c.b.dec(trade["quantity"]) * c.b.dec(trade["price"])) * c.b.dec(c.r.RATE) / 100)
        for event in history:
            source = event.get("source") or {}
            if event["request"]["kind"] in ("RULE_DECISION", "RULE_EXECUTION"):
                assert source["decision_session"] < source["execution_session"]
                if source.get("inputs"):
                    assert all(max(d for d, _ in v) <= source["decision_session"] for v in source["inputs"].values())
                    if strategy.startswith("MIN_"):
                        assert all(len(v) == 253 for v in source["inputs"].values())
                        assert source["optimizer"], "252 past returns available; preserve actual optimizer result"
                        symbols = sorted(source["inputs"])
                        cov = pd.DataFrame({t: [v for _, v in source["inputs"][t]] for t in symbols}).pct_change().dropna().cov().values
                        weights = np.array([source["weights"][t] for t in symbols])
                        result = source["optimizer"][0]
                        assert result["success"] and min(weights) >= -1e-12 and abs(sum(weights) - 1) < 1e-8
                        assert abs(float(weights @ cov @ weights) - result["unscaled_variance"]) < 1e-12
                        gradient = 2 * cov @ weights / result["objective_scale"]
                        active = weights > 1e-6
                        lagrange = np.mean(gradient[active])
                        assert max(abs(gradient[active] - lagrange)) < 1e-3
                        assert not (~active).any() or min(gradient[~active] - lagrange) > -1e-3
    checked = 0
    for day in days:
        reference = c.r.checked(root / "references" / (day + ".json"))
        marker = root / "sessions" / day / "day.json"
        states = c.r.checked(marker)["valuation"] if marker.exists() else reference["valuation"]
        for strategy, valuation in states.items():
            prefix = []
            for event in histories[strategy]:
                req = event["request"]
                economic = (req.get("trade") or {}).get("economic_date") or (req.get("dividend") or {}).get("payment_date") or (event.get("source") or {}).get("execution_session") or req.get("start_date")
                if economic and economic > day:
                    break
                prefix.append(event)
            wallet = c.manual.replay(prefix)
            actual = c.r.valuation(wallet, c.orders.session_rows(day), day)
            assert actual == valuation, (day, strategy, actual, valuation)
            assert c.b.dec(wallet["dividends_received"]) == sum((c.b.dec(d["net"]) for d in wallet["dividends"]), c.b.ZERO)
            assert all(d["payment_date"] <= day for d in wallet["dividends"])
            expected_paid, _ = c.dividends.on(c.dividends.entitlements(wallet, day), day)
            assert c.b.dec(wallet["dividends_received"]) == expected_paid, (day, strategy, "all B3 components must be credited separately")
            checked += 1
    budget = Budget(c.budget_path(root))
    assert Decimal(budget.summary()["exposure_usd"]) <= Decimal("34.78")
    if (root / "references_complete.json").exists():
        assert len(list((root / "references").glob("*.json"))) == len(days)
    result = {"status": "PASS", "daily_wallet_states_reconstructed": checked, "sessions": len(days), "strategies": list(c.STRATEGIES), "checks": ["equal initial book", "causal inputs", "252 past returns", "raw next-open fills", "0.03% fees", "no early dividend cash", "daily cash/positions/receivables/equity", "aggregate budget"]}
    c.r.radar.write(root / "checks.json", c.b.sealed(result))
    print(json.dumps(result))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        runtime()
    else:
        historical(Path(sys.argv[1]))
