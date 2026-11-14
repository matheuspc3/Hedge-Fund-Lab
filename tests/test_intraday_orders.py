"""DP-35: post-approval prices, atomic execution and recovery; no network/provider calls."""

import pytest
from test_wallet_manager import approve, at, lab, m, result, seed  # noqa: F401


@pytest.fixture
def pending(lab, monkeypatch):  # noqa: F811
    old, raw = lab
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-22T10:35:22"))
    run = m.analysis.create(
        {
            "command_id": "e" * 32,
            "wallet": old["wallet"]["id"],
            "wallet_revision": old["wallet"]["revision"],
            "target_date": "2026-10-22",
            "reference_session": "2026-10-21",
            "tickers": ["PETR4", "VALE3"],
            "confirm": True,
        }
    )["run"]
    c = m.prepare({"run": run, "proposal": "f" * 32, "cost_rate_pct": "0.10"})["context"]
    result(c, raw)
    order = approve(c, "2026-10-22")["order"]
    assert order["leg"] == "INTRADAY"
    assert m.status(run, c["proposal"])["status"] == "PENDING_INTRADAY"
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-22T11:00:00"))
    return c, order


def records():
    return {
        t: {
            "day": "2026-10-22",
            "interval": "1m",
            "fetched_at": "2026-10-22T10:55:00-03:00",
            "bars": [
                ["10:35", 1, 2, 1, 1, 100],
                ["10:36", price, price + 1, price - 1, price, 100],
                ["10:37", 99, 100, 98, 99, 100],
            ],
        }
        for t, price in [("PETR4", 41.0), ("VALE3", 62.5)]
    }


def test_first_complete_bar_after_approval_books_once_with_frozen_source(
    pending, monkeypatch
):
    c, order = pending
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *args: records())
    assert m.orders.settle_pending(intraday_only=True)["settled"] == [c["proposal"]]
    assert m.orders.settle_pending(intraday_only=True)["settled"] == []
    wallet = m.manual.get({"wallet": c["wallet"]["id"]})["selected"]
    trades = wallet["trades"][1:]
    assert [(t["ticker"], t["price"]) for t in trades] == [
        ("VALE3", "62.50"),
        ("PETR4", "41.00"),
    ]
    assert wallet["cash"] == "239.34"
    src = trades[0]["source"]
    assert src["kind"] == "WALLET_MANAGER_INTRADAY_EXECUTION"
    assert src["price_basis"] == "YAHOO_1M_OPEN_AFTER_APPROVAL"
    quote = src["prices"]["VALE3"]
    assert quote["price_time"] == "2026-10-22T10:36:00-03:00"
    assert at("2026-10-22T10:36:00") > at("2026-10-22T10:35:22")
    assert "auction" not in quote
    snap = m.orders.read(m.folder(c["run"], c["proposal"]) / "execution-prices.json")
    assert snap["order_sha256"] == order["sha256"]
    assert snap["sha256"] == src["execution_snapshot_sha256"]
    assert snap["payloads"] == records()


@pytest.mark.parametrize(
    "invalid", ["old_bar", "wrong_day", "wrong_interval", "incomplete_bar", "no_volume"]
)
def test_old_or_invalid_price_never_executes_even_if_fetched_after_approval(
    pending, monkeypatch, invalid
):
    c, _ = pending
    rows = records()
    for rec in rows.values():
        if invalid == "old_bar":
            rec["bars"] = rec["bars"][:1]
        if invalid == "wrong_day":
            rec["day"] = "2026-10-21"
        if invalid == "wrong_interval":
            rec["interval"] = "5m"
        if invalid == "incomplete_bar":
            rec["fetched_at"] = "2026-10-22T10:36:30-03:00"
        if invalid == "no_volume":
            for row in rec["bars"]:
                row[5] = 0
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *args: rows)
    out = m.orders.settle_pending()
    assert out["waiting"] == [c["proposal"]] and not out["errors"]
    assert (
        m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["revision"]
        == c["wallet"]["revision"]
    )
    assert not (m.folder(c["run"], c["proposal"]) / "execution-prices.json").exists()


def test_missing_asset_waits_for_whole_basket_and_deadline_never_falls_back_to_close(
    pending, monkeypatch
):
    c, _ = pending
    monkeypatch.setattr(
        m.orders, "delayed_bars", lambda *args: {"VALE3": records()["VALE3"]}
    )
    assert m.orders.settle_pending()["waiting"] == [c["proposal"]]
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-22T17:26:00"))
    seed(
        monkeypatch, {("VALE3", "2026-10-22"): (1, 99), ("PETR4", "2026-10-22"): (1, 99)}
    )
    out = m.orders.settle_pending()
    assert out["settled"] == [c["proposal"]], out
    s = m.status(c["run"], c["proposal"])
    assert s["status"] == "NOT_EXECUTED"
    assert s["execution"]["reason"] == "NO_POST_APPROVAL_INTRADAY_PRICE"
    assert (
        m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["revision"]
        == c["wallet"]["revision"]
    )


