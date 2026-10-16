"""CAL-B4 deterministic selection: calendar/identity only; commit before v4 live."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from select_cal_b2 import H_REAL_SESSIONS_PRE_AMENDMENT_1, git  # noqa: E402

from src.experiments import anchors, treatment  # noqa: E402
from src.experiments.hardening import H_REAL_SESSIONS  # noqa: E402
from src.experiments.phases import SEQUENTIAL_DEVELOPMENT_END, SEQUENTIAL_DEVELOPMENT_START  # noqa: E402
from src.pipeline.snapshot import load_dataset_snapshot, load_snapshot_frames, verify_snapshot_integrity  # noqa: E402


def used_sessions() -> set[str]:
    """Identity fields in all development JSONL artifacts, including traces without decisions."""
    used = set()
    for path in (ROOT / "docs/evidence").rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            for item in (row, row.get("decision") or {}, row.get("request") or {}):
                if item.get("decision_session"):
                    used.add(item["decision_session"])
    return used


def main():
    if git("status", "--porcelain"):
        sys.exit("commit the selection script before selecting CAL-B4")
    out = ROOT / anchors.CAL_B4_SELECTION_EVIDENCE
    if out.exists() or anchors.CAL_B4_ANCHORS:
        sys.exit("CAL-B4 already selected: reselection refused")
    snapshot = load_dataset_snapshot(ROOT / "data/snapshots" / anchors.ANCHOR_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    index = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index  # calendar only
    low, high = (pd.Timestamp(d) for d in anchors.ANCHOR_WINDOW)
    domain = [str(s.date()) for i, s in enumerate(index)
              if low <= s <= high and i + 1 >= 504 and str(s.date()) not in H_REAL_SESSIONS]
    if anchors.digest(domain) != anchors.ANCHOR_DOMAIN_SHA256 or anchors.strata_of(domain) != anchors.STRATA:
        sys.exit("domain/strata differ from Amendment 2")
    used = used_sessions()
    excluded = (used | set(anchors.CAL_B_ANCHORS) | set(anchors.CAL_B2_ANCHORS) | set(anchors.CAL_B3_ANCHORS)
                | set(anchors.CAL_A_ANCHORS) | set(H_REAL_SESSIONS) | set(H_REAL_SESSIONS_PRE_AMENDMENT_1)
                | {d for d in domain if SEQUENTIAL_DEVELOPMENT_START <= d <= SEQUENTIAL_DEVELOPMENT_END})
    rows = treatment.select_cal_b2(domain, excluded, seed=treatment.CAL_B4_SELECTION_SEED)
    blocks = treatment.stratum_sessions(domain)
    for row in rows:
        sid = row["stratum_id"]
        row["cal_b1_anchor"] = next(s.anchor for s in anchors.STRATA if s.stratum_id == sid)
        row["cal_b2_anchor"] = next(a for a in anchors.CAL_B2_ANCHORS if a in blocks[sid])
        row["cal_b3_anchor"] = next(a for a in anchors.CAL_B3_ANCHORS if a in blocks[sid])
        row["excluded_sessions"] = sorted(set(blocks[sid]) & excluded)
    new = tuple(r["winner"] for r in rows)
    assert len(set(new)) == 10 and not set(new) & excluded
    selection = {"kind": "CAL_B4_DETERMINISTIC_SELECTION", "computed_utc": datetime.now(timezone.utc).isoformat(),
                 "git_commit": git("rev-parse", "HEAD"), "status": "SEALED",
                 "rule": "SHA256(seed + '|' + stratum_id + '|' + ISO_DATE), lowest digest per CAL-B stratum",
                 "seed_formula": "SHA256('HEDGE-FUND-LAB|CAL-B4|' + CAL_B3_COMMITMENT_HASH)",
                 "seed": treatment.CAL_B4_SELECTION_SEED,
                 "cal_b3_commitment_sha256": anchors.CAL_B3_COMMITMENT_SHA256,
                 "domain_sha256": anchors.ANCHOR_DOMAIN_SHA256,
                 "inputs": "session calendar and prior decision identity only; no feature/return/volatility/regime/LLM output",
                 "excluded_sessions": sorted(excluded), "excluded_sessions_sha256": anchors.digest(sorted(excluded)),
                 "artifact_decision_sessions": len(used), "strata": rows,
                 "cal_b4_anchors": new, "cal_b4_commitment_sha256": anchors.digest(new),
                 "provider_calls_before_commitment": 0, "executed": False}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(r["stratum_id"], r["cal_b1_anchor"], r["cal_b2_anchor"], r["cal_b3_anchor"], r["winner"])
    print("CAL_B4_COMMITMENT_SHA256", anchors.digest(new))


if __name__ == "__main__":
    main()
