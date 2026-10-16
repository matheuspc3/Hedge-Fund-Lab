"""Verified, GET-only PAPER-02 read model. Never opens SQLite or runs a qualifier."""

import copy
import os
from bisect import bisect_left, bisect_right
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pilot_paper as pilot

b, data = pilot.b, pilot.data
IDENTITY = "HFL-PILOT-DEMO-EXPORT-V1"
DEFAULT_FILE = pilot.ledger.ROOT / "data/platform/pilot-demo.json"
PERIODS = ("day", "since_start", "month", "year", "last_12_months")
LABELS = {
    pilot.AGENTS: "Agentes roteirizados — demonstração",
    pilot.REFERENCE: "Buy & Hold 20% inicial — demonstração",
}


def demo_path():
    return Path(os.environ.get("HFL_PILOT_DEMO", str(DEFAULT_FILE))).resolve()


def delta(value, base):
    value, base = b.dec(value), b.dec(base)
    if base <= 0:
        raise ValueError("nonpositive_metric_anchor")
    return {"change_brl": str(value - base), "change_pct": str((value / base - 1) * 100)}


def periods(history, calendar, selected):
    """Calendar anchors and a complete reconciled chain; no older substitute."""
    days = data.check_calendar(calendar)
    points = {h["session"]: h["view"] for h in history}
    if len(points) != len(history) or list(points) != sorted(points):
        raise ValueError("history_order_or_duplicate")
    data.calendar_session(calendar, selected)
    current = points.get(selected)
    initial = history[0] if history else None
    result = {}
    for period in PERIODS:
        metric = {
            "status": "INSUFFICIENT_HISTORY",
            "session": selected,
            "anchor_session": None,
            "change_brl": None,
            "change_pct": None,
            "partial": None,
            "missing_sessions": [],
        }
        if not current:
            metric["status"] = "SESSION_UNAVAILABLE"
        elif initial:
            start = initial["session"]
            since_days = [d for d in days if start <= d <= selected]
            since_complete = all(d in points for d in since_days)
            if since_complete:
                partial = {
                    "label": "Desde o início (parcial)",
                    "anchor_session": start,
                    **delta(current["equity"], initial["view"]["initial_capital"]),
                }
                metric["partial"] = partial
            end = date.fromisoformat(selected)
            if period == "since_start":
                anchor = start
            elif period == "day":
                index = days.index(selected)
                anchor = days[index - 1] if index else None
            else:
                if period == "month":
                    boundary = end.replace(day=1).isoformat()
                    index = bisect_left(days, boundary) - 1
                elif period == "year":
                    boundary = end.replace(month=1, day=1).isoformat()
                    index = bisect_left(days, boundary) - 1
                else:
                    # Civil 12 months, including leap day; never 252 observations/YTD.
                    boundary = end.replace(
                        year=end.year - 1,
                        day=28 if end.month == 2 and end.day == 29 else end.day,
                    ).isoformat()
                    index = bisect_right(days, boundary) - 1
                anchor = days[index] if index >= 0 and days[0] <= boundary else None
            metric["anchor_session"] = anchor
            if anchor and anchor >= start:
                required = [d for d in days if anchor <= d <= selected]
                missing = [d for d in required if d not in points]
                metric["missing_sessions"] = missing
                if missing:
                    metric["status"] = "UNAVAILABLE"
                    metric["partial"] = None
                elif period == "day" and selected == start:
                    pass  # Initial baseline is not a daily return.
                else:
                    base = (
                        initial["view"]["initial_capital"]
                        if period == "since_start"
                        else points[anchor]["equity"]
                    )
                    metric.update(
                        status="AVAILABLE", partial=None, **delta(current["equity"], base)
                    )
            if period == "since_start" and not since_complete:
                metric.update(status="UNAVAILABLE", partial=None)
        result[period] = metric
    return result


