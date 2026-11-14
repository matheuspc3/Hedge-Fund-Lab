"""DP-33/35: durable manager orders, official opening or post-approval intraday prices.

Approving no longer books at the reference close: it stores one sealed, idempotent
PENDING order per proposal (order.json, beside the proposal). `settle_pending` (called by
the DP-27 market update) books it through `manual.batch` at the official OPEN (PREABE)
or CLOSE (PREULT) of the target session, with the economic date of that auction.
DP-35 adds INTRADAY orders using the first traded 1m bar after approval, polled by
the server. Its complete source is frozen in execution-prices.json before booking.
Old OPEN/CLOSE orders retain their recorded policy. All financial records stay sealed.

DP-33 stage B (preview/approval quotes, never marks or prompts): a
delayed-quote snapshot per ticker (DP-26 Yahoo path), the volatility tolerance band
between the preview and the approval quote, and the "stale thesis" alert against the
close the manager saw. The sigma/band parameters live here, outside the manager
contract hash.
"""

import hashlib
import logging
import math
import statistics
import threading
from datetime import date, datetime, time, timedelta

import dividends_api as dividends
import manual_portfolio_api as manual
import market_base_api as base
import radar_runs as runs
import stock_history_api as stock
from zoneinfo import ZoneInfo

from src.backtesting.b3_calendar import B3Calendar

b, radar = manual.b, runs.radar
IDENTITY = "HFL-WALLET-MANAGER-AUCTION-ORDER-V1"
KIND = "WALLET_MANAGER_AUCTION_EXECUTION"
SP = ZoneInfo("America/Sao_Paulo")
LOCK = (
    threading.Lock()
)  # ponytail: single process; a second app instance needs a file lock
# Approval cutoffs of the standard regime: opening pre-auction starts 09:45; the closing
# call is 16:55-17:00, cut 5 min earlier because extensions can push it past 17:00.
OPEN_CUTOFF, CLOSE_CUTOFF = time(9, 45), time(16, 50)
# (first day, shift in hours of both cutoffs). B3 follows the US daylight-saving clock:
# +1h from 2025-11-03 until early March 2026 (Money Times). ponytail: 2026-03-09 (Monday
# after the US change) and 2026-11-02 are inferred by analogy, NOT confirmed by a B3
# circular - confirm and edit these dates; nothing else depends on them.
REGIMES = (("2000-01-01", 0), ("2025-11-03", 1), ("2026-03-09", 0), ("2026-11-02", 1))
FILES = ("order", "execution", "expired", "opportunity")
INTRADAY_POLICY = "HFL-POST-APPROVAL-1M-V1"
INTRADAY_SINCE = "2026-10-22"  # DP-35; old recorded orders keep their own leg.


def cutoffs(day):
    """(opening, closing) approval cutoffs of the ISO `day`, aware in America/Sao_Paulo."""
    shift = [h for start, h in REGIMES if start <= day][-1]
    d = date.fromisoformat(day)
    return tuple(
        datetime.combine(d, t, SP) + timedelta(hours=shift)
        for t in (OPEN_CUTOFF, CLOSE_CUTOFF)
    )


def first_auction(at):
    """(session, leg) of the first official auction after `at`: OPEN or CLOSE."""
    at = getattr(at, "to_pydatetime", lambda: at)().astimezone(SP)
    calendar = B3Calendar()
    if calendar.is_session(at.date()):
        opening, closing = cutoffs(at.date().isoformat())
        if at < opening:
            return at.date().isoformat(), "OPEN"
        if at < closing:
            return at.date().isoformat(), "CLOSE"
    return calendar.next_session(at.date()).isoformat(), "OPEN"


def expired(target_date, at):
    """DP-33 (4): valid until the target session's last cutoff, then never."""
    return first_auction(at)[0] > target_date


def execution_slot(at):
    session, leg = first_auction(at)
    if session >= INTRADAY_SINCE and leg == "CLOSE":
        leg = "INTRADAY"
    return session, leg


def schedule(at, target_date):
    session, leg = execution_slot(at)
    opening, closing = cutoffs(session)
    return {
        "session": session,
        "leg": leg,
        "valid": session <= target_date,
        "valid_until": cutoffs(target_date)[1].isoformat(timespec="minutes"),
        "cutoffs": {
            "open": opening.isoformat(timespec="minutes"),
            "close": closing.isoformat(timespec="minutes"),
        },
    }


