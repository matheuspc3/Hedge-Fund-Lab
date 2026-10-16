"""Global advisory contracts, covariance risk and independent deterministic validation."""

import copy
import hashlib
import math
from datetime import timedelta
from decimal import ROUND_DOWN

import multiasset_portfolio as b
import multiasset_radar as radar
import numpy as np
import pandas as pd

PROPOSAL_FIELDS = {
    "schema_version",
    "identity",
    "portfolio_id",
    "mode",
    "record_id",
    "planner",
    "decision_session",
    "created_at",
    "not_before_session",
    "expires_at",
    "state_sha256",
    "opinion_hashes",
    "marks_sha256",
    "risk_report_sha256",
    "limits_sha256",
    "current_weights",
    "target_weights",
    "target_cash_weight",
    "operations",
    "reasoning",
    "sha256",
}


def radar_opinions(root, values, day):
    """Read existing V4 seals only. Never creates a claim, journal or analysis."""
    result = {}
    for symbol in radar.tickers(values, empty=False):
        item = radar.detail(symbol, day, root)
        if item["status"] != "COMPLETED" or len(item["votes"]) != 5:
            raise ValueError("complete_radar_opinion_required")
        path = radar.folder_for(root, symbol, day)
        data = radar.read(path / "input.json")
        if (
            item["identity"] != radar.IDENTITY
            or item["manifest_sha256"] != data["manifest_sha256"]
            or radar.digest(data["manifest"]) != data["manifest_sha256"]
            or item["mode"] != data["manifest"]["mode"]
            or item["ticker"] != symbol
            or item["session"] != day
        ):
            raise ValueError("radar_contract_mismatch")
        result[symbol] = b.sealed(
            {
                "schema_version": 1,
                "identity": radar.IDENTITY,
                "ticker": symbol,
                "session": day,
                "mode": item["mode"],
                "source_family": "RADAR_V4_" + item["mode"],
                "generated_at": item["completed_at"],
                "recommendation": item["recommendation"],
                "risk_verdict": item["risk"]["verdict"],
                "votes_count": 5,
                "result_sha256": radar.sha_file(path / "result.json"),
                "input_sha256": item["input_sha256"],
                "history_sha256": item["history_sha256"],
                "manifest_sha256": item["manifest_sha256"],
                "source": item["source"],
                "origin": "SEALED_RADAR_V4",
            }
        )
    return result


def adjusted_histories(root, opinions):
    result = {}
    for symbol, opinion in opinions.items():
        path = radar.folder_for(root, symbol, opinion["session"]) / "bars.csv"
        if radar.sha_file(path) != opinion["history_sha256"]:
            raise ValueError("history_hash_changed")
        frame = pd.read_csv(path, index_col=0)
        result[symbol] = [[day, str(value)] for day, value in frame["fechamento"].items()]
    return result


def compatible(context, day, at):
    b.checked_marks(context["marks"])
    if context["marks"]["session"] != day or b.instant(
        context["marks"]["observed_at"]
    ) > b.instant(at):
        raise ValueError("market_session_or_lookahead")
    families = set()
    for symbol, opinion in context["opinions"].items():
        b.check_seal(opinion)
        if (
            opinion["identity"] != radar.IDENTITY
            or opinion["schema_version"] != 1
            or opinion["ticker"] != symbol
            or opinion["votes_count"] != 5
            or opinion["recommendation"] not in ("COMPRA", "VENDA", "MANTER")
            or opinion["risk_verdict"] not in ("APROVADO", "VETADO")
        ):
            raise ValueError("incompatible_opinion_contract")
        if opinion["session"] != day:
            raise ValueError("opinion_session_mismatch")
        if opinion["mode"] != context["marks"]["mode"]:
            raise ValueError("synthetic_official_mix")
        if b.instant(opinion["generated_at"]) > b.instant(at):
            raise ValueError("opinion_lookahead")
        for name in (
            "result_sha256",
            "input_sha256",
            "history_sha256",
            "manifest_sha256",
        ):
            if (
                not isinstance(opinion[name], str)
                or len(opinion[name]) != 64
                or any(c not in "0123456789abcdef" for c in opinion[name])
            ):
                raise ValueError("invalid_opinion_hash")
        families.add((opinion["source_family"], opinion["manifest_sha256"]))
    if len(families) > 1:
        raise ValueError("incompatible_opinion_sources")


