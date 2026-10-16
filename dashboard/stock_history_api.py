"""APP-03 stock explorer: explicit Yahoo refresh, immutable local copies, no ledger writes.

DP-26 adds an intraday archive: each closed session keeps the finest Yahoo bars
still available (1m/5m/1h), written once; the open session stays in memory.
"""

import hashlib
import math
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from pathlib import Path
from threading import Lock

import manual_portfolio_api as manual
import pandas as pd
import radar_runs as runs
import yfinance as yf

from src.backtesting.b3_calendar import B3Calendar
from src.pipeline.extract import DataExtractor
from src.pipeline.transform import DataQualityError, validate_ohlcv

b, radar = manual.b, runs.radar
ROOT = Path(
    os.environ.get(
        "HFL_STOCK_HISTORY_ROOT", manual.PROJECT / "data/platform/stock-history-v1"
    )
)
IDENTITY = "HFL-STOCK-EXPLORER-YAHOO-V1"
REFRESH_LOCK = Lock()


def tickers(wallet_id):
    wallet = manual.get({"wallet": wallet_id})["selected"]
    symbols = sorted(
        {t["ticker"] for t in wallet["trades"]}
        | {p["ticker"] for p in wallet["positions"]}
    )
    if len(symbols) > 20:
        raise ValueError("stock_history_maximum_20_assets")
    return [b.ticker(t) for t in symbols]


def load(ticker):
    folder = ROOT / b.ticker(ticker)
    if not (folder / "latest.json").exists():
        return None
    pointer = b.check_seal(radar.read(folder / "latest.json"))
    key = pointer["snapshot"]
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
        raise ValueError("invalid_stock_snapshot")
    result = b.check_seal(radar.read(folder / (key + ".json")))
    if (
        result["sha256"] != key
        or result["ticker"] != ticker
        or result["identity"] != IDENTITY
    ):
        raise ValueError("stock_snapshot_identity_mismatch")
    raw_sha = result["raw_sha256"]
    if not isinstance(raw_sha, str) or not re.fullmatch(r"[a-f0-9]{64}", raw_sha):
        raise ValueError("invalid_stock_raw_hash")
    if radar.sha_file(folder / (raw_sha + ".csv")) != raw_sha:
        raise ValueError("stock_raw_hash_mismatch")
    return result


def prepare(ticker, frame, closed, fetched_at):
    if frame is None or frame.empty or len(frame) > 50000:
        raise ValueError("empty_or_oversized_yahoo_history")
    raw = frame.to_csv().encode("utf-8")
    frame = frame.copy()
    index = pd.DatetimeIndex(frame.index)
    if index.tz is not None:
        index = index.tz_convert("America/Sao_Paulo").tz_localize(None)
    frame.index = index.normalize()
    if (
        frame.index.hasnans
        or frame.index.has_duplicates
        or not frame.index.is_monotonic_increasing
    ):
        raise ValueError("invalid_yahoo_dates")
    frame = frame.loc[(frame.index >= "1900-01-01") & (frame.index <= closed)]
    normalized = DataExtractor._normalize_columns(frame.copy())
    complete = normalized.notna().all(axis=1)

    def check(block):
        try:
            validate_ohlcv(block)
        except DataQualityError:
            if len(block) == 1:
                complete.loc[block.index[0]] = False
            else:
                # Reuse the validator; bisection avoids validating every good row.
                middle = len(block) // 2
                check(block.iloc[:middle])
                check(block.iloc[middle:])

    check(normalized.loc[complete])
    if not complete.any():
        raise ValueError("no_complete_yahoo_bars")

    def value(row, column):
        v = row.get(column)
        return (
            float(v) if pd.notna(v) and math.isfinite(float(v)) and float(v) > 0 else None
        )

    rows = [
        {
            "date": stamp.date().isoformat(),
            "close": value(row, "Close") if complete.loc[stamp] else None,
            "adjusted_close": value(row, "Adj Close") if complete.loc[stamp] else None,
        }
        for stamp, row in frame.iterrows()
    ]
    snapshot = b.sealed(
        {
            "identity": IDENTITY,
            "ticker": ticker,
            "symbol": ticker + ".SA",
            "provider": "Yahoo Finance via yfinance",
            "yfinance_version": yf.__version__,
            "fetched_at": fetched_at,
            "requested_period": "max",
            "interval": "1d",
            "auto_adjust": False,
            "repair": False,
            "through": closed,
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "rows": rows,
            "missing_bars": int((~complete).sum()),
            "classification": "EXPLORATION_ONLY_NOT_PORTFOLIO_MARKS",
        }
    )
    return snapshot, raw


