"""APP-03: GET-only personal valuation from verified, local RAW daily references.

No downloads, adjusted-price substitution, inference or financial event writes.
"""

from functools import lru_cache

import dividends_api as dividends
import manual_portfolio_api as manual
import market_base_api as base
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


def quote_book(symbols, since=None):
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
    # DP-27: the local B3 market base is one more candidate; a disagreement between
    # its files (conflict) or with a Radar close is a gap, never a chosen price.
    for ticker in sorted(symbols) if since else ():
        for row in base.merged(ticker, closed):
            if row["date"] < since:
                continue
            if row["conflict"]:
                issues.append(
                    {
                        "ticker": ticker,
                        "session": row["date"],
                        "reason": "MARKET_BASE_CONFLICT",
                    }
                )
                continue
            values.setdefault((ticker, row["date"]), []).append(
                {
                    "price": manual.number(str(row["close"]), "price", positive=True),
                    "run": None,
                    "source": "B3_MARKET_BASE",
                    "acquired_at": row["acquired_at"],
                    "prepared_at": row["acquired_at"],
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
                "sources": sorted(
                    candidates, key=lambda c: (c["prepared_at"], c["run"] or "")
                ),
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
    for trade in wallet["trades"]:
        if trade["economic_date"] <= day:
            history.append(
                {
                    "wallet": wallet["id"],
                    "id": trade["id"],
                    "sequence": trade["order"],
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
    # DP-30 A: booked dividends enter the replay on their payment date.
    for d in wallet["dividends"]:
        if d["payment_date"] <= day:
            history.append(
                {
                    "wallet": wallet["id"],
                    "id": d["id"],
                    "sequence": d["order"],
                    "recorded_at": d["recorded_at"],
                    "sha256": wallet["revision"],
                    "request": {
                        "kind": "DIVIDEND",
                        "wallet": wallet["id"],
                        "dividend": {
                            k: d[k]
                            for k in (
                                "ticker",
                                "kind",
                                "data_com",
                                "payment_date",
                                "quantity",
                                "gross",
                                "net",
                            )
                        },
                        "trade": None,
                    },
                }
            )
    return manual.replay(history)


def valuation(wallet, prices, session, receivable=b.ZERO, unbooked=b.ZERO):
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
    # DP-30: after the ex date the price drops, so the receivable is equity (not cash);
    # received dividends are already in the ledger cash.
    equity = (
        b.dec(wallet["cash"]) + invested + receivable + unbooked
        if invested is not None
        else None
    )
    change = equity - b.dec(wallet["capital"]) if equity is not None else None
    fraction = (
        change / b.dec(wallet["capital"])
        if change is not None and b.dec(wallet["capital"])
        else None
    )
    return {
        "price_session": session,
        "cash": wallet["cash"],
        "dividends_received": wallet["dividends_received"],
        "dividends_receivable": str(receivable),
        "cash_available": wallet["cash"],  # kept for the UI: ledger cash incl. dividends
        "positions": positions,
        "invested_value": str(invested) if invested is not None else None,
        "equity": str(equity) if equity is not None else None,
        "change": str(change) if change is not None else None,
        "return_fraction": str(fraction) if fraction is not None else None,
        "missing": missing,
    }


MANAGER_KINDS = (
    "WALLET_MANAGER_REFERENCE_PRICE_SIMULATION",  # old rule: booked at approval
    "WALLET_MANAGER_AUCTION_EXECUTION",  # DP-33: booked at the official auction
    "WALLET_MANAGER_INTRADAY_EXECUTION",  # DP-35: first post-approval 1m bar
)
PERIODS = (
    ("1d", "Dia"),
    ("5d", "5 dias"),
    ("mtd", "Mês"),
    ("ytd", "Ano"),
    ("12m", "12 meses"),
)


def pending(items, wallet, session):
    """(receivable, received-not-booked-yet): both equity-only, never cash.

    ponytail: compared by totals; a stale booking larger than the computed value is
    clamped to zero instead of reopening the old on-read cash.
    """
    got, receivable = dividends.on(items, session)
    return receivable, max(got - b.dec(wallet["dividends_received"]), b.ZERO)


def periods(daily, wallet, sessions, anchor_ok):
    """DP-04: variations over AVAILABLE closes only; a missing anchor is never zero."""
    ok = [p for p in daily if p["state"] == "AVAILABLE"]
    end = ok[-1] if ok else None
    by_day = {p["session"]: p for p in ok}

    def before(cutoff, inclusive=False):
        # last calendar session before (or on) cutoff; None when not covered
        return max(
            (d for d in sessions if d < cutoff or inclusive and d == cutoff), default=None
        )

    def item(key, label, anchor_day, anchor_equity=None):
        anchor = by_day.get(anchor_day) if anchor_equity is None else None
        if anchor is not None:
            anchor_equity = anchor["equity"]
        ready = end is not None and anchor_equity is not None and anchor_day is not None
        if ready and anchor is not None and anchor["session"] >= end["session"]:
            ready = False
        change = b.dec(end["equity"]) - b.dec(anchor_equity) if ready else None
        base = b.dec(anchor_equity) if ready else None
        return {
            "key": key,
            "label": label,
            "state": "AVAILABLE"
            if ready
            else "UNAVAILABLE"
            if end is None
            else "INSUFFICIENT_HISTORY",
            "anchor_session": anchor_day if ready else None,
            "end_session": end["session"] if end else None,
            "anchor_equity": anchor_equity if ready else None,
            "end_equity": end["equity"] if ready else None,
            "change": str(change) if ready else None,
            "return_fraction": str(change / base) if ready and base else None,
        }

    days = [p["session"] for p in daily]
    i = days.index(end["session"]) if end else 0
    cutoffs = {}
    if end:
        d = end["session"]
        cutoffs = {
            "1d": days[i - 1] if i >= 1 else None,
            "5d": days[i - 5] if i >= 5 else None,
            "mtd": before(d[:7] + "-01"),
            "ytd": before(d[:4] + "-01-01"),
            # ponytail: Feb 29 maps to Feb 28 a year earlier
            "12m": before(
                str(int(d[:4]) - 1) + "-" + d[5:].replace("02-29", "02-28"), True
            ),
        }
    out = [item(k, label, cutoffs.get(k)) for k, label in PERIODS]
    out.append(
        item(
            "inception",
            "Desde o início",
            wallet["start_date"] if anchor_ok else None,
            wallet["capital"],
        )
    )
    return out


def build(wallet, book, issues, *, today, last_closed, calendar):
    symbols = sorted(
        {t["ticker"] for t in wallet["trades"]}
        | {p["ticker"] for p in wallet["positions"]}
    )
    reference_day = max(book, default=None)
    items = dividends.entitlements(wallet, today)
    current = valuation(
        wallet,
        book.get(reference_day, {}),
        reference_day,
        *pending(items, wallet, today),
    )
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
        point = valuation(
            snapshot, book.get(day, {}), day, *pending(items, snapshot, day)
        )
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
        # ponytail: trades dated on a non-session day appear in no point.
        point["trades"] = [
            {
                **{k: t[k] for k in ("id", "ticker", "side", "quantity", "price")},
                "origin": "MANAGER"
                if (t.get("source") or {}).get("kind") in MANAGER_KINDS
                else "RULE"
                if (t.get("source") or {}).get("kind") == "RULE_STRATEGY_EXECUTION"
                else "MANUAL",
            }
            for t in wallet["trades"]
            if t["economic_date"] == day
        ]
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
    initial_anchor = (
        calendar["coverage"][0] <= wallet["start_date"] <= calendar["coverage"][1]
    )
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
        "initial_anchor_available": initial_anchor,
        "dividends": {
            "source": dividends.SOURCE,
            "fetched_at": dividends.fetched_at(symbols),
            "events": items,
            "received": dividends.total(items, "RECEBIDO"),
            "receivable": dividends.total(items, "A_RECEBER"),
            "announced": dividends.total(items, "PREVISTO"),
        },
        "valuation": current,
        "daily_history": daily,
        "periods": periods(daily, wallet, calendar["trading_sessions"], initial_anchor),
        "price_history": price_history,
        "tickers": symbols,
        "references": book,
        "source_issues": issues,
        "classification": "LOCAL_FROZEN_RADAR_RAW_REFERENCE_NOT_LIVE",
        "read_only": True,
        "history_basis": "ECONOMIC_DATE_REPLAY_WITH_CURRENT_CORRECTIONS",
        "corporate_events_included": False,  # cash dividends only; no splits/bonus
    }


def get(query):
    manual.fields(query, ("wallet",))
    wallet = manual.get({"wallet": query["wallet"]})["selected"]
    symbols = sorted(
        {t["ticker"] for t in wallet["trades"]}
        | {p["ticker"] for p in wallet["positions"]}
    )
    book, issues = quote_book(symbols, wallet["start_date"])
    at = radar.now()
    return build(
        wallet,
        book,
        issues,
        today=at.date().isoformat(),
        last_closed=radar.last_closed(at),
        calendar=observed.calendar(),
    )
