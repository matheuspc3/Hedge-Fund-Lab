"""Offline financial, proposal, recovery and dashboard qualification; stdlib unittest."""

import copy
import http.client
import json
import shutil
import socket
import sys
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "dashboard")]
import multiasset_manager as manager  # noqa: E402
import multiasset_portfolio as book  # noqa: E402
import portfolio_api  # noqa: E402
import run_multiasset_portfolio as cli  # noqa: E402
import server  # noqa: E402

from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

DAY = "2026-10-09"
AT = DAY + "T19:00:00-03:00"
EXPIRY = DAY + "T22:00:00-03:00"
PRICES = {
    "PETR4": "40.00",
    "VALE3": "60.00",
    "ITUB4": "30.00",
    "WEGE3": "50.00",
    "BBAS3": "25.00",
}
CONNECT = socket.create_connection


def op(oid, symbol="PETR4", side="BUY", quantity="100", dependencies=None):
    deps = dependencies or []
    return {
        "operation_id": oid,
        "ticker": symbol,
        "side": side,
        "quantity": quantity,
        "limit_price": PRICES[symbol],
        "cost_ceiling": "100.00",
        "funding_source": ("SETTLEMENT" if deps else "SETTLED_CASH")
        if side == "BUY"
        else None,
        "priority": 1 if side == "SELL" else 2,
        "dependencies": deps,
        "reasoning": "SYNTHETIC fixture, not investment advice.",
    }


