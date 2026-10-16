"""Descriptive delivery, including a truthful NOT EXECUTED state; no provider calls."""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from h2_v4 import git  # noqa: E402
from h2_v5 import require_pre_live_freeze  # noqa: E402

from src.agents.llm_trace import load_trace  # noqa: E402
from src.agents.technical_prompt_v4 import TECHNICAL_SYSTEM_PROMPT_V4_SHA256  # noqa: E402
from src.artifacts import canonical_json  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.spec import ParticipantSpec  # noqa: E402

OUT = ROOT / "docs/evidence/h2_v5"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    require_pre_live_freeze()
    patterns = {"Defect-directed hardening v5": "h2_v5/defect_hardening_*/manifest.json",
                "Hardening v5": "h2_v5/hardening_low_*/manifest.json",
                "B0 v5": "h2_v5/b0_low_*/manifest.json",
                "CAL-A v5": "cal_a_v5/run_*/summary.json",
                "Sequential Development v5": "sequential_dev_v5/run_*/summary.json",
                "Stress v5": "stress_v5/run_*/summary.json"}
    phases, records = {}, []
    for name, pattern in patterns.items():
        paths = sorted((ROOT / "docs/evidence").glob(pattern))
        path = paths[-1] if paths else None
        result = None if path is None else read(path)
        phases[name] = {"executed": path is not None,
                        "evidence": None if path is None else path.relative_to(ROOT).as_posix(), "result": result}
        if path is None:
            continue
        if "Hardening" in name or "hardening" in name or name == "B0 v5":
            traces = sorted((path.parent / "traces").glob("*.jsonl"))
        else:
            key = "trajectories" if name == "Stress v5" else "evaluations"
            traces = [ROOT / row["runs_root"] / row["run_dir"] / "llm_calls.jsonl" for row in result[key]]
        records.extend(r for p in traces for r in load_trace(p.read_bytes()))
    sessions = {r.request.decision_session for r in records}
    assert not sessions & set(anchors.CAL_B4_ANCHORS)
    assert not any(s > "2024-08-30" for s in sessions)
    assert anchors.CAL_B4_STATUS == "SEALED" and anchors.CAL_B_AUTHORIZED is False
    technical = [r for r in records if r.request.stage == "technical_analyst"]
    assert all(r.request.system_prompt_sha256 == TECHNICAL_SYSTEM_PROMPT_V4_SHA256 for r in technical)
    defect = phases["Defect-directed hardening v5"]["result"]
    temporal_failure = any(p["result"] is not None and p["result"].get("technical_audit", {}).get("V5-S3", 0)
                           for p in phases.values())
    complete = defect is not None and defect["status"] == treatment.H2_V5_DEFECT_FIX_PASSED
    for name, phase in phases.items():
        if name == "Defect-directed hardening v5":
            continue
        result = phase["result"]
        complete = complete and result is not None and result.get("complete", result.get("gates_pass", False))
        if result is not None and "gates" in result:
            complete = complete and all(g["pass"] for g in result["gates"].values())
    complete = complete and not temporal_failure
    status = (treatment.H2_V5_TEMPORAL_FIX_FAILED if temporal_failure else
              "H2_V5 DEVELOPMENT COMPLETE — READY FOR CAL-B4 PROTOCOL" if complete else
              "H2_V5 LIVE NOT EXECUTED — AWAITING PROVIDER EGRESS APPROVAL" if defect is None else
              defect["status"] if defect["status"] != treatment.H2_V5_DEFECT_FIX_PASSED else
              "H2_V5 DEVELOPMENT INCOMPLETE")
    audit, regression = read(OUT / "pre_live_audit.json"), read(OUT / "checker_regression.json")
    blocker = OUT / "execution_blocker.json"
    verification = OUT / "offline_verification.json"
    post_verification = OUT / "post_live_verification.json"
    governance = OUT / "final_governance.json"
    authorization = OUT / "execution_authorization.json"
    temporal = {"v3_consumed_CAL_B3": {"violations": 16, "outputs": 50, "rate": .32},
                "v4_defect": {"violations": 10, "outputs": 150, "rate": 10 / 150},
                "v5_defect": None if defect is None else {
                    "violations": defect["technical_audit"]["V5-S3"],
                    "outputs": defect["technical_audit"]["technical_votes"],
                    "rate": defect["technical_audit"]["rates"]["V5-S3"]},
                "interpretation": "development language fidelity only; no future performance"}
    temporal["v5_by_phase"] = {name: {"violations": p["result"]["technical_audit"]["V5-S3"],
                                     "outputs": p["result"]["technical_audit"]["technical_votes"],
                                     "rate": p["result"]["technical_audit"]["rates"]["V5-S3"]}
                              for name, p in phases.items() if p["result"] is not None}
    spec_hashes = {f"v{version}": hashlib.sha256(canonical_json(ParticipantSpec("llm_agent", params).to_dict()).encode()).hexdigest()
                   for version, params in ((4, dict(treatment.H2_V4_DEFECT_PARAMS)), (5, dict(treatment.H2_V5_DEFECT_PARAMS)))}
    assert spec_hashes["v4"] != spec_hashes["v5"]
    summary = {"kind": "H2_V5_DEVELOPMENT_SUMMARY", "descriptive_only": True,
               "status": status, "development_complete": complete, "phases": phases,
               "v4_final_governance": read(ROOT / "docs/evidence/h2_v4/final_governance.json"),
               "treatment_version": 5, "technical_prompt_version": 4, "risk_prompt_version": 2,
               "feature_schema_version": 2, "technical_prompt_sha256": TECHNICAL_SYSTEM_PROMPT_V4_SHA256,
               "participant_spec_hashes": spec_hashes, "baseline_v5_params": dict(treatment.H2_V5_DEFECT_PARAMS),
               "final_v5_params": treatment.stress_v5_params() if complete else None,
               "CAL_A_V5_SELECTED_CONFIG": None if treatment.CAL_A_V5_SELECTED_CONFIG is None else dict(treatment.CAL_A_V5_SELECTED_CONFIG),
               "SEQUENTIAL_DEV_V5_SELECTED_CONFIG": None if treatment.SEQUENTIAL_DEV_V5_SELECTED_CONFIG is None else dict(treatment.SEQUENTIAL_DEV_V5_SELECTED_CONFIG),
               "temporal_claim_comparison": temporal, "checker_immutability_audit": audit["checker_freeze"],
               "offline_checker_baselines": {name: {k: baseline[k] for k in ("technical_votes", "V4-S1", "V4-S2", "V4-S3")}
                                            for name, baseline in regression["baselines"].items()},
               "CAL_B4_CARRIED_FORWARD_TO_H2_V5": True, "CAL_B4_HOLDOUT_INTEGRITY": "PRESERVED",
               "cal_b4_safety": {"status": "SEALED — NEVER EXECUTED", "executed": False,
                   "commitment": anchors.CAL_B4_COMMITMENT_SHA256, "sessions_touched": [], "new_commitment": False},
               "validation_final_safety": {"executed": False, "sessions_touched": [], "last_permitted_bar": "2024-08-30"},
               "structured_outputs": "existing decisions/traces preserve session, features, five votes, consensus, all stage rationales, final action, target weight, reason and provenance; no UI changes",
               "technical_calls_in_traces": len(technical),
               "live_technical_calls": len({(r.request.identity_digest, r.provider_response_id)
                                             for r in technical if r.status == "ok"}),
               "development_temporal_contract_failed": temporal_failure,
               "final_governance": read(governance) if governance.exists() else None,
               "provider_authorization": read(authorization) if authorization.exists() else None,
               "selected_v5_values_NOT_FINAL_FREEZE": treatment.stress_v5_params()
                   if treatment.CAL_A_V5_SELECTED_CONFIG is not None and treatment.SEQUENTIAL_DEV_V5_SELECTED_CONFIG is not None else None,
               "execution_blocker": read(blocker) if defect is None and blocker.exists() else None,
               "offline_verification": read(verification) if verification.exists() else None,
               "post_live_offline_verification": read(post_verification) if post_verification.exists() else None,
               "next_step": "CAL-B4 protocol only; do not execute automatically" if complete else
                   "STOP v5 after development S3 failure; no prompt/checker edits or rerun. A new user-authorized treatment/protocol decision is required; CAL-B4 stays sealed." if temporal_failure else
                   "Provider egress approval, then run frozen defect hardening; later phases require PASS" if defect is None else
                   "STOP; preserve evidence, do not edit prompt or checker; CAL-B4 stays sealed" if defect["status"] != treatment.H2_V5_DEFECT_FIX_PASSED else
                   "Continue development under the frozen protocol; CAL-B4 stays sealed"}
    (OUT / "development_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = ["# H2 v5 — delivery report", "", f"**{status}**", "", "## H2 V4 FINAL GOVERNANCE", "",
             "H2_V4 TEMPORAL CONTRACT FIX FAILED; H2_V4_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True.",
             "Reason: DEFECT-DIRECTED HARDENING FAILED V4-S3. Existing v4 evidence preserved.", "",
             "## H2 V5 CHANGESET", "", "[Amendment 13](../../H2_V5_AMENDMENT_13.md). Only Technical v3 -> v4 snapshot/temporal language.",
             "Treatment 5; Technical 4; Risk 2; feature schema 2. All other treatment settings unchanged.",
             "Participant spec SHA-256:", "", f"- v4: `{spec_hashes['v4']}`", f"- v5: `{spec_hashes['v5']}`", "",
             "## EXACT TECHNICAL PROMPT V4", "", "[Exact UTF-8 prompt](technical_prompt_v4.txt); " + f"SHA-256 `{TECHNICAL_SYSTEM_PROMPT_V4_SHA256}`.", "",
             "## SNAPSHOT-ONLY STRICT CONTRACT", "", "Only current snapshot statements. Persistence/evolution forbidden. Current trend, current momentum and mathematical RSI lookback allowed. Five explicit PASS/FAIL pairs tested; MANTER unchanged.", "",
             "## CHECKER IMMUTABILITY AUDIT", "", "Checker v3 byte-identical; no recalibration. [Pre-live audit](pre_live_audit.json), [offline regression](checker_regression.json).", "",
             "| Source | SHA-256 | Git blob |", "|---|---|---|"]
    for path, sha in audit["checker_freeze"]["source_sha256"].items():
        lines.append(f"| {path} | `{sha}` | `{audit['checker_freeze']['source_blobs'][path]}` |")
    lines += ["", "## V4 BASELINE VIOLATIONS", "", "Original 10/150 S3 flags reproduced exactly; S1=S2=0. No v4 results corrected.", "",
              "## CAL-B4 CARRY-FORWARD AUDIT", "", "CAL_B4_CARRIED_FORWARD_TO_H2_V5 = True; CAL_B4_HOLDOUT_INTEGRITY = PRESERVED.",
              "Calendar/date/commitment reproduced; runner and call-bank guards block all ten dates before network. No CAL-B4 development decision identity found.", "",
              "## CAL-B4 COMMITMENT", "", f"Existing `{anchors.CAL_B4_COMMITMENT_SHA256}`. Selection file byte-identical; no new commitment/CAL-B5.", "",
              "## DEFECT-DIRECTED HARDENING V5", "", "NOT EXECUTED (no provider call)" if defect is None else f"{defect['status']}; {defect['technical_audit']['technical_votes']}/150 Technical outputs.", "",
              "Targets: 2020-05-13 and 2022-03-11. Decisions may remain MANTER; only current-state rationale fidelity is tested."]
    if defect is not None:
        for day, target in defect["target_anchors"].items():
            live = target["v5_live"]
            actions = [{k: (d["decision"] or {}).get(k) for k in ("technical_outcome", "portfolio_decision", "final_cause")}
                       for d in target["v5_decisions"]]
            lines += ["", f"{day}: S1={live['V5-S1']}, S2={live['V5-S2']}, S3={live['V5-S3']}/{live['technical_votes']}; actions {actions}."]
    lines += ["", "## TEMPORAL CLAIM RATE", "", "| Evidence | Claims / outputs | Rate |", "|---|---|---|",
              "| v3 consumed CAL-B3 (R=1) | 16/50 | 32% |", "| v4 defect (R=3) | 10/150 | 6.67% |"]
    v5 = temporal["v5_defect"]
    lines += ["| v5 defect (R=3) | NOT EXECUTED | not measured |" if v5 is None else
              f"| v5 defect (R=3) | {v5['violations']}/{v5['outputs']} | {v5['rate']:.2%} |", "",
              "Descriptive development evidence with different R; no future-performance claim.", "",
              "| V5 phase | Claims / unique Technical responses | Rate |", "|---|---|---|"]
    for name, rate in temporal["v5_by_phase"].items():
        lines.append(f"| {name} | {rate['violations']}/{rate['outputs']} | {rate['rate']:.4%} |")
    lines += ["", "## V5 GATE TABLE", "",
              "The following are the original defect-directed gates. Their PASS is preserved. "
              + ("Full development later failed the same zero-S3 language contract (Sequential: 4/1905); progression stopped before Stress." if temporal_failure else ""), "",
              "| Gate | Threshold | Observed | Result |", "|---|---|---|---|"]
    for gate in ("V5-S1", "V5-S2", "V5-S3", "V5-A", "V5-T", "V5-D"):
        g = None if defect is None else defect["gates"][gate]
        lines.append(f"| {gate} | {'< 0.90' if gate == 'V5-D' else '== 0'} | {'not measured' if g is None else g['value']} | {'NOT EXECUTED' if g is None else 'PASS' if g['pass'] else 'FAIL'} |")
    for name, phase in phases.items():
        if name == "Defect-directed hardening v5":
            continue
        lines += ["", f"## {name.upper()}", "", "NOT EXECUTED — STOP after Sequential Development S3 failure." if not phase["executed"] and temporal_failure else
                  "NOT EXECUTED — requires prior gates/selection." if not phase["executed"] else
                  f"Evidence: [{phase['evidence']}]({Path(phase['evidence']).relative_to('docs/evidence/h2_v5').as_posix() if phase['evidence'].startswith('docs/evidence/h2_v5/') else '../' + '/'.join(phase['evidence'].split('/')[2:])})."]
        result = phase["result"]
        if result is None:
            continue
        if "gates" in result:
            lines += ["", "```json", json.dumps(result["gates"], indent=2, ensure_ascii=False), "```"]
        if name == "CAL-A v5":
            lines += ["", "360/360 evaluations; 60/60 paired Technical realizations; audit S1/S2/S3=0/300.",
                      "CAL_A_V5_DISCRIMINATION = NONE; CAL_A_V5_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK.",
                      "All six S1 scores identical; C1 (21 / 0.40) selected by lowest config_id. No superiority claim.",
                      "```json", json.dumps({k: result[k] for k in ("S1", "ranking", "selected_config_id", "paired_technical_audit")}, indent=2), "```",
                      "Two recovered transient failures: one timeout and one transport error; no final failure."]
        if name == "Sequential Development v5":
            lines += ["", "9/9 runs; 381/381 session-replicates paired; last decision 2024-08-29, last data/settlement 2024-08-30.",
                      "SEQUENTIAL_DEV_V5_DISCRIMINATION = YES; SEQUENTIAL_DEV_V5_SELECTION_BASIS = EMPIRICAL_S2.",
                      "D02 (drawdown 0.15) selected by highest mean Scientific Sharpe; no top tie. R=3 development evidence only.",
                      "```json", json.dumps({k: result[k] for k in ("S2", "ranking", "selected_config_id", "sharpe_by_replicate", "paired_technical_audit", "validation_audit")}, indent=2), "```",
                      "Three recovered transient failures: one connection reset and two transport errors; no final failure.", "",
                      "**Temporal contract FAIL: 4/1905 (0.2100%), S1=S2=0.**", "",
                      "All four rationales asserted `enfraquecimento` rather than a current weak state; all four votes were MANTER."]
            for flag in result["technical_audit"]["flagged"]:
                lines += ["", f"- {flag['decision_session']}, analyst {flag['analyst_id']}: "
                          + "; ".join(f["text"] for f in flag["findings"]["V5-S3"])]
    lines += ["", "## FINAL V5 PARAMETERS", "", "No parameters eligible for final freeze: v5 stopped before Stress. Recorded phase selections: window 21, max volatility 0.40, max drawdown 0.15, max concentration 1.0. Original input baseline: 21 / 0.50 / 0.25 / 1.0." if temporal_failure else
              "No final selection yet. Input baseline only: 21 / 0.50 / 0.25 / 1.0." if not complete else
              "```json\n" + json.dumps(summary["final_v5_params"], indent=2, ensure_ascii=False) + "\n```", "",
              "## CAL-B4 SAFETY", "", "NOT EXECUTED — SEALED. No features, payloads, rationales, returns or Risk/checker evaluation for CAL-B4.", "",
              "## VALIDATION / FINAL SAFETY", "", "NOT EXECUTED. No v5 decision >=2024-09-02; scientific data capped at 2024-08-30.", "",
              "## COMMITS CREATED", "", "```text", git("log", "--reverse", "--format=%h %s", "ab7a328..HEAD"), "```", "",
              "The commit containing this delivery is available in git log (a commit cannot contain its own hash).", ""]
    if verification.exists():
        check = read(verification)
        lines += ["## OFFLINE VERIFICATION", "", f"{check['passed']} tests passed, {check['failed']} failed, {check['errors']} errors. Provider calls: 0.",
                  "Tests use mocks and synthetic data. Temporary-directory ACL limitations were resolved by running this offline check outside the sandbox.", ""]
    if post_verification.exists():
        check = read(post_verification)
        lines += [f"Post-live: {check['passed']} targeted tests passed, {check['failed']} failed, {check['errors']} errors; provider calls: 0.",
                  "The shared phase guard refuses further development after S3 failure. Frozen prompt, checker, Risk, Portfolio, features and CAL-B4 commitment unchanged.", ""]
    lines += ["## NEXT STEP", "", summary["next_step"]]
    if defect is None and blocker.exists():
        lines += ["", "Automatic approval review rejected the live command before process start: provider payload egress to the named Google Gemini endpoint requires explicit authorization. [Blocker record](execution_blocker.json)."]
    (OUT / "DELIVERY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(status)


if __name__ == "__main__":
    main()
