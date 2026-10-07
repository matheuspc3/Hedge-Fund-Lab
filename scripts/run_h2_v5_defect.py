"""CAL-B3 consumed anchors x R=3, N=5 LIVE Technical v4; no t+1 settlement."""

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from h2_v5 import require_pre_live_freeze, require_sessions, technical_audit  # noqa: E402
from h2_v4 import technical_audit as historical_audit  # noqa: E402
from run_cal_b import history_until, load_frame  # noqa: E402
from run_h2_hardening import AttemptLog, git, load_key  # noqa: E402

from src.agents.technical_prompt_v4 import TECHNICAL_SYSTEM_PROMPT_V4_SHA256  # noqa: E402
from src.agents.llm_client import GeminiLLMClient, RetryingLLMClient  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.agents.participant import LLMParticipant  # noqa: E402
from src.agents.risk_contract import RISK_SYSTEM_PROMPT_V2_SHA256  # noqa: E402
from src.artifacts import canonical_json  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.cal_b import CAL_B3_EVIDENCE  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FREEZE_V1_GATES,
    HardeningAbortedError,
    HardeningState,
    diagnostic_metrics,
    run_hardening,
)
from src.experiments.spec import ParticipantSpec  # noqa: E402

TARGETS = ("2020-05-13", "2022-03-11")