def appliable(c):
    return c["wallet"]["nature"] == "SIMULATION" and c["wallet"].get("strategy") not in (
        "BUY_HOLD",
        *manual.RULE_STRATEGIES,
    )


def read(path):
    return b.check_seal(radar.read(path)) if path.exists() else None


def records(root):
    return {k: read(root / (k + ".json")) for k in FILES}


def folders():
    for entry in runs.load()["runs"].values():
        for p in sorted((runs.root_of(entry) / "wallet-manager").glob("*/context.json")):
            yield p.parent


def expire(root, c, result, at):
    """EXPIRED record with the opportunity-cost inputs; idempotent (first sighting wins)."""
    path = root / "expired.json"
    if not path.exists():
        radar.write(
            path,
            b.sealed(
                {
                    "identity": IDENTITY,
                    "status": "EXPIRED",
                    "run": c["run"],
                    "proposal": c["proposal"],
                    "proposal_sha256": result["sha256"],
                    "wallet": c["wallet"]["id"],
                    "target_date": c["target_date"],
                    "reference_session": c["reference_session"],
                    "detected_at": at.isoformat(),
                    "basket": [
                        {k: t[k] for k in ("ticker", "side", "quantity")}
                        for t in result["trades"]
                    ],
                    "decision_prices": {
                        t["ticker"]: t["price"] for t in result["trades"]
                    },
                }
            ),
            immutable=True,
        )
    return read(path)


def place(root, c, result, at, quotes=None, checks=None):
    """Idempotent pending order of one proposal; one pending order per wallet."""
    with LOCK:
        if (order := read(root / "order.json")) is not None:
            return order, True
        session, leg = execution_slot(at)
        if session > c["target_date"]:
            raise ValueError("manager_proposal_expired")
        for other in folders():
            theirs = read(other / "order.json")
            if (
                other != root
                and theirs
                and theirs["wallet"]["id"] == c["wallet"]["id"]
                and not (other / "execution.json").exists()
            ):
                raise ValueError("manager_pending_order_exists")
        order = b.sealed(
            {
                "identity": IDENTITY,
                "status": "PENDING_INTRADAY" if leg == "INTRADAY" else "PENDING_AUCTION",
                "execution_policy": INTRADAY_POLICY if leg == "INTRADAY" else "DP-33",
                "run": c["run"],
                "proposal": c["proposal"],
                "proposal_sha256": result["sha256"],
                "context_sha256": c["sha256"],
                "wallet": {"id": c["wallet"]["id"], "revision": c["wallet"]["revision"]},
                "cost_rate_pct": c["cost_rate_pct"],
                "basket": [
                    {k: t[k] for k in ("ticker", "side", "quantity")}
                    for t in result["trades"]
                ],
                "target_date": c["target_date"],
                "session": session,
                "leg": leg,
                "approved_at": at.isoformat(),
                "reference_session": c["reference_session"],
                "decision_prices": {t["ticker"]: t["price"] for t in result["trades"]},
                # {ticker: delayed-quote snapshot} at the preview and at the approval.
                "quotes": quotes or {"preview": None, "approval": None},
                # Band checks + stale-thesis alert/acknowledgement of the approval.
                "checks": checks,
            }
        )
        radar.write(root / "order.json", order, immutable=True)
        return order, False


# ---- DP-33 stage B: delayed-quote snapshot, tolerance band, stale thesis ----
POLICY = "HFL-DELAYED-QUOTE-POLICY-V1"
SOURCE = "Yahoo (atraso ~15 min)"
DELAY_MIN = 15
SESSION_MIN = 415  # continuous trading 10:00-16:55 (standard regime)
K, TOL_MIN, TOL_MAX = 3, 0.005, 0.02
WINDOW, MIN_SESSIONS = 60, 20


