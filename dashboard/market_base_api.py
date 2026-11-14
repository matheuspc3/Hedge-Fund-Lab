"""DP-27 local market base: official B3 COTAHIST rows of the 5 assets, kept forever.

Annual files since 2000 once, then daily files for missing sessions. Only the
asset rows are stored (ZIP discarded) with URL, sha256, size and acquisition
instant (raw_sha256: "sha256" is the seal), one immutable sealed JSON per source file: b3/<FILE_NAME>.json.
"""

import hashlib
import io
import os
import zipfile
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from threading import Lock, Thread
from urllib import error, request

import manual_portfolio_api as manual
import radar_runs as runs
import stock_history_api as stock

from src.backtesting.b3_calendar import B3Calendar
from src.pipeline.b3_official import COTAHIST_URL

b, radar = manual.b, runs.radar
ROOT = Path(
    os.environ.get(
        "HFL_MARKET_BASE_ROOT", manual.PROJECT / "data/platform/market-base-v1"
    )
)
IDENTITY = "HFL-MARKET-BASE-B3-V1"
PARSER = "HFL-COTAHIST-ONEPASS-V1"
TICKERS = radar.EXAMPLES  # PETR4, VALE3, ITUB4, WEGE3, BBAS3
FIRST_YEAR = 2000
MAX_BYTES = 512 * 1024 * 1024  # downloaded ZIP (2026 annual is ~95 MB)
# Annual text members reach several hundred MB; parsing streams, so this only
# guards against a zip bomb.
MAX_MEMBER = 2 * 1024 * 1024 * 1024
# Old B3 code -> (current code, last session of the old code): Lucas, 17/10, normalize
# to today's ticker. ITAU4 -> ITUB4 (2009-05-20) is a plain rename: no overlap, +1.97%.
# WEGE4 -> WEGE3 (DP-29 option B): the old code is the series up to 2007-05-31.
ALIASES = {"ITAU4": ("ITUB4", "2009-05-19"), "WEGE4": ("WEGE3", "2007-05-31")}
# Native rows of a current code before this date are dropped at read time in merged()
# (stored records stay untouched): WEGE3 before 2007-06-01 was the thin ordinary class
# trading beside WEGE4 (616 no-trade sessions, 61 overlapping dates), DP-29.
EXCLUDE_BEFORE = {"WEGE3": "2007-06-01"}
FIELDS = ("open", "high", "low", "close", "volume")
UPDATE_LOCK = Lock()
USER_AGENT = "HedgeFundLab/1.0 (uso local; TCC)"
JOB_LOCK = Lock()


class _B3Agent(request.BaseHandler):
    """Project user-agent on B3 requests only (B3 answers 403 to "Python-urllib")."""

    def https_request(self, req):
        if (req.host or "").endswith("bmfbovespa.com.br"):
            req.add_unredirected_header("User-Agent", USER_AGENT)
        return req

    http_request = https_request


def install_b3_user_agent():
    # The sealed src/pipeline/b3_official.py (Radar preparation) calls urlopen with
    # the default agent; a process-wide opener fixes it without editing that module.
    request.install_opener(request.build_opener(_B3Agent))


def fetch_http(url):
    """Bytes, or None when B3 has not published the file (HTTP 404)."""
    try:
        # B3 refuses the default "Python-urllib" agent (403); identify the project honestly.
        req = request.Request(url, headers={"User-Agent": USER_AGENT})
        with request.urlopen(req, timeout=600) as response:
            return response.read(MAX_BYTES + 1)
    except error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def parse(raw, symbols=TICKERS):
    """One pass over a COTAHIST ZIP -> ({symbol: rows}, every record date seen).

    Same filters and OHLC/volume offsets as b3_official.read_cotahist (record 01,
    TPMERC 010, CODBDI 02). Extra fields use the B3 layout (0-based slices of the
    245-byte record): PREMED 95:108, TOTNEG 147:152, VOLTOT 170:188 (cents), next to
    QUATOT 152:170 that read_cotahist reports as volume.
    """
    rows, seen = {s: [] for s in symbols}, set()
    names = {s: s for s in symbols} | {o: n for o, (n, _) in ALIASES.items() if n in rows}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].file_size > MAX_MEMBER:
            raise ValueError("single_bounded_cotahist_member_required")
        with archive.open(members[0]) as handle:
            for line in io.TextIOWrapper(handle, encoding="latin-1"):
                if line[:2] != "01":
                    continue
                day = f"{line[2:6]}-{line[6:8]}-{line[8:10]}"
                seen.add(day)
                symbol = line[12:24].strip()
                if line[24:27] != "010" or line[10:12] != "02" or symbol not in names:
                    continue
                rows[names[symbol]].append(
                    {
                        **({"source_symbol": symbol} if symbol in ALIASES else {}),
                        "date": day,
                        "open": int(line[56:69]) / 100,
                        "high": int(line[69:82]) / 100,
                        "low": int(line[82:95]) / 100,
                        "close": int(line[108:121]) / 100,
                        "avg": int(line[95:108]) / 100,
                        "volume": float(int(line[152:170])),
                        "trades": int(line[147:152]),
                        "financial": int(line[170:188]) / 100,
                    }
                )
    return rows, seen


