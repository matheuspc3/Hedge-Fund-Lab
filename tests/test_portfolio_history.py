"""RAW reference marks and economic-date portfolio history, with no writes/network."""

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "dashboard"), str(PROJECT / "scripts"), str(PROJECT)]
import portfolio_history_api as h  # noqa: E402


@pytest.fixture
def portfolio(tmp_path, monkeypatch):
    m = h.manual
    monkeypatch.setattr(m, "ROOT", tmp_path / "personal")
    wallet = m.post(
        "confirm",
        {
            "request": {
                "kind": "CREATE",
                "name": "Carteira",
                "nature": "SIMULATION",
                "capital": "1000.00",
                "start_date": "2026-10-13",
            },
            "command_id": "wallet",
            "preview_token": None,
            "confirm": True,
        },
    )["wallet"]
    operations = [
        ("2026-10-13", "PETR4", "BUY", "20", "10.00", "1.00"),
        ("2026-10-14", "PETR4", "SELL", "5", "12.00", "2.00"),
        ("2026-10-14", "VALE3", "BUY", "10", "21.00", "1.00"),
        ("2026-10-15", "PETR4", "BUY", "10", "11.00", "3.00"),
    ]
    for i, (day, ticker, side, quantity, price, costs) in enumerate(operations):
        request = {
            "kind": "TRADE",
            "wallet": wallet["id"],
            "trade": {
                "economic_date": day,
                "ticker": ticker,
                "side": side,
                "quantity": quantity,
                "price": price,
                "costs": costs,
            },
        }
        preview = m.post("preview", {"request": request})
        wallet = m.post(
            "confirm",
            {
                "request": request,
                "command_id": "trade-" + str(i),
                "preview_token": preview["preview_token"],
                "confirm": True,
            },
        )["wallet"]
    return wallet


def book():
    return {
        "2026-10-13": {
            "PETR4": {"price": "10.00", "sources": []},
            "VALE3": {"price": "20.00", "sources": []},
        },
        "2026-10-14": {
            "PETR4": {"price": "11.00", "sources": []},
            "VALE3": {"price": "21.00", "sources": []},
        },
    }


def projection(wallet, quotes=None):
    return h.build(
        wallet,
        book() if quotes is None else quotes,
        [],
        today="2026-10-15",
        last_closed="2026-10-14",
        calendar=h.observed.calendar(),
    )


def test_historical_quantities_cash_costs_and_current_estimate_are_separate(portfolio):
    before = h.manual.path().read_bytes()
    d = projection(portfolio)
    daily = d["daily_history"]
    assert [p["session"] for p in daily] == ["2026-10-13", "2026-10-14", "2026-10-15"]
    assert [p["equity"] for p in daily] == ["999.00", "1021.00", None]
    assert daily[-1]["state"] == "PENDING_CLOSE"
    assert d["valuation"]["equity"] == "1018.00"
    assert d["valuation"]["positions_through"] == "2026-10-15"
    assert d["valuation"]["price_session"] == "2026-10-14"
    assert h.manual.path().read_bytes() == before


def test_correction_changes_the_economic_day_and_keeps_original_history(portfolio):
    trade = portfolio["trades"][2]
    request = {
        "kind": "CORRECTION",
        "wallet": portfolio["id"],
        "target": trade["id"],
        "reason": "Custo corrigido",
        "trade": {
            **{
                k: trade[k]
                for k in ("economic_date", "ticker", "side", "quantity", "price")
            },
            "costs": "0.50",
        },
    }
    preview = h.manual.post("preview", {"request": request})
    corrected = h.manual.post(
        "confirm",
        {
            "request": request,
            "command_id": "correction",
            "preview_token": preview["preview_token"],
            "confirm": True,
        },
    )["wallet"]
    d = projection(corrected)
    assert d["daily_history"][0]["equity"] == "999.00"
    assert d["daily_history"][1]["equity"] == "1021.50"
    assert d["valuation"]["equity"] == "1018.50"
    assert corrected["audit"][2]["trade"]["costs"] == "1.00"


def test_missing_quote_is_not_cost_basis_or_a_carried_forward_close(portfolio):
    quotes = book()
    del quotes["2026-10-14"]["VALE3"]
    d = projection(portfolio, quotes)
    assert d["valuation"]["equity"] is None
    assert d["valuation"]["missing"] == ["VALE3"]
    assert d["daily_history"][1]["equity"] is None
    assert d["daily_history"][1]["state"] == "MISSING_QUOTES"
    assert d["price_history"][1]["prices"]["VALE3"] is None


