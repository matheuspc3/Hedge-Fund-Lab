"""Offline checks: fake native Gemini only, no market/provider network."""

# ruff: noqa: E402 -- standalone checks establish repository imports.

import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import unittest
import uuid
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "dashboard"))
import multiasset_radar as radar
import radar_api
import server

DAY = "2026-10-09"
CONNECT = socket.create_connection


class RadarChecks(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "data/radar" / ("check-" + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.offline = radar.no_network()
        self.offline.__enter__()
        self.key = patch.dict(os.environ, {"GEMINI_API_KEY": "OFFLINE_TEST_NOT_A_SECRET"})
        self.key.start()

    def tearDown(self):
        self.key.stop()
        self.offline.__exit__(None, None, None)
        self.assertTrue(
            self.root.resolve().is_relative_to((ROOT / "data/radar").resolve())
        )
        shutil.rmtree(self.root)

    def prepare(self, values=None, day=DAY):
        values = values or list(radar.EXAMPLES)
        result = radar.prepare(values, self.root, end=day, mode="synthetic")
        self.assertTrue(all(i["status"] == "PREPARED" for i in result), result)

    def run_batch(self, values=None, *, replay=False, transport=None, budget=5):
        values = values or list(radar.EXAMPLES)
        report = radar.preflight(
            values, self.root, day=DAY, max_usd=budget, replay=replay
        )
        self.assertTrue(report["ready"], report)
        return radar.run(
            values,
            report["confirmation_token"],
            self.root,
            day=DAY,
            max_usd=budget,
            replay=replay,
            transport=transport,
        )

    def live(self, values=None):
        values = values or ["PETR4"]
        bars = radar.synthetic_bars(pd.Timestamp(DAY))

        class Extractor:
            def download(self, *args):
                return bars

            def source_description(self):
                return {"name": "FAKE_OFFICIAL_SOURCE_OFFLINE"}

            def _cotahist(self, year):
                return self

        with patch.object(radar, "read_cotahist", return_value=bars):
            result = radar.prepare(
                values, self.root, end=DAY, mode="live", extractor=Extractor()
            )
        self.assertTrue(all(i["status"] == "PREPARED" for i in result), result)

    def test_zero_one_five_selection_and_validation(self):
        for values in ([], ["petr4.sa"], list(radar.EXAMPLES)):
            self.assertEqual(radar.configure(values, self.root), radar.tickers(values))
        for values in (
            ["PETR4"] * 2,
            ["../PETR4"],
            [True],
            ["BTC"],
            ["AAPL"],
            ["XXXX99"],
            [*radar.EXAMPLES, "ABEV3"],
        ):
            with self.assertRaises(ValueError):
                radar.configure(values, self.root)
        with self.assertRaises(ValueError):
            radar.prepare([], self.root, mode="synthetic")
        with self.assertRaises(ValueError):
            radar.preflight([], self.root)

    def test_original_storage_and_path_traversal_refused(self):
        for root in (
            ROOT,
            ROOT / "data/forward/h2_v6_paper",
            ROOT / "data/raw",
            ROOT / "src",
        ):
            with self.assertRaises(ValueError):
                radar.configure(["PETR4"], root)
        for value in ("../2026-10-09", "2026-99-09", "2026-10-10", "2026-10-12"):
            with self.assertRaises(ValueError):
                radar.folder_for(self.root, "PETR4", value)

    def test_short_missing_nontrading_and_corporate_events(self):
        bars = radar.synthetic_bars(pd.Timestamp(DAY))
        for frame in (
            bars.tail(199),
            bars.drop(bars.index[-10]),
            bars.assign(volume=0),
            bars.assign(fechamento=float("nan")),
        ):
            with self.assertRaises(ValueError):
                radar.technical_input(frame)
        # Existing extractor is reused, including split/event guards; no replacement adjustment logic.
        self.assertIs(
            radar.RadarExtractor.download, radar.B3OfficialAdjustedExtractor.download
        )
        with patch.object(
            radar.RadarExtractor,
            "download",
            side_effect=ValueError("corporate event factor changes"),
        ):
            result = radar.prepare(["PETR4"], self.root, end=DAY)
        self.assertEqual(result[0]["status"], "BLOCKED")
        self.assertFalse((self.root / "analyses/PETR4" / DAY / "input.json").exists())

    def test_preflight_individual_batch_different_sessions_and_no_writes(self):
        self.prepare(["PETR4"])
        self.prepare(["VALE3"], "2026-10-08")
        before = self.tree()
        self.assertTrue(radar.preflight(["PETR4"], self.root, day=DAY)["ready"])
        report = radar.preflight(["PETR4", "VALE3"], self.root, day=DAY)
        self.assertFalse(report["ready"])
        self.assertTrue(report["items"][0]["ready"])
        self.assertFalse(report["items"][1]["ready"])
        self.assertEqual(before, self.tree())

    def tree(self):
        return {
            p.relative_to(self.root).as_posix(): radar.sha_file(p)
            for p in self.root.rglob("*")
            if p.is_file()
        }

    def test_five_complete_committees_and_read_only_lookup(self):
        self.prepare()
        results = self.run_batch()
        self.assertEqual([r["status"] for r in results], ["COMPLETED"] * 5)
        for row in results:
            self.assertEqual(len(row["votes"]), 5)
            self.assertEqual(row["tokens"]["thoughts_tokens"], 120)
            self.assertEqual(row["cost_usd"], 0)
            self.assertEqual(row["portfolio_risk"], "NOT_EVALUATED")
            self.assertEqual(row["portfolio_manager"], "NOT_INVOKED")
        before = self.tree()
        with patch.object(
            radar.RadarGeminiClient,
            "generate",
            side_effect=AssertionError("lookup called LLM"),
        ):
            self.assertEqual(len(radar.status(self.root)["items"]), 5)
            self.assertEqual(len(radar.detail("PETR4", DAY, self.root)["history"]), 3)
            replay = self.run_batch(replay=True)
            self.assertTrue(all(r["status"] == "COMPLETED" for r in replay))
        self.assertEqual(before, self.tree())

    def test_reinference_confirmation_and_frozen_tamper_refused(self):
        self.prepare(["PETR4"])
        with self.assertRaises(ValueError):
            radar.run(["PETR4"], "incorrect", self.root, day=DAY)
        self.run_batch(["PETR4"])
        report = radar.preflight(["PETR4"], self.root, day=DAY)
        self.assertFalse(report["ready"])
        with self.assertRaises(ValueError):
            radar.run(["PETR4"], report["confirmation_token"], self.root, day=DAY)
        path = self.root / "analyses/PETR4" / DAY / "bars.csv"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assertFalse(
            radar.preflight(["PETR4"], self.root, day=DAY, replay=True)["ready"]
        )
        with self.assertRaises(ValueError):
            radar.detail("PETR4", DAY, self.root)

    def test_partial_committee_failure_preserves_siblings_and_no_replacement(self):
        self.prepare(["PETR4", "VALE3"])
        calls = 0

        def flaky(*args):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise TimeoutError("uncertain response")
            return radar.fake_gemini(*args)

        results = self.run_batch(["PETR4", "VALE3"], transport=flaky)
        self.assertEqual(results[0]["status"], "FAILED_REPLAY_ONLY")
        self.assertEqual(results[1]["status"], "COMPLETED")
        partial = radar.detail("PETR4", DAY, self.root)
        self.assertEqual(len(partial["votes"]), 4)
        self.assertIsNone(partial["recommendation"])
        count = calls
        results = self.run_batch(
            ["PETR4", "VALE3"],
            replay=True,
            transport=lambda *args: self.fail("replay reached transport"),
        )
        self.assertEqual(results[0]["status"], "FAILED_REPLAY_ONLY")
        self.assertEqual(results[1]["status"], "COMPLETED")
        self.assertEqual(count, calls)

    def test_lost_claim_cannot_promote_existing_journal_to_fresh(self):
        self.prepare(["PETR4"])
        self.run_batch(["PETR4"])
        (self.root / "analyses/PETR4" / DAY / "claim.json").unlink()
        self.assertFalse(radar.preflight(["PETR4"], self.root, day=DAY)["ready"])

    def test_journal_loss_cannot_trigger_replacement_transport(self):
        self.prepare(["PETR4"])
        self.run_batch(["PETR4"])
        (self.root / "analyses/PETR4" / DAY / "calls.sqlite").unlink()
        result = self.run_batch(
            ["PETR4"],
            replay=True,
            transport=lambda *args: self.fail("missing journal caused inference"),
        )
        self.assertEqual(result[0]["status"], "FAILED_REPLAY_ONLY")

    def test_recover_durable_responses_after_publication_crash(self):
        self.prepare(["PETR4"])
        original = radar.write

        def crash(path, *args, **kwargs):
            if Path(path).name == "result.sha256":
                raise OSError("simulated crash before seal")
            return original(path, *args, **kwargs)

        with patch.object(radar, "write", side_effect=crash):
            self.assertEqual(self.run_batch(["PETR4"])[0]["status"], "FAILED_REPLAY_ONLY")
        result = self.run_batch(
            ["PETR4"],
            replay=True,
            transport=lambda *args: self.fail("recovery sent new inference"),
        )[0]
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(radar.detail("PETR4", DAY, self.root)["status"], "COMPLETED")

    def test_lock_prevents_second_process_and_is_released(self):
        self.prepare(["PETR4"])
        report = radar.preflight(["PETR4"], self.root, day=DAY)
        with radar._exclusive_state_lock(self.root / "operation"):
            with self.assertRaises(RuntimeError):
                radar.run(["PETR4"], report["confirmation_token"], self.root, day=DAY)
            with self.assertRaises(RuntimeError):
                radar.prepare(["VALE3"], self.root, end=DAY, mode="synthetic")
            process = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_multiasset_radar.py"),
                    "prepare",
                    "--root",
                    str(self.root),
                    "--tickers",
                    "VALE3",
                    "--session",
                    DAY,
                    "--synthetic",
                ],
                capture_output=True,
                timeout=30,
            )
            self.assertNotEqual(process.returncode, 0)
        self.assertFalse((self.root / "operation.lock").exists())
        self.assertEqual(self.run_batch(["PETR4"])[0]["status"], "COMPLETED")

    def test_request_concurrency_limit_and_journal_before_transport(self):
        self.prepare(["PETR4"])
        active = maximum = 0

        def observe(*args):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            folder = self.root / "analyses/PETR4" / DAY
            self.assertTrue((folder / "claim.json").exists())
            import sqlite3

            with closing(sqlite3.connect(folder / "calls.sqlite")) as db:
                self.assertGreater(
                    db.execute("SELECT count(*) FROM calls").fetchone()[0], 0
                )
                self.assertGreater(
                    db.execute("SELECT count(*) FROM attempts").fetchone()[0], 0
                )
            response = radar.fake_gemini(*args)
            active -= 1
            return response

        self.assertEqual(
            self.run_batch(["PETR4"], transport=observe)[0]["status"], "COMPLETED"
        )
        self.assertEqual(maximum, 1)

    def test_budget_global_missing_credentials_and_paid_consent(self):
        self.live(["PETR4", "VALE3"])
        report = radar.preflight(["PETR4", "VALE3"], self.root, day=DAY, max_usd=0.01)
        self.assertFalse(report["ready"])
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            self.assertFalse(radar.preflight(["PETR4"], self.root, day=DAY)["ready"])
        report = radar.preflight(["PETR4"], self.root, day=DAY)
        with self.assertRaisesRegex(ValueError, "explicit_paid_authorization_required"):
            radar.run(["PETR4"], report["confirmation_token"], self.root, day=DAY)
        self.assertFalse((self.root / "reservations").exists())
        result = radar.run(
            ["PETR4"],
            report["confirmation_token"],
            self.root,
            day=DAY,
            authorize_paid=True,
            transport=radar.fake_gemini,
        )[0]
        self.assertEqual(result["status"], "COMPLETED")
        self.assertGreater(result["cost_usd"], 0)
        self.assertAlmostEqual(radar.budget_used(self.root), report["usd_reserved"])
        radar.write(self.root / "reservations/exhausted.json", {"usd_reserved": 4.8})
        self.assertFalse(radar.preflight(["VALE3"], self.root, day=DAY)["ready"])
        for value in (True, float("nan"), -1, 0, 6, "5"):
            with self.assertRaises(ValueError):
                radar.preflight(["VALE3"], self.root, day=DAY, max_usd=value)

    def test_offline_network_guard(self):
        with self.assertRaises(RuntimeError):
            socket.create_connection(("example.com", 443))

    def test_original_artifacts_and_manifest_integrity(self):
        baseline = radar.read(
            ROOT / "docs/evidence/hfl_multiasset_radar/preservation_baseline.json"
        )
        for name, expected in baseline.items():
            path = ROOT / name
            if not path.exists() and name.startswith("data/forward/"):
                continue  # Local ignored records may be absent in a clean checkout.
            self.assertEqual(radar.sha_file(path), expected, name)
        from src.experiments.h2_evaluation_manifest import verify_manifest

        verify_manifest(
            radar.CANDIDATE,
            radar.CANDIDATE.with_suffix(".sha256").read_text().strip(),
            clean=False,
        )

    def test_http_origin_csrf_api_and_no_llm_on_get(self):
        self.prepare(["PETR4"])
        self.run_batch(["PETR4"])
        with patch.object(radar_api, "ROOT", self.root), patch.object(
            radar.RadarGeminiClient,
            "generate",
            side_effect=AssertionError("GET inferred"),
        ):
            with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
                thread = threading.Thread(target=httpd.serve_forever, daemon=True)
                thread.start()
                port = httpd.server_address[1]
                connection = http.client.HTTPConnection("127.0.0.1", port)
                # Only this loopback test connection bypasses create_connection's blanket guard.
                connection._create_connection = CONNECT
                try:
                    connection.request("GET", "/api/radar/status")
                    response = connection.getresponse()
                    state = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                    self.assertEqual(len(state["items"]), 1)
                    headers = {
                        "Origin": f"http://127.0.0.1:{port}",
                        "Content-Type": "application/json",
                        "X-CSRF-Token": state["csrf_token"],
                    }
                    connection.request(
                        "POST",
                        "/api/radar/universe",
                        json.dumps({"tickers": ["VALE3"]}),
                        headers,
                    )
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200, response.read())
                    headers["Origin"] = "https://attacker.invalid"
                    connection.request(
                        "POST", "/api/radar/universe", '{"tickers":[]}', headers
                    )
                    response = connection.getresponse()
                    response.read()
                    self.assertEqual(response.status, 403)
                    for url in (
                        "/radar",
                        "/radar.css",
                        "/radar.js",
                        "/api/radar/detail?ticker=PETR4&session=" + DAY,
                    ):
                        connection.request("GET", url)
                        response = connection.getresponse()
                        response.read()
                        self.assertEqual(response.status, 200)
                finally:
                    connection.close()
                    httpd.shutdown()
                    thread.join()


if __name__ == "__main__":
    (ROOT / "data/radar").mkdir(parents=True, exist_ok=True)
    unittest.main()