def session_clock(now):
    """(state, fraction): OPEN while continuous trading runs, PRE before it, else CLOSED."""
    now = getattr(now, "to_pydatetime", lambda: now)().astimezone(SP)
    if not B3Calendar().is_session(now.date()):
        return "CLOSED", 0.0
    start = cutoffs(now.date().isoformat())[0] + timedelta(minutes=15)  # 09:45 -> 10:00
    if now < start:
        return "PRE", 0.0
    f = (now - start) / timedelta(minutes=SESSION_MIN)
    return ("OPEN", f) if f < 1 else ("CLOSED", 1.0)


def delayed_bars(tickers, now, day):
    """{ticker: DP-26 1-min record of `day`} after refreshing it under the DP-26 lock.

    Reuses stock_history_api.collect (the only Yahoo client). `day` still trading (or
    ended before 18:00) -> the live record, fetched now; a closed `day` -> the sealed
    archive collect writes for it. A lock busy for 20 s, a failed fetch or no delayed
    bar yet just leaves the ticker out; the snapshot then says so.
    """
    live = day == stock.session_today(now)
    if not (live or day <= radar.last_closed(now)) or not stock.INTRADAY_LOCK.acquire(
        timeout=20
    ):
        return {}
    try:
        out = {}
        for t in tickers:
            try:
                stock.collect(t, now)
                rec = stock.LIVE.get(t) if live else stock.load_day(t, day)
            except Exception:
                continue
            if rec and (
                not live or datetime.fromisoformat(rec["fetched_at"]) >= now
            ):  # not a stale live one
                out[t] = rec
        return out
    finally:
        stock.INTRADAY_LOCK.release()


def digest(value):
    return hashlib.sha256(manual.canonical(value).encode()).hexdigest()


def last_close(ticker, as_of):
    rows = [r for r in base.merged(ticker, as_of) if price_of(r, "close")]
    return rows[-1] if rows else None


def snapshot(tickers, now):
    """{ticker: delayed-quote snapshot}. Never a fabricated value.

    The session that matters is today while trading or once it ended, else the last closed
    one. Its official close in the base wins (published, flagged). Without it (COTAHIST
    lands the next morning), its last coherent delayed bar (DELAYED_QUOTE; flagged
    outside trading). ponytail: Yahoo's 1-min bars stop at the continuous session's last
    trade, so after the session this is not the closing-auction price. Otherwise (Yahoo
    down, before the first delayed bar) -> the last official close of the base, flagged;
    `value` is None if even that is missing.
    """
    state, fraction = session_clock(now)
    today, out = now.date().isoformat(), {}
    day = today if state == "OPEN" or fraction == 1 else radar.last_closed(now)
    official = {t: last_close(t, today) for t in tickers}
    missing = [t for t in tickers if not official[t] or official[t]["date"] < day]
    live = delayed_bars(missing, now, day) if missing else {}
    for t in tickers:
        common = {
            "session_state": state,
            "session_fraction": round(fraction, 6),
            "policy": POLICY,
        }
        rec = live.get(t)
        bars = rec["bars"] if rec and rec["day"] == day else []
        bar = next((x for x in reversed(bars) if stock.bar_close(x) is not None), None)
        if bar:
            hour, minute = map(int, bar[0].split(":"))
            out[t] = {
                **common,
                # a closed day's bar covers the whole session (stale check units)
                "session_fraction": round(fraction if state == "OPEN" else 1.0, 6),
                "basis": "DELAYED_QUOTE",
                "flag": None if state == "OPEN" else "SESSION_" + state,
                "value": f"{stock.bar_close(bar):.2f}",
                "source": SOURCE,
                "declared_delay_min": DELAY_MIN,
                "quote_time": datetime.combine(
                    date.fromisoformat(day), time(hour, minute), SP
                ).isoformat(),
                "quote_session": day,
                "fetched_at": rec["fetched_at"],
                "payload_sha256": digest(rec),
            }
            continue
        row = official[t]
        out[t] = {
            **common,
            "basis": "LAST_OFFICIAL_CLOSE",
            "flag": "INTRADAY_UNAVAILABLE" if t in missing else "SESSION_" + state,
            "value": str(price_of(row, "close")) if row else None,
            "source": "B3 COTAHIST (fechamento oficial)",
            "declared_delay_min": None,
            "quote_time": row["date"] if row else None,
            "quote_session": row["date"] if row else None,
            "fetched_at": now.isoformat(),
            "payload_sha256": digest(row) if row else None,
        }
    return out


