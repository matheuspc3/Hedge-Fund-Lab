"""Stock exploration stays independent from the ledger and preserves every refresh."""

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "dashboard"), str(PROJECT / "scripts"), str(PROJECT)]
import stock_history_api as h  # noqa: E402


@pytest.fixture
def history(tmp_path, monkeypatch):
    monkeypatch.setattr(h, "ROOT", tmp_path / "history")
    monkeypatch.setattr(h, "tickers", lambda wallet: ["PETR4"])
    monkeypatch.setattr(h.radar, "now", lambda: pd.Timestamp("2026-10-15T12:00:00-03:00"))
    frame = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0],
            "High": [12.0, 13.0, 14.0],
            "Low": [9.0, 10.0, 11.0],
            "Close": [11.0, 12.0, 13.0],
            "Volume": [100.0, 200.0, 300.0],
            "Adj Close": [5.0, 6.0, 7.0],
            "Dividends": [0.0, 1.0, 0.0],
        },
        index=pd.DatetimeIndex(
            ["2000-01-03", "2026-10-14", "2026-10-15"], tz="America/Sao_Paulo"
        ),
    )
    calls = []

    class Ticker:
        def history(self, **kwargs):
            calls.append(kwargs)
            return frame.copy()

    monkeypatch.setattr(h.yf, "Ticker", lambda symbol: Ticker())
    return frame, calls


def test_max_daily_explicit_adjustments_cutoff_and_read_only_cache(history):
    _, calls = history
    result = h.refresh({"wallet": "wallet"})
    s = result["series"]["PETR4"]
    assert [r["date"] for r in s["rows"]] == ["2000-01-03", "2026-10-14"]
    assert s["rows"][0] == {"date": "2000-01-03", "close": 11.0, "adjusted_close": 5.0}
    assert calls[0]["period"] == "max" and calls[0]["interval"] == "1d"
    assert calls[0]["end"] == "2026-10-15"
    assert calls[0]["auto_adjust"] is False and calls[0]["repair"] is False
    before = {str(p): p.read_bytes() for p in h.ROOT.rglob("*") if p.is_file()}
    assert h.get({"wallet": "wallet"})["series"] == result["series"]
    assert len(calls) == 1
    assert before == {str(p): p.read_bytes() for p in h.ROOT.rglob("*") if p.is_file()}


def test_inconsistent_or_incomplete_rows_are_gaps_not_interpolated(history):
    frame, _ = history
    frame.loc[frame.index[0], "High"] = 1.0
    s, raw = h.prepare("PETR4", frame, "2026-10-14", h.radar.now().isoformat())
    assert s["rows"][0]["close"] is None
    assert s["rows"][0]["adjusted_close"] is None
    assert s["rows"][1]["close"] == 12.0
    assert s["missing_bars"] == 1 and b"Dividends" in raw
    frame.loc[frame.index[0], "Close"] = float("nan")
    assert (
        h.prepare("PETR4", frame, "2026-10-14", h.radar.now().isoformat())[0][
            "missing_bars"
        ]
        == 1
    )


def test_refresh_keeps_old_snapshots_and_failure_keeps_previous_copy(
    history, monkeypatch
):
    frame, _ = history
    first = h.refresh({"wallet": "wallet"})["series"]["PETR4"]
    frame.loc[frame.index[1], "Close"] = 12.5
    second = h.refresh({"wallet": "wallet"})["series"]["PETR4"]
    assert second["sha256"] != first["sha256"]
    assert h.radar.read(h.ROOT / "PETR4" / (first["sha256"] + ".json")) == first
    monkeypatch.setattr(
        h, "download", lambda *args: (_ for _ in ()).throw(ValueError("offline"))
    )
    failed = h.refresh({"wallet": "wallet"})
    assert failed["series"]["PETR4"] == second and "PETR4" in failed["refresh_errors"]


