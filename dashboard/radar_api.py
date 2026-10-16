"""Local radar API, asynchronous commands and read-only result projections."""

import functools
import os
import re
import secrets
import sys
import threading
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import multiasset_radar as radar

ROOT = Path(os.environ.get("HFL_RADAR_ROOT", radar.OUTPUT))
FIELDS = {
    "universe": {"tickers"},
    "prepare": {"tickers", "session", "mode"},
    "preflight": {"tickers", "session", "max_usd", "replay"},
    "run": {
        "tickers",
        "session",
        "max_usd",
        "replay",
        "confirmation_token",
        "authorize_paid",
        "confirm",
    },
}
MUTEX = threading.Lock()
ACTIVE = False


@functools.lru_cache(maxsize=2)
def _catalog(path, stamp):
    symbols = set(radar.EXAMPLES)
    if path:
        with zipfile.ZipFile(path) as archive, archive.open(
            archive.namelist()[0]
        ) as rows:
            for line in rows:
                if line[:2] == b"01" and line[24:27] == b"010" and line[10:12] == b"02":
                    symbol = line[12:24].strip().decode("ascii")
                    if re.fullmatch(r"[A-Z]{4}[3-8]", symbol):
                        symbols.add(symbol)
    return sorted(symbols)


def search(query):
    if not isinstance(query, str) or not re.fullmatch(r"[A-Za-z0-9.]{0,10}", query):
        raise ValueError("invalid_search")
    paths = sorted((radar.ROOT / "data/raw/cotahist").glob("COTAHIST_A*.ZIP"))
    path = paths[-1] if paths else None
    symbols = _catalog(
        str(path) if path else None, path.stat().st_mtime_ns if path else 0
    )
    return {
        "tickers": [s for s in symbols if query.upper() in s][:100],
        "source": path.name if path else "technical_examples_only",
        "note": "Catálogo local histórico; negociação atual validada ao preparar dados.",
    }


def get(command, query, csrf):
    if command == "status" and not query:
        result = radar.status(ROOT)
        result["csrf_token"] = csrf
        result["job"] = job()
        return result
    if command == "search" and set(query) <= {"q"}:
        return search(query.get("q", ""))
    if command == "detail" and set(query) == {"ticker", "session"}:
        return radar.detail(query["ticker"], query["session"], ROOT)
    raise ValueError("invalid_query")


def job():
    path = ROOT / "job.json"
    result = radar.read(path) if path.exists() else None
    if result and result["status"] == "RUNNING" and not ACTIVE:
        return {**result, "status": "INTERRUPTED_REVIEW_LOCK_AND_REPLAY"}
    return result


def post(command, payload):
    global ACTIVE
    if (
        command not in FIELDS
        or not isinstance(payload, dict)
        or set(payload) != FIELDS[command]
    ):
        raise ValueError("invalid_payload")
    values = radar.tickers(payload["tickers"], empty=command == "universe")
    if "session" in payload:
        radar.session(payload["session"])
    for key in ("replay", "authorize_paid", "confirm"):
        if key in payload and type(payload[key]) is not bool:
            raise ValueError("invalid_boolean")
    if command == "universe":
        return {"tickers": radar.configure(values, ROOT)}
    if command == "preflight":
        return radar.preflight(
            values,
            ROOT,
            day=payload["session"],
            max_usd=payload["max_usd"],
            replay=payload["replay"],
        )
    if command == "prepare" and payload["mode"] not in ("live", "synthetic"):
        raise ValueError("invalid_mode")
    if command == "run":
        report = radar.preflight(
            values,
            ROOT,
            day=payload["session"],
            max_usd=payload["max_usd"],
            replay=payload["replay"],
        )
        if (
            not report["ready"]
            or not payload["confirm"]
            or payload["confirmation_token"] != report["confirmation_token"]
        ):
            raise ValueError("preflight_or_confirmation_changed")
        if (
            not payload["replay"]
            and any(i["mode"] == "live" for i in report["items"])
            and not payload["authorize_paid"]
        ):
            raise ValueError("explicit_paid_authorization_required")
    with MUTEX:
        if ACTIVE or (ROOT / "operation.lock").exists():
            raise ValueError("radar_busy_or_stale_lock")
        state = {
            "id": secrets.token_hex(12),
            "command": command,
            "status": "RUNNING",
            "started_at": radar.now().isoformat(),
        }
        radar.write(ROOT / "job.json", state)
        ACTIVE = True

    def work():
        global ACTIVE
        try:
            if command == "prepare":
                result = radar.prepare(
                    values, ROOT, end=payload["session"], mode=payload["mode"]
                )
            else:
                result = radar.run(
                    values,
                    payload["confirmation_token"],
                    ROOT,
                    day=payload["session"],
                    max_usd=payload["max_usd"],
                    authorize_paid=payload["authorize_paid"],
                    replay=payload["replay"],
                )
            state.update(
                status="COMPLETED",
                items=[{"ticker": i["ticker"], "status": i["status"]} for i in result],
            )
        except Exception as exc:
            state.update(status="FAILED", error=type(exc).__name__)
        finally:
            state["finished_at"] = radar.now().isoformat()
            radar.write(ROOT / "job.json", state)
            with MUTEX:
                ACTIVE = False

    threading.Thread(target=work, daemon=True).start()
    return state.copy()
