"""V7 contracts: offline HTTP, explicit commands, preserved authorities."""

import http.client
import json
import shutil
import socket
import sys
import threading
import time
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import platform_api as api  # noqa: E402
import server  # noqa: E402

from src.agents.llm_client import GeminiLLMClient  # noqa: E402
from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

CONNECT = socket.create_connection


def inventory(root):
    return {
        p.relative_to(root).as_posix(): api.b.sha_file(p)
        for p in root.rglob("*")
        if p.is_file() and p.suffix != ".lock"
    }


class PlatformChecks(unittest.TestCase):
    def setUp(self):
        self.suite = ROOT / "data/global_pm" / ("test-only-v7-" + uuid.uuid4().hex)
        self.jobs = api.GlobalJobs(self.suite / "jobs")
        self.output = patch.object(api.pm, "OUTPUT", self.suite)
        self.output.start()
        self.job_patch = patch.object(api, "GLOBAL_JOBS", self.jobs)
        self.job_patch.start()
        self.offline = no_network()
        self.offline.__enter__()
        self.transport = patch.object(
            GeminiLLMClient,
            "_default_transport",
            side_effect=AssertionError("PAID_CALL_FORBIDDEN"),
        )
        self.transport.start()
        self.httpd = server.socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), server.Handler
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.transport.stop()
        self.offline.__exit__(None, None, None)
        self.job_patch.stop()
        self.output.stop()
        assert self.suite.resolve().parent == (ROOT / "data/global_pm").resolve()
        assert self.suite.name.startswith("test-only-v7-")
        shutil.rmtree(self.suite, ignore_errors=True)

    def request(self, method, path, body=None, headers=None):
        with patch.object(socket, "create_connection", CONNECT):
            c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
            c.request(method, path, body, headers or {})
            response = c.getresponse()
            result = response.status, response.read(), dict(response.getheaders())
            c.close()
            return result

    def post(self, command, value, headers=None):
        h = {
            "Origin": f"http://127.0.0.1:{self.port}",
            "Content-Type": "application/json",
            "X-CSRF-Token": api.forward_jobs.JOBS.csrf,
        }
        if headers:
            h.update(headers)
        return self.request(
            "POST",
            "/api/platform/global-" + command,
            json.dumps(value) if not isinstance(value, str) else value,
            h,
        )

    def payload(self, **updates):
        return {
            "id": "v7-" + uuid.uuid4().hex,
            "mode": "SYNTHETIC_DEMO",
            "session": "2026-10-09",
            "tickers": ["PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3"],
            "capital": "100000",
            "confirm_hypothetical": True,
            "ack_fixture_policy": True,
            **updates,
        }

    def wait(self):
        deadline = time.monotonic() + 15
        while self.jobs.active and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertFalse(self.jobs.active, "job did not finish")

    def prepare(self):
        p = self.payload()
        status, body, _ = self.post("prepare", p)
        self.assertEqual(status, 202, body)
        self.wait()
        self.assertEqual(api.public_global(p["id"])["state"], "PREPARED")
        return p

    def test_navigation_and_head_compatibility(self):
        for path in (
            "/",
            "/paper",
            "/paper.html",
            "/paper/",
            "/radar?tickers=PETR4",
            "/portfolio?analysis=v7-" + "a" * 32,
            "/h2",
            "/logs",
            "/legacy",
            "/index.html",
        ):
            with self.subTest(path=path):
                status, body, h = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(b"hfl-shell", body)
                # V7.6.2 (HFL-UX-001): "Pesquisa e Auditoria" became two areas of the
                # unified navigation; the shell must still be on every page.
                self.assertIn('aria-label="Navegação principal"'.encode(), body)
                self.assertIn(b">Legacy</a>", body)
                self.assertIn(b">Auditoria</a>", body)
                head, empty, hh = self.request("HEAD", path)
                self.assertEqual(head, 200)
                self.assertEqual(empty, b"")
                self.assertEqual(h["Content-Length"], hh["Content-Length"])
        for path in (
            "/platform.js",
            "/shell.css",
            "/shell.js",
            "/global-workflow.js",
            "/vendor/chart.umd.js",
        ):
            self.assertEqual(self.request("GET", path)[0], 200)
        for path in (
            "/platform_api.py",
            "/shell.html",
            "/data/global_pm/private/calls.sqlite",
            "/../src/config.py",
        ):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_origin_csrf_host_and_payload_security(self):
        p = self.payload()
        for h in (
            {"Origin": "https://evil.example"},
            {"Host": "evil.example"},
            {"X-CSRF-Token": "wrong"},
            {"Origin": ""},
            {"Sec-Fetch-Site": "cross-site"},
        ):
            self.assertEqual(self.post("prepare", p, h)[0], 403)
        for body in ('{"id":1,"id":2}', '{"id":NaN}', "[]", "{}", "x" * 4097):
            self.assertEqual(self.post("prepare", body)[0], 400)
        self.assertEqual(self.post("prepare", p, {"Content-Type": "text/plain"})[0], 400)
        self.assertEqual(self.post("prepare", "", {"Content-Length": "65537"})[0], 400)
        self.assertEqual(inventory(self.suite), {})

    def test_duplicate_headers_and_all_mutation_routes(self):
        for command in ("prepare", "run", "replay"):
            for headers in ({"Origin": "https://evil.example"}, {"X-CSRF-Token": ""}):
                self.assertEqual(self.post(command, {}, headers)[0], 403)
            self.assertEqual(self.post(command, {"unexpected": True})[0], 400)
        for duplicate in ("Host", "Origin", "X-CSRF-Token", "Content-Length"):
            with self.subTest(header=duplicate), patch.object(
                socket, "create_connection", CONNECT
            ):
                c = http.client.HTTPConnection("127.0.0.1", self.port)
                c.putrequest("POST", "/api/platform/global-prepare", skip_host=True)
                headers = {
                    "Host": f"127.0.0.1:{self.port}",
                    "Origin": f"http://127.0.0.1:{self.port}",
                    "X-CSRF-Token": api.forward_jobs.JOBS.csrf,
                    "Content-Type": "application/json",
                    "Content-Length": "0",
                }
                for key, value in headers.items():
                    c.putheader(key, value)
                    if key == duplicate:
                        c.putheader(key, value)
                c.endheaders()
                response = c.getresponse()
                self.assertEqual(
                    response.status, 400 if duplicate == "Content-Length" else 403
                )
                response.read()
                c.close()
        self.assertEqual(inventory(self.suite), {})

    def test_prepare_trust_boundary(self):
        for updates in (
            {"id": "../../escape"},
            {"tickers": ["PETR4"] * 2},
            {"tickers": ["PETR4"] * 6},
            {"tickers": []},
            {"session": "2026-10-08"},
            {"session": "2026-10-13"},
            {"mode": "live"},
            {"mode": "CONSULTATIVE_SANDBOX"},
            {"capital": "NaN"},
            {"capital": "-1"},
            {"capital": "1000000001"},
            {"capital": 100000},
            {"confirm_hypothetical": 1},
            {"ack_fixture_policy": False},
            {"extra": True},
        ):
            with self.subTest(updates=updates):
                status, body, _ = self.post("prepare", self.payload(**updates))
                self.assertEqual(status, 400, body)
        self.assertEqual(inventory(self.suite), {})

    def test_separate_sources_and_no_session_mixing(self):
        tickers = ["PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3"]
        synthetic = api.global_api.selection("SYNTHETIC_DEMO", "2026-10-09", tickers)
        official = api.global_api.selection("CONSULTATIVE_SANDBOX", "2026-10-09", tickers)
        self.assertFalse(synthetic["missing"])
        self.assertEqual(official["missing"], tickers)
        self.assertEqual(official["provider_calls"], 0)
        for mode in api.pm.MODES:
            d = api.get("radar-view", {"mode": mode})
            self.assertTrue(d["read_only"])
        with patch.object(api.radar_api, "ROOT", api.global_api.SYNTHETIC_RADAR):
            d = api.get("radar-view", {"mode": "CONSULTATIVE_SANDBOX"})
            self.assertFalse(d["mutation_available"])
            self.assertTrue(all(i["mode"] == "live" for i in d["items"]))
        with self.assertRaises((ValueError, OSError)):
            api.pm.load_opinions(
                api.global_api.SYNTHETIC_RADAR,
                tickers,
                "2026-10-08",
                "SYNTHETIC_DEMO",
                api.pm.now(),
            )

    def test_complete_fake_flow_duplicate_and_replay(self):
        with patch.object(
            api.radar, "run", side_effect=AssertionError("RADAR_CASCADE")
        ), patch.object(
            api.forward.fwd, "run", side_effect=AssertionError("FORWARD_CASCADE")
        ), patch.object(
            api.b.Store,
            "append",
            side_effect=AssertionError("FINANCIAL_EXECUTION"),
        ):
            p = self.prepare()
            self.assertEqual(self.post("prepare", p)[0], 409)
            q = {"id": p["id"], "max_usd": "0.25"}
            before = inventory(self.suite)
            preflight = api.get("global-preflight", q)
            self.assertTrue(preflight["ready"])
            self.assertEqual(inventory(self.suite), before)
            payload = {
                **q,
                "confirmation_token": preflight["confirmation_token"],
                "authorize_paid": False,
                "confirm": True,
            }
            self.assertEqual(
                self.post("run", {**payload, "confirmation_token": "stale"})[0], 400
            )
            self.assertEqual(
                self.post("run", {**payload, "authorize_paid": True})[0], 400
            )
            self.assertEqual(self.post("run", payload)[0], 202)
            self.wait()
            d = api.public_global(p["id"])
            self.assertEqual(d["status"], "VALID_PROPOSAL")
            self.assertFalse(d["execution_enabled"])
            self.assertFalse(d["result"]["response"]["operations"])
            self.assertEqual(self.post("run", payload)[0], 400)
            result_sha = api.b.sha_file(api.analysis_root(p["id"]) / "result.json")
            self.assertEqual(
                self.post("replay", {"id": p["id"], "confirm": True})[0], 202
            )
            self.wait()
            self.assertEqual(
                api.b.sha_file(api.analysis_root(p["id"]) / "result.json"), result_sha
            )
            self.assertEqual(
                self.post("replay", {"id": p["id"], "confirm": True})[0], 409
            )

    def test_preflight_budget_and_paid_gate_before_job(self):
        p = self.prepare()
        for budget in ("-1", "NaN", "6", "0"):
            with self.assertRaises(ValueError):
                api.cli.preflight(api.analysis_root(p["id"]), budget)
        report = {"ready": True, "confirmation_token": "test", "paid": True}
        payload = {
            "id": p["id"],
            "max_usd": "0.25",
            "confirmation_token": "test",
            "authorize_paid": False,
            "confirm": True,
        }
        before = inventory(self.suite)
        with patch.object(api.cli, "preflight", return_value=report), patch.dict(
            api.os.environ, {"GEMINI_API_KEY": ""}
        ):
            self.assertEqual(self.post("run", payload)[0], 400)
            self.assertEqual(
                self.post("run", {**payload, "authorize_paid": True})[0], 400
            )
        self.assertEqual(before, inventory(self.suite))

    def test_jobs_recovery_public_allowlist_and_native_states(self):
        p = self.payload()
        job = {
            "module": "Global PM",
            "id": p["id"],
            "job_id": p["id"] + "-run",
            "command": "run",
            "state": "RUNNING",
            "started_at": api.pm.now(),
            "cost_usd": None,
            "prompt": "PRIVATE",
            "error": "secret key private provider message",
        }
        api.b.write(self.jobs.root / (job["job_id"] + ".json"), api.b.sealed(job))
        before = inventory(self.suite)
        d = self.jobs.status()[0]
        self.assertEqual(d["state"], "RECOVERY_REQUIRED")
        self.assertEqual(d["native_state"], "RUNNING")
        self.assertNotIn("PRIVATE", json.dumps(d))
        self.assertNotIn("secret", json.dumps(d))
        self.assertEqual(before, inventory(self.suite))
        for native, state in (
            ("PROVIDER_FAILED", "FAILED"),
            ("REJECTED_BY_VALIDATOR", "BLOCKED"),
            ("PROPOSAL_EXPIRED", "EXPIRED"),
            ("AWAITING_PREFLIGHT", "PREPARED"),
            ("unknown", "BLOCKED"),
        ):
            self.assertEqual(
                api.visual_state(native), {"state": state, "native_state": native}
            )

    def test_failure_is_durable_and_not_retried(self):
        p = self.payload()
        with patch.object(api.pm, "load_opinions", return_value=({}, {})), patch.object(
            api.pm, "make_snapshot", side_effect=ValueError("secret prompt")
        ):
            self.assertEqual(self.post("prepare", p)[0], 202)
            self.wait()
        job = self.jobs.status()[0]
        self.assertEqual(job["state"], "FAILED")
        self.assertNotIn("secret", json.dumps(job))
        self.assertEqual(self.post("prepare", p)[0], 409)

    def test_worker_launch_failure_does_not_leave_active_job(self):
        with patch.object(
            api.threading.Thread, "start", side_effect=RuntimeError("no worker")
        ):
            with self.assertRaisesRegex(OSError, "global_worker_start_failed"):
                self.jobs.start("prepare", self.payload())
        self.assertFalse(self.jobs.active)
        self.assertEqual(self.jobs.status()[0]["state"], "FAILED")

    def test_recovery_uses_existing_envelope_without_new_call(self):
        p = self.prepare()
        root = api.analysis_root(p["id"])
        with self.assertRaises(api.cli.SimulatedCrash):
            api.cli.run(
                root,
                api.cli.preflight(root)["confirmation_token"],
                fake_case="E",
                crash="after_envelope",
            )
        self.assertEqual(api.public_global(p["id"])["state"], "RECOVERY_REQUIRED")
        self.assertEqual(self.post("replay", {"id": p["id"], "confirm": True})[0], 202)
        self.wait()
        self.assertEqual(api.public_global(p["id"])["state"], "COMPLETED")
        self.assertFalse(api.cli.preflight(root)["ready"])

    def test_read_only_overview_and_no_final_test_reads(self):
        original_read = Path.open

        def guarded(path, *args, **kwargs):
            text = path.as_posix().lower()
            if any(part in text for part in ("final_test", "final-test", "finaltest")):
                raise AssertionError("FINAL_TEST_READ")
            return original_read(path, *args, **kwargs)

        roots = [
            ROOT / "data/forward",
            ROOT / "data/radar",
            ROOT / "data/portfolio",
            self.suite,
        ]
        before = [inventory(root) for root in roots]
        with patch.object(Path, "open", guarded):
            d = api.overview()
            self.assertTrue(d["read_only"])
            self.assertEqual(d["provider_calls"], 0)
            self.assertEqual(len(d["wallets"]["data"]["wallets"]), 5)
            self.assertTrue(d["integrity"]["data"]["ok"])
            self.assertTrue(d["supervision"]["data"]["audit"]["ok"])
            self.assertEqual(d["decision"]["data"]["session"], "2026-10-09")
            self.assertFalse(d["execution_multiasset_available"])
            self.assertEqual(self.request("GET", "/api/platform/overview")[0], 200)
        self.assertEqual(before, [inventory(root) for root in roots])

    def test_get_query_and_empty_states(self):
        for path in (
            "/api/platform/overview?x=1",
            "/api/platform/jobs?x=1&x=2",
            "/api/platform/global?id=../../src",
            "/api/platform/radar-view?mode=unknown",
        ):
            self.assertEqual(self.request("GET", path)[0], 400)
        self.assertEqual(api.public_global(self.payload()["id"])["state"], "NOT_PREPARED")
        with patch.object(api.forward, "portfolios", side_effect=ValueError("private")):
            d = api.overview()
            self.assertFalse(d["wallets"]["available"])
            self.assertNotIn("private", json.dumps(d))
        with patch.object(api.forward, "decision", return_value=None):
            self.assertIsNone(api.overview()["decision"]["data"])

    def test_radar_readiness_explains_each_missing_opinion(self):
        import pandas as pd

        root, day = self.suite / "radar", "2026-10-09"
        bars = api.radar.synthetic_bars(pd.Timestamp(day))

        class Extractor:
            def download(self, *args):
                return bars

            def source_description(self):
                return {"name": "FAKE_OFFICIAL_SOURCE_OFFLINE"}

            def _cotahist(self, year):
                return self

        with patch.object(api.radar, "read_cotahist", return_value=bars):
            api.radar.prepare(
                ["PETR4", "WEGE3", "BBAS3", "ELET3"],
                root,
                end=day,
                mode="live",
                extractor=Extractor(),
            )
        with patch.dict(api.os.environ, {"GEMINI_API_KEY": "offline-placeholder"}):
            token = api.radar.preflight(["ELET3"], root, day=day)["confirmation_token"]
            api.radar.run(
                ["ELET3"],
                token,
                root,
                day=day,
                authorize_paid=True,
                transport=api.radar.fake_gemini,
            )
        api.radar.write(
            root / "last_prepare.json",
            {
                "items": [
                    {
                        "ticker": "ITUB4",
                        "session": day,
                        "status": "BLOCKED",
                        "error": "ValueError: split-like mismatch between yfinance "
                        "and B3 closes: {2025: 0.97}",
                    }
                ]
            },
        )
        folder = api.radar.folder_for(root, "WEGE3", day)
        (folder / "bars.csv").write_bytes((folder / "bars.csv").read_bytes() + b"\n")
        api.radar.write(api.radar.folder_for(root, "BBAS3", day) / "claim.json", {})
        before = inventory(root)
        with patch.object(api.global_api, "OFFICIAL_RADAR", root):
            d = api.get(
                "radar-readiness",
                {"session": day, "tickers": "PETR4,VALE3,ITUB4,WEGE3,BBAS3"},
            )
            eligible = api.radar_readiness(day, ["ELET3"])
        states = {i["ticker"]: i["state"] for i in d["items"]}
        self.assertEqual(
            states,
            {
                "PETR4": "AWAITING_RADAR_AUTHORIZATION",
                "VALE3": "NO_INPUT",
                "ITUB4": "INPUT_BLOCKED",
                "WEGE3": "INTEGRITY_ERROR",
                "BBAS3": "RECOVERY_REQUIRED",
            },
        )
        itub = next(i for i in d["items"] if i["ticker"] == "ITUB4")
        self.assertEqual(itub["input_state"], "UNRESOLVED_DIVERGENCE")
        self.assertIn(
            "radar_corporate_events.py prepare --session 2026-10-09", d["prepare_command"]
        )
        self.assertFalse(d["global_pm_ready"])
        self.assertEqual(eligible["items"][0]["state"], "ELIGIBLE")
        self.assertTrue(eligible["global_pm_ready"])
        self.assertEqual(before, inventory(root))  # consulting never writes or claims

    def test_radar_and_global_authorizations_are_independent(self):
        p = self.prepare()
        root, day = self.suite / "radar", "2026-10-09"
        api.radar.prepare(["PETR4"], root, end=day, mode="synthetic")
        radar_token = api.radar.preflight(["PETR4"], root, day=day)["confirmation_token"]
        global_token = api.get("global-preflight", {"id": p["id"], "max_usd": "0.25"})[
            "confirmation_token"
        ]
        self.assertNotEqual(radar_token, global_token)
        payload = {
            "id": p["id"],
            "max_usd": "0.25",
            "confirmation_token": radar_token,
            "authorize_paid": False,
            "confirm": True,
        }
        self.assertEqual(self.post("run", payload)[0], 400)
        with self.assertRaisesRegex(ValueError, "preflight_or_confirmation_changed"):
            api.radar.run(["PETR4"], global_token, root, day=day)
        self.assertFalse(list(root.rglob("claim.json")))
        self.assertFalse((api.analysis_root(p["id"]) / "claim.json").exists())

    def test_get_routes_never_infer_or_write(self):
        roots = [ROOT / "data/forward", ROOT / "data/radar", ROOT / "data/portfolio"]
        before = [inventory(root) for root in roots]
        for path in (
            "/",
            "/api/platform/overview",
            "/api/platform/jobs",
            "/api/platform/radar-readiness?session=2026-10-09&tickers=PETR4,ITUB4",
            "/api/platform/radar-view?mode=CONSULTATIVE_SANDBOX",
            "/api/radar/status",
            "/api/global-pm/selection?mode=CONSULTATIVE_SANDBOX&session=2026-10-09&tickers=PETR4",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 200)
        self.assertEqual(before, [inventory(root) for root in roots])
        import check_platform

        text = check_platform.summary(api.overview())
        for title in (
            "[H2 original]",
            "[Supervisão]",
            "[Carteiras e benchmarks]",
            "[Radar oficial",
            "[Global PM]",
            "[Mercado]",
            "[Jobs incompletos, incertos ou bloqueados]",
            "[Integridade]",
            "[Ações manuais pendentes]",
        ):
            self.assertIn(title, text)
        self.assertEqual(before, [inventory(root) for root in roots])

    def test_attention_is_derived_and_ordered(self):
        import pandas as pd

        at = pd.Timestamp("2026-10-14 09:00", tz="America/Sao_Paulo")
        ok = lambda data: {"available": True, "data": data}  # noqa: E731
        d = {
            "decision": ok(
                {
                    "status": "DECIDED",
                    "session": "2026-10-09",
                    "target_session": "2026-10-13",
                }
            ),
            "supervision": ok({"selected": None}),
            "integrity": {"available": False},
            "official_selection": ok({"items": [], "missing": []}),
            "jobs": ok([]),
            "calendar": {"next_session": "2026-10-14", "expected_open": None},
            "last_observed_session": "2026-10-09",
            "last_closed_session": "2026-10-13",
            "global_records": [
                {
                    "id": "v7-" + "a" * 32,
                    "state": "PREPARED",
                    # 13/10 23:30 UTC is still 13/10 in BRT: earlier than ``at``.
                    "expires_at": "2026-10-13T23:30:00+00:00",
                    "href": "/portfolio",
                }
            ],
        }
        a = api.attention(d, at)
        self.assertEqual(a["level"], "blocked")
        self.assertIn("Integridade", a["next_action"])
        self.assertEqual([i["level"] for i in a["items"]], ["blocked", "action", "info"])
        self.assertIn("13/10/2026", a["items"][1]["text"])  # stale close to prepare
        self.assertIn("expirou", a["items"][2]["text"])
        self.assertFalse(a["data"]["current"])
        d["global_records"][0]["expires_at"] = "2026-10-14T12:30:00+00:00"  # 09:30 BRT
        self.assertNotIn("expirou", json.dumps(api.attention(d, at), ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()


def test_gemini_key_from_env_file_never_overrides_or_logs(tmp_path, monkeypatch, caplog):
    env = tmp_path / ".env"
    env.write_text("OTHER=x\nGEMINI_API_KEY=from-dotenv-placeholder\n", encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert server.load_gemini_key(env) == ".env"
    assert server.os.environ["GEMINI_API_KEY"] == "from-dotenv-placeholder"
    assert "OTHER" not in server.os.environ  # only the key is loaded
    monkeypatch.setenv("GEMINI_API_KEY", "from-terminal-placeholder")
    assert server.load_gemini_key(env) == "ambiente"
    assert server.os.environ["GEMINI_API_KEY"] == "from-terminal-placeholder"
    monkeypatch.setenv("GEMINI_API_KEY", " ")
    env.write_text("GEMINI_API_KEY=\n", encoding="utf-8")
    assert server.load_gemini_key(env) == "ausente"
    assert server.load_gemini_key(tmp_path / "missing.env") == "ausente"
    assert "placeholder" not in caplog.text
