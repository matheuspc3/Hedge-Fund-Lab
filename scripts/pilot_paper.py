"""PAPER-02 bridge V1. Synthetic only; SQLite and accounting remain V765/V5.

Economic instants and fixture release times use an explicitly simulated clock.
DATA-01 import receipts and SQLite recorded_at retain their actual clocks.
"""

import copy
from datetime import date
from types import FunctionType, SimpleNamespace

import paper_ledger as ledger
import pilot_market_data as data

b = ledger.b
IDENTITY = "HFL-PILOT-PAPER-SYNTHETIC-V1"
AGENTS = "SCRIPTED_AGENTS_TEST_V1"
REFERENCE = "BUY_HOLD_EQUAL_WEIGHT_INITIAL_TEST_V1"


def bind(function, **dependencies):
    """Reuse sealed bytecode with a private namespace, never monkeypatch globals.

    ponytail: these functions have module dependencies rather than injection
    parameters. Keep this small bridge pinned/tested; a future unsealed engine
    can expose explicit parameters. No source edits, exec or global POLICY writes.
    """
    result = FunctionType(
        function.__code__,
        {**function.__globals__, **dependencies},
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def policy(strategy):
    if strategy not in (AGENTS, REFERENCE):
        raise ValueError("unknown_test_strategy")
    return {
        **b.POLICY,
        "version": strategy,
        "settlement_rule": "SYNTHETIC_EXPLICIT_CALENDAR_D+2",
        "max_exposure": "1.00" if strategy == REFERENCE else "0.85",
        "max_concentration": "1.00" if strategy == REFERENCE else "0.40",
        "producer": "SCRIPTED_TEST_NO_AGENT_OPINIONS",
    }


def safety(financial):
    report = b.view(financial)
    limits = financial["policy"]
    if b.dec(report["exposure"]) > b.dec(limits["max_exposure"]) or any(
        b.dec(p["market_value"])
        > b.dec(limits["max_concentration"]) * b.dec(report["equity"])
        for p in report["positions"].values()
    ):
        raise ValueError("concentration_or_exposure_limit")
    return report


def engine(state):
    calendar, limits = state["calendar"], state["portfolio"]["financial_policy"]

    def session(day):
        return date.fromisoformat(data.calendar_session(calendar, day))

    checked = bind(b.checked_marks, session=session)
    cost = bind(b.cost, POLICY=limits)
    reserve = bind(b.reserve, POLICY=limits, cost=cost)
    fill = bind(
        b.fill,
        POLICY=limits,
        cost=cost,
        safety=safety,
        settlement_day=lambda day: data.settlement_session(calendar, day),
    )
    apply = bind(b.apply, POLICY=limits, checked_marks=checked, session=session)
    return SimpleNamespace(apply=apply, reserve=reserve, fill=fill, cost=cost)


def quote_prices(state, payload, phase, processed_at):
    bundle = payload["bundle"]
    content = data.verify_bundle(bundle, at=processed_at)
    if (
        content["source"]["nature"] != "SYNTHETIC_TEST"
        or content["calendar"] != state["calendar"]
        or set(content["selection"]["tickers"]) != set(data.UNIVERSE)
        or content["selection"]["sessions"] != [payload["session"]]
    ):
        raise ValueError("synthetic_complete_daily_bundle_required")
    # A fixture release is a simulation gate, not evidence of B3 publication.
    if data.instant(payload["fixture_released_at"]) > data.instant(processed_at):
        raise ValueError("fixture_not_released")
    prices = data.prices(bundle, payload["session"], phase, at=processed_at)
    if set(prices) != set(data.UNIVERSE):
        raise ValueError("price_missing")
    return prices


def agent_risk(state, financial, fixture, at):
    b.check_seal(fixture)
    if fixture["classification"] != "SYNTHETIC_TEST" or data.instant(
        fixture["available_at"]
    ) > data.instant(at):
        raise ValueError("risk_fixture_unavailable")
    calendar = state["calendar"]
    proxy = SimpleNamespace(**vars(b))
    proxy.POLICY = financial["policy"]
    proxy.session = lambda day: date.fromisoformat(data.calendar_session(calendar, day))
    proxy.B3Calendar = lambda: SimpleNamespace(
        sessions_between=lambda start, end: [
            date.fromisoformat(d)
            for d in calendar["sessions"]
            if start <= date.fromisoformat(d) <= end
        ]
    )
    b.check_seal(fixture["marks"])
    if data.instant(at).date().isoformat() != fixture["marks"]["session"]:
        raise ValueError("risk_fixture_decision_session_mismatch")
    context = {"marks": fixture["marks"], "histories": fixture["histories"]}
    report = bind(ledger.manager.risk, b=proxy)(financial, context)
    if report["errors"]:
        raise ValueError("scripted_risk_blocked:" + ",".join(report["errors"]))
    return report


def basket_limits(financial, operations, prices, fees):
    equity = b.dec(b.view(financial)["equity"])
    turnover = sum(
        (b.units(op["quantity"]) * b.dec(prices[op["ticker"]]) for op in operations),
        b.ZERO,
    )
    if turnover > equity * b.dec(
        financial["policy"]["max_turnover"]
    ) or fees > equity * b.dec(financial["policy"]["max_cost_weight"]):
        raise ValueError("turnover_or_cost_limit")


def validate(state, proposal):
    b.check_seal(proposal)
    f, day = state["financial"], state["financial"]["marks"]["session"]
    target = data.next_session(state["calendar"], day)
    times = [
        proposal[k]
        for k in ("decision_at", "target_open_at", "expires_at", "processing_deadline")
    ]
    if (
        proposal["identity"] != IDENTITY
        or proposal["portfolio_id"] != state["portfolio"]["portfolio_id"]
        or proposal["producer"] != "SCRIPTED_TEST_NO_AGENT_OPINIONS"
        or proposal["state_sha256"] != b.financial_hash(f)
        or proposal["close_sha256"] != state["quote"]["bundle"]["sha256"]
        or proposal["policy_sha256"] != b.digest(f["policy"])
        or proposal["data_session"] != day
        or proposal["target_session"] != target
        or data.instant(times[1]).date().isoformat() != target
        or not all(data.instant(a) < data.instant(c) for a, c in zip(times, times[1:]))
        or state["valuation_unavailable"]
        or state["reconciliation_failed"]
        or not state["history"]
        or state["history"][-1]["session"] != day
        or state["history"][-1]["view"]["state_sha256"] != b.financial_hash(f)
        or state["intent"]
        or target in state["blocked_sessions"]
    ):
        raise ValueError("proposal_state_or_clock_invalid")
    quote_prices(state, state["quote"], "CLOSE", proposal["decision_at"])
    operations = proposal["operations"]
    if proposal["action"] != ("TRADE" if operations else "HOLD"):
        raise ValueError("explicit_trade_or_hold_required")
    if state["portfolio"]["strategy"] == REFERENCE:
        if operations:
            if (
                f["executions"]
                or len(operations) != 5
                or any(op["side"] != "BUY" for op in operations)
                or {op["ticker"] for op in operations} != set(data.UNIVERSE)
            ):
                raise ValueError("reference_single_five_asset_entry_required")
            if proposal["targets"] != dict.fromkeys(data.UNIVERSE, "0.20"):
                raise ValueError("reference_targets_must_be_twenty_percent")
            if operations != reference_operations(state):
                raise ValueError("reference_entry_must_match_ex_ante_equal_budgets")
    preview = copy.deepcopy(f)
    risk = None
    if operations:
        data.settlement_session(state["calendar"], target)
        adapter = engine(state)
        adapter.reserve(preview, operations)
        # Worst authorized prices, not the subsequently observed OPEN.
        limits = {
            **preview["marks"]["prices"],
            **{op["ticker"]: op["limit_price"] for op in operations},
        }
        preview["marks"] = b.marks(target, limits)
        preview["as_of_session"] = target
        adapter.fill(preview, operations, target)
        report = safety(preview)
        basket_limits(
            f,
            operations,
            limits,
            sum((b.dec(op["cost_ceiling"]) for op in operations), b.ZERO),
        )
    else:
        report = b.view(preview)
    if state["portfolio"]["strategy"] == AGENTS:
        if proposal["risk_fixture"]["marks"] != f["marks"]:
            raise ValueError("risk_fixture_close_mismatch")
        risk = agent_risk(
            state, preview, proposal["risk_fixture"], proposal["decision_at"]
        )
    return b.sealed(
        {
            "valid": True,
            "proposal_sha256": proposal["sha256"],
            "projected": report,
            "risk": risk,
        }
    )


def reconciliation(state, expected=None):
    report = b.view(state["financial"])
    f, errors = state["financial"], []
    for field, execution_field in (("costs", "cost"), ("realized_pnl", "realized_pnl")):
        if b.dec(f[field]) != sum(
            (b.dec(e[execution_field]) for e in f["executions"].values()), b.ZERO
        ):
            errors.append(field + "_execution_total_mismatch")
    for execution in f["executions"].values():
        if execution["due_session"] != data.settlement_session(
            state["calendar"], execution["trade_session"]
        ):
            errors.append("settlement_date_mismatch")
    for name, value in (expected or {}).items():
        if report.get(name) != value:
            errors.append("expected_state_mismatch:" + name)
    if state["valuation_unavailable"] or any(
        day <= state["last_economic_at"][:10] for day in state["blocked_sessions"]
    ):
        errors.append("valuation_incomplete_or_corporate_blocked")
    return b.sealed(
        {
            "status": "RECONCILIATION_FAILED" if errors else "RECONCILED",
            "errors": errors,
            "view": report,
            "financial_sha256": b.financial_hash(f),
        }
    )


def reduce(state, event):
    kind, p, at = event["kind"], event["payload"], event["effective_at"]
    day = b.instant(at).date().isoformat()
    if (
        event["authority"] != "SYNTHETIC_TEST_OPERATOR"
        or event["source"] != ("ISOLATED_SYNTHETIC_QUALIFICATION")
        or event["session"] != day
    ):
        raise ValueError("synthetic_event_authority_required")
    state = copy.deepcopy(state)
    if kind == "PORTFOLIO_CREATED":
        if state is not None or p["strategy"] not in (AGENTS, REFERENCE):
            raise ValueError("portfolio_already_created_or_strategy_unknown")
        if p["calendar"]["nature"] != "SYNTHETIC_TEST":
            raise ValueError("synthetic_calendar_required")
        data.calendar_session(p["calendar"], day)
        if (
            p["parameters"] != test_parameters()
            or p["engine_fingerprints"] != fingerprints()
        ):
            raise ValueError("test_contract_or_implementation_changed")
        state = {
            "portfolio": {
                "portfolio_id": event["portfolio_id"],
                "strategy": p["strategy"],
                "classification": "SYNTHETIC_TEST",
                "scientific_identity": None,
                "financial_policy": policy(p["strategy"]),
            },
            "parameters": p["parameters"],
            "calendar": p["calendar"],
            "financial": None,
            "quote": None,
            "history": [],
            "proposals": {},
            "validations": {},
            "authorizations": {},
            "intent": None,
            "blocked_sessions": {},
            "valuation_unavailable": True,
            "reconciliation_failed": False,
            "reconciliations": [],
            "trades": [],
            "settlement_confirmations": [],
        }
        prices = quote_prices(state, p["quote"], "CLOSE", p["processed_at"])
        if p["quote"]["session"] != day:
            raise ValueError("initial_session_mismatch")
        state["financial"] = engine(state).apply(
            None,
            "INITIALIZED",
            {
                "portfolio_id": event["portfolio_id"],
                "policy": policy(p["strategy"]),
                "capital": p["parameters"]["capital"],
                "marks": b.marks(day, prices),
            },
        )
        state["quote"], state["valuation_unavailable"] = p["quote"], False
    elif state is None:
        raise ValueError("portfolio_not_initialized")
    else:
        if data.instant(at) < data.instant(state["last_economic_at"]):
            raise ValueError("economic_clock_backwards")
        data.calendar_session(state["calendar"], day)
        f, adapter = state["financial"], engine(state)
        if any(d <= day for d in state["blocked_sessions"]) and kind not in (
            "CORPORATE_EVENT_UNSUPPORTED",
            "PAPER_ORDER_CANCELLED",
            "PORTFOLIO_RECONCILED",
        ):
            raise ValueError("unsupported_corporate_event_blocks_session")
        if kind == "CORPORATE_EVENT_UNSUPPORTED":
            if not p["reason"] or p["ticker"] not in data.UNIVERSE:
                raise ValueError("corporate_block_reason_required")
            state["blocked_sessions"][day] = p
            state["valuation_unavailable"] = True
        elif kind == "PORTFOLIO_VALUED":
            if (
                state["intent"]
                or day in state["blocked_sessions"]
                or any(h["session"] == day for h in state["history"])
            ):
                raise ValueError("intent_or_corporate_block_or_session_finalized")
            if p.get("quote") is None:
                state["valuation_unavailable"] = True
            else:
                if p["quote"]["session"] != day:
                    raise ValueError("close_session_mismatch")
                prices = quote_prices(state, p["quote"], "CLOSE", p["processed_at"])
                state["financial"] = adapter.apply(
                    f, "MARKED", {"marks": b.marks(day, prices)}
                )
                state["quote"], state["valuation_unavailable"] = p["quote"], False
        elif kind == "PORTFOLIO_RECONCILED":
            report = reconciliation(state, p.get("expected"))
            state["reconciliations"].append(report)
            state["reconciliation_failed"] = bool(report["errors"])
            if not report["errors"]:
                if report["view"]["session"] != day or any(
                    h["session"] == day for h in state["history"]
                ):
                    raise ValueError("session_not_marked_or_already_published")
                state["history"].append(
                    {
                        "session": day,
                        "view": report["view"],
                        "quote_sha256": state["quote"]["bundle"]["sha256"],
                    }
                )
        elif kind == "PROPOSAL_LINKED":
            proposal = b.check_seal(p["record"])
            rid = b.key(proposal["record_id"])
            if rid in state["proposals"] or proposal["decision_at"] != at:
                raise ValueError("proposal_identity_or_time_invalid")
            state["proposals"][rid] = proposal
        elif kind == "VALIDATION_RECORDED":
            proposal = state["proposals"][p["proposal_id"]]
            if data.instant(at) < data.instant(proposal["decision_at"]):
                raise ValueError("validation_before_decision")
            state["validations"][p["proposal_id"]] = validate(state, proposal)
        elif kind == "AUTHORIZATION_RECORDED":
            proposal = state["proposals"][p["proposal_id"]]
            validation = state["validations"].get(p["proposal_id"])
            if (
                not validation
                or validation != validate(state, proposal)
                or p["proposal_id"] in state["authorizations"]
                or p["operator"] != "SYNTHETIC_TEST_OPERATOR"
                or not data.instant(proposal["decision_at"])
                <= data.instant(at)
                < data.instant(proposal["target_open_at"])
                or p["expires_at"] != proposal["expires_at"]
            ):
                raise ValueError("authorization_missing_late_or_incompatible")
            state["authorizations"][p["proposal_id"]] = {
                **p,
                "authorized_at": at,
                "event_id": event["event_id"],
                "proposal_sha256": proposal["sha256"],
                "validation_sha256": validation["sha256"],
            }
        elif kind == "PAPER_ORDER_CREATED":
            rid = p["proposal_id"]
            proposal = state["proposals"][rid]
            authorization = state["authorizations"].get(rid)
            if (
                not authorization
                or event["authorization_ref"] != authorization["event_id"]
                or state["intent"]
                or not proposal["operations"]
                or not data.instant(authorization["authorized_at"])
                <= data.instant(at)
                < data.instant(proposal["target_open_at"])
            ):
                raise ValueError("ex_ante_authorization_and_intent_required")
            validate(state, proposal)
            adapter.reserve(f, proposal["operations"])
            state["intent"] = {
                "proposal_id": rid,
                "reserved_state_sha256": b.financial_hash(f),
                "created_at": at,
                "authorization_id": authorization["event_id"],
            }
        elif kind == "PAPER_ORDER_EXECUTED":
            intent = state["intent"]
            if not intent:
                raise ValueError("authorized_intent_required")
            proposal = state["proposals"][intent["proposal_id"]]
            auth = state["authorizations"][intent["proposal_id"]]
            if (
                event["authorization_ref"] != intent["authorization_id"]
                or b.financial_hash(f) != intent["reserved_state_sha256"]
                or day != proposal["target_session"]
                or at != proposal["target_open_at"]
                or day in state["blocked_sessions"]
                or not data.instant(auth["authorized_at"])
                <= data.instant(intent["created_at"])
                < data.instant(at)
                < data.instant(auth["expires_at"])
                or not data.instant(at)
                <= data.instant(p["processed_at"])
                <= data.instant(proposal["processing_deadline"])
            ):
                raise ValueError("approved_state_or_execution_clock_changed")
            if p.get("quote") is None:
                raise ValueError("OPEN_unavailable_intent_remains_pending")
            if p["quote"]["session"] != day:
                raise ValueError("open_session_mismatch")
            prices = quote_prices(state, p["quote"], "OPEN", p["processed_at"])
            for op in proposal["operations"]:
                price = b.amount(prices[op["ticker"]], positive=True)
                if (
                    (op["side"] == "BUY" and price > b.dec(op["limit_price"]))
                    or (op["side"] == "SELL" and price < b.dec(op["limit_price"]))
                    or adapter.cost(b.units(op["quantity"]) * price)
                    > b.dec(op["cost_ceiling"])
                ):
                    raise ValueError("OPEN_outside_authorized_limit_or_fee")
            basket_limits(
                f,
                proposal["operations"],
                prices,
                sum(
                    (
                        adapter.cost(
                            b.units(op["quantity"]) * b.dec(prices[op["ticker"]])
                        )
                        for op in proposal["operations"]
                    ),
                    b.ZERO,
                ),
            )
            f["marks"], f["as_of_session"] = b.marks(day, prices), day
            adapter.fill(f, proposal["operations"], day)
            if state["portfolio"]["strategy"] == AGENTS:
                agent_risk(state, f, proposal["risk_fixture"], proposal["decision_at"])
            for op in proposal["operations"]:
                state["trades"].append(
                    {
                        **f["executions"][op["operation_id"]],
                        "proposal_id": intent["proposal_id"],
                        "authorization_id": intent["authorization_id"],
                        "decision_session": proposal["data_session"],
                        "decision_at": proposal["decision_at"],
                        "authorized_at": auth["authorized_at"],
                        "economic_phase": "OPEN",
                        "economic_at": None,
                        "economic_precision": "SESSION_OPEN",
                        "test_target_open_at": at,
                        "processed_at": p["processed_at"],
                        "available_at": p["quote"]["bundle"]["import"]["available_at"],
                        "fixture_released_at": p["quote"]["fixture_released_at"],
                        "bundle_sha256": p["quote"]["bundle"]["sha256"],
                    }
                )
            state["intent"] = None
        elif kind == "PAPER_ORDER_CANCELLED":
            if not state["intent"] or not p["reason"]:
                raise ValueError("pending_intent_and_cancellation_reason_required")
            state["financial"] = adapter.apply(f, "CANCELLED", {})
            state["intent"] = None
        elif kind == "SETTLEMENT_RECORDED":
            if p["confirmation_source"] != "SYNTHETIC_CALENDAR_CONFIRMATION":
                raise ValueError("synthetic_settlement_confirmation_required")
            data.calendar_session(state["calendar"], p["session"])
            if p["session"] != day:
                raise ValueError("settlement_session_mismatch")
            state["financial"] = adapter.apply(f, "SETTLED", p)
            state["settlement_confirmations"].append(p)
        else:
            raise ValueError("unknown_pilot_event")
    if "processed_at" in p and data.instant(p["processed_at"]) < data.instant(at):
        raise ValueError("processing_before_economic_phase")
    state["last_economic_at"] = at
    report = b.view(state["financial"])
    state["financial"]["peak_equity"] = str(
        max(b.dec(state["financial"]["peak_equity"]), b.dec(report["equity"]))
    )
    return state


# Same bytecode/schema/transactions/guards as V765. Only reducer and contract
# identity are locally bound. Old readers reject new events and vice versa.
replay = bind(ledger.replay, reduce=reduce, IDENTITY=IDENTITY)


class Store(ledger.Store):
    append = bind(ledger.Store.append, reduce=reduce, IDENTITY=IDENTITY)
    _load = staticmethod(bind(ledger.Store._load, replay=replay))
    verify = bind(ledger.Store.verify, reconciliation=reconciliation)
    export = bind(ledger.Store.export, IDENTITY=IDENTITY)


def fingerprints():
    return {
        **ledger.fingerprints(),
        **{
            name: b.sha_file(ledger.ROOT / name)
            for name in (
                "scripts/paper_ledger.py",
                "scripts/pilot_market_data.py",
                "scripts/pilot_paper.py",
            )
        },
    }


def test_parameters():
    return {
        "classification": "SYNTHETIC_TEST",
        "clock": "SIMULATED_SCENARIO_NOT_B3_HOURS",
        "capital": "100000.00",
        "fee_rate": "0.001",
        "buy_buffer": "0.02",
        "sell_buffer": "0.02",
        "open": "10:00:00-03:00",
        "close": "18:00:00-03:00",
        "release": "18:05:00-03:00",
        "decision": "18:20:00-03:00",
        "authorization": "18:30:00-03:00",
        "intent": "18:35:00-03:00",
        "economic_expiry": "10:05:00-03:00",
        "processing_deadline": "23:00:00-03:00",
        "lot": "INTEGER_UNITS_TEST_NO_LIQUIDITY_CLAIM",
        "slippage": "0",
        "corporate_events": "UNSUPPORTED_BLOCK_SESSION",
        "official_activation": False,
    }


def proposal(state, operations, record_id, *, risk_fixture=None):
    day = state["financial"]["marks"]["session"]
    target = data.next_session(state["calendar"], day)
    params = state["parameters"]
    return b.sealed(
        {
            "identity": IDENTITY,
            "record_id": b.key(record_id),
            "portfolio_id": state["portfolio"]["portfolio_id"],
            "producer": "SCRIPTED_TEST_NO_AGENT_OPINIONS",
            "action": "TRADE" if operations else "HOLD",
            "operations": operations,
            "targets": dict.fromkeys(data.UNIVERSE, "0.20")
            if state["portfolio"]["strategy"] == REFERENCE
            else None,
            "state_sha256": b.financial_hash(state["financial"]),
            "close_sha256": state["quote"]["bundle"]["sha256"],
            "policy_sha256": b.digest(state["financial"]["policy"]),
            "data_session": day,
            "target_session": target,
            "decision_at": day + "T" + params["decision"],
            "target_open_at": target + "T" + params["open"],
            "expires_at": target + "T" + params["economic_expiry"],
            "processing_deadline": target + "T" + params["processing_deadline"],
            "risk_fixture": risk_fixture,
        }
    )


def operation(state, oid, symbol, side, quantity):
    b.ticker(symbol)
    price = b.dec(state["financial"]["marks"]["prices"][symbol])
    buffer = b.dec(state["parameters"]["buy_buffer" if side == "BUY" else "sell_buffer"])
    limit = b.money(price * (1 + buffer if side == "BUY" else 1 - buffer))
    return {
        "operation_id": b.key(oid),
        "ticker": symbol,
        "side": side,
        "quantity": str(quantity),
        "limit_price": str(limit),
        "cost_ceiling": str(engine(state).cost(b.units(str(quantity)) * limit))
        if side == "BUY"
        else str(
            b.money(
                b.units(str(quantity))
                * price
                * b.dec(state["parameters"]["fee_rate"])
                * 2
            )
        ),
        "funding_source": "SETTLED_CASH" if side == "BUY" else None,
        "priority": 1 if side == "SELL" else 2,
        "dependencies": [],
        "reasoning": "Explicit scripted synthetic test; not an agent opinion.",
    }


def reference_operations(state):
    operations = []
    budget = b.dec(state["financial"]["initial_capital"]) / 5
    for symbol in data.UNIVERSE:
        probe = operation(state, "reference-" + symbol, symbol, "BUY", 1)
        limit = b.dec(probe["limit_price"])
        quantity = int(budget / (limit * (1 + b.dec(state["parameters"]["fee_rate"]))))
        while b.money(quantity * limit) + engine(state).cost(quantity * limit) > budget:
            quantity -= 1
        while (
            b.money((quantity + 1) * limit) + engine(state).cost((quantity + 1) * limit)
            <= budget
        ):
            quantity += 1
        if quantity <= 0:
            raise ValueError("reference_zero_quantity")
        operations.append(
            operation(state, "reference-" + symbol, symbol, "BUY", quantity)
        )
    return operations


def projection(store, portfolio_ids):
    wallets = []
    for pid in portfolio_ids:
        state, events, checkpoint = store.load(pid)
        report = reconciliation(state)
        history = state["history"]
        available = not report["errors"]
        current = report["view"] if available else None
        points = []
        for i, h in enumerate(history):
            equity = b.dec(h["view"]["equity"])
            initial = b.dec(history[0]["view"]["equity"])
            previous = b.dec(history[i - 1]["view"]["equity"]) if i else None
            points.append(
                {
                    **h,
                    "base100": str(equity / initial * 100),
                    "change_brl": str(equity - initial),
                    "change_pct": str((equity / initial - 1) * 100),
                    "day_change_brl": str(equity - previous) if previous else None,
                    "day_change_pct": str((equity / previous - 1) * 100)
                    if previous
                    else None,
                }
            )
        wallets.append(
            {
                **state["portfolio"],
                "session": state["last_economic_at"][:10],
                "status": "AVAILABLE" if available else "UNAVAILABLE",
                "errors": report["errors"],
                "summary": current,
                "last_reconciled": history[-1] if history else None,
                "initial_targets": dict.fromkeys(data.UNIVERSE, "0.20")
                if state["portfolio"]["strategy"] == REFERENCE
                else None,
                "realized_weights": {
                    t: p["weight"] for t, p in current["positions"].items()
                }
                if current
                else None,
                "data_source": state["quote"]["bundle"]["content"]["source"],
                "bundle_sha256": state["quote"]["bundle"]["sha256"],
                "history": points,
                "trades": state["trades"],
                "settlements": state["settlement_confirmations"],
                "decisions": [
                    {
                        "id": rid,
                        "action": p["action"],
                        "data_session": p["data_session"],
                        "target_session": p["target_session"],
                        "sha256": p["sha256"],
                    }
                    for rid, p in state["proposals"].items()
                ],
                "periods": {
                    "since_start": {
                        "status": "AVAILABLE",
                        "change_brl": points[-1]["change_brl"],
                        "change_pct": points[-1]["change_pct"],
                    }
                    if points
                    else {"status": "INSUFFICIENT_HISTORY"},
                    "day": {
                        "status": "AVAILABLE"
                        if len(points) >= 2
                        else "INSUFFICIENT_HISTORY",
                        "change_brl": points[-1]["day_change_brl"] if points else None,
                        "change_pct": points[-1]["day_change_pct"] if points else None,
                    },
                    "month": {"status": "INSUFFICIENT_HISTORY"},
                    "year": {"status": "INSUFFICIENT_HISTORY"},
                    "last_12_months": {"status": "INSUFFICIENT_HISTORY"},
                },
                "event_count": len(events),
                "head_sha256": checkpoint["head_sha256"],
                "accounting_identity": "E = settled_cash + receivables + sum(quantity * RAW_mark) = initial_capital + realized_pnl + income_net + unrealized_pnl",
            }
        )
    common = set.intersection(*({p["session"] for p in w["history"]} for w in wallets))
    first = min(common) if common else None
    for wallet in wallets:
        if wallet["status"] == "UNAVAILABLE":
            for period in ("day", "since_start"):
                wallet["periods"][period] = {
                    "status": "UNAVAILABLE",
                    "change_brl": None,
                    "change_pct": None,
                }
        wallet["decision_status"] = "RECORDED" if wallet["decisions"] else "NO_DECISION"
    return b.sealed(
        {
            "identity": IDENTITY,
            "classification": "SYNTHETIC_TEST",
            "official_activation": False,
            "parameters": test_parameters(),
            "wallets": wallets,
            "comparison": {
                "status": "AVAILABLE" if len(common) >= 2 else "INSUFFICIENT_HISTORY",
                "basis": "100_AT_COMMON_INITIAL_RECONCILED_SESSION",
                "series": {
                    w["portfolio_id"]: [
                        {
                            "session": p["session"],
                            "value": str(
                                b.dec(p["view"]["equity"])
                                / b.dec(
                                    next(
                                        h["view"]["equity"]
                                        for h in w["history"]
                                        if h["session"] == first
                                    )
                                )
                                * 100
                            ),
                        }
                        for p in w["history"]
                        if p["session"] in common
                    ]
                    for w in wallets
                },
            },
        }
    )
