"""Offline checker acceptance: consumed/development evidence only, never CAL-B4."""

import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from h2_v3_summary import phases, sealed  # noqa: E402
from h2_v4 import CHECKER_FILES, technical_audit  # noqa: E402

from src.agents import feature_semantics as v3  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.experiments import anchors, cal_b  # noqa: E402
from tests.agents.test_feature_semantics import BASE  # noqa: E402
from tests.agents.test_temporal_contract import FAIL, PASS  # noqa: E402

OUT = ROOT / "docs/evidence/h2_v4/technical_checker_v3"
V2_BLOB = "7a086701afda203a415cf1f9b67912d4788b3e56"


def main():
    old = types.ModuleType("technical_checker_v2")
    source = subprocess.run(["git", "cat-file", "-p", V2_BLOB], cwd=ROOT, check=True,
                            capture_output=True, encoding="utf-8").stdout
    exec(compile(source, "technical_checker_v2.py", "exec"), old.__dict__)
    corpus = [{"source": "synthetic PT/EN", "text": text, "expected_temporal_fail": expected}
              for texts, expected in ((FAIL, True), (PASS, False)) for text in texts]
    data = phases()
    data["v3 CAL-B3 (consumed, primary review FAIL)"] = sealed(ROOT / cal_b.CAL_B3_EVIDENCE, anchors.CAL_B3_ANCHORS)
    seen, regressions, baseline = set(), [], {}
    golden = []
    for name, phase in data.items():
        records = []
        for path in phase["risk_traces"]:
            for r in load_trace(path.read_bytes()):
                if r.request.stage != "technical_analyst" or r.status != "ok":
                    continue
                records.append(r)
                key = (r.request.identity_digest, r.provider_response_id)
                if key in seen:
                    continue
                seen.add(key)
                text = r.validated_response["justification"]
                features = json.loads(r.request.user_prompt.splitlines()[0].removeprefix("Features: "))
                before = old.audit_rationale(text, features)
                after = [f for f in v3.audit_rationale(text, features)
                         if f["claim"] != v3.UNSUPPORTED_TEMPORAL_STATE_CLAIM]
                if before != after:
                    regressions.append({"call_id": r.call_id, "source": name})
                item = {"source": name, "decision_session": r.request.decision_session,
                        "analyst_id": r.request.analyst_id, "call_id": r.call_id, "text": text,
                        "features": features, "observed_temporal_findings": v3.temporal_state_claims(text)}
                corpus.append(item)
                if name.startswith("v3 CAL-B3") and (r.request.decision_session, r.request.analyst_id) in {
                    ("2020-05-13", 3), ("2020-05-13", 5), ("2022-03-11", 1), ("2022-03-11", 4)
                }:
                    item["expected_temporal_fail"] = True
                    golden.append(item)
        baseline[name] = {k: v for k, v in technical_audit(records).items() if k != "flagged"}
    misses = [i for i in corpus if "expected_temporal_fail" in i
              and bool(v3.temporal_state_claims(i["text"])) != i["expected_temporal_fail"]]
    explicit = bool(v3.transitions(v3.audit_rationale("o MACD cruzou acima da linha de sinal", BASE)))
    static = not v3.transitions(v3.audit_rationale("o MACD está acima da linha de sinal", BASE))
    report = {"kind": "TECHNICAL_CHECKER_V3_REGRESSION_REPORT", "checker_version": 3,
              "v2_source_blob": V2_BLOB, "unique_consumed_technical_responses": len(seen),
              "golden_fail": len(FAIL) + len(golden), "golden_pass": len(PASS),
              "human_cal_b3_golden": golden, "golden_misses": misses,
              "semantic_and_explicit_transition_regressions": regressions,
              "state_vs_transition_pass": explicit and static,
              "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in CHECKER_FILES},
              "acceptance_pass": not misses and not regressions and explicit and static and len(golden) == 4,
              "provider_calls": 0, "cal_b4_used": False, "future_returns_used": False,
              "descriptive_baseline_by_phase": baseline}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, value in (("golden_corpus", corpus), ("calibration_report", report)):
        (OUT / f"{name}.json").write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "technical_prompt_v3.txt").write_text(v3.TECHNICAL_SYSTEM_PROMPT_V3, encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("acceptance_pass", "unique_consumed_technical_responses",
                                           "golden_fail", "golden_pass", "golden_misses")}, ensure_ascii=False))
    if not report["acceptance_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