class AccountingChecks(unittest.TestCase):
    def setUp(self):
        self.root = book.OUTPUT / ("demo-check-" + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.store = book.Store(self.root)
        self.offline = no_network()
        self.offline.__enter__()
        self.store.append(
            "INITIALIZED",
            {
                "policy": book.POLICY,
                "portfolio_id": self.root.name,
                "capital": "100000.00",
                "marks": book.marks(DAY, PRICES),
            },
            "init",
        )

    def tearDown(self):
        self.offline.__exit__(None, None, None)
        self.assertEqual(self.root.resolve().parent, book.OUTPUT.resolve())
        shutil.rmtree(self.root)

    def state(self):
        return self.store.load()[0]

    def reserve(self, ops, command="reserve", at=None, expiry=None):
        state = self.state()
        at = at or state["marks"]["session"] + "T19:00:00-03:00"
        expiry = expiry or state["marks"]["session"] + "T22:00:00-03:00"
        approval = book.demo_approval(
            state,
            ops,
            proposal_sha256="fixture",
            risk_sha256="fixture",
            at=at,
            expires_at=expiry,
        )
        payload = {
            "operations": ops,
            "approval": approval,
            "state_sha256": book.financial_hash(state),
            "at": at,
        }
        self.store.append("RESERVED", payload, command)
        return payload

    def fill(self, command="fill", at=None):
        state = self.state()
        at = at or state["marks"]["session"] + "T19:00:00-03:00"
        payload = {
            "reserved_state_sha256": book.financial_hash(state),
            "session": state["marks"]["session"],
            "at": at,
        }
        self.store.append("FILLED", payload, command)
        return payload

    def buy(self, ops=None):
        self.reserve(ops or [op("buy")])
        self.fill()

    def settle(self, oid, command=None, day=None):
        day = day or self.state()["executions"][oid]["due_session"]
        payload = {
            "operation_id": oid,
            "session": day,
            "confirmation_source": "SYNTHETIC_CUSTODIAN_CONFIRMATION",
        }
        self.store.append("SETTLED", payload, command or "settle-" + oid)
        if day > self.state()["marks"]["session"]:
            self.store.append(
                "MARKED",
                {"marks": book.marks(day, self.state()["marks"]["prices"])},
                "mark-" + (command or oid),
            )
        return payload

    def test_initial_cash_and_decimal_boundaries(self):
        view = book.view(self.state())
        self.assertEqual(view["equity"], "100000.00")
        self.assertEqual(view["cash_weight"], "1")
        for value in (True, 1.0, "NaN", "Infinity"):
            with self.assertRaises((ValueError, ArithmeticError)):
                book.dec(value)
        for value in ("0", "-1", "0.5"):
            with self.assertRaises(ValueError):
                book.units(value)
        for root in (
            ROOT,
            ROOT / "data/forward/demo",
            ROOT / "data/radar/demo",
            book.OUTPUT / "live-one",
            book.OUTPUT / "demo-test/nested",
        ):
            with self.assertRaises(ValueError):
                book.Store(root)

    def test_buy_multiple_reserves_cost_basis_and_unsettled_units(self):
        self.reserve([op("a"), op("b", "VALE3", quantity="200")])
        view = book.view(self.state())
        self.assertEqual(view["cash"]["reserved"], "16200.00")
        self.assertEqual(view["cash"]["available"], "83800.00")
        self.fill()
        view = book.view(self.state())
        self.assertEqual(view["equity"], "99984.00")
        self.assertEqual(view["positions"]["PETR4"]["basis"], "4004.00")
        self.assertEqual(view["positions"]["PETR4"]["available"], "0")
        self.settle("a")
        self.assertEqual(
            book.view(self.state())["positions"]["PETR4"]["available"], "100"
        )

    def test_insufficient_cash_short_and_concentration(self):
        for item in (
            op("too-big", quantity="3000"),
            op("concentrated", quantity="1000"),
            op("short", side="SELL"),
        ):
            with self.assertRaises(ValueError):
                self.reserve([item])
        self.assertEqual(len(self.store.load()[1]), 1)

    def test_partial_sale_and_total_sale_without_purchase(self):
        self.buy()
        self.settle("buy")
        self.reserve([op("partial", side="SELL", quantity="40")], "r-part")
        self.fill("f-part")
        view = book.view(self.state())
        self.assertEqual(view["positions"]["PETR4"]["quantity"], "60")
        self.assertEqual(view["cash"]["settled"], "95996.00")
        self.assertEqual(view["cash"]["receivable"], "1598.40")
        self.assertEqual(view["realized_pnl"], "-3.20")
        self.reserve([op("total", side="SELL", quantity="60")], "r-total")
        self.fill("f-total")
        self.assertEqual(book.view(self.state())["positions"]["PETR4"]["basis"], "0.00")
        self.assertEqual(len(self.state()["executions"]), 3)

    def test_receivable_not_spendable_and_dependency_waits(self):
        self.buy([op("p", quantity="900"), op("v", "VALE3", quantity="600")])
        self.settle("p")
        self.settle("v")
        self.reserve([op("sale", side="SELL", quantity="900")], "r-sale")
        self.fill("f-sale")
        for item in (
            op("cash", "ITUB4", quantity="1000"),
            op("dependent", "ITUB4", dependencies=["sale"]),
        ):
            with self.assertRaises(ValueError):
                self.reserve([item], "r-new")
        with self.assertRaisesRegex(ValueError, "not_due"):
            self.settle("sale", day="2026-10-15")
        self.settle("sale")
        self.reserve([op("dependent", "ITUB4", dependencies=["sale"])], "r-next")
        self.fill("f-next")

    def test_duplicate_ids_legs_and_idempotent_retry(self):
        payload = self.reserve([op("one")])
        self.store.append("RESERVED", payload, "reserve")
        count = len(self.store.load()[1])
        filled = self.fill()
        self.store.append("FILLED", filled, "fill")
        self.assertEqual(len(self.store.load()[1]), count + 1)
        for ops in ([op("one")], [op("x"), op("x")], [op("x"), op("y")]):
            with self.assertRaisesRegex(ValueError, "duplicate"):
                self.reserve(ops, "another")
        with self.assertRaisesRegex(ValueError, "idempotency_conflict"):
            self.store.append("FILLED", {**filled, "session": "2026-10-08"}, "fill")

    def test_crash_before_after_commit_and_recovery(self):
        payload = self.reserve([op("crash")])
        self.store.append("CANCELLED", {}, "cancel")
        state = self.state()
        ops = [op("second")]
        payload = {
            "operations": ops,
            "approval": book.demo_approval(
                state,
                ops,
                proposal_sha256="fixture",
                risk_sha256="fixture",
                at=AT,
                expires_at=EXPIRY,
            ),
            "state_sha256": book.financial_hash(state),
            "at": AT,
        }
        for stage in ("before_event", "after_event"):
            with self.assertRaisesRegex(RuntimeError, "simulated_crash"):
                self.store.append("RESERVED", payload, "second-reserve", crash=stage)
        self.assertEqual(len(self.state()["pending"]), 1)
        self.store.recover()
        self.store.append("RESERVED", payload, "second-reserve")
        state = self.state()
        fill = {
            "reserved_state_sha256": book.financial_hash(state),
            "session": DAY,
            "at": AT,
        }
        with self.assertRaises(RuntimeError):
            self.store.append("FILLED", fill, "second-fill", crash="before_event")
        self.assertEqual(len(self.state()["executions"]), 0)
        with self.assertRaises(RuntimeError):
            self.store.append("FILLED", fill, "second-fill", crash="after_event")
        self.store.append("FILLED", fill, "second-fill")
        self.assertEqual(len(self.state()["executions"]), 1)
        self.assertTrue(self.store.verify()["ok"])

    def test_chain_snapshot_tamper_missing_event_and_lock(self):
        path = self.root / "events/00000001.json"
        original = path.read_bytes()
        data = json.loads(original)
        data["payload"]["capital"] = "200000.00"
        book.write(path, data)
        self.assertFalse(self.store.verify()["ok"])
        book.write(path, original)
        path.unlink()
        self.assertFalse(self.store.verify()["ok"])
        book.write(path, original)
        with book._exclusive_state_lock(self.root / "operation"):
            with self.assertRaises(RuntimeError):
                self.store.append("CANCELLED", {}, "locked")

    def test_expiry_rejection_and_stale_approval(self):
        state = self.state()
        ops = [op("x")]
        approval = book.demo_approval(
            state,
            ops,
            proposal_sha256="fixture",
            risk_sha256="fixture",
            at=AT,
            expires_at=EXPIRY,
            action="REJECT",
        )
        payload = {
            "operations": ops,
            "approval": approval,
            "state_sha256": book.financial_hash(state),
            "at": AT,
        }
        with self.assertRaises(ValueError):
            self.store.append("RESERVED", payload, "rejected")
        payload["approval"] = book.demo_approval(
            state,
            ops,
            proposal_sha256="fixture",
            risk_sha256="fixture",
            at=AT,
            expires_at=EXPIRY,
        )
        payload["at"] = EXPIRY
        with self.assertRaisesRegex(ValueError, "expired"):
            self.store.append("RESERVED", payload, "expired")
        payload["at"] = AT
        self.store.append(
            "MARKED", {"marks": book.marks("2026-10-13", PRICES)}, "new-mark"
        )
        with self.assertRaisesRegex(ValueError, "stale"):
            self.store.append("RESERVED", payload, "stale")

    def test_settlement_calendar_holiday_year_boundary(self):
        self.assertEqual(book.settlement_day(DAY), "2026-10-14")
        self.assertEqual(book.settlement_day("2026-12-23"), "2026-12-29")
        with self.assertRaises(ValueError):
            book.settlement_day("2026-12-30")

    def test_corporate_cash_split_and_unreconciled_fraction(self):
        self.buy()
        self.settle("buy")
        base = {
            "event_id": "div",
            "ticker": "PETR4",
            "source": "SYNTHETIC_ISSUER",
            "source_sha256": "a" * 64,
            "effective_session": "2026-10-14",
            "eligible_quantity": "100",
            "reconciled": True,
        }
        self.store.append(
            "CORPORATE",
            {
                **base,
                "type": "JCP",
                "gross_amount": "100.00",
                "withholding": "17.50",
                "net_amount": "82.50",
                "due_session": "2026-10-14",
            },
            "jcp",
        )
        self.assertEqual(book.view(self.state())["cash"]["receivable"], "82.50")
        self.store.append(
            "CORPORATE_PAID",
            {
                "event_id": "div",
                "session": "2026-10-14",
                "confirmation_source": "SYNTHETIC_BANK",
            },
            "paid",
        )
        self.store.append(
            "CORPORATE",
            {
                **base,
                "event_id": "split",
                "type": "SPLIT",
                "factor": "2",
                "raw_mark_after": "20.00",
            },
            "split",
        )
        self.assertEqual(self.state()["positions"]["PETR4"]["quantity"], "200")
        self.store.append(
            "CORPORATE",
            {
                **base,
                "eligible_quantity": "200",
                "event_id": "group",
                "type": "REVERSE_SPLIT",
                "factor": "0.03",
                "raw_mark_after": "666.67",
            },
            "group",
        )
        self.assertIn("PETR4", self.state()["blocked"])
        with self.assertRaisesRegex(ValueError, "corporate_event"):
            self.reserve([op("blocked")], "blocked")

    def test_accounting_property_many_rounding_sequences(self):
        # Differing integer sizes force proportional cent rounding; no money/units created.
        self.store.append(
            "MARKED",
            {"marks": book.marks(DAY, {**PRICES, "PETR4": "40.26"})},
            "rounding-marks",
        )
        for index in range(6):
            q = str(index + 20)
            oid = "b" + str(index)
            self.reserve([{**op(oid, quantity=q), "limit_price": "40.26"}], "r" + oid)
            self.fill("f" + oid)
            self.settle(oid)
            partial = "partial" + str(index)
            self.reserve(
                [{**op(partial, side="SELL", quantity="1"), "limit_price": "40.26"}],
                "r" + partial,
            )
            self.fill("f" + partial)
            sell = "s" + str(index)
            self.reserve(
                [
                    {
                        **op(sell, side="SELL", quantity=str(int(q) - 1)),
                        "limit_price": "40.26",
                    }
                ],
                "r" + sell,
            )
            self.fill("f" + sell)
            self.settle(partial)
            self.settle(sell)
            state = self.state()
            view = book.view(state)
            self.assertEqual(
                book.dec(view["equity"]) + book.dec(view["costs"]), book.dec("100000.00")
            )
            self.assertEqual(state["positions"]["PETR4"]["quantity"], "0")
            self.assertEqual(state["positions"]["PETR4"]["basis"], "0.00")


class ManagerChecks(unittest.TestCase):
    setUp = AccountingChecks.setUp
    tearDown = AccountingChecks.tearDown
    state = AccountingChecks.state
    reserve = AccountingChecks.reserve
    fill = AccountingChecks.fill
    buy = AccountingChecks.buy
    settle = AccountingChecks.settle

    def context(self):
        return manager.fixture_context(self.state()["marks"]["session"])

    def make(self, ops=None):
        return cli.manual(
            self.state(),
            self.context(),
            ops or [],
            "proposal",
            "Synthetic explicit planning fixture.",
        )

    def valid(self, p, context=None, at=None):
        return manager.validate(
            self.state(), p, context or self.context(), at or p["created_at"]
        )

    def change(self, record, **fields):
        return book.sealed(
            {**{k: v for k, v in record.items() if k != "sha256"}, **fields}
        )

    def test_global_buy_selected_opportunities_and_no_op(self):
        context = self.context()
        p = manager.FakePortfolioManager().propose(
            self.state(),
            context,
            {"PETR4": "0.20", "VALE3": "0.20"},
            "0.60",
            record_id="selected",
            at=AT,
            expires_at=EXPIRY,
            reasoning="Choose two; preserve cash despite five buy opinions.",
        )
        report = manager.publish(self.store, p, context, AT)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(len(p["operations"]), 2)
        approval = manager.approve_demo(self.store, p, context, AT)
        manager.execute_demo(self.store, p, context, approval, AT)
        self.assertEqual(set(self.state()["positions"]), {"PETR4", "VALE3"})
        hold = self.make()
        self.assertTrue(self.valid(hold)["valid"])
        self.assertEqual(hold["operations"], [])
        self.assertLess(book.dec(book.view(self.state())["equity"]), book.dec("100000"))

    def test_weight_validation_and_declared_weights_cannot_override_cash(self):
        p = self.make()
        for target, cash in (
            ({"PETR4": "0.3", "VALE3": "0.3"}, "0.6"),
            ({"PETR4": "-0.1"}, "1.1"),
            ({"PETR4": "0.41"}, "0.59"),
        ):
            bad = self.change(p, target_weights=target, target_cash_weight=cash)
            self.assertFalse(self.valid(bad)["valid"])
        bad = self.change(
            p,
            operations=[op("impossible", quantity="3000")],
            target_weights={"PETR4": "0.2"},
            target_cash_weight="0.8",
        )
        self.assertFalse(self.valid(bad)["valid"])
        bad = self.change(p, target_weights={"PETR4": "0.2"}, target_cash_weight="0.8")
        self.assertFalse(self.valid(bad)["valid"])

    def test_sessions_sources_veto_and_lookahead(self):
        p = self.make([op("buy")])
        context = self.context()
        for fields in (
            {"session": "2026-10-08"},
            {"mode": "live"},
            {"generated_at": "2026-10-13T20:00:00-03:00"},
            {"risk_verdict": "VETADO"},
            {"source_family": "other"},
        ):
            changed = copy.deepcopy(context)
            changed["opinions"]["PETR4"] = self.change(
                changed["opinions"]["PETR4"], **fields
            )
            altered = self.change(
                p, opinion_hashes={t: o["sha256"] for t, o in changed["opinions"].items()}
            )
            self.assertFalse(self.valid(altered, changed)["valid"], fields)
        missing = copy.deepcopy(context)
        del missing["opinions"]["PETR4"]
        changed = self.change(
            p, opinion_hashes={t: o["sha256"] for t, o in missing["opinions"].items()}
        )
        self.assertFalse(self.valid(changed, missing)["valid"])

    def test_risk_covariance_matches_matrix_and_correlations(self):
        self.buy([op("p", quantity="500"), op("v", "VALE3", quantity="300")])
        context = self.context()
        report = manager.risk(self.state(), context)
        self.assertEqual(report["status"], "OK", report)
        cov = report["covariance_daily"]
        weights = report["weights"]
        variance = (
            sum(
                float(weights[a]) * float(weights[c]) * float(cov[a][c])
                for a in weights
                for c in weights
            )
            * 252
        )
        self.assertAlmostEqual(float(report["volatility"]) ** 2, variance, places=14)
        self.assertGreater(float(report["correlations"]["PETR4"]["VALE3"]), 0.99)
        a, c = (context["histories"][t][-61:] for t in ("PETR4", "VALE3"))
        ra = [float(a[i][1]) / float(a[i - 1][1]) - 1 for i in range(1, 61)]
        rc = [float(c[i][1]) / float(c[i - 1][1]) - 1 for i in range(1, 61)]
        ma, mc = sum(ra) / 60, sum(rc) / 60
        expected = sum((x - ma) * (y - mc) for x, y in zip(ra, rc, strict=True)) / 59
        self.assertAlmostEqual(float(cov["PETR4"]["VALE3"]), expected, places=15)
        short = copy.deepcopy(context)
        short["histories"]["PETR4"] = short["histories"]["PETR4"][-20:]
        blocked = manager.risk(self.state(), short)
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertIsNone(blocked["volatility"])
        gap = copy.deepcopy(context)
        del gap["histories"]["PETR4"][-10]
        self.assertEqual(manager.risk(self.state(), gap)["status"], "BLOCKED")
        future = copy.deepcopy(context)
        future["histories"]["PETR4"].append(["2026-10-13", "50"])
        self.assertEqual(manager.risk(self.state(), future)["status"], "BLOCKED")

    def test_risk_projected_cash_to_stock_requires_history(self):
        p = self.make([op("buy")])
        context = self.context()
        context["histories"]["PETR4"] = []
        changed = self.change(
            p, risk_report_sha256=manager.risk(self.state(), context)["sha256"]
        )
        result = self.valid(changed, context)
        self.assertFalse(result["valid"])
        self.assertIsNone(result["risk_projected"]["volatility"])
        high = self.context()
        for i, row in enumerate(high["histories"]["PETR4"]):
            row[1] = "100" if i % 2 else "10"
        changed = self.change(
            p, risk_report_sha256=manager.risk(self.state(), high)["sha256"]
        )
        self.assertFalse(self.valid(changed, high)["valid"])

    def test_price_cost_limits_and_no_future_marks(self):
        p = self.make([op("buy")])
        for changes in (
            {"limit_price": "39.00"},
            {"cost_ceiling": "0.00"},
            {"quantity": "-1"},
        ):
            changed_op = {**p["operations"][0], **changes}
            self.assertFalse(self.valid(self.change(p, operations=[changed_op]))["valid"])
        with self.assertRaisesRegex(ValueError, "session"):
            marks = self.change(
                self.state()["marks"], observed_at="2026-10-13T18:00:00-03:00"
            )
            book.checked_marks(marks)

    def test_drawdown_and_daily_global_limits(self):
        self.buy([op("buy", quantity="900")])
        self.settle("buy")
        prices = {**PRICES, "PETR4": "1.00"}
        context = manager.fixture_context("2026-10-14", prices)
        self.store.append("MARKED", {"marks": context["marks"]}, "drop")
        report = manager.risk(self.state(), context)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("portfolio_drawdown_limit", report["errors"])
        self.assertGreater(book.dec(report["drawdown"]), book.dec("0.2"))
        # Limit checks are cumulative by session, rather than reset per proposal.
        state = self.state()
        changed = copy.deepcopy(state)
        context = manager.fixture_context("2026-10-14")
        changed["marks"] = context["marks"]
        template = next(iter(changed["executions"].values()))
        for i in range(10):
            changed["executions"]["old" + str(i)] = {
                **template,
                "trade_session": "2026-10-14",
            }
        p = manager.proposal(
            changed,
            context,
            [op("extra", "BBAS3", quantity="1")],
            {"PETR4": "0.02", "BBAS3": "0.01"},
            "0.97",
            record_id="limit",
            at="2026-10-14T19:00:00-03:00",
            expires_at="2026-10-14T22:00:00-03:00",
            reasoning="Check cumulative global limits.",
        )
        result = manager.validate(changed, p, context, p["created_at"])
        self.assertFalse(result["valid"])
        self.assertEqual(result["errors"][0]["code"], "daily_operation_count_limit")

    def test_rebalance_sell_cash_and_deferred_rotation(self):
        self.buy([op("p", quantity="500"), op("v", "VALE3", quantity="300")])
        self.settle("p")
        self.settle("v")
        context = self.context()
        for name in ("buy", "sell_cash", "partial", "rebalance", "hold", "rotation"):
            p = cli.scenario(self.state(), context, name)
            report = self.valid(p, context)
            self.assertTrue(report["valid"], (name, report["errors"]))
            if name == "sell_cash":
                self.assertTrue(all(o["side"] == "SELL" for o in p["operations"]))
            if name == "rotation":
                self.assertEqual(len(report["ready_operations"]), 1)
                self.assertEqual(len(report["deferred_operations"]), 1)
                self.assertIsNotNone(report["future_conditional"])
                self.assertGreater(book.dec(report["projected"]["cash"]["receivable"]), 0)

    def test_dependency_cycles_duplicate_leg_and_bad_quantities(self):
        p = self.make()
        for operations in (
            [op("x"), op("x")],
            [op("x"), op("y")],
            [op("x", quantity="0.5")],
            [op("x", dependencies=["x"])],
            [op("x", dependencies=["unknown"])],
            [op("x", side="SELL", quantity="101")],
        ):
            changed = self.change(p, operations=operations)
            self.assertFalse(self.valid(changed)["valid"])

    def test_hash_tampering_expiry_human_rejection_and_state_change(self):
        context = self.context()
        p = self.make([op("buy")])
        altered = copy.deepcopy(p)
        altered["operations"][0]["quantity"] = "101"
        self.assertFalse(self.valid(altered)["valid"])
        for field in (
            "state_sha256",
            "risk_report_sha256",
            "marks_sha256",
            "limits_sha256",
        ):
            self.assertFalse(self.valid(self.change(p, **{field: "0" * 64}))["valid"])
        self.assertFalse(self.valid(p, at=EXPIRY)["valid"])
        manager.publish(self.store, p, context, AT)
        approval = manager.approve_demo(self.store, p, context, AT, action="REJECT")
        with self.assertRaises(ValueError):
            manager.execute_demo(self.store, p, context, approval, AT)
        self.assertEqual(len(self.state()["executions"]), 0)
        self.store.append(
            "MARKED", {"marks": book.marks("2026-10-13", PRICES)}, "advance"
        )
        self.assertFalse(self.valid(p, context)["valid"])

    def test_registered_validation_cannot_be_bypassed(self):
        context = self.context()
        p = self.make([op("buy")])
        manager.publish(self.store, p, context, AT)
        approval = manager.approve_demo(self.store, p, context, AT)
        bad = copy.deepcopy(context)
        bad["histories"]["PETR4"] = []
        with self.assertRaises(ValueError):
            manager.execute_demo(self.store, p, bad, approval, AT)
        with self.assertRaises(ValueError):
            self.store.append(
                "RESERVED",
                {
                    "operations": [op("other")],
                    "approval": approval,
                    "state_sha256": book.financial_hash(self.state()),
                    "at": AT,
                },
                "bypass",
            )

    def test_recovery_reserved_global_basket_no_duplicate(self):
        context = self.context()
        p = self.make([op("buy")])
        manager.publish(self.store, p, context, AT)
        approval = manager.approve_demo(self.store, p, context, AT)
        payload = {
            "operations": [op("buy")],
            "approval": approval,
            "state_sha256": book.financial_hash(self.state()),
            "at": AT,
        }
        with self.assertRaises(RuntimeError):
            self.store.append(
                "RESERVED", payload, "reserve-proposal", crash="after_event"
            )
        cli.recover_demo(self.store)
        cli.recover_demo(self.store)
        self.assertEqual(len(self.state()["executions"]), 1)
        self.assertTrue(self.store.verify()["ok"])

    def test_real_sealed_radar_adapter_is_readonly(self):
        root = ROOT / "data/radar/demo-v4"
        if not root.exists():
            self.skipTest(
                "Local V4 demo not distributed in Git; archive remains available."
            )
        before = {
            str(p): book.digest(p.read_bytes().hex())
            for p in root.rglob("*")
            if p.is_file()
        }
        opinions = manager.radar_opinions(root, list(PRICES), DAY)
        histories = manager.adjusted_histories(root, opinions)
        self.assertEqual(len(opinions), 5)
        self.assertEqual(len(histories), 5)
        for item in opinions.values():
            self.assertEqual(item["origin"], "SEALED_RADAR_V4")
        after = {
            str(p): book.digest(p.read_bytes().hex())
            for p in root.rglob("*")
            if p.is_file()
        }
        self.assertEqual(before, after)

    def test_sector_metadata_reported_only_when_reliable(self):
        self.buy()
        context = self.context()
        self.assertIsNone(manager.risk(self.state(), context)["sector_exposure"])
        context["sectors"] = book.sealed(
            {
                "source": "SYNTHETIC_SECTOR_FIXTURE",
                "reliable": True,
                "mapping": {"PETR4": "Energia"},
            }
        )
        report = manager.risk(self.state(), context)
        self.assertEqual(
            report["sector_exposure"]["Energia"],
            book.view(self.state())["positions"]["PETR4"]["weight"],
        )
        context["sectors"] = self.change(context["sectors"], reliable=False)
        self.assertEqual(manager.risk(self.state(), context)["status"], "BLOCKED")


class IntegrationChecks(unittest.TestCase):
    def setUp(self):
        self.root = book.OUTPUT / ("demo-integration-" + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.offline = no_network()
        self.offline.__enter__()

    tearDown = AccountingChecks.tearDown

    def test_full_demo_a_to_e_and_dashboard_readonly_scenarios(self):
        report = cli.demo(self.root)
        self.assertEqual(report["provider_calls"], 0)
        self.assertTrue(report["verification"]["ok"])
        self.assertEqual(
            [c["validation"]["valid"] for c in report["cases"]],
            [True, True, True, True, False],
        )
        b_case, c_case, d_case = report["cases"][1:4]
        self.assertEqual(b_case["after"]["cash"]["receivable"], "3996.00")
        self.assertEqual(
            b_case["before"]["cash"]["available"], b_case["after"]["cash"]["available"]
        )
        self.assertEqual(c_case["before"]["cash"]["receivable"], "0")
        self.assertEqual(
            d_case["before"]["state_sha256"], d_case["after"]["state_sha256"]
        )
        before = {str(p): book.sha_file(p) for p in self.root.rglob("*") if p.is_file()}
        with patch.object(portfolio_api, "ROOT", self.root), patch.object(
            manager.radar.RadarGeminiClient,
            "generate",
            side_effect=AssertionError("Dashboard inferred"),
        ):
            status = portfolio_api.get("status", {})
            self.assertEqual(len(status["opportunities"]), 5)
            for name in portfolio_api.SCENARIOS:
                scenario = portfolio_api.get("scenario", {"name": name})
                self.assertTrue(
                    scenario["validation"]["valid"],
                    (name, scenario["validation"]["errors"]),
                )
            for case in "ABCDE":
                self.assertIn("proposal", portfolio_api.get("case", {"case": case}))
        after = {str(p): book.sha_file(p) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_http_host_origin_get_readonly_and_no_execution_endpoint(self):
        cli.demo(self.root)
        before = {str(p): book.sha_file(p) for p in self.root.rglob("*") if p.is_file()}
        with patch.object(portfolio_api, "ROOT", self.root), patch.object(
            manager.radar.RadarGeminiClient,
            "generate",
            side_effect=AssertionError("HTTP inferred"),
        ):
            with server.ReusableTCPServer(("127.0.0.1", 0), server.Handler) as httpd:
                threading.Thread(target=httpd.serve_forever, daemon=True).start()
                port = httpd.server_address[1]
                connection = http.client.HTTPConnection("127.0.0.1", port)
                connection._create_connection = CONNECT
                try:
                    for path in (
                        "/portfolio",
                        "/portfolio.css",
                        "/portfolio.js",
                        "/api/portfolio/status",
                        "/api/portfolio/scenario?name=rotation",
                        "/api/portfolio/case?case=E",
                    ):
                        connection.request("GET", path)
                        response = connection.getresponse()
                        response.read()
                        self.assertEqual(response.status, 200, path)
                    connection.request(
                        "GET", "/api/portfolio/status", headers={"Host": "evil.example"}
                    )
                    response = connection.getresponse()
                    response.read()
                    self.assertEqual(response.status, 403)
                    connection.request(
                        "GET",
                        "/api/portfolio/status",
                        headers={"Origin": "https://evil.example"},
                    )
                    response = connection.getresponse()
                    response.read()
                    self.assertEqual(response.status, 403)
                    headers = {
                        "Origin": f"http://127.0.0.1:{port}",
                        "Content-Type": "application/json",
                        "X-CSRF-Token": server.forward_jobs.JOBS.csrf,
                    }
                    connection.request("POST", "/api/portfolio/execute", "{}", headers)
                    response = connection.getresponse()
                    response.read()
                    self.assertEqual(response.status, 404)
                    for path in (
                        "/api/portfolio/scenario?name=bad",
                        "/api/portfolio/status?root=../../data/forward",
                        "/api/portfolio/case?case=AA",
                        "/api/portfolio/status?x=1&x=2",
                    ):
                        connection.request("GET", path)
                        response = connection.getresponse()
                        response.read()
                        self.assertEqual(response.status, 400)
                    connection.request("GET", "/../data/forward/h2_v6_paper/state.json")
                    response = connection.getresponse()
                    response.read()
                    self.assertEqual(response.status, 404)
                finally:
                    connection.close()
                    httpd.shutdown()
        self.assertEqual(
            before,
            {str(p): book.sha_file(p) for p in self.root.rglob("*") if p.is_file()},
        )
        with self.assertRaises(RuntimeError):
            socket.create_connection(("example.com", 443))

    def test_original_scientific_radar_and_ledger_preservation(self):
        baseline = book.read(
            ROOT / "docs/evidence/hfl_multiasset_portfolio/preservation_baseline.json"
        )
        for name, expected in baseline.items():
            path = ROOT / name
            if not path.exists() and name.startswith("data/"):
                continue  # Ignored local records can be absent in a clean checkout.
            self.assertEqual(book.sha_file(path), expected, name)
        from src.experiments.h2_evaluation_manifest import verify_manifest

        result = verify_manifest(
            manager.radar.CANDIDATE,
            manager.radar.CANDIDATE.with_suffix(".sha256").read_text().strip(),
            clean=False,
        )
        self.assertEqual(len(result["sources_sha256"]), 73)


if __name__ == "__main__":
    unittest.main()
