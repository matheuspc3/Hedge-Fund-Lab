"""Offline integration and negative checks for the versioned PAPER-02 bridge."""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack, closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "tests")]

import qualify_pilot_paper as q  # noqa: E402
from test_pilot_market_data import reseal  # noqa: E402

p, b = q.pilot, q.b
PID, REF = q.WALLETS
D0, D1 = q.SESSIONS[:2]


class PilotPaperChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        q.offline(cls.stack)
        cls.root = Path(
            cls.stack.enter_context(tempfile.TemporaryDirectory(prefix="hfl-paper-base-"))
        )
        cls.calendar, cls.bundles = q.fixture_inputs(cls.root)
        store = p.Store.create(cls.root / "ledger.sqlite3")
        for pid, strategy in zip(q.WALLETS, (p.AGENTS, p.REFERENCE), strict=True):
            q.initialize(store, pid, strategy, cls.calendar, cls.bundles[D0])
        cls.addClassCleanup(cls.stack.close)

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(
            self.stack.enter_context(
                tempfile.TemporaryDirectory(prefix="hfl-paper-test-")
            )
        )
        shutil.copy2(self.__class__.root / "ledger.sqlite3", self.root / "ledger.sqlite3")
        self.store = p.Store(self.root / "ledger.sqlite3", writable=True)

    def state(self, pid=PID):
        return self.store.load(pid)[0]

    def ops(self, side="BUY", quantity="100"):
        return [p.operation(self.state(), "test-operation", "PETR4", side, quantity)]

    def pending(self, pid=PID):
        ops = self.ops() if pid == PID else p.reference_operations(self.state(REF))
        record, auth = q.prepare(self.store, pid, D0, ops)
        return record, auth

    def execute(self, record, auth, *, pid=PID, quote=None, processed=None, crash=None):
        return q.command(
            self.store,
            pid,
            "PAPER_ORDER_EXECUTED",
            {
                "quote": q.quote(self.bundles[D1]) if quote is None else quote,
                "processed_at": processed or D1 + "T18:10:00-03:00",
            },
            "test-fill",
            record["target_open_at"],
            authorization_ref=auth["event_id"],
            crash=crash,
        )

    def link_validate(self, record):
        q.command(
            self.store,
            PID,
            "PROPOSAL_LINKED",
            {"record": record},
            "proposal",
            record["decision_at"],
        )
        q.command(
            self.store,
            PID,
            "VALIDATION_RECORDED",
            {"proposal_id": record["record_id"]},
            "validation",
            D0 + "T18:25:00-03:00",
        )

    def test_complete_eight_session_rehearsal(self):
        with tempfile.TemporaryDirectory(prefix="hfl-paper-cycle-") as temp:
            result = q.run(Path(temp))
            agents, reference = result["wallets"]
            self.assertEqual(agents["summary"]["equity"], "100039.36")
            self.assertEqual(reference["summary"]["equity"], "101744.07")
            self.assertEqual(agents["summary"]["positions"]["PETR4"]["quantity"], "60")
            self.assertEqual(
                reference["initial_targets"], dict.fromkeys(q.data.UNIVERSE, "0.20")
            )
            self.assertNotEqual(
                reference["initial_targets"], reference["realized_weights"]
            )
            self.assertEqual(agents["summary"]["costs"], "5.64")
            self.assertEqual(reference["summary"]["costs"], "98.03")
            for wallet in result["wallets"]:
                self.assertEqual(len(wallet["history"]), 8)
                self.assertEqual(wallet["classification"], "SYNTHETIC_TEST")
                self.assertEqual(wallet["summary"]["cash"]["reserved"], "0")
                self.assertEqual(wallet["summary"]["cash"]["receivable"], "0")
                self.assertTrue(
                    all(
                        b.dec(pos["unsettled"]) == 0
                        for pos in wallet["summary"]["positions"].values()
                    )
                )
                for point in wallet["history"]:
                    v = point["view"]
                    self.assertEqual(
                        b.dec(v["equity"]),
                        b.dec(v["initial_capital"])
                        + b.dec(v["realized_pnl"])
                        + b.dec(v["income_net"])
                        + b.dec(v["unrealized_pnl"]),
                    )
                    self.assertEqual(
                        b.dec(v["equity"]),
                        b.dec(v["cash"]["settled"])
                        + b.dec(v["cash"]["receivable"])
                        + sum(
                            (
                                b.dec(pos["market_value"])
                                for pos in v["positions"].values()
                            ),
                            b.ZERO,
                        ),
                    )
                store = p.Store(Path(temp) / "ledger.sqlite3")
                state, events, checkpoint = store.load(wallet["portfolio_id"])
                self.assertTrue(store.verify(wallet["portfolio_id"])["ok"])
                self.assertEqual(p.replay(events, checkpoint), state)
                self.assertTrue(
                    all(e["portfolio_id"] == wallet["portfolio_id"] for e in events)
                )
                self.assertEqual(
                    len(state["financial"]["settlements"]), len(wallet["trades"])
                )
                for trade in wallet["trades"]:
                    proposal = state["proposals"][trade["proposal_id"]]
                    approved = next(
                        op
                        for op in proposal["operations"]
                        if op["operation_id"] == trade["operation"]["operation_id"]
                    )
                    self.assertEqual(approved, trade["operation"])
                    self.assertLess(
                        q.data.instant(trade["authorized_at"]),
                        q.data.instant(trade["test_target_open_at"]),
                    )
                    self.assertLess(trade["decision_session"], trade["trade_session"])
                    self.assertIsNone(trade["economic_at"])
                    self.assertGreater(
                        q.data.instant(trade["processed_at"]),
                        q.data.instant(trade["test_target_open_at"]),
                    )
                self.assertEqual(
                    wallet["periods"]["last_12_months"]["status"], "INSUFFICIENT_HISTORY"
                )
            self.assertEqual(len(agents["trades"]), 2)
            self.assertEqual(len(reference["trades"]), 5)
            self.assertEqual(agents["decisions"][0]["action"], "HOLD")
            self.assertEqual(result["comparison"]["status"], "AVAILABLE")
            for points in result["comparison"]["series"].values():
                self.assertEqual(b.dec(points[0]["value"]), 100)
            self.assertNotIn("total_equity", result)
            self.assertTrue((Path(temp) / "projection.json").is_file())

    def test_missing_authorization(self):
        record = p.proposal(
            self.state(),
            self.ops(),
            "missing-auth",
            risk_fixture=q.risk_fixture(self.state()),
        )
        self.link_validate(record)
        with self.assertRaisesRegex(ValueError, "ex_ante_authorization"):
            q.command(
                self.store,
                PID,
                "PAPER_ORDER_CREATED",
                {"proposal_id": record["record_id"]},
                "order",
                D0 + "T18:35:00-03:00",
            )
        self.assertFalse(self.state()["financial"]["pending"])

    def test_late_authorization(self):
        record = p.proposal(
            self.state(), self.ops(), "late", risk_fixture=q.risk_fixture(self.state())
        )
        self.link_validate(record)
        with self.assertRaisesRegex(ValueError, "authorization_missing_late"):
            q.command(
                self.store,
                PID,
                "AUTHORIZATION_RECORDED",
                {
                    "proposal_id": "late",
                    "operator": "SYNTHETIC_TEST_OPERATOR",
                    "expires_at": record["expires_at"],
                },
                "auth",
                record["target_open_at"],
            )

    def test_economic_authorization_expired_before_open(self):
        record = p.proposal(
            self.state(), self.ops(), "expired", risk_fixture=q.risk_fixture(self.state())
        )
        record["expires_at"] = D1 + "T09:59:00-03:00"
        record = b.sealed({k: v for k, v in record.items() if k != "sha256"})
        with self.assertRaisesRegex(ValueError, "proposal_state_or_clock_invalid"):
            p.validate(self.state(), record)

    def test_processing_deadline_expired(self):
        record, auth = self.pending()
        with self.assertRaisesRegex(ValueError, "execution_clock_changed"):
            self.execute(record, auth, processed=D1 + "T23:01:00-03:00")
        self.assertFalse(self.state()["trades"])

    def test_incompatible_reserved_state_change(self):
        record, auth = self.pending()
        state = self.state()
        state["financial"]["settled_cash"] = "100001.00"
        state["financial"]["income_net"] = "1.00"
        event = {
            "kind": "PAPER_ORDER_EXECUTED",
            "payload": {
                "quote": q.quote(self.bundles[D1]),
                "processed_at": D1 + "T18:10:00-03:00",
            },
            "effective_at": record["target_open_at"],
            "session": D1,
            "authority": "SYNTHETIC_TEST_OPERATOR",
            "source": "ISOLATED_SYNTHETIC_QUALIFICATION",
            "authorization_ref": auth["event_id"],
        }
        with self.assertRaisesRegex(ValueError, "approved_state"):
            p.reduce(state, event)

    def test_missing_open_cancellation_releases_reserve(self):
        record, auth = self.pending()
        with self.assertRaisesRegex(ValueError, "OPEN_unavailable"):
            q.command(
                self.store,
                PID,
                "PAPER_ORDER_EXECUTED",
                {"quote": None, "processed_at": D1 + "T18:10:00-03:00"},
                "no-open",
                record["target_open_at"],
                authorization_ref=auth["event_id"],
            )
        self.assertTrue(self.state()["intent"])
        q.command(
            self.store,
            PID,
            "PAPER_ORDER_CANCELLED",
            {"reason": "OPEN_MISSING_TEST"},
            "cancel",
            D1 + "T18:11:00-03:00",
        )
        self.assertEqual(b.dec(b.view(self.state()["financial"])["cash"]["reserved"]), 0)
        self.assertFalse(self.state()["trades"])
        with self.assertRaisesRegex(ValueError, "economic_clock_backwards"):
            self.execute(record, auth)

    def test_bad_open_blocks_whole_reference_basket(self):
        record, auth = self.pending(REF)
        bundle = copy.deepcopy(self.bundles[D1])
        bar = next(bar for bar in bundle["content"]["bars"] if bar["ticker"] == "VALE3")
        bar["OPEN"] = bar["HIGH"] = "90.00"
        before = self.store.load(REF)[2]
        with self.assertRaisesRegex(ValueError, "OPEN_outside_authorized_limit"):
            self.execute(record, auth, pid=REF, quote=q.quote(reseal(bundle)))
        self.assertEqual(self.store.load(REF)[2], before)
        self.assertFalse(self.state(REF)["financial"]["executions"])

    def test_missing_close_no_snapshot_or_zero(self):
        q.command(
            self.store,
            PID,
            "PORTFOLIO_VALUED",
            {"quote": None, "processed_at": D1 + "T18:10:00-03:00"},
            "no-close",
            D1 + "T18:00:00-03:00",
        )
        q.command(
            self.store,
            PID,
            "PORTFOLIO_RECONCILED",
            {},
            "no-reconcile",
            D1 + "T18:15:00-03:00",
        )
        view = p.projection(self.store, q.WALLETS)["wallets"][0]
        self.assertEqual(view["status"], "UNAVAILABLE")
        self.assertIsNone(view["summary"])
        self.assertEqual(len(view["history"]), 1)
        self.assertEqual(view["last_reconciled"]["session"], D0)
        self.assertEqual(view["periods"]["since_start"]["status"], "UNAVAILABLE")

    def test_insufficient_cash(self):
        record = p.proposal(
            self.state(),
            self.ops(quantity="5000"),
            "cash",
            risk_fixture=q.risk_fixture(self.state()),
        )
        with self.assertRaisesRegex(ValueError, "insufficient_settled_cash"):
            p.validate(self.state(), record)

    def test_insufficient_custody(self):
        record = p.proposal(
            self.state(),
            self.ops(side="SELL"),
            "custody",
            risk_fixture=q.risk_fixture(self.state()),
        )
        with self.assertRaisesRegex(ValueError, "insufficient_available_units"):
            p.validate(self.state(), record)

    def test_retry_conflict_restart_lost_ack(self):
        record, auth = self.pending()
        with self.assertRaisesRegex(RuntimeError, "lost_confirmation"):
            self.execute(record, auth, crash="after_commit")
        committed = self.store.load(PID)[2]
        self.store = p.Store(self.root / "ledger.sqlite3", writable=True)
        _, event = self.execute(record, auth)
        self.assertEqual(self.store.load(PID)[2], committed)
        self.assertEqual(len(self.state()["trades"]), 1)
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.execute(record, auth, processed=D1 + "T18:11:00-03:00")
        self.assertEqual(self.state()["trades"][0]["quantity"], "100")
        self.assertEqual(event["idempotency_key"], "test-fill")

    def test_atomic_rollback(self):
        record, auth = self.pending()
        before = self.store.load(PID)[2]
        with self.assertRaisesRegex(RuntimeError, "before_checkpoint"):
            self.execute(record, auth, crash="after_event")
        self.assertEqual(self.store.load(PID)[2], before)
        self.execute(record, auth)
        self.assertEqual(len(self.state()["trades"]), 1)

    def test_dplus2_insufficient_coverage_blocks_validation(self):
        state = self.state()
        calendar = copy.deepcopy(state["calendar"])
        calendar["sessions"] = [d for d in calendar["sessions"] if d <= D1]
        calendar["sha256"] = q.data.digest(
            {k: v for k, v in calendar.items() if k != "sha256"}
        )
        state["calendar"] = calendar
        bundle = copy.deepcopy(state["quote"]["bundle"])
        bundle["content"]["calendar"] = calendar
        state["quote"]["bundle"] = reseal(bundle)
        record = p.proposal(
            state,
            [p.operation(state, "no-coverage", "PETR4", "BUY", "100")],
            "no-d2",
            risk_fixture=q.risk_fixture(state),
        )
        with self.assertRaisesRegex(ValueError, "calendar_coverage_insufficient"):
            p.validate(state, record)

    def test_accounting_divergence(self):
        state = self.state()
        state["financial"]["settled_cash"] = "99999.99"
        with self.assertRaisesRegex(ValueError, "equity_reconciliation_failed"):
            p.reconciliation(state)
        state = self.state()
        state["financial"]["costs"] = "0.01"
        self.assertIn("costs_execution_total_mismatch", p.reconciliation(state)["errors"])

    def test_checkpoint_corruption_is_detected(self):
        with closing(self.store.connect(write=True)) as connection, connection:
            checkpoint = json.loads(
                connection.execute(
                    "SELECT body FROM checkpoints WHERE portfolio_id=?", (PID,)
                ).fetchone()[0]
            )
            checkpoint["state"]["financial"]["settled_cash"] = "99999.00"
            connection.execute(
                "UPDATE checkpoints SET body=? WHERE portfolio_id=?",
                (json.dumps(checkpoint), PID),
            )
        self.assertFalse(self.store.verify(PID)["ok"])

    def test_explicit_hold_and_absent_decision_are_distinct(self):
        before = p.projection(self.store, q.WALLETS)["wallets"][0]
        self.assertEqual(before["decision_status"], "NO_DECISION")
        record, auth = q.prepare(self.store, PID, D0, [])
        self.assertEqual(record["action"], "HOLD")
        self.assertTrue(self.state()["validations"][record["record_id"]]["valid"])
        self.assertFalse(self.state()["intent"])
        self.assertFalse(self.state()["trades"])
        with self.assertRaisesRegex(ValueError, "authorized_intent_required"):
            self.execute(record, auth)
        after = p.projection(self.store, q.WALLETS)["wallets"][0]
        self.assertEqual(after["decisions"][0]["action"], "HOLD")
        self.assertEqual(after["periods"]["day"]["status"], "INSUFFICIENT_HISTORY")

    def test_wallet_separation(self):
        reference = self.store.load(REF)[2]
        record, auth = self.pending()
        self.execute(record, auth)
        self.assertEqual(self.store.load(REF)[2], reference)
        self.assertFalse(self.state(REF)["financial"]["positions"])
        self.assertNotEqual(
            self.state()["financial"]["portfolio_id"],
            self.state(REF)["financial"]["portfolio_id"],
        )

    def test_unsupported_corporate_event_blocks_session_and_following(self):
        q.command(
            self.store,
            PID,
            "CORPORATE_EVENT_UNSUPPORTED",
            {"ticker": "PETR4", "reason": "SYNTHETIC_SPLIT_NOT_IMPLEMENTED"},
            "corp",
            D1 + "T09:00:00-03:00",
        )
        for day in (D1, q.SESSIONS[2]):
            with self.assertRaisesRegex(ValueError, "unsupported_corporate_event"):
                q.command(
                    self.store,
                    PID,
                    "PORTFOLIO_VALUED",
                    {
                        "quote": q.quote(self.bundles[day]),
                        "processed_at": day + "T18:10:00-03:00",
                    },
                    "mark-" + day,
                    day + "T18:00:00-03:00",
                )
        self.assertEqual(
            p.projection(self.store, q.WALLETS)["wallets"][0]["status"], "UNAVAILABLE"
        )

    def test_availability_is_not_economic_open(self):
        record, auth = self.pending()
        with self.assertRaisesRegex(ValueError, "fixture_not_released"):
            self.execute(record, auth, processed=D1 + "T10:01:00-03:00")
        self.execute(record, auth)
        trade = self.state()["trades"][0]
        self.assertEqual(trade["economic_precision"], "SESSION_OPEN")
        self.assertNotEqual(trade["available_at"], trade["test_target_open_at"])

    def test_import_availability_cannot_be_ignored(self):
        record, auth = self.pending()
        bundle = copy.deepcopy(self.bundles[D1])
        bundle["import"]["imported_at"] = bundle["import"]["available_at"] = (
            D1 + "T19:00:00-03:00"
        )
        bundle = reseal(bundle)
        with self.assertRaisesRegex(ValueError, "data_not_yet_available"):
            self.execute(record, auth, quote=q.quote(bundle))

    def test_reference_quantities_are_fixed_from_close_limits(self):
        record, auth = self.pending(REF)
        quantities = {op["ticker"]: op["quantity"] for op in record["operations"]}
        self.execute(record, auth, pid=REF)
        self.assertEqual(
            {t["operation"]["ticker"]: t["quantity"] for t in self.state(REF)["trades"]},
            quantities,
        )
        op = next(op for op in record["operations"] if op["ticker"] == "PETR4")
        open_price = b.dec(
            self.state(REF)["financial"]["executions"][op["operation_id"]]["raw_price"]
        )
        self.assertNotEqual(
            int(b.dec("20000") / (open_price * b.dec("1.001"))), int(op["quantity"])
        )
        self.assertGreater(
            b.dec(b.view(self.state(REF)["financial"])["exposure"]), b.dec("0.85")
        )

    def test_reference_cannot_claim_twenty_percent_with_arbitrary_quantities(self):
        state = self.state(REF)
        operations = p.reference_operations(state)
        operations[0]["quantity"] = "1"
        record = p.proposal(state, operations, "fake-allocation")
        with self.assertRaisesRegex(ValueError, "ex_ante_equal_budgets"):
            p.validate(state, record)

    def test_turnover_and_cost_limits_apply_to_observed_prices_too(self):
        financial = self.state()["financial"]
        operations = self.ops(quantity="1000")
        p.basket_limits(financial, operations, {"PETR4": "99.00"}, b.dec("99.00"))
        # A SELL gap upward can exceed turnover even when its minimum limit passed.
        with self.assertRaisesRegex(ValueError, "turnover_or_cost_limit"):
            p.basket_limits(financial, operations, {"PETR4": "101.00"}, b.dec("101.00"))
        with self.assertRaisesRegex(ValueError, "turnover_or_cost_limit"):
            p.basket_limits(financial, operations, {"PETR4": "99.00"}, b.dec("1000.01"))

    def test_old_contracts_and_temp_guard_preserved(self):
        self.assertEqual(b.POLICY["max_exposure"], "0.85")
        self.assertEqual(p.ledger.IDENTITY, "HFL-MULTIASSET-PAPER-LEDGER-V1")
        self.assertIs(p.ledger.Store.append.__globals__["reduce"], p.ledger.reduce)
        self.assertIs(b.fill.__globals__["POLICY"], b.POLICY)
        self.assertIs(p.Store.append.__code__, p.ledger.Store.append.__code__)
        self.assertIs(p.Store._load.__code__, p.ledger.Store._load.__code__)
        self.assertIs(p.engine(self.state(REF)).fill.__code__, b.fill.__code__)
        with self.assertRaisesRegex(ValueError, "external_temporary"):
            p.Store.create(ROOT / "ledger.sqlite3")
        with self.assertRaisesRegex(ValueError, "event_chain_or_identity"):
            p.ledger.Store(self.root / "ledger.sqlite3").load(PID)
        state = self.state(REF)["financial"]
        state["positions"]["PETR4"] = {
            **b.position(),
            "quantity": "2400",
            "basis": "96000.00",
        }
        state["settled_cash"] = "4000.00"
        # Original 85% gate still rejects a valid, fully funded 96% state.
        with self.assertRaisesRegex(ValueError, "concentration_or_exposure"):
            b.safety(state)

    def test_fixture_cannot_be_promoted(self):
        state = self.state()
        quote = copy.deepcopy(state["quote"])
        quote["bundle"]["content"]["source"]["nature"] = "REAL_UNVERIFIED"
        quote["bundle"] = reseal(quote["bundle"])
        with self.assertRaises(ValueError):
            p.quote_prices(state, quote, "CLOSE", D0 + "T18:20:00-03:00")

    def test_agents_keep_limits_and_require_risk_history(self):
        state = self.state()
        record = p.proposal(
            state,
            self.ops(quantity="1100"),
            "concentration",
            risk_fixture=q.risk_fixture(state),
        )
        with self.assertRaisesRegex(ValueError, "concentration_or_exposure_limit"):
            p.validate(state, record)
        fixture = q.risk_fixture(state)
        fixture["histories"]["PETR4"] = fixture["histories"]["PETR4"][-1:]
        fixture = b.sealed({k: v for k, v in fixture.items() if k != "sha256"})
        record = p.proposal(state, self.ops(), "risk-history", risk_fixture=fixture)
        with self.assertRaisesRegex(ValueError, "insufficient_aligned_history"):
            p.validate(state, record)

    def test_proposal_requires_current_reconciled_state(self):
        state = self.state()
        state["financial"]["settled_cash"] = "100001.00"
        state["financial"]["income_net"] = "1.00"
        record = p.proposal(
            state, [], "unreconciled-change", risk_fixture=q.risk_fixture(state)
        )
        with self.assertRaisesRegex(ValueError, "proposal_state_or_clock_invalid"):
            p.validate(state, record)

    def test_no_network_even_on_rehearsal_dependencies(self):
        import socket
        import urllib.request

        with socket.socket() as sock, self.assertRaisesRegex(
            AssertionError, "network forbidden"
        ):
            sock.connect(("127.0.0.1", 80))
        with self.assertRaisesRegex(AssertionError, "download forbidden"):
            urllib.request.urlopen("https://example.invalid")


if __name__ == "__main__":
    unittest.main()