def main():
    if git("status", "--porcelain"):
        sys.exit("working tree must be clean before a scientific run")
    freeze = require_pre_live_freeze()
    params = dict(treatment.H2_V5_DEFECT_PARAMS)
    ticker = params.pop("ticker")
    capability = LLMParticipant.preflight({"ticker": ticker, **params}, scientific=True)
    require_sessions(anchors.CAL_B3_ANCHORS)
    _, frame = load_frame()
    states = [HardeningState(f"cal-b3:{a}", ticker, history_until(frame, a)) for a in anchors.CAL_B3_ANCHORS]
    assert not set(anchors.CAL_B3_ANCHORS) & set(anchors.CAL_B4_ANCHORS)
    assert all(str(s.history.index[-1].date()) <= "2024-08-30" for s in states)
    load_key()
    log = AttemptLog(timeout=120.0)
    started = datetime.now(timezone.utc)
    counter = 0
    total = len(states) * treatment.H2_V5_DEFECT_REPETITIONS

    def factory(name):
        nonlocal counter
        anchor = anchors.CAL_B3_ANCHORS[counter // treatment.H2_V5_DEFECT_REPETITIONS]
        rep = counter % treatment.H2_V5_DEFECT_REPETITIONS
        counter += 1
        print(f"treatment {counter}/{total} ({anchor} r{rep})", flush=True)
        live = RetryingLLMClient(GeminiLLMClient(model=params["model"], transport=log),
                                 max_attempts=params["retry_attempts"], base_delay=params["retry_base_delay"])
        return LLMParticipant(name, llm_client=live, **params)

    aborted = None
    try:
        outcomes = run_hardening(states, factory, repetitions=treatment.H2_V5_DEFECT_REPETITIONS)
    except HardeningAbortedError as exc:
        aborted, outcomes = exc, exc.outcomes
    finished = datetime.now(timezone.utc)
    out = ROOT / "docs/evidence/h2_v5" / f"defect_hardening_{started.strftime('%Y%m%dT%H%M%SZ')}"
    (out / "traces").mkdir(parents=True)
    decisions, records = [], []
    for o in outcomes:
        name = f"{o.state_id.replace(':', '_')}__r{o.repetition}.jsonl"
        (out / "traces" / name).write_bytes(o.trace.content)
        records.extend(load_trace(o.trace.content))
        decisions.append({"state_id": o.state_id, "repetition": o.repetition, "error": o.error,
                          "reason": o.reason, "trace_file": f"traces/{name}",
                          "decision": None if o.record is None else o.record.to_json_dict(ticker)})
    for name, rows in (("decisions", decisions), ("attempts", log.attempts)):
        (out / f"{name}.jsonl").write_text("".join(canonical_json(r) + "\n" for r in rows), encoding="utf-8")
    metrics, audit = diagnostic_metrics(outcomes), technical_audit(records)
    complete = aborted is None and len(outcomes) == total and audit["technical_votes"] == total * 5
    final_errors = sum(r.status == "error" for r in records)
    truncations = sum(r.finish_reason in ("MAX_TOKENS", "length") for r in records)
    structural = sum(d["decision"] is not None and any(d["decision"].get(k) in {
        "INVALID_RESPONSE", "DIRECTION_INVERSION"} for k in ("risk_rule", "portfolio_rule")) for d in decisions)
    gates = {g: {"value": audit[g], "threshold": "== 0", "pass": audit[g] == 0} for g in ("V5-S1", "V5-S2", "V5-S3")}
    failures = metrics["failure_count"] + final_errors + structural
    gates.update({"V5-A": {"value": failures, "threshold": "== 0", "pass": complete and failures == 0},
                  "V5-T": {"value": truncations, "threshold": "== 0", "pass": truncations == 0},
                  "V5-D": {"value": metrics["total_hold_rate"], "threshold": "< 0.90",
                           "pass": metrics["total_hold_rate"] is not None
                           and metrics["total_hold_rate"] < H2_FREEZE_V1_GATES.max_total_hold_rate}})
    if not all(gates[g]["pass"] for g in ("V5-S1", "V5-S2", "V5-S3")):
        status = treatment.H2_V5_TEMPORAL_FIX_FAILED
    elif not (gates["V5-A"]["pass"] and gates["V5-T"]["pass"]):
        status = "H2_V5_DEFECT_HARDENING TECHNICAL FAILURE"
    elif not gates["V5-D"]["pass"]:
        status = treatment.H2_V5_DEGENERACY_PERSISTS
    else:
        status = treatment.H2_V5_DEFECT_FIX_PASSED
    prior = [r for a in anchors.CAL_B3_ANCHORS for r in load_trace(
        (ROOT / CAL_B3_EVIDENCE / "anchors" / a / "llm_calls.jsonl").read_bytes())]
    targets = {a: {"v3_consumed": historical_audit(r for r in prior if r.request.decision_session == a),
                   "v5_live": technical_audit(r for r in records if r.request.decision_session == a),
                   "v5_decisions": [d for d in decisions if d["state_id"] == f"cal-b3:{a}"]} for a in TARGETS}
    manifest = {"kind": "H2_V5_DEFECT_DIRECTED_HARDENING", "treatment_version": 5,
                "technical_prompt_version": 4, "risk_prompt_version": 2, "feature_schema_version": 2,
                "technical_prompt_sha256": TECHNICAL_SYSTEM_PROMPT_V4_SHA256,
                "risk_prompt_sha256": RISK_SYSTEM_PROMPT_V2_SHA256, "checker_freeze": freeze,
                "participant_params": {"ticker": ticker, **params},
                "participant_spec_sha256": hashlib.sha256(canonical_json(ParticipantSpec(
                    "llm_agent", {"ticker": ticker, **params}).to_dict()).encode()).hexdigest(),
                "git_commit": git("rev-parse", "HEAD"), "cal_b4_commitment": anchors.CAL_B4_COMMITMENT_SHA256,
                "started_utc": started.isoformat(), "finished_utc": finished.isoformat(),
                "financial_metrics": "none computed (no settlement, no t+1)", "states": [s.state_id for s in states],
                "repetitions": 3, "complete": complete, "aborted": None if aborted is None else str(aborted),
                "capability": {"status": capability.status, "qualified": list(capability.qualified)},
                "diagnostics": metrics, "technical_audit": audit, "gates": gates, "status": status,
                "v3_consumed_reference_DESCRIPTIVE": historical_audit(prior), "target_anchors": targets,
                "operational": {"logical_calls": len(records), "http_attempts": len(log.attempts),
                                "logical_calls_by_stage": dict(Counter(r.request.stage for r in records)),
                                "attempt_outcomes": dict(Counter(a["outcome"] for a in log.attempts)),
                                "wall_clock_seconds": (finished - started).total_seconds()}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out.as_posix())
    print(json.dumps({"status": status, "gates": gates}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
