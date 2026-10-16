"""APP-03: GET-only personal valuation from verified, local RAW daily references.

No downloads, adjusted-price substitution, inference or financial event writes.
"""

from functools import lru_cache

import manual_portfolio_api as manual
import pilot_observed_data as observed
import radar_runs as runs

b, radar = manual.b, runs.radar


@lru_cache(maxsize=128)
def verified_input(root, ticker, day, input_sha, bars_sha, manifest_sha):
    data = radar.checked_input(root, ticker, day)
    path = radar.folder_for(root, ticker, day)
    if (
        radar.sha_file(path / "input.json") != input_sha
        or radar.sha_file(path / "bars.csv") != bars_sha
        or data["manifest_sha256"] != manifest_sha
    ):
        raise ValueError("reference_changed_during_read")
    return data


def quote_book(symbols):
    """Only registered live runs; conflicts remain gaps, never latest-wins prices."""
    values, issues = {}, []
    manifest_sha = radar.digest(radar.manifest("live"))
    at = radar.now()
    closed = radar.last_closed(at)
    for entry in runs.load()["runs"].values():
        if entry["mode"] != "CONSULTATIVE_SANDBOX" or entry["session"] > closed:
            continue
        root = runs.root_of(entry)
        for ticker in sorted(set(entry["universe"]) & set(symbols)):
            day = entry["session"]
            path = radar.folder_for(root, ticker, day)
            if not (path / "input.json").exists():
                continue
            try:
                input_sha = radar.sha_file(path / "input.json")
                bars_sha = radar.sha_file(path / "bars.csv")
                data = verified_input(
                    root, ticker, day, input_sha, bars_sha, manifest_sha
                )
                if data["manifest"]["mode"] != "live" or b.instant(
                    data["prepared_at"]
                ) > b.instant(at.isoformat()):
                    raise ValueError("reference_not_available")
                radar.validate_ohlcv(
                    radar.pd.DataFrame(
                        [data["raw_bar"]], index=radar.pd.DatetimeIndex([day])
                    )
                )
                price = manual.number(
                    str(data["raw_bar"]["fechamento"]), "price", positive=True
                )
                values.setdefault((ticker, day), []).append(
                    {
                        "price": price,
                        "run": entry["id"],
                        "input_sha256": input_sha,
                        "prepared_at": data["prepared_at"],
                    }
                )
            except (ValueError, TypeError, KeyError, OSError, ArithmeticError):
                issues.append(
                    {
                        "ticker": ticker,
                        "session": day,
                        "run": entry["id"],
                        "reason": "REFERENCE_INVALID_OR_UNAVAILABLE",
                    }
                )
    result = {}
    for (ticker, day), candidates in values.items():
        prices = {b.dec(c["price"]) for c in candidates}
        if len(prices) != 1:
            issues.append(
                {"ticker": ticker, "session": day, "reason": "CONFLICTING_RAW_REFERENCES"}
            )
            result.setdefault(day, {})[ticker] = None
        else:
            result.setdefault(day, {})[ticker] = {
                "price": str(next(iter(prices))),
                "sources": sorted(candidates, key=lambda c: (c["prepared_at"], c["run"])),
            }
    return result, issues


def historical_wallet(wallet, day):
    # ponytail: O(days * trades) using the existing accounting replay. Verified
    # checkpoints can replace this when long personal histories justify them.
    history = [
        {
            "wallet": wallet["id"],
            "request": {
                k: wallet[k] for k in ("name", "nature", "capital", "start_date")
            },
            "recorded_at": wallet["created_at"],
            "sha256": wallet["revision"],
        }
    ]
    for i, trade in enumerate(wallet["trades"]):
        if trade["economic_date"] <= day:
            history.append(
                {
                    "wallet": wallet["id"],
                    "id": trade["id"],
                    "sequence": i + 1,
                    "recorded_at": trade["recorded_at"],
                    "sha256": wallet["revision"],
                    "request": {
                        "kind": "TRADE",
                        "wallet": wallet["id"],
                        "trade": {
                            k: trade[k]
                            for k in (
                                "ticker",
                                "side",
                                "quantity",
                                "price",
                                "costs",
                                "economic_date",
                            )
                        },
                    },
                }
            )
    return manual.replay(history)


