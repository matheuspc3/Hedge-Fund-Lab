"""Separate deterministic forward ledgers; same H2 benchmark factories and settlement.

Only today's last closed session can create an order. No historical backfill.
Initialization at the AI inception is allowed only while its first target open
is still in the future. Otherwise comparison is refused, never synthesized.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_h2_v6_forward as fwd  # noqa: E402

from src.backtesting.arena import MarketObservation  # noqa: E402
from src.experiments.h2_evaluation import (  # noqa: E402
    BENCHMARK_FACTORIES,
    BENCHMARK_SPECS,
    digest,
)

OUTPUT = ROOT / "data/forward/h2_v6_benchmarks"
STRATEGIES = tuple(s.kind for s in BENCHMARK_SPECS if s.kind != "buy_and_hold")


def sync(strategy, root=OUTPUT, forward_root=fwd.OUTPUT, clock=fwd.now):
    if strategy not in STRATEGIES:
        raise ValueError("unknown deterministic strategy")
    at = clock()
    session = fwd.last_closed_session(at)
    deadline = fwd.target_open(session)
    ai = fwd.read(forward_root / "state.json")
    if not ai["sessions"]:
        raise ValueError("AI inception not recorded")
    inception = ai["sessions"][0]["session"]
    folder = forward_root / "sessions" / str(session.date())
    frozen = fwd.read(folder / "input.json")
    bars = fwd.load_bars(folder)
    if (
        frozen["decision_session"] != str(session.date())
        or fwd.sha_file(folder / "bars.csv") != frozen["history"]["sha256"]
        or bars.index[-1] != session
        or frozen["target_open_deadline"] != deadline.isoformat()
    ):
        raise ValueError("frozen forward input/calendar differs")
    if at >= deadline:
        raise ValueError("target opening deadline expired; no order may be created")
    sha, _ = fwd.identity()
    spec = next(s for s in BENCHMARK_SPECS if s.kind == strategy)
    book_root = root / strategy
    book_root.mkdir(parents=True, exist_ok=True)
    with fwd._exclusive_state_lock(book_root / "state.json"):
        path = book_root / "state.json"
        if path.exists():
            state = fwd.read(path)
            if any(state[k] != fwd.new_state(sha)[k] for k in fwd.IDENTITY_KEYS):
                raise ValueError("benchmark ledger treatment drift")
            if (
                state["strategy_sha256"] != digest(spec.to_dict())
                or state["inception"] != inception
            ):
                raise ValueError("benchmark strategy or inception drift")
            if state["mark"]["session"] == str(session.date()):
                return state  # idempotent: do not decide, settle or write twice
            if state["mark"]["session"] > str(session.date()):
                raise ValueError("benchmark clock cannot go backwards")
        else:
            if str(session.date()) != inception or len(ai["sessions"]) != 1:
                raise ValueError(
                    "NOT_COMPARABLE: missed inception; retrospective orders forbidden"
                )
            state = fwd.new_state(sha)
            state.update(
                {
                    "strategy": strategy,
                    "strategy_sha256": digest(spec.to_dict()),
                    "inception": inception,
                    "initialized_at": at.isoformat(),
                    "strategy_target": 0.0,
                }
            )
        previous = state["mark"]["session"] if state["mark"] else None
        rows = fwd.reconcile(state, bars, session)
        participant = BENCHMARK_FACTORIES[strategy](**spec.params)
        # Restore the existing SignalParticipant's target, not a new signal rule.
        if previous:
            participant._last_session = fwd._timestamp(previous)
            participant._target_weight = state["strategy_target"]
        observation = MarketObservation(
            session=session,
            history={fwd.TICKER: bars.loc[:session].copy()},
            positions={fwd.TICKER: state["portfolio"]["units"]},
            cash=state["portfolio"]["cash"],
            equity=rows[-1]["equity"],
        )
        intents = participant.decide(observation)
        fwd._engine(bars)._validate_intents(intents, observation)
        if clock() >= deadline:
            raise ValueError(
                "deadline crossed during deterministic decision; nothing saved"
            )
        state["strategy_target"] = participant._target_weight
        state["pending"] = (
            {
                "decision_session": str(session.date()),
                "target_session": str(deadline.date()),
                "target_weight": intents[0].target_weight,
            }
            if intents
            else None
        )
        rows[-1]["decision"] = "DECIDED"
        state["decisions"].append(
            {
                "session": str(session.date()),
                "target_session": str(deadline.date()),
                "status": "DECIDED",
                "generated_at": clock().isoformat(),
                "target_weight": participant._target_weight,
                "input_sha256": fwd.sha_file(folder / "input.json"),
            }
        )
        fwd.save_state(book_root, state)
        return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strategy", choices=STRATEGIES)
    args = parser.parse_args()
    state = sync(args.strategy)
    print(
        json.dumps(
            {
                "strategy": args.strategy,
                "session": state["mark"]["session"],
                "status": "DECIDED",
            }
        )
    )


if __name__ == "__main__":
    main()