def test_corrupt_raw_copy_and_pointer_never_supply_prices(history):
    s = h.refresh({"wallet": "wallet"})["series"]["PETR4"]
    (h.ROOT / "PETR4" / (s["raw_sha256"] + ".csv")).write_bytes(b"corrupt")
    result = h.get({"wallet": "wallet"})
    assert not result["series"] and "PETR4" in result["errors"]
    h.radar.write(h.ROOT / "PETR4/latest.json", h.b.sealed({"snapshot": "../other"}))
    assert not h.get({"wallet": "wallet"})["series"]


def test_duplicate_dates_empty_and_all_invalid_rejected(history):
    frame, _ = history
    for bad in [frame.iloc[:0], pd.concat([frame.iloc[:1], frame.iloc[:1]])]:
        with pytest.raises(ValueError):
            h.prepare("PETR4", bad, "2026-10-14", h.radar.now().isoformat())
    bad = copy.deepcopy(frame)
    bad["Close"] = -1.0
    with pytest.raises(ValueError):
        h.prepare("PETR4", bad, "2026-10-14", h.radar.now().isoformat())


def test_queries_and_concurrent_refresh_are_bounded(history):
    with pytest.raises(ValueError):
        h.get({"wallet": "wallet", "ticker": "../../secret"})
    h.REFRESH_LOCK.acquire()
    try:
        with pytest.raises(ValueError, match="already_running"):
            h.refresh({"wallet": "wallet"})
    finally:
        h.REFRESH_LOCK.release()


def test_web_refresh_requires_local_origin_csrf_and_strict_json(history, monkeypatch):
    import gzip
    import http.client
    import json
    import threading

    import server

    calls = []
    monkeypatch.setattr(h, "refresh", lambda body: calls.append(body) or {"ok": True})
    with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as web:
        thread = threading.Thread(target=web.serve_forever, daemon=True)
        thread.start()
        port = web.server_address[1]

        def post(body, **headers):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            conn.request(
                "POST",
                "/api/portfolio/stock-history/refresh",
                body,
                {
                    "Content-Type": "application/json",
                    "Origin": f"http://127.0.0.1:{port}",
                    **headers,
                },
            )
            response = conn.getresponse()
            status = response.status
            response.read()
            conn.close()
            return status

        try:
            payload = json.dumps({"wallet": "wallet"})
            csrf = {"X-CSRF-Token": server.forward_jobs.JOBS.csrf}
            assert post(payload) == 403
            assert post(payload, Origin="https://example.com", **csrf) == 403
            assert post('{"wallet":"a","wallet":"b"}', **csrf) == 400
            assert not calls
            assert post(payload, **csrf) == 200
            assert calls == [{"wallet": "wallet"}]
            monkeypatch.setattr(h, "get", lambda query: {"data": "x" * 200000})
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            conn.request(
                "GET",
                "/api/portfolio/stock-history?wallet=wallet",
                headers={"Accept-Encoding": "gzip"},
            )
            response = conn.getresponse()
            assert (
                response.status == 200
                and response.getheader("Content-Encoding") == "gzip"
            )
            assert json.loads(gzip.decompress(response.read()))["data"] == "x" * 200000
            conn.close()
        finally:
            web.shutdown()
            thread.join()


@pytest.fixture
def intraday(tmp_path, monkeypatch):
    """Fake Yahoo: bars at 10:00/10:01/10:07 on every weekday of the window."""
    monkeypatch.setattr(h, "ROOT", tmp_path / "history")
    monkeypatch.setattr(h, "tickers", lambda wallet: ["PETR4"])
    monkeypatch.setattr(h.radar, "now", lambda: pd.Timestamp("2026-10-16T14:21:00-03:00"))
    monkeypatch.setattr(h, "LIVE", {})
    monkeypatch.setattr(h, "ATTEMPTED", set())
    calls, fail = [], set()

    class Ticker:
        def history(self, **kw):
            calls.append(kw)
            if kw["interval"] in fail:
                raise ValueError("offline")
            days = pd.bdate_range(
                kw["start"], pd.Timestamp(kw["end"]) - pd.Timedelta(days=1)
            )
            stamps = [
                pd.Timestamp(f"{d.date()} {t}", tz="America/Sao_Paulo")
                for d in days
                for t in ("10:00", "10:01", "10:07")
            ]
            frame = pd.DataFrame(
                {
                    "Open": 10.0,
                    "High": 11.0,
                    "Low": 9.0,
                    "Close": [10.0, 10.5, 10.25] * len(days),
                    "Volume": 100.0,
                },
                index=pd.DatetimeIndex(stamps),
            )
            frame.loc[
                pd.Timestamp("2026-10-15 10:07", tz="America/Sao_Paulo"), "High"
            ] = 10.0
            return frame.dropna()

    monkeypatch.setattr(h.yf, "Ticker", lambda symbol: Ticker())
    return calls, fail


