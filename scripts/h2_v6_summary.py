"""Describe frozen preparation or observed v6 phases; never invoke a provider."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT / "scripts"))

import h2_v4
from h2_v6 import PHASE_PATHS, require_sessions
from select_cal_b4 import used_sessions
from src.agents.technical_evidence import EVIDENCE_CODES, ROLE_DISPLAY
from src.agents.technical_prompt_v5 import TECHNICAL_SYSTEM_PROMPT_V5, TECHNICAL_SYSTEM_PROMPT_V5_SHA256
from src.experiments import anchors, treatment

OUT = ROOT / "docs/evidence/h2_v6"


def main():
    phases = {}
    for name,glob in PHASE_PATHS.items():
        files = sorted((ROOT / "docs/evidence").glob(glob))
        if not files:
            phases[name] = {"status":"NOT EXECUTED","technical_votes":None,"S3_rate":None,"parameters":None}
            continue
        path=files[-1]; p=json.loads(path.read_text(encoding="utf-8")); a=p["technical_audit"]
        phases[name] = {"status":p.get("status","COMPLETE" if p.get("complete") else "INCOMPLETE"),
                       "v6_phase_pass":p.get("v6_phase_pass",False),"source":path.relative_to(ROOT).as_posix(),
                       "technical_votes":a["technical_votes"],"technical_audit":a,"S3_rate":a["rates"]["V6-S3"],
                       "gates":p.get("gates"),"complete":p.get("complete",p.get("gates_pass")),
                       "selected_config_id":p.get("selected_config_id"),"selection_basis":p.get("selection_basis"),
                       "parameters":p.get("participant_params",p.get("frozen_params")),
                       "S1":p.get("S1"),"S2":p.get("S2"),"ranking":p.get("ranking"),
                       "tie_at_top":p.get("tie_at_top"),"pairing":p.get("paired_technical_audit"),
                       "natural_v5_failure_sessions":a["natural_v5_failure_sessions"],"operational":p.get("operational")}
    failed = any(p.get("v6_phase_pass") is False for p in phases.values())
    complete = all(p.get("v6_phase_pass") for p in phases.values())
    status = ("H2_V6 DEVELOPMENT COMPLETE — READY FOR CAL-B4 PROTOCOL" if complete
              else treatment.H2_V6_DEFECT_FIX_FAILED if failed
              else "H2_V6 PREPARED OFFLINE — AWAITING SPECIFIC EXTERNAL AUTHORIZATION"
              if all(p["status"] == "NOT EXECUTED" for p in phases.values()) else "H2_V6 DEVELOPMENT IN PROGRESS")
    require_sessions(used_sessions())
    final = phases["stress"].get("parameters") if complete else None
    commits = h2_v4.git("log","--reverse","--format=%h %s","9cca5b4..HEAD").splitlines()
    v5=json.loads((ROOT / "docs/evidence/h2_v5/governance_for_v6.json").read_text(encoding="utf-8"))
    carry=json.loads((OUT / "cal_b4_carry_forward_audit.json").read_text(encoding="utf-8"))
    verification=json.loads((OUT / "offline_verification.json").read_text(encoding="utf-8"))
    packet = {"status":status,"treatment_version":6,"technical_prompt_version":5,"response_schema_version":2,
        "evidence_validator_version":1,"evidence_vocabulary_version":1,"v5_governance":v5,
        "phases":phases,"entry_baseline_label":treatment.H2_V6_ENTRY_BASELINE_LABEL,
        "entry_baseline_params":dict(treatment.H2_V6_DEFECT_PARAMS),"final_v6_params":final,
        "cal_b4":{"status":"SEALED / NOT EXECUTED","commitment":anchors.CAL_B4_COMMITMENT_SHA256,
                   "carry_forward_integrity":carry["CAL_B4_HOLDOUT_INTEGRITY"],"executed":False},
        "validation_final":{"executed":False,"decision_sessions":[]},"offline_verification":verification,
        "temporal_rates":{"v3_consumed":{"S3":16,"N":50,"rate":.32},
            "v4_directed":{"S3":10,"N":150,"rate":10/150},
            "v5_directed":{"S3":0,"N":150,"rate":0},"v5_hardening":{"S3":0,"N":300,"rate":0},
            "v5_b0":{"S3":0,"N":60,"rate":0},"v5_cal_a":{"S3":0,"N":300,"rate":0},
            "v5_sequential":{"S3":4,"N":1905,"rate":4/1905},
            "v6":{n:p["S3_rate"] for n,p in phases.items()}},
        "commits_at_report_generation":commits,"provider_calls_from_this_report":0}
    (OUT / "development_summary.json").write_text(json.dumps(packet,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    lines = ["# H2 v6 delivery", "",status,"",
        "## H2 V5 FINAL GOVERNANCE", "", v5["status"]+"; "+v5["reason"]+". Ineligible for System Freeze.",
        "All original artifacts and four flagged responses remain byte-identical; intermediate selections are preserved; Stress NOT EXECUTED.","",
        "## H2 V6 CHANGESET", "", "Treatment 6 / Technical prompt 5 / response schema 2 / evidence validator 1 / vocabulary 1.",
        "Eight features/schema 2, Risk prompt 2, Portfolio, confidence semantics V1, runtime, quorum, data/cost and execution are unchanged.","",
        "## WHY FREE TEXT WAS REMOVED", "", "V5 snapshot instructions still allowed 4 unsupported temporal claims among 1905 Sequential outputs. A closed current-fact contract removes factual free narration without selecting the model's signal or qualitative roles.","",
        "## TECHNICAL RESPONSE SCHEMA V2", "", "Exactly signal, confidence, evidence [{code, role}]. Strict extra-property rejection, confidence 0..1; no justification, reasoning, comment or free string.",
        "Exact JSON Schema: [technical_response_schema_v2.json](technical_response_schema_v2.json).", "",
        "## EVIDENCE VOCABULARY", "", ", ".join(EVIDENCE_CODES)+".","",
        "## ALLOWED-EVIDENCE GENERATION", "", "Exactly eight canonical features; sign/zero comparison selects one SMA50, SMA200, band, MACD-zero and MACD/signal fact, plus current RSI and width. No epsilon thresholds. Inconsistent band order and coincident zero boundaries fail before provider calls. JSON user prompt contains only features and allowed_evidence_codes.","",
        "## EVIDENCE VALIDATOR", "", "Schema + request-specific membership + nonempty unique subset of at most seven facts. Roles are free qualitative classifications, never hardcoded to code or signal. Invalid response is fail closed, without repair; v6 validation errors are replayable ValueError records.","",
        "## EXACT TECHNICAL PROMPT V5", "", "SHA256: "+TECHNICAL_SYSTEM_PROMPT_V5_SHA256,"", "```text",TECHNICAL_SYSTEM_PROMPT_V5,"```","",
        "## DETERMINISTIC RENDERER", "", "Fixed Portuguese current-fact templates with each role explicitly attributed to the analyst. Canonical RSI/width values are rendered directly. No evolution, persistence or inference. Display never enters Risk, Portfolio or any other LLM request.","",
        "## TRACE / PROVENANCE CHANGES", "", "Original raw provider output, validated structured response, allowed codes and display remain separate. Optional technical_evidence observation records treatment/prompt/schema/vocabulary/validator versions and prompt/schema/allowed/raw/validated/display SHA256 values plus UI serialization. Existing request identity already covers changed prompt and schema. Historical v1-v5 response schemas and requests stay reproducible.","",
        "## CHECKER V3 IMMUTABILITY AUDIT", "", "feature_semantics.py and scripts/h2_v4.py remain byte-identical to their freeze. The original checker audits rendered text without recalibration. Offline regression reproduces v3 16/50, v4 10/150 and v5 Sequential 4/1905. The 1620-case renderer matrix has zero S1/S2/S3 flags.","",
        "## CAL-B4 CARRY-FORWARD AUDIT", "", "CAL_B4_CARRIED_FORWARD_TO_H2_V6=True; PRESERVED. Same commitment/ranking reproduced using calendar/identity only; runner/bank guards passed with no inference. "+str(carry["historical_artifacts_count"])+" original v5 artifacts hashed and preserved.","",
        "## DEFECT-DIRECTED HARDENING V6", "",phases["defect"]["status"]+". Ten consumed CAL-B3 anchors x R=3 x N=5; 150 live Technical outputs; no t+1. Gates E/S1/S2/S3/A/T ==0 and HOLD <.90. Any failure stops, with no edits/reruns. Targets 2020-05-13 and 2022-03-11 may remain MANTER.","",
        "## STRUCTURED EVIDENCE FAILURES", "", "V6 live E results are pending for phases not executed; offline incompatible facts, duplicate codes, invalid roles and textual extras were rejected. No live PASS is inferred from tests.","",
        "## TEMPORAL CLAIM RATE", "", "Rates below describe different phase corpora; they are not a paired estimate of treatment effects.","",
        "| Corpus | S3 / N | Rate |","|---|---:|---:|","| v3 consumed | 16/50 | 32% |","| v4 directed | 10/150 | 6.67% |",
        "| v5 directed | 0/150 | 0% |","| v5 Hardening | 0/300 | 0% |","| v5 B0 | 0/60 | 0% |","| v5 CAL-A | 0/300 | 0% |","| v5 Sequential | 4/1905 | 0.21% |"]
    for name,p in phases.items():
        lines.append(f"| v6 {name} | {p.get('technical_audit',{}).get('V6-S3','NOT EXECUTED')}/{p['technical_votes']} | {p['S3_rate'] if p['S3_rate'] is not None else 'pending'} |")
    for name,title,description in (("hardening","HARDENING V6","Same 12 H states, R=5, original gates plus E/S1/S2/S3."),
        ("b0","B0 V6","Same H states, R=1, same ex ante baseline and gates."),
        ("cal_a","CAL-A V6","Same 20 anchors, six 21/63 x .40/.50/.60 candidates, R=3, original S1 and tie-break; new live Technical with within-phase pairing."),
        ("sequential","SEQUENTIAL DEVELOPMENT V6","Same 2024-03-01 -> 2024-08-30 window, D01 .25/D02 .15/D03 .35, R=3, original Sharpe/S2/tie-break. All 1905 unique Technical outputs audited. Four prior failure sessions are naturally re-evaluated here only."),
        ("stress","STRESS V6","Only after complete Sequential PASS: same four windows, R=3, original integrity gates plus E/S1/S2/S3; no tuning authority.")):
        lines.extend(["","## "+title,"",phases[name]["status"]+". "+description])
        if name == "sequential":
            lines.extend(["", "Natural four-session results:","",json.dumps(phases[name].get("natural_v5_failure_sessions",
                {d:"NOT EXECUTED" for d in ("2024-04-01","2024-05-16","2024-06-12","2024-08-06")}),ensure_ascii=False)])
    lines.extend(["","## FINAL V6 PARAMETERS","",json.dumps(final,ensure_ascii=False)+" — no final selection before all required phases pass.",
        "Entry only: 21/.40/.15/1.0; "+treatment.H2_V6_ENTRY_BASELINE_LABEL+". CAL-A and Sequential reselect independently.","",
        "## UI SERIALIZATION CONTRACT","","signal, confidence, evidence [{code, role, display}], display_explanation; portable JSON, no frontend dependency.","",
        "## CAL-B4 SAFETY","","SEALED / NOT EXECUTED. Commitment: "+anchors.CAL_B4_COMMITMENT_SHA256,"",
        "## VALIDATION / FINAL SAFETY","","NOT EXECUTED; no v6 decision beyond 2024-08-30. Development engines retain their existing data boundaries.","",
        "## COMMITS CREATED","","Commits through report generation (the delivery commit itself is recorded by git log):","",*['- '+c for c in commits],"",
        "## NEXT STEP","","Specific H2 v6 external authorization is required before first live call (user request item 40). V5 authorization does not carry to v6.",
        "After authorization, execute directed hardening then conditional phases in frozen order. CAL-B4 remains sealed throughout.","",
        "Offline verification: "+str(verification["tests_passed"])+" tests passed; zero external provider calls.",""])
    (OUT / "DELIVERY.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"status":status,"final_v6_params":final,"provider_calls_from_report":0},ensure_ascii=False))


if __name__ == "__main__":
    main()
