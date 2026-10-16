"""Deterministic offline lifecycle. All DB writes use an external TemporaryDirectory."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import paper_ledger as ledger  # noqa: E402

from src.experiments.h2_evaluation_offline import no_network  # noqa: E402

b, manager = ledger.b, ledger.manager
PRICES = {"PETR4": "40.00", "VALE3": "60.00"}
PORTFOLIO = "synthetic-v765"
DAY = "2026-04-17"


def operation(
    oid, symbol="PETR4", side="BUY", quantity="100", price="40.00", dependencies=None
):
    dependencies = dependencies or []
    return {
        "operation_id": oid,
        "ticker": symbol,
        "side": side,
        "quantity": quantity,
        "limit_price": price,
        "cost_ceiling": "100.00",
        "funding_source": ("SETTLEMENT" if dependencies else "SETTLED_CASH")
        if side == "BUY"
        else None,
        "priority": 1 if side == "SELL" else 2,
        "dependencies": dependencies,
        "reasoning": "Explicit synthetic fixture; no LLM decision or official order.",
    }


def append(store, kind, payload, command, *, day=DAY, authorization_ref=None, **kwargs):
    return store.append(
        PORTFOLIO,
        kind,
        payload,
        command,
        effective_at=day + "T19:00:00-03:00",
        authorization_ref=authorization_ref,
        **kwargs,
    )


def proposal_payload(store, operations, record_id, day=DAY, *, veto=None):
    state = store.load(PORTFOLIO)[0]["financial"]
    context = manager.fixture_context(day, state["marks"]["prices"])
    context["marks"] = state["marks"]
    if veto:
        opinion = context["opinions"][veto]
        context["opinions"][veto] = b.sealed(
            {
                **{k: v for k, v in opinion.items() if k != "sha256"},
                "risk_verdict": "VETADO",
            }
        )
    view = b.view(state)
    targets = {t: p["weight"] for t, p in view["positions"].items()}
    proposal = manager.proposal(
        state,
        context,
        operations,
        targets,
        view["cash_weight"],
        record_id=record_id,
        at=day + "T19:00:00-03:00",
        expires_at=day + "T22:00:00-03:00",
        reasoning="Synthetic lifecycle qualification with explicit quantities; no official decision.",
    )
    return {"record": proposal, "context": context}


def authorize(store, operations, prefix, day=DAY, *, veto=None):
    payload = proposal_payload(store, operations, prefix, day, veto=veto)
    append(store, "PROPOSAL_LINKED", payload, "proposal-" + prefix, day=day)
    state, event = append(
        store,
        "VALIDATION_RECORDED",
        {"proposal_id": prefix},
        "validation-" + prefix,
        day=day,
    )
    validation = state["validations"][event["event_id"]]
    p = {
        "validation_id": event["event_id"],
        "validation_sha256": validation["sha256"],
        "proposal_id": prefix,
        "proposal_sha256": payload["record"]["sha256"],
        "portfolio_id": PORTFOLIO,
        "scope": ledger.IDENTITY,
        "operator": "SYNTHETIC_TEST_OPERATOR",
        "action": "APPROVE",
        "expires_at": day + "T22:00:00-03:00",
    }
    _, authorization = append(
        store, "AUTHORIZATION_RECORDED", p, "authorize-" + prefix, day=day
    )
    return authorization["event_id"]


def trade(store, operations, prefix, day=DAY):
    ref = authorize(store, operations, prefix, day)
    append(
        store,
        "PAPER_ORDER_CREATED",
        {"proposal_id": prefix},
        "reserve-" + prefix,
        day=day,
        authorization_ref=ref,
    )
    append(
        store,
        "PAPER_ORDER_EXECUTED",
        {"execution_id": "execution-" + prefix},
        "fill-" + prefix,
        day=day,
        authorization_ref=ref,
    )


def mark(
    store,
    day,
    prices,
    *,
    classification="SYNTHETIC_TEST",
    price_type="SYNTHETIC_REFERENCE",
    command=None,
):
    command = command or day
    _, event = append(
        store,
        "MARKET_PRICE_OBSERVED",
        {
            "observation": ledger.observation(
                day, prices, classification=classification, price_type=price_type
            )
        },
        "observe-" + command,
        day=day,
    )
    return append(
        store,
        "PORTFOLIO_VALUED",
        {"observation_id": event["event_id"]},
        "value-" + command,
        day=day,
    )


def settle(store, oid, day):
    return append(
        store,
        "SETTLEMENT_RECORDED",
        {
            "order_id": oid,
            "settlement_id": "settlement-" + oid,
            "confirmation_source": "SYNTHETIC_CUSTODIAN_CONFIRMATION",
        },
        "settle-" + oid,
        day=day,
    )


def lifecycle(store):
    append(store, "PORTFOLIO_CREATED", ledger.creation(PORTFOLIO, DAY, PRICES), "create")
    trade(
        store,
        [operation("buy-petr"), operation("buy-vale", "VALE3", price="60.00")],
        "buy",
    )
    append(store, "PORTFOLIO_RECONCILED", {}, "reconcile-17")
    mark(store, "2026-04-20", {"PETR4": "42.00", "VALE3": "59.00"})
    append(store, "PORTFOLIO_RECONCILED", {}, "reconcile-20", day="2026-04-20")
    settle(store, "buy-petr", "2026-04-22")
    settle(store, "buy-vale", "2026-04-22")
    mark(store, "2026-04-22", {"PETR4": "43.00", "VALE3": "61.00"})
    trade(
        store,
        [operation("sell-petr", side="SELL", quantity="40", price="43.00")],
        "sell",
        "2026-04-22",
    )
    append(store, "PORTFOLIO_RECONCILED", {}, "reconcile-22", day="2026-04-22")
    mark(store, "2026-04-23", {"PETR4": "39.00", "VALE3": "58.00"})
    append(store, "PORTFOLIO_RECONCILED", {}, "reconcile-23", day="2026-04-23")
    settle(store, "sell-petr", "2026-04-24")
    mark(store, "2026-04-24", {"PETR4": "41.00", "VALE3": "60.00"})
    append(store, "PORTFOLIO_RECONCILED", {}, "reconcile-24", day="2026-04-24")
    # A fresh read-only instance is the restart boundary, not an in-memory object.
    restarted = ledger.Store(store.path)
    assert restarted.verify(PORTFOLIO)["ok"], restarted.verify(PORTFOLIO)
    assert restarted.load(PORTFOLIO)[0] == store.load(PORTFOLIO)[0]
    return restarted.export(PORTFOLIO)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    args = parser.parse_args()
    with no_network(), tempfile.TemporaryDirectory(prefix="hfl-paper-") as folder:
        store = ledger.Store.create(Path(folder) / "ledger.sqlite3")
        result = lifecycle(store)
        state = result["checkpoint"]["state"]
        print(
            json.dumps(
                {
                    "identity": ledger.IDENTITY,
                    "status": "SYNTHETIC_LIFECYCLE_PASSED",
                    "events": len(result["events"]),
                    "sessions": [h["session"] for h in state["history"]],
                    "summary": b.view(state["financial"]),
                },
                indent=1,
            )
        )
        if args.export:
            # Qualification evidence only; never an official data/ ledger.
            target = args.export.resolve()
            evidence = ROOT / "docs/evidence/hfl_paper_ledger_v765"
            if target.parent != evidence or target.name != "synthetic_ledger.json":
                raise ValueError("qualification_evidence_export_only")
            with target.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
