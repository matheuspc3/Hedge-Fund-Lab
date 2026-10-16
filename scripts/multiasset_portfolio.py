"""Event-sourced, pre-funded BRL engine. Synthetic portfolios only; no provider API."""

import copy
import re
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from multiasset_radar import ROOT, digest, read, sha_file, write

from src.backtesting.b3_calendar import B3Calendar
from src.backtesting.daily_agent import _exclusive_state_lock

IDENTITY = "HFL-MULTIASSET-PORTFOLIO-V1"
OUTPUT = ROOT / "data/portfolio/hfl_multiasset_v1"
ZERO = Decimal(0)
CENT = Decimal("0.01")
POLICY = {
    "version": "DEMO_ACCOUNTING_V1",
    "mode": "synthetic",
    "currency": "BRL",
    "rounding": "HALF_EVEN_CENT; BASIS_AUTHORITY; WEIGHT_RESIDUE_TO_CASH",
    "fee_rate": "0.001",
    "taxes": "PRE_IR_NOT_A_TAX_MODEL",
    "max_concentration": "0.40",
    "max_exposure": "0.85",
    "max_volatility": "0.35",
    "max_drawdown": "0.20",
    "max_turnover": "1.00",
    "max_cost_weight": "0.01",
    "max_operations": 10,
    "risk_window": 60,
    "annualization": 252,
    "veto_policy": "NO_OPERATION_ON_VETO; MISSING_OPINION_HOLD_ONLY",
    "settlement_rule": "B3_CASH_EQUITIES_D+2_OC041_2026_CONFIRMED",
    "calendar_year": 2026,
}


