"""DP-35: the chosen 20 Apr-5 May stress window, using the frozen first runner.

Only preparation dates and the already-qualified report writer are adapted.
Prompts, opinions, manager, risk, execution, accounting and costs stay unchanged.
"""

import argparse
import json
import os
from pathlib import Path

import replay_multiasset as r
import report_multiasset_replay as reports
from pilot_paper import bind

START, END = "2026-04-20", "2026-05-05"
CAP = r.b.dec("34.78")
ADAPTER = Path(__file__).resolve()


def prepare(root, source):
    def window_sessions(start=START, end=END):
        return r.sessions(start, end)

    def save(path, value):
        if path.name == "manifest.json":
            value = {
                **value,
                "experiment_id": root.name,
                "window": {"start": START, "end": END},
                "window_adapter_sha256": r.b.sha_file(ADAPTER),
                "selection": "EX_POST_DOWNSIDE_STRESS_WINDOW_CHOSEN_BY_LUCAS_2026_11_13",
                "limitations": [
                    *value["limitations"],
                    "Janela escolhida pela queda observada; não é teste incondicional de retorno ou superioridade.",
                ],
            }
        r.save(path, value)

    # ponytail: reuse the existing private namespace bridge; changing the frozen
    # first runner would invalidate its paid-call manifests. Only dates differ.
    bind(r.prepare, sessions=window_sessions, END=END, save=save)(root, source)
    return checked(root)


def checked(root):
    m, assets = r.load(root)
    if (
        m.get("experiment_id") != root.name
        or m.get("window") != {"start": START, "end": END}
        or m.get("window_adapter_sha256") != r.b.sha_file(ADAPTER)
        or m["sessions"] != r.sessions(START, END)
        or len(m["sessions"]) != 10
    ):
        raise ValueError("stress_window_adapter_or_identity_changed")
    return m, assets


def preflight(root, cap):
    checked(root)
    if cap is not None and not r.b.ZERO < r.b.dec(cap) <= CAP:
        raise ValueError("stress_window_cap_must_not_exceed_34_78")
    return r.preflight(root, cap)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command",
        choices=(
            "prepare",
            "preflight",
            "offline",
            "live",
            "report",
            "review-and-resume",
        ),
    )
    p.add_argument("--id", required=True)
    p.add_argument("--source-platform", type=Path)
    p.add_argument("--max-usd")
    p.add_argument("--confirm")
    p.add_argument("--day")
    p.add_argument("--only", type=int, choices=range(1, 11))
    args = p.parse_args()
    root = r.root_of(args.id)
    if args.command == "prepare":
        if args.source_platform is None:
            p.error("--source-platform required")
        prepare(root, args.source_platform.resolve())
    m, assets = checked(root)
    if args.command in ("prepare", "preflight"):
        value = preflight(root, args.max_usd)
        r.radar.write(root / "preflight.json", r.b.sealed(value))
        print(json.dumps(value, indent=2))
    elif args.command == "report":
        value = reports.report(root)
        print(
            json.dumps(
                {k: v for k, v in value.items() if k not in ("days", "limitations")},
                indent=2,
            )
        )
    else:
        offline = args.command == "offline"
        if not offline:
            authorization = r.checked(root / "authorization.json")
            value = preflight(root, authorization["max_aggregate_usd"])
            if not value["ready"] or authorization["manifest_sha256"] != m["sha256"]:
                raise ValueError("stress_authorization_or_preflight_invalid")
            if args.command == "live" and (
                args.max_usd != authorization["max_aggregate_usd"]
                or args.confirm != value["confirmation_token"]
            ):
                raise ValueError("stress_current_preflight_token_required")
        with r.radar._exclusive_state_lock(root / "operation"):
            if offline:
                os.environ["GEMINI_API_KEY"] = "OFFLINE_TEST_NO_SECRET"
                with r.no_network():
                    r.execute(root, m, assets, offline=True, only=args.only)
            else:
                if args.command == "review-and-resume":
                    reports.review(root, args.day)
                execute = bind(r.execute, write_report=reports.report)
                try:
                    execute(
                        root,
                        m,
                        assets,
                        max_usd=authorization["max_aggregate_usd"],
                        only=args.only,
                    )
                finally:
                    reports.report(root)


if __name__ == "__main__":
    main()