def risk(state, context, *, weights=None):
    """60 aligned adjusted daily returns, sample covariance (ddof=1), 252/year."""
    current = b.view(state)
    weights = weights or {t: p["weight"] for t, p in current["positions"].items()}
    selected = sorted(t for t, w in weights.items() if b.dec(w) > 0)
    day = context["marks"]["session"]
    window = b.POLICY["risk_window"]
    base = {
        "schema_version": 1,
        "identity": b.IDENTITY,
        "mode": "synthetic",
        "session": day,
        "state_sha256": b.financial_hash(state),
        "marks_sha256": context["marks"]["sha256"],
        "limits_sha256": b.digest(b.POLICY),
        "history_sha256": b.digest(context["histories"]),
        "window_returns": window,
        "annualization": b.POLICY["annualization"],
        "weights": weights,
        "cash_available": current["cash"]["available"],
        "drawdown": current["drawdown"],
        "exposure": str(sum((b.dec(w) for w in weights.values()), b.ZERO)),
        "concentration_by_company": weights,
        "costs_cumulative": current["costs"],
        "sector_exposure": None,
        "sector_status": "NOT_EVALUATED_NO_RELIABLE_METADATA",
        "volatility": None,
        "covariance_daily": None,
        "correlations": None,
        "status": "BLOCKED",
        "errors": [],
    }
    sectors = context.get("sectors")
    if sectors:
        b.check_seal(sectors)
        if (
            sectors.get("reliable") is not True
            or not sectors.get("source")
            or set(selected) - set(sectors["mapping"])
        ):
            base["errors"].append("sector_metadata_unreliable")
        else:
            exposures = {}
            for symbol in selected:
                sector = sectors["mapping"][symbol]
                exposures[sector] = str(
                    b.dec(exposures.get(sector, "0")) + b.dec(weights[symbol])
                )
            base.update(
                sector_status="EVALUATED_WITHOUT_APPROVED_SECTOR_CAP",
                sector_exposure=exposures,
            )
    if not selected:
        base.update(
            status="OK",
            volatility="0",
            covariance_daily={},
            correlations={},
            aligned_returns=0,
            note="All cash: market exposure exactly zero, not missing-data imputation.",
        )
        return b.sealed(base)
    try:
        series = {}
        expected = list(
            b.B3Calendar().sessions_between(
                b.session(day) - timedelta(days=150), b.session(day)
            )
        )[-(window + 1) :]
        expected = pd.DatetimeIndex(expected)
        for symbol in selected:
            rows = context["histories"].get(symbol, [])
            index = pd.DatetimeIndex([r[0] for r in rows])
            if (
                index.has_duplicates
                or not index.is_monotonic_increasing
                or index.tz is not None
                or index.empty
                or index[-1] > pd.Timestamp(day)
            ):
                raise ValueError("invalid_or_future_history")
            values = pd.Series([float(b.dec(r[1])) for r in rows], index=index)
            if (
                not np.isfinite(values).all()
                or (values <= 0).any()
                or not values.tail(window + 1).index.equals(expected)
            ):
                raise ValueError("insufficient_aligned_history")
            series[symbol] = values.tail(window + 1)
        prices = pd.DataFrame(series)
        returns = prices.pct_change(fill_method=None).iloc[1:]
        if len(returns) != window or returns.isna().any().any():
            raise ValueError("insufficient_aligned_history")
        cov = returns.cov(ddof=1).to_numpy()
        vector = np.array([float(b.dec(weights[t])) for t in selected])
        variance = float(vector @ cov @ vector) * b.POLICY["annualization"]
        if not math.isfinite(variance) or variance < -1e-15:
            raise ValueError("invalid_covariance")
        corr = returns.corr()
        base.update(
            volatility=str(math.sqrt(max(0, variance))),
            covariance_daily={
                a: {c: str(cov[i, j]) for j, c in enumerate(selected)}
                for i, a in enumerate(selected)
            },
            correlations={
                a: {
                    c: str(corr.loc[a, c]) if pd.notna(corr.loc[a, c]) else None
                    for c in selected
                }
                for a in selected
            },
            correlation_note="Undefined correlation for constant returns remains null; covariance still observed.",
            aligned_returns=len(returns),
            start=str(returns.index[0].date()),
            end=day,
        )
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        base["errors"].append(str(exc))
    if base["volatility"] is not None and b.dec(base["volatility"]) > b.dec(
        b.POLICY["max_volatility"]
    ):
        base["errors"].append("portfolio_volatility_limit")
    if b.dec(base["drawdown"]) > b.dec(b.POLICY["max_drawdown"]):
        base["errors"].append("portfolio_drawdown_limit")
    base["status"] = "BLOCKED" if base["errors"] else "OK"
    return b.sealed(base)


