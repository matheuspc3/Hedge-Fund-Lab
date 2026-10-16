"""Read-only synthetic portfolio projections and in-memory scenarios. No POST API."""

import os
import sys
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[1] / "scripts"),
]
import multiasset_manager as manager  # noqa: E402
import multiasset_portfolio as book  # noqa: E402
import run_multiasset_portfolio as cli  # noqa: E402

ROOT = Path(os.environ.get("HFL_PORTFOLIO_ROOT", book.OUTPUT / "demo-qualified-v5"))
SCENARIOS = ("buy", "sell_cash", "partial", "rebalance", "hold", "rotation")


def get(command, query):
    store = book.Store(ROOT)
    state, events = store.load()
    if state is None:
        if command == "status" and not query:
            return {
                "identity": book.IDENTITY,
                "mode": "synthetic",
                "initialized": False,
                "reason": "Gere a demonstração offline pelo comando documentado antes de consultar.",
            }
        raise ValueError("synthetic_demo_missing")
    demo = book.check_seal(book.read(store.root / "demo.json"))
    if (
        demo["identity"] != book.IDENTITY
        or demo["mode"] != "synthetic"
        or demo["portfolio_id"] != state["portfolio_id"]
        or demo["verification"]["head_sha256"] != events[-1]["sha256"]
    ):
        raise ValueError("demo_integrity_failed")
    context = demo["context"]
    if context["marks"] != state["marks"]:
        raise ValueError("demo_market_context_changed")
    if (
        command == "case"
        and set(query) == {"case"}
        and query["case"] in "ABCDE"
        and len(query["case"]) == 1
    ):
        return demo["cases"][ord(query["case"]) - ord("A")]
    if command == "scenario" and set(query) == {"name"} and query["name"] in SCENARIOS:
        proposal = cli.scenario(state, context, query["name"])
        return {
            "label": proposal["reasoning"],
            "before": book.view(state),
            "proposal": proposal,
            "validation": manager.validate(
                state, proposal, context, proposal["created_at"]
            ),
            "after": None,
        }
    if command == "status" and not query:
        return {
            "identity": book.IDENTITY,
            "mode": "synthetic",
            "initialized": True,
            "portfolio": book.view(state),
            "policy": book.POLICY,
            "risk": manager.risk(state, context),
            "opportunities": list(context["opinions"].values()),
            "scenarios": list(SCENARIOS),
            "cases": [
                {
                    "id": chr(65 + i),
                    "label": c["label"],
                    "valid": c["validation"]["valid"],
                }
                for i, c in enumerate(demo["cases"])
            ],
            "events": [
                {
                    k: e[k]
                    for k in (
                        "sequence",
                        "kind",
                        "record_id",
                        "created_at",
                        "sha256",
                        "previous_sha256",
                    )
                }
                for e in events
            ],
            "integrity": {
                "ok": True,
                "events": len(events),
                "head_sha256": events[-1]["sha256"],
                "state_sha256": book.financial_hash(state),
            },
            "provider_calls": 0,
            "real_orders": 0,
        }
    raise ValueError("invalid_portfolio_query")
