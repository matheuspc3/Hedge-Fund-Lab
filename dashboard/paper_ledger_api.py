"""GET-only projections of exported qualification evidence. Never opens a writer."""

from datetime import date, datetime, timezone

import paper_ledger as ledger

b = ledger.b
FIXTURE = ledger.ROOT / "docs/evidence/hfl_paper_ledger_v765/synthetic_ledger.json"
RESOURCES = {
    "events",
    "sessions",
    "trades",
    "settlements",
    "reconciliations",
    "orders",
    "observations",
}


def official_reference(record_id):
    """Reference the original result; never adapt it into an executable V5 proposal."""
    import platform_api

    record = platform_api.public_global(record_id)
    result = record["result"]
    if record["mode"] != "CONSULTATIVE_SANDBOX":
        raise ValueError("official_consultative_reference_required")
    return b.sealed(
        {
            "record_id": record_id,
            "identity": record["identity"],
            "classification": "CONSULTATIVE_SNAPSHOT",
            "context_sha256": record["context_sha256"],
            "result_sha256": result["sha256"],
            "validation_sha256": result["validation"]["sha256"],
            "status": record["validation_status"],
            "operation_count": len((result.get("response") or {}).get("operations", [])),
            "execution_enabled": False,
        }
    )


def read_fixture():
    artifact = b.check_seal(b.read(FIXTURE))
    if (
        artifact["identity"] != ledger.IDENTITY
        or artifact["classification"] != "SYNTHETIC_TEST"
    ):
        raise ValueError("synthetic_fixture_identity_required")
    state = ledger.replay(artifact["events"], artifact["checkpoint"])
    return state, artifact["events"]


def page(items, offset, limit):
    return {
        "items": items[offset : offset + limit],
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "next_offset": offset + limit if offset + limit < len(items) else None,
    }


def read_model(state, events, query):
    source = "/api/portfolio/ledger?demo=1&wallet=" + state["portfolio"]["portfolio_id"]
    selected = next(
        (h for h in state["history"] if h["session"] == query.get("session")), None
    )
    if query.get("session") and selected is None:
        raise ValueError("session_not_reconciled")
    view = selected["view"] if selected else b.view(state["financial"])
    quotes = [events[0]["payload"]["observation"], *state["observations"].values()]
    quote = (
        next(q for q in quotes if q["sha256"] == selected["quote_sha256"])
        if selected
        else state["quote"]
    )

    def within(day):
        return (
            bool(day)
            and query.get("from", "0000") <= day <= query.get("to", "9999")
            and (not query.get("session") or day == query["session"])
        )

    timeline = [
        {
            "kind": e["kind"],
            "session": e["session"],
            "at": e["effective_at"],
            "recorded_at": e["recorded_at"],
            "status": "SYNTHETIC_TEST",
            "sha256": e["sha256"],
            "evidence": source + "&resource=events",
            "event_id": e["event_id"],
        }
        for e in events
        if within(e["session"])
    ]
    trades = [
        {
            "order_id": oid,
            "execution_id": state["execution_ids"][oid],
            "session": ex["trade_session"],
            "ticker": ex["operation"]["ticker"],
            "type": ex["operation"]["side"],
            "quantity": ex["quantity"],
            "price": ex["raw_price"],
            "cost": ex["cost"],
            "settlement": ex["due_session"],
            "source": source,
            "decision_session": ex["trade_session"],
            "status": "SYNTHETIC_FILLED",
            "marks_sha256": ex["marks_sha256"],
            "realized_pnl": ex["realized_pnl"],
        }
        for oid, ex in view["executions"].items()
        if within(ex["trade_session"])
    ]
    curve = [
        {
            "session": h["session"],
            "equity": h["view"]["equity"],
            "cash": h["view"]["cash"]["settled"],
            "invested": str(
                sum(
                    (b.dec(p["market_value"]) for p in h["view"]["positions"].values()),
                    b.ZERO,
                )
            ),
            "receivable": h["view"]["cash"]["receivable"],
            "pnl": str(b.dec(h["view"]["equity"]) - b.dec(h["view"]["initial_capital"])),
            "costs": h["view"]["costs"],
            "realized_pnl": h["view"]["realized_pnl"],
            "unrealized_pnl": h["view"]["unrealized_pnl"],
            "exposure": h["view"]["exposure"],
            "drawdown": h["view"]["drawdown"],
            "positions": h["view"]["positions"],
            "quote_sha256": h["quote_sha256"],
            "reconciliation_id": h["reconciliation_id"],
        }
        for h in state["history"]
        if within(h["session"])
    ]
    settlements = [
        {"order_id": oid, "settlement_id": state["settlement_ids"][oid], **record}
        for oid, record in state["financial"]["settlements"].items()
        if within(record["session"])
    ]
    reconciliations = [r for r in state["reconciliations"] if within(r["session"])]
    orders = [
        e
        for e in events
        if e["kind"]
        in ("PAPER_ORDER_CREATED", "PAPER_ORDER_CANCELLED", "PAPER_ORDER_EXECUTED")
        and within(e["session"])
    ]
    resources = {
        "events": [e for e in events if within(e["session"])],
        "sessions": curve,
        "trades": trades,
        "settlements": settlements,
        "reconciliations": reconciliations,
        "orders": orders,
        "observations": [q for q in quotes if within(q["session"])],
    }
    limit, offset = int(query.get("limit", "50")), int(query.get("offset", "0"))
    if query.get("resource"):
        return {
            "identity": ledger.IDENTITY,
            "portfolio_id": view["portfolio_id"],
            "classification": "SYNTHETIC_TEST",
            "read_only": True,
            "resource": query["resource"],
            **page(resources[query["resource"]], offset, limit),
        }
    latest = reconciliations[-1] if reconciliations else None
    cash = view["cash"]
    result = {
        "id": view["portfolio_id"],
        "label": state["portfolio"]["display_name"],
        "identity": ledger.IDENTITY,
        "classification": "SYNTHETIC_TEST",
        "portfolio": state["portfolio"],
        "available": True,
        "persistent_execution": True,
        "source": source,
        "read_only": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "limitation": "DEMONSTRAÇÃO — DADOS SINTÉTICOS. Qualificação em SQLite temporário; consulta de exportação verificada. Sem tratamento científico associado. Sessões históricas de abril/2026, sem cotações em tempo real. Execução oficial desabilitada.",
        "summary": {
            "initial_capital": view["initial_capital"],
            "equity": view["equity"],
            "cash": cash["available"],
            "reserved": cash["reserved"],
            "receivable": cash["receivable"],
            "exposure": view["exposure"],
            "realized_pnl": view["realized_pnl"],
            "unrealized_pnl": view["unrealized_pnl"],
            "costs": view["costs"],
            "drawdown": view["drawdown"],
            "volatility": None,
            "pnl": str(b.dec(view["equity"]) - b.dec(view["initial_capital"])),
            "invested": str(
                sum(
                    (b.dec(p["market_value"]) for p in view["positions"].values()), b.ZERO
                )
            ),
        },
        "positions": [
            {"ticker": symbol, **pos}
            for symbol, pos in view["positions"].items()
            if b.dec(pos["quantity"]) > 0
        ],
        "allocation": [
            {"asset": symbol, "value": pos["market_value"], "weight": pos["weight"]}
            for symbol, pos in view["positions"].items()
        ]
        + [
            {
                "asset": "Caixa liquidado",
                "value": cash["settled"],
                "weight": str(
                    b.dec(view["cash_weight"]) - b.dec(view["receivable_weight"])
                ),
            },
            {
                "asset": "Recebíveis",
                "value": cash["receivable"],
                "weight": view["receivable_weight"],
            },
        ],
        "mark": quote,
        "curve": curve[offset : offset + limit],
        "trades": trades[offset : offset + limit],
        "timeline": timeline[offset : offset + limit],
        "future": [
            {
                "kind": "Liquidação sintética pendente · " + oid,
                "target_session": rec["due_session"],
                "deadline": None,
            }
            for oid, rec in view["executions"].items()
            if oid
            not in {
                key
                for key, record in state["financial"]["settlements"].items()
                if record["session"] <= view["session"]
            }
        ],
        "decision": None,
        "operation_status": "RECONCILIATION_FAILED"
        if state["reconciliation_failed"]
        else "OFFLINE_SYNTHETIC_ONLY",
        "authorization_status": "Autorizações sintéticas isoladas; não aplicáveis a campanhas oficiais",
        "last_reconciliation": latest,
        "reconciliations": reconciliations[offset : offset + limit],
        "unavailable_sessions": state["unavailable_sessions"],
        "pagination": {
            name: {k: v for k, v in page(items, offset, limit).items() if k != "items"}
            for name, items in resources.items()
        },
        "sessions_available": [h["session"] for h in state["history"]],
    }
    return result