def proposal(
    state, context, operations, targets, cash, *, record_id, at, expires_at, reasoning
):
    report = risk(state, context)
    return b.sealed(
        {
            "schema_version": 1,
            "identity": b.IDENTITY,
            "portfolio_id": state["portfolio_id"],
            "mode": "synthetic",
            "record_id": b.key(record_id),
            "planner": "DEMO_RULE_BASED",
            "decision_session": state["marks"]["session"],
            "created_at": at,
            "not_before_session": state["marks"]["session"],
            "expires_at": expires_at,
            "state_sha256": b.financial_hash(state),
            "opinion_hashes": {
                t: item["sha256"] for t, item in context["opinions"].items()
            },
            "marks_sha256": context["marks"]["sha256"],
            "risk_report_sha256": report["sha256"],
            "limits_sha256": b.digest(b.POLICY),
            "current_weights": {
                t: p["weight"] for t, p in b.view(state)["positions"].items()
            },
            "target_weights": targets,
            "target_cash_weight": cash,
            "operations": operations,
            "reasoning": reasoning,
        }
    )


def validate(state, p, context, at):
    result = {
        "schema_version": 1,
        "identity": b.IDENTITY,
        "mode": "synthetic",
        "proposal_sha256": p.get("sha256"),
        "state_sha256": b.financial_hash(state),
        "checked_at": at,
        "valid": False,
        "errors": [],
        "ready_operations": [],
        "deferred_operations": [],
        "projected": None,
        "future_conditional": None,
        "risk_current": None,
        "risk_projected": None,
    }
    try:
        b.check_seal(p)
        if (
            set(p) != PROPOSAL_FIELDS
            or p["schema_version"] != 1
            or p["identity"] != b.IDENTITY
            or p["portfolio_id"] != state["portfolio_id"]
            or p["mode"] != "synthetic"
            or p["planner"] != "DEMO_RULE_BASED"
        ):
            raise ValueError("proposal_contract_or_identity")
        b.key(p["record_id"])
        day = p["decision_session"]
        b.session(day)
        b.session(p["not_before_session"])
        compatible(context, day, p["created_at"])
        if (
            day != state["marks"]["session"]
            or day != state["as_of_session"]
            or p["not_before_session"] > b.instant(at).date().isoformat()
            or b.instant(at).date().isoformat() != day
        ):
            raise ValueError("proposal_session_not_eligible")
        if not b.instant(p["created_at"]) <= b.instant(at) < b.instant(p["expires_at"]):
            raise ValueError("proposal_expired_or_future")
        if (
            p["state_sha256"] != b.financial_hash(state)
            or p["limits_sha256"] != b.digest(b.POLICY)
            or p["marks_sha256"] != state["marks"]["sha256"]
            or context["marks"] != state["marks"]
        ):
            raise ValueError("proposal_state_marks_or_limits_hash")
        if p["opinion_hashes"] != {
            t: item["sha256"] for t, item in context["opinions"].items()
        }:
            raise ValueError("opinion_hash_mismatch")
        if not p["reasoning"] or p["current_weights"] != {
            t: item["weight"] for t, item in b.view(state)["positions"].items()
        }:
            raise ValueError("reasoning_or_current_weights")
        for t, w in p["target_weights"].items():
            b.ticker(t)
            if t not in state["marks"]["prices"]:
                raise ValueError("target_missing_mark")
            if b.dec(w) < 0 or b.dec(w) > b.dec(b.POLICY["max_concentration"]):
                raise ValueError("negative_or_excessive_target_weight")
        if (
            b.dec(p["target_cash_weight"]) < 0
            or sum((b.dec(w) for w in p["target_weights"].values()), b.ZERO)
            + b.dec(p["target_cash_weight"])
            != 1
        ):
            raise ValueError("weights_must_sum_to_one")
        current = risk(state, context)
        result["risk_current"] = current
        if p["risk_report_sha256"] != current["sha256"]:
            raise ValueError("risk_report_hash_mismatch")
        if (
            not isinstance(p["operations"], list)
            or len(p["operations"]) > b.POLICY["max_operations"]
        ):
            raise ValueError("operation_count_limit")
        ids, legs, prior_sales = set(), set(), set()
        ordered = sorted(
            p["operations"], key=lambda o: (o["priority"], o["operation_id"])
        )
        if not ordered and (
            p["target_weights"] != p["current_weights"]
            or b.dec(p["target_cash_weight"]) != b.dec(b.view(state)["cash_weight"])
        ):
            raise ValueError("no_operation_targets_must_preserve_state")
        for op in ordered:
            b.operation(op)
            oid = op["operation_id"]
            if (
                oid in ids
                or (op["ticker"], op["side"]) in legs
                or oid in state["used_orders"]
            ):
                raise ValueError("duplicate_order")
            ids.add(oid)
            legs.add((op["ticker"], op["side"]))
            opinion = context["opinions"].get(op["ticker"])
            if opinion is None:
                raise ValueError("missing_opinion_hold_only")
            if opinion["risk_verdict"] == "VETADO":
                raise ValueError("individual_veto")
            if op["side"] == "BUY" and opinion["recommendation"] != "COMPRA":
                raise ValueError("buy_incompatible_with_opinion")
            if op["dependencies"]:
                if op["side"] != "BUY" or any(
                    dep not in prior_sales and dep not in state["executions"]
                    for dep in op["dependencies"]
                ):
                    raise ValueError("dependency_cycle_unknown_or_not_sale")
                if any(
                    dep in state["executions"]
                    and state["executions"][dep]["operation"]["side"] != "SELL"
                    for dep in op["dependencies"]
                ):
                    raise ValueError("dependency_not_sale")
            if op["side"] == "SELL":
                prior_sales.add(oid)
            waiting = any(dep not in state["settlements"] for dep in op["dependencies"])
            result["deferred_operations" if waiting else "ready_operations"].append(op)
        projection = copy.deepcopy(state)
        ready = result["ready_operations"]
        if ready:
            b.reserve(projection, ready)
            b.fill(projection, ready, day)
        projected = b.safety(projection, limits=bool(ready))
        result["projected"] = projected
        projected_risk = risk(projection, context)
        result["risk_projected"] = projected_risk
        if ready and projected_risk["status"] != "OK":
            raise ValueError("global_risk_blocked:" + ",".join(projected_risk["errors"]))
        equity = b.dec(b.view(state)["equity"])
        turnover = (
            sum(
                (
                    b.dec(op["quantity"]) * b.dec(state["marks"]["prices"][op["ticker"]])
                    for op in ordered
                ),
                b.ZERO,
            )
            / equity
        )
        costs = sum(
            (
                b.cost(
                    b.dec(op["quantity"]) * b.dec(state["marks"]["prices"][op["ticker"]])
                )
                for op in ordered
            ),
            b.ZERO,
        )
        result.update(
            turnover=str(turnover),
            estimated_costs=str(costs),
            post_cost_equity=projected["equity"],
        )
        previous_trades = [
            e for e in state["executions"].values() if e["trade_session"] == day
        ]
        daily_turnover = (
            turnover
            + sum(
                (b.dec(e["quantity"]) * b.dec(e["raw_price"]) for e in previous_trades),
                b.ZERO,
            )
            / equity
        )
        daily_costs = costs + sum((b.dec(e["cost"]) for e in previous_trades), b.ZERO)
        result.update(
            turnover_session=str(daily_turnover), costs_session=str(daily_costs)
        )
        if ordered and len(previous_trades) + len(ordered) > b.POLICY["max_operations"]:
            raise ValueError("daily_operation_count_limit")
        if ordered and (
            daily_turnover > b.dec(b.POLICY["max_turnover"])
            or daily_costs / equity > b.dec(b.POLICY["max_cost_weight"])
        ):
            raise ValueError("turnover_or_cost_limit")
        if result["deferred_operations"]:
            # Conditional projection is never an executable cash balance.
            future = copy.deepcopy(projection)
            for op in result["deferred_operations"]:
                for dep in op["dependencies"]:
                    if dep not in future["settlements"]:
                        ex = future["executions"][dep]
                        future = b.apply(
                            future,
                            "SETTLED",
                            {
                                "operation_id": dep,
                                "session": max(
                                    ex["due_session"], future["as_of_session"]
                                ),
                                "confirmation_source": "CONDITIONAL_PROJECTION_ONLY",
                            },
                        )
                hypothetical = copy.deepcopy(op)
                future["marks"] = b.marks(
                    future["as_of_session"], future["marks"]["prices"]
                )
                b.reserve(future, [hypothetical])
                b.fill(future, [hypothetical], future["as_of_session"])
            result["future_conditional"] = b.view(future)
            future_risk = risk(
                future,
                context,
                weights={
                    t: item["weight"] for t, item in b.view(future)["positions"].items()
                },
            )
            if future_risk["status"] != "OK":
                raise ValueError("conditional_risk_blocked")
            result["dependency_note"] = (
                "WAIT_FOR_CONFIRMED_SETTLEMENT_AND_NEW_PROPOSAL_APPROVAL; prices are conditional."
            )
        # Targets describe intent. Integer quantities, fees and limit prices drive
        # the separately displayed financial projection; targets never size fills.
        result["valid"] = True
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        result["errors"].append({"code": str(exc), "stage": "DETERMINISTIC_VALIDATOR"})
    return b.sealed(result)


