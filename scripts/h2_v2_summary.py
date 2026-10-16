"""Resumo de development do H2 v2 (Amendment 8), só com evidência publicada.

Compara, apenas descritivamente, v1 x v2 por fase: contradições semânticas e
transições não suportadas no rationale técnico (checker congelado), taxa de
TECH_EXPLICIT_HOLD e total de HOLD; e audita que nenhuma decisão v2 tocou a
CAL-B2 nem dados de Validation/Final. Nenhuma chamada ao provedor.

Uso: ``python scripts/h2_v2_summary.py`` -> ``docs/evidence/h2_v2/development_summary.json``.
"""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.feature_semantics import audit_rationale, contradictions, transitions  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.hardening import HOLD_RATE_CAUSES  # noqa: E402
from src.experiments.phases import SEQUENTIAL_DEVELOPMENT_END, VALIDATION_START  # noqa: E402

E = ROOT / "docs" / "evidence"
OUT = E / "h2_v2" / "development_summary.json"


def runs(summary: Path, key: str) -> list[Path]:
    items = json.loads(summary.read_text(encoding="utf-8"))[key]
    return [ROOT / i["runs_root"] / i["run_dir"] for i in items if i.get("config_id", 1) == 1]


def phases() -> dict[str, dict[str, Any]]:
    """Por fase: traces (uma realização técnica por estado/repetição) e decisões."""
    def hard(d: Path) -> dict[str, Any]:
        rows = [json.loads(x) for x in (d / "decisions.jsonl").read_text(encoding="utf-8").splitlines() if x]
        return {"traces": sorted((d / "traces").glob("*.jsonl")), "decisions": [r["decision"] for r in rows if r["decision"]]}

    def runner(summary: Path, key: str) -> dict[str, Any]:
        dirs = runs(summary, key)
        return {"traces": [d / "llm_calls.jsonl" for d in dirs],
                "decisions": [json.loads(x) for d in dirs for x in (d / "decisions.jsonl").read_text(encoding="utf-8")
                              .splitlines() if x and json.loads(x).get("eligible", True)]}

    def latest(pattern: str) -> Path:
        return sorted(E.glob(pattern))[-1]

    cal_b1 = E / "cal_b" / "run_20261005T021523Z" / "anchors"
    return {
        "v1 Hardening": hard(E / "h2" / "hardening_low_20261004T201555Z"),
        "v2 Hardening": hard(latest("h2_v2/hardening_low_*")),
        "v1 B0": hard(E / "h2" / "b0_low_20261004T202013Z"),
        "v2 B0": hard(latest("h2_v2/b0_low_*")),
        "v1 CAL-B1 (sealed one-shot)": {
            "traces": [cal_b1 / a / "llm_calls.jsonl" for a in anchors.CAL_B_ANCHORS],
            "decisions": [json.loads((cal_b1 / a / "decisions.jsonl").read_text(encoding="utf-8").splitlines()[0])
                          for a in anchors.CAL_B_ANCHORS]},
        "v2 defect hardening (CAL-B1 x R=3)": hard(ROOT / Path(treatment.H2_V2_DEFECT_EVIDENCE).parent),
        "v1 CAL-A": runner(E / "cal_a" / "run_20261004T231101Z" / "summary.json", "evaluations"),
        "v2 CAL-A": runner(ROOT / treatment.CAL_A_V2_SELECTED_CONFIG["evidence"], "evaluations"),
        "v1 Sequential Dev": runner(E / "sequential_dev" / "run_20261004T235634Z" / "summary.json", "evaluations"),
        "v2 Sequential Dev": runner(ROOT / treatment.SEQUENTIAL_DEV_V2_SELECTED_CONFIG["evidence"], "evaluations"),
        "v1 Stress": runner(E / "stress" / "run_20261005T011248Z" / "summary.json", "trajectories"),
        "v2 Stress": runner(latest("stress_v2/run_*/summary.json"), "trajectories"),
    }


def profile(phase: dict[str, Any]) -> dict[str, Any]:
    votes = c_votes = t_votes = 0
    sessions: set[str] = set()
    for path in phase["traces"]:
        for r in load_trace(path.read_bytes()):
            sessions.add(r.request.decision_session)
            if r.request.stage != "technical_analyst" or not r.request.user_prompt.startswith("Features: "):
                continue
            f = json.loads(r.request.user_prompt.splitlines()[0][len("Features: "):])
            audit = audit_rationale(r.validated_response["justification"], f)
            votes += 1
            c_votes += bool(contradictions(audit))
            t_votes += bool(transitions(audit))
    causes = Counter(d["final_cause"] for d in phase["decisions"])
    n = len(phase["decisions"])
    holds = sum(causes[c] for members in HOLD_RATE_CAUSES.values() for c in members)
    return {"technical_votes": votes, "contradiction_rate": round(c_votes / votes, 4) if votes else None,
            "transition_rate": round(t_votes / votes, 4) if votes else None, "decisions": n,
            "tech_explicit_hold_rate": round(causes["TECH_EXPLICIT_HOLD"] / n, 4) if n else None,
            "total_hold_rate": round(holds / n, 4) if n else None, "_sessions": sessions}


def main() -> None:
    profiles = {name: profile(p) for name, p in phases().items()}
    v2_sessions = set().union(*(p["_sessions"] for k, p in profiles.items() if k.startswith("v2")))
    for p in profiles.values():
        p.pop("_sessions")
    stress_v2 = json.loads(sorted(E.glob("stress_v2/run_*/summary.json"))[-1].read_text(encoding="utf-8"))
    summary = {
        "kind": "H2_V2_DEVELOPMENT_SUMMARY", "descriptive_only": True,
        "h2_v1_status": treatment.H2_V1_STATUS, "treatment_version": treatment.H2_TREATMENT_VERSION,
        "phases": profiles,
        "selections": {
            "CAL-A v2": dict(treatment.CAL_A_V2_SELECTED_CONFIG),
            "Sequential Dev v2": dict(treatment.SEQUENTIAL_DEV_V2_SELECTED_CONFIG),
        },
        "stress_v2": {"gates": stress_v2["gates"], "coverage": stress_v2["coverage"], "status": stress_v2["status"],
                      "frozen_params": stress_v2["frozen_params"]},
        "cal_b2_safety": {"anchors": list(anchors.CAL_B2_ANCHORS), "status": anchors.CAL_B2_STATUS,
                          "v2_decision_sessions_in_cal_b2": sorted(v2_sessions & set(anchors.CAL_B2_ANCHORS)),
                          "executed": False},
        "validation_final_safety": {"validation_start": VALIDATION_START,
                                    "v2_sessions_at_or_after_validation": sorted(s for s in v2_sessions
                                                                                 if s >= VALIDATION_START),
                                    "max_v2_session": max(v2_sessions),
                                    "sequential_development_end": SEQUENTIAL_DEVELOPMENT_END},
    }
    ok = (not summary["cal_b2_safety"]["v2_decision_sessions_in_cal_b2"]
          and not summary["validation_final_safety"]["v2_sessions_at_or_after_validation"]
          and stress_v2["status"].startswith("STRESS PROBING COMPLETE"))
    summary["status"] = "H2_V2 DEVELOPMENT COMPLETE — READY FOR CAL-B2 PROTOCOL" if ok else "H2_V2 DEVELOPMENT INCOMPLETE"
    OUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: summary[k] for k in ("phases", "cal_b2_safety", "validation_final_safety", "status")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
