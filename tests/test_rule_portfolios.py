"""Same initial basket -> causal signals -> frozen pending order -> atomic B3 fill."""

import copy
import sys
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dashboard"), str(ROOT / "scripts"), str(ROOT)]
import daily_cycle as cycle  # noqa: E402
import rule_portfolios as r  # noqa: E402


@pytest.fixture
def lab(tmp_path, monkeypatch):
    m = r.manual
    monkeypatch.setattr(m, "ROOT", tmp_path / "book")
    monkeypatch.setattr(r.radar, "now", lambda: pd.Timestamp("2026-10-15T09:00:00-03:00"))
    monkeypatch.setattr(r.radar, "last_closed", lambda now: "2026-10-14")
    monkeypatch.setattr(r.dividends, "events", lambda ticker: [])
    baseline = m.post(
        "confirm",
        {
            "request": {
                "kind": "CREATE",
                "name": "Buy & Hold",
                "nature": "SIMULATION",
                "capital": "100000.00",
                "start_date": r.START,
                "strategy": "BUY_HOLD",
                "comparison_group": "same-group",
                "initialization_note": "Test initial basket",
            },
            "command_id": "baseline",
            "confirm": True,
            "preview_token": None,
        },
    )["wallet"]
    for ticker in r.base.TICKERS:
        req = {
            "kind": "TRADE",
            "wallet": baseline["id"],
            "trade": {
                "ticker": ticker,
                "side": "BUY",
                "quantity": "199",
                "price": "100.00",
                "costs": "0.00",
                "economic_date": r.START,
            },
        }
        preview = m.post("preview", {"request": req})
        baseline = m.post(
            "confirm",
            {
                "request": req,
                "command_id": ticker,
                "confirm": True,
                "preview_token": preview["preview_token"],
            },
        )["wallet"]
    ids = r.initialize(baseline["id"], "0.03")
    days = [
        d.isoformat()
        for d in r.B3Calendar().sessions_between(
            date.fromisoformat(r.START) - timedelta(days=450), date.fromisoformat(r.START)
        )
    ][-201:]
    # Last close makes a death cross; Bollinger says BUY while already holding.
    values = [100.0] * 151 + [102.0] * 49 + [1.0]
    rows = [
        {
            "date": d,
            "adjusted_close": v,
            "close": v,
            "open": v,
            "conflict": False,
            "volume": 1000,
        }
        for d, v in zip(days, values, strict=True)
    ]
    datasets = {
        t: {
            "rows": copy.deepcopy(rows),
            "factor_source": {"sha256": "snapshot", "fetched_at": "now"},
        }
        for t in r.base.TICKERS
    }
    monkeypatch.setattr(r.base, "series", lambda ticker: datasets[ticker])
    monkeypatch.setattr(r.orders, "session_rows", lambda day: {})
    return baseline, ids, datasets


def wallet(wid):
    return r.manual.get({"wallet": wid})["selected"]


def opening():
    return {
        t: {"date": "2026-10-15", "open": 110.0, "conflict": False}
        for t in r.base.TICKERS
    }


def test_common_basket_causal_freeze_pending_retry_and_holds(lab, monkeypatch):
    baseline, ids, datasets = lab
    assert r.initialize(baseline["id"], "0.03") == ids
    with pytest.raises(r.manual.Invalid, match="outra política"):
        r.initialize(baseline["id"], "0.10")
    for wid in ids:
        assert wallet(wid)["positions"] == baseline["positions"]
        assert wallet(wid)["cash"] == baseline["cash"]
        assert not r.orders.appliable({"wallet": wallet(wid)})
    # Future prices cannot affect a past signal.
    expected = r.signal_data("SMA_50_200", r.START, datasets)
    for data in datasets.values():
        data["rows"].append(
            {**data["rows"][-1], "date": "2026-10-15", "adjusted_close": 1e9}
        )
    assert r.signal_data("SMA_50_200", r.START, datasets) == expected
    assert all(s["signal"] == -1 for s in expected.values())
    out = r.advance()
    assert "rule_open_missing" in out[ids[0]]["blocked"]
    assert len(wallet(ids[0])["trades"]) == 5
    assert [a["kind"] for a in wallet(ids[1])["audit"]][-2:] == [
        "RULE_DECISION",
        "RULE_EXECUTION",
    ]
    with closing(r.manual.connect()) as conn:
        frozen = r.manual.events(conn, ids[0])[-1]
    assert frozen["source"]["classification"] == "PROSPECTIVE_SIMULATION"
    for data in datasets.values():
        data["rows"] = []  # retry must use the sealed decision, not today's new snapshot
    monkeypatch.setattr(r.orders, "session_rows", lambda day: opening())
    r.advance()
    sold = wallet(ids[0])
    assert sold["positions"] == [] and len(sold["trades"]) == 10
    assert sold["costs"] == "32.85"  # 5 x round(199 x 110 x 0.03%)
    assert wallet(baseline["id"])["revision"] == baseline["revision"]
    before = {wid: wallet(wid)["revision"] for wid in ids}
    assert all(v["completed"] == 0 for v in r.advance().values())
    assert before == {wid: wallet(wid)["revision"] for wid in ids}
    # Management boundaries: neither UI edits nor the agent's batch may move rules.
    with pytest.raises(r.manual.Invalid, match="regra automática"):
        r.manual.post(
            "preview",
            {
                "request": {
                    "kind": "TRADE",
                    "wallet": ids[0],
                    "trade": {
                        "ticker": "PETR4",
                        "side": "BUY",
                        "quantity": "1",
                        "price": "1.00",
                        "costs": "0.00",
                        "economic_date": r.START,
                    },
                }
            },
        )
    with pytest.raises(cycle.Stop, match="ausente"):
        cycle.multiagent_wallet()  # the two rule books do not become agent candidates