def test_ledger_failure_reuses_exact_frozen_prices_after_restart(pending, monkeypatch):
    c, _ = pending
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *args: records())
    append = m.manual.append

    def fail(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(m.manual, "append", fail)
    assert m.orders.settle_pending()["errors"]
    path = m.folder(c["run"], c["proposal"]) / "execution-prices.json"
    frozen = path.read_bytes()
    monkeypatch.setattr(m.manual, "append", append)
    monkeypatch.setattr(
        m.orders,
        "delayed_bars",
        lambda *args: pytest.fail("download repeated after freeze"),
    )
    # Recovery after the deadline still uses the prices already captured on time.
    monkeypatch.setattr(m.radar, "now", lambda: at("2026-10-23T09:00:00"))
    assert m.orders.settle_pending()["settled"] == [c["proposal"]]
    assert path.read_bytes() == frozen


def test_previously_recorded_close_order_keeps_original_policy(pending, monkeypatch):
    c, order = pending
    # Historical on-disk fixture, not a migration of a live order.
    legacy = m.b.sealed(
        {
            **{k: v for k, v in order.items() if k not in ("sha256", "execution_policy")},
            "leg": "CLOSE",
            "status": "PENDING_AUCTION",
        }
    )
    m.radar.write(m.folder(c["run"], c["proposal"]) / "order.json", legacy)
    monkeypatch.setattr(
        m.orders,
        "delayed_bars",
        lambda *args: pytest.fail("legacy order queried intraday"),
    )
    seed(
        monkeypatch, {("VALE3", "2026-10-22"): (1, 60), ("PETR4", "2026-10-22"): (1, 40)}
    )
    assert m.orders.settle_pending(intraday_only=True)["settled"] == []
    out = m.orders.settle_pending()
    assert not out["errors"], out["errors"]
    assert out["settled"] == [c["proposal"]], out
    s = m.status(c["run"], c["proposal"])
    assert s["execution"]["leg"] == "CLOSE"
    assert s["execution"]["prices"]["PETR4"]["auction"] == "40.00"


@pytest.mark.parametrize(
    "invalid", ["future_fetch", "no_timezone", "nan_price", "bad_ohlc"]
)
def test_untrustworthy_source_cannot_change_the_ledger(pending, monkeypatch, invalid):
    c, _ = pending
    rows = records()
    for rec in rows.values():
        if invalid == "future_fetch":
            rec["fetched_at"] = "2026-10-22T11:01:00-03:00"
        if invalid == "no_timezone":
            rec["fetched_at"] = "2026-10-22T10:55:00"
        if invalid in ("nan_price", "bad_ohlc"):
            for bar in rec["bars"]:
                bar[1] = float("nan") if invalid == "nan_price" else 1000
    monkeypatch.setattr(m.orders, "delayed_bars", lambda *args: rows)
    out = m.orders.settle_pending()
    assert not out["settled"] and (out["errors"] or out["waiting"])
    assert (
        m.manual.get({"wallet": c["wallet"]["id"]})["selected"]["revision"]
        == c["wallet"]["revision"]
    )


def test_approval_requires_new_preview_if_execution_modality_changes(
    pending, monkeypatch
):
    c, _ = pending
    # Remove only this temporary fixture's approval, to exercise the approval boundary.
    (m.folder(c["run"], c["proposal"]) / "order.json").unlink()
    payload = {"run": c["run"], "proposal": c["proposal"], "economic_date": "2026-10-22"}
    preview = m.post("preview", payload)
    schedule = m.orders.schedule
    monkeypatch.setattr(
        m.orders, "schedule", lambda *args: {**schedule(*args), "leg": "CLOSE"}
    )
    with pytest.raises(m.manual.Invalid, match="prévia mudou"):
        m.post(
            "apply",
            {**payload, "preview_token": preview["preview_token"], "confirm": True},
        )
    assert not (m.folder(c["run"], c["proposal"]) / "order.json").exists()


def test_execution_slot_retains_opening_and_changes_only_new_intraday_approvals():
    assert m.orders.execution_slot(at("2026-10-21T10:35:22")) == ("2026-10-21", "CLOSE")
    assert m.orders.execution_slot(at("2026-10-22T09:44:59")) == ("2026-10-22", "OPEN")
    assert m.orders.execution_slot(at("2026-10-22T09:45:00")) == (
        "2026-10-22",
        "INTRADAY",
    )
    assert m.orders.execution_slot(at("2026-10-22T10:35:22")) == (
        "2026-10-22",
        "INTRADAY",
    )
    assert not m.orders.schedule(at("2026-10-22T16:50:00"), "2026-10-22")["valid"]


@pytest.mark.parametrize("hour", [12, 16])
def test_daily_retry_approves_intraday_with_same_policy(pending, monkeypatch, hour):
    import daily_cycle as dc

    c, _ = pending
    (m.folder(c["run"], c["proposal"]) / "order.json").unlink()
    monkeypatch.setattr(m.radar, "now", lambda: at(f"2026-10-22T{hour}:00:00"))
    monkeypatch.setattr(
        dc, "links", lambda day: {"run": c["run"], "proposal": c["proposal"]}
    )
    rec = {"links": {}, "steps": [], "reservations": {}}
    dc.manager(rec, m.runs.run(c["run"]), "2026-10-22")
    assert rec["links"]["order"]["leg"] == "INTRADAY"
    assert "barra posterior à aprovação" in rec["outcome"]
    assert rec["steps"][-1]["by"] == dc.ACTOR
