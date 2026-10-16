"""Incident 2026-10-12 02:59: a GET's offline guard blocked the paid Radar worker.

Everything runs against a fake Gemini on loopback: no external network, no key.
"""

import asyncio
import http.server
import json
import socket
import sqlite3
import sys
import threading
from contextlib import closing, contextmanager
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import multiasset_radar as radar  # noqa: E402
import network_scope  # noqa: E402
import platform_api  # noqa: E402
import server  # noqa: E402

from src.agents.llm_client import GeminiLLMClient, _http_json_transport  # noqa: E402
from src.experiments import h2_evaluation_offline as offline  # noqa: E402

DAY = "2026-10-09"
SOCKET = (socket.socket.connect, socket.socket.connect_ex, socket.create_connection)


@pytest.fixture(autouse=True)
def restore_socket(monkeypatch):
    """Every test leaves the process exactly as it found it (incl. a leaked guard)."""
    for owner, name, value in (
        (socket.socket, "connect", SOCKET[0]),
        (socket.socket, "connect_ex", SOCKET[1]),
        (socket, "create_connection", SOCKET[2]),
    ):
        monkeypatch.setattr(owner, name, value)
    for module in list(sys.modules.values()):
        if getattr(module, "no_network", None) is offline.no_network:
            monkeypatch.setattr(module, "no_network", offline.no_network)
    monkeypatch.setattr(offline, "no_network", offline.no_network)
    # No test here may reach the real provider, whatever the guard state.
    monkeypatch.setattr(
        GeminiLLMClient,
        "_default_transport",
        lambda *a: pytest.fail("real Gemini transport used"),
    )
    yield
    socket.socket.connect, socket.socket.connect_ex, socket.create_connection = SOCKET


@pytest.fixture
def gemini():
    """Fake Gemini on 127.0.0.1 answering with the existing offline fake payload."""
    seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            payload = radar.fake_gemini("POST", self.path, {}, body)
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def transport(method, url, headers, body):
        # Real urllib/http.client path: socket.create_connection, like Gemini.
        return _http_json_transport(method, f"http://127.0.0.1:{port}/g", {}, body, 10)

    transport.port, transport.seen = port, seen
    yield transport
    httpd.shutdown()
    httpd.server_close()


def ping(port):
    with closing(socket.create_connection(("127.0.0.1", port), timeout=5)):
        return True


def live_input(root, ticker):
    bars = radar.synthetic_bars(pd.Timestamp(DAY))

    class Extractor:
        def download(self, *args):
            return bars

        def source_description(self):
            return {"name": "FAKE_OFFICIAL_SOURCE_OFFLINE"}

        def _cotahist(self, year):
            return self

    original = radar.read_cotahist
    radar.read_cotahist = lambda *args: bars
    try:
        result = radar.prepare(
            [ticker], root, end=DAY, mode="live", extractor=Extractor()
        )
    finally:
        radar.read_cotahist = original
    assert result[0]["status"] == "PREPARED"


def incident(root, transport, monkeypatch):
    """GET readiness holds its preflight guard while the worker transmits, as at 02:59."""
    live_input(root, "PETR4")
    monkeypatch.setenv("GEMINI_API_KEY", "offline-placeholder-never-sent")
    monkeypatch.setattr(platform_api.global_api, "OFFICIAL_RADAR", root)
    inside, release, probes = threading.Event(), threading.Event(), {}
    guard = radar.no_network  # sealed today; scoped once network_scope is installed

    @contextmanager
    def held():
        with guard():
            if threading.current_thread().name == "get":
                try:
                    ping(transport.port)
                    probes["get_loopback"] = "allowed"
                except RuntimeError as exc:
                    probes["get_loopback"] = str(exc)
                inside.set()
                release.wait(30)
            yield

    monkeypatch.setattr(radar, "no_network", held)
    get = threading.Thread(
        target=lambda: platform_api.radar_readiness(DAY, ["PETR4"], root), name="get"
    )
    get.start()
    assert inside.wait(30)
    token = radar.preflight(["PETR4"], root, day=DAY)["confirmation_token"]
    outcome = {}

    def work():  # the Radar API worker: a plain thread, like radar_api.post
        outcome["result"] = radar.run(
            ["PETR4"], token, root, day=DAY, authorize_paid=True, transport=transport
        )

    worker = threading.Thread(target=work, name="radar-worker")
    worker.start()
    worker.join(60)
    release.set()
    get.join(30)
    return outcome["result"][0], probes


def journal(root):
    path = radar.folder_for(root, "PETR4", DAY) / "calls.sqlite"
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        calls = db.execute("SELECT raw, record FROM calls ORDER BY sequence").fetchall()
        attempts = db.execute("SELECT evidence FROM attempts").fetchall()
    return calls, [json.loads(e) for (e,) in attempts]