def volatility(ticker, as_of, window=WINDOW):
    """Official RAW sigmas over the last `window` sessions <= as_of (conflicts skipped).

    sigma60 = std of log(close/open); sigma_d = std of log(close/previous close);
    overnight_share = var(log(open/previous close)) / var(log(close/previous close)),
    at most 1. ponytail: "previous" is the previous usable row, so a skipped conflict
    makes a 2-session return, and splits/ex-dividend drops stay in (RAW). None below
    MIN_SESSIONS: callers then use the ceiling band and skip the stale check.
    """
    rows = [
        r
        for r in base.merged(ticker, as_of)
        if price_of(r, "open") and price_of(r, "close")
    ][-(window + 1) :]
    if len(rows) < MIN_SESSIONS + 1:
        return None
    pairs = list(zip(rows, rows[1:]))
    var_d = statistics.variance(math.log(r["close"] / p["close"]) for p, r in pairs)
    gap = statistics.variance(math.log(r["open"] / p["close"]) for p, r in pairs)
    return {
        "sigma60": statistics.stdev(math.log(r["close"] / r["open"]) for _, r in pairs),
        "sigma_d": math.sqrt(var_d),
        "overnight_share": min(1.0, gap / var_d) if var_d else 0.0,
        "sessions": len(pairs),
        "as_of": rows[-1]["date"],
    }


def tolerance(sigma, minutes, early=False):
    """clamp(3 sigma60 sqrt(h/415), 0.5%, 2%); sigma doubles in the first 30 min of trading.

    An unknown sigma (short base) gets the ceiling, never an invented volatility.
    """
    if sigma is None:
        return TOL_MAX
    raw = K * sigma * (2 if early else 1) * math.sqrt(max(minutes, 0) / SESSION_MIN)
    return min(max(raw, TOL_MIN), TOL_MAX)


def early(snap, extra=0):
    """True if the quote (moved `extra` minutes ahead) is inside the first 30 min of trading."""
    return (
        snap["session_state"] == "OPEN"
        and snap["session_fraction"] * SESSION_MIN + extra < 30
    )


def sessions_in(first, last):
    return len(B3Calendar().sessions_between(first, last)) if first <= last else 0


def adjusted_reference(price, ticker, reference, through):
    """(price minus the cash proceeds whose ex-date is in (reference, through], events).

    Ex-date = first session after the data-com (B3), so a data-com >= the reference session
    has its effect after the manager's close. Gross value per share (a JCP's tax falls on
    the holder, not on the price). ponytail: only proceeds already in the DP-30 B3
    snapshot; no splits or bonus shares.
    """
    cal = B3Calendar()
    hits = [
        e
        for e in dividends.events(ticker)
        if e["data_com"] >= reference
        and cal.next_session(date.fromisoformat(e["data_com"])).isoformat() <= through
    ]
    adjusted = b.dec(price) - sum((b.dec(e["value_per_share"]) for e in hits), b.ZERO)
    keys = ("kind", "data_com", "value_per_share")
    return float(adjusted), [{k: e[k] for k in keys} for e in hits]


def stale_check(c, ticker, snap, vol):
    """Alert if |quote / adjusted manager close - 1| > 3 sigma_d sqrt(s + (1-s) f) (+ whole sessions)."""
    if not vol or not snap["value"]:
        return {"evaluated": False, "alert": False}
    ref, q = (
        date.fromisoformat(c["reference_session"]),
        date.fromisoformat(snap["quote_session"]),
    )
    day = timedelta(1)
    if (
        snap["basis"] == "DELAYED_QUOTE"
    ):  # today is partial: gap share s + intraday (1-s) f
        s = vol["overnight_share"]
        units = sessions_in(ref + day, q - day) + s + (1 - s) * snap["session_fraction"]
    else:  # a published close: whole sessions after the reference
        units = sessions_in(ref + day, q)
    adjusted, events = adjusted_reference(
        c["prices"][ticker], ticker, c["reference_session"], snap["quote_session"]
    )
    move = float(snap["value"]) / adjusted - 1
    band = K * vol["sigma_d"] * math.sqrt(units)
    return {
        "evaluated": units > 0,
        "alert": units > 0 and abs(move) > band,
        "move": round(move, 6),
        "band": round(band, 6),
        "reference": c["prices"][ticker],
        "adjusted_reference": round(adjusted, 6),
        "dividends": events,
    }