def test_intraday_tiers_live_session_and_no_repeat_requests(intraday):
    calls, _ = intraday
    assert h.refresh_intraday({"wallet": "w"})["refresh_errors"] == {}
    assert [c["interval"] for c in calls] == ["1m"] * 5 + ["5m", "1h"]
    assert calls[0]["start"] == "2026-09-17" and calls[4]["end"] == "2026-10-17"
    assert all(c["auto_adjust"] is False and c["repair"] is False for c in calls)
    files = {p.relative_to(h.ROOT).as_posix() for p in h.ROOT.rglob("*.json")}
    assert "PETR4/intraday/2026-10-15/1m.json" in files
    assert "PETR4/intraday/2026-09-01/5m.json" in files
    assert "PETR4/intraday/2025-10-01/1h.json" in files
    assert not any("2026-10-16" in f for f in files)  # open session: memory only
    assert len({f.split("/")[2] for f in files}) == len(files)  # one tier per day
    calls.clear()
    h.refresh_intraday({"wallet": "w"})
    assert [(c["interval"], c["start"], c["end"]) for c in calls] == [
        ("1m", "2026-10-16", "2026-10-17")
    ]
    q = {"wallet": "w", "from": "2026-10-15", "to": "2026-10-16", "interval": "5m"}
    result = h.get_intraday(q)
    assert result["series"]["PETR4"]["rows"] == [
        ["2026-10-15 10:00", 10.5],
        ["2026-10-15 10:05", None],  # incoherent bar is a gap, not repaired
        ["2026-10-16 10:00", 10.5],
        ["2026-10-16 10:05", 10.25],
    ]
    assert result["live"]["PETR4"]["last_bar"] == "10:07"
    assert h.resample("2026-10-15", [["16:55", None, None, None, None, None]], 1) == []
    old = h.get_intraday(
        {**q, "from": "2026-09-01", "to": "2026-09-01", "interval": "1m"}
    )
    assert old["series"]["PETR4"]["resolution"] == {"2026-09-01": "5m"}
    assert [r[0] for r in old["series"]["PETR4"]["rows"]] == [
        "2026-09-01 10:00",
        "2026-09-01 10:05",
    ]
    with pytest.raises(ValueError):
        h.get_intraday({**q, "from": "2026-01-01"})


def test_intraday_failed_fine_tier_is_not_filled_coarser_and_corruption_is_refused(
    intraday,
):
    calls, fail = intraday
    fail.add("1m")
    assert "PETR4" in h.refresh_intraday({"wallet": "w"})["refresh_errors"]
    days = {p.parent.name for p in h.ROOT.rglob("*.json")}
    assert days and max(days) < "2026-09-17"  # recent days wait for a 1m retry
    fail.clear()
    h.refresh_intraday({"wallet": "w"})
    assert (h.ROOT / "PETR4/intraday/2026-09-17/1m.json").exists()
    path = h.ROOT / "PETR4/intraday/2026-10-15/1m.json"
    path.write_bytes(path.read_bytes().replace(b"10.5", b"99.5"))
    q = {"wallet": "w", "from": "2026-10-15", "to": "2026-10-15", "interval": "1m"}
    result = h.get_intraday(q)
    assert not result["series"] and "PETR4" in result["errors"]