class FakePortfolioManager:
    """Offline scripted planner: explicit targets; confidence never enters sizing."""

    def propose(
        self, state, context, targets, cash, *, record_id, at, expires_at, reasoning
    ):
        operations = []
        view = b.view(state)
        for symbol in sorted(set(view["positions"]) | set(targets)):
            price = b.dec(state["marks"]["prices"][symbol])
            held = b.dec(state["positions"].get(symbol, b.position())["quantity"])
            target = b.dec(targets.get(symbol, "0"))
            # ponytail: one pass at unchanged demo marks with fee-aware sizing;
            # intent may leave extra cash. Real optimization needs an approved policy.
            desired = (
                target
                * b.dec(view["equity"])
                / (price * (1 + b.dec(b.POLICY["fee_rate"])))
            ).to_integral_value(rounding=ROUND_DOWN)
            delta = desired - held
            if delta == 0:
                continue
            side = "BUY" if delta > 0 else "SELL"
            notional = abs(delta) * price
            operations.append(
                {
                    "operation_id": record_id + "-" + symbol.lower(),
                    "ticker": symbol,
                    "side": side,
                    "quantity": str(abs(delta)),
                    "limit_price": str(price),
                    "cost_ceiling": str(b.cost(notional)),
                    "funding_source": "SETTLED_CASH" if side == "BUY" else None,
                    "priority": 2 if side == "BUY" else 1,
                    "dependencies": [],
                    "reasoning": reasoning,
                }
            )
        return proposal(
            state,
            context,
            operations,
            targets,
            cash,
            record_id=record_id,
            at=at,
            expires_at=expires_at,
            reasoning=reasoning,
        )