def pct(x):
    return f"{x * 100:.2f}".replace(".", ",")


def stale_message(ticker, check):
    return (
        f"Tese possivelmente desatualizada: {ticker} moveu "
        + f"{check['move'] * 100:+.2f}%".replace(".", ",")
        + f" desde o fechamento usado pelo gestor (faixa de 3 desvios: {pct(check['band'])}%)."
    )


def review(c, tickers, preview, approval=None):
    """({ticker: row}, [band-breach messages]) for the preview or the approval gate.

    Preview (approval=None): decision price, delayed quote, the approval band after
    15/30/60 min and the stale check on the preview quote. Approval: the band
    tolerance(h) between the two quotes (h = minutes between their collection times)
    and the stale check on the approval quote. Two closed-session snapshots of the same
    official close have move 0, so they pass.
    """
    rows, breaches = {}, []
    for t in tickers:
        vol = volatility(t, c["reference_session"])
        p, a = preview[t], (approval or preview)[t]
        sigma = vol and vol["sigma60"]
        row = {
            "decision": c["prices"][t],
            "quote": a,
            "volatility": vol,
            "stale": stale_check(c, t, a, vol),
        }
        if approval is None:
            row["tolerance_by_minutes"] = {
                str(h): round(tolerance(sigma, h, early(p, h)), 6) for h in (15, 30, 60)
            }
        elif p["value"] and a["value"]:
            minutes = (
                datetime.fromisoformat(a["fetched_at"])
                - datetime.fromisoformat(p["fetched_at"])
            ).total_seconds() / 60
            limit = tolerance(sigma, minutes, early(a))
            move = float(a["value"]) / float(p["value"]) - 1
            row["band"] = {
                "minutes": round(minutes, 2),
                "tolerance": round(limit, 6),
                "move": round(move, 6),
            }
            if abs(move) > limit:
                breaches.append(
                    f"O preço de {t} mudou {pct(move)}% desde a prévia (limite {pct(limit)}%)"
                )
        rows[t] = row
    return rows, breaches


def session_rows(session):
    """{ticker: official row} of the sessions in the base; empty = not published yet."""
    out = {}
    for ticker in base.TICKERS:
        rows = base.merged(ticker, session)
        if rows and rows[-1]["date"] == session:
            out[ticker] = rows[-1]
    return out


def price_of(row, field):
    return (
        b.dec(f"{row[field]:.2f}") if row and not row["conflict"] and row[field] else None
    )


def intraday_price(record, order):
    """First coherent traded 1m bar starting strictly after approval; never a last quote."""
    if (
        not record
        or record.get("day") != order["session"]
        or record.get("interval") != "1m"
    ):
        return None
    approved = datetime.fromisoformat(order["approved_at"])
    fetched = datetime.fromisoformat(record["fetched_at"])
    if approved.tzinfo is None or fetched.tzinfo is None:
        raise ValueError("intraday_timezone_required")
    if fetched > radar.now():
        raise ValueError("intraday_fetch_in_future")
    opening, _ = cutoffs(order["session"])
    start = opening + timedelta(minutes=15)
    end = start + timedelta(minutes=SESSION_MIN)
    previous = None
    for bar in record["bars"]:
        hour, minute = map(int, bar[0].split(":"))
        stamp = datetime.combine(
            date.fromisoformat(order["session"]), time(hour, minute), SP
        )
        if previous is not None and stamp <= previous:
            raise ValueError("intraday_times_not_increasing")
        previous = stamp
        if not (
            approved < stamp
            and start <= stamp < end
            and stamp + timedelta(minutes=1) <= fetched
        ):
            continue
        if len(bar) != 6 or any(v is None or not math.isfinite(v) for v in bar[1:]):
            continue
        if not stock.bar_close(bar) or bar[5] <= 0:
            continue
        return {
            "price": manual.number(f"{bar[1]:.2f}", "price", positive=True),
            "price_time": stamp.isoformat(),
            "fetched_at": fetched.isoformat(),
            "source": SOURCE,
            "basis": "YAHOO_1M_OPEN_AFTER_APPROVAL",
            "bar": bar,
            "payload_sha256": digest(record),
        }
    return None


