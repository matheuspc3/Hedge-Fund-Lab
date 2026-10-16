"""V7.6 protocol: audit, erratum, scenario qualification, plan, gates. Offline only."""

import copy
import json
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import experiment_protocol_v76 as x  # noqa: E402
import multiasset_global_pm_v2 as pm  # noqa: E402
import verify_consolidation_v75 as v75  # noqa: E402

from src.agents.llm_client import GeminiLLMClient  # noqa: E402
from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

LOCAL = (x.V2_REAL / "result.json").exists() and (
    x.OUT / "READINESS_REPORT.json"
).exists()


class PureRules(unittest.TestCase):
    # 5 — absent, null and explicit zero are different facts.
    def test_05_absent_null_and_zero_are_distinct(self):
        key = "thoughtsTokenCount"
        self.assertEqual(x.field_state({}, key), "ABSENT")
        self.assertEqual(x.field_state({key: None}, key), "NULL")
        self.assertEqual(x.field_state({key: 0}, key), "ZERO")
        self.assertEqual(x.field_state({key: 7}, key), "VALUE")

    # 31 — planned rates are reproducible and refuse tiny samples.
    def test_31_rates_are_reproducible_and_guarded(self):
        self.assertEqual(x.rate(1, 2, 10)["status"], "INSUFFICIENT_SAMPLE")
        self.assertIsNone(x.rate(1, 2, 10)["value"])
        first, second = x.rate(9, 10, 10), x.rate(9, 10, 10)
        self.assertEqual(first, second)
        low, high = first["wilson95"]
        self.assertTrue(0 <= low < 0.9 < high <= 1)
        self.assertEqual(x.zero_event_upper_bound(29), 0.098145)

    # 30 — zero weights are a decision; a rejected response is not.
    def test_30_zero_weight_decisions_compare_and_rejections_do_not(self):
        cash = {"BBAS3": 0, "PETR4": 0}

        def made(status, cash_weight="1"):
            return x.decision(
                {
                    "status": status,
                    "response": {
                        "target_weights": {t: str(w) for t, w in cash.items()},
                        "target_cash_weight": cash_weight,
                        "asset_reasoning": {t: {"action": "NOT_SELECTED"} for t in cash},
                        "operations": [],
                        "watchlist_candidates": [],
                    },
                }
            )

        a, b = made("VALID_PROPOSAL", "1.0"), made("VALID_PROPOSAL", "1.00")
        same = x.compare(a, b)
        self.assertEqual(
            (same["weight_l1"], same["action_agreement"], same["both_all_cash"]),
            ("0", "2/2", True),
        )
        self.assertIsNone(same["watchlist_jaccard"])
        rejected = made("REJECTED_BY_VALIDATOR")
        self.assertFalse(x.compare(a, rejected)["comparable"])
        self.assertEqual(
            x.compare(a, rejected, raw_intent=True)["basis"], "RAW_LLM_INTENT"
        )