def get(query):
    if set(query) - {
        "demo",
        "wallet",
        "resource",
        "limit",
        "offset",
        "from",
        "to",
        "session",
    } or any(not isinstance(v, str) for v in query.values()):
        raise ValueError("invalid_ledger_query")
    if query.get("demo", "0") not in ("0", "1"):
        raise ValueError("invalid_demo_selection")
    if "wallet" not in query:
        if set(query) - {"demo"}:
            raise ValueError("wallet_required")
        return {
            "identity": ledger.IDENTITY,
            "wallets": [
                {
                    "id": "synthetic-v765",
                    "label": "DEMONSTRAÇÃO · ledger sintético V7.6.5",
                    "classification": "SYNTHETIC_TEST",
                }
            ]
            if query.get("demo") == "1" and FIXTURE.is_file()
            else [],
            "read_only": True,
            "official_execution_enabled": False,
            "status": "OFFICIAL_PAPER_DISABLED",
        }
    if query.get("demo") != "1" or query["wallet"] != "synthetic-v765":
        raise ValueError("explicit_synthetic_selection_required")
    for field in ("session", "from", "to"):
        if (
            field in query
            and date.fromisoformat(query[field]).isoformat() != query[field]
        ):
            raise ValueError("invalid_session_filter")
    if query.get("from", "0000") > query.get("to", "9999"):
        raise ValueError("invalid_session_range")
    for field, default, upper in (("limit", "50", 100), ("offset", "0", 1000000)):
        value = query.get(field, default)
        if (
            not value.isascii()
            or not value.isdigit()
            or not (1 if field == "limit" else 0) <= int(value) <= upper
        ):
            raise ValueError("invalid_pagination")
    if query.get("resource") and query["resource"] not in RESOURCES:
        raise ValueError("invalid_history_resource")
    state, events = read_fixture()
    return read_model(state, events, query)