# 1. Cause ----------------------------------------------------------------------------


def test_sealed_guard_blocks_other_threads(gemini):
    errors = []

    def call():
        try:
            gemini("POST", "", {}, {"contents": [{"parts": [{"text": "{}"}]}]})
        except RuntimeError as exc:
            errors.append(str(exc))

    with offline.no_network():  # a GET in another thread
        worker = threading.Thread(target=call)
        worker.start()
        worker.join(10)
    assert errors == ["offline qualification forbids network"]
    assert gemini.seen == []  # refused before any socket: nothing reached the server
    assert ping(gemini.port)  # outside the window the same call works


def test_sealed_guard_leaks_when_checks_interleave(gemini):
    a_in, b_in, a_out = threading.Event(), threading.Event(), threading.Event()

    def a():
        with offline.no_network():
            a_in.set()
            b_in.wait(10)
        a_out.set()

    def b():
        a_in.wait(10)
        with offline.no_network():
            b_in.set()
            a_out.wait(10)

    threads = [threading.Thread(target=a), threading.Thread(target=b)]
    [t.start() for t in threads]
    [t.join(10) for t in threads]
    # Both checks are over, yet each restored what it saw on entry: still guarded.
    assert socket.create_connection is not SOCKET[2]
    with pytest.raises(RuntimeError, match="offline qualification forbids network"):
        ping(gemini.port)


def test_incident_reproduced_with_real_radar_code(tmp_path, gemini, monkeypatch):
    item, probes = incident(tmp_path / "radar", gemini, monkeypatch)
    assert item["status"] == "FAILED_REPLAY_ONLY"
    assert probes["get_loopback"] == "offline qualification forbids network"
    calls, attempts = journal(tmp_path / "radar")
    records = [json.loads(r) for _, r in calls]
    assert len(calls) == 5 and all(raw is None for raw, _ in calls)
    assert {(r["status"], r["error_type"], r["error_message"]) for r in records} == {
        ("error", "RuntimeError", "offline qualification forbids network")
    }
    assert {(a["state"], a["http_status"], a["type"]) for a in attempts} == {
        ("TRANSPORT_ERROR", None, "RuntimeError")
    }
    assert gemini.seen == []  # same signature as 02:59 and zero requests received
    outcome = platform_api.committee_outcome(tmp_path / "radar", "PETR4", DAY)
    assert outcome == {
        "state": "NO_RECOVERABLE_ENVELOPE",
        "calls_reserved": 5,
        "calls": {"BLOCKED_BEFORE_CONNECT": 5},
        "billing": "NO_SEND_EVIDENCE",
    }


# 2. Fix ------------------------------------------------------------------------------


def test_scoped_guard_isolates_worker(tmp_path, gemini, monkeypatch):
    network_scope.install()
    item, probes = incident(tmp_path / "radar", gemini, monkeypatch)
    assert (
        probes["get_loopback"] == "offline qualification forbids network"
    )  # GET still offline
    assert item["status"] == "COMPLETED", item
    assert len(gemini.seen) == 6  # 5 analysts + Risk, through the real HTTP path
    assert platform_api.committee_outcome(tmp_path / "radar", "PETR4", DAY)["state"] == (
        "COMMITTEE_COMPLETED"
    )
    assert socket.create_connection(("127.0.0.1", gemini.port), timeout=5)


def test_scoped_guard_blocks_like_the_sealed_one(gemini):
    network_scope.install()
    network_scope.install()  # idempotent: no double wrapping
    with network_scope.no_network():
        for attempt in (
            lambda: ping(gemini.port),  # create_connection refused, even loopback
            lambda: socket.socket().connect(("192.0.2.1", 443)),  # external connect
            lambda: asyncio.run(
                asyncio.to_thread(ping, gemini.port)
            ),  # follows to_thread
        ):
            with pytest.raises(
                RuntimeError, match="offline qualification forbids network"
            ):
                attempt()
        with closing(socket.socket()) as raw:  # loopback connect allowed, as sealed
            raw.connect(("127.0.0.1", gemini.port))
        other = []
        thread = threading.Thread(target=lambda: other.append(ping(gemini.port)))
        thread.start()
        thread.join(10)
        assert other == [True]  # a separate request/worker thread is not offline
    assert ping(gemini.port)


