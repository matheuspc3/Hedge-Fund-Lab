"""Read real replay call banks, including uncertain responses; review missing days.

The original runner is frozen by its manifest. Its report reader expects seals on
Radar's unsealed failure files. This adapter reads the durable banks directly and
reuses the unchanged execute function with a replacement report writer only.
"""

import argparse
import json
import sqlite3
from hashlib import sha256

import replay_multiasset as r
from pilot_paper import bind


def usage_of(item):
    usage = dict(item.get("token_usage") or {})
    # No grounding/tools in this replay. An omitted zero is proved by the total,
    # never inferred from absence alone; an unresolved count remains unknown.
    if (
        usage.get("thoughts_tokens") is None
        and all(
            isinstance(usage.get(k), int)
            for k in ("prompt_tokens", "completion_tokens", "total_tokens")
        )
        and usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
    ):
        usage["thoughts_tokens"] = 0
    keys = ("prompt_tokens", "completion_tokens", "thoughts_tokens", "total_tokens")
    return (
        usage
        if all(isinstance(usage.get(k), int) and usage[k] >= 0 for k in keys)
        and usage["total_tokens"] == sum(usage[k] for k in keys[:3])
        else None
    )


def report(root):
    m, _ = r.load(root)
    records, uncertain, attempts, errors = [], [], 0, []
    for path in sorted(root.glob("sessions/**/calls.sqlite")):
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            attempts += conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            for sequence, raw, raw_sha, text, record_sha in conn.execute(
                "SELECT sequence,raw,raw_sha,record,record_sha FROM calls"
            ):
                if (
                    raw
                    and sha256(raw).hexdigest() != raw_sha
                    or text
                    and sha256(text.encode()).hexdigest() != record_sha
                ):
                    raise ValueError("replay_bank_integrity_failed")
                item = json.loads(text) if text else {}
                if item:
                    records.append(item)
                if item.get("error_type"):
                    errors.append(
                        {
                            "bank": path.relative_to(root).as_posix(),
                            "sequence": sequence,
                            "error_type": item["error_type"],
                        }
                    )
                if not raw or usage_of(item) is None:
                    bound = "0.079872" if path.parent.name == "manager" else "0.055296"
                    uncertain.append(
                        {
                            "bank": path.relative_to(root).as_posix(),
                            "sequence": sequence,
                            "billing_unknown": True,
                            "maximum_cost_at_2026_rates_usd": bound,
                        }
                    )
    usage = [u for x in records if (u := usage_of(x)) is not None]
    keys = ("prompt_tokens", "completion_tokens", "thoughts_tokens", "total_tokens")
    known_tokens = {k: sum(u.get(k, 0) or 0 for u in usage) for k in keys}
    known_cost = (
        r.b.dec(known_tokens["prompt_tokens"]) * r.b.dec("0.75")
        + r.b.dec(known_tokens["completion_tokens"] + known_tokens["thoughts_tokens"])
        * r.b.dec("3.75")
    ) / 1000000
    unknown_bound = sum(
        (r.b.dec(x["maximum_cost_at_2026_rates_usd"]) for x in uncertain), r.b.ZERO
    )
    days = [r.checked(p) for p in sorted(root.glob("sessions/*/day.json"))]
    incomplete = [d["day"] for d in days if d.get("status") == "NO_ANALYSIS"]
    result = {
        "identity": r.IDENTITY,
        "classification": "EXPLORATORY_REAL_INFERENCE_WITH_MISSING_SESSIONS"
        if incomplete
        else "EXPLORATORY_REAL_INFERENCE",
        "manifest_sha256": m["sha256"],
        "created_at": r.radar.now().isoformat(),
        "sessions_valued": len(days),
        "sessions_with_complete_analysis": len(days) - len(incomplete),
        "sessions_without_analysis": incomplete,
        "calls_recorded": len(records),
        "http_attempts": attempts,
        "known_tokens": known_tokens,
        "total_tokens_complete": known_tokens if not uncertain else None,
        "known_usage_estimated_cost_usd_not_invoice": str(known_cost),
        "unknown_billing_attempts": uncertain,
        "estimated_cost_upper_bound_including_unknown_usd": str(
            known_cost + unknown_bound
        ),
        "latency_ms_total": sum(x["duration_ms"] for x in records),
        "resolved_models": sorted(
            {x["resolved_model"] for x in records if x.get("resolved_model")}
        ),
        "errors": errors,
        "days": days,
        "limitations": m["limitations"],
    }
    r.radar.write(root / "report.json", r.b.sealed(result))
    return result


