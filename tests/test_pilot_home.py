"""UX-M3/M5: real exported PAPER-02, pure metrics, HTTP and selection races."""

import copy
import http.client
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]

import pilot_api as api  # noqa: E402
import prepare_pilot_demo as prepare  # noqa: E402
import server  # noqa: E402

b = api.b


def calendar(days):
    body = {
        "nature": "SYNTHETIC_TEST",
        "source": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
        "file_sha256": "0" * 64,
        "sessions": days,
    }
    return {**body, "sha256": api.data.digest(body)}


def history(days):
    return [
        {"session": day, "view": {"equity": str(100 + i), "initial_capital": "100"}}
        for i, day in enumerate(days)
    ]


class MetricChecks(unittest.TestCase):
    def setUp(self):
        self.days = [
            "2023-02-28",
            "2023-12-29",
            "2024-02-28",
            "2024-02-29",
            "2024-12-30",
            "2024-12-31",
            "2025-01-02",
            "2025-01-31",
            "2025-02-03",
            "2025-12-31",
            "2026-01-02",
        ]
        self.calendar = calendar(self.days)
        self.history = history(self.days)

    def test_month_anchor_and_formula(self):
        metric = api.periods(self.history, self.calendar, "2025-02-03")["month"]
        self.assertEqual(metric["status"], "AVAILABLE")
        self.assertEqual(metric["anchor_session"], "2025-01-31")
        self.assertEqual(b.dec(metric["change_brl"]), 1)
        self.assertEqual(b.dec(metric["change_pct"]), (b.dec(108) / 107 - 1) * 100)

    def test_year_anchor_and_year_transition(self):
        first = api.periods(self.history, self.calendar, "2025-01-02")["year"]
        self.assertEqual(first["anchor_session"], "2024-12-31")
        next_year = api.periods(self.history, self.calendar, "2026-01-02")["year"]
        self.assertEqual(next_year["anchor_session"], "2025-12-31")
        self.assertEqual(next_year["status"], "AVAILABLE")

    def test_civil_twelve_months_and_leap_day_not_ytd(self):
        metrics = api.periods(self.history, self.calendar, "2024-02-29")
        self.assertEqual(metrics["last_12_months"]["anchor_session"], "2023-02-28")
        self.assertEqual(metrics["last_12_months"]["status"], "AVAILABLE")
        self.assertNotEqual(
            metrics["last_12_months"]["anchor_session"], metrics["year"]["anchor_session"]
        )

    def test_short_history_has_labelled_partial(self):
        short = self.history[-2:]
        result = api.periods(short, self.calendar, "2026-01-02")
        self.assertEqual(result["last_12_months"]["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(
            result["last_12_months"]["partial"]["label"], "Desde o início (parcial)"
        )
        self.assertEqual(b.dec(result["since_start"]["change_brl"]), 10)

    def test_missing_anchor_is_not_replaced_by_older_snapshot(self):
        rows = [h for h in self.history if h["session"] != "2025-01-31"]
        metric = api.periods(rows, self.calendar, "2025-02-03")["month"]
        self.assertEqual(metric["anchor_session"], "2025-01-31")
        self.assertEqual(metric["status"], "UNAVAILABLE")
        self.assertIsNone(metric["change_brl"])

    def test_internal_gap_blocks_period(self):
        rows = [h for h in self.history if h["session"] != "2025-01-02"]
        metric = api.periods(rows, self.calendar, "2025-02-03")["year"]
        self.assertEqual(metric["status"], "UNAVAILABLE")
        self.assertIn("2025-01-02", metric["missing_sessions"])

    def test_initial_baseline_and_missing_session(self):
        result = api.periods(self.history, self.calendar, self.days[0])
        self.assertEqual(result["day"]["status"], "INSUFFICIENT_HISTORY")
        self.assertIsNone(result["day"]["change_pct"])
        result = api.periods(self.history[:-1], self.calendar, self.days[-1])
        self.assertEqual(result["since_start"]["status"], "SESSION_UNAVAILABLE")

    def test_calendar_coverage_not_extrapolated(self):
        short = calendar(self.days[-2:])
        metric = api.periods(self.history[-2:], short, "2026-01-02")["last_12_months"]
        self.assertIsNone(metric["anchor_session"])
        self.assertEqual(metric["status"], "INSUFFICIENT_HISTORY")


class HomeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        cls.addClassCleanup(cls.stack.close)
        cls.root = Path(
            cls.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="hfl-home-checks-")
            )
        )
        cls.base = prepare.prepare(cls.root / "export.json")
        cls.raw = cls.base.read_bytes()
        cls.artifact = json.loads(cls.raw)

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="hfl-home-request-")
            )
        )
        self.path = self.root / "demo.json"
        self.path.write_bytes(self.raw)
        self.stack.enter_context(patch.object(api, "demo_path", return_value=self.path))

    def get(self, **values):
        return api.get({"demo": "1", **values})

    def test_explicit_demo_default_empty_and_preparation_idempotent(self):
        self.assertEqual(api.get({})["status"], "NOT_STARTED")
        self.assertEqual(api.get({})["wallets"], [])
        before = self.path.read_bytes()
        prepare.prepare(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_verified_wallet_session_and_no_crossed_values(self):
        agents = self.get()
        reference_id = agents["wallets"][1]["id"]
        reference = self.get(wallet=reference_id)
        self.assertEqual(agents["summary"]["equity"], "100039.36")
        self.assertEqual(reference["summary"]["equity"], "101744.07")
        self.assertEqual(reference["summary"]["position_count"], 5)
        self.assertEqual(agents["summary"]["position_count"], 1)
        earlier = self.get(wallet=reference_id, session="2026-11-03", period="day")
        self.assertEqual(earlier["summary"]["equity"], "100000.00")
        self.assertEqual(earlier["trades"], [])
        self.assertTrue(all(a["position"] is None for a in earlier["assets"]))
        self.assertEqual(earlier["periods"]["day"]["status"], "INSUFFICIENT_HISTORY")

    def test_assets_prices_position_changes_and_initial_targets(self):
        agents = self.get(session="2026-11-10")
        petr = next(a for a in agents["assets"] if a["ticker"] == "PETR4")
        self.assertEqual(petr["price_change"]["change_brl"], "0.10")
        self.assertEqual(petr["position_value_change"], "-1612.00")
        self.assertNotEqual(
            petr["price_change"]["change_brl"], petr["position_value_change"]
        )
        self.assertEqual(len(agents["assets"]), 5)
        self.assertEqual(sum(a["position"] is None for a in agents["assets"]), 4)
        reference = self.get(wallet=agents["wallets"][1]["id"])
        self.assertTrue(all(a["initial_target"] == "0.20" for a in reference["assets"]))
        self.assertTrue(
            any(a["position"]["weight"] != "0.20" for a in reference["assets"])
        )

    def test_decisions_and_trades_cut_off_at_selected_session(self):
        earlier = self.get(session="2026-11-03")
        self.assertEqual(earlier["decision"]["action"], "HOLD")
        self.assertEqual(earlier["trades"], [])
        later = self.get(session="2026-11-05")
        self.assertEqual(len(later["trades"]), 1)
        self.assertEqual(later["trades"][0]["side"], "BUY")
        self.assertLess(
            later["trades"][0]["decision_session"], later["trades"][0]["session"]
        )

    def test_period_selection_and_current_reference_is_reconciled(self):
        d = self.get(period="month")
        self.assertEqual(d["session"], "2026-11-12")
        self.assertEqual(d["period"], "month")
        self.assertEqual(d["periods"]["month"]["anchor_session"], "2026-10-30")
        self.assertEqual(d["periods"]["month"]["status"], "INSUFFICIENT_HISTORY")
        self.assertEqual(d["periods"]["day"]["change_brl"], "6.00")
        missing = self.get(session="2026-11-13")
        self.assertEqual(missing["status"], "SESSION_UNAVAILABLE")
        self.assertIsNone(missing["summary"])

    def test_comparison_includes_null_gaps(self):
        artifact, states = api.read_demo(self.path)
        del artifact
        pid = next(iter(states))
        state = states[pid][0]
        state["history"] = [h for h in state["history"] if h["session"] != "2026-11-05"]
        c = api.comparison(states, state["calendar"], "2026-11-12")
        index = c["sessions"].index("2026-11-05")
        self.assertIsNone(c["series"][0]["points"][index]["value"])
        self.assertIsNotNone(c["series"][1]["points"][index]["value"])
        self.assertEqual(b.dec(c["series"][0]["points"][0]["value"]), 100)

    def test_pending_session_keeps_last_reconciled_reference_and_empty_history(self):
        artifact, states = api.read_demo(self.path)
        state = next(iter(states.values()))[0]
        state["valuation_unavailable"] = True
        state["last_economic_at"] = "2026-11-13T18:00:00-03:00"
        with patch.object(api, "read_demo", return_value=(artifact, states)):
            result = self.get()
            self.assertEqual(result["session"], "2026-11-12")
            self.assertEqual(result["pending_session"], "2026-11-13")
            self.assertEqual(result["summary"]["equity"], "100039.36")
            state["history"] = []
            self.assertEqual(self.get()["status"], "EMPTY_HISTORY")
            self.assertNotIn("summary", self.get())

    def test_missing_and_corrupt_export_do_not_fallback(self):
        self.path.unlink()
        self.assertEqual(self.get()["status"], "DEMO_NOT_PREPARED")
        self.assertFalse(self.path.exists())
        self.path.write_text('{"broken":true}', encoding="utf-8")
        self.assertEqual(self.get()["status"], "INTEGRITY_INVALID")
        self.assertNotIn("summary", self.get())

    def test_resealed_schema_identity_classification_or_projection_rejected(self):
        for field, value in (
            ("schema_version", 2),
            ("identity", "official"),
            ("classification", "PAPER_ACTIVE"),
            ("official_activation", True),
        ):
            artifact = copy.deepcopy(self.artifact)
            artifact[field] = value
            artifact = b.sealed({k: v for k, v in artifact.items() if k != "sha256"})
            self.path.write_text(json.dumps(artifact), encoding="utf-8")
            self.assertEqual(self.get()["status"], "INTEGRITY_INVALID")
        artifact = copy.deepcopy(self.artifact)
        artifact["projection"]["wallets"][0]["summary"]["equity"] = "999999.00"
        artifact = b.sealed({k: v for k, v in artifact.items() if k != "sha256"})
        self.path.write_text(json.dumps(artifact), encoding="utf-8")
        self.assertEqual(self.get()["status"], "INTEGRITY_INVALID")

    def test_query_invalid_and_no_path_parameter(self):
        for query in (
            {"demo": "1", "path": "C:/private"},
            {"demo": "1", "period": "252"},
            {"demo": "1", "wallet": "h2:ai"},
            {"demo": "1", "session": "2026-11-08"},
            {"wallet": "anything"},
            {"demo": "true"},
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                api.get(query)

    def test_get_does_not_write_create_sqlite_qualify_or_call_network(self):
        import qualify_pilot_paper as qualifier

        before = self.path.read_bytes()
        with patch.object(
            qualifier, "run", side_effect=AssertionError("qualifier on GET")
        ), patch.object(
            api.pilot.Store, "create", side_effect=AssertionError("SQLite on GET")
        ), patch.object(
            socket.socket, "connect", side_effect=AssertionError("network on GET")
        ):
            d = self.get()
            self.assertTrue(d["read_only"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertNotIn("journals", json.dumps(d))
        self.assertNotIn("risk_fixture", json.dumps(d))

    def test_http_route_queries_static_compatibility_and_no_writes(self):
        httpd = server.ReusableTCPServer(("127.0.0.1", 0), server.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:

            def request(path):
                c = http.client.HTTPConnection(
                    "127.0.0.1", httpd.server_address[1], timeout=20
                )
                c.request("GET", path)
                r = c.getresponse()
                result = r.status, r.read()
                c.close()
                return result

            before = self.path.read_bytes()
            status, body = request("/api/portfolio/pilot?demo=1")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["classification"], "SYNTHETIC_TEST")
            self.assertEqual(request("/api/portfolio/pilot?demo=1&demo=1")[0], 400)
            self.assertEqual(request("/api/portfolio/pilot?demo=1&path=x")[0], 400)
            for path in ("/", "/?demo=1", "/portfolio", "/paper", "/vendor/chart.umd.js"):
                self.assertEqual(request(path)[0], 200)
            self.assertEqual(request("/pilot_api.py")[0], 404)
            self.assertEqual(self.path.read_bytes(), before)
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(5)

    def test_actual_js_ignores_old_replies_and_clears_error_balances(self):
        source = ROOT / "tests/pilot_home_ui_check.js"
        views = [
            self.get(),
            self.get(wallet="paper02-equal-weight-reference", period="month"),
        ]
        path = self.root / "views.json"
        path.write_text(json.dumps(views), encoding="utf-8")
        result = subprocess.run(
            [
                shutil.which("node") or "node",
                str(source),
                str(ROOT / "dashboard/platform.js"),
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
