"""V6 qualification: no external network, no real Gemini, no wallet writes."""

import copy
import http.client
import json
import os
import shutil
import socket
import sqlite3
import sys
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import global_pm_api as api  # noqa: E402
import multiasset_global_pm as pm  # noqa: E402
import multiasset_portfolio as b  # noqa: E402
import run_global_pm as cli  # noqa: E402
import server  # noqa: E402

from src.agents.llm_client import GeminiLLMClient  # noqa: E402
from src.experiments.h2_evaluation_offline import no_network  # noqa: E402
from src.experiments.h2_evaluation_production import JournalIntegrityError  # noqa: E402

DAY = "2026-10-09"
PRICES = {
    "PETR4": "40.00",
    "VALE3": "60.00",
    "ITUB4": "30.00",
    "WEGE3": "50.00",
    "BBAS3": "25.00",
}
CONNECT = socket.create_connection


def seal(value, **updates):
    return b.sealed({**{k: v for k, v in value.items() if k != "sha256"}, **updates})


def inventory(root):
    return {
        p.relative_to(root).as_posix(): b.sha_file(p)
        for p in root.rglob("*")
        if p.is_file() and p.suffix != ".lock"
    }


class GlobalPMChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = ROOT / "data/global_pm" / ("test-only-" + uuid.uuid4().hex)
        cls.output_patch = patch.object(pm, "OUTPUT", cls.suite)
        cls.output_patch.start()
        with no_network():
            cls.opinions, cls.histories = pm.load_opinions(
                ROOT / "data/radar/demo-v4", list(PRICES), DAY, "SYNTHETIC_DEMO", pm.now()
            )

    @classmethod
    def tearDownClass(cls):
        cls.output_patch.stop()
        assert cls.suite.resolve().parent == (ROOT / "data/global_pm").resolve()
        assert cls.suite.name.startswith("test-only-")
        shutil.rmtree(cls.suite, ignore_errors=True)

    def setUp(self):
        self.root = self.suite / ("check-" + uuid.uuid4().hex)
        self.offline = no_network()
        self.offline.__enter__()
        self.network = patch.object(
            GeminiLLMClient,
            "_default_transport",
            side_effect=AssertionError("REAL_GEMINI_FORBIDDEN"),
        )
        self.network.start()

    def tearDown(self):
        self.network.stop()
        self.offline.__exit__(None, None, None)

    def context(self, case="A", *, histories=None, opinions=None, mode="SYNTHETIC_DEMO"):
        holdings, cash = {}, "100000.00"
        if case == "B":
            holdings, cash = (
                {"PETR4": {"quantity": "1250", "basis": "50000.00"}},
                "50000.00",
            )
        elif case in "CE":
            holdings, cash = (
                {"PETR4": {"quantity": "500", "basis": "20000.00"}},
                "80000.00",
            )
        elif case == "D":
            holdings, cash = (
                {
                    t: {"quantity": q, "basis": cost}
                    for t, q, cost in (
                        ("PETR4", "1000", "40000.00"),
                        ("VALE3", "500", "30000.00"),
                        ("ITUB4", "700", "21000.00"),
                    )
                },
                "9000.00",
            )
        snapshot = pm.make_snapshot(self.root.name, mode, DAY, PRICES, holdings, cash)
        return cli.prepare(
            self.root,
            snapshot,
            opinions or self.opinions,
            histories or self.histories,
            ack_fixture_policy=True,
        )

    def proposal(self, c, case="A"):
        return cli.FakeGlobalPortfolioManager.propose(c, case)

    def report(self, c, p):
        return pm.validate(c, p, c["created_at"])

    def rejected(self, c, p, code):
        r = self.report(c, p)
        self.assertFalse(r["valid"], r)
        self.assertEqual(r["status"], "REJECTED_BY_VALIDATOR")
        self.assertIn(code, str(r["errors"]))
        return r

    def transport(self, response):
        calls = []

        def fake(*args):
            calls.append(args[-1])
            return cli.fake_response(response)

        return fake, calls

    def test_01_complete_read_only_opinions(self):
        before = inventory(ROOT / "data/radar/demo-v4")
        opinions, histories = pm.load_opinions(
            ROOT / "data/radar/demo-v4", list(PRICES), DAY, "SYNTHETIC_DEMO", pm.now()
        )
        self.assertEqual(len(opinions), 5)
        self.assertTrue(
            all(
                len(o["votes"]) == 5 and o["integrity"] == "VERIFIED_READ_ONLY"
                for o in opinions.values()
            )
        )
        self.assertTrue(all(len(h) >= 61 for h in histories.values()))
        self.assertEqual(before, inventory(ROOT / "data/radar/demo-v4"))

    def test_02_tampered_opinion(self):
        opinions = copy.deepcopy(self.opinions)
        opinions["PETR4"]["recommendation"] = "VENDA"
        with self.assertRaisesRegex(ValueError, "hash"):
            self.context(opinions=opinions)

    def test_03_incompatible_sessions(self):
        opinions = copy.deepcopy(self.opinions)
        opinions["PETR4"] = seal(opinions["PETR4"], session="2026-10-08")
        with self.assertRaisesRegex(ValueError, "incompatible"):
            self.context(opinions=opinions)

    def test_04_synthetic_official_mix(self):
        opinions = copy.deepcopy(self.opinions)
        opinions["PETR4"] = seal(opinions["PETR4"], mode="live")
        with self.assertRaisesRegex(ValueError, "synthetic_official_mix"):
            self.context(opinions=opinions)
        with self.assertRaisesRegex(ValueError, "synthetic_official_mix"):
            pm.load_opinions(
                ROOT / "data/radar/demo-v4",
                list(PRICES),
                DAY,
                "CONSULTATIVE_SANDBOX",
                pm.now(),
            )

    def test_05_missing_opinion_and_no_fallback(self):
        opinions = {t: o for t, o in self.opinions.items() if t != "BBAS3"}
        with self.assertRaisesRegex(ValueError, "missing_opinion"):
            self.context(opinions=opinions)
        with patch.object(api, "OFFICIAL_RADAR", self.suite / "no-official"):
            selected = api.selection("CONSULTATIVE_SANDBOX", DAY, list(PRICES))
        self.assertEqual(selected["missing"], list(PRICES))
        self.assertEqual(selected["status"], "INSUFFICIENT_DATA")

    def test_06_all_cash_snapshot(self):
        c = self.context()
        v = b.view(c["snapshot"]["financial_state"])
        self.assertEqual(b.dec(v["equity"]), 100000)
        self.assertEqual(b.dec(v["cash"]["available"]), 100000)
        self.assertEqual(b.dec(c["risk_current"]["volatility"]), 0)
        self.assertEqual(c["history_coverage"]["aligned_returns"], 60)
        self.assertFalse(c["execution_policy"]["enabled"])

    def test_07_partially_invested_increase(self):
        c = self.context("C")
        p = self.proposal(c)
        self.assertEqual(p["asset_reasoning"]["PETR4"]["action"], "INCREASE")
        self.assertTrue(self.report(c, p)["valid"])

    def test_08_multiple_buys(self):
        c = self.context()
        r = self.report(c, self.proposal(c))
        self.assertTrue(r["valid"], r["errors"])
        self.assertEqual(len(r["operations"]), 3)
        self.assertEqual(b.dec(r["projection"]["cash"]["available"]), b.dec("53954.00"))

    def test_09_partial_sale(self):
        c = self.context("C")
        r = self.report(c, self.proposal(c, "C"))
        self.assertEqual(r["projection"]["positions"]["PETR4"]["quantity"], "400")
        self.assertEqual(b.dec(r["projection"]["cash"]["receivable"]), 3996)

    def test_10_total_exit(self):
        c = self.context("C")
        p = self.proposal(c, "C")
        p["operations"][0].update(quantity="500", cost_ceiling="20.00")
        p.update(target_weights={t: "0" for t in PRICES}, target_cash_weight="1")
        p["asset_reasoning"]["PETR4"]["action"] = "EXIT"
        r = self.report(c, p)
        self.assertTrue(r["valid"], r["errors"])
        self.assertEqual(r["projection"]["positions"]["PETR4"]["quantity"], "0")
        self.assertEqual(b.dec(r["projection"]["cash"]["receivable"]), 19980)

    def test_11_sale_without_purchase(self):
        c = self.context("C")
        r = self.report(c, self.proposal(c, "C"))
        self.assertTrue(all(o["side"] == "SELL" for o in r["operations"]))
        self.assertEqual(b.dec(r["projection"]["cash"]["available"]), 80000)
        self.assertFalse(r["conditional_projection"])

    def test_12_preserve_cash_select_fewer_assets(self):
        c = self.context()
        p = self.proposal(c)
        self.assertEqual(set(p["not_selected"]), {"WEGE3", "BBAS3"})
        self.assertGreater(
            b.dec(self.report(c, p)["projection"]["cash"]["available"]), 50000
        )

    def test_13_rebalance_reduces_concentration(self):
        c = self.context("B")
        self.assertEqual(c["current_weights"]["PETR4"], "0.500000000000")
        r = self.report(c, self.proposal(c, "B"))
        self.assertTrue(r["valid"], r["errors"])
        self.assertLess(
            b.dec(r["projection"]["positions"]["PETR4"]["weight"]), b.dec("0.4")
        )

    def test_14_no_operations_preserves_finances(self):
        c = self.context("E")
        before = b.financial_hash(c["snapshot"]["financial_state"])
        p = self.proposal(c, "E")
        r = self.report(c, p)
        self.assertTrue(r["valid"], r["errors"])
        self.assertEqual(r["operations"], [])
        self.assertEqual(before, b.financial_hash(c["snapshot"]["financial_state"]))

    def test_15_invalid_weights(self):
        c = self.context()
        self.rejected(c, self.proposal(c, "F"), "weights_must_sum_to_one")
        p = self.proposal(c)
        p["target_weights"]["BBAS3"] = "-0.1"
        p["target_cash_weight"] = str(b.dec(p["target_cash_weight"]) + b.dec("0.1"))
        self.rejected(c, p, "negative_or_excessive")

    def test_16_insufficient_cash(self):
        c = self.context()
        p = self.proposal(c)
        p["operations"][0].update(quantity="3000", cost_ceiling="120.00")
        self.rejected(c, p, "insufficient_settled_cash")

    def test_17_nonexistent_units(self):
        c = self.context("C")
        p = self.proposal(c, "C")
        p["operations"][0].update(quantity="501", cost_ceiling="25.00")
        self.rejected(c, p, "insufficient_available_units")

    def test_18_excessive_concentration(self):
        c = self.context()
        p = self.proposal(c)
        p["operations"][0].update(quantity="1100", cost_ceiling="44.00")
        self.rejected(c, p, "concentration_or_exposure_limit")

    def test_19_global_volatility_veto(self):
        histories = {
            t: [[day, "100" if i % 2 else "200"] for i, (day, _) in enumerate(rows)]
            for t, rows in self.histories.items()
        }
        c = self.context(histories=histories)
        self.rejected(c, self.proposal(c), "global_risk_blocked")

    def test_20_insufficient_or_future_covariance_history(self):
        histories = copy.deepcopy(self.histories)
        histories["PETR4"] = histories["PETR4"][-60:]
        with self.assertRaisesRegex(ValueError, "insufficient_covariance"):
            self.context(histories=histories)
        histories = copy.deepcopy(self.histories)
        histories["PETR4"].append(["2026-10-14", "42"])
        with self.assertRaisesRegex(ValueError, "insufficient_covariance"):
            self.context(histories=histories)

    def test_21_settlement_dependency_is_conditional(self):
        c = self.context("D")
        before = b.financial_hash(c["snapshot"]["financial_state"])
        r = self.report(c, self.proposal(c, "D"))
        self.assertTrue(r["valid"], r["errors"])
        self.assertEqual(len(r["financial_validation"]["deferred_operations"]), 1)
        self.assertNotIn("WEGE3", r["projection"]["positions"])
        self.assertEqual(
            r["conditional_projection"]["positions"]["WEGE3"]["quantity"], "250"
        )
        self.assertEqual(b.dec(r["projection"]["cash"]["available"]), 9000)
        self.assertEqual(before, b.financial_hash(c["snapshot"]["financial_state"]))

    def test_22_integer_weight_sizing_and_costs(self):
        c = self.context()
        p = self.proposal(c)
        p.update(
            target_weights={
                "PETR4": "0.20",
                "VALE3": "0.20",
                "ITUB4": "0.15",
                "WEGE3": "0",
                "BBAS3": "0",
            },
            target_cash_weight="0.45",
        )
        for op in p["operations"]:
            op.update(quantity=None, cost_ceiling="100.00")
        r = self.report(c, p)
        self.assertTrue(r["valid"], r["errors"])
        self.assertEqual(
            {op["ticker"]: op["quantity"] for op in r["operations"]},
            {"PETR4": "499", "VALE3": "333", "ITUB4": "499"},
        )
        self.assertEqual(
            b.dec(r["financial_validation"]["estimated_costs"]), b.dec("54.91")
        )
        p["operations"][0]["quantity"] = "0.5"
        self.rejected(c, p, "whole_positive_units")

    def test_23_state_change_after_proposal(self):
        c = self.context()
        changed = seal(c["snapshot"], observed_at=pm.now())
        r = pm.validate(c, self.proposal(c), c["created_at"], current_snapshot=changed)
        self.assertIn("snapshot_changed", str(r["errors"]))
        p = self.proposal(c)
        p["snapshot_sha256"] = "0" * 64
        self.rejected(c, p, "proposal_hash_mismatch")

    def test_24_expired_proposal_and_preflight(self):
        c = self.context()
        future = (b.instant(c["expires_at"]) + timedelta(seconds=1)).isoformat()
        self.assertIn(
            "proposal_expired", str(pm.validate(c, self.proposal(c), future)["errors"])
        )
        self.assertFalse(cli.preflight(self.root, at=future)["ready"])

    def test_25_llm_schema_failure_durable_no_retry(self):
        self.context()
        transport, calls = self.transport({"unknown": "invalid"})
        report = cli.preflight(self.root)
        with self.assertRaises(RuntimeError):
            cli.run(self.root, report["confirmation_token"], transport=transport)
        with self.assertRaises(RuntimeError):
            cli.run(self.root, replay=True, transport=transport)
        self.assertEqual(len(calls), 1)
        with closing(sqlite3.connect(self.root / "private/calls.sqlite")) as db:
            row = db.execute("SELECT raw,record FROM calls").fetchone()
            self.assertIsNotNone(row[0])
            self.assertIsNotNone(row[1])
        self.assertEqual(cli.detail(self.root)["status"], "REJECTED_BY_VALIDATOR")

    def test_26_impossible_response_rejected_without_retry(self):
        c = self.context()
        transport, calls = self.transport(self.proposal(c, "F"))
        r = cli.run(
            self.root, cli.preflight(self.root)["confirmation_token"], transport=transport
        )
        self.assertEqual(r["status"], "REJECTED_BY_VALIDATOR")
        self.assertEqual(len(calls), 1)
        self.assertEqual(r["cost_usd"], "0")

    def test_27_duplicate_and_concurrent_inference_blocked(self):
        c = self.context()
        token = cli.preflight(self.root)["confirmation_token"]
        transport, calls = self.transport(self.proposal(c))

        def attempt():
            try:
                return cli.run(self.root, token, transport=transport)["status"]
            except (ValueError, RuntimeError):
                return "BLOCKED"

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: attempt(), range(2)))
        self.assertCountEqual(outcomes, ["VALID_PROPOSAL", "BLOCKED"])
        self.assertEqual(len(calls), 1)
        self.assertFalse(cli.preflight(self.root)["ready"])

    def test_28_crashes_before_journal_and_after_journal(self):
        c = self.context()
        transport, calls = self.transport(self.proposal(c))
        with self.assertRaises(cli.SimulatedCrash):
            cli.run(
                self.root,
                cli.preflight(self.root)["confirmation_token"],
                transport=transport,
                crash="after_claim",
            )
        with self.assertRaises(ValueError):
            cli.run(self.root, replay=True, transport=transport)
        self.assertEqual(len(calls), 0)
        self.root = self.suite / ("crash-" + uuid.uuid4().hex)
        c = self.context()
        transport, calls = self.transport(self.proposal(c))
        with self.assertRaises(cli.SimulatedCrash):
            cli.run(
                self.root,
                cli.preflight(self.root)["confirmation_token"],
                transport=transport,
                crash="before_transport",
            )
        with self.assertRaises(JournalIntegrityError):
            cli.run(self.root, replay=True, transport=transport)
        self.assertEqual(len(calls), 0)
        self.assertEqual(cli.detail(self.root)["status"], "RECOVERY_REQUIRED")

    def test_29_replay_after_envelope_or_before_result_no_call(self):
        for crash in ("after_envelope", "before_result"):
            with self.subTest(crash=crash):
                self.root = self.suite / ("replay-" + uuid.uuid4().hex)
                c = self.context()
                transport, calls = self.transport(self.proposal(c))
                with self.assertRaises(cli.SimulatedCrash):
                    cli.run(
                        self.root,
                        cli.preflight(self.root)["confirmation_token"],
                        transport=transport,
                        crash=crash,
                    )
                r = cli.run(self.root, replay=True, transport=transport)
                self.assertEqual(r["status"], "VALID_PROPOSAL")
                self.assertEqual(len(calls), 1)
                result_hash = b.sha_file(self.root / "result.json")
                cli.run(self.root, replay=True, transport=transport)
                self.assertEqual(result_hash, b.sha_file(self.root / "result.json"))

    def test_30_read_only_http_and_private_allowlist(self):
        indexroot = self.suite / ("demo-http-" + uuid.uuid4().hex)
        cli.demo(indexroot)
        before = inventory(self.suite)
        with patch.object(api, "ROOT", indexroot):
            httpd = server.socketserver.ThreadingTCPServer(
                ("127.0.0.1", 0), server.Handler
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            try:
                with patch.object(socket, "create_connection", CONNECT):
                    for url in (
                        ["/api/global-pm/status"]
                        + ["/api/global-pm/case?case=" + c for c in "ABCDEF"]
                        + ["/api/global-pm/simulate?case=D"]
                    ):
                        connection = http.client.HTTPConnection(
                            "127.0.0.1", httpd.server_address[1]
                        )
                        connection.request("GET", url)
                        response = connection.getresponse()
                        self.assertEqual(response.status, 200, response.read())
                        connection.close()
                    for url in (
                        "/data/global_pm/private/calls.sqlite",
                        "/api/global-pm/case?case=A&case=B",
                        "/api/global-pm/case?case=../../src",
                    ):
                        connection = http.client.HTTPConnection(
                            "127.0.0.1", httpd.server_address[1]
                        )
                        connection.request("GET", url)
                        self.assertIn(connection.getresponse().status, (400, 404))
                        connection.close()
                    connection = http.client.HTTPConnection(
                        "127.0.0.1", httpd.server_address[1]
                    )
                    connection.request(
                        "GET",
                        "/api/global-pm/status",
                        headers={"Origin": "https://evil.example"},
                    )
                    self.assertEqual(connection.getresponse().status, 403)
                    connection.close()
                    for command in ("run", "execute"):
                        connection = http.client.HTTPConnection(
                            "127.0.0.1", httpd.server_address[1]
                        )
                        connection.request(
                            "POST",
                            "/api/global-pm/" + command,
                            "{}",
                            headers={
                                "Origin": f"http://127.0.0.1:{httpd.server_address[1]}",
                                "Content-Type": "application/json",
                                "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
                            },
                        )
                        self.assertEqual(connection.getresponse().status, 404)
                        connection.close()
            finally:
                httpd.shutdown()
                httpd.server_close()
        self.assertEqual(before, inventory(self.suite))

    def test_31_original_ledgers_preserved(self):
        expected = json.loads(
            (ROOT / "docs/evidence/hfl_global_pm/preservation_baseline.json").read_text(
                encoding="utf-8"
            )
        )
        changed = [
            name
            for name, sha in expected.items()
            if not (ROOT / name).is_file() or b.sha_file(ROOT / name) != sha
        ]
        self.assertEqual(changed, [])

    def test_32_scientific_identity_and_v5_seals(self):
        import run_h2_v6_forward as forward

        sha, _ = forward.identity(clean=False)
        self.assertEqual(
            sha, "dc118ce9841df612d030f40e5993858eacc6d06e41eff173706fc3a72d3acb98"
        )
        self.assertTrue(b.Store(b.OUTPUT / "demo-qualified-v5").verify()["ok"])

    def test_33_unsupported_evidence_and_action_mismatch(self):
        c = self.context()
        p = self.proposal(c)
        p["asset_reasoning"]["PETR4"]["evidence_codes"] = ["INVENTED_NEWS"]
        self.rejected(c, p, "unsupported_explanation_reference")
        p = self.proposal(c)
        p["asset_reasoning"]["PETR4"]["action"] = "EXIT"
        self.rejected(c, p, "explanation_action_inconsistent")

    def test_34_budget_confirmation_and_policy_required(self):
        c = self.context()
        self.assertEqual(cli.preflight(self.root)["usd_reserved"], "0")
        self.assertEqual(b.dec(cli.estimate(c)["usd_reserved"]), b.dec("0.159744"))
        with self.assertRaisesRegex(ValueError, "confirmation_changed"):
            cli.run(self.root, "bad-confirmation")
        self.assertFalse((self.root / "claim.json").exists())
        with self.assertRaisesRegex(ValueError, "acknowledgment_required"):
            pm.freeze(c["snapshot"], self.opinions, self.histories, "unapproved")
        with self.assertRaisesRegex(ValueError, "root_required"):
            pm.root_path(ROOT / "data/forward")

    def test_35_prompt_minimization_and_unique_global_request(self):
        c = self.context()
        text = pm.prompt_input(c)
        self.assertNotIn("GEMINI_API_KEY", text)
        self.assertNotIn("raw_base64", text)
        self.assertNotIn("system_prompt", text)
        self.assertNotIn('"histories":', text)
        transport, calls = self.transport(self.proposal(c))
        cli.run(
            self.root, cli.preflight(self.root)["confirmation_token"], transport=transport
        )
        self.assertEqual(len(calls), 1)
        self.assertIn(
            "GlobalProposal",
            json.dumps(calls[0]["generationConfig"]["responseJsonSchema"]),
        )

    def test_36_consultative_budget_and_new_authorization_gate(self):
        opinions = {
            t: seal(
                o,
                mode="live",
                raw_close=PRICES[t],
                source_family="TEST_ONLY_OFFICIAL_SOURCE_FIXTURE",
            )
            for t, o in self.opinions.items()
        }
        self.context(opinions=opinions, mode="CONSULTATIVE_SANDBOX")
        report = cli.preflight(self.root)
        self.assertTrue(report["paid"])
        self.assertEqual(b.dec(report["usd_reserved"]), b.dec("0.159744"))
        self.assertFalse(cli.preflight(self.root, "0.10")["ready"])
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "new_explicit_paid_authorization"):
                cli.run(self.root, report["confirmation_token"])
            with self.assertRaisesRegex(ValueError, "new_explicit_paid_authorization"):
                cli.run(self.root, report["confirmation_token"], authorize_paid=True)
        self.assertFalse((self.root / "claim.json").exists())
        reserve = (
            pm.OUTPUT / "reservations" / ("test-budget-" + uuid.uuid4().hex + ".json")
        )
        b.write(
            reserve,
            b.sealed({"identity": pm.IDENTITY, "usd_reserved": "4.90"}),
            immutable=True,
        )
        self.assertIn("budget_exceeded", cli.preflight(self.root)["errors"])

    def test_37_context_journal_and_response_tampering(self):
        c = self.context()
        transport, _ = self.transport(self.proposal(c))
        cli.run(
            self.root, cli.preflight(self.root)["confirmation_token"], transport=transport
        )
        result_path = self.root / "result.json"
        result = b.read(result_path)
        result["response"]["summary"] = "tampered"
        b.write(result_path, result)
        with self.assertRaisesRegex(ValueError, "hash"):
            cli.detail(self.root)
        c["opinions"]["PETR4"]["recommendation"] = "VENDA"
        with self.assertRaisesRegex(ValueError, "hash"):
            pm.checked_context(c)

    def test_38_uncertain_provider_and_live_stale_locks(self):
        self.context()
        calls = []

        def uncertain(*args):
            calls.append(1)
            raise ConnectionError("uncertain native response")

        with self.assertRaises(ConnectionError):
            cli.run(
                self.root,
                cli.preflight(self.root)["confirmation_token"],
                transport=uncertain,
            )
        self.assertEqual(cli.detail(self.root)["status"], "RECOVERY_REQUIRED")
        with self.assertRaises(ConnectionError):
            cli.run(self.root, replay=True, transport=uncertain)
        self.assertEqual(len(calls), 1)
        path = self.root / "qualification-only.lock"
        path.write_text(str(os.getpid()), encoding="utf-8")
        self.assertTrue(cli.active_lock(path))
        path.write_text("0", encoding="utf-8")
        self.assertFalse(cli.active_lock(path))

    def test_39_manual_snapshot_boundary_and_read_only_states(self):
        c = self.context("C")
        snap = copy.deepcopy(c["snapshot"])
        snap["financial_state"]["positions"]["PETR4"]["reserved"] = "-100"
        snap = seal(snap, state_sha256=b.financial_hash(snap["financial_state"]))
        with self.assertRaisesRegex(ValueError, "invalid_hypothetical_availability"):
            pm.calculation_context(snap, self.opinions, self.histories)
        with patch.object(api, "ROOT", self.root):
            before = inventory(self.root)
            self.assertEqual(
                api.get("status", {})["prepared"]["status"], "AWAITING_PREFLIGHT"
            )
            self.assertTrue(api.get("preflight", {"max_usd": "0.25"})["ready"])
            self.assertEqual(before, inventory(self.root))
        self.assertEqual(
            cli.detail(self.suite / "missing-analysis")["status"], "NO_PROPOSAL"
        )


if __name__ == "__main__":
    unittest.main()