def test_no_prices_all_cash_zero_capital_and_no_history_before_start(portfolio):
    no_prices = projection(portfolio, {})
    assert no_prices["valuation"]["equity"] is None
    cash_wallet = copy.deepcopy(portfolio)
    cash_wallet.update(
        trades=[], positions=[], cash="0.00", capital="0.00", start_date="2026-10-14"
    )
    d = projection(cash_wallet, {})
    assert (
        d["valuation"]["equity"] == "0.00" and d["valuation"]["return_fraction"] is None
    )
    assert all(p["session"] >= "2026-10-14" for p in d["daily_history"])


def test_get_is_read_only_and_strict_about_wallet_identity(portfolio, monkeypatch):
    before = h.manual.path().read_bytes()
    monkeypatch.setattr(h, "quote_book", lambda symbols: (book(), []))
    monkeypatch.setattr(h.radar, "now", lambda: pd.Timestamp("2026-10-15T12:00:00-03:00"))
    d = h.get({"wallet": portfolio["id"]})
    assert d["wallet_revision"] == portfolio["revision"] and d["read_only"]
    assert h.manual.path().read_bytes() == before
    with pytest.raises(ValueError):
        h.get({"wallet": "other-wallet"})
    with pytest.raises(ValueError):
        h.get({"wallet": portfolio["id"], "unexpected": "value"})


@pytest.fixture
def sources(tmp_path, monkeypatch):
    h.verified_input.cache_clear()
    manifest = h.radar.manifest("live")
    entries = {}
    for i in range(2):
        root = tmp_path / ("source-" + str(i))
        folder = h.radar.folder_for(root, "PETR4", "2026-10-14")
        folder.mkdir(parents=True)
        (folder / "input.json").write_text("input " + str(i))
        (folder / "bars.csv").write_text("bars")
        entries[str(i)] = {
            "id": "run-" + str(i),
            "root": root,
            "mode": "CONSULTATIVE_SANDBOX",
            "universe": ["PETR4"],
            "session": "2026-10-14",
        }
    entries["synthetic"] = {**entries["0"], "id": "synthetic", "mode": "SYNTHETIC_DEMO"}
    monkeypatch.setattr(h.runs, "load", lambda: {"runs": entries})
    monkeypatch.setattr(h.runs, "root_of", lambda entry: entry["root"])
    monkeypatch.setattr(h.radar, "now", lambda: pd.Timestamp("2026-10-15T12:00:00-03:00"))
    data = {
        "manifest": manifest,
        "manifest_sha256": h.radar.digest(manifest),
        "prepared_at": "2026-10-15T10:00:00-03:00",
        "adjusted_close": 999.0,
        "raw_bar": {
            "abertura": 10.0,
            "maxima": 12.0,
            "minima": 9.0,
            "fechamento": 11.0,
            "volume": 1000.0,
        },
    }
    monkeypatch.setattr(h.radar, "checked_input", lambda *args: copy.deepcopy(data))
    return entries, data


def test_sources_use_raw_not_adjusted_and_exclude_synthetic(sources):
    quotes, issues = h.quote_book(["PETR4"])
    assert quotes["2026-10-14"]["PETR4"]["price"] == "11.0"
    assert len(quotes["2026-10-14"]["PETR4"]["sources"]) == 2
    assert not issues


def test_conflicting_raw_references_become_gap(sources, monkeypatch):
    _, data = sources

    def source(root, *args):
        value = copy.deepcopy(data)
        value["raw_bar"]["fechamento"] = 11.0 if root.name == "source-0" else 12.0
        return value

    monkeypatch.setattr(h.radar, "checked_input", source)
    quotes, issues = h.quote_book(["PETR4"])
    assert quotes["2026-10-14"]["PETR4"] is None
    assert issues[-1]["reason"] == "CONFLICTING_RAW_REFERENCES"


def test_corruption_or_future_availability_never_supplies_prices(sources):
    _, data = sources
    data["prepared_at"] = "2026-10-16T10:00:00-03:00"
    quotes, issues = h.quote_book(["PETR4"])
    assert not quotes and len(issues) == 2


def test_cached_input_is_rechecked_when_a_source_file_changes(sources, monkeypatch):
    entries, _ = sources
    h.quote_book(["PETR4"])
    folder = h.radar.folder_for(entries["0"]["root"], "PETR4", "2026-10-14")
    (folder / "bars.csv").write_text("corrupted bars")
    monkeypatch.setattr(
        h.radar,
        "checked_input",
        lambda *args: (_ for _ in ()).throw(ValueError("corrupted")),
    )
    quotes, issues = h.quote_book(["PETR4"])
    assert len(quotes["2026-10-14"]["PETR4"]["sources"]) == 1
    assert len(issues) == 1