def target(kind, key):
    """Plan item: annual year (int), daily session (date) or (year, old code) alias supplement."""
    alias = kind == "annual-alias"
    year = key[0] if alias else key
    name = f"COTAHIST_A{year}.ZIP" if kind != "daily" else f"COTAHIST_D{key:%d%m%Y}.ZIP"
    url = COTAHIST_URL.replace("COTAHIST_A{year}.ZIP", name)
    # supplement = the same ZIP re-read for one old code, stored as <annual>+<code>
    return {
        "file": f"{name}+{key[1]}" if alias else name,
        "kind": kind,
        "key": key,
        "url": url,
    }


@lru_cache(maxsize=4)
def _verified(root, stamps):
    files = []
    for name, _, _ in stamps:
        record = b.check_seal(radar.read(Path(root) / "b3" / name))
        if record["identity"] != IDENTITY or record["file_name"] + ".json" != name:
            raise ValueError("market_base_identity_mismatch")
        files.append(record)
    return files


def acquired():
    """Every verified source file on disk (re-verified only when a file changes)."""
    stamps = tuple(
        (p.name, (st := p.stat()).st_size, st.st_mtime_ns)
        for p in sorted((ROOT / "b3").glob("*.json"))
    )
    # ponytail: size+mtime_ns detect rewrites; files are immutable once written.
    return list(_verified(str(ROOT), stamps))


def published():
    """Last session B3 already published into this base (ISO), or None when empty.

    A session's COTAHIST arrives hours after its 18:00 close (night or next morning):
    until then the calendar's last closed session is an explicit gap (DP-27).
    """
    return max((f.get("session") or f["through"] for f in acquired()), default=None)


def plan(closed, have=None):
    """Files still missing up to the `closed` session (ISO date string)."""
    have = acquired() if have is None else have
    end = date.fromisoformat(closed)
    this_year = B3Calendar().sessions_between(date(end.year, 1, 1), end)
    years = {f["year"] for f in have if f["kind"] == "annual"}
    covered = {f["session"] for f in have if f["kind"] == "daily"}
    for f in have:
        if f["kind"] == "annual" and f["year"] == end.year:
            covered |= {str(d) for d in this_year if str(d) <= f["through"]}
    items = [target("annual", y) for y in range(FIRST_YEAR, end.year) if y not in years]
    missing = [d for d in this_year if str(d) not in covered]
    # ponytail: ~10 sessions is the break-even between one annual and many daily
    # requests; a 404 daily is not remembered and is retried on every update.
    # Annual records written before an alias existed lack its rows: one supplement
    # per (file, old code), while the old code could still trade that year.
    done = {(f["year"], a) for f in have if "year" in f for a in f.get("aliases", [])}
    items += [
        target("annual-alias", (y, a))
        for y in sorted(years)
        for a in ALIASES
        if y <= int(ALIASES[a][1][:4]) and (y, a) not in done
    ]
    if end.year not in years and len(missing) > 10:
        return [*items, target("annual", end.year)]
    return [*items, *(target("daily", d) for d in missing)]


def acquire(item, fetch):
    """Fetch, verify, reduce and store one file. Returns the record, None if 404."""
    raw = fetch(item["url"])
    if raw is None:
        return None
    if len(raw) > MAX_BYTES:
        raise ValueError("cotahist_file_too_large")
    rows, seen = parse(raw)
    if not seen:
        raise ValueError("cotahist_without_records")
    alias = item["kind"] == "annual-alias"
    if alias:  # only the rows that came from that old code
        rows = {
            t: [r for r in v if r.get("source_symbol") == item["key"][1]]
            for t, v in rows.items()
        }
    record = {
        "identity": IDENTITY,
        "url": item["url"],
        "file_name": item["file"],
        "kind": item["kind"],
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "acquired_at": radar.now().isoformat(),
        "parser": PARSER,
        "rows": rows,
    }
    if item["kind"] in ("annual", "annual-alias"):
        year = item["key"][0] if alias else item["key"]
        if {d[:4] for d in seen} != {str(year)}:
            raise ValueError("annual_file_year_mismatch")
        record |= {
            "year": year,
            "through": max(seen),
            "aliases": [item["key"][1]] if alias else sorted(ALIASES),
        }
    else:
        if seen != {str(item["key"])}:
            raise ValueError("daily_file_session_mismatch")
        record["session"] = str(item["key"])
    radar.write(ROOT / "b3" / (item["file"] + ".json"), b.sealed(record), immutable=True)
    return record


