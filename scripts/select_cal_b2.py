"""Seleção determinística da CAL-B2 (Amendment 8), antes de qualquer chamada v2.

Só identidade e data: seed público derivado do compromisso da CAL-B1, menor
SHA-256 por estrato CAL-B entre as sessões ainda não usadas em development.
Nenhum preço, retorno, volatilidade, feature, resposta de LLM ou regime entra;
o snapshot só fornece o calendário de sessões (o domínio do Amendment 2).

Uso: ``python scripts/select_cal_b2.py`` -> ``docs/evidence/cal_b2/selection.json``.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.experiments import treatment  # noqa: E402
from src.experiments.anchors import (  # noqa: E402
    ANCHOR_DOMAIN_SHA256,
    ANCHOR_SNAPSHOT_ID,
    ANCHOR_WINDOW,
    CAL_A_ANCHORS,
    CAL_B_ANCHORS,
    CAL_B_COMMITMENT_SHA256,
    STRATA,
    digest,
    strata_of,
)
from src.experiments.hardening import H_REAL_SESSIONS  # noqa: E402
from src.experiments.phases import SEQUENTIAL_DEVELOPMENT_END, SEQUENTIAL_DEVELOPMENT_START  # noqa: E402
from src.pipeline.snapshot import load_dataset_snapshot, load_snapshot_frames, verify_snapshot_integrity  # noqa: E402

#: H_real do snapshot anterior (Hardening/B0 superados, Amendment 1): também usadas.
H_REAL_SESSIONS_PRE_AMENDMENT_1 = ("2019-04-08", "2020-06-29", "2021-09-17", "2022-12-07")
OUT = ROOT / "docs" / "evidence" / "cal_b2" / "selection.json"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def evidence_decision_sessions() -> set[str]:
    """Toda sessão de decisão registrada em qualquer evidência de development."""
    sessions: set[str] = set()
    for path in (ROOT / "docs" / "evidence").rglob("decisions.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row = row.get("decision") or row
            if row.get("decision_session"):
                sessions.add(row["decision_session"])
    return sessions


def main() -> None:
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit before selecting CAL-B2")
    snapshot = load_dataset_snapshot(ROOT / "data" / "snapshots" / ANCHOR_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    index = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"].index  # só o calendário
    low, high = (pd.Timestamp(day) for day in ANCHOR_WINDOW)
    domain = [str(s.date()) for i, s in enumerate(index)
              if low <= s <= high and i + 1 >= 504 and str(s.date()) not in H_REAL_SESSIONS]
    if digest(domain) != ANCHOR_DOMAIN_SHA256 or strata_of(domain) != STRATA:
        sys.exit("domain/strata differ from Amendment 2")
    used = evidence_decision_sessions()
    excluded = (set(CAL_B_ANCHORS) | set(H_REAL_SESSIONS) | set(H_REAL_SESSIONS_PRE_AMENDMENT_1)
                | set(CAL_A_ANCHORS) | used
                | {d for d in domain if SEQUENTIAL_DEVELOPMENT_START <= d <= SEQUENTIAL_DEVELOPMENT_END})
    rows = treatment.select_cal_b2(domain, excluded)
    blocks = treatment.stratum_sessions(domain)
    for row in rows:
        row["old_cal_b1_anchor"] = next(s.anchor for s in STRATA if s.stratum_id == row["stratum_id"])
        row["excluded_sessions"] = sorted(set(blocks[row["stratum_id"]]) & excluded)
    new = tuple(row["winner"] for row in rows)
    assert not set(new) & excluded and len(set(new)) == 10
    selection = {
        "kind": "CAL_B2_DETERMINISTIC_SELECTION", "computed_utc":
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": git("rev-parse", "HEAD"),
        "rule": "SHA256(seed + '|' + stratum_id + '|' + ISO_DATE), lowest digest per CAL-B stratum",
        "seed_formula": "SHA256('HEDGE-FUND-LAB|CAL-B2|' + CAL_B1_COMMITMENT_HASH)",
        "cal_b1_commitment_sha256": CAL_B_COMMITMENT_SHA256,
        "seed": treatment.CAL_B2_SELECTION_SEED,
        "inputs": "session calendar only (no price, return, volatility, feature, LLM response or regime)",
        "domain_sha256": ANCHOR_DOMAIN_SHA256,
        "exclusions": {"cal_b1_anchors": list(CAL_B_ANCHORS), "h_real": list(H_REAL_SESSIONS),
                       "h_real_pre_amendment_1": list(H_REAL_SESSIONS_PRE_AMENDMENT_1),
                       "cal_a_anchors": len(CAL_A_ANCHORS), "evidence_decision_sessions": len(used)},
        "strata": rows,
        "cal_b2_anchors": list(new),
        "cal_b2_commitment_sha256": digest(new),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8", newline="\n")
    for row in rows:
        print(row["stratum_id"], row["old_cal_b1_anchor"], "->", row["winner"], row["candidates"])
    print("commitment", selection["cal_b2_commitment_sha256"])


if __name__ == "__main__":
    main()