def review(root, day):
    """Record a missing analysis, never a fabricated HOLD or replacement LLM call."""
    m, assets = r.load(root)
    if day not in m["sessions"]:
        raise ValueError("review_session_outside_manifest")
    folder = root / "sessions" / day
    if (folder / "day.json").exists():
        raise ValueError("review_session_already_closed")
    if (folder / "proposal.json").exists() or (folder / "manager").exists():
        raise ValueError("review_cannot_skip_existing_manager_proposal")
    r.checked(folder / "claim.json")
    audit = report(root)
    missing = [
        e for e in audit["errors"] if e["bank"].startswith("sessions/" + day + "/")
    ]
    if not missing or any(e["error_type"] != "ProviderTransportError" for e in missing):
        raise ValueError("review_requires_observed_transport_error")
    r.initialize(root, m, assets)
    before = r.wallets()
    if any(t["economic_date"] >= day for w in before.values() for t in w["trades"]):
        raise ValueError("review_cannot_skip_day_with_existing_operations")
    rows = {
        t: next(x for x in assets[t]["rows"] if x["date"] == day) for t in m["universe"]
    }
    r.dividends.book_received(day)
    r.save(
        folder / "review.json",
        {
            "identity": r.IDENTITY,
            "reviewed_at": r.radar.now().isoformat(),
            "actor": "Codex technical review within Lucas's aggregate authorization",
            "decision": "NO_ANALYSIS_NO_OPERATIONS_CONTINUE_NEXT_SESSION",
            "reason": "Remote connection reset; incomplete quorum; uncertain request is not repeated",
            "errors": missing,
            "report_adapter_sha256": r.b.sha_file(__file__),
            "replacement_inference": False,
        },
    )
    r.save(
        folder / "day.json",
        {
            "identity": r.IDENTITY,
            "day": day,
            "reference": m["references"][day],
            "offline": False,
            "status": "NO_ANALYSIS",
            "created_at": r.radar.now().isoformat(),
            "context_sha256": None,
            "before": {
                k: {
                    "cash": w["cash"],
                    "revision": w["revision"],
                    "positions": w["positions"],
                }
                for k, w in before.items()
            },
            "operations": [],
            "execution_source": {
                "status": "NOT_EXECUTED",
                "reason": "INCOMPLETE_COMMITTEE_TRANSPORT_ERROR",
            },
            "valuation": {k: r.valuation(w, rows, day) for k, w in r.wallets().items()},
        },
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("report", "review-and-resume"))
    p.add_argument("--id", required=True)
    p.add_argument("--day")
    args = p.parse_args()
    root = r.root_of(args.id)
    if args.command == "review-and-resume":
        authorization = r.checked(root / "authorization.json")
        m, assets = r.load(root)
        cap = authorization["max_aggregate_usd"]
        if (
            authorization["manifest_sha256"] != m["sha256"]
            or not r.preflight(root, cap)["ready"]
        ):
            raise ValueError("review_authorization_or_preflight_invalid")
        with r.radar._exclusive_state_lock(root / "operation"):
            review(root, args.day)
            execute = bind(r.execute, write_report=report)
            try:
                execute(root, m, assets, max_usd=cap)
            finally:
                report(root)
    else:
        value = report(root)
        print(
            json.dumps(
                {k: v for k, v in value.items() if k not in ("days", "limitations")},
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