@lru_cache(maxsize=2)
def verified(raw, implementation_sha):
    # ponytail: replay each distinct artifact/implementation once; bytes are reread
    # on every GET so replacement/corruption cannot hide behind a path/mtime cache.
    artifact = b.check_seal(data.load_json(raw))
    if set(artifact) != {
        "schema_version",
        "identity",
        "classification",
        "official_activation",
        "ledgers",
        "projection",
        "sha256",
    } or (
        artifact["schema_version"] != 1
        or type(artifact["schema_version"]) is not int
        or artifact["identity"] != IDENTITY
        or artifact["classification"] != "SYNTHETIC_TEST"
        or artifact["official_activation"] is not False
        or len(artifact["ledgers"]) != 2
    ):
        raise ValueError("invalid_demo_schema_or_classification")
    states = {}
    for export in artifact["ledgers"]:
        b.check_seal(export)
        if (
            export["identity"] != pilot.IDENTITY
            or export["classification"] != "SYNTHETIC_TEST"
        ):
            raise ValueError("invalid_demo_ledger_identity")
        state = pilot.replay(export["events"], export["checkpoint"])
        pid = state["portfolio"]["portfolio_id"]
        if pid in states:
            raise ValueError("duplicate_demo_wallet")
        states[pid] = state, export["events"], export["checkpoint"]
    if {s[0]["portfolio"]["strategy"] for s in states.values()} != set(LABELS):
        raise ValueError("demo_strategy_mismatch")
    store = SimpleNamespace(load=lambda pid: states[pid])
    if pilot.projection(store, list(states)) != artifact["projection"]:
        raise ValueError("demo_projection_replay_mismatch")
    return artifact, states


def read_demo(path=None):
    return copy.deepcopy(
        verified((path or demo_path()).read_bytes(), b.digest(pilot.fingerprints()))
    )


def comparison(states, calendar, selected):
    maps = {
        pid: {h["session"]: h["view"] for h in state["history"]}
        for pid, (state, _, _) in states.items()
    }
    common = set.intersection(*(set(points) for points in maps.values()))
    common = {d for d in common if d <= selected}
    anchor = min(common) if common else None
    sessions = [d for d in calendar["sessions"] if anchor and anchor <= d <= selected]
    series = []
    for pid, points in maps.items():
        base = points[anchor]["equity"] if anchor else None
        series.append(
            {
                "id": pid,
                "label": LABELS[states[pid][0]["portfolio"]["strategy"]],
                "points": [
                    {
                        "session": d,
                        "equity": points[d]["equity"] if d in points else None,
                        "value": str(b.dec(points[d]["equity"]) / b.dec(base) * 100)
                        if d in points
                        else None,
                    }
                    for d in sessions
                ],
            }
        )
    return {
        "status": "AVAILABLE" if len(common) >= 2 else "INSUFFICIENT_HISTORY",
        "anchor_session": anchor,
        "sessions": sessions,
        "series": series,
    }


