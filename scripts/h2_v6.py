"""V6 governance and structured audits; no holdout payload is constructed."""

import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import h2_v4
from select_cal_b4 import used_sessions
from src.agents.technical_evidence import render_technical_evidence
from src.agents.technical_prompt_v5 import TECHNICAL_SYSTEM_PROMPT_V5_SHA256
from src.experiments import anchors, treatment

AUDIT = "docs/evidence/h2_v6/pre_live_audit.json"
AUTHORIZATION = "docs/evidence/h2_v6/execution_authorization.json"
SOURCE_FILES = (
    "src/agents/technical_evidence.py", "src/agents/technical_prompt_v5.py",
    "src/agents/technical_analyst.py", "src/agents/state.py", "src/agents/participant.py",
    "src/agents/llm_trace.py", "src/agents/llm_client.py", "src/experiments/treatment.py",
    "scripts/h2_v6.py", "scripts/run_h2_v6_defect.py", "scripts/run_h2_hardening.py",
    "scripts/run_cal_a.py", "scripts/run_sequential_dev.py", "scripts/run_stress.py",
    "docs/H2_V6_AMENDMENT_14.md",
)
PHASE_PATHS = {
    "defect": "h2_v6/defect_hardening_*/manifest.json",
    "hardening": "h2_v6/hardening_low_*/manifest.json",
    "b0": "h2_v6/b0_low_*/manifest.json",
    "cal_a": "cal_a_v6/run_*/summary.json",
    "sequential": "sequential_dev_v6/run_*/summary.json",
    "stress": "stress_v6/run_*/summary.json",
}
PHASES = tuple(PHASE_PATHS)


def require_sessions(sessions):
    for day in sessions:
        if day > "2024-08-30" or day in anchors.CAL_B4_ANCHORS:
            raise ValueError("v6 refuses CAL-B4 and decisions after 2024-08-30")


def technical_audit(records):
    unique = {}
    for r in records:
        if r.request.stage == "technical_analyst":
            unique.setdefault((r.request.identity_digest, r.provider_response_id), r)
    converted, invalid = [], []
    for r in unique.values():
        if r.status != "ok":
            if r.error_type in ("ValueError", "TypeError", "ValidationError"):
                invalid.append({"call_id": r.call_id, "decision_session": r.request.decision_session,
                                "error": r.error_message})
            continue
        try:
            payload = json.loads(r.request.user_prompt)
            text = render_technical_evidence(r.validated_response, payload["features"], payload["allowed_evidence_codes"])
            converted.append(replace(r, request=replace(r.request, user_prompt="Features: " + json.dumps(payload["features"])),
                                     validated_response={**r.validated_response, "justification": text}))
        except (ValueError, KeyError, TypeError) as exc:
            invalid.append({"call_id": r.call_id, "decision_session": r.request.decision_session, "error": str(exc)})
    audit = h2_v4.technical_audit(converted)
    audit.pop("technical_prompt_v3_only")
    for gate in ("S1", "S2", "S3"):
        audit[f"V6-{gate}"] = audit.pop(f"V4-{gate}")
    audit["rates"] = {k.replace("V4-", "V6-"): v for k, v in audit["rates"].items()}
    for row in audit["flagged"]:
        row["findings"] = {k.replace("V4-", "V6-"): v for k, v in row["findings"].items()}
    audit.update({"V6-E": len(invalid), "invalid_evidence": invalid,
                  "technical_calls": len(unique), "evidence_validator_version": 1,
                  "technical_prompt_v5_only": all(r.request.system_prompt_sha256 == TECHNICAL_SYSTEM_PROMPT_V5_SHA256
                      and r.request.response_schema == "TechnicalEvidenceResponse" for r in unique.values())})
    audit["rates"]["V6-E"] = len(invalid) / len(unique) if unique else None
    audit["natural_v5_failure_sessions"] = {
        d: {"technical_calls": sum(r.request.decision_session == d for r in unique.values()),
            "invalid_evidence": sum(row["decision_session"] == d for row in invalid),
            "linguistic_flags": [row for row in audit["flagged"] if row["decision_session"] == d]}
        for d in ("2024-04-01", "2024-05-16", "2024-06-12", "2024-08-06")}
    return audit


def apply_structural_gates(payload):
    audit = payload["technical_audit"]
    gates = payload.setdefault("gates", {})
    for key in ("V6-E", "V6-S1", "V6-S2", "V6-S3"):
        gates[key] = {"value": audit[key], "threshold": "== 0", "pass": audit[key] == 0}
    passed = (audit["technical_calls"] > 0 and audit["technical_prompt_v5_only"]
              and all(g["pass"] for g in gates.values()) and payload.get("complete", payload.get("gates_pass", False)))
    pairing = payload.get("paired_technical_audit")
    if pairing:
        passed = passed and pairing["same_five_technical_responses_in_all_configs"]
    expected = {"H2_HARDENING_V6": 300, "H2_B0_V6": 60, "CAL_A_V6": 300,
                "SEQUENTIAL_DEVELOPMENT_V6": 1905}.get(payload.get("kind"))
    if expected:
        passed = passed and audit["technical_votes"] == expected
    passed = passed and sum(r["value"] for k, r in gates.items() if k in ("V6-E", "V6-S1", "V6-S2", "V6-S3")) == 0
    payload["v6_phase_pass"] = bool(passed)
    if not passed:
        payload["status"] = treatment.H2_V6_DEFECT_FIX_FAILED
    return payload