def update(fetch=None, closed=None):
    fetch = fetch or fetch_http
    if not UPDATE_LOCK.acquire(blocking=False):
        raise ValueError("market_base_update_already_running")
    try:
        closed = closed or radar.last_closed(radar.now())
        results, tried = [], set()
        # Round 2 exists only because a new annual file changes which sessions
        # remain for daily files.
        for _ in range(2):
            todo = [i for i in plan(closed) if i["file"] not in tried]
            for item in todo:
                tried.add(item["file"])
                try:
                    stored = acquire(item, fetch)
                    status, err = ("ACQUIRED" if stored else "NOT_PUBLISHED"), None
                except Exception as e:  # one bad file never aborts the run
                    status, err = "FAILED", f"{type(e).__name__}: {e}"
                results.append({"file": item["file"], "status": status, "error": err})
            if not any(i["kind"] == "annual" for i in todo):
                break
        return {"closed": closed, "results": results}
    finally:
        UPDATE_LOCK.release()


def merged(ticker, as_of=None):
    """Rows of sessions <= as_of (ISO date); disagreement between files is a conflict.

    as_of is the decision's data session: a B3 close is public after that session,
    so later rows are never visible. acquired_at only audits when we stored it.
    """
    seen = {}
    for f in acquired():
        for row in f["rows"].get(ticker, []):
            if as_of and row["date"] > as_of[:10]:
                continue
            if (
                row["date"] < EXCLUDE_BEFORE.get(ticker, "")
                and "source_symbol" not in row
            ):
                continue
            seen.setdefault(row["date"], []).append((f["acquired_at"], row))
    out = []
    for day in sorted(seen):
        versions = seen[day]
        agree = len({tuple(r[k] for k in FIELDS) for _, r in versions}) == 1
        first = min(versions, key=lambda v: datetime.fromisoformat(v[0]))
        row = dict(first[1]) if agree else {k: None for k in first[1]}
        out.append({**row, "date": day, "acquired_at": first[0], "conflict": not agree})
    return out


def series(ticker, as_of=None):
    snapshot = stock.load(ticker)
    factors = {
        r["date"]: r["adjusted_close"] / r["close"]
        for r in (snapshot or {}).get("rows", [])
        if r["close"] and r["adjusted_close"]
    }
    rows = []
    for row in merged(ticker, as_of):
        factor, raw = factors.get(row["date"]), row["close"]
        rows.append(
            {
                **row,
                "factor": factor,
                "adjusted_close": raw * factor if raw and factor else None,
            }
        )
    # ponytail: the factor comes from the latest Yahoo snapshot, not as-of (Yahoo
    # rewrites history on each dividend); upgrade: pick the snapshot fetched <= as_of.
    return {
        "ticker": ticker,
        "factor_source": snapshot
        and {"sha256": snapshot["sha256"], "fetched_at": snapshot["fetched_at"]},
        "rows": rows,
    }


def coverage():
    result = {}
    for ticker in TICKERS:
        rows = merged(ticker)
        if not rows:
            result[ticker] = None
            continue
        first, last = rows[0]["date"], rows[-1]["date"]
        have = {r["date"] for r in rows}
        sessions = B3Calendar().sessions_between(
            date.fromisoformat(first), date.fromisoformat(last)
        )
        result[ticker] = {
            "first": first,
            "last": last,
            "rows": len(rows),
            "conflicts": sum(r["conflict"] for r in rows),
            "gaps": sum(str(d) not in have for d in sessions),
        }
    return result


JOB = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "last": None,
    "error": None,
}


