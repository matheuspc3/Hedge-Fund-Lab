"""One-command PAPER-02 rehearsal. No real data/network; artifacts only in TEMP.

Run: .venv/Scripts/python.exe -B scripts/qualify_pilot_paper.py
"""

import json
import socket
import sys
import tempfile
from contextlib import ExitStack
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]

import pilot_paper as pilot  # noqa: E402
from test_pilot_market_data import cotahist_line, write_fixture  # noqa: E402

b, data = pilot.b, pilot.data
SESSIONS = [
    "2026-11-03",
    "2026-11-04",
    "2026-11-05",
    "2026-11-06",
    "2026-11-09",
    "2026-11-10",
    "2026-11-11",
    "2026-11-12",
    "2026-11-13",
]
WALLETS = ("paper02-scripted-agents", "paper02-equal-weight-reference")
BASE = dict(zip(data.UNIVERSE, (4000, 6000, 3000, 5000, 2000), strict=True))


def offline(stack):
    for name in ("connect", "connect_ex"):
        stack.enter_context(
            patch.object(
                socket.socket, name, side_effect=AssertionError("network forbidden")
            )
        )
    stack.enter_context(
        patch("urllib.request.urlopen", side_effect=AssertionError("download forbidden"))
    )
    stack.enter_context(
        patch("yfinance.download", side_effect=AssertionError("download forbidden"))
    )


def fixture_inputs(root):
    """Weekday generation is ONLY a synthetic warm-up, never official coverage."""
    start = date.fromisoformat(SESSIONS[0])
    warmup = [
        str(start - timedelta(days=i))
        for i in range(130, 0, -1)
        if (start - timedelta(days=i)).weekday() < 5
    ]
    calendar_path = root / "SYNTHETIC_calendar.json"
    calendar_path.write_text(
        json.dumps(
            {
                "nature": "SYNTHETIC_TEST",
                "source": "SYNTHETIC_CALENDAR_NOT_OFFICIAL",
                "sessions": warmup + SESSIONS,
            }
        ),
        encoding="utf-8",
    )
    calendar = data.load_calendar(calendar_path)
    bundles = {}
    for i, day in enumerate(SESSIONS[:-1]):
        directory = root / day
        directory.mkdir()
        lines = [
            cotahist_line(
                symbol,
                day,
                opening=base + i * 10,
                close=base + i * 10 + 5,
                high=base + i * 10 + 15,
                low=base + i * 10 - 10,
            )
            for symbol, base in BASE.items()
        ]
        manifest, _ = write_fixture(directory, lines)
        bundle = data.import_file(manifest, calendar=calendar, sessions=[day])
        data.write_bundle(directory / "bundle.json", bundle)
        bundles[day] = bundle
    return calendar, bundles


def quote(bundle):
    day = bundle["content"]["selection"]["sessions"][0]
    return {
        "session": day,
        "fixture_released_at": day + "T18:05:00-03:00",
        "bundle": bundle,
    }


def risk_fixture(state):
    day = state["financial"]["marks"]["session"]
    dates = [d for d in state["calendar"]["sessions"] if d <= day][-61:]
    histories = {
        t: [
            [d, str(b.money(b.dec(base) / 100 + b.dec(i) / 100))]
            for i, d in enumerate(dates)
        ]
        for t, base in BASE.items()
    }
    return b.sealed(
        {
            "classification": "SYNTHETIC_TEST",
            "source": "SCRIPTED_ADJUSTED_RISK_WARMUP_FIXTURE",
            "available_at": state["quote"]["bundle"]["import"]["available_at"],
            "marks": state["financial"]["marks"],
            "histories": histories,
        }
    )


def command(store, pid, kind, payload, key, at, **kwargs):
    return store.append(pid, kind, payload, key, effective_at=at, **kwargs)


def prepare(store, pid, day, operations, *, prefix=None):
    state = store.load(pid)[0]
    rid = prefix or "decision-" + day
    record = pilot.proposal(
        state,
        operations,
        rid,
        risk_fixture=risk_fixture(state) if pid == WALLETS[0] else None,
    )
    command(
        store,
        pid,
        "PROPOSAL_LINKED",
        {"record": record},
        rid + "-proposal",
        record["decision_at"],
    )
    command(
        store,
        pid,
        "VALIDATION_RECORDED",
        {"proposal_id": rid},
        rid + "-validation",
        day + "T18:25:00-03:00",
    )
    _, auth = command(
        store,
        pid,
        "AUTHORIZATION_RECORDED",
        {
            "proposal_id": rid,
            "operator": "SYNTHETIC_TEST_OPERATOR",
            "expires_at": record["expires_at"],
        },
        rid + "-authorization",
        day + "T18:30:00-03:00",
    )
    if operations:
        command(
            store,
            pid,
            "PAPER_ORDER_CREATED",
            {"proposal_id": rid},
            rid + "-intent",
            day + "T18:35:00-03:00",
            authorization_ref=auth["event_id"],
        )
    return record, auth


