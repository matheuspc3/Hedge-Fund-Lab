"""Visible Technical audit and pre-live freeze checks for Amendment 12."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.feature_semantics import (  # noqa: E402
    TECHNICAL_SYSTEM_PROMPT_V3_SHA256,
    UNSUPPORTED_TEMPORAL_STATE_CLAIM,
    audit_rationale,
    contradictions,
    transitions,
)
from src.experiments import anchors, treatment  # noqa: E402

CHECKER_FILES = ("src/agents/feature_semantics.py", "scripts/h2_v4.py")
REGRESSION_REPORT = "docs/evidence/h2_v4/technical_checker_v3/calibration_report.json"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout.strip()


def require_pre_live_freeze(*, full_development: bool = False) -> dict:
    treatment.require_cal_b4_committed()
    report = json.loads((ROOT / REGRESSION_REPORT).read_text(encoding="utf-8"))
    if not report["acceptance_pass"]:
        raise ValueError("Technical checker v3 acceptance failed")
    for path, digest in report["source_sha256"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"checker changed after calibration: {path}")
    for path in (*report["source_sha256"], REGRESSION_REPORT, anchors.CAL_B4_SELECTION_EVIDENCE):
        git("cat-file", "-e", f"HEAD:{path}")  # must be committed, not merely on disk
    committed_report = json.loads(git("show", f"HEAD:{REGRESSION_REPORT}"))
    if committed_report["source_sha256"] != report["source_sha256"] or not committed_report["acceptance_pass"]:
        raise ValueError("checker calibration report differs from its committed freeze")
    for path in report["source_sha256"]:
        if git("hash-object", path) != git("rev-parse", f"HEAD:{path}"):
            raise ValueError(f"checker source is uncommitted: {path}")
    selection = json.loads(git("show", f"HEAD:{anchors.CAL_B4_SELECTION_EVIDENCE}"))
    if selection["cal_b4_commitment_sha256"] != anchors.CAL_B4_COMMITMENT_SHA256:
        raise ValueError("CAL-B4 committed selection differs")
    if full_development:
        manifests = sorted((ROOT / "docs/evidence/h2_v4").glob("defect_hardening_*/manifest.json"))
        if not manifests or json.loads(manifests[-1].read_text(encoding="utf-8"))["status"] != treatment.H2_V4_DEFECT_FIX_PASSED:
            raise ValueError("full development requires defect-directed hardening PASS")
        git("cat-file", "-e", f"HEAD:{manifests[-1].relative_to(ROOT).as_posix()}")
    return {"version": 3, "source_sha256": report["source_sha256"],
            "source_blobs": {p: git("rev-parse", f"HEAD:{p}") for p in CHECKER_FILES},
            "regression_report": REGRESSION_REPORT}


def technical_audit(records) -> dict:
    # Common realizations count once per request/provider response, not once per grid configuration.
    seen = {}
    for r in records:
        if r.request.stage == "technical_analyst" and r.status == "ok":
            seen.setdefault((r.request.identity_digest, r.provider_response_id), r)
    counts = {"V4-S1": 0, "V4-S2": 0, "V4-S3": 0}
    flagged = []
    for r in seen.values():
        features = json.loads(r.request.user_prompt.splitlines()[0].removeprefix("Features: "))
        findings = audit_rationale(r.validated_response["justification"], features)
        groups = {"V4-S1": contradictions(findings), "V4-S2": transitions(findings),
                  "V4-S3": [f for f in findings if f["claim"] == UNSUPPORTED_TEMPORAL_STATE_CLAIM]}
        for gate, hits in groups.items():
            counts[gate] += bool(hits)
        if any(groups.values()):
            flagged.append({"call_id": r.call_id, "decision_session": r.request.decision_session,
                            "analyst_id": r.request.analyst_id, **r.validated_response, "findings": groups})
    n = len(seen)
    return {"technical_votes": n, **counts, "rates": {g: c / n if n else None for g, c in counts.items()},
            "technical_prompt_v3_only": all(r.request.system_prompt_sha256 == TECHNICAL_SYSTEM_PROMPT_V3_SHA256
                                            for r in seen.values()), "flagged": flagged}
