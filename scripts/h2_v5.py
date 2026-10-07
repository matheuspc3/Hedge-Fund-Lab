"""V5 audits reuse the frozen v3 checker; never infer on CAL-B4."""

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import h2_v4  # noqa: E402
from run_cal_a import BankedGeminiClient  # noqa: E402
from select_cal_b4 import used_sessions  # noqa: E402

from src.agents.llm_trace import load_trace  # noqa: E402
from src.agents.technical_prompt_v4 import TECHNICAL_SYSTEM_PROMPT_V4_SHA256  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402

AUDIT = "docs/evidence/h2_v5/pre_live_audit.json"
REGRESSION = "docs/evidence/h2_v5/checker_regression.json"
PRESERVED = ("src/agents/feature_semantics.py", "scripts/h2_v4.py",
             "src/agents/features.py", "src/agents/risk_contract.py",
             "src/agents/risk_manager.py", "src/agents/portfolio_manager.py",
             "docs/evidence/cal_b4/selection.json")
V4_FREEZE_COMMIT = "ab7a328"


def technical_audit(records):
    records = list(records)
    audit = h2_v4.technical_audit(records)
    audit.pop("technical_prompt_v3_only")
    # Same checker and counting; only presentation labels change for v5.
    for gate in ("S1", "S2", "S3"):
        audit[f"V5-{gate}"] = audit.pop(f"V4-{gate}")
    audit["rates"] = {k.replace("V4-", "V5-"): v for k, v in audit["rates"].items()}
    for row in audit["flagged"]:
        row["findings"] = {k.replace("V4-", "V5-"): v for k, v in row["findings"].items()}
    audit["technical_prompt_v4_only"] = all(
        r.request.system_prompt_sha256 == TECHNICAL_SYSTEM_PROMPT_V4_SHA256
        for r in records if r.request.stage == "technical_analyst" and r.status == "ok")
    return audit


def require_sessions(sessions):
    for day in sessions:
        if day > "2024-08-30":
            raise ValueError("v5 development refuses decision sessions after 2024-08-30")
        if day in anchors.CAL_B4_ANCHORS:
            raise ValueError("CAL-B4 must stay sealed during v5 development")