def test_atomic_execution_rolls_back_and_can_resume(lab, monkeypatch):
    _, ids, datasets = lab
    monkeypatch.setattr(r.orders, "session_rows", lambda day: opening())
    append = r.manual.append

    def fail(conn, req, *args, **kwargs):
        if (
            req["kind"] == "TRADE"
            and req["trade"]["side"] == "SELL"
            and req["trade"]["ticker"] == "VALE3"
        ):
            raise RuntimeError("interrupted")
        return append(conn, req, *args, **kwargs)

    monkeypatch.setattr(r.manual, "append", fail)
    with pytest.raises(RuntimeError, match="interrupted"):
        r.advance_wallet(ids[0], [r.START], datasets, "2026-10-15")
    assert len(wallet(ids[0])["trades"]) == 5
    assert not any(e["kind"] == "RULE_EXECUTION" for e in wallet(ids[0])["audit"])
    monkeypatch.setattr(r.manual, "append", append)
    assert r.advance_wallet(ids[0], [r.START], datasets, "2026-10-15")["completed"] == 1
    assert wallet(ids[0])["positions"] == []


def test_missing_history_blocks_and_sleeve_cash_never_reinvests_dividends(
    lab, monkeypatch
):
    _, ids, datasets = lab
    datasets["PETR4"]["rows"][-1]["conflict"] = True
    assert all(
        "rule_signal_history_missing" in v["blocked"] for v in r.advance().values()
    )
    assert all(len(wallet(wid)["audit"]) == 5 for wid in ids)
    datasets["PETR4"]["rows"][-1]["conflict"] = False
    monkeypatch.setattr(r.orders, "session_rows", lambda day: opening())
    r.advance()
    sold = wallet(ids[0])
    # A hypothetical extra dividend remains cash, not extra buying power per sleeve.
    sold["cash"] = str(r.b.dec(sold["cash"]) + 10000)
    decision = {
        "signals": {t: {"signal": 1} for t in r.base.TICKERS},
        "execution_session": "2026-10-16",
    }
    reqs = r.trades_for(sold, decision, opening(), r.b.dec("0.03"))
    assert all(x["trade"]["quantity"] == "199" for x in reqs)
    assert all(x["trade"]["economic_date"] > r.START for x in reqs)


def test_dividend_right_survives_sale_and_is_booked_once_after_catchup(lab, monkeypatch):
    _, ids, _ = lab
    monkeypatch.setattr(r.orders, "session_rows", lambda day: opening())
    r.advance()  # SMA sells on 15/10, after the data-com of 14/10.
    event = {
        "ticker": "PETR4",
        "kind": "DIVIDENDO",
        "label": "Dividendo",
        "data_com": r.START,
        "payment_date": "2026-10-16",
        "value_per_share": "1.00",
    }
    monkeypatch.setattr(r.dividends, "events", lambda t: [event] if t == "PETR4" else [])
    monkeypatch.setattr(r.dividends, "snapshot", lambda t: {"sha256": "div", "url": "B3"})
    monkeypatch.setattr(r.radar, "now", lambda: pd.Timestamp("2026-10-16T09:00:00-03:00"))
    before = wallet(ids[0])["cash"]
    assert r.advance()[ids[0]]["dividends"]["booked"] == 1
    assert r.b.dec(wallet(ids[0])["cash"]) == r.b.dec(before) + 199
    assert r.advance()[ids[0]]["dividends"]["booked"] == 0
    assert wallet(ids[0])["dividends"][0]["quantity"] == "199"