def download(ticker, closed):
    end = (date.fromisoformat(closed) + timedelta(days=1)).isoformat()
    frame = yf.Ticker(ticker + ".SA").history(
        period="max",
        interval="1d",
        end=end,
        auto_adjust=False,
        back_adjust=False,
        repair=False,
        actions=True,
        keepna=True,
        timeout=12,
        raise_errors=True,
    )
    snapshot, raw = prepare(ticker, frame, closed, radar.now().isoformat())
    folder = ROOT / ticker
    # Reuse the existing fsync/atomic publisher. Only the latest pointer is mutable.
    radar.write(folder / (snapshot["raw_sha256"] + ".csv"), raw, immutable=True)
    radar.write(folder / (snapshot["sha256"] + ".json"), snapshot, immutable=True)
    radar.write(folder / "latest.json", b.sealed({"snapshot": snapshot["sha256"]}))
    return ticker


def get(query):
    manual.fields(query, ("wallet",))
    series, errors = {}, {}
    closed = radar.last_closed(radar.now())
    for ticker in tickers(query["wallet"]):
        try:
            snapshot = load(ticker)
            if snapshot:
                series[ticker] = {
                    **snapshot,
                    "rows": [r for r in snapshot["rows"] if r["date"] <= closed],
                }
            else:
                errors[ticker] = "Histórico ainda não baixado."
        except (ValueError, KeyError, TypeError, OSError):
            errors[ticker] = (
                "A cópia local não passou na verificação; atualize o histórico."
            )
    return {
        "identity": IDENTITY,
        "wallet": query["wallet"],
        "tickers": tickers(query["wallet"]),
        "series": series,
        "errors": errors,
        "read_only": True,
        "last_closed": closed,
        "today": session_today(radar.now()),
    }


def refresh(payload):
    manual.fields(payload, ("wallet",))
    symbols = tickers(payload["wallet"])
    if not REFRESH_LOCK.acquire(blocking=False):
        raise ValueError("stock_history_refresh_already_running")
    errors = {}
    try:
        closed = radar.last_closed(radar.now())
        # ponytail: three bounded requests, no scheduler/retry. For larger universes
        # move this explicit refresh to the existing job runner.
        with ThreadPoolExecutor(max_workers=3) as pool:
            pending = {
                ticker: pool.submit(download, ticker, closed) for ticker in symbols
            }
            for ticker, future in pending.items():
                try:
                    future.result()
                except Exception:
                    errors[ticker] = (
                        "Yahoo indisponível ou histórico inválido; a cópia anterior foi preservada."
                    )
        return {**get(payload), "refresh_errors": errors}
    finally:
        REFRESH_LOCK.release()


INTRADAY_IDENTITY = "HFL-STOCK-INTRADAY-YAHOO-V1"
STEPS = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
# ponytail: Yahoo retention measured on 16/10/2026: 1m ~30 days (7 per request),
# 5m 60 days, 1h 730 days. Each missing day is asked once per tier per process;
# if Yahoo changes these limits, only this table changes.
TIERS = (("1m", 29, 7), ("5m", 59, 59), ("1h", 729, 729))
LIVE, ATTEMPTED = {}, set()
INTRADAY_LOCK = Lock()


