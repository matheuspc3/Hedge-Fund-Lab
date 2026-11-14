"""Collect only required missing market data into the continuous campaign root."""
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import replay_multiasset as r
from pilot_paper import bind

ROOT = r.PROJECT / "data/cache/continuous-replay/april-november-2026-flash"
SOURCE = Path("C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab")
START = "2026-04-06"


def prepare():
    root = ROOT
    if (root / "data_audit.json").exists():
        return r.checked(root / "data_audit.json")
    source = SOURCE / "data/platform"
    platform = root / "source/platform"
    rawdir = root / "source/raw"
    rawdir.mkdir(parents=True, exist_ok=True)
    at = r.radar.now()
    end = r.radar.last_closed(at)
    if (root / "clock.json").exists():
        end = r.checked(root / "clock.json")["end"]
    else:
        r.save(root / "clock.json", {"at": at.isoformat(), "start": START, "end": end, "open_session_excluded": True})
    r.market.ROOT = source / "market-base-v1"
    original = r.market.acquired()
    for item in original:
        if item.get("year") in (2025, 2026) or item.get("session", "").startswith("2026"):
            src = r.market.ROOT / "b3" / (item["file_name"] + ".json")
            r.radar.write(platform / "market-base-v1/b3" / src.name, src.read_bytes(), immutable=True)
    r.market.ROOT = platform / "market-base-v1"
    missing = [d for d in r.sessions(START, end) if any(d not in {v["date"] for v in r.market.merged(t)} for t in r.radar.EXAMPLES)]

    def fetch(url):
        raw = r.market.fetch_http(url)
        if raw is not None:
            ext = ".zip" if "COTAHIST" in url else ".json"
            r.radar.write(rawdir / (r.hashlib.sha256(raw).hexdigest() + ext), raw, immutable=True)
        return raw

    for day in missing:
        result = r.market.acquire(r.market.target("daily", date.fromisoformat(day)), fetch)
        print(json.dumps({"acquired_b3": day, "published": result is not None}), flush=True)
    for t in r.radar.EXAMPLES:
        # Keep previous provenance intact; refresh only the replay's needed interval.
        old = source / "stock-history-v1" / t
        if old.exists():
            shutil.copytree(old, root / "source/prior-yahoo" / t, dirs_exist_ok=True)
        begin = str(date.fromisoformat(r.previous(START)) - timedelta(days=450))
        frame = r.stock.yf.Ticker(t + ".SA").history(start=begin, end=str(date.fromisoformat(end) + timedelta(days=1)), interval="1d", auto_adjust=False, back_adjust=False, repair=False, actions=True, keepna=True, timeout=30, raise_errors=True)
        snapshot, raw = r.stock.prepare(t, frame, end, r.radar.now().isoformat())
        snapshot = r.b.sealed({**{k: v for k, v in snapshot.items() if k != "sha256"}, "requested_period": "BOUNDED_REPLAY", "requested_start": begin, "requested_end": end})
        out = platform / "stock-history-v1" / t
        r.radar.write(out / (snapshot["raw_sha256"] + ".csv"), raw, immutable=True)
        r.radar.write(out / (snapshot["sha256"] + ".json"), snapshot, immutable=True)
        r.radar.write(out / "latest.json", r.b.sealed({"snapshot": snapshot["sha256"]}))
        r.dividends.refresh(t, fetch)
        print(json.dumps({"yahoo_and_dividends": t, "through": end}), flush=True)
    r.stock.ROOT = platform / "stock-history-v1"
    def days(start=START, stop=end):
        return r.sessions(start, stop)
    prep = bind(r.prepare, END=end, sessions=days)
    prep(root / "inputs", platform)
    audit = {"start": START, "end": end, "at": at.isoformat(), "sessions": len(days()), "missing_b3_fetched": missing, "source": str(source), "market_storage": "sealed JSON plus original newly downloaded ZIP/JSON and Yahoo CSV", "book_and_calls_storage": "separate campaign SQLite", "source_platform": str(platform), "data_manifest_sha256": r.b.sha_file(root / "inputs/manifest.json")}
    r.save(root / "data_audit.json", audit)
    return audit


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