def intraday_deadline(session):
    return cutoffs(session)[0] + timedelta(minutes=15 + SESSION_MIN + 30)


def intraday_capture(root, order, now):
    """Freeze all execution prices before the atomic ledger write, including on retries."""
    path = root / "execution-prices.json"
    record = read(path)
    tickers = sorted(t["ticker"] for t in order["basket"])
    if order.get("execution_policy") != INTRADAY_POLICY:
        raise ValueError("intraday_policy_mismatch")
    if record:
        if (
            record["identity"] != INTRADAY_POLICY
            or record["order_sha256"] != order["sha256"]
        ):
            raise ValueError("intraday_order_snapshot_mismatch")
        return record
    # ponytail: allow the delayed feed 30 minutes after continuous trading ends;
    # beyond that record a missed execution, never substitute a close/next-day price.
    if now >= intraday_deadline(order["session"]):
        return None
    payloads = delayed_bars(tickers, now, order["session"])
    prices = {t: intraday_price(payloads.get(t), order) for t in tickers}
    if not all(prices.values()):
        return None
    record = b.sealed(
        {
            "identity": INTRADAY_POLICY,
            "order_sha256": order["sha256"],
            "recorded_at": radar.now().isoformat(),
            "prices": prices,
            "payloads": payloads,
        }
    )
    radar.write(path, record, immutable=True)
    return record


def plan(order, wallet, rows, intraday=None):
    """TRADE requests at the selected execution price, with its recorded source.

    Sells first; if cash after the sells cannot pay the buys, every buy shrinks by the same
    factor in whole shares, then the largest buy loses one share at a time (ties: ticker)
    until it fits. Missing price = that leg is not executed; nothing is invented.
    """
    field, rate = (
        ("open" if order["leg"] in ("OPEN", "INTRADAY") else "close"),
        b.dec(order["cost_rate_pct"]),
    )
    side = {i["ticker"]: i["side"] for i in order["basket"]}
    ordered = {i["ticker"]: int(b.dec(i["quantity"])) for i in order["basket"]}
    price, missing = {}, []
    for t in ordered:
        row = rows.get(t)
        if value := price_of(row, field):
            price[t] = value
        else:
            reason = (
                "NO_OFFICIAL_PRICE"
                if row is None
                else "SOURCE_CONFLICT"
                if row["conflict"]
                else "ZERO_PRICE"
            )
            missing.append({"ticker": t, "reason": reason})
    gross = lambda t, q: b.money(q * price[t])  # noqa: E731
    fees = lambda t, q: b.money(gross(t, q) * rate / 100)  # noqa: E731
    qty = {t: ordered[t] for t in price}
    cash = b.dec(wallet["cash"]) + sum(
        (gross(t, q) - fees(t, q) for t, q in qty.items() if side[t] == "SELL"), b.ZERO
    )
    buys = [t for t in sorted(qty) if side[t] == "BUY"]
    cost = lambda: sum((gross(t, qty[t]) + fees(t, qty[t]) for t in buys), b.ZERO)  # noqa: E731
    if buys and cost() > cash:
        factor = max(cash, b.ZERO) / cost()
        for t in buys:
            qty[t] = int(qty[t] * factor)
        while cost() > cash and any(qty[t] for t in buys):
            qty[
                max((t for t in buys if qty[t]), key=lambda t: (gross(t, qty[t]), t))
            ] -= 1
    adjustments = [
        {
            "ticker": t,
            "ordered": str(ordered[t]),
            "executed": str(qty[t]),
            "reason": "INSUFFICIENT_CASH",
        }
        for t in buys
        if qty[t] != ordered[t]
    ]
    quote = lambda k, t: ((order["quotes"] or {}).get(k) or {}).get(t)  # noqa: E731
    source = {
        "kind": "WALLET_MANAGER_INTRADAY_EXECUTION" if intraday else KIND,
        "run": order["run"],
        "proposal": order["proposal"],
        "proposal_sha256": order["proposal_sha256"],
        "context_sha256": order["context_sha256"],
        "reference_session": order["reference_session"],
        "price_basis": "YAHOO_1M_OPEN_AFTER_APPROVAL"
        if intraday
        else "B3_OFFICIAL_RAW_" + ("OPEN_PREABE" if field == "open" else "CLOSE_PREULT"),
        "target_date": order["target_date"],
        "cost_rate_pct": order["cost_rate_pct"],
        "economic_date": order["session"],
        "leg": order["leg"],
        "approved_at": order["approved_at"],
        # The four prices of the TCC's implementation-shortfall measure.
        "prices": {
            t: {
                "decision": order["decision_prices"][t],
                "preview_quote": quote("preview", t),
                "approval_quote": quote("approval", t),
                **(
                    {"intraday": str(price[t]), **intraday["prices"][t]}
                    if intraday
                    else {
                        "auction": str(price[t]) if t in price else None,
                    }
                ),
            }
            for t in ordered
        },
        "adjustments": adjustments,
        "not_executed": missing,
        **(
            {
                "execution_snapshot_sha256": intraday["sha256"],
                "execution_policy": INTRADAY_POLICY,
            }
            if intraday
            else {}
        ),
    }
    requests = [
        {
            "kind": "TRADE",
            "wallet": order["wallet"]["id"],
            "trade": {
                "ticker": t,
                "side": side[t],
                "quantity": str(qty[t]),
                "price": str(price[t]),
                "costs": str(fees(t, qty[t])),
                "economic_date": order["session"],
            },
        }
        for want in ("SELL", "BUY")
        for t in sorted(qty)
        if side[t] == want and qty[t] > 0
    ]
    return requests, source