def require_pre_live_freeze(*, full_development=False):
    freeze = h2_v4.require_pre_live_freeze()
    for path in (AUDIT, REGRESSION, "src/agents/technical_prompt_v4.py"):
        if h2_v4.git("hash-object", path) != h2_v4.git("rev-parse", f"HEAD:{path}"):
            raise ValueError(f"v5 freeze must be committed and identical: {path}")
    audit = json.loads((ROOT / AUDIT).read_text(encoding="utf-8"))
    for path, digest in audit["preserved_sources_sha256"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError(f"preserved source changed: {path}")
    if not audit["CAL_B4_CARRIED_FORWARD_TO_H2_V5"] or audit["CAL_B4_HOLDOUT_INTEGRITY"] != "PRESERVED":
        raise ValueError("CAL-B4 carry-forward audit failed")
    require_sessions(used_sessions())
    if full_development:
        paths = sorted((ROOT / "docs/evidence/h2_v5").glob("defect_hardening_*/manifest.json"))
        if not paths:
            raise ValueError("full development requires v5 defect-directed hardening PASS")
        manifest = json.loads(paths[-1].read_text(encoding="utf-8"))
        if manifest["status"] != treatment.H2_V5_DEFECT_FIX_PASSED or not all(g["pass"] for g in manifest["gates"].values()):
            raise ValueError("full development requires v5 defect-directed hardening PASS")
        path = paths[-1].relative_to(ROOT).as_posix()
        if h2_v4.git("hash-object", path) != h2_v4.git("rev-parse", f"HEAD:{path}"):
            raise ValueError("v5 defect PASS must be committed and unchanged")
    return {**freeze, "carry_forward_audit": AUDIT, "offline_regression": REGRESSION}


def create_pre_live_audit():
    from tests.experiments.test_cal_b4_safety import test_cal_b4_commitment_selection_and_ranking

    h2_v4.require_pre_live_freeze()
    test_cal_b4_commitment_selection_and_ranking()  # calendar/identity only
    out = ROOT / "docs/evidence/h2_v5"
    if (ROOT / AUDIT).exists() or (ROOT / REGRESSION).exists():
        raise ValueError("pre-live audit is immutable; refusing overwrite")
    preserved = {}
    for path in PRESERVED:
        blob = h2_v4.git("rev-parse", f"{V4_FREEZE_COMMIT}:{path}")
        assert h2_v4.git("hash-object", path) == blob, path
        preserved[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    sessions = used_sessions()
    require_sessions(sessions)
    guards = []
    for day in anchors.CAL_B4_ANCHORS:
        try:
            anchors.require_cal_b_locked(day, day)
        except ValueError:
            pass
        else:
            raise AssertionError("runner guard failed")
        client = BankedGeminiClient(api_key="offline-guard-test", model="gemini-3.8-flash")
        client.begin_session(day)
        try:
            asyncio.run(client.generate("unused", "unused"))
        except RuntimeError as exc:
            assert "must never reach the call bank" in str(exc)
        else:
            raise AssertionError("call bank guard failed")
        guards.append({"session": day, "runner_blocked": True, "call_bank_blocked": True, "network_calls": 0})
    selection = json.loads((ROOT / anchors.CAL_B4_SELECTION_EVIDENCE).read_text(encoding="utf-8"))
    v4 = json.loads((ROOT / treatment.H2_V4_DEFECT_EVIDENCE).read_text(encoding="utf-8"))
    assert selection["computed_utc"] < v4["started_utc"]
    baselines = {}
    roots = ("h2_v3", "cal_a_v3", "sequential_dev_v3", "stress_v3", "cal_b3", "h2_v4")
    for name in roots:
        paths = sorted(p for p in (ROOT / "docs/evidence" / name).rglob("*.jsonl")
                       if p.name == "llm_calls.jsonl" or p.parent.name == "traces")
        records = [r for p in paths for r in load_trace(p.read_bytes())]
        baseline = h2_v4.technical_audit(records)
        baseline.pop("technical_prompt_v3_only")
        baseline["evidence_files"] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        baselines[name] = baseline
    assert baselines["h2_v4"]["technical_votes"] == 150 and baselines["h2_v4"]["V4-S3"] == 10
    assert baselines["h2_v4"]["flagged"] == v4["technical_audit"]["flagged"]
    assert baselines["cal_b3"]["technical_votes"] == 50 and baselines["cal_b3"]["V4-S3"] == 16
    out.mkdir(parents=True, exist_ok=True)
    (ROOT / REGRESSION).write_text(json.dumps({"checker_version": 3, "checker_recalibrated": False,
        "provider_calls": 0, "cal_b4_used": False, "baselines": baselines}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    audit = {"kind": "H2_V5_PRE_LIVE_CARRY_FORWARD_AUDIT", "audited_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": h2_v4.git("rev-parse", "HEAD"), "CAL_B4_CARRIED_FORWARD_TO_H2_V5": True,
        "CAL_B4_HOLDOUT_INTEGRITY": "PRESERVED", "cal_b4_status": "SEALED — NEVER EXECUTED",
        "cal_b4_commitment": anchors.CAL_B4_COMMITMENT_SHA256, "commitment_reproduced": True,
        "calendar_only_ranking_reproduced": True, "selected_utc": selection["computed_utc"],
        "selected_before_v4_live": True, "selection_commit": h2_v4.git("log", "-1", "--format=%H", "--", anchors.CAL_B4_SELECTION_EVIDENCE),
        "preserved_sources_sha256": preserved,
        "preserved_source_blobs": {p: h2_v4.git("rev-parse", f"{V4_FREEZE_COMMIT}:{p}") for p in PRESERVED},
        "checker_freeze": h2_v4.require_pre_live_freeze(), "guards": guards,
        "development_decision_sessions_audited": len(sessions), "cal_b4_sessions_in_development": [],
        "validation_final_sessions_in_development": [], "provider_calls": 0,
        "no_new_commitment": True, "technical_prompt_v4_sha256": TECHNICAL_SYSTEM_PROMPT_V4_SHA256}
    (ROOT / AUDIT).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"carry_forward": "PRESERVED", "v4_S3": "10/150", "checker": "byte-identical"}))


if __name__ == "__main__":
    create_pre_live_audit()
