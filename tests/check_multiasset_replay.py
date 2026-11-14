"""Runnable assertions over an isolated completed offline replay; no network/LLM.

python tests/check_multiasset_replay.py --id april-2026-flash-offline-v2
"""

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import replay_multiasset as r


def check(name):
    from report_multiasset_replay import usage_of

    assert usage_of({}) is None
    assert (
        usage_of(
            {
                "token_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "total_tokens": 12,
                }
            }
        )["thoughts_tokens"]
        == 0
    )
    assert (
        usage_of(
            {
                "token_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "total_tokens": 15,
                }
            }
        )
        is None
    )
    assert (
        usage_of(
            {
                "token_usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 2,
                    "thoughts_tokens": 3,
                    "total_tokens": 15,
                }
            }
        )["thoughts_tokens"]
        == 3
    )
    root = r.root_of(name)
    m, assets = r.load(root)
    report = r.checked(root / "report.json")
    assert report["classification"] == "OFFLINE_TEST_NOT_INVESTMENT_RESULT"
    assert report["completed_sessions"] == 10
    assert r.checked(root / "execution_mode.json")["mode"] == "OFFLINE_TEST_ONLY"
    assert report["estimated_cost_usd_not_invoice"] == 0
    assert report["calls_recorded"] <= 310
    assert not r.preflight(root)["ready"]  # No implicit use of the DP-34 budget.
    assert not r.preflight(root, "1")["ready"]
    assert "offline_root_cannot_run_live" in r.preflight(root, "34.78")["errors"]
    try:
        r.root_of("../../platform/manual-v1")
        raise AssertionError("unsafe path accepted")
    except ValueError:
        pass

    initial = r.checked(root / "initialization.json")["wallets"]
    assert initial["MULTIAGENT"]["cash"] == initial["BUY_HOLD"]["cash"]
    assert initial["MULTIAGENT"]["positions"] == initial["BUY_HOLD"]["positions"]
    previous = None
    operation_count = 0
    for d in report["days"]:
        assert d["reference"] == r.previous(d["day"]) < d["day"]
        context = r.checked(root / "sessions" / d["day"] / "manager/context.json")
        assert context["wallet"]["cash"] == d["before"]["MULTIAGENT"]["cash"]
        assert context["wallet"]["positions"] == d["before"]["MULTIAGENT"]["positions"]
        before = {
            p["ticker"]: r.b.dec(p["quantity"]) for p in context["wallet"]["positions"]
        }
        cash = r.b.dec(context["wallet"]["cash"])
        if previous:
            assert cash == r.b.dec(previous["cash"])
            assert before == {t: r.b.dec(q) for t, q in previous["positions"].items()}
        for op in d["operations"]:
            t = op["trade"]
            assert t["economic_date"] == d["day"]
            market = next(x for x in assets[t["ticker"]]["rows"] if x["date"] == d["day"])
            assert r.b.dec(t["price"]) == r.b.dec(str(market["open"]))
            quantity, price, fees = map(r.b.dec, (t["quantity"], t["price"], t["costs"]))
            assert fees == r.b.money(
                r.b.money(quantity * price) * r.b.dec(m["cost_rate_pct"]) / 100
            )
            before[t["ticker"]] += quantity if t["side"] == "BUY" else -quantity
            cash += (
                -(quantity * price + fees)
                if t["side"] == "BUY"
                else quantity * price - fees
            )
            operation_count += 1
        v = d["valuation"]["MULTIAGENT"]
        assert {t: str(q) for t, q in before.items() if q} == v["positions"]
        assert cash == r.b.dec(v["cash"]) >= 0
        assert d["valuation"]["BUY_HOLD"]["positions"] == {
            p["ticker"]: p["quantity"] for p in initial["BUY_HOLD"]["positions"]
        }
        previous = v
    assert operation_count > 0, "test must exercise state changes"

    # Poison every future target bar. Features and request data must stay identical.
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        day, ticker = m["sessions"][0], m["universe"][0]
        poisoned = copy.deepcopy(assets)
        for row in poisoned[ticker]["rows"]:
            if row["date"] >= day:
                for key in r.market.FIELDS:
                    row[key] = 1000000000
        r.freeze_input(temp, m, poisoned, ticker, day)
        original = (
            root / "sessions" / day / "radar/analyses" / ticker / m["references"][day]
        )
        rebuilt = (
            temp / "sessions" / day / "radar/analyses" / ticker / m["references"][day]
        )
        assert (rebuilt / "input.json").read_bytes() == (
            original / "input.json"
        ).read_bytes()
        assert (rebuilt / "bars.csv").read_bytes() == (original / "bars.csv").read_bytes()

    # Resuming completed sessions changes neither accounting nor paid-call banks.
    banks = [root / "book/manual.sqlite3", *root.glob("sessions/**/calls.sqlite")]
    hashes = {p: r.b.sha_file(p) for p in banks}
    os.environ["GEMINI_API_KEY"] = "OFFLINE_TEST_NO_SECRET"
    with r.no_network():
        r.execute(root, m, assets, offline=True)
    assert hashes == {p: r.b.sha_file(p) for p in banks}
    try:
        r.execute(root, m, assets, offline=False, max_usd="34.78")
        raise AssertionError("mixed offline/live accepted")
    except ValueError:
        pass
    print(
        json.dumps(
            {
                "status": "PASS",
                "sessions": 10,
                "operations_checked": operation_count,
                "checks": [
                    "isolated paths and SQLite",
                    "equal initial positions/cash",
                    "prior-session inputs",
                    "poisoned future has no effect",
                    "official open and fees",
                    "daily positions/cash propagation",
                    "buy_hold unchanged",
                    "no implicit budget",
                    "idempotent resume with sockets blocked",
                    "offline/live separation",
                ],
            }
        )
    )