def publish(store, p, context, at):
    state = store.load()[0]
    report = validate(state, p, context, at)
    store.append(
        "PROPOSED",
        {"record": p, "validation": report, "context": context},
        "propose-" + p["record_id"],
    )
    return report


def approve_demo(store, p, context, at, *, action="APPROVE"):
    state = store.load()[0]
    report = validate(state, p, context, at)
    if (
        p["record_id"] not in state["proposals"]
        or state["proposals"][p["record_id"]] != p
    ):
        raise ValueError("proposal_not_persisted")
    if action not in ("APPROVE", "REJECT") or (
        action == "APPROVE" and not report["valid"]
    ):
        raise ValueError("invalid_proposal_or_action")
    approval = b.demo_approval(
        state,
        report["ready_operations"],
        proposal_sha256=p["sha256"],
        risk_sha256=p["risk_report_sha256"],
        at=at,
        expires_at=p["expires_at"],
        action=action,
    )
    store.append(
        "APPROVED",
        {"record": approval, "validation": report},
        "approve-" + p["record_id"],
    )
    return approval


def execute_demo(store, p, context, approval, at):
    state = store.load()[0]
    report = validate(state, p, context, at)
    if (
        not report["valid"]
        or approval["proposal_sha256"] != p["sha256"]
        or approval["record_id"] not in state["approvals"]
        or state["approvals"][approval["record_id"]] != approval
        or approval["action"] != "APPROVE"
    ):
        raise ValueError("proposal_or_approval_not_executable")
    ready = report["ready_operations"]
    if not ready:
        return state
    state = store.append(
        "RESERVED",
        {
            "operations": ready,
            "approval": approval,
            "state_sha256": b.financial_hash(state),
            "at": at,
        },
        "reserve-" + p["record_id"],
    )
    return store.append(
        "FILLED",
        {
            "reserved_state_sha256": b.financial_hash(state),
            "session": state["marks"]["session"],
            "at": at,
        },
        "fill-" + p["record_id"],
    )