@unittest.skipUnless(LOCAL, "local Radar/Global PM records or built V7.6 package absent")
class Protocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.offline = no_network()
        cls.offline.__enter__()
        cls.network = patch.object(
            GeminiLLMClient,
            "_default_transport",
            side_effect=AssertionError("REAL_GEMINI_FORBIDDEN"),
        )
        cls.network.start()
        cls.audit = x.audit_v75()
        cls.erratum = x.erratum()
        cls.qual = x.qualify()
        cls.rows = {r["case"]: r for r in cls.qual["cases"]}
        cls.manifest = x.read(x.OUT / "EXPERIMENT_MANIFEST.json")
        cls.plan = x.plan(cls.manifest)

    @classmethod
    def tearDownClass(cls):
        cls.network.stop()
        cls.offline.__exit__(None, None, None)

    def case(self, name, status, codes=()):
        row = self.rows[name]
        self.assertTrue(row["passed"], row)
        self.assertEqual((row["status"], row["codes"]), (status, list(codes)))
        self.assertEqual(row["response"], "SCRIPTED_FAKE_NOT_GEMINI")
        return row

    def variant(self, **changes):
        m = copy.deepcopy(self.manifest)
        m.update(changes)
        return m

    # 1 — the V7.5 inventory, counts and conclusions.
    def test_01_v75_inventory_audited(self):
        c = self.audit["checks"]
        self.assertTrue(self.audit["ok"], c)
        self.assertEqual((c["sources_inventoried"], c["metrics_defined"]), (64, 32))
        self.assertEqual(c["regression_failed_passed"], [15, 1706])
        self.assertTrue(c["raw_radar_tokens_match_v75"] and c["raw_gpm_tokens_match_v75"])
        self.assertEqual(c["forbidden_financial_claims"], [])
        probe = x.OUT.parent / "hfl_scientific_consolidation_v75" / "README.md"
        with patch.object(
            Path,
            "read_text",
            return_value="A V2 comprovou que o sistema reduz o risco operacional.",
        ):
            self.assertEqual(len(x.forbidden_claims([probe])), 1)

    # 2 — hashes of every inventoried source; a changed byte is a violation.
    def test_02_hashes_verified_and_tampering_detected(self):
        self.assertEqual(v75.check()["violations"], [])
        target, real = v75.V2 + "/result.json", v75.sha
        with patch.object(v75, "sha", lambda p: "0" * 64 if p == target else real(p)):
            self.assertIn(target, v75.check()["violations"])

    # 3 — a missing source is reported, never ignored.
    def test_03_missing_source_detected(self):
        real = v75.load

        def load(path):
            data = real(path)
            if path.endswith("EVIDENCE_MANIFEST.json"):
                data = {
                    **data,
                    "sources": [
                        *data["sources"],
                        {
                            "path": "data/radar/absent.json",
                            "sha256": "0" * 64,
                            "immutability": "IMMUTABLE",
                        },
                    ],
                }
            return data

        with patch.object(v75, "load", load):
            report = v75.check()
        self.assertEqual(report["missing"], ["data/radar/absent.json"])
        self.assertFalse(report["ok"])

    # 4 — the erratum names the four records and changes nothing.
    def test_04_radar_token_erratum(self):
        e = self.erratum
        self.assertEqual(e["recorded_zero_tickers"], ["BBAS3", "ITUB4", "PETR4", "WEGE3"])
        self.assertEqual(e["partial_sum_tickers"], ["VALE3"])
        self.assertEqual(e["field_states_total"], {"ABSENT": 28, "VALUE": 1})
        self.assertTrue(e["aggregation_rule_found"])
        for t, v in e["tickers"].items():
            self.assertEqual(v["result_sha256"], v["result_sha256_pin"], t)
            self.assertEqual(v["explicit_zero_calls"], 0)
            self.assertTrue(
                v["corrected_interpretation"]["recorded_cost_equals_lower_bound"]
            )
            self.assertEqual(v["corrected_interpretation"]["usd_billed"], "UNKNOWN")
        self.assertEqual(
            e["tickers"]["PETR4"]["corrected_interpretation"]["thoughts_tokens"],
            "NOT_REPORTED",
        )

    # 6 — synthetic qualification never passes for an official result.
    def test_06_synthetic_and_real_separated(self):
        self.assertEqual(self.audit["checks"]["metrics_citing_synthetic_sources"], [])
        self.assertTrue(self.audit["checks"]["real_records_are_gemini"])
        self.assertEqual(self.qual["real_provider_calls"], 0)
        self.assertEqual(self.qual["category"], "A_SYNTHETIC_QUALIFICATION")
        self.assertEqual(
            {r["response"] for r in self.qual["cases"]}, {"SCRIPTED_FAKE_NOT_GEMINI"}
        )

    # 7/8 — the plan, the draw of sessions and the qualification are deterministic.
    def test_07_plan_and_matrix_deterministic(self):
        self.assertEqual(x.plan(self.manifest)["plan_sha256"], self.plan["plan_sha256"])
        rule = self.manifest["session_selection"]
        self.assertEqual(x.select_sessions(rule), x.select_sessions(rule))
        self.assertEqual(
            x.qualify()["qualification_sha256"], self.qual["qualification_sha256"]
        )

    def test_08_stable_ids_and_hashes(self):
        first = {c["id"]: c["first_attempt_id"] for c in self.plan["campaigns"]}
        self.assertEqual(first["c1-pilot"], "v76-c1-pilot-20261009-r001")
        self.assertEqual(
            first["c4-prospective"], "v76-c4-prospective-after_freeze_01-r001"
        )
        built = x.read(x.OUT / "BUDGET_PLAN.json")
        self.assertEqual(built["plan_sha256"], self.plan["plan_sha256"])
        self.assertEqual(x.validate_protocol(), [])
        self.assertEqual(
            self.manifest["protocol_sha256"], x.digest(x.documents(x.PROTOCOL_DOCS))
        )

    # 9-17 — scenario matrix on the sealed V2 validator.
    def test_09_all_cash(self):
        self.case("S0-cash-watchlist", "VALID_PROPOSAL")
        self.case("S9-all-cash-no-operation", "VALID_PROPOSAL")

    def test_10_existing_positions(self):
        for name in (
            "S1-hold",
            "S1-reduce",
            "S1-exit",
            "S1-increase",
            "S1-new-buy",
            "S9-hold-despite-sell-signal",
        ):
            self.case(name, "VALID_PROPOSAL")
        self.case(
            "S1-not-selected-while-held",
            "REJECTED_BY_VALIDATOR",
            ["explanation_action_inconsistent"],
        )

    def test_11_insufficient_cash(self):
        self.case("S2-buy-within-cash", "VALID_PROPOSAL")
        self.case(
            "S2-buy-beyond-cash", "REJECTED_BY_VALIDATOR", ["insufficient_settled_cash"]
        )
        self.case(
            "S2-buy-without-compra-opinion",
            "REJECTED_BY_VALIDATOR",
            ["buy_incompatible_with_opinion"],
        )

    def test_12_sale_without_custody(self):
        self.case(
            "S0-sale-without-custody",
            "REJECTED_BY_VALIDATOR",
            ["insufficient_available_units"],
        )

    def test_13_d2_settlement(self):
        self.case("S3-sale-creates-receivable", "VALID_PROPOSAL")
        self.case(
            "S3-receivable-used-as-cash",
            "REJECTED_BY_VALIDATOR",
            ["insufficient_settled_cash"],
        )

    def test_14_conditional_buy(self):
        self.case("S4-dependent-buy", "VALID_PROPOSAL")
        self.case(
            "S4-dependency-not-declared",
            "REJECTED_BY_VALIDATOR",
            ["insufficient_settled_cash"],
        )
        self.case(
            "S4-deferred-list-omitted",
            "REJECTED_BY_VALIDATOR",
            ["settlement_deferred_inconsistent"],
        )
        self.case(
            "S4-unknown-dependency",
            "REJECTED_BY_VALIDATOR",
            ["dependency_cycle_unknown_or_not_sale"],
        )

    def test_15_vetoed_asset(self):
        for name in (
            "S5-buy-vetoed",
            "S5-weight-on-vetoed",
            "S5-held-vetoed-increase",
            "S5-held-vetoed-reduce",
        ):
            self.case(name, "REJECTED_BY_VALIDATOR", ["vetoed_asset_allocation"])
        self.case("S5-held-vetoed-hold", "VALID_PROPOSAL")

    def test_16_concentration_limit(self):
        self.case("S6-within-limit", "VALID_PROPOSAL")
        self.case(
            "S6-beyond-limit",
            "REJECTED_BY_VALIDATOR",
            ["concentration_or_exposure_limit"],
        )

    def test_17_exposure_and_operation_limits(self):
        self.case(
            "S7-exposure-beyond-limit",
            "REJECTED_BY_VALIDATOR",
            ["concentration_or_exposure_limit"],
        )
        self.case(
            "S7-operation-count-beyond-limit",
            "REJECTED_BY_VALIDATOR",
            ["response_schema_invalid"],
        )

    # 18/19 — expired context, tampered opinions and Radar origin.
    def test_18_expired_context(self):
        self.case(
            "S8-expired-context", "REJECTED_BY_VALIDATOR", ["proposal_expired_or_future"]
        )

    def test_19_incompatible_radar_source(self):
        self.assertEqual(
            self.qual["radar_origin"],
            {"verified": "VERIFIED", "mismatch": "MISMATCH", "missing": "MISSING"},
        )
        self.case(
            "S8-tampered-opinion", "REJECTED_BY_VALIDATOR", ["record_hash_mismatch"]
        )
        self.case(
            "S8-opinion-hash", "REJECTED_BY_VALIDATOR", ["opinion_reference_mismatch"]
        )

    # 20 — every metric is fully defined and every reference resolves.
    def test_20_metric_without_definition(self):
        catalog = x.read(x.OUT / "METRIC_CATALOG.json")
        del catalog["metrics"]["global_validation_rate"]["formula"]
        errors = x.validate_protocol(catalog=catalog)
        self.assertIn(
            "metric_definition_incomplete:global_validation_rate:formula", errors
        )
        matrix = x.read(x.OUT / "SCENARIO_MATRIX.json")
        matrix["scenarios"]["S0"]["metrics"].append("alpha")
        self.assertIn("metric_undefined:S0:alpha", x.validate_protocol(matrix=matrix))

    # 21 — aggregate budgets block, never silently pass.
    def test_21_aggregate_budget_exceeded(self):
        status = {c["id"]: c for c in self.plan["campaigns"]}
        self.assertIn(
            "BUDGET_EXCEEDS_SEALED_V2_CAP_REQUIRES_NEW_TREATMENT_OR_DECISION",
            status["c1-extended"]["blocks"],
        )
        self.assertIn(
            "RADAR_AGGREGATE_EXCEEDS_CAP_REQUIRES_HUMAN_BUDGET_AUTHORIZATION",
            status["c3-oos"]["blocks"],
        )
        self.assertEqual(self.plan["caps"]["global_pm_max_new_calls"], 29)
        self.assertEqual(status["c1-intermediate"]["status"], "PLANNED_NOT_AUTHORIZED")

    # 22 — no paid attempt without a human authorization; none is ever implemented here.
    def test_22_paid_attempt_without_authorization(self):
        with self.assertRaisesRegex(PermissionError, "paid_execution_not_authorized"):
            x.paid_gate(self.manifest)
        forged = self.variant(
            state="AUTHORIZED_FOR_PAID_EXECUTION",
            frozen_at="2026-10-12",
            human_review={"by": "x"},
        )
        self.assertIn(
            "paid_state_without_valid_authorization", x.validate_protocol(forged)
        )
        signed = {
            **forged,
            "authorization": {
                "protocol_sha256": forged["protocol_sha256"],
                "signatory": "x",
                "max_usd": "1",
            },
        }
        with self.assertRaisesRegex(PermissionError, "not_implemented_in_v76"):
            x.paid_gate(signed)

    # 23 — replication identities are unique and never reuse an existing record.
    def test_23_duplicate_replication_identity(self):
        dup = self.variant(
            campaigns=[*self.manifest["campaigns"], self.manifest["campaigns"][0]]
        )
        self.assertTrue(
            any(e.startswith("duplicate_attempt_id:") for e in x.plan(dup)["errors"])
        )
        with patch.object(
            x, "attempt_ids", lambda c, s: ["v74-76d07c0d32444cecaf07e875deacb519"]
        ):
            errors = x.plan(self.variant(campaigns=self.manifest["campaigns"][:1]))[
                "errors"
            ]
        self.assertEqual(
            errors, ["attempt_id_already_used:v74-76d07c0d32444cecaf07e875deacb519"]
        )
        rep = self.qual["replication_identity"]
        self.assertTrue(
            rep["context_sha256_differ"] and rep["economic_fingerprint_equal"]
        )
        self.assertFalse(rep["bytes_identical_claimed"])
        other = x.frozen("v76-rep-c", "90000.00", {})
        self.assertNotEqual(x.economic_fingerprint(other), rep["fingerprint"])

    # 24 — V1 is closed and never pooled with V2.
    def test_24_v1_v2_separated(self):
        self.case(
            "S8-v1-response", "REJECTED_BY_VALIDATOR", ["treatment_identity_mismatch"]
        )
        v1_campaign = {
            **self.manifest["campaigns"][0],
            "id": "v1-again",
            "treatment": "HFL-MULTIASSET-GLOBAL-PM-V1",
        }
        errors = x.validate_protocol(
            self.variant(campaigns=[*self.manifest["campaigns"], v1_campaign])
        )
        self.assertIn("closed_treatment_in_campaign:v1-again", errors)
        self.assertIn("treatments_mixed_in_replication_group:RG-S0-2026-10-09", errors)

    # 25/26 — sealed evidence intact; no financial or record effects.
    def test_25_sealed_evidence_unchanged(self):
        self.assertTrue(self.qual["sealed_trees_unchanged"])
        self.assertTrue(v75.check()["ok"])
        self.assertTrue(
            self.audit["checks"]["v2_contract_unchanged"]
            and self.audit["checks"]["v1_contract_unchanged"]
        )
        self.assertEqual(
            (
                x.read(x.V1_REAL / "result.json")["status"],
                x.read(x.V2_REAL / "result.json")["status"],
            ),
            ("REJECTED_BY_VALIDATOR", "VALID_PROPOSAL"),
        )

    def test_26_no_financial_effects(self):
        roots = [p.name for base in (pm.OUTPUT, x.v1.OUTPUT) for p in base.iterdir()]
        self.assertFalse([r for r in roots if r.startswith("v76-")])
        self.assertFalse(
            x.read(x.OUT / "READINESS_REPORT.json")["gates"]["paid_execution_authorized"]
        )

    # 27 — the H2 Final Test stays blocked and out of scope.
    def test_27_h2_final_test_blocked(self):
        checkpoint = x.read(
            ROOT
            / "docs/evidence/h2_v6_provisional/VALIDATION_PROVISIONAL_CHECKPOINT.json"
        )
        self.assertIs(checkpoint["final_test_authorized"], False)
        treatments = {**self.manifest["treatments"], "H2-V6": {"role": "x"}}
        self.assertIn(
            "h2_out_of_scope:H2-V6",
            x.validate_protocol(self.variant(treatments=treatments)),
        )
        inside = {
            **self.manifest["campaigns"][0],
            "id": "h2-window",
            "sessions": ["2026-03-02"],
            "evaluation": "RETROSPECTIVE_OUT_OF_SAMPLE",
            "replication_group": "RG-X",
        }
        self.assertIn(
            "session_in_h2_window:2026-03-02",
            x.validate_protocol(self.variant(campaigns=[inside])),
        )
        final = x.PHASE_WINDOWS["FINAL_TEST"]
        self.assertFalse(
            [
                s
                for s in x.eligible_sessions(self.manifest["session_selection"])
                if final.start <= s <= final.end
            ]
        )

    # 28 — a protocol cannot claim EXECUTED or skip human review.
    def test_28_executed_state_rejected(self):
        errors = x.validate_protocol(self.variant(state="EXECUTED"))
        for code in (
            "frozen_without_human_review",
            "paid_state_without_valid_authorization",
            "executed_without_execution_evidence",
        ):
            self.assertIn(code, errors)
        self.assertIn(
            "frozen_without_human_review",
            x.validate_protocol(self.variant(state="FROZEN_FOR_FUTURE_EVALUATION")),
        )

    # 29 — temporal leakage and mislabelled prospective sessions.
    def test_29_temporal_leakage_detected(self):
        rule = {
            **self.manifest["session_selection"],
            "selection_inputs": ["b3_calendar", "forward_return_5d"],
        }
        campaigns = [
            {"id": "p", "evaluation": "PROSPECTIVE", "sessions": ["2026-09-01"]},
            {
                "id": "o",
                "evaluation": "RETROSPECTIVE_OUT_OF_SAMPLE",
                "sessions": ["2026-10-09"],
                "decision_information_cutoff": "NEXT_OPEN",
            },
        ]
        found = x.leakage(rule, campaigns, date(2026, 10, 12))
        for code in (
            "forbidden_selection_input:forward_return_5d",
            "prospective_label_on_known_session:p",
            "development_session_reused:o:2026-10-09",
            "information_after_decision:o",
        ):
            self.assertIn(code, found)
        self.assertEqual(
            x.leakage(self.manifest["session_selection"], [], date(2026, 10, 12)), []
        )

    # 32 — readiness is QUALIFIED_OFFLINE and nothing more.
    def test_32_readiness_report(self):
        built = x.read(x.OUT / "READINESS_REPORT.json")
        self.assertEqual(
            (built["state"], self.manifest["state"]),
            ("QUALIFIED_OFFLINE", "QUALIFIED_OFFLINE"),
        )
        self.assertFalse(built["gates"]["paid_execution_authorized"])
        self.assertIn("HUMAN_REVIEW_OF_PREREGISTRATION", built["blocked_by"])
        self.assertIn("PAID_EXECUTION_AUTHORIZATION", built["blocked_by"])
        self.assertEqual(
            built["qualification"]["qualification_sha256"],
            self.qual["qualification_sha256"],
        )
        self.assertEqual(
            json.dumps(built["v75_audit"], sort_keys=True),
            json.dumps(self.audit["checks"], sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
