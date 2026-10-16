"""Resumo de development do H2 v3 (Amendment 10), só com evidência publicada.

Compara, apenas descritivamente, v1/v2 x v3 por fase: taxas do checker do Risk
(limiar de confidence inventado, regra numérica inventada, contradição
rationale/veredito) sobre as respostas únicas do Risk LLM, vereditos do Risk,
TECH_EXPLICIT_HOLD e total de HOLD; soma a auditoria do replay do Technical v2;
e audita que nenhuma decisão v3 tocou a CAL-B3 nem dados de Validation/Final.
Nenhuma chamada ao provedor.

Uso: ``python scripts/h2_v3_summary.py`` -> ``docs/evidence/h2_v3/development_summary.json``.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from h2_v2_summary import profile  # noqa: E402
from h2_v3 import risk_audit  # noqa: E402

from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.phases import (  # noqa: E402
    SEQUENTIAL_DEVELOPMENT_END,
    VALIDATION_START,
)

E = ROOT / "docs" / "evidence"
OUT = E / "h2_v3" / "development_summary.json"


def hard(d: Path) -> dict[str, Any]:
    rows = [json.loads(x) for x in (d / "decisions.jsonl").read_text(encoding="utf-8").splitlines() if x]
    traces = sorted((d / "traces").glob("*.jsonl"))
    return {"traces": traces, "risk_traces": traces, "decisions": [r["decision"] for r in rows if r["decision"]],
            "manifest": d / "manifest.json"}


def runner(summary: Path, key: str) -> dict[str, Any]:
    """Holds sobre a config 1 (como no resumo v2); Risk sobre todas as configurações."""
    items = json.loads(summary.read_text(encoding="utf-8"))[key]
    dirs = [ROOT / i["runs_root"] / i["run_dir"] for i in items]
    first = [ROOT / i["runs_root"] / i["run_dir"] for i in items if i.get("config_id", 1) == 1]
    return {"traces": [d / "llm_calls.jsonl" for d in first], "risk_traces": [d / "llm_calls.jsonl" for d in dirs],
            "decisions": [json.loads(x) for d in first for x in (d / "decisions.jsonl").read_text(encoding="utf-8")
                          .splitlines() if x and json.loads(x).get("eligible", True)],
            "manifest": summary}


def sealed(run: Path, dates: tuple[str, ...]) -> dict[str, Any]:
    paths = [run / "anchors" / a / "llm_calls.jsonl" for a in dates]
    return {"traces": paths, "risk_traces": paths, "manifest": None,
            "decisions": [json.loads((run / "anchors" / a / "decisions.jsonl").read_text(encoding="utf-8")
                                     .splitlines()[0]) for a in dates]}


def phases() -> dict[str, dict[str, Any]]:
    def latest(pattern: str) -> Path:
        return sorted(E.glob(pattern))[-1]

    return {
        "v1 Hardening": hard(E / "h2" / "hardening_low_20261004T201555Z"),
        "v2 Hardening": hard(E / "h2_v2" / "hardening_low_20261006T022444Z"),
        "v3 Hardening": hard(latest("h2_v3/hardening_low_*")),
        "v1 B0": hard(E / "h2" / "b0_low_20261004T202013Z"),
        "v2 B0": hard(E / "h2_v2" / "b0_low_20261006T022838Z"),
        "v3 B0": hard(latest("h2_v3/b0_low_*")),
        "v1 CAL-B1 (sealed one-shot)": sealed(E / "cal_b" / "run_20261005T021523Z", anchors.CAL_B_ANCHORS),
        "v2 defect hardening (CAL-B1 x R=3)": hard(ROOT / Path(treatment.H2_V2_DEFECT_EVIDENCE).parent),
        "v2 CAL-B2 (consumed one-shot, now development)": sealed(ROOT / treatment.FROZEN_V2_EVIDENCE["defect"],
                                                                 anchors.CAL_B2_ANCHORS),
        "v3 defect hardening (CAL-B2 x R=3)": hard(ROOT / Path(treatment.H2_V3_DEFECT_EVIDENCE).parent),
        "v1 CAL-A": runner(E / "cal_a" / "run_20261004T231101Z" / "summary.json", "evaluations"),
        "v2 CAL-A": runner(ROOT / treatment.CAL_A_V2_SELECTED_CONFIG["evidence"], "evaluations"),
        "v3 CAL-A": runner(ROOT / treatment.CAL_A_V3_SELECTED_CONFIG["evidence"], "evaluations"),
        "v1 Sequential Dev": runner(E / "sequential_dev" / "run_20261004T235634Z" / "summary.json", "evaluations"),
        "v2 Sequential Dev": runner(ROOT / treatment.SEQUENTIAL_DEV_V2_SELECTED_CONFIG["evidence"], "evaluations"),
        "v3 Sequential Dev": runner(ROOT / treatment.SEQUENTIAL_DEV_V3_SELECTED_CONFIG["evidence"], "evaluations"),
        "v1 Stress": runner(E / "stress" / "run_20261005T011248Z" / "summary.json", "trajectories"),
        "v2 Stress": runner(ROOT / treatment.STRESS_V2_EVIDENCE, "trajectories"),
        "v3 Stress": runner(ROOT / treatment.STRESS_V3_EVIDENCE, "trajectories"),
    }


def risk_profile(phase: dict[str, Any]) -> dict[str, Any]:
    records = [r for p in phase["risk_traces"] for r in load_trace(p.read_bytes())]
    audit = risk_audit(records)
    n = audit["risk_llm_responses"]
    return {"risk_llm_responses": n, "risk_verdicts": audit["verdicts"],
            "risk_llm_veto_rate": round(audit["verdicts"].get("VETADO", 0) / n, 4) if n else None,
            **{f"{gate}_count": audit[gate] for gate in ("V3-R1", "V3-R2", "V3-R3")},
            "unsupported_confidence_threshold_rate": None if n is None or not n else round(audit["V3-R1"] / n, 4),
            "unsupported_numeric_rule_rate": None if not n else round(audit["V3-R2"] / n, 4),
            "contradiction_rate": None if not n else round(audit["V3-R3"] / n, 4),
            "flagged_v3_only": [{k: f[k] for k in ("decision_session", "verdict", "analysis")}
                                | {"codes": sorted({x["code"] for x in f["findings"]})} for f in audit["flagged"]]
            if audit["risk_prompt_v2_only"] and n else None}


def replay(phase: dict[str, Any]) -> dict[str, Any] | None:
    if phase["manifest"] is None:
        return None
    m = json.loads(phase["manifest"].read_text(encoding="utf-8"))
    return m.get("replay_audit") or m["frozen_component_replay"]  # no defect, a outra chave é a política


def main() -> None:
    profiles: dict[str, dict[str, Any]] = {}
    v3_sessions: set[str] = set()
    replay_total: Counter = Counter()
    mismatches = 0
    for name, phase in phases().items():
        p = {**profile(phase), **risk_profile(phase)}
        if name.startswith("v3"):
            v3_sessions |= p["_sessions"] | {r.request.decision_session for t in phase["risk_traces"]
                                             for r in load_trace(t.read_bytes())}
            audit = replay(phase)
            p["technical_replay"] = {k: audit[k] for k in ("replayed", "live", "mismatch",
                                                           "technical_prompt_v2_byte_identical")}
            replay_total.update({f"{stage}/{k}": n for k in ("replayed", "live", "mismatch")
                                 for stage, n in audit[k].items()})
            mismatches += sum(audit["mismatch"].values())
        p.pop("_sessions")
        profiles[name] = p
    v3_dev = [p for k, p in profiles.items() if k.startswith("v3")]
    stress_v3 = json.loads((ROOT / treatment.STRESS_V3_EVIDENCE).read_text(encoding="utf-8"))
    summary = {
        "kind": "H2_V3_DEVELOPMENT_SUMMARY", "descriptive_only": True,
        "treatment_version": treatment.H2_TREATMENT_VERSION,
        "v2_governance": {"CAL_B2_HISTORICAL_STATUS": treatment.CAL_B2_HISTORICAL_STATUS,
                          "H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE": treatment.H2_V2_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE,
                          "reason": treatment.H2_V2_SYSTEM_FREEZE_INELIGIBILITY_REASON},
        "phases": profiles,
        "risk_checker_totals_v3_development": {
            "risk_llm_responses": sum(p["risk_llm_responses"] for p in v3_dev),
            "V3-R1": sum(p["V3-R1_count"] for p in v3_dev), "V3-R2": sum(p["V3-R2_count"] for p in v3_dev),
            "V3-R3": sum(p["V3-R3_count"] for p in v3_dev),
            "risk_verdicts": dict(sum((Counter(p["risk_verdicts"]) for p in v3_dev), Counter())),
        },
        # Observação, sem autoridade: sem regra inventada, o Risk LLM v3 não vetou nada no development.
        "risk_llm_verdicts_by_version_OBSERVATION": {
            v: dict(sum((Counter(p["risk_verdicts"]) for k, p in profiles.items() if k.startswith(v)), Counter()))
            for v in ("v1", "v2", "v3")},
        "frozen_component_replay": {"policy": treatment.FROZEN_COMPONENT_REPLAY, "totals": dict(replay_total),
                                    "mismatches": mismatches},
        "selections": {"CAL-A v3": dict(treatment.CAL_A_V3_SELECTED_CONFIG),
                       "Sequential Dev v3": dict(treatment.SEQUENTIAL_DEV_V3_SELECTED_CONFIG)},
        "final_v3_params": treatment.stress_v3_params(),
        "stress_v3": {"gates": stress_v3["gates"], "coverage": stress_v3["coverage"], "status": stress_v3["status"]},
        "cal_b3_safety": {"anchors": list(anchors.CAL_B3_ANCHORS), "commitment": anchors.CAL_B3_COMMITMENT_SHA256,
                          "status": anchors.CAL_B3_STATUS,
                          "v3_decision_sessions_in_cal_b3": sorted(v3_sessions & set(anchors.CAL_B3_ANCHORS)),
                          "executed": False},
        "validation_final_safety": {"validation_start": VALIDATION_START,
                                    "v3_sessions_at_or_after_validation": sorted(s for s in v3_sessions
                                                                                 if s >= VALIDATION_START),
                                    "max_v3_session": max(v3_sessions),
                                    "sequential_development_end": SEQUENTIAL_DEVELOPMENT_END},
    }
    ok = (not summary["cal_b3_safety"]["v3_decision_sessions_in_cal_b3"]
          and not summary["validation_final_safety"]["v3_sessions_at_or_after_validation"]
          and anchors.CAL_B3_STATUS == "SEALED" and mismatches == 0
          and treatment.H2_V3_DEFECT_STATUS == treatment.H2_V3_DEFECT_FIX_PASSED
          and stress_v3["status"].startswith("STRESS PROBING COMPLETE"))
    summary["status"] = "H2_V3 DEVELOPMENT COMPLETE — READY FOR CAL-B3 PROTOCOL" if ok else "H2_V3 DEVELOPMENT INCOMPLETE"
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: summary[k] for k in ("risk_checker_totals_v3_development", "frozen_component_replay",
                                              "cal_b3_safety", "validation_final_safety", "status")},
                     indent=1, ensure_ascii=False))
    for name, p in profiles.items():
        print(f"{name:48s} risk n={p['risk_llm_responses']:3d} veto={p['risk_llm_veto_rate']} "
              f"R1={p['unsupported_confidence_threshold_rate']} R2={p['unsupported_numeric_rule_rate']} "
              f"R3={p['contradiction_rate']} hold={p['total_hold_rate']} explicit={p['tech_explicit_hold_rate']}")


if __name__ == "__main__":
    main()