def test_server_main_installs_scope_and_rebinds_every_guard(monkeypatch):
    assert radar.no_network is offline.no_network  # importing the server changes nothing
    view = {"mode": "CONSULTATIVE_SANDBOX"}
    assert platform_api.get("radar-view", view)["network_isolation"] is False

    class Stop(server.ReusableTCPServer):
        def __init__(self, *args):
            pass

        def __exit__(self, *args):
            pass

        def serve_forever(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(radar, "RadarExtractor", radar.RadarExtractor)
    monkeypatch.setattr(platform_api.radar_api, "ROOT", platform_api.radar_api.ROOT)
    monkeypatch.setattr(server, "ReusableTCPServer", Stop)
    monkeypatch.setattr(sys, "argv", ["server.py", "0"])
    server.main()
    assert getattr(socket.create_connection, "_hfl_scoped", False)
    left = [
        name
        for name, module in list(sys.modules.items())
        if getattr(module, "no_network", None) is network_scope.SEALED
    ]
    assert left == []
    assert offline.no_network is network_scope.no_network  # later imports get it too
    assert platform_api.get("radar-view", view)["network_isolation"] is True


# 3. Audit trail ------------------------------------------------------------------------


def test_replay_after_incident_sends_nothing_and_keeps_records(
    tmp_path, gemini, monkeypatch
):
    root = tmp_path / "radar"
    incident(root, gemini, monkeypatch)
    folder = radar.folder_for(root, "PETR4", DAY)
    claim, calls = (folder / "claim.json").read_bytes(), journal(root)[0]
    report = radar.preflight(["PETR4"], root, day=DAY, replay=True)
    assert report["usd_reserved"] == 0
    [item] = radar.run(
        ["PETR4"],
        report["confirmation_token"],
        root,
        day=DAY,
        replay=True,
        transport=lambda *a: pytest.fail("replay must not transmit"),
    )
    assert item["status"] == "FAILED_REPLAY_ONLY"
    assert (folder / "claim.json").read_bytes() == claim
    assert journal(root)[0] == calls and gemini.seen == []
    # A new paid batch on the same claim is refused, never re-sent.
    with pytest.raises(ValueError):
        radar.run(
            ["PETR4"], report["confirmation_token"], root, day=DAY, authorize_paid=True
        )
    assert "inference_already_reserved_replay_only" in json.dumps(
        radar.preflight(["PETR4"], root, day=DAY)
    )


def test_job_outcome_distinguishes_infrastructure_from_committees(
    tmp_path, gemini, monkeypatch
):
    root = tmp_path / "radar"
    incident(root, gemini, monkeypatch)
    job = {
        "command": "run",
        "status": "COMPLETED",
        "started_at": "2000-01-01T00:00:00+00:00",
        "finished_at": "2100-01-01T00:00:00+00:00",
        "items": [{"ticker": "PETR4", "status": "FAILED_REPLAY_ONLY"}],
    }
    radar.write(root / "job.json", job)
    monkeypatch.setattr(platform_api.radar_api, "ROOT", root)
    outcome = platform_api.radar_job(root)["outcome"]
    assert outcome["state"] == "FAILED"
    assert outcome["summary"] == "Infraestrutura concluída · 0/1 comitês concluídos"
    [entry] = [j for j in platform_api.jobs_status() if j["module"] == "Radar"]
    assert (entry["native_state"], entry["state"]) == ("COMPLETED", "FAILED")
    item = platform_api.radar_readiness(DAY, ["PETR4"], root)["items"][0]
    assert item["outcome"]["state"] == "NO_RECOVERABLE_ENVELOPE"
    assert "identidade operacional separada" in item["action"]
    assert "offline qualification" not in json.dumps(item)  # codes only, no messages


def test_partial_and_uncertain_calls_are_not_reported_as_failures_only(tmp_path, gemini):
    def flaky(method, url, headers, body):
        flaky.n = getattr(flaky, "n", 0) + 1
        if flaky.n == 3:
            raise ConnectionResetError("simulated drop after send")
        return gemini(method, url, headers, body)

    root = tmp_path / "radar"
    live_input(root, "PETR4")
    with pytest.MonkeyPatch.context() as m:
        m.setenv("GEMINI_API_KEY", "offline-placeholder-never-sent")
        token = radar.preflight(["PETR4"], root, day=DAY)["confirmation_token"]
        radar.run(["PETR4"], token, root, day=DAY, authorize_paid=True, transport=flaky)
    outcome = platform_api.committee_outcome(root, "PETR4", DAY)
    assert (
        outcome["state"] == "COMMITTEE_PARTIAL"
        and outcome["billing"] == "PROVIDER_USAGE_RECORDED"
    )
    path = radar.folder_for(root, "PETR4", DAY) / "calls.sqlite"
    with closing(sqlite3.connect(path)) as db, db:  # a crash between reserve and record
        db.execute("UPDATE calls SET record=NULL, record_sha=NULL WHERE sequence=0")
    outcome = platform_api.committee_outcome(root, "PETR4", DAY)
    assert outcome["state"] == "UNCERTAIN_CALLS"