def _run(fetch):
    try:
        last = update(fetch)
        yahoo = {}
        with stock.REFRESH_LOCK:  # never alongside the explorer's own refresh
            for ticker in (
                *TICKERS,
                "IBOV",
            ):  # Yahoo: adjustment factor (series) + DP-28 index
                try:
                    # Each download is a new ~1 MB snapshot: skip when already current.
                    rows = (stock.load(ticker) or {}).get("rows", [])
                    if (
                        max((r["date"] for r in rows if r["close"]), default="")
                        < last["closed"]
                    ):
                        stock.download(ticker, last["closed"])
                    yahoo[ticker] = "OK"
                except Exception as e:
                    yahoo[ticker] = f"{type(e).__name__}: {e}"
            try:  # when Yahoo fills the session's volume (the Radar prepare waits for it)
                volume = stock.consolidation(last["closed"], TICKERS)
            except Exception as e:
                volume = f"{type(e).__name__}: {e}"
        import reference_rates_api as rates  # circular: it needs this module's ROOT

        try:  # DP-28 CDI: same fetcher contract (url -> bytes); never aborts the rest
            rates.update(last["closed"], fetch)
            cdi = "OK"
        except Exception as e:
            cdi = f"{type(e).__name__}: {e}"
        import dividends_api  # circular, like reference_rates_api

        try:  # DP-30 B3 cash dividends; per-ticker failures stay inside the result
            divs = dividends_api.update(fetch)
        except Exception as e:
            divs = f"{type(e).__name__}: {e}"
        import rule_portfolios  # decisions/operations use only the freshly stored data

        try:
            rules = rule_portfolios.advance()
        except Exception as e:
            rules = f"{type(e).__name__}: {e}"
        try:  # DP-30 A: received dividends go to the ledger; errors never abort the job
            booked = dividends_api.book_received(radar.now().date().isoformat())
        except Exception as e:
            booked = f"{type(e).__name__}: {e}"
        import auction_orders  # circular: it reads this module's merged()

        try:  # DP-33: approved orders whose auction price just arrived; never aborts the job
            orders = auction_orders.settle_pending()
        except Exception as e:
            orders = f"{type(e).__name__}: {e}"
        JOB["last"] = {
            **last,
            "yahoo": yahoo,
            "yahoo_volume": volume,
            "cdi": cdi,
            "dividends": divs,
            "rule_portfolios": rules,
            "dividends_booked": booked,
            "orders": orders,
        }
        JOB["error"] = None
    except Exception as e:
        JOB["error"] = f"{type(e).__name__}: {e}"
    finally:
        JOB["finished_at"] = radar.now().isoformat()
        JOB["running"] = False


def start(fetch=None):
    """Background update; a second call while running just reports the status."""
    with JOB_LOCK:
        if not JOB["running"]:
            JOB.update(running=True, started_at=radar.now().isoformat(), error=None)
            Thread(target=_run, args=(fetch,), daemon=True).start()
    return status()


def status():
    return {
        **JOB,
        "closed": radar.last_closed(radar.now()),
        "coverage": coverage(),
    }


def benchmark(since):
    """DP-28 Ibovespa closes for the Comparison page: read-only, local snapshot only.

    The wallets entered on the previous session's closes (DP-20), so the anchor is
    the last close strictly before `since`.
    """
    manual.day(since, "since")
    snap = stock.load("IBOV")
    closed = radar.last_closed(radar.now())
    rows = [
        {"date": r["date"], "close": r["close"]}
        for r in (snap or {}).get("rows", [])
        if r["close"] and r["date"] <= closed
    ]
    before = [r for r in rows if r["date"] < since]
    anchor = before[-1] if before else None
    import reference_rates_api as rates

    try:
        stored = rates.daily()
        start = (anchor and anchor["date"]) or max(
            (d for d in stored if d < since), default=None
        )
        ref = rates.cdi(start, closed, stored) if start else None
        cdi = {
            "provider": rates.PROVIDER,
            "anchor": start,
            "rows": ref["rows"] if ref and len(ref["rows"]) > 1 else [],
            "acquired_at": ref and ref["acquired_at"],
        }
    except ValueError as e:  # e.g. cdi_conflict:<date>: no series rather than a guess
        cdi = {"provider": rates.PROVIDER, "anchor": None, "rows": [], "error": str(e)}
    return {
        "symbol": "IBOV",
        "provider_symbol": "^BVSP",
        "provider": "Yahoo Finance via yfinance",
        "fetched_at": snap and snap["fetched_at"],
        "snapshot": snap and snap["sha256"],
        "classification": "EXTERNAL_REFERENCE_INDEX_NOT_PORTFOLIO_MARKS",
        "anchor": anchor and anchor["date"],
        "anchor_note": None
        if anchor
        else "Sem fechamento anterior a since; a série começa em since.",
        "rows": ([anchor] if anchor else []) + [r for r in rows if r["date"] >= since],
        "cdi": cdi,
    }
