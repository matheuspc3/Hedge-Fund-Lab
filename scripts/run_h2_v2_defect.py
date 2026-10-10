"""Hardening dirigido ao defeito do H2 v2 (Amendment 8).

Estados: as 10 âncoras CAL-B1 (consumidas, agora development), histórico até
close(t), carteira zerada. Config: a final de desenvolvimento v1 + prompt técnico
v2. R = 3, N = 5 (150 chamadas técnicas); Risk/Portfolio seguem o grafo. Nenhum
retorno, nenhum preço t+1. Gates: V2-S1 (contradições semânticas), V2-S2
(transições não suportadas), V2-A, V2-T, V2-D (total_hold_rate < 0.90).

Exige CAL-B2 já comprometida (Amendment 8: antes de qualquer chamada v2).

Uso: ``python scripts/run_h2_v2_defect.py``.
"""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_cal_b import history_until, load_frame  # noqa: E402
from run_h2_hardening import AttemptLog, git, load_key  # noqa: E402

from src.agents.feature_semantics import (  # noqa: E402
    TECHNICAL_SYSTEM_PROMPT_V2_SHA256,
    audit_rationale,
    contradictions,
    transitions,
)
from src.agents.llm_client import GeminiLLMClient, RetryingLLMClient  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.agents.participant import LLMParticipant  # noqa: E402
from src.artifacts import canonical_json  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.anchors import CAL_B_ANCHORS  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FREEZE_V1_GATES,
    HardeningAbortedError,
    HardeningState,
    diagnostic_metrics,
    run_hardening,
)

OUT_ROOT = ROOT / "docs" / "evidence" / "h2_v2"
CAL_B1_RUN = ROOT / "docs" / "evidence" / "cal_b" / "run_20261005T021523Z"


def semantic_audit(records: list[Any]) -> dict[str, Any]:
    """Checker sobre o rationale visível de cada voto técnico (sem hidden reasoning)."""
    votes, flagged = 0, []
    c_votes = t_votes = 0
    for r in records:
        if r.request.stage != "technical_analyst" or r.status != "ok":
            continue
        features = json.loads(r.request.user_prompt.splitlines()[0][len("Features: "):])
        audit = audit_rationale(r.validated_response["justification"], features)
        c, t = contradictions(audit), transitions(audit)
        votes += 1
        c_votes += bool(c)
        t_votes += bool(t)
        if c or t:
            flagged.append({"call_id": r.call_id, "signal": r.validated_response["signal"],
                            "justification": r.validated_response["justification"],
                            "contradictions": c, "transitions": t})
    return {"technical_votes": votes, "votes_with_contradiction": c_votes, "votes_with_transition": t_votes,
            "contradiction_rate": c_votes / votes if votes else None,
            "transition_rate": t_votes / votes if votes else None, "flagged": flagged}


def v1_cal_b1_reference() -> dict[str, Any]:
    """Mesmo checker sobre os 50 votos v1 da CAL-B1 (descritivo)."""
    records = [r for a in CAL_B_ANCHORS for r in load_trace((CAL_B1_RUN / "anchors" / a / "llm_calls.jsonl").read_bytes())]
    audit = semantic_audit(records)
    causes = Counter(json.loads((CAL_B1_RUN / "anchors" / a / "decisions.jsonl").read_text(encoding="utf-8")
                                .splitlines()[0])["final_cause"] for a in CAL_B_ANCHORS)
    holds = causes["TECH_EXPLICIT_HOLD"] + causes["TECH_NO_MAJORITY"] + causes["PORTFOLIO_HOLD"] + sum(
        n for c, n in causes.items() if c.startswith("RISK_VETO"))
    return {**{k: v for k, v in audit.items() if k != "flagged"}, "total_hold_rate": holds / len(CAL_B_ANCHORS),
            "tech_explicit_hold_rate": causes["TECH_EXPLICIT_HOLD"] / len(CAL_B_ANCHORS)}