def ledger(wallet, sha):
    return [
        t
        for t in wallet["trades"]
        if (t.get("source") or {}).get("proposal_sha256") == sha
    ]


def conclude(root, order, status, now, **fields):
    record = b.sealed(
        {
            "identity": IDENTITY,
            "status": status,
            "run": order["run"],
            "proposal": order["proposal"],
            "proposal_sha256": order["proposal_sha256"],
            "wallet": order["wallet"]["id"],
            "session": order["session"],
            "leg": order["leg"],
            "executed_at": now.isoformat(),
            **fields,
        }
    )
    radar.write(root / "execution.json", record, immutable=True)
    return status


def settle_one(root, order, official, now):
    """Book one order once its recorded policy has eligible prices; return the new state."""
    session, sha, wid = order["session"], order["proposal_sha256"], order["wallet"]["id"]
    if session > now.date().isoformat():
        return "WAITING"
    captured = None
    if order["leg"] == "INTRADAY":
        captured = intraday_capture(root, order, now)
        if not captured:
            if now < intraday_deadline(session):
                return "WAITING"
            return conclude(
                root,
                order,
                "NOT_EXECUTED",
                now,
                reason="NO_POST_APPROVAL_INTRADAY_PRICE",
                trades=[],
                prices={},
                adjustments=[],
                not_executed=[
                    {"ticker": t["ticker"], "reason": "NO_POST_APPROVAL_INTRADAY_PRICE"}
                    for t in order["basket"]
                ],
            )
        rows = {
            t: {"open": float(q["price"]), "conflict": False}
            for t, q in captured["prices"].items()
        }
    elif not (rows := official(session)):
        return "WAITING"
    try:
        wallet = manual.get({"wallet": wid})["selected"]
        booked, token = (
            ledger(wallet, sha),
            None,
        )  # booked = a crash after the ledger write
        if not booked:
            requests, source = plan(order, wallet, rows, captured)
            if requests:
                token = manual.batch(wid, wallet["revision"], requests, source)[
                    "preview_token"
                ]
    except (
        manual.Invalid
    ) as e:  # accounting refusal at the official price: terminal, recorded
        return conclude(root, order, "ORDER_REJECTED", now, reason=str(e), field=e.field)
    if not booked and requests:
        wallet = manual.batch(
            wid, wallet["revision"], requests, source, confirm=True, token=token
        )["wallet"]
        booked = ledger(wallet, sha)
    source = booked[0]["source"] if booked else source
    ordered = {i["ticker"]: i["quantity"] for i in order["basket"]}
    return conclude(
        root,
        order,
        "EXECUTED" if booked else "NOT_EXECUTED",
        now,
        trades=[
            {
                **{
                    k: t[k]
                    for k in ("id", "ticker", "side", "quantity", "price", "costs")
                },
                "quantity_ordered": ordered[t["ticker"]],
            }
            for t in booked
        ],
        prices=source["prices"],
        adjustments=source["adjustments"],
        not_executed=source["not_executed"],
    )