def session_today(now):
    """Open session date once its first delayed (~15 min) bars can exist."""
    today = now.date()
    if str(today) > radar.last_closed(now) and B3Calendar().is_session(today):
        return str(today) if now.time() >= time(10, 15) else None
    return None


def intraday_path(ticker, day, interval):
    return ROOT / ticker / "intraday" / day / (interval + ".json")


def intraday_bars(frame):
    """Yahoo frame -> {day: [[HH:MM, open, high, low, close, volume]]}, as returned."""
    if frame is None or len(frame) > 50000:
        raise ValueError("oversized_yahoo_intraday")
    if frame.empty:
        return {}
    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        raise ValueError("yahoo_intraday_without_timezone")
    index = index.tz_convert("America/Sao_Paulo")
    if index.has_duplicates or not index.is_monotonic_increasing:
        raise ValueError("invalid_yahoo_intraday_times")
    columns = frame.reindex(columns=["Open", "High", "Low", "Close", "Volume"])
    days = {}
    for stamp, values in zip(index, columns.itertuples(index=False)):
        days.setdefault(stamp.date().isoformat(), []).append(
            [stamp.strftime("%H:%M")]
            + [float(v) if pd.notna(v) and math.isfinite(v) else None for v in values]
        )
    return days


def bar_close(bar):
    """Close of a coherent bar, else None: gaps are shown, never repaired."""
    _, o, h, low, c, _ = bar
    if any(v is None or v <= 0 for v in (o, h, low, c)):
        return None
    return c if low <= min(o, c) and h >= max(o, c) else None


def collect(ticker, now):
    """Archive every missing closed session at the finest tier Yahoo still has."""
    today, closed = now.date(), radar.last_closed(now)
    live = session_today(now)
    have = {p.parent.name for p in (ROOT / ticker / "intraday").glob("*/*.json")}
    sessions = B3Calendar().sessions_between(today - timedelta(729), today)
    failures, finer = 0, None
    for interval, age, span in TIERS:
        # A coarser tier only takes a day the finer tier no longer covers or
        # already asked for without bars; a failed finer request is retried.
        want = [
            d
            for d in sessions
            if d >= today - timedelta(age)
            and str(d) <= closed
            and str(d) not in have
            and (ticker, interval, d) not in ATTEMPTED
            and (
                finer is None
                or d < today - timedelta(finer[1])
                or (ticker, finer[0], d) in ATTEMPTED
            )
        ]
        finer = (interval, age)
        last = today if interval == "1m" and live else (want[-1] if want else None)
        start = want[0] if want else last
        while start is not None and start <= last:
            end = min(start + timedelta(span), last + timedelta(1))
            try:
                days = intraday_bars(
                    yf.Ticker(ticker + ".SA").history(
                        interval=interval,
                        start=start.isoformat(),
                        end=end.isoformat(),
                        auto_adjust=False,
                        back_adjust=False,
                        repair=False,
                        actions=False,
                        keepna=True,
                        timeout=12,
                        raise_errors=True,
                    )
                )
            except Exception:
                # A failed window is retried on the next refresh; nothing is written.
                failures += 1
                start = end
                continue
            fetched_at = radar.now().isoformat()
            for d in (d for d in want if start <= d < end):
                ATTEMPTED.add((ticker, interval, d))
                if days.get(str(d)):
                    radar.write(
                        intraday_path(ticker, str(d), interval),
                        b.sealed(
                            {
                                "identity": INTRADAY_IDENTITY,
                                "ticker": ticker,
                                "symbol": ticker + ".SA",
                                "day": str(d),
                                "interval": interval,
                                "provider": "Yahoo Finance via yfinance",
                                "yfinance_version": yf.__version__,
                                "fetched_at": fetched_at,
                                "auto_adjust": False,
                                "repair": False,
                                "columns": [
                                    "time",
                                    "open",
                                    "high",
                                    "low",
                                    "close",
                                    "volume",
                                ],
                                "bars": days[str(d)],
                                "classification": "EXPLORATION_ONLY_NOT_PORTFOLIO_MARKS",
                            }
                        ),
                        immutable=True,
                    )
                    have.add(str(d))
            if interval == "1m" and live and start <= today < end:
                LIVE[ticker] = {
                    "day": live,
                    "interval": "1m",
                    "fetched_at": fetched_at,
                    "bars": days.get(live, []),
                }
            start = end
    return failures


