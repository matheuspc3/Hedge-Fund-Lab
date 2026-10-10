"""Hardening dirigido ao defeito do H2 v3 (Amendment 10).

Estados: as 10 âncoras CAL-B2 (consumidas, agora development), histórico até
close(t), carteira zerada. Config: final v2 (21 / 0.40 / 0.15) + Risk prompt v2.
R = 3. Technical = replay EXATO das respostas CAL-B2 seladas (nenhuma chamada
Technical nova: requisição sem par v2 falha fechada); Risk v2 live quando
alcançado; Portfolio replay por identidade exata, senão live. Nenhum retorno,
nenhum preço t+1. Gates: V3-R1, V3-R2, V3-R3, V3-S, V3-D.

Exige CAL-B3 já comprometida (Amendment 10: antes de qualquer chamada v3).

Uso: ``python scripts/run_h2_v3_defect.py``.
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

from h2_v3 import (  # noqa: E402
    CHECKER_FILES,
    FrozenReplayClient,
    frozen_index,
    git_blob,
    replay_audit,
    risk_audit,
)
from run_cal_b import history_until, load_frame  # noqa: E402
from run_h2_hardening import AttemptLog, git, load_key  # noqa: E402

from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2_SHA256  # noqa: E402
from src.agents.llm_client import GeminiLLMClient, RetryingLLMClient  # noqa: E402
from src.agents.llm_trace import STAGE_TECHNICAL_ANALYST, load_trace  # noqa: E402
from src.agents.participant import LLMParticipant  # noqa: E402
from src.agents.risk_contract import (  # noqa: E402
    RISK_SYSTEM_PROMPT_V2_SHA256,
    audit_risk_rationale,
)
from src.artifacts import canonical_json  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.anchors import CAL_B2_ANCHORS  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FREEZE_V1_GATES,
    HardeningAbortedError,
    HardeningState,
    diagnostic_metrics,
    run_hardening,
)

OUT_ROOT = ROOT / "docs" / "evidence" / "h2_v3"
CAL_B2_RUN = ROOT / treatment.FROZEN_V2_EVIDENCE["defect"]
TARGET = "2023-06-26"
#: Regras de Risk/Portfolio que denunciam resposta inválida ou fallback.
STRUCTURAL_RULES = {"INVALID_RESPONSE", "DIRECTION_INVERSION"}


def main() -> None:
    if git("status", "--porcelain", "--untracked-files=no"):
        sys.exit("working tree has tracked changes: commit before a scientific run")
    try:
        treatment.require_cal_b3_committed()
    except ValueError as exc:
        sys.exit(str(exc))
    commit = git("rev-parse", "HEAD")
    params = {k: v for k, v in treatment.H2_V3_DEFECT_PARAMS.items() if k != "ticker"}
    ticker = treatment.H2_V3_DEFECT_PARAMS["ticker"]
    capability = LLMParticipant.preflight({"ticker": ticker, **params}, scientific=True)
    _, frame = load_frame()
    states = [HardeningState(f"cal-b2:{a}", ticker, history_until(frame, a)) for a in CAL_B2_ANCHORS]
    assert not set(CAL_B2_ANCHORS) & set(anchors.CAL_B3_ANCHORS)
    frozen = {a: frozen_index([CAL_B2_RUN / "anchors" / a / "llm_calls.jsonl"]) for a in CAL_B2_ANCHORS}
    order = [(a, r) for a in CAL_B2_ANCHORS for r in range(treatment.H2_V3_DEFECT_REPETITIONS)]
    load_key()
    log = AttemptLog(timeout=120.0)
    uses: list[dict[str, Any]] = []
    started = datetime.now(timezone.utc)

    counter = {"n": 0}

    def factory(name: str) -> LLMParticipant:
        anchor, rep = order[counter["n"]]  # run_hardening: estados por fora, repetições por dentro
        counter["n"] += 1
        print(f"treatment {counter['n']}/{len(order)} ({anchor} r{rep})", flush=True)
        live = RetryingLLMClient(GeminiLLMClient(model=params["model"], transport=log),
                                 max_attempts=params["retry_attempts"], base_delay=params["retry_base_delay"])
        client = FrozenReplayClient(live, frozen[anchor], provider=params["provider"], model=params["model"],
                                    uses=uses, context={"anchor": anchor, "repetition": rep},
                                    required=frozenset({STAGE_TECHNICAL_ANALYST}))
        return LLMParticipant(name, llm_client=client, **params)

    aborted = None
    try:
        outcomes = run_hardening(states, factory, repetitions=treatment.H2_V3_DEFECT_REPETITIONS)
    except HardeningAbortedError as exc:
        aborted, outcomes = exc, exc.outcomes
    finished = datetime.now(timezone.utc)
    out = OUT_ROOT / f"defect_hardening_{started.strftime('%Y%m%dT%H%M%SZ')}"
    (out / "traces").mkdir(parents=True, exist_ok=True)
    decisions, records, pairs = [], [], []
    for outcome in outcomes:
        name = f"{outcome.state_id.replace(':', '_')}__r{outcome.repetition}"
        (out / "traces" / f"{name}.jsonl").write_bytes(outcome.trace.content)
        trace = load_trace(outcome.trace.content)
        records.extend(trace)
        pairs.extend((r, frozen[outcome.state_id.split(":", 1)[1]]) for r in trace)
        decisions.append({"state_id": outcome.state_id, "repetition": outcome.repetition, "error": outcome.error,
                          "reason": outcome.reason, "trace_file": f"traces/{name}.jsonl",
                          "decision": None if outcome.record is None else outcome.record.to_json_dict(ticker)})
    for name, rows in (("decisions", decisions), ("attempts", log.attempts), ("replay_uses", uses)):
        (out / f"{name}.jsonl").write_text("".join(canonical_json(d) + "\n" for d in rows), encoding="utf-8",
                                           newline="\n")
    metrics = diagnostic_metrics(outcomes)
    audit = risk_audit(records)
    replay = replay_audit(pairs)
    truncations = sum(r.finish_reason in ("MAX_TOKENS", "length") for r in records)
    final_errors = sum(r.status == "error" for r in records)
    structural = [d["decision"] for d in decisions if d["decision"] and (
        d["decision"].get("risk_rule") in STRUCTURAL_RULES or d["decision"].get("portfolio_rule") in STRUCTURAL_RULES)]
    complete = aborted is None and len(outcomes) == len(order)
    s_ok = (complete and metrics["failure_count"] == 0 and truncations == 0 and final_errors == 0 and not structural
            and not replay["mismatch"] and replay["technical_prompt_v2_byte_identical"] and audit["risk_prompt_v2_only"])
    gates = {
        "V3-R1": {"value": audit["V3-R1"], "threshold": "== 0", "pass": audit["V3-R1"] == 0},
        "V3-R2": {"value": audit["V3-R2"], "threshold": "== 0", "pass": audit["V3-R2"] == 0},
        "V3-R3": {"value": audit["V3-R3"], "threshold": "== 0", "pass": audit["V3-R3"] == 0},
        "V3-S": {"value": {"failures": metrics["failure_count"], "truncations": truncations,
                           "final_provider_errors": final_errors, "invalid_or_inversion": len(structural),
                           "replay_mismatches": replay["mismatch"], "complete": complete}, "pass": s_ok},
        "V3-D": {"value": metrics["total_hold_rate"], "threshold": f"< {H2_FREEZE_V1_GATES.max_total_hold_rate}",
                 "pass": metrics["total_hold_rate"] is not None
                 and metrics["total_hold_rate"] < H2_FREEZE_V1_GATES.max_total_hold_rate},
    }
    if not gates["V3-S"]["pass"]:
        status = treatment.H2_V3_TECHNICAL_FAILURE
    elif not (gates["V3-R1"]["pass"] and gates["V3-R2"]["pass"] and gates["V3-R3"]["pass"]):
        status = treatment.H2_V3_RISK_FIX_FAILED
    elif not gates["V3-D"]["pass"]:
        status = treatment.H2_V3_DEGENERACY_PERSISTS
    else:
        status = treatment.H2_V3_DEFECT_FIX_PASSED

    v2_records = [r for a in CAL_B2_ANCHORS for r in load_trace((CAL_B2_RUN / "anchors" / a / "llm_calls.jsonl")
                                                                 .read_bytes())]
    target_v2 = next(r for r in v2_records if r.request.stage == "risk_manager" and r.request.decision_session == TARGET)
    target_v3 = [r for r in records if r.request.stage == "risk_manager" and r.request.decision_session == TARGET]
    target = {
        "anchor": TARGET,
        "risk_payload": json.loads(target_v2.request.user_prompt),
        "same_logical_payload_in_all_v3_calls": all(r.request.user_prompt == target_v2.request.user_prompt
                                                    for r in target_v3),
        "v2_risk_prompt_v1": {"verdict": target_v2.validated_response["verdict"],
                              "analysis": target_v2.validated_response["analysis"],
                              "findings": audit_risk_rationale(target_v2.validated_response["analysis"],
                                                               target_v2.validated_response["verdict"],
                                                               json.loads(target_v2.request.user_prompt))},
        "v3_risk_prompt_v2": [{"call_id": r.call_id, "verdict": r.validated_response["verdict"],
                               "analysis": r.validated_response["analysis"],
                               "findings": audit_risk_rationale(r.validated_response["analysis"],
                                                                r.validated_response["verdict"],
                                                                json.loads(r.request.user_prompt))}
                              for r in target_v3],
    }
    usage: Counter = Counter()  # replay não grava usage: o total é só do que foi live
    for r in records:
        for k, v in (r.token_usage or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                usage[k] += v
    manifest = {
        "kind": "H2_V3_DEFECT_DIRECTED_HARDENING", "treatment_version": treatment.H2_TREATMENT_VERSION,
        "technical_prompt_version": treatment.SCIENTIFIC_TECHNICAL_PROMPT_VERSION,
        "technical_prompt_sha256": TECHNICAL_SYSTEM_PROMPT_V2_SHA256,
        "risk_prompt_version": treatment.SCIENTIFIC_RISK_PROMPT_VERSION,
        "risk_prompt_sha256": RISK_SYSTEM_PROMPT_V2_SHA256,
        "frozen_component_replay": treatment.FROZEN_COMPONENT_REPLAY,
        "frozen_v2_evidence": treatment.FROZEN_V2_EVIDENCE["defect"],
        "checker_blobs": {path: git_blob(path) for path in CHECKER_FILES},
        "financial_metrics": "none computed (no settlement, no t+1)",
        "started_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "finished_utc": finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": commit, "participant_params": {"ticker": ticker, **params},
        "capability": {"status": capability.status, "qualified": list(capability.qualified)},
        "states": [s.state_id for s in states], "repetitions": treatment.H2_V3_DEFECT_REPETITIONS,
        "cal_b3_commitment": anchors.CAL_B3_COMMITMENT_SHA256,
        "aborted": None if aborted is None else str(aborted),
        "diagnostics": metrics, "risk_audit": audit, "replay_audit": replay, "truncations": truncations,
        "gates": gates, "status": status, "target_case": target,
        "v2_consumed_cal_b2_risk_audit_REFERENCE": risk_audit(v2_records),
        "operational": {
            "logical_calls": len(records), "logical_calls_by_stage": dict(Counter(r.request.stage for r in records)),
            "calls_by_stage_and_source": {f"{s}/{src}": n for (s, src), n in
                                          sorted(Counter((u["stage"], u["source"]) for u in uses).items())},
            "http_attempts": len(log.attempts), "attempt_outcomes": dict(Counter(a["outcome"] for a in log.attempts)),
            "recovered_retries": sum(r.attempt_count - 1 for r in records if r.status == "ok"),
            "live_token_usage": dict(usage),
            "resolved_models": dict(Counter(r.resolved_model for r in records)),
            "wall_clock_seconds": round((finished - started).total_seconds(), 1),
            "cost": "not computed: no pricing source is recorded in the repository",
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
                                       encoding="utf-8", newline="\n")
    print(out.as_posix())
    print(json.dumps({"gates": gates, "status": status, "target_case": target}, indent=1, ensure_ascii=False,
                     default=str))


if __name__ == "__main__":
    main()