def committed_phase(phase):
    paths = sorted((ROOT / "docs/evidence").glob(PHASE_PATHS[phase]))
    if not paths:
        raise ValueError(f"v6 requires committed {phase} PASS")
    path = paths[-1].relative_to(ROOT).as_posix()
    if h2_v4.git("hash-object", path) != h2_v4.git("rev-parse", f"HEAD:{path}"):
        raise ValueError(f"v6 phase evidence must be committed: {path}")
    summary = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not summary.get("v6_phase_pass"):
        raise ValueError(f"v6 stopped at {phase}; further execution refused")
    return summary


def load_v6_selections():
    cal = committed_phase("cal_a")
    row = next(c for c in cal["grid"] if c["config_id"] == cal["selected_config_id"])
    treatment.CAL_A_V6_SELECTED_CONFIG = {**row, "discrimination": cal["cal_a_discrimination"],
                                         "selection_basis": ("PROTOCOL_TIE_FALLBACK" if cal["cal_a_discrimination"] == "NONE"
                                                             else "EMPIRICAL_S1")}
    paths = sorted((ROOT / "docs/evidence").glob(PHASE_PATHS["sequential"]))
    if paths:
        seq = committed_phase("sequential")
        from src.experiments.phases import SEQUENTIAL_DEV_GRID
        row = next(c for c in SEQUENTIAL_DEV_GRID if c["config_id"] == seq["selected_config_id"])
        treatment.SEQUENTIAL_DEV_V6_SELECTED_CONFIG = {**row, "discrimination": seq["sequential_dev_discrimination"],
                                                      "selection_basis": seq["selection_basis"]}


def require_pre_live_freeze(*, full_development=False, phase=None):
    checker = h2_v4.require_pre_live_freeze()
    audit = json.loads((ROOT / AUDIT).read_text(encoding="utf-8"))
    for path, digest in {**audit["frozen_sources_sha256"], **audit["preserved_sources_sha256"]}.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"v6 frozen source changed: {path}")
        if h2_v4.git("hash-object", path) != h2_v4.git("rev-parse", f"HEAD:{path}"):
            raise ValueError(f"v6 frozen source must be committed: {path}")
    for path in (AUDIT, "docs/evidence/h2_v6/offline_verification.json"):
        if h2_v4.git("hash-object", path) != h2_v4.git("rev-parse", f"HEAD:{path}"):
            raise ValueError(f"v6 offline freeze must be committed: {path}")
    carry = json.loads((ROOT / "docs/evidence/h2_v6/cal_b4_carry_forward_audit.json").read_text(encoding="utf-8"))
    for path, digest in carry["historical_artifacts_sha256"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"historical v5 evidence changed: {path}")
    if not audit["CAL_B4_CARRIED_FORWARD_TO_H2_V6"] or audit["CAL_B4_HOLDOUT_INTEGRITY"] != "PRESERVED":
        raise ValueError("v6 carry-forward audit failed")
    require_sessions(used_sessions())
    if anchors.CAL_B_AUTHORIZED is not False or audit["cal_b4_commitment"] != anchors.CAL_B4_COMMITMENT_SHA256:
        raise ValueError("CAL-B4 must remain sealed and unchanged")
    if full_development:
        committed_phase("defect")
    if phase:
        # Earlier failures permanently stop this task; do not authorize reruns.
        for earlier in PHASES[:PHASES.index(phase)]:
            committed_phase(earlier)
        if list((ROOT / "docs/evidence").glob(PHASE_PATHS[phase])):
            raise ValueError(f"v6 {phase} already has evidence; rerun refused")
    endpoint = urlsplit(os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"))
    if (endpoint.scheme != "https" or endpoint.hostname != "generativelanguage.googleapis.com"
            or endpoint.port not in (None,443) or endpoint.path.rstrip("/") != "/v1beta"
            or endpoint.username or endpoint.query or endpoint.fragment):
        raise ValueError("v6 only permits the authorized native Gemini endpoint")
    auth_path = ROOT / AUTHORIZATION
    if not auth_path.exists():
        raise ValueError("H2 v6 requires explicit external-provider authorization; v5 permission is insufficient")
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    if auth.get("treatment_version") != 6 or auth.get("authorized") is not True or auth.get("host") != endpoint.hostname:
        raise ValueError("H2 v6 authorization is invalid")
    if h2_v4.git("hash-object", AUTHORIZATION) != h2_v4.git("rev-parse", f"HEAD:{AUTHORIZATION}"):
        raise ValueError("v6 authorization must be committed")
    return {"checker": checker, "pre_live_audit": AUDIT, "authorization": AUTHORIZATION}
