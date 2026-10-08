"""Offline, identity-only carry-forward and immutable v6 pre-live packet."""

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import h2_v4
import h2_v6
from run_cal_a import BankedGeminiClient
from select_cal_b4 import used_sessions
from src.agents.technical_prompt_v5 import TECHNICAL_SYSTEM_PROMPT_V5, TECHNICAL_SYSTEM_PROMPT_V5_SHA256
from src.agents.technical_evidence import TechnicalEvidenceResponse, EVIDENCE_CODES
from src.agents.llm_trace import load_trace, schema_digest
from src.artifacts import canonical_json
from src.experiments import anchors, treatment

OUT = ROOT / "docs/evidence/h2_v6"
BASELINE = "9cca5b4"
CARRY = OUT / "cal_b4_carry_forward_audit.json"
PRESERVED = ("src/agents/feature_semantics.py", "scripts/h2_v4.py", "src/agents/features.py",
             "src/agents/risk_contract.py", "src/agents/risk_manager.py", "src/agents/portfolio_manager.py",
             "src/agents/technical_prompt_v4.py", "docs/evidence/cal_b4/selection.json",
             "docs/evidence/h2_v5/final_governance.json")


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def hashes(paths):
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def carry_forward():
    from tests.experiments.test_cal_b4_safety import test_cal_b4_commitment_selection_and_ranking
    h2_v4.require_pre_live_freeze()
    test_cal_b4_commitment_selection_and_ranking()
    for p in PRESERVED:
        assert h2_v4.git("hash-object", p) == h2_v4.git("rev-parse", f"{BASELINE}:{p}"), p
    sessions = used_sessions()
    h2_v6.require_sessions(sessions)
    guards = []
    for day in (*anchors.CAL_B4_ANCHORS, "2024-09-02"):
        try:
            h2_v6.require_sessions([day])
        except ValueError:
            pass
        else:
            raise AssertionError("v6 session guard failed")
        if day in anchors.CAL_B4_ANCHORS:
            try:
                anchors.require_cal_b_locked(day, day)
            except ValueError:
                pass
            else:
                raise AssertionError("holdout runner guard failed")
        client = BankedGeminiClient(api_key="offline-guard",model="gemini-3.8-flash")
        client.begin_session(day)
        try:
            asyncio.run(client.generate("unused","unused"))
        except RuntimeError:
            pass
        else:
            raise AssertionError("call bank guard failed before network")
        guards.append({"session":day,"v6_guard":True,"bank_guard":True,"network_calls":0})
    roots = ("docs/evidence/h2_v5", "docs/evidence/cal_a_v5", "docs/evidence/sequential_dev_v5")
    original = h2_v4.git("ls-tree", "-r", "--name-only", BASELINE, "--", *roots).splitlines()
    changed = set(h2_v4.git("diff", "--name-only", BASELINE, "--", *roots).splitlines()) & set(original)
    assert not changed, changed
    historical_hashes = hashes(original)
    write_once(CARRY, {
        "kind":"H2_V6_CAL_B4_CARRY_FORWARD", "audited_utc":datetime.now(timezone.utc).isoformat(),
        "CAL_B4_CARRIED_FORWARD_TO_H2_V6":True,"CAL_B4_HOLDOUT_INTEGRITY":"PRESERVED",
        "cal_b4_status":"SEALED / NOT EXECUTED", "cal_b4_commitment":anchors.CAL_B4_COMMITMENT_SHA256,
        "commitment_and_calendar_ranking_reproduced":True,"new_commitment_created":False,
        "selection_sha256": hashes([anchors.CAL_B4_SELECTION_EVIDENCE])[anchors.CAL_B4_SELECTION_EVIDENCE],
        "preserved_sources_sha256": hashes(PRESERVED),
        "preserved_source_blobs":{p:h2_v4.git("rev-parse",f"{BASELINE}:{p}") for p in PRESERVED},
        "historical_artifacts_count":len(original),
        "historical_artifacts_aggregate_sha256":hashlib.sha256(canonical_json(historical_hashes).encode()).hexdigest(),
        "historical_artifacts_sha256":historical_hashes,
        "v5_governance":"docs/evidence/h2_v5/governance_for_v6.json",
        "development_identity_sessions_audited":len(sessions),"cal_b4_decision_sessions":[],
        "validation_final_decision_sessions":[],"guards":guards,"provider_calls":0,
        "holdout_inputs":"calendar and decision identity only — no holdout features, returns or LLM outputs",
        "checker_freeze":h2_v4.require_pre_live_freeze(),
    })
    print(json.dumps({"carry_forward":"PRESERVED","historical_artifacts":len(original),"network_calls":0}))


