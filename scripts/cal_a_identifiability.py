"""Gate de identificabilidade de CAL-A (Amendment 2): só veto, sem resultado.

Para cada configuração da grade e cada âncora de CAL-A, calcula a
volatilidade de risco com o mesmo caminho do participante
(``LLMParticipant._agent_state``) sobre o histórico truncado em ``t`` e aplica
a mesma regra dura do gestor de risco (valor canônico de 6 casas,
``vol > risk_max_volatility``). Não chama LLM, não olha ``t+1``, não calcula
retorno.

Uso: ``python scripts/cal_a_identifiability.py``
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.features import canonical_number  # noqa: E402
from src.agents.llm_client import MockLLMClient  # noqa: E402
from src.agents.participant import LLMParticipant  # noqa: E402
from src.experiments.anchors import (  # noqa: E402
    ANCHOR_SNAPSHOT_ID,
    CAL_A_ANCHORS,
    CAL_A_COMMITMENT_SHA256,
    CAL_A_GRID,
    IDENTIFIABILITY_MIN_DISTINGUISHING,
    digest,
)
from src.experiments.hardening import HardeningState, frozen_observation  # noqa: E402
from src.pipeline.snapshot import (  # noqa: E402
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)


def main() -> None:
    if subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip():
        sys.exit("working tree has tracked changes: commit before the gate")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if digest(CAL_A_ANCHORS) != CAL_A_COMMITMENT_SHA256:
        sys.exit("CAL-A anchors do not match their commitment")

    snapshot = load_dataset_snapshot(ROOT / "data" / "snapshots" / ANCHOR_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    if not snapshot.scientific_ready:
        sys.exit("snapshot is not READY")
    frame = load_snapshot_frames(snapshot, ("PETR4.SA",))["PETR4.SA"]

    rows = []
    for anchor in CAL_A_ANCHORS:
        history = frame.loc[:anchor]  # nada depois de t
        close = float(history["fechamento"].iloc[-1])
        state = HardeningState(f"cal-a:{anchor}", "PETR4.SA", history)
        row = {"anchor": anchor, "configs": {}}
        for config in CAL_A_GRID:
            participant = LLMParticipant(
                "PETR4.SA",
                llm_client=MockLLMClient(),
                strict_inputs=True,
                volatility_window=config["volatility_window"],
                risk_max_volatility=config["risk_max_volatility"],
            )
            agent_state = participant._agent_state(
                frozen_observation(state, 100_000.0), history, 100_000.0, close
            )
            violations = participant._input_violations(agent_state, history)
            if violations:
                sys.exit(f"{anchor} config {config['config_id']}: {violations}")
            volatility = canonical_number(agent_state["recent_volatility"])
            row["configs"][str(config["config_id"])] = {
                "volatility": volatility,
                "veto": volatility > config["risk_max_volatility"],
            }
        vetoes = {item["veto"] for item in row["configs"].values()}
        row["distinguishing"] = len(vetoes) > 1
        rows.append(row)

    distinguishing = sum(row["distinguishing"] for row in rows)
    result = "CAL-A REDUCED" if distinguishing >= IDENTIFIABILITY_MIN_DISTINGUISHING else "CAL-A REMOVED"
    vectors = {
        str(c["config_id"]): [row["configs"][str(c["config_id"])]["veto"] for row in rows]
        for c in CAL_A_GRID
    }
    evidence = {
        "kind": "CAL_A_IDENTIFIABILITY_GATE",
        "financial_metrics": "none computed; no t+1, no return, no LLM call",
        "computed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": commit,
        "snapshot_id": ANCHOR_SNAPSHOT_ID,
        "snapshot_identity_digest": snapshot.identity_digest,
        "grid": list(CAL_A_GRID),
        "anchors": rows,
        "veto_vectors": vectors,
        "veto_counts": {key: sum(value) for key, value in vectors.items()},
        "distinguishing_anchors": distinguishing,
        "threshold": IDENTIFIABILITY_MIN_DISTINGUISHING,
        "result": result,
    }
    out = ROOT / "docs" / "evidence" / "cal_a" / "identifiability.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: evidence[k] for k in ("veto_counts", "distinguishing_anchors", "result")}, indent=1))


if __name__ == "__main__":
    main()