def initialize(store, pid, strategy, calendar, bundle):
    day = bundle["content"]["selection"]["sessions"][0]
    command(
        store,
        pid,
        "PORTFOLIO_CREATED",
        {
            "strategy": strategy,
            "calendar": calendar,
            "parameters": pilot.test_parameters(),
            "engine_fingerprints": pilot.fingerprints(),
            "quote": quote(bundle),
            "processed_at": day + "T18:10:00-03:00",
        },
        "creation",
        day + "T18:00:00-03:00",
    )
    command(
        store,
        pid,
        "PORTFOLIO_RECONCILED",
        {},
        "reconcile-" + day,
        day + "T18:15:00-03:00",
    )


def advance_session(store, bundles, i):
    """Apply one existing scripted session; caller owns storage/transaction."""
    day = SESSIONS[i]
    if i:
        for pid in WALLETS:
            state = store.load(pid)[0]
            for oid, execution in state["financial"]["executions"].items():
                if (
                    execution["due_session"] <= day
                    and oid not in state["financial"]["settlements"]
                ):
                    command(
                        store,
                        pid,
                        "SETTLEMENT_RECORDED",
                        {
                            "operation_id": oid,
                            "session": day,
                            "confirmation_source": "SYNTHETIC_CALENDAR_CONFIRMATION",
                        },
                        "settle-" + oid,
                        day + "T09:00:00-03:00",
                    )
            state = store.load(pid)[0]
            if state["intent"]:
                intent = state["intent"]
                record = state["proposals"][intent["proposal_id"]]
                command(
                    store,
                    pid,
                    "PAPER_ORDER_EXECUTED",
                    {
                        "quote": quote(bundles[day]),
                        "processed_at": day + "T18:10:00-03:00",
                    },
                    "fill-" + day,
                    record["target_open_at"],
                    authorization_ref=intent["authorization_id"],
                )
            command(
                store,
                pid,
                "PORTFOLIO_VALUED",
                {
                    "quote": quote(bundles[day]),
                    "processed_at": day + "T18:10:00-03:00",
                },
                "close-" + day,
                day + "T18:00:00-03:00",
            )
            command(
                store,
                pid,
                "PORTFOLIO_RECONCILED",
                {},
                "reconcile-" + day,
                day + "T18:15:00-03:00",
            )
    for pid in WALLETS:
        state = store.load(pid)[0]
        if pid == WALLETS[1] and i == 0:
            operations = pilot.reference_operations(state)
        elif pid == WALLETS[0] and i == 1:
            operations = [pilot.operation(state, "agents-buy", "PETR4", "BUY", "100")]
        elif pid == WALLETS[0] and i == 4:
            operations = [pilot.operation(state, "agents-sell", "PETR4", "SELL", "40")]
        else:
            operations = []
        prepare(store, pid, day, operations)


def run(root):
    """Returns verified JSON; keeps artifacts so the caller can inspect/restart."""
    pilot.ledger.isolated_path(root / "ledger.sqlite3")
    calendar, bundles = fixture_inputs(root)
    store = pilot.Store.create(root / "ledger.sqlite3")
    for pid, strategy in zip(WALLETS, (pilot.AGENTS, pilot.REFERENCE), strict=True):
        initialize(store, pid, strategy, calendar, bundles[SESSIONS[0]])
    for i, _day in enumerate(SESSIONS[:-1]):
        advance_session(store, bundles, i)
        # Open a fresh connection/replay between sessions; no in-memory authority.
        store = pilot.Store(root / "ledger.sqlite3", writable=True)
    for pid in WALLETS:
        assert store.verify(pid)["ok"], store.verify(pid)
        with (root / (pid + ".json")).open("x", encoding="utf-8") as handle:
            handle.write(pilot.ledger.canonical(store.export(pid)) + "\n")
    result = pilot.projection(store, WALLETS)
    with (root / "projection.json").open("x", encoding="utf-8") as handle:
        handle.write(pilot.ledger.canonical(result) + "\n")
    return result


def main():
    root = Path(tempfile.mkdtemp(prefix="hfl-paper-paper02-"))
    with ExitStack() as stack:
        offline(stack)
        result = run(root)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "directory": str(root),
                "projection": str(root / "projection.json"),
                "wallets": [
                    {
                        "portfolio_id": w["portfolio_id"],
                        "equity": w["summary"]["equity"],
                        "cash": w["summary"]["cash"],
                        "costs": w["summary"]["costs"],
                        "sessions": len(w["history"]),
                        "trades": len(w["trades"]),
                        "base100": w["history"][-1]["base100"],
                    }
                    for w in result["wallets"]
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