def check_real(name):
    import sqlite3

    import portfolio_history_api as hist
    from report_multiasset_replay import report

    root = r.root_of(name)
    with r.no_network():
        m, assets = r.load(root)
        assert r.checked(root / "execution_mode.json")["mode"] == "REAL_INFERENCE"
        value = report(root)
        assert [d["day"] for d in value["days"]] == m["sessions"]
        assert value["http_attempts"] <= 310
        assert r.b.dec(
            value["estimated_cost_upper_bound_including_unknown_usd"]
        ) <= r.b.dec(r.checked(root / "authorization.json")["max_aggregate_usd"])
        r.manual.ROOT, r.market.ROOT = root / "book", root / "market"
        assert r.manual.path().resolve().is_relative_to(root.resolve())
        books = r.wallets()
        initial = r.checked(root / "initialization.json")["wallets"]
        assert initial["MULTIAGENT"]["cash"] == initial["BUY_HOLD"]["cash"]
        assert initial["MULTIAGENT"]["positions"] == initial["BUY_HOLD"]["positions"]
        operations = 0
        for d in value["days"]:
            folder = root / "sessions" / d["day"]
            assert d["reference"] == r.previous(d["day"]) < d["day"]
            expected_before = (
                initial["MULTIAGENT"]
                if d["day"] == m["sessions"][0]
                else hist.historical_wallet(books["MULTIAGENT"], d["reference"])
            )
            assert d["before"]["MULTIAGENT"]["cash"] == expected_before["cash"]
            assert d["before"]["MULTIAGENT"]["positions"] == expected_before["positions"]
            for strategy, book in books.items():
                historical = hist.historical_wallet(book, d["day"])
                prices = {
                    t: next(x for x in assets[t]["rows"] if x["date"] == d["day"])
                    for t in m["universe"]
                }
                assert (
                    r.valuation(historical, prices, d["day"]) == d["valuation"][strategy]
                )
            if d.get("status") == "NO_ANALYSIS":
                assert not d["operations"] and not (folder / "manager").exists()
                assert r.checked(folder / "review.json")["replacement_inference"] is False
            else:
                c = r.checked(folder / "manager/context.json")
                assert c["wallet"]["cash"] == d["before"]["MULTIAGENT"]["cash"]
                assert c["wallet"]["positions"] == d["before"]["MULTIAGENT"]["positions"]
                compiled = r.checked(folder / "proposal.json")
                assert r.wm.compile_proposal(c, compiled["response"]) == {
                    k: v for k, v in compiled.items() if k != "sha256"
                }
                for t in m["universe"]:
                    assert (
                        r.radar.detail(t, d["reference"], folder / "radar")["status"]
                        == "COMPLETED"
                    )
            for t in m["universe"]:
                data = r.radar.checked_input(folder / "radar", t, d["reference"])
                assert data["session"] < d["day"]
            for op in d["operations"]:
                t = op["trade"]
                market = next(
                    x for x in assets[t["ticker"]]["rows"] if x["date"] == d["day"]
                )
                assert r.b.dec(t["price"]) == r.b.dec(str(market["open"]))
                assert t["economic_date"] == d["day"]
                assert r.b.dec(t["costs"]) == r.b.money(
                    r.b.money(r.b.dec(t["quantity"]) * r.b.dec(t["price"]))
                    * r.b.dec(m["cost_rate_pct"])
                    / 100
                )
                operations += 1
        for bank in root.glob("sessions/**/calls.sqlite"):
            with sqlite3.connect(bank.resolve().as_uri() + "?mode=ro", uri=True) as conn:
                assert (
                    conn.execute("SELECT MAX(attempt) FROM attempts").fetchone()[0] <= 1
                )
    result = {
        "status": "PASS",
        "classification": "REAL_REPLAY_VERIFIED_WITH_MISSING_ANALYSES",
        "sessions_valued": len(value["days"]),
        "complete_analyses": value["sessions_with_complete_analysis"],
        "missing_analyses": value["sessions_without_analysis"],
        "operations_checked": operations,
        "http_attempts": value["http_attempts"],
        "checks": [
            "isolated economic book",
            "all daily valuations reconstructed from ledger",
            "same initial portfolio",
            "prior-session inputs",
            "complete quorum and proposal validation",
            "no invented decision on failed days",
            "official open and declared fees",
            "no replacement HTTP attempt",
            "authorized aggregate ceiling",
        ],
    }
    r.radar.write(root / "checks.json", r.b.sealed(result))
    print(json.dumps(result))