def main() -> None:
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("working tree has tracked changes: commit before a scientific run")
    if not anchors.CAL_B2_ANCHORS or anchors.digest(anchors.CAL_B2_ANCHORS) != anchors.CAL_B2_COMMITMENT_SHA256:
        sys.exit("CAL-B2 must be committed before any H2 v2 live call")
    commit = git("rev-parse", "HEAD")
    params = {k: v for k, v in treatment.H2_V2_DEFECT_PARAMS.items() if k != "ticker"}
    ticker = treatment.H2_V2_DEFECT_PARAMS["ticker"]
    capability = LLMParticipant.preflight({"ticker": ticker, **params}, scientific=True)
    _, frame = load_frame()
    states = [HardeningState(f"cal-b1:{a}", ticker, history_until(frame, a)) for a in CAL_B_ANCHORS]
    assert not {a for a in CAL_B_ANCHORS} & set(anchors.CAL_B2_ANCHORS)
    load_key()
    log = AttemptLog(timeout=120.0)
    started = datetime.now(timezone.utc)
    counter = {"n": 0}
    total = len(states) * treatment.H2_V2_DEFECT_REPETITIONS

    def factory(name: str) -> LLMParticipant:
        counter["n"] += 1
        print(f"treatment {counter['n']}/{total}", flush=True)
        client = RetryingLLMClient(GeminiLLMClient(model=params["model"], transport=log),
                                   max_attempts=params["retry_attempts"], base_delay=params["retry_base_delay"])
        return LLMParticipant(name, llm_client=client, **params)

    aborted = None
    try:
        outcomes = run_hardening(states, factory, repetitions=treatment.H2_V2_DEFECT_REPETITIONS)
    except HardeningAbortedError as exc:
        aborted, outcomes = exc, exc.outcomes
    finished = datetime.now(timezone.utc)
    out = OUT_ROOT / f"defect_hardening_{started.strftime('%Y%m%dT%H%M%SZ')}"
    (out / "traces").mkdir(parents=True, exist_ok=True)
    decisions, records = [], []
    for outcome in outcomes:
        name = f"{outcome.state_id.replace(':', '_')}__r{outcome.repetition}"
        (out / "traces" / f"{name}.jsonl").write_bytes(outcome.trace.content)
        records.extend(load_trace(outcome.trace.content))
        decisions.append({"state_id": outcome.state_id, "repetition": outcome.repetition, "error": outcome.error,
                          "reason": outcome.reason, "trace_file": f"traces/{name}.jsonl",
                          "decision": None if outcome.record is None else outcome.record.to_json_dict(ticker)})
    (out / "decisions.jsonl").write_text("".join(canonical_json(d) + "\n" for d in decisions), encoding="utf-8",
                                         newline="\n")
    (out / "attempts.jsonl").write_text("".join(canonical_json(a) + "\n" for a in log.attempts), encoding="utf-8",
                                        newline="\n")
    metrics = diagnostic_metrics(outcomes)
    audit = semantic_audit(records)
    truncations = sum(r.finish_reason in ("MAX_TOKENS", "length") for r in records)
    complete = aborted is None and len(outcomes) == total
    gates = {
        "V2-S1": {"value": audit["votes_with_contradiction"], "threshold": "== 0",
                  "pass": audit["votes_with_contradiction"] == 0},
        "V2-S2": {"value": audit["votes_with_transition"], "threshold": "== 0",
                  "pass": audit["votes_with_transition"] == 0},
        "V2-A": {"value": metrics["failure_count"], "threshold": "== 0",
                 "pass": metrics["failure_count"] == 0 and complete},
        "V2-T": {"value": truncations, "threshold": "== 0", "pass": truncations == 0},
        "V2-D": {"value": metrics["total_hold_rate"], "threshold": f"< {H2_FREEZE_V1_GATES.max_total_hold_rate}",
                 "pass": metrics["total_hold_rate"] is not None
                 and metrics["total_hold_rate"] < H2_FREEZE_V1_GATES.max_total_hold_rate},
    }
    if not (gates["V2-A"]["pass"] and gates["V2-T"]["pass"]):
        status = "H2_V2_DEFECT_HARDENING TECHNICAL FAILURE"
    elif not (gates["V2-S1"]["pass"] and gates["V2-S2"]["pass"]):
        status = treatment.H2_V2_SEMANTIC_FIX_FAILED
    elif not gates["V2-D"]["pass"]:
        status = treatment.H2_V2_DEGENERACY_PERSISTS
    else:
        status = treatment.H2_V2_DEFECT_FIX_PASSED
    usage: Counter = Counter()
    for r in records:
        for k, v in (r.token_usage or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                usage[k] += v
    manifest = {
        "kind": "H2_V2_DEFECT_DIRECTED_HARDENING", "treatment_version": treatment.H2_TREATMENT_VERSION,
        "technical_prompt_version": treatment.SCIENTIFIC_TECHNICAL_PROMPT_VERSION,
        "technical_prompt_sha256": TECHNICAL_SYSTEM_PROMPT_V2_SHA256,
        "financial_metrics": "none computed (no settlement, no t+1)",
        "started_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "finished_utc": finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": commit, "participant_params": {"ticker": ticker, **params},
        "capability": {"status": capability.status, "qualified": list(capability.qualified)},
        "states": [s.state_id for s in states], "repetitions": treatment.H2_V2_DEFECT_REPETITIONS,
        "cal_b2_commitment": anchors.CAL_B2_COMMITMENT_SHA256,
        "aborted": None if aborted is None else str(aborted),
        "diagnostics": metrics, "semantic_audit": audit, "truncations": truncations, "gates": gates,
        "status": status,
        "v1_cal_b1_reference_DESCRIPTIVE": v1_cal_b1_reference(),
        "operational": {
            "logical_calls": len(records), "logical_calls_by_stage": dict(Counter(r.request.stage for r in records)),
            "http_attempts": len(log.attempts), "attempt_outcomes": dict(Counter(a["outcome"] for a in log.attempts)),
            "recovered_retries": sum(r.attempt_count - 1 for r in records if r.status == "ok"),
            "token_usage_totals": dict(usage), "resolved_models": dict(Counter(r.resolved_model for r in records)),
            "wall_clock_seconds": round((finished - started).total_seconds(), 1),
            "cost": "not computed: no pricing source is recorded in the repository",
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
                                       encoding="utf-8", newline="\n")
    print(out.as_posix())
    print(json.dumps({"gates": gates, "status": status,
                      "v1_reference": manifest["v1_cal_b1_reference_DESCRIPTIVE"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