def dec(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("decimal_string_required")
    result = Decimal(value)
    if not result.is_finite() or abs(result) > Decimal("1e15"):
        raise ValueError("invalid_decimal")
    return result


def money(value):
    return dec(value).quantize(CENT, rounding=ROUND_HALF_EVEN)


def amount(value, *, positive=False):
    result = dec(value)
    if result < 0 or (positive and result == 0) or result != money(result):
        raise ValueError("invalid_cent_amount")
    return result


def units(value):
    result = dec(value)
    if result <= 0 or result != result.to_integral_value():
        raise ValueError("whole_positive_units_required")
    return result


def ticker(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z]{4}[3-8]", value):
        raise ValueError("invalid_ticker")
    return value


def key(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", value):
        raise ValueError("invalid_record_id")
    return value


def pack(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {k: pack(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [pack(v) for v in value]
    return value


def sealed(value):
    body = pack(value)
    return {**body, "sha256": digest(body)}


def check_seal(value):
    if value.get("sha256") != digest({k: v for k, v in value.items() if k != "sha256"}):
        raise ValueError("record_hash_mismatch")
    return value


def instant(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("timezone_required")
    return result


def session(value):
    if not isinstance(value, str) or not re.fullmatch(r"2026-\d{2}-\d{2}", value):
        raise ValueError("calendar_2026_only")
    day = date.fromisoformat(value)
    if not B3Calendar().is_session(day):
        raise ValueError("not_a_b3_session")
    return day


def settlement_day(value):
    day = session(value)
    for _ in range(2):
        day = B3Calendar().next_session(day)
    session(day.isoformat())
    return day.isoformat()


def folder(root):
    result = Path(root).resolve()
    if (
        not result.is_relative_to(OUTPUT.resolve())
        or result.parent != OUTPUT.resolve()
        or not re.fullmatch(r"demo-[a-zA-Z0-9_-]{1,80}", result.name)
    ):
        raise ValueError("synthetic_portfolio_root_required")
    return result


def implementation():
    return {
        name: sha_file(ROOT / name)
        for name in (
            "scripts/multiasset_portfolio.py",
            "scripts/multiasset_manager.py",
            "scripts/run_multiasset_portfolio.py",
        )
    }


def financial_hash(state):
    return digest(
        {
            k: v
            for k, v in state.items()
            if k not in ("proposals", "approvals", "proposal_contexts")
        }
    )


def position():
    return {"quantity": "0", "reserved": "0", "unsettled": "0", "basis": "0.00"}


def view(state):
    positions = {}
    for symbol, pos in state["positions"].items():
        q, basis = dec(pos["quantity"]), dec(pos["basis"])
        mark = amount(state["marks"]["prices"][symbol], positive=True)
        positions[symbol] = {
            **pos,
            "available": q - dec(pos["reserved"]) - dec(pos["unsettled"]),
            "average_cost": (basis / q).quantize(
                Decimal("0.00000001"), rounding=ROUND_HALF_EVEN
            )
            if q
            else ZERO,
            "raw_mark": mark,
            "market_value": q * mark,
            "unrealized_pnl": q * mark - basis,
        }
    settled = dec(state["settled_cash"])
    reserved = sum((dec(o["cash_reserved"]) for o in state["pending"].values()), ZERO)
    receivables = sum((dec(r["amount"]) for r in state["receivables"].values()), ZERO)
    invested = sum((p["market_value"] for p in positions.values()), ZERO)
    equity = settled + receivables + invested
    if equity <= 0:
        raise ValueError("nonpositive_equity")
    for p in positions.values():
        p["weight"] = (p["market_value"] / equity).quantize(
            Decimal("0.000000000001"), rounding=ROUND_HALF_EVEN
        )
    cash_weight = 1 - sum((p["weight"] for p in positions.values()), ZERO)
    result = {
        "identity": IDENTITY,
        "portfolio_id": state["portfolio_id"],
        "mode": "synthetic",
        "session": state["marks"]["session"],
        "initial_capital": state["initial_capital"],
        "positions": positions,
        "cash": {
            "settled": settled,
            "reserved": reserved,
            "available": settled - reserved,
            "receivable": receivables,
        },
        "cash_weight": cash_weight,
        "receivable_weight": receivables / equity,
        "equity": equity,
        "exposure": invested / equity,
        "costs": state["costs"],
        "realized_pnl": state["realized_pnl"],
        "income_net": state["income_net"],
        "unrealized_pnl": sum((p["unrealized_pnl"] for p in positions.values()), ZERO),
        "drawdown": max(ZERO, 1 - equity / dec(state["peak_equity"])),
        "pending": state["pending"],
        "executions": state["executions"],
        "receivables": state["receivables"],
        "blocked": state["blocked"],
        "state_sha256": financial_hash(state),
    }
    if (
        settled < 0
        or reserved > settled
        or any(p["available"] < 0 or dec(p["basis"]) < 0 for p in positions.values())
    ):
        raise ValueError("accounting_invariant_failed")
    # Every cent is explained by contributions, net realization, income and marks.
    if (
        equity
        != dec(state["initial_capital"])
        + dec(state["realized_pnl"])
        + dec(state["income_net"])
        + result["unrealized_pnl"]
    ):
        raise ValueError("equity_reconciliation_failed")
    return pack(result)


def checked_marks(marks, state=None):
    check_seal(marks)
    session(marks["session"])
    if marks["mode"] != "synthetic" or marks["basis"] != "RAW" or not marks["source"]:
        raise ValueError("synthetic_raw_marks_required")
    if instant(marks["observed_at"]).date() != session(marks["session"]):
        raise ValueError("mark_timestamp_session_mismatch")
    for symbol, price in marks["prices"].items():
        ticker(symbol)
        amount(price, positive=True)
    if state and (
        set(state["positions"]) - set(marks["prices"])
        or marks["session"] < state["marks"]["session"]
    ):
        raise ValueError("missing_or_backdated_marks")


def operation(op):
    if set(op) != {
        "operation_id",
        "ticker",
        "side",
        "quantity",
        "limit_price",
        "cost_ceiling",
        "funding_source",
        "priority",
        "dependencies",
        "reasoning",
    }:
        raise ValueError("invalid_operation_contract")
    key(op["operation_id"])
    ticker(op["ticker"])
    units(op["quantity"])
    amount(op["limit_price"], positive=True)
    amount(op["cost_ceiling"])
    if (
        op["side"] not in ("BUY", "SELL")
        or type(op["priority"]) is not int
        or op["priority"] < 0
        or not op["reasoning"]
    ):
        raise ValueError("invalid_operation")
    if not isinstance(op["dependencies"], list) or len(set(op["dependencies"])) != len(
        op["dependencies"]
    ):
        raise ValueError("invalid_dependencies")
    for dep in op["dependencies"]:
        key(dep)
    if op["funding_source"] != (
        "SETTLED_CASH"
        if op["side"] == "BUY" and not op["dependencies"]
        else "SETTLEMENT"
        if op["side"] == "BUY"
        else None
    ):
        raise ValueError("invalid_funding_source")


def cost(notional):
    return money(notional * dec(POLICY["fee_rate"]))


def safety(state, *, limits=True):
    report = view(state)
    if limits and (
        dec(report["exposure"]) > dec(POLICY["max_exposure"])
        or any(
            dec(p["market_value"])
            > dec(POLICY["max_concentration"]) * dec(report["equity"])
            for p in report["positions"].values()
        )
    ):
        raise ValueError("concentration_or_exposure_limit")
    return report


def reserve(state, operations):
    if state["pending"] or not operations or len(operations) > POLICY["max_operations"]:
        raise ValueError("pending_basket_or_invalid_count")
    ids, legs = set(), set()
    for op in operations:
        operation(op)
        oid, symbol = op["operation_id"], op["ticker"]
        leg = (symbol, op["side"])
        if (
            oid in ids
            or leg in legs
            or oid in state["executions"]
            or oid in state["used_orders"]
        ):
            raise ValueError("duplicate_order")
        ids.add(oid)
        legs.add(leg)
        if symbol in state["blocked"]:
            raise ValueError("corporate_event_unreconciled")
        if any(dep not in state["settlements"] for dep in op["dependencies"]):
            raise ValueError("waiting_for_settlement")
        price = amount(state["marks"]["prices"][symbol], positive=True)
        q = units(op["quantity"])
        if (op["side"] == "BUY" and price > dec(op["limit_price"])) or (
            op["side"] == "SELL" and price < dec(op["limit_price"])
        ):
            raise ValueError("price_limit")
        if cost(q * price) > dec(op["cost_ceiling"]):
            raise ValueError("cost_ceiling")
        cash_reserved = ZERO
        if op["side"] == "BUY":
            cash_reserved = money(q * dec(op["limit_price"]) + dec(op["cost_ceiling"]))
            if cash_reserved > dec(view(state)["cash"]["available"]):
                raise ValueError("insufficient_settled_cash")
        else:
            p = state["positions"].get(symbol, position())
            if q > dec(p["quantity"]) - dec(p["reserved"]) - dec(p["unsettled"]):
                raise ValueError("insufficient_available_units")
            p["reserved"] = str(dec(p["reserved"]) + q)
        state["pending"][oid] = {**op, "cash_reserved": str(cash_reserved)}
        state["used_orders"].append(oid)
    view(state)


def fill(state, operations, trade_session):
    if (
        trade_session != state["marks"]["session"]
        or trade_session != state["as_of_session"]
    ):
        raise ValueError("trade_session_mismatch")
    due = settlement_day(trade_session)
    for op in sorted(operations, key=lambda o: (o["priority"], o["operation_id"])):
        oid, symbol, side = op["operation_id"], op["ticker"], op["side"]
        if oid not in state["pending"] or oid in state["executions"]:
            raise ValueError("order_not_reserved_or_duplicate")
        q = units(op["quantity"])
        price = amount(state["marks"]["prices"][symbol], positive=True)
        gross, fees = money(q * price), cost(q * price)
        p = state["positions"].setdefault(symbol, position())
        if side == "BUY":
            if gross + fees > dec(state["pending"][oid]["cash_reserved"]):
                raise ValueError("reservation_insufficient")
            state["settled_cash"] = str(dec(state["settled_cash"]) - gross - fees)
            p["quantity"] = str(dec(p["quantity"]) + q)
            p["unsettled"] = str(dec(p["unsettled"]) + q)
            p["basis"] = str(dec(p["basis"]) + gross + fees)
            realized = ZERO
        else:
            previous = dec(p["quantity"])
            basis = (
                dec(p["basis"])
                if q == previous
                else money(dec(p["basis"]) * q / previous)
            )
            p["quantity"] = str(previous - q)
            p["reserved"] = str(dec(p["reserved"]) - q)
            p["basis"] = str(dec(p["basis"]) - basis)
            realized = gross - fees - basis
            state["realized_pnl"] = str(dec(state["realized_pnl"]) + realized)
            state["receivables"][oid] = {
                "amount": str(gross - fees),
                "trade_session": trade_session,
                "due_session": due,
                "rule": POLICY["settlement_rule"],
                "source_sha256": state["marks"]["sha256"],
            }
        state["costs"] = str(dec(state["costs"]) + fees)
        state["executions"][oid] = {
            "operation": op,
            "quantity": str(q),
            "raw_price": str(price),
            "cost": str(fees),
            "realized_pnl": str(realized),
            "trade_session": trade_session,
            "due_session": due,
            "marks_sha256": state["marks"]["sha256"],
        }
        del state["pending"][oid]
        safety(state)


def apply(state, kind, payload):
    """Pure reducer. Replays all financial guards; no filesystem/network effects."""
    state = copy.deepcopy(state)
    if kind == "INITIALIZED":
        if state is not None or payload["policy"] != POLICY:
            raise ValueError("identity_or_policy_changed")
        checked_marks(payload["marks"])
        capital = amount(payload["capital"], positive=True)
        state = {
            "schema_version": 1,
            "identity": IDENTITY,
            "mode": "synthetic",
            "portfolio_id": key(payload["portfolio_id"]),
            "policy": POLICY,
            "initial_capital": str(capital),
            "settled_cash": str(capital),
            "positions": {},
            "costs": "0.00",
            "realized_pnl": "0.00",
            "income_net": "0.00",
            "peak_equity": str(capital),
            "marks": payload["marks"],
            "pending": {},
            "executions": {},
            "receivables": {},
            "settlements": {},
            "used_orders": [],
            "blocked": {},
            "corporate_events": {},
            "proposals": {},
            "approvals": {},
        }
    elif state is None:
        raise ValueError("portfolio_not_initialized")
    elif kind == "MARKED":
        if state["pending"]:
            raise ValueError("cancel_reservations_before_mark")
        checked_marks(payload["marks"], state)
        state["marks"] = payload["marks"]
    elif kind == "RESERVED":
        if payload["state_sha256"] != financial_hash(state):
            raise ValueError("stale_approval_state")
        approval = check_seal(payload["approval"])
        if (
            approval["identity"] != IDENTITY
            or approval["portfolio_id"] != state["portfolio_id"]
            or approval["mode"] != "synthetic"
            or approval["action"] != "APPROVE"
            or approval["state_sha256"] != financial_hash(state)
            or approval["operations_sha256"] != digest(payload["operations"])
            or approval["limits_sha256"] != digest(POLICY)
            or approval["marks_sha256"] != state["marks"]["sha256"]
            or approval["max_quantities"]
            != {op["operation_id"]: op["quantity"] for op in payload["operations"]}
        ):
            raise ValueError("invalid_synthetic_approval")
        if approval["proposal_sha256"] != "fixture":
            from multiasset_manager import validate

            p = next(
                (
                    p
                    for p in state["proposals"].values()
                    if p["sha256"] == approval["proposal_sha256"]
                ),
                None,
            )
            if (
                p is None
                or approval["record_id"] not in state["approvals"]
                or state["approvals"][approval["record_id"]] != approval
            ):
                raise ValueError("registered_proposal_approval_required")
            validation = validate(
                state, p, state["proposal_contexts"][p["record_id"]], payload["at"]
            )
            if (
                not validation["valid"]
                or validation["ready_operations"] != payload["operations"]
            ):
                raise ValueError("global_validation_failed_before_reservation")
        if (
            not instant(approval["created_at"])
            <= instant(payload["at"])
            < instant(approval["expires_at"])
        ):
            raise ValueError("approval_expired")
        reserve(state, payload["operations"])
        preview = copy.deepcopy(state)
        fill(preview, payload["operations"], state["marks"]["session"])
        state["pending_approval"] = approval
    elif kind == "FILLED":
        if payload["reserved_state_sha256"] != financial_hash(state):
            raise ValueError("reserved_state_changed")
        approval = state["pending_approval"]
        if (
            not instant(approval["created_at"])
            <= instant(payload["at"])
            < instant(approval["expires_at"])
        ):
            raise ValueError("approval_expired")
        ops = [
            {k: v for k, v in op.items() if k != "cash_reserved"}
            for op in state["pending"].values()
        ]
        fill(state, ops, payload["session"])
        del state["pending_approval"]
    elif kind == "CANCELLED":
        for op in state["pending"].values():
            if op["side"] == "SELL":
                p = state["positions"][op["ticker"]]
                p["reserved"] = str(dec(p["reserved"]) - dec(op["quantity"]))
        state["pending"] = {}
        state.pop("pending_approval", None)
    elif kind == "SETTLED":
        session(payload["session"])
        if (
            payload["session"] < state["marks"]["session"]
            or not payload["confirmation_source"]
        ):
            raise ValueError("invalid_settlement_confirmation")
        oid = payload["operation_id"]
        if oid in state["settlements"] or oid not in state["executions"]:
            raise ValueError("settlement_duplicate_or_unknown")
        execution = state["executions"][oid]
        if payload["session"] < execution["due_session"]:
            raise ValueError("settlement_not_due")
        if execution["operation"]["side"] == "SELL":
            state["settled_cash"] = str(
                dec(state["settled_cash"]) + dec(state["receivables"].pop(oid)["amount"])
            )
        else:
            p = state["positions"][execution["operation"]["ticker"]]
            p["unsettled"] = str(dec(p["unsettled"]) - dec(execution["quantity"]))
        state["settlements"][oid] = payload
    elif kind == "CORPORATE":
        corporate(state, payload)
    elif kind == "CORPORATE_PAID":
        eid = payload["event_id"]
        receivable = state["receivables"][eid]
        session(payload["session"])
        if (
            payload["session"] < max(receivable["due_session"], state["marks"]["session"])
            or not payload["confirmation_source"]
        ):
            raise ValueError("corporate_payment_not_due")
        state["settled_cash"] = str(
            dec(state["settled_cash"]) + dec(receivable["amount"])
        )
        del state["receivables"][eid]
        state["settlements"][eid] = payload
    elif kind in ("PROPOSED", "APPROVED"):
        record = check_seal(payload["record"])
        name = "proposals" if kind == "PROPOSED" else "approvals"
        rid = key(record["record_id"])
        if (
            rid in state[name]
            or record["identity"] != IDENTITY
            or record["portfolio_id"] != state["portfolio_id"]
            or record["mode"] != "synthetic"
        ):
            raise ValueError("record_identity_or_duplicate")
        state[name][rid] = record
        if kind == "PROPOSED":
            state.setdefault("proposal_contexts", {})[rid] = payload["context"]
    else:
        raise ValueError("unknown_event")
    state.setdefault("as_of_session", state["marks"]["session"])
    if kind == "MARKED":
        if state["marks"]["session"] < state["as_of_session"]:
            raise ValueError("clock_backwards")
        state["as_of_session"] = state["marks"]["session"]
    elif kind in ("SETTLED", "CORPORATE_PAID"):
        if payload["session"] < state["as_of_session"]:
            raise ValueError("clock_backwards")
        state["as_of_session"] = payload["session"]
    report = view(state)
    state["peak_equity"] = str(max(dec(state["peak_equity"]), dec(report["equity"])))
    return state


def corporate(state, payload):
    eid, symbol = key(payload["event_id"]), ticker(payload["ticker"])
    if (
        eid in state["corporate_events"]
        or not payload["source"]
        or not payload["source_sha256"]
    ):
        raise ValueError("corporate_duplicate_or_missing_source")
    session(payload["effective_session"])
    if (
        payload["effective_session"] != state["marks"]["session"]
        or payload["effective_session"] != state["as_of_session"]
        or state["pending"]
    ):
        raise ValueError("corporate_session_or_pending_orders")
    p = state["positions"].get(symbol, position())
    q = dec(p["quantity"])
    error = None
    if (
        payload["eligible_quantity"] != str(q)
        or payload.get("reconciled") is not True
        or dec(p["unsettled"]) != 0
    ):
        error = "ENTITLEMENT_UNRECONCILED"
    elif payload["type"] in ("DIVIDEND", "JCP"):
        gross, tax, net = (
            amount(payload[k]) for k in ("gross_amount", "withholding", "net_amount")
        )
        if gross - tax != net or payload["due_session"] < payload["effective_session"]:
            error = "CASH_EVENT_UNRECONCILED"
        else:
            session(payload["due_session"])
            state["receivables"][eid] = {
                "amount": str(net),
                "due_session": payload["due_session"],
                "source_sha256": payload["source_sha256"],
                "type": payload["type"],
            }
            state["income_net"] = str(dec(state["income_net"]) + net)
    elif payload["type"] in ("SPLIT", "REVERSE_SPLIT", "BONUS"):
        factor = dec(payload["factor"])
        new_q = q * factor
        if (
            factor <= 0
            or new_q != new_q.to_integral_value()
            or amount(payload["raw_mark_after"], positive=True) * new_q
            != q * dec(state["marks"]["prices"][symbol])
        ):
            error = "FACTOR_FRACTION_OR_MARK_UNRECONCILED"
        else:
            p["quantity"] = str(new_q)
            state["marks"] = sealed(
                {
                    **{k: v for k, v in state["marks"].items() if k != "sha256"},
                    "prices": {
                        **state["marks"]["prices"],
                        symbol: payload["raw_mark_after"],
                    },
                    "source": payload["source"],
                    "corporate_source_sha256": payload["source_sha256"],
                }
            )
    else:
        error = "UNSUPPORTED_CORPORATE_EVENT"
    state["corporate_events"][eid] = {**payload, "status": error or "RECONCILED"}
    if error:
        state["blocked"][symbol] = {
            "event_id": eid,
            "reason": error,
            "payload_sha256": digest(payload),
        }


class Store:
    def __init__(self, root):
        self.root = folder(root)

    def load(self):
        # ponytail: replay all events for every read, O(n) per command; a verified
        # checkpoint plus immutable segment seals is the upgrade for long ledgers.
        state, previous, events, states = None, None, [], []
        for index, path in enumerate(sorted((self.root / "events").glob("*.json")), 1):
            event = check_seal(read(path))
            if (
                event["sequence"] != index
                or path.name != f"{index:08d}.json"
                or event["previous_sha256"] != previous
                or event["identity"] != IDENTITY
                or event["portfolio_id"] != self.root.name
                or event["schema_version"] != 1
                or any(e["record_id"] == event["record_id"] for e in events)
            ):
                raise ValueError("event_chain_broken")
            if events and instant(event["created_at"]) < instant(
                events[-1]["created_at"]
            ):
                raise ValueError("event_clock_backwards")
            state = apply(state, event["kind"], event["payload"])
            if (
                index == 1
                and event["payload"].get("implementation_sha256") != implementation()
            ):
                raise ValueError("portfolio_implementation_changed")
            if state["portfolio_id"] != self.root.name:
                raise ValueError("portfolio_identity_changed")
            previous = event["sha256"]
            states.append(digest(state))
            events.append(event)
        checkpoint = self.root / "snapshot.json"
        if checkpoint.exists():
            snap = check_seal(read(checkpoint))
            seq = snap["sequence"]
            if (
                not 0 < seq <= len(events)
                or snap["event_sha256"] != events[seq - 1]["sha256"]
                or digest(snap["state"]) != states[seq - 1]
            ):
                raise ValueError("snapshot_integrity_failed")
        for event in events:
            if event["kind"] in ("PROPOSED", "APPROVED"):
                record = event["payload"]["record"]
                path = (
                    self.root
                    / ("proposals" if event["kind"] == "PROPOSED" else "approvals")
                    / (record["record_id"] + ".json")
                )
                if path.exists() and read(path) != record:
                    raise ValueError("projection_integrity_failed")
                validation = self.root / "validations" / (event["record_id"] + ".json")
                if (
                    "validation" in event["payload"]
                    and validation.exists()
                    and read(validation) != event["payload"]["validation"]
                ):
                    raise ValueError("validation_projection_integrity_failed")
        return state, events

    def checkpoint(self, state, events):
        if not events:
            return
        for event in events:
            if event["kind"] in ("PROPOSED", "APPROVED"):
                name = "proposals" if event["kind"] == "PROPOSED" else "approvals"
                record = event["payload"]["record"]
                write(
                    self.root / name / (record["record_id"] + ".json"),
                    record,
                    immutable=True,
                )
                if "validation" in event["payload"]:
                    write(
                        self.root / "validations" / (event["record_id"] + ".json"),
                        event["payload"]["validation"],
                        immutable=True,
                    )
        write(
            self.root / "snapshot.json",
            sealed(
                {
                    "schema_version": 1,
                    "identity": IDENTITY,
                    "sequence": len(events),
                    "event_sha256": events[-1]["sha256"],
                    "state": state,
                }
            ),
        )

    def append(self, kind, payload, command_id, *, crash=None):
        key(command_id)
        payload = pack(payload)
        if kind == "INITIALIZED":
            if payload["portfolio_id"] != self.root.name:
                raise ValueError("portfolio_identity_changed")
            payload = {**payload, "implementation_sha256": implementation()}
        # ponytail: a local basket lock serializes writers. Multi-host requires a transaction store.
        with _exclusive_state_lock(self.root / "operation"):
            state, events = self.load()
            prior = next((e for e in events if e["record_id"] == command_id), None)
            if prior:
                if prior["kind"] != kind or prior["payload"] != payload:
                    raise ValueError("idempotency_conflict")
                self.checkpoint(state, events)
                return state
            next_state = apply(state, kind, payload)
            event = sealed(
                {
                    "schema_version": 1,
                    "identity": IDENTITY,
                    "portfolio_id": self.root.name,
                    "sequence": len(events) + 1,
                    "record_id": command_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "previous_sha256": events[-1]["sha256"] if events else None,
                    "kind": kind,
                    "payload": payload,
                }
            )
            if crash == "before_event":
                raise RuntimeError("simulated_crash_before_event")
            write(
                self.root / "events" / f"{event['sequence']:08d}.json",
                event,
                immutable=True,
            )
            if crash == "after_event":
                raise RuntimeError("simulated_crash_after_event")
            self.checkpoint(next_state, [*events, event])
            return next_state

    def recover(self):
        with _exclusive_state_lock(self.root / "operation"):
            state, events = self.load()
            self.checkpoint(state, events)
            return state

    def verify(self):
        try:
            state, events = self.load()
            return {
                "ok": state is not None,
                "events": len(events),
                "head_sha256": events[-1]["sha256"] if events else None,
                "state_sha256": financial_hash(state) if state else None,
                "errors": [],
            }
        except (ValueError, KeyError, OSError, TypeError, ArithmeticError) as exc:
            return {"ok": False, "errors": [str(exc)]}


def demo_approval(
    state, operations, *, proposal_sha256, risk_sha256, at, expires_at, action="APPROVE"
):
    return sealed(
        {
            "schema_version": 1,
            "identity": IDENTITY,
            "mode": "synthetic",
            "portfolio_id": state["portfolio_id"],
            "record_id": "approval-"
            + digest(
                {
                    "proposal": proposal_sha256,
                    "state": financial_hash(state),
                    "action": action,
                }
            )[:24],
            "action": action,
            "proposal_sha256": proposal_sha256,
            "risk_sha256": risk_sha256,
            "state_sha256": financial_hash(state),
            "operations_sha256": digest(operations),
            "marks_sha256": state["marks"]["sha256"],
            "limits_sha256": digest(POLICY),
            "created_at": at,
            "expires_at": expires_at,
            "max_quantities": {op["operation_id"]: op["quantity"] for op in operations},
        }
    )


def marks(day, prices):
    return sealed(
        {
            "schema_version": 1,
            "mode": "synthetic",
            "basis": "RAW",
            "session": day,
            "observed_at": day + "T18:00:00-03:00",
            "source": "SYNTHETIC_OFFLINE_NOT_MARKET_DATA",
            "prices": prices,
        }
    )