def fixture_context(day, prices=None):
    """Five synthetic opinions and deterministic histories, no LLM/parser calls."""
    prices = prices or {
        "PETR4": "40.00",
        "VALE3": "60.00",
        "ITUB4": "30.00",
        "WEGE3": "50.00",
        "BBAS3": "25.00",
    }
    histories = {}
    for index, symbol in enumerate(prices):
        frame = radar.synthetic_bars(pd.Timestamp(day), index)
        histories[symbol] = [
            [str(d.date()), str(v)] for d, v in frame["fechamento"].items()
        ]
    manifest = b.digest(
        {"fixture": "SYNTHETIC_FULL_COMMITTEES_V1", "identity": radar.IDENTITY}
    )
    opinions = {
        t: b.sealed(
            {
                "schema_version": 1,
                "identity": radar.IDENTITY,
                "ticker": t,
                "session": day,
                "mode": "synthetic",
                "source_family": "SYNTHETIC_FULL_COMMITTEES_V1",
                "generated_at": day + "T18:30:00-03:00",
                "recommendation": "COMPRA",
                "risk_verdict": "APROVADO",
                "votes_count": 5,
                "result_sha256": b.digest({"ticker": t, "votes": ["COMPRA"] * 5}),
                "input_sha256": b.digest({"ticker": t, "session": day}),
                "history_sha256": hashlib.sha256(
                    b.digest(histories[t]).encode()
                ).hexdigest(),
                "manifest_sha256": manifest,
                "origin": "SYNTHETIC_FIXTURE_NOT_GEMINI",
            }
        )
        for t in prices
    }
    return {
        "marks": b.marks(day, prices),
        "opinions": opinions,
        "histories": histories,
        "sectors": None,
    }
