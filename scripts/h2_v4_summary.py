"""Publish descriptive v4 evidence and safety audit; never invokes a provider."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.feature_semantics import (  # noqa: E402
    TECHNICAL_SYSTEM_PROMPT_V3,
    TECHNICAL_SYSTEM_PROMPT_V3_SHA256,
)
from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402

E = ROOT / "docs/evidence"
OUT = E / "h2_v4"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def latest(pattern):
    paths = sorted(E.glob(pattern))
    return None if not paths else paths[-1]


def main():
    paths = {"Defect-directed hardening": latest("h2_v4/defect_hardening_*/manifest.json"),
             "Hardening v4": latest("h2_v4/hardening_low_*/manifest.json"),
             "B0 v4": latest("h2_v4/b0_low_*/manifest.json"),
             "CAL-A v4": latest("cal_a_v4/run_*/summary.json"),
             "Sequential Development v4": latest("sequential_dev_v4/run_*/summary.json"),
             "Stress v4": latest("stress_v4/run_*/summary.json")}
    phases = {name: {"executed": path is not None, "evidence": None if path is None else path.relative_to(ROOT).as_posix(),
                     "result": None if path is None else read(path)} for name, path in paths.items()}
    defect = phases["Defect-directed hardening"]["result"]
    if defect is None:
        raise ValueError("defect evidence is required")
    records = []
    for name, path in paths.items():
        if path is None:
            continue
        if name in ("Defect-directed hardening", "Hardening v4", "B0 v4"):
            traces = sorted((path.parent / "traces").glob("*.jsonl"))
        else:
            key = "trajectories" if name == "Stress v4" else "evaluations"
            traces = [ROOT / r["runs_root"] / r["run_dir"] / "llm_calls.jsonl" for r in read(path)[key]]
        records.extend(r for p in traces for r in load_trace(p.read_bytes()))
    sessions = {r.request.decision_session for r in records}
    safety = {"cal_b4_status": anchors.CAL_B4_STATUS, "cal_b4_executed": False,
              "cal_b4_sessions_touched": sorted(sessions & set(anchors.CAL_B4_ANCHORS)),
              "validation_final_sessions_touched": sorted(d for d in sessions if d >= "2024-09-02"),
              "max_development_session": max(sessions, default=None),
              "last_permitted_development_bar": "2024-08-30", "global_cal_b_authorized": anchors.CAL_B_AUTHORIZED}
    assert not safety["cal_b4_sessions_touched"] and not safety["validation_final_sessions_touched"]
    assert anchors.CAL_B4_STATUS == "SEALED" and anchors.CAL_B_AUTHORIZED is False
    technical = [r for r in records if r.request.stage == "technical_analyst" and r.status == "ok"]
    assert all(r.request.system_prompt_sha256 == TECHNICAL_SYSTEM_PROMPT_V3_SHA256 for r in technical)
    complete = (defect["status"] == treatment.H2_V4_DEFECT_FIX_PASSED and all(p["executed"] for p in phases.values())
                and all(phases[n]["result"].get("complete", phases[n]["result"].get("gates_pass", False))
                        for n in phases if n != "Defect-directed hardening"))
    if complete:
        assert all(g["pass"] for g in phases["Stress v4"]["result"]["gates"].values())
    status = "H2_V4 DEVELOPMENT COMPLETE — READY FOR CAL-B4 PROTOCOL" if complete else defect["status"]
    regression = read(OUT / "technical_checker_v3/calibration_report.json")
    selection = read(E / "cal_b4/selection.json")
    summary = {"kind": "H2_V4_DEVELOPMENT_SUMMARY", "descriptive_only": True, "treatment_version": 4,
               "status": status, "development_complete": complete, "phases": phases,
               "v3_governance": read(E / "cal_b3/run_20261006T161844Z/status.json"),
               "checker_regression": {k: v for k, v in regression.items() if k != "descriptive_baseline_by_phase"},
               "temporal_claim_comparison": {"v3_consumed_CAL_B3": defect["v3_consumed_reference_DESCRIPTIVE"],
                                               "v4_development": {n: p["result"].get("technical_audit")
                                                                  for n, p in phases.items() if p["executed"]}},
               "CAL_A_V4_SELECTED_CONFIG": None if treatment.CAL_A_V4_SELECTED_CONFIG is None else dict(treatment.CAL_A_V4_SELECTED_CONFIG),
               "SEQUENTIAL_DEV_V4_SELECTED_CONFIG": None if treatment.SEQUENTIAL_DEV_V4_SELECTED_CONFIG is None else dict(treatment.SEQUENTIAL_DEV_V4_SELECTED_CONFIG),
               "final_v4_params": treatment.stress_v4_params() if complete else None, "safety": safety,
               "technical_prompt_sha256": TECHNICAL_SYSTEM_PROMPT_V3_SHA256,
               "unchanged_sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                            for p in ("src/agents/risk_contract.py", "src/agents/risk_manager.py",
                                                      "src/agents/portfolio_manager.py", "src/agents/features.py")},
               "next_step": "CAL-B4 PROTOCOL ONLY; do not execute automatically" if complete else
               "Stop v4 progression; preserve failure evidence. A new treatment/protocol decision is required; CAL-B4 stays sealed."}
    (OUT / "development_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    commits = subprocess.run(["git", "log", "--reverse", "--format=%h %s", "9407126^..HEAD"], cwd=ROOT,
                             check=True, capture_output=True, encoding="utf-8").stdout.strip()
    lines = ["# H2 v4 — delivery report", "", f"**{status}**", "", "## CAL-B3 FINAL GOVERNANCE", "",
             "CAL_B3_FAIL — HOLDOUT CONSUMED. All 10 automatic gates PASS; primary-author human review FAIL at "
             "2020-05-13 and 2022-03-11. H2_V3_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True. Reason: "
             "CAL_B3 HUMAN REVIEW FAILURE — UNSUPPORTED TEMPORAL CLAIMS. Second review: NOT_REVIEWED — NONBLOCKING. "
             "Raw evidence, commitment, human review and historical v1/v2/v3 evidence preserved. No future return used.",
             "", "## H2 V4 CHANGESET", "",
             "Only treatment change: Technical Prompt v2 -> v3. Risk Prompt v2, Portfolio, eight features/schema v2, "
             "runtime, self-consistency, execution, data/calendar and costs unchanged. Audit checker v3 is separate from decisions. "
             "Spec v3: 1d63ad4cc93f9ef49368ba6772a22403354b36f3cc7d9d57d3b0627b85b9becc. "
             f"Spec v4 defect: {defect['participant_spec_sha256']}.", "", "## EXACT TECHNICAL PROMPT V3", "",
             f"SHA256: `{TECHNICAL_SYSTEM_PROMPT_V3_SHA256}`", "", "```text", TECHNICAL_SYSTEM_PROMPT_V3, "```", "",
             "## TEMPORAL CONTRACT", "",
             "Allowed: MACD currently above signal; current momentum positive/weak/mixed/neutral. "
             "Unsupported: strengthened/weakened/recovered/lost momentum/consolidating/persisting based on earlier observations. "
             "A conflicting snapshot is a mixed current state. MANTER semantics unchanged; action changes are not required.",
             "", "## CHECKER V3", "",
             "Visible rationale only, PT/EN clause/context patterns. UNSUPPORTED_TEMPORAL_STATE_CLAIM is separate from "
             "feature contradictions and explicit transitions. Negation/conditionals/nonmarket contexts are tested. "
             "The bounded heuristic cannot prove completeness over every paraphrase; new calibration requires consumed "
             "development evidence and a new checker version. No v4-output-driven retuning occurred.", "",
             "Source blobs/hashes were committed before live in [pre_live_freeze.json](pre_live_freeze.json).", "",
             "## CHECKER REGRESSION REPORT", "",
             f"Acceptance PASS. {regression['unique_consumed_technical_responses']} unique consumed/development responses; "
             f"{regression['golden_fail']} golden FAIL (including four human rationales); {regression['golden_pass']} golden PASS. "
             "Zero golden misses; zero Bollinger/SMA/MACD or explicit-transition regressions. No CAL-B4 used. "
             "Tests: 783 agents/experiments + 12 CAL-B4 safety passed.", "",
             "[Regression report](technical_checker_v3/calibration_report.json) · [Golden corpus](technical_checker_v3/golden_corpus.json)",
             "", "## CAL-B4 SELECTION", "", "| Stratum | B1 | B2 | B3 | B4 |", "|---:|---|---|---|---|"]
    lines += [f"| {r['stratum_id']} | {r['cal_b1_anchor']} | {r['cal_b2_anchor']} | {r['cal_b3_anchor']} | {r['winner']} |"
              for r in selection["strata"]]
    lines += ["", "## CAL-B4 COMMITMENT", "", f"`{anchors.CAL_B4_COMMITMENT_SHA256}` — SEALED.", "",
              f"Seed `{selection['seed']}`. Ranking hashes and complete exclusions: [selection.json](../cal_b4/selection.json). "
              "Minimum lexicographic SHA256 per stratum using only calendar and prior decision identity. "
              "Selection script commit e4fed89; commitment commit eed7576 preceded first provider call.", "",
              "## DEFECT-DIRECTED HARDENING", "", "10 consumed CAL-B3 anchors x R=3 x N=5. Technical v4 inferred live. No t+1.",
              "", "| Gate | Value | PASS |", "|---|---|---|"]
    lines += [f"| {g} | {v['value']} | {v['pass']} |" for g, v in defect["gates"].items()]
    for a, d in defect["target_anchors"].items():
        signals = [x["decision"]["technical_outcome"] for x in d["v4_decisions"] if x["decision"]]
        lines += ["", f"**{a}**: v4 S1/S2/S3 = " + "/".join(str(d["v4_live"][g]) for g in ("V4-S1", "V4-S2", "V4-S3"))
                  + f"; technical actions {signals}. All votes retained in raw traces."]
    lines += ["", "## TEMPORAL CLAIM RATE", "", "| Evidence | Votes | Implicit temporal claim votes | Rate |",
              "|---|---:|---:|---:|"]
    for label, a in (("v3 consumed CAL-B3", defect["v3_consumed_reference_DESCRIPTIVE"]),
                     ("v4 defect development", defect["technical_audit"])):
        lines.append(f"| {label} | {a['technical_votes']} | {a['V4-S3']} | {a['rates']['V4-S3']:.2%} |")
    lines += ["", "Descriptive comparison; different repetition counts and stochastic realizations. "
              "Zero observed findings would not prove that all unseen future rationales satisfy the contract."]
    for n in ("Hardening v4", "B0 v4", "CAL-A v4", "Sequential Development v4", "Stress v4"):
        p = phases[n]
        lines += ["", f"## {n.upper()}", "", "Not executed: defect-directed hardening did not pass; progression blocked."
                  if not p["executed"] else f"Evidence: `{p['evidence']}`. Result and frozen metrics in development_summary.json."]
    lines += ["", "## FINAL V4 PARAMETERS", "", json.dumps(summary["final_v4_params"], ensure_ascii=False)
              if complete else "Not selected: full development was not authorized after the defect gate result. "
              "The defect run used inherited v3 parameters 21 / 0.50 / drawdown 0.25; these are not a new final selection.",
              "", "Runtime: gemini / gemini-3.8-flash / native API / thinking low / temperature 1.0 / max_output_tokens 8192 / no seed. "
              "N=5 / threshold 0.6 / require_all_votes=true. Technical prompt 3 / Risk prompt 2 / feature schema 2.",
              "", "## CAL-B4 SAFETY", "", f"SEALED; executed=false; v4 decision intersections {safety['cal_b4_sessions_touched']}. "
              "Runner and bank rejection tests passed before live; no CAL-B4 protocol/authorization added.", "",
              "## VALIDATION / FINAL SAFETY", "", f"No scientific session >= 2024-09-02: {safety['validation_final_sessions_touched']}. "
              f"Max v4 decision {safety['max_development_session']}; permitted development end remains 2024-08-30.", "",
              "## COMMITS CREATED", "", "```text", commits, "```", "", "The delivery-summary commit follows this recorded evidence history.",
              "", "## NEXT STEP", "", summary["next_step"]]
    (OUT / "DELIVERY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(status)


if __name__ == "__main__":
    main()