def check_receivables(name):
    """Independent per-event money/cash check for the chosen stress window."""
    import portfolio_history_api as hist

    root = r.root_of(name)
    m, _ = r.load(root)
    assert m.get("window") == {"start": "2026-04-20", "end": "2026-05-05"}
    r.manual.ROOT, r.market.ROOT = root / "book", root / "market"
    count = 0
    with r.no_network():
        books = r.wallets()
        assert all(not book["dividends"] for book in books.values())
        for path in sorted(root.glob("sessions/*/day.json")):
            day = r.checked(path)
            for strategy, book in books.items():
                receivable = r.b.ZERO
                for ticker in m["universe"]:
                    for event in r.dividends.events(ticker):
                        if not m["sessions"][0] <= event["data_com"] <= day["day"]:
                            continue
                        assert event["payment_date"] > day["day"]
                        entitled = hist.historical_wallet(book, event["data_com"])
                        quantity = sum(
                            (
                                r.b.dec(p["quantity"])
                                for p in entitled["positions"]
                                if p["ticker"] == ticker
                            ),
                            r.b.ZERO,
                        )
                        receivable += r.b.money(
                            quantity
                            * r.b.dec(event["value_per_share"])
                            * (r.b.dec("0.85") if event["kind"] == "JCP" else 1)
                        )
                historical = hist.historical_wallet(book, day["day"])
                expected_cash = r.b.dec(m["capital"])
                for trade in historical["trades"]:
                    gross = r.b.money(
                        r.b.dec(trade["quantity"]) * r.b.dec(trade["price"])
                    )
                    expected_cash += (
                        gross if trade["side"] == "SELL" else -gross
                    ) - r.b.dec(trade["costs"])
                value = day["valuation"][strategy]
                assert expected_cash == r.b.dec(value["cash"])
                assert receivable == r.b.dec(value["receivable"])
                count += 1
        last = r.checked(sorted(root.glob("sessions/*/day.json"))[-1])
        assert last["day"] == m["sessions"][-1]
        assert last["valuation"]["BUY_HOLD"]["cash"] == "146.11"
        assert last["valuation"]["BUY_HOLD"]["receivable"] == "252.49"
    result = {
        "status": "PASS",
        "daily_wallet_checks": count,
        "checks": [
            "end-of-data-com quantity",
            "JCP net 15 percent",
            "round each entitlement to cents",
            "receivable outside available cash",
            "no payment booked before payment date",
        ],
        "buy_hold_final_receivable": "252.49",
        "buy_hold_cash": "146.11",
    }
    r.radar.write(root / "dividend_checks.json", r.b.sealed(result))
    print(json.dumps(result))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True)
    p.add_argument("--real", action="store_true")
    p.add_argument("--receivables", action="store_true")
    args = p.parse_args()
    (check_real if args.real else check)(args.id)
    if args.receivables:
        check_receivables(args.id)