def freeze():
    carry = json.loads(CARRY.read_text(encoding="utf-8"))
    assert carry["CAL_B4_HOLDOUT_INTEGRITY"] == "PRESERVED"
    h2_v6.require_sessions(used_sessions())
    for p,digest in carry["preserved_sources_sha256"].items():
        assert hashes([p])[p] == digest
    baselines = {}
    sources = {
        "v3_consumed":ROOT / "docs/evidence/cal_b3/run_20261006T161844Z/anchors",
        "v4_directed":ROOT / "docs/evidence/h2_v4/defect_hardening_20261007T220356Z/traces",
        "v5_sequential":ROOT / "docs/evidence/sequential_dev_v5/run_20261007T234620Z/runs",
    }
    for label,root in sources.items():
        paths = sorted(root.rglob("*.jsonl"))
        paths = [p for p in paths if p.name == "llm_calls.jsonl" or p.parent.name == "traces"]
        baselines[label] = h2_v4.technical_audit(r for p in paths for r in load_trace(p.read_bytes()))
        baselines[label].pop("technical_prompt_v3_only")
    assert (baselines["v3_consumed"]["technical_votes"],baselines["v3_consumed"]["V4-S3"]) == (50,16)
    assert (baselines["v4_directed"]["technical_votes"],baselines["v4_directed"]["V4-S3"]) == (150,10)
    assert (baselines["v5_sequential"]["technical_votes"],baselines["v5_sequential"]["V4-S3"]) == (1905,4)
    with (OUT / "technical_prompt_v5.txt").open("x",encoding="utf-8",newline="\n") as f:
        f.write(TECHNICAL_SYSTEM_PROMPT_V5)
    write_once(OUT / "technical_response_schema_v2.json",TechnicalEvidenceResponse.model_json_schema())
    write_once(OUT / "checker_regression.json",{"checker_version":3,"recalibrated":False,"provider_calls":0,
        "baselines":baselines,"render_matrix_cases":1620,"render_matrix_S1":0,"render_matrix_S2":0,"render_matrix_S3":0,
        "proof":"tests/agents/test_technical_evidence.py::test_all_renderer_codes_and_roles_against_frozen_checker"})
    files = (*h2_v6.SOURCE_FILES, "scripts/prepare_h2_v6.py", "scripts/h2_v6_summary.py",
             "tests/agents/test_technical_evidence.py", "tests/experiments/test_v6_phase_routing.py",
             "docs/evidence/h2_v6/technical_prompt_v5.txt", "docs/evidence/h2_v6/technical_response_schema_v2.json",
             "docs/evidence/h2_v6/cal_b4_carry_forward_audit.json", "docs/evidence/h2_v6/checker_regression.json")
    write_once(ROOT / h2_v6.AUDIT,{
        "kind":"H2_V6_PRE_LIVE_FREEZE","created_utc":datetime.now(timezone.utc).isoformat(),
        "git_commit":h2_v4.git("rev-parse","HEAD"),"frozen_sources_sha256":hashes(files),
        "preserved_sources_sha256":carry["preserved_sources_sha256"],
        "CAL_B4_CARRIED_FORWARD_TO_H2_V6":True,"CAL_B4_HOLDOUT_INTEGRITY":"PRESERVED",
        "cal_b4_commitment":anchors.CAL_B4_COMMITMENT_SHA256,"cal_b4_status":"SEALED / NOT EXECUTED",
        "technical_prompt_version":5,"technical_prompt_sha256":TECHNICAL_SYSTEM_PROMPT_V5_SHA256,
        "technical_response_schema_version":2,"technical_response_schema_sha256":schema_digest(TechnicalEvidenceResponse),
        "evidence_vocabulary_version":1,"evidence_codes":EVIDENCE_CODES,"evidence_validator_version":1,
        "entry_baseline_label":treatment.H2_V6_ENTRY_BASELINE_LABEL,
        "entry_baseline_params":dict(treatment.H2_V6_DEFECT_PARAMS),"final_v6_params":None,
        "provider_calls":0,"authorization":"PENDING SPECIFIC H2 V6 AUTHORIZATION",
    })
    print(json.dumps({"freeze":"PREPARED OFFLINE","v6_live_calls":0,"v5_sequential_S3":"4/1905"}))


if __name__ == "__main__":
    {"carry-forward":carry_forward,"freeze":freeze}[sys.argv[1]]()