def valuation(wallet, prices, session):
    positions, missing = [], []
    for position in wallet["positions"]:
        reference = prices.get(position["ticker"])
        value = (
            b.money(b.dec(position["quantity"]) * b.dec(reference["price"]))
            if reference
            else None
        )
        if reference is None:
            missing.append(position["ticker"])
        positions.append(
            {
                **position,
                "reference_price": reference["price"] if reference else None,
                "market_value": str(value) if value is not None else None,
                "price_session": session if reference else None,
            }
        )
    invested = (
        None if missing else sum((b.dec(p["market_value"]) for p in positions), b.ZERO)
    )
    equity = b.dec(wallet["cash"]) + invested if invested is not None else None
    change = equity - b.dec(wallet["capital"]) if equity is not None else None
    fraction = (
        change / b.dec(wallet["capital"])
        if change is not None and b.dec(wallet["capital"])
        else None
    )
    return {
        "price_session": session,
        "cash": wallet["cash"],
        "positions": positions,
        "invested_value": str(invested) if invested is not None else None,
        "equity": str(equity) if equity is not None else None,
        "change": str(change) if change is not None else None,
        "return_fraction": str(fraction) if fraction is not None else None,
        "missing": missing,
    }


def build(wallet, book, issues, *, today, last_closed, calendar):
    symbols = sorted(
        {t["ticker"] for t in wallet["trades"]}
        | {p["ticker"] for p in wallet["positions"]}
    )
    reference_day = max(book, default=None)
    current = valuation(wallet, book.get(reference_day, {}), reference_day)
    # Current positions can include today's trades while the reference is yesterday.
    # This estimate is kept separate from the daily close series.
    current["positions_through"] = max(
        (t["economic_date"] for t in wallet["trades"]), default=wallet["start_date"]
    )
    daily = []
    for day in calendar["trading_sessions"]:
        if not wallet["start_date"] <= day <= today:
            continue
        snapshot = historical_wallet(wallet, day)
        point = valuation(snapshot, book.get(day, {}), day)
        if day > last_closed:
            point.update(
                equity=None, invested_value=None, change=None, return_fraction=None
            )
        point.update(
            session=day,
            state="PENDING_CLOSE"
            if day > last_closed
            else "MISSING_QUOTES"
            if point["missing"]
            else "AVAILABLE",
        )
        daily.append(point)
    stock_days = sorted(
        set(book)
        | {
            d
            for d in calendar["trading_sessions"]
            if min(book, default=today) <= d <= today
        }
    )
    price_history = [
        {
            "session": day,
            "prices": {t: (book.get(day, {}).get(t) or {}).get("price") for t in symbols},
        }
        for day in stock_days
    ]
    return {
        "identity": "HFL-PERSONAL-HISTORY-REFERENCE-V1",
        "wallet": wallet["id"],
        "wallet_revision": wallet["revision"],
        "wallet_name": wallet["name"],
        "nature": wallet["nature"],
        "today": today,
        "last_closed": last_closed,
        "initial_capital": wallet["capital"],
        "start_date": wallet["start_date"],
        "initial_anchor_available": calendar["coverage"][0]
        <= wallet["start_date"]
        <= calendar["coverage"][1],
        "valuation": current,
        "daily_history": daily,
        "price_history": price_history,
        "tickers": symbols,
        "references": book,
        "source_issues": issues,
        "classification": "LOCAL_FROZEN_RADAR_RAW_REFERENCE_NOT_LIVE",
        "read_only": True,
        "history_basis": "ECONOMIC_DATE_REPLAY_WITH_CURRENT_CORRECTIONS",
        "corporate_events_included": False,
    }


def get(query):
    manual.fields(query, ("wallet",))
    wallet = manual.get({"wallet": query["wallet"]})["selected"]
    symbols = sorted(
        {t["ticker"] for t in wallet["trades"]}
        | {p["ticker"] for p in wallet["positions"]}
    )
    book, issues = quote_book(symbols)
    at = radar.now()
    return build(
        wallet,
        book,
        issues,
        today=at.date().isoformat(),
        last_closed=radar.last_closed(at),
        calendar=observed.calendar(),
    )