def opportunity(root, rec, rows, now):
    """Cost-of-opportunity inputs of an expired proposal: decision price vs official close."""
    items = []
    for i in rec["basket"]:
        close = price_of(rows.get(i["ticker"]), "close")
        decision = b.dec(rec["decision_prices"][i["ticker"]])
        move = (
            (close - decision) * b.dec(i["quantity"]) * (1 if i["side"] == "BUY" else -1)
            if close
            else None
        )
        items.append(
            {
                **i,
                "decision_price": str(decision),
                "official_close": None if close is None else str(close),
                "move_vs_decision": None if move is None else str(b.money(move)),
            }
        )
    radar.write(
        root / "opportunity.json",
        b.sealed(
            {
                "identity": IDENTITY,
                "proposal_sha256": rec["proposal_sha256"],
                "session": rec["target_date"],
                "recorded_at": now.isoformat(),
                "items": items,
            }
        ),
        immutable=True,
    )


def settle_pending(now=None, *, intraday_only=False):
    """Book eligible orders; expire stale proposals. Isolate each broken proposal.

    Safe to repeat: every step is keyed by a record or by the ledger command of the
    proposal. A transient failure leaves the order pending for the next update.
    """
    out = {"settled": [], "waiting": [], "rejected": [], "expired": [], "errors": []}
    now, cache = now or radar.now(), {}

    def official(session):
        if session not in cache:
            cache[session] = session_rows(session)
        return cache[session]

    with LOCK:
        try:
            roots = list(folders())
        except Exception as e:
            out["errors"].append({"error": f"{type(e).__name__}: {e}"})
            return out
        for root in roots:
            try:
                order = read(root / "order.json")
                if intraday_only and (not order or order["leg"] != "INTRADAY"):
                    continue
                if order and not (root / "execution.json").exists():
                    state = settle_one(root, order, official, now)
                    key = {"WAITING": "waiting", "ORDER_REJECTED": "rejected"}.get(
                        state, "settled"
                    )
                    out[key].append(root.name)
                if order or not (root / "result.json").exists():
                    continue
                rec = read(root / "expired.json")
                if rec is None:
                    c, result = (
                        b.check_seal(radar.read(root / f))
                        for f in ("context.json", "result.json")
                    )
                    if (
                        result["status"] != "VALID_PROPOSAL"
                        or not result["trades"]
                        or not appliable(c)
                        or not expired(c["target_date"], now)
                    ):
                        continue
                    try:  # booked under the old rule (reference price on approval): not expired
                        wallet = manual.get({"wallet": c["wallet"]["id"]})["selected"]
                    except manual.Invalid:  # wallet gone: nothing can be booked anyway
                        continue
                    if ledger(wallet, result["sha256"]):
                        continue
                    rec = expire(root, c, result, now)
                    out["expired"].append(root.name)
                if (
                    rec["target_date"] <= now.date().isoformat()
                    and not (root / "opportunity.json").exists()
                ):
                    if rows := official(rec["target_date"]):
                        opportunity(root, rec, rows, now)
            except Exception as e:  # one broken folder never blocks the others
                out["errors"].append(
                    {"proposal": root.name, "error": f"{type(e).__name__}: {e}"}
                )
    return out


def start():
    """DP-35: pending intraday orders advance even without an open browser/market update."""

    def loop():
        pause = threading.Event()
        while True:
            try:
                result = settle_pending(intraday_only=True)
                if result["errors"]:
                    logging.getLogger(__name__).warning("DP-35: %s", result["errors"])
            except Exception:
                logging.getLogger(__name__).exception("DP-35 processamento intradiário")
            pause.wait(60)

    worker = threading.Thread(target=loop, name="hfl-intraday-execution", daemon=True)
    worker.start()
    return worker
