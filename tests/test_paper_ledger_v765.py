"""Offline qualification; every writable DB is external, temporary and synthetic."""

import copy
import json
import sqlite3
import subprocess
import sys
import tempfile
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "dashboard"), str(ROOT)]

import paper_ledger as ledger  # noqa: E402
import paper_ledger_api as api  # noqa: E402
import qualify_paper_ledger as q  # noqa: E402

from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

b = ledger.b


class LedgerChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hfl-paper-")
        self.path = Path(self.temp.name) / "ledger.sqlite3"
        self.store = ledger.Store.create(self.path)
        self.offline = no_network()
        self.offline.__enter__()
        self.create = ledger.creation(q.PORTFOLIO, q.DAY, q.PRICES)
        q.append(self.store, "PORTFOLIO_CREATED", self.create, "create")

    def tearDown(self):
        self.offline.__exit__(None, None, None)
        self.temp.cleanup()

    def state(self):
        return self.store.load(q.PORTFOLIO)[0]

    def view(self):
        return b.view(self.state()["financial"])

    def test_identity_initial_cash_restart_and_second_process(self):
        self.assertEqual(self.view()["equity"], "100000.00")
        self.assertEqual(self.view()["cash"]["reserved"], "0")
        self.assertEqual(self.state()["portfolio"]["ledger_version"], ledger.IDENTITY)
        self.assertEqual(ledger.Store(self.path).load(q.PORTFOLIO)[0], self.state())
        code = "import sys;sys.path[:0]=['scripts','.'];import paper_ledger as p;assert p.Store(sys.argv[1]).verify(sys.argv[2])['ok']"
        result = subprocess.run(
            [sys.executable, "-B", "-c", code, str(self.path), q.PORTFOLIO],
            cwd=ROOT,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaises(FileExistsError):
            ledger.Store.create(self.path)

    def test_storage_boundaries_read_only_and_classifications(self):
        for target in (
            ROOT / "data/paper/ledger.sqlite3",
            ROOT / "data/forward/ledger.sqlite3",
            ROOT / ".pytest_cache/hfl-paper-demo/ledger.sqlite3",
            self.path.parent / "other.sqlite3",
        ):
            with self.subTest(path=str(target)), self.assertRaises(ValueError):
                ledger.Store(target, writable=True)
        with self.assertRaisesRegex(ValueError, "read_only_store"):
            ledger.Store(self.path).append(
                q.PORTFOLIO,
                "PORTFOLIO_CLOSED",
                {},
                "close",
                effective_at=q.DAY + "T19:00:00-03:00",
            )
        for classification in ledger.CLASSIFICATIONS[1:]:
            event = self.store.load(q.PORTFOLIO)[1][0]
            altered = copy.deepcopy(event)
            altered["payload"]["portfolio"]["classification"] = classification
            with self.subTest(classification=classification), self.assertRaises(
                ValueError
            ):
                ledger.reduce(None, altered)

    def test_whole_lifecycle_accounting_and_history(self):
        artifact = q.lifecycle(self.store)
        view = self.view()
        self.assertEqual(
            (view["equity"], view["costs"], view["realized_pnl"], view["unrealized_pnl"]),
            ("100168.28", "11.72", "116.68", "51.60"),
        )
        self.assertEqual(view["cash"]["settled"], "91708.28")
        self.assertEqual(view["positions"]["PETR4"]["quantity"], "60")
        self.assertEqual(view["positions"]["PETR4"]["average_cost"], "40.04000000")
        self.assertEqual(len(self.state()["history"]), 5)
        self.assertEqual(len(artifact["events"]), 27)
        self.assertGreater(b.dec(view["drawdown"]), 0)
        self.assertGreater(b.dec(view["exposure"]), 0)
        history = {h["session"]: h["view"] for h in self.state()["history"]}
        self.assertEqual(history["2026-04-22"]["cash"]["receivable"], "1718.28")
        self.assertEqual(history["2026-04-17"]["positions"]["PETR4"]["unsettled"], "100")
        self.assertEqual(history["2026-04-24"]["cash"]["receivable"], "0")
        self.assertEqual(self.store.verify(q.PORTFOLIO)["errors"], [])

    def test_buy_reservation_cancel_and_reused_order_id(self):
        ref = q.authorize(self.store, [q.operation("buy")], "buy")
        q.append(
            self.store,
            "PAPER_ORDER_CREATED",
            {"proposal_id": "buy"},
            "reserve",
            authorization_ref=ref,
        )
        self.assertEqual(self.view()["cash"]["reserved"], "4100.00")
        self.assertEqual(self.view()["cash"]["available"], "95900.00")
        q.append(self.store, "PAPER_ORDER_CANCELLED", {}, "cancel", authorization_ref=ref)
        self.assertEqual(self.view()["cash"]["reserved"], "0")
        with self.assertRaisesRegex(ValueError, "authorization_scope"):
            q.authorize(self.store, [q.operation("buy")], "reused")

    def test_buy_cost_and_unsettled_custody_not_sellable(self):
        q.trade(self.store, [q.operation("buy")], "buy")
        self.assertEqual(self.view()["equity"], "99996.00")
        self.assertEqual(self.view()["positions"]["PETR4"]["basis"], "4004.00")
        self.assertEqual(self.view()["positions"]["PETR4"]["available"], "0")
        with self.assertRaisesRegex(ValueError, "authorization_scope"):
            q.authorize(self.store, [q.operation("sell", side="SELL")], "unsettled-sale")

    def test_invalid_cash_custody_quantity_price_and_concentration(self):
        cases = [
            q.operation("cash", quantity="3000"),
            q.operation("concentration", quantity="1000"),
            q.operation("short", side="SELL"),
        ]
        cases += [
            q.operation("quantity-" + str(i), quantity=v)
            for i, v in enumerate(("0", "-1", "0.5", True, 1.5, "NaN"))
        ]
        cases += [
            q.operation("price-" + str(i), price=v)
            for i, v in enumerate(("0", "-1", "1.001", 1.0, "Infinity"))
        ]
        for i, op in enumerate(cases):
            with self.subTest(operation=op), self.assertRaises(ValueError):
                q.authorize(self.store, [op], "invalid-" + str(i))
        self.assertEqual(self.view()["cash"]["available"], "100000.00")
        self.assertEqual(self.view()["executions"], {})

    def test_veto_blocks_buy_and_sale(self):
        with self.assertRaisesRegex(ValueError, "authorization_scope"):
            q.authorize(self.store, [q.operation("veto-buy")], "veto-buy", veto="PETR4")
        q.trade(self.store, [q.operation("buy")], "buy")
        q.settle(self.store, "buy", "2026-04-22")
        q.mark(self.store, "2026-04-22", q.PRICES)
        with self.assertRaisesRegex(ValueError, "authorization_scope"):
            q.authorize(
                self.store,
                [q.operation("veto-sale", side="SELL")],
                "veto-sale",
                "2026-04-22",
                veto="PETR4",
            )
        self.assertEqual(self.view()["positions"]["PETR4"]["quantity"], "100")

    def test_no_operation_proposal_does_not_create_order(self):
        ref = q.authorize(self.store, [], "hold")
        with self.assertRaisesRegex(ValueError, "has_no_operations"):
            q.append(
                self.store,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "hold"},
                "reserve",
                authorization_ref=ref,
            )
        self.assertEqual(self.view()["executions"], {})

    def test_official_references_remain_advisory_and_rejected_stays_rejected(self):
        before = self.view()
        ids = (
            "v7-5a78ea5d15214e37bcae18f167ffcee3",
            "v74-76d07c0d32444cecaf07e875deacb519",
        )
        for i, rid in enumerate(ids):
            reference = api.official_reference(rid)
            q.append(
                self.store,
                "PROPOSAL_REFERENCED",
                {"reference": reference},
                "reference-" + str(i),
            )
            with self.assertRaises(KeyError):
                q.append(
                    self.store,
                    "VALIDATION_RECORDED",
                    {"proposal_id": rid},
                    "cannot-validate-" + str(i),
                )
        self.assertEqual(
            self.state()["advisory_references"][ids[0]]["status"], "REJECTED_BY_VALIDATOR"
        )
        self.assertEqual(
            self.state()["advisory_references"][ids[1]]["operation_count"], 0
        )
        self.assertEqual(self.view(), before)

    def test_authorization_scope_missing_foreign_validation_and_expiration(self):
        ref = q.authorize(self.store, [q.operation("buy")], "buy")
        before = len(self.store.load(q.PORTFOLIO)[1])
        for authorization in (None, "h2-approval", "other-campaign"):
            with self.subTest(authorization=authorization), self.assertRaises(
                (ValueError, KeyError)
            ):
                q.append(
                    self.store,
                    "PAPER_ORDER_CREATED",
                    {"proposal_id": "buy"},
                    "wrong",
                    authorization_ref=authorization,
                )
        _, events, _ = self.store.load(q.PORTFOLIO)
        authorization = next(e for e in events if e["kind"] == "AUTHORIZATION_RECORDED")
        for field, value in (
            ("scope", "H2_V6"),
            ("portfolio_id", "other"),
            ("validation_sha256", "0" * 64),
            ("proposal_sha256", "0" * 64),
            ("expires_at", q.DAY + "T18:00:00-03:00"),
        ):
            payload = {**authorization["payload"], field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                q.append(
                    self.store, "AUTHORIZATION_RECORDED", payload, "foreign-" + field
                )
        with self.assertRaisesRegex(
            ValueError, "global_validation_failed_before_reservation"
        ):
            self.store.append(
                q.PORTFOLIO,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "buy"},
                "expired",
                authorization_ref=ref,
                effective_at=q.DAY + "T22:00:00-03:00",
            )
        self.assertEqual(len(self.store.load(q.PORTFOLIO)[1]), before)

    def test_d_plus_two_weekend_holiday_and_unknown_calendar(self):
        self.assertEqual(ledger.settlement_day("2026-04-17"), "2026-04-22")
        self.assertEqual(ledger.settlement_day("2026-04-22"), "2026-04-24")
        for day in ("2026-04-18", "2026-04-21", "2026-10-13", "2027-01-04", "2026-08-28"):
            with self.subTest(day=day), self.assertRaises(ValueError):
                ledger.settlement_day(day)

    def test_early_unknown_and_duplicate_settlement(self):
        q.trade(self.store, [q.operation("buy")], "buy")
        with self.assertRaisesRegex(ValueError, "settlement_not_due"):
            q.settle(self.store, "buy", "2026-04-20")
        q.settle(self.store, "buy", "2026-04-22")
        self.assertEqual(self.view()["positions"]["PETR4"]["available"], "100")
        payload = {
            "order_id": "buy",
            "settlement_id": "another",
            "confirmation_source": "SYNTHETIC_CUSTODIAN_CONFIRMATION",
        }
        with self.assertRaisesRegex(ValueError, "settlement_duplicate"):
            q.append(
                self.store,
                "SETTLEMENT_RECORDED",
                payload,
                "repeat-settle",
                day="2026-04-22",
            )
        with self.assertRaises(KeyError):
            q.settle(self.store, "unknown", "2026-04-22")

    def test_official_format_fixture_valuation_cannot_execute_close(self):
        q.mark(
            self.store,
            "2026-04-20",
            q.PRICES,
            classification="OFFICIAL_B3_RAW",
            price_type="CLOSE",
        )
        self.assertEqual(self.state()["quote"]["source"], "B3_COTAHIST_FIXTURE")
        ref = q.authorize(self.store, [q.operation("buy")], "buy", "2026-04-20")
        with self.assertRaisesRegex(ValueError, "synthetic_execution_price_required"):
            q.append(
                self.store,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "buy"},
                "reserve",
                day="2026-04-20",
                authorization_ref=ref,
            )

    def test_invalid_price_provenance_adjusted_unknown_and_lookahead(self):
        quote = ledger.observation("2026-04-20", q.PRICES)
        for field, value in (
            ("basis", "ADJUSTED"),
            ("classification", "ADJUSTED_RESEARCH"),
            ("classification", "UNKNOWN_SOURCE"),
            ("currency", "USD"),
            ("source", "untrusted"),
            ("fixture", False),
            ("price_type", "CLOSE"),
            ("data_sha256", "0" * 64),
            ("observed_at", "2026-04-20T22:00:00-03:00"),
        ):
            body = {k: v for k, v in quote.items() if k not in ("sha256", "data_sha256")}
            body[field] = value
            invalid = b.sealed(
                {
                    **body,
                    "data_sha256": value if field == "data_sha256" else b.digest(body),
                }
            )
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                q.append(
                    self.store,
                    "MARKET_PRICE_OBSERVED",
                    {"observation": invalid},
                    "bad-" + field,
                    day="2026-04-20",
                )

    def test_missing_marks_unavailable_not_imputed_and_recovery(self):
        q.trade(self.store, [q.operation("buy")], "buy")
        q.mark(self.store, "2026-04-20", {"VALE3": "60.00"})
        self.assertEqual(self.state()["valuation_unavailable"], ["PETR4"])
        self.assertEqual(self.state()["quote"]["session"], q.DAY)
        self.assertEqual(len(self.state()["history"]), 0)
        self.assertFalse(self.store.verify(q.PORTFOLIO)["ok"])
        q.mark(self.store, "2026-04-20", q.PRICES, command="complete")
        q.append(self.store, "PORTFOLIO_RECONCILED", {}, "reconciled", day="2026-04-20")
        self.assertTrue(self.store.verify(q.PORTFOLIO)["ok"])
        self.assertEqual(self.state()["unavailable_sessions"][0]["session"], "2026-04-20")

    def test_duplicate_import_and_duplicate_valuation(self):
        _, event = q.append(
            self.store,
            "MARKET_PRICE_OBSERVED",
            {"observation": ledger.observation("2026-04-20", q.PRICES)},
            "observation",
            day="2026-04-20",
        )
        with self.assertRaisesRegex(ValueError, "duplicate_price_import"):
            q.append(
                self.store,
                "MARKET_PRICE_OBSERVED",
                event["payload"],
                "duplicate-import",
                day="2026-04-20",
            )
        payload = {"observation_id": event["event_id"]}
        q.append(self.store, "PORTFOLIO_VALUED", payload, "value", day="2026-04-20")
        with self.assertRaisesRegex(ValueError, "duplicate_valuation"):
            q.append(
                self.store, "PORTFOLIO_VALUED", payload, "other-value", day="2026-04-20"
            )

    def test_reconciliation_divergence_is_recorded_and_blocks_orders(self):
        ref = q.authorize(self.store, [q.operation("buy")], "buy")
        q.append(
            self.store,
            "PORTFOLIO_RECONCILED",
            {"expected": {"equity": "99999.00"}},
            "bad-recon",
        )
        report = self.store.verify(q.PORTFOLIO)
        self.assertEqual(report["status"], "RECONCILIATION_FAILED")
        self.assertEqual(report["errors"], ["expected_state_mismatch:equity"])
        self.assertEqual(self.view()["equity"], "100000.00")
        with self.assertRaisesRegex(ValueError, "inconsistent_or_finalized"):
            q.append(
                self.store,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "buy"},
                "reserve",
                authorization_ref=ref,
            )

    def test_finalized_session_cannot_trade(self):
        ref = q.authorize(self.store, [q.operation("buy")], "buy")
        q.append(self.store, "PORTFOLIO_RECONCILED", {}, "reconcile")
        with self.assertRaisesRegex(ValueError, "finalized_session"):
            q.append(
                self.store,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "buy"},
                "reserve",
                authorization_ref=ref,
            )

    def test_idempotency_conflict_replay_and_lost_confirmation(self):
        state, original = q.append(self.store, "PORTFOLIO_CREATED", self.create, "create")
        self.assertEqual(len(self.store.load(q.PORTFOLIO)[1]), 1)
        self.assertEqual(original, self.store.load(q.PORTFOLIO)[1][0])
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            q.append(
                self.store,
                "PORTFOLIO_CREATED",
                {**self.create, "capital": "1.00"},
                "create",
            )
        payload = {"observation": ledger.observation("2026-04-20", q.PRICES)}
        with self.assertRaisesRegex(RuntimeError, "lost_confirmation"):
            q.append(
                self.store,
                "MARKET_PRICE_OBSERVED",
                payload,
                "lost-ack",
                day="2026-04-20",
                crash="after_commit",
            )
        reopened = ledger.Store(self.path, writable=True)
        q.append(reopened, "MARKET_PRICE_OBSERVED", payload, "lost-ack", day="2026-04-20")
        self.assertEqual(len(reopened.load(q.PORTFOLIO)[1]), 2)
        export = reopened.export(q.PORTFOLIO)
        self.assertEqual(
            ledger.replay(export["events"], export["checkpoint"]),
            reopened.load(q.PORTFOLIO)[0],
        )

    def test_duplicate_execution_and_wrong_fill_authority(self):
        ref = q.authorize(self.store, [q.operation("buy")], "buy")
        q.append(
            self.store,
            "PAPER_ORDER_CREATED",
            {"proposal_id": "buy"},
            "reserve",
            authorization_ref=ref,
        )
        with self.assertRaisesRegex(ValueError, "reserved_authorized"):
            q.append(
                self.store,
                "PAPER_ORDER_EXECUTED",
                {"execution_id": "fill"},
                "wrong-fill",
                authorization_ref="foreign",
            )
        q.append(
            self.store,
            "PAPER_ORDER_EXECUTED",
            {"execution_id": "fill"},
            "fill",
            authorization_ref=ref,
        )
        before = self.view()
        with self.assertRaisesRegex(ValueError, "reserved_authorized"):
            q.append(
                self.store,
                "PAPER_ORDER_EXECUTED",
                {"execution_id": "fill"},
                "duplicate-fill",
                authorization_ref=ref,
            )
        self.assertEqual(self.view(), before)

    def test_atomic_transaction_interruptions_and_actual_process_death(self):
        for crash in ("after_event", "before_commit"):
            with self.subTest(crash=crash), self.assertRaises(RuntimeError):
                q.append(self.store, "PORTFOLIO_RECONCILED", {}, "reconcile", crash=crash)
            self.assertEqual(len(self.store.load(q.PORTFOLIO)[1]), 1)
        code = "import sqlite3,sys,os;c=sqlite3.connect(sys.argv[1]);c.execute('BEGIN IMMEDIATE');c.execute(\"UPDATE checkpoints SET body='corrupt'\");os._exit(7)"
        died = subprocess.run(
            [sys.executable, "-B", "-c", code, str(self.path)],
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(died.returncode, 7)
        self.assertTrue(ledger.Store(self.path).verify(q.PORTFOLIO)["ok"])
        q.append(self.store, "PORTFOLIO_RECONCILED", {}, "reconcile")
        self.assertEqual(len(self.state()["history"]), 1)

    def test_concurrent_retry_commits_once(self):
        request = {"observation": ledger.observation("2026-04-20", q.PRICES)}

        def writer(_):
            return q.append(
                ledger.Store(self.path, writable=True),
                "MARKET_PRICE_OBSERVED",
                request,
                "same-command",
                day="2026-04-20",
            )[1]["event_id"]

        with ThreadPoolExecutor(max_workers=6) as pool:
            ids = list(pool.map(writer, range(6)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(len(self.store.load(q.PORTFOLIO)[1]), 2)

    def test_concurrent_conflicting_payload_has_one_winner(self):
        def writer(price):
            payload = {
                "observation": ledger.observation(
                    "2026-04-20", {"PETR4": price, "VALE3": "60.00"}
                )
            }
            try:
                q.append(
                    ledger.Store(self.path, writable=True),
                    "MARKET_PRICE_OBSERVED",
                    payload,
                    "contested",
                    day="2026-04-20",
                )
                return "committed"
            except ValueError as exc:
                return str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(writer, ("41.00", "42.00")))
        self.assertCountEqual(results, ["committed", "idempotency_conflict"])
        self.assertEqual(len(self.store.load(q.PORTFOLIO)[1]), 2)

    def test_execution_and_settlement_ids_cannot_cross_orders(self):
        q.trade(self.store, [q.operation("first")], "first")
        ref = q.authorize(self.store, [q.operation("second")], "second")
        q.append(
            self.store,
            "PAPER_ORDER_CREATED",
            {"proposal_id": "second"},
            "reserve-second",
            authorization_ref=ref,
        )
        with self.assertRaisesRegex(ValueError, "duplicate_execution_id"):
            q.append(
                self.store,
                "PAPER_ORDER_EXECUTED",
                {"execution_id": "execution-first"},
                "cross-fill",
                authorization_ref=ref,
            )
        q.append(
            self.store,
            "PAPER_ORDER_EXECUTED",
            {"execution_id": "execution-second"},
            "fill-second",
            authorization_ref=ref,
        )
        q.settle(self.store, "first", "2026-04-22")
        with self.assertRaisesRegex(ValueError, "settlement_identity"):
            q.append(
                self.store,
                "SETTLEMENT_RECORDED",
                {
                    "order_id": "second",
                    "settlement_id": "settlement-first",
                    "confirmation_source": "SYNTHETIC_CUSTODIAN_CONFIRMATION",
                },
                "cross-settle",
                day="2026-04-22",
            )

    def test_temporal_order_and_corrupted_checkpoint(self):
        q.mark(self.store, "2026-04-20", q.PRICES)
        with self.assertRaisesRegex(ValueError, "clock_backwards"):
            q.append(self.store, "PORTFOLIO_RECONCILED", {}, "backdate")
        with closing(sqlite3.connect(self.path)) as conn, conn:
            checkpoint = json.loads(
                conn.execute("SELECT body FROM checkpoints").fetchone()[0]
            )
            checkpoint["state"]["financial"]["settled_cash"] = "1.00"
            conn.execute("UPDATE checkpoints SET body=?", (json.dumps(checkpoint),))
        report = self.store.verify(q.PORTFOLIO)
        self.assertEqual(report["status"], "RECONCILIATION_FAILED")
        self.assertIn("checkpoint_replay_mismatch", report["errors"])
        with self.assertRaises(ValueError):
            q.append(
                self.store, "PORTFOLIO_RECONCILED", {}, "cannot-repair", day="2026-04-20"
            )

    def test_hash_chain_mutation_and_immutable_sql_events(self):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable_event"):
                conn.execute("UPDATE events SET body='{}'")
            with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable_event"):
                conn.execute("DELETE FROM events")
            event = json.loads(conn.execute("SELECT body FROM events").fetchone()[0])
            event["payload"]["portfolio"]["initial_capital"] = "999.00"
            conn.execute("DROP TRIGGER immutable_update")
            conn.execute("UPDATE events SET body=?", (json.dumps(event),))
        self.assertEqual(
            self.store.verify(q.PORTFOLIO)["errors"], ["record_hash_mismatch"]
        )

    def test_corrupted_database_and_missing_tail(self):
        self.path.write_bytes(b"not a database")
        self.assertEqual(
            self.store.verify(q.PORTFOLIO)["status"], "RECONCILIATION_FAILED"
        )

    def test_close_empty_portfolio_and_reject_new_financial_events(self):
        q.append(self.store, "PORTFOLIO_CLOSED", {}, "close")
        self.assertEqual(self.state()["portfolio"]["status"], "CLOSED")
        with self.assertRaisesRegex(ValueError, "portfolio_closed"):
            q.append(self.store, "PORTFOLIO_RECONCILED", {}, "after-close")

    def test_sale_receivable_cannot_fund_purchase_before_confirmation(self):
        q.trade(
            self.store,
            [
                q.operation("p", quantity="900"),
                q.operation("v", "VALE3", quantity="600", price="60.00"),
            ],
            "initial",
        )
        q.settle(self.store, "p", "2026-04-22")
        q.settle(self.store, "v", "2026-04-22")
        q.mark(self.store, "2026-04-22", q.PRICES)
        q.trade(
            self.store,
            [q.operation("sale", side="SELL", quantity="900")],
            "sale",
            "2026-04-22",
        )
        self.assertEqual(self.view()["cash"]["receivable"], "35964.00")
        self.assertEqual(self.view()["cash"]["available"], "27928.00")
        with self.assertRaises(ValueError):
            q.authorize(
                self.store,
                [q.operation("unfunded", quantity="900")],
                "unfunded",
                "2026-04-22",
            )
        ref = q.authorize(
            self.store,
            [q.operation("deferred", quantity="900", dependencies=["sale"])],
            "deferred",
            "2026-04-22",
        )
        with self.assertRaisesRegex(ValueError, "has_no_operations"):
            q.append(
                self.store,
                "PAPER_ORDER_CREATED",
                {"proposal_id": "deferred"},
                "reserve-deferred",
                day="2026-04-22",
                authorization_ref=ref,
            )
        q.settle(self.store, "sale", "2026-04-24")
        q.mark(self.store, "2026-04-24", q.PRICES)
        q.trade(
            self.store,
            [q.operation("funded", quantity="900", dependencies=["sale"])],
            "funded",
            "2026-04-24",
        )
        self.assertIn("funded", self.view()["executions"])

    def test_resealed_invalid_events_sequence_temporal_replay_and_deleted_tail(self):
        artifact = q.lifecycle(self.store)
        for field, value in (
            ("sequence", 999),
            ("previous_sha256", "0" * 64),
            ("kind", "UNKNOWN"),
            ("recorded_at", "2026-01-02T12:00:00Z"),
            ("effective_at", "2026-04-17T19:00:00-03:00"),
        ):
            events = copy.deepcopy(artifact["events"])
            events[-1] = b.sealed(
                {**{k: v for k, v in events[-1].items() if k != "sha256"}, field: value}
            )
            with self.subTest(field=field), self.assertRaises(ValueError):
                ledger.replay(events, artifact["checkpoint"])
        with self.assertRaises(ValueError):
            ledger.replay(artifact["events"][:-1], artifact["checkpoint"])
        with self.assertRaises(ValueError):
            ledger.replay(
                [*artifact["events"], artifact["events"][-1]], artifact["checkpoint"]
            )


class MutationChecks(unittest.TestCase):
    def test_removed_guards_are_detected_without_editing_any_file(self):
        source = (ROOT / "scripts/paper_ledger.py").read_text(encoding="utf-8")
        artifact = b.read(api.FIXTURE)

        def source_check(module):
            quote = ledger.observation(q.DAY, q.PRICES)
            body = {k: v for k, v in quote.items() if k not in ("sha256", "data_sha256")}
            body["basis"] = "ADJUSTED"
            with self.assertRaises(ValueError):
                module.checked_observation(
                    b.sealed({**body, "data_sha256": b.digest(body)}),
                    q.DAY + "T19:00:00-03:00",
                )

        def checkpoint_check(module):
            checkpoint = copy.deepcopy(artifact["checkpoint"])
            checkpoint["state"]["financial"]["settled_cash"] = "1.00"
            with self.assertRaises(ValueError):
                module.replay(artifact["events"], checkpoint)

        def authorization_check(module):
            events = artifact["events"]
            i = next(
                i for i, e in enumerate(events) if e["kind"] == "AUTHORIZATION_RECORDED"
            )
            state = None
            for event in events[:i]:
                state = ledger.reduce(state, event)
            event = copy.deepcopy(events[i])
            event["payload"]["scope"] = "H2_V6"
            with self.assertRaises(ValueError):
                module.reduce(state, event)

        def fill_authority_check(module):
            events = artifact["events"]
            i = next(
                i for i, e in enumerate(events) if e["kind"] == "PAPER_ORDER_EXECUTED"
            )
            state = None
            for event in events[:i]:
                state = ledger.reduce(state, event)
            event = copy.deepcopy(events[i])
            event["authorization_ref"] = "another-campaign"
            with self.assertRaises(ValueError):
                module.reduce(state, event)

        def calendar_check(module):
            with self.assertRaises(ValueError):
                module.session("2026-10-13")

        mutations = [
            ('or quote["basis"] != "RAW"', "or False", source_check),
            ("if checkpoint != {", "if False and checkpoint != {", checkpoint_check),
            ('or p["scope"] != IDENTITY', "or False", authorization_check),
            (
                'or event["authorization_ref"] != state.get("pending_authorization")',
                "or False",
                fill_authority_check,
            ),
            ("if day not in sessions():", "if False:", calendar_check),
        ]
        for old, new, check in mutations:
            with self.subTest(guard=old):
                check(ledger)
                self.assertEqual(source.count(old), 1)
                module = types.ModuleType("paper_ledger_mutant")
                module.__file__ = ledger.__file__
                exec(
                    compile(source.replace(old, new), ledger.__file__, "exec"),
                    module.__dict__,
                )
                with self.assertRaises(AssertionError):
                    check(module)


class ReadChecks(unittest.TestCase):
    def test_explicit_demo_opt_in_and_official_empty_catalog(self):
        self.assertEqual(api.get({})["wallets"], [])
        self.assertFalse(api.get({})["official_execution_enabled"])
        self.assertEqual(
            api.get({"demo": "1"})["wallets"][0]["classification"], "SYNTHETIC_TEST"
        )
        for query in (
            {"wallet": q.PORTFOLIO},
            {"demo": "1", "wallet": "h2:ai"},
            {"demo": "1", "wallet": "../../state"},
            {"path": "x"},
            {"demo": "2"},
            {"demo": "1", "wallet": q.PORTFOLIO, "execute": "1"},
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                api.get(query)

    def test_get_provenance_pagination_filters_and_session_positions(self):
        before = api.FIXTURE.read_bytes()
        query = {"demo": "1", "wallet": q.PORTFOLIO}
        with no_network(), patch.object(
            ledger.Store, "append", side_effect=AssertionError("GET attempted write")
        ), patch.object(
            ledger.Store, "create", side_effect=AssertionError("GET attempted creation")
        ):
            d = api.get(query)
            first = api.get({**query, "resource": "events", "limit": "3"})
            second = api.get({**query, "resource": "events", "limit": "3", "offset": "3"})
            self.assertEqual((first["total"], first["next_offset"]), (27, 3))
            self.assertTrue(
                {e["event_id"] for e in first["items"]}.isdisjoint(
                    e["event_id"] for e in second["items"]
                )
            )
            historical = api.get({**query, "session": "2026-04-17"})
            self.assertEqual(historical["positions"][0]["quantity"], "100")
            self.assertEqual(historical["positions"][0]["available"], "0")
            self.assertEqual(historical["summary"]["equity"], "99990.00")
            filtered = api.get(
                {
                    **query,
                    "resource": "sessions",
                    "from": "2026-04-20",
                    "to": "2026-04-22",
                }
            )
            self.assertEqual(
                [p["session"] for p in filtered["items"]], ["2026-04-20", "2026-04-22"]
            )
        self.assertEqual(api.FIXTURE.read_bytes(), before)
        self.assertEqual(d["mark"]["session"], "2026-04-24")
        self.assertEqual(len(d["curve"]), 5)
        self.assertEqual(len(d["trades"]), 3)
        self.assertEqual(d["last_reconciliation"]["status"], "RECONCILED")
        self.assertEqual(d["portfolio"]["scientific_identity"], None)
        self.assertEqual(len(d["future"]), 0)

    def test_invalid_read_queries_and_corrupt_export(self):
        query = {"demo": "1", "wallet": q.PORTFOLIO}
        for field, value in (
            ("limit", "0"),
            ("limit", "101"),
            ("offset", "-1"),
            ("resource", "write"),
            ("session", "2026-04-21"),
            ("from", "20260420"),
            ("limit", "nan"),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                api.get({**query, field: value})
        artifact = json.loads(api.FIXTURE.read_text(encoding="utf-8"))
        artifact["checkpoint"]["state"]["financial"]["settled_cash"] = "0"
        with patch.object(b, "read", return_value=artifact), self.assertRaisesRegex(
            ValueError, "hash_mismatch"
        ):
            api.get(query)


if __name__ == "__main__":
    unittest.main()
