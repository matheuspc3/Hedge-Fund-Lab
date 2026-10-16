"""Explicit CLI; no paid calls without --authorize-paid and an exact preflight token."""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import multiasset_radar as radar


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("universe", "prepare", "preflight", "run", "replay", "status", "demo"),
    )
    parser.add_argument("--tickers", nargs="*", default=list(radar.EXAMPLES))
    parser.add_argument("--root", type=Path, default=radar.OUTPUT)
    parser.add_argument("--session")
    parser.add_argument("--max-usd", type=float, default=radar.GLOBAL_BUDGET_USD)
    parser.add_argument("--confirm")
    parser.add_argument("--authorize-paid", action="store_true")
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    if args.command == "universe":
        result = radar.configure(args.tickers, args.root)
    elif args.command in ("prepare", "demo"):
        result = radar.prepare(
            args.tickers,
            args.root,
            end=args.session,
            mode="synthetic" if args.synthetic or args.command == "demo" else "live",
        )
        if args.command == "demo":
            radar.configure(args.tickers, args.root)
            report = radar.preflight(args.tickers, args.root, day=args.session)
            result = radar.run(
                args.tickers, report["confirmation_token"], args.root, day=args.session
            )
    elif args.command == "preflight":
        result = radar.preflight(
            args.tickers, args.root, day=args.session, max_usd=args.max_usd
        )
    elif args.command in ("run", "replay"):
        replay = args.command == "replay"
        report = radar.preflight(
            args.tickers, args.root, day=args.session, max_usd=args.max_usd, replay=replay
        )
        result = radar.run(
            args.tickers,
            report["confirmation_token"] if replay else args.confirm,
            args.root,
            day=args.session,
            max_usd=args.max_usd,
            authorize_paid=args.authorize_paid,
            replay=replay,
        )
    else:
        result = radar.status(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, list) and any(
        isinstance(item, dict) and item.get("status") in ("BLOCKED", "FAILED_REPLAY_ONLY")
        for item in result
    ):
        raise SystemExit(1)
    if isinstance(result, dict) and result.get("ready") is False:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