def load_day(ticker, day):
    for interval in ("1m", "5m", "1h"):
        path = intraday_path(ticker, day, interval)
        if path.exists():
            record = b.check_seal(radar.read(path))
            if (
                record["identity"],
                record["ticker"],
                record["day"],
                record["interval"],
            ) != (
                INTRADAY_IDENTITY,
                ticker,
                day,
                interval,
            ):
                raise ValueError("stock_intraday_identity_mismatch")
            return record
    return None


def resample(day, bars, step):
    """Last valid close per bucket of `step` minutes; a bucket without one is a gap.

    All-empty bars are auction minutes without trades (10:00-10:04, 16:55-16:59
    observed); they are kept in the archive but are not gaps on the chart.
    """
    out = {}
    for bar in bars:
        if all(v is None for v in bar[1:5]):
            continue
        hour, minute = map(int, bar[0].split(":"))
        bucket = (hour * 60 + minute) // step * step
        key = f"{day} {bucket // 60:02d}:{bucket % 60:02d}"
        close = bar_close(bar)
        out[key] = close if close is not None else out.get(key)
    return [[k, v] for k, v in out.items()]


def get_intraday(query):
    manual.fields(query, ("wallet", "from", "to", "interval"))
    if query["interval"] not in STEPS:
        raise ValueError("invalid_intraday_interval")
    days = B3Calendar().sessions_between(
        date.fromisoformat(query["from"]), date.fromisoformat(query["to"])
    )
    if len(days) > 60:
        raise ValueError("intraday_maximum_60_sessions")
    today = session_today(radar.now())
    series, errors, live = {}, {}, {}
    for ticker in tickers(query["wallet"]):
        try:
            rows, resolution = [], {}
            for day in map(str, days):
                record = LIVE.get(ticker) if day == today else load_day(ticker, day)
                if not record or record["day"] != day:
                    continue
                resolution[day] = record["interval"]
                step = max(STEPS[query["interval"]], STEPS[record["interval"]])
                rows += resample(day, record["bars"], step)
                if day == today:
                    live[ticker] = {
                        "fetched_at": record["fetched_at"],
                        "last_bar": record["bars"][-1][0] if record["bars"] else None,
                    }
            series[ticker] = {"rows": rows, "resolution": resolution}
        except (ValueError, KeyError, TypeError, OSError):
            errors[ticker] = "A cópia intradiária local não passou na verificação."
    return {
        "identity": INTRADAY_IDENTITY,
        "wallet": query["wallet"],
        "from": query["from"],
        "to": query["to"],
        "interval": query["interval"],
        "today": today,
        "series": series,
        "live": live,
        "errors": errors,
        "read_only": True,
    }


def refresh_intraday(payload):
    manual.fields(payload, ("wallet",))
    symbols = tickers(payload["wallet"])
    if not INTRADAY_LOCK.acquire(blocking=False):
        raise ValueError("stock_intraday_refresh_already_running")
    errors = {}
    try:
        now = radar.now()
        with ThreadPoolExecutor(max_workers=3) as pool:
            pending = {ticker: pool.submit(collect, ticker, now) for ticker in symbols}
            for ticker, future in pending.items():
                try:
                    if future.result():
                        errors[ticker] = (
                            "Parte das barras intradiárias não veio do Yahoo; tente de novo."
                        )
                except Exception:
                    errors[ticker] = (
                        "Yahoo indisponível ou barras inválidas; o acervo foi preservado."
                    )
        return {
            "identity": INTRADAY_IDENTITY,
            "wallet": payload["wallet"],
            "refresh_errors": errors,
        }
    finally:
        INTRADAY_LOCK.release()