def get(query):
    if (
        set(query) - {"demo", "wallet", "session", "period"}
        or any(not isinstance(value, str) or not value for value in query.values())
        or query.get("demo", "0") not in ("0", "1")
        or query.get("period", "since_start") not in PERIODS
    ):
        raise ValueError("invalid_query")
    if query.get("demo") != "1":
        if set(query) - {"demo"}:
            raise ValueError("explicit_demo_required")
        return {
            "available": False,
            "status": "NOT_STARTED",
            "wallets": [],
            "message": "Carteira multiativos ainda não iniciada",
        }
    try:
        artifact, states = read_demo()
    except FileNotFoundError:
        return {
            "available": False,
            "status": "DEMO_NOT_PREPARED",
            "wallets": [],
            "message": "Demonstração ainda não preparada. Execute o comando de preparação local.",
        }
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError, AttributeError):
        return {
            "available": False,
            "status": "INTEGRITY_INVALID",
            "wallets": [],
            "message": "Integridade da demonstração inválida. Nenhum saldo será apresentado.",
        }
    catalog = [
        {"id": pid, "label": LABELS[state["portfolio"]["strategy"]]}
        for pid, (state, _, _) in states.items()
    ]
    pid = query.get("wallet", catalog[0]["id"])
    if pid not in states:
        raise ValueError("unknown_demo_wallet")
    state, events, _ = states[pid]
    calendar, history = state["calendar"], state["history"]
    if not history:
        return {
            "available": False,
            "status": "EMPTY_HISTORY",
            "wallets": catalog,
            "message": "Esta demonstração ainda não possui sessões reconciliadas. Nenhum saldo será apresentado.",
        }
    selected = query.get(
        "session", history[-1]["session"] if history else calendar["sessions"][-1]
    )
    data.calendar_session(calendar, selected)
    point = next((h for h in history if h["session"] == selected), None)
    latest = history[-1]["session"] if history else None
    result = {
        "available": True,
        "read_only": True,
        "classification": "SYNTHETIC_TEST",
        "status": "AVAILABLE" if point else "SESSION_UNAVAILABLE",
        "wallets": catalog,
        "wallet": pid,
        "label": LABELS[state["portfolio"]["strategy"]],
        "session": selected,
        "last_reconciled_session": latest,
        "scenario": {
            "start": history[0]["session"] if history else None,
            "end": latest,
            "calendar": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
        },
        "sessions": [
            d for d in calendar["sessions"] if history and d >= history[0]["session"]
        ],
        "period": query.get("period", "since_start"),
        "periods": periods(history, calendar, selected),
        "summary": None,
        "assets": [],
        "decision": None,
        "trades": [],
        "comparison": comparison(states, calendar, selected),
        "source": "PAPER-02 · COTAHIST RAW sintético · agentes roteirizados",
        "pending_session": state["last_economic_at"][:10]
        if state["valuation_unavailable"]
        else None,
        "integrity": {"status": "VERIFIED", "artifact_sha256": artifact["sha256"]},
    }
    if not point:
        return result
    view = point["view"]
    held = {t: p for t, p in view["positions"].items() if b.dec(p["quantity"]) > 0}
    result["summary"] = {
        k: view[k] for k in ("equity", "cash", "costs", "realized_pnl", "unrealized_pnl")
    }
    result["summary"].update(
        invested=str(sum((b.dec(p["market_value"]) for p in held.values()), b.ZERO)),
        position_count=len(held),
    )
    quotes = {}
    for event in events:
        quote = event["payload"].get("quote")
        if quote:
            quotes[quote["bundle"]["sha256"]] = quote["bundle"]
    bundle = quotes[point["quote_sha256"]]
    close = data.prices(bundle, selected, "CLOSE", at=bundle["import"]["available_at"])
    index = calendar["sessions"].index(selected)
    previous_day = calendar["sessions"][index - 1] if index else None
    previous = next((h for h in history if h["session"] == previous_day), None)
    previous_close = None
    if previous:
        previous_bundle = quotes[previous["quote_sha256"]]
        previous_close = data.prices(
            previous_bundle,
            previous_day,
            "CLOSE",
            at=previous_bundle["import"]["available_at"],
        )
    for ticker in data.UNIVERSE:
        position = held.get(ticker)
        previous_position = (
            previous["view"]["positions"].get(ticker) if previous else None
        )
        result["assets"].append(
            {
                "ticker": ticker,
                "close": close[ticker],
                "price_session": selected,
                "previous_session": previous_day,
                "price_change": delta(close[ticker], previous_close[ticker])
                if previous_close
                else None,
                "position": {
                    k: position[k]
                    for k in (
                        "quantity",
                        "raw_mark",
                        "market_value",
                        "weight",
                        "average_cost",
                        "unrealized_pnl",
                    )
                }
                if position
                else None,
                "position_value_change": str(
                    b.dec(position["market_value"])
                    - b.dec(previous_position["market_value"])
                )
                if position
                and previous_position
                and b.dec(previous_position["quantity"]) > 0
                else None,
                "position_status": "HELD"
                if position
                and previous_position
                and b.dec(previous_position["quantity"]) > 0
                else "NEW_POSITION"
                if position
                else "NO_POSITION",
                "initial_target": "0.20"
                if state["portfolio"]["strategy"] == pilot.REFERENCE
                else None,
            }
        )
    decisions = [p for p in state["proposals"].values() if p["data_session"] <= selected]
    if decisions:
        proposal = max(decisions, key=lambda p: p["decision_at"])
        result["decision"] = {
            "action": proposal["action"],
            "session": proposal["data_session"],
            "target_session": proposal["target_session"],
            "producer": "Roteiro sintético",
        }
    result["trades"] = [
        {
            "session": t["trade_session"],
            "decision_session": t["decision_session"],
            "ticker": t["operation"]["ticker"],
            "side": t["operation"]["side"],
            "quantity": t["quantity"],
            "price": t["raw_price"],
            "cost": t["cost"],
            "due_session": t["due_session"],
        }
        for t in state["trades"]
        if t["trade_session"] <= selected
    ][-5:]
    return result
