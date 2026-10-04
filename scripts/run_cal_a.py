"""CAL-A do H2 (Amendment 3): 20 âncoras x R=3 x 6 configurações, pareadas.

Cada avaliação (âncora, repetição, configuração) é um run de âncora normal do
``ExperimentRunner`` (decisão em close(t), execução em open(t+1), CostSpec
congelado, capital em caixa). O que este script acrescenta é o **banco de
chamadas** por ``LLMCallRequest.identity()`` dentro de cada repetição:

- a primeira chamada com uma identidade vai ao provedor e é guardada;
- qualquer chamada posterior com a MESMA identidade, na mesma repetição,
  reproduz a resposta e a evidência do provedor guardadas;
- identidade diferente (ex.: ``recent_volatility`` diferente no prompt do risco
  por causa da janela) é chamada própria, nunca igualada à força.

Como o prompt técnico não depende da grade, as seis configurações de uma
(âncora, repetição) reutilizam a mesma realização técnica de 5 chamadas.

Uso: ``python scripts/run_cal_a.py``. Grava os runs em ``data/runs`` (ignorado,
para não sujar a árvore durante a execução) e copia tudo para
``docs/evidence/cal_a/`` no fim.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_h2_hardening import AttemptLog, load_key  # noqa: E402

import src.agents.participant as participant_module  # noqa: E402
from src.agents.llm_client import (  # noqa: E402
    GeminiLLMClient,
    LLMCallMetadata,
    current_call_telemetry,
)
from src.agents.llm_trace import (  # noqa: E402
    STAGE_UNDECLARED,
    LLMCallRequest,
    _jsonable_options,
    load_trace,
    schema_digest,
    schema_name,
    session_key,
)
from src.artifacts import canonical_json  # noqa: E402
from src.experiments import anchors  # noqa: E402
from src.experiments.anchors import (  # noqa: E402
    ANCHOR_SNAPSHOT_ID,
    CAL_A_ANCHORS,
    CAL_A_COMMITMENT_SHA256,
    CAL_A_COST_SPEC,
    CAL_A_GRID,
    CAL_A_INITIAL_CAPITAL,
    CAL_A_MINIMUM_HISTORY_SESSIONS,
    CAL_A_REPETITIONS,
    CAL_B_ANCHORS,
    CAL_B_COMMITMENT_SHA256,
    digest,
)
from src.experiments.context import RunContext  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FROZEN_THINKING_LEVEL,
    h2_freeze_v1_params,
)
from src.experiments.runner import ExperimentRunner  # noqa: E402
from src.experiments.spec import (  # noqa: E402
    CostSpec,
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
)


class CallBank:
    """Respostas por (repetição, identity_digest) e a proveniência de cada uso."""

    def __init__(self) -> None:
        self.entries: dict[tuple[int, str], dict[str, Any]] = {}
        self.uses: list[dict[str, Any]] = []
        self.context: dict[str, Any] = {}

    @property
    def replicate(self) -> int:
        return int(self.context["replicate"])


BANK = CallBank()
ATTEMPTS = AttemptLog(timeout=120.0)


class BankedGeminiClient(GeminiLLMClient):
    """Cliente Gemini nativo com o banco de chamadas científico na frente."""

    def __init__(self, model: str = "", **kwargs: Any) -> None:
        super().__init__(model=model, transport=ATTEMPTS, **kwargs)
        self._session: str | None = None

    def begin_session(self, session: Any) -> None:
        self._session = session_key(session)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        declared = metadata or LLMCallMetadata(stage=STAGE_UNDECLARED)
        if self._session is None:
            raise RuntimeError("call bank needs a declared decision session")
        if self._session in CAL_B_ANCHORS:
            raise RuntimeError(f"CAL-B session {self._session} must never reach the call bank")
        request = LLMCallRequest(
            stage=declared.stage,
            analyst_id=declared.analyst_id,
            decision_session=self._session,
            provider="gemini",
            requested_model=self.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        key = (BANK.replicate, request.identity_digest)
        slot = current_call_telemetry()
        use = {**BANK.context, "stage": request.stage, "analyst_id": request.analyst_id,
               "identity_digest": request.identity_digest}
        hit = BANK.entries.get(key)
        if hit is not None:
            if slot is not None:
                for name, value in hit["evidence"].items():
                    setattr(slot, name, value)
            BANK.uses.append({**use, "source": "bank", "first_use": hit["first_use"]})
            if response_schema is None:
                return hit["response"]
            # Objeto novo a cada uso: o nó de risco muta ``risk_metrics``.
            return response_schema.model_validate(hit["response"])

        response = await super().generate(
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )
        evidence = {}
        if slot is not None:
            evidence = {
                name: getattr(slot, name)
                for name in ("provider_response_id", "resolved_model", "finish_reason",
                             "raw_response", "usage", "transport_system_prompt")
            }
        BANK.entries[key] = {
            "response": response.model_dump(mode="json") if isinstance(response, BaseModel) else response,
            "evidence": evidence,
            "first_use": dict(BANK.context),
        }
        BANK.uses.append({**use, "source": "live", "usage": evidence.get("usage")})
        return response


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def spec_for(anchor: str, config: dict[str, Any]) -> ExperimentSpec:
    params = {
        "ticker": "PETR4.SA",
        **h2_freeze_v1_params(H2_FROZEN_THINKING_LEVEL),
        "volatility_window": config["volatility_window"],
        "risk_max_volatility": config["risk_max_volatility"],
    }
    return ExperimentSpec(
        snapshot_id=ANCHOR_SNAPSHOT_ID,
        participant=ParticipantSpec("llm_agent", params),
        initial_capital=CAL_A_INITIAL_CAPITAL,
        costs=CostSpec(**CAL_A_COST_SPEC),
        metrics=MetricSpec(),
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start=anchor,
            decision_end=anchor,
            minimum_history_sessions=CAL_A_MINIMUM_HISTORY_SESSIONS,
        ),
    )


def carried_blocks(previous: Path | None) -> tuple[list[dict], list[dict], list[dict]]:
    """Blocos (âncora, repetição) COMPLETOS de uma execução abortada (Amendment 4).

    Um bloco pareado só é aproveitado com as seis configurações: as seis
    compartilham a mesma realização técnica. Bloco parcial é descartado e
    reexecutado inteiro.
    """
    if previous is None:
        return [], [], []
    summary = json.loads((previous / "summary.json").read_text(encoding="utf-8"))
    if summary["git_commit"] is None or summary["complete"]:
        sys.exit("--resume needs an aborted CAL-A run")
    counts = Counter((e["anchor"], e["replicate"]) for e in summary["evaluations"])
    kept = {block for block, n in counts.items() if n == len(CAL_A_GRID)}
    root = previous.relative_to(ROOT).as_posix() + "/runs"
    evaluations = [
        {**e, "runs_root": root, "carried_from": previous.name}
        for e in summary["evaluations"]
        if (e["anchor"], e["replicate"]) in kept
    ]
    uses = [
        json.loads(line)
        for line in (previous / "call_bank.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    uses = [u for u in uses if (u["anchor"], u["replicate"]) in kept]
    attempts = [
        json.loads(line)
        for line in (previous / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    return evaluations, uses, attempts


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=Path, default=None)
    args = parser.parse_args()
    previous = None if args.resume is None else (ROOT / args.resume).resolve()
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit before CAL-A")
    if anchors.CAL_B_AUTHORIZED is not False:
        sys.exit("CAL-B must be locked before CAL-A")
    if digest(CAL_A_ANCHORS) != CAL_A_COMMITMENT_SHA256 or digest(CAL_B_ANCHORS) != CAL_B_COMMITMENT_SHA256:
        sys.exit("anchor commitments do not match")
    load_key()
    commit = git("rev-parse", "HEAD")
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    runs_dir = ROOT / "data" / "runs" / f"cal_a_{stamp}"
    # O participante constrói o cliente pelo registro de provedores: o banco
    # entra no lugar do cliente nativo, por baixo do retry e da gravação.
    participant_module.PROVIDER_CLIENTS["gemini"] = BankedGeminiClient  # type: ignore[index]

    evaluations, carried_uses, prior_attempts = carried_blocks(previous)
    BANK.uses.extend(carried_uses)
    carried = {(e["anchor"], e["replicate"]) for e in evaluations}
    new_root = f"docs/evidence/cal_a/run_{stamp}/runs"
    failure: str | None = None
    total = len(CAL_A_ANCHORS) * CAL_A_REPETITIONS * len(CAL_A_GRID)
    clock = time.perf_counter()
    try:
        for a_index, anchor in enumerate(CAL_A_ANCHORS, 1):
            for replicate in range(1, CAL_A_REPETITIONS + 1):
                if (anchor, replicate) in carried:
                    continue
                for config in sorted(CAL_A_GRID, key=lambda item: item["config_id"]):
                    BANK.context = {"anchor": anchor, "replicate": replicate, "config_id": config["config_id"]}
                    spec = spec_for(anchor, config)
                    runner = ExperimentRunner(
                        spec,
                        context=RunContext("CALIBRATION", f"cal-a-c{config['config_id']}-a{a_index:02d}-r{replicate}"),
                        runs_dir=runs_dir,
                        repository_dir=ROOT,
                    )
                    result, path = runner.run_and_persist()
                    evaluations.append({
                        **BANK.context,
                        "spec_hash": result.spec_hash,
                        "run_id": result.run_id,
                        "run_dir": path.name,
                        "runs_root": new_root,
                        "net_return": result.final_equity / result.initial_capital - 1.0,
                        "trade_count": len(result.trades),
                        "total_transaction_cost": result.total_transaction_cost,
                    })
                    print(f"[{len(evaluations)}/{total}] {anchor} r{replicate} c{config['config_id']} "
                          f"net={evaluations[-1]['net_return']:+.6f}", flush=True)
    except Exception as exc:  # integridade do conjunto perdida: registra e para
        failure = f"{type(exc).__name__}: {exc}"
        print("CAL-A STOPPED:", failure, flush=True)

    finished = datetime.now(timezone.utc)
    out = ROOT / "docs" / "evidence" / "cal_a" / f"run_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    if runs_dir.exists():
        shutil.copytree(runs_dir, out / "runs")

    order = {anchor: i for i, anchor in enumerate(CAL_A_ANCHORS)}
    evaluations.sort(key=lambda e: (order[e["anchor"]], e["replicate"], e["config_id"]))
    complete = failure is None and len(evaluations) == total
    summary: dict[str, Any] = {
        "resumed_from": None if previous is None else previous.name,
        "carried_evaluations": sum(1 for e in evaluations if e.get("carried_from")),
        "kind": "CAL_A",
        "started_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "finished_utc": finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "git_commit": commit,
        "snapshot_id": ANCHOR_SNAPSHOT_ID,
        "cal_a_commitment": CAL_A_COMMITMENT_SHA256,
        "cal_b_commitment": CAL_B_COMMITMENT_SHA256,
        "cal_b_authorized": anchors.CAL_B_AUTHORIZED,
        "grid": list(CAL_A_GRID),
        "repetitions": CAL_A_REPETITIONS,
        "cost_spec": CAL_A_COST_SPEC,
        "complete": complete,
        "failure": failure,
        "evaluations": evaluations,
    }

    if complete:
        by = defaultdict(list)
        for item in evaluations:
            by[(item["config_id"], item["anchor"])].append(item["net_return"])
        anchor_scores = {
            str(c["config_id"]): {a: sum(by[(c["config_id"], a)]) / CAL_A_REPETITIONS for a in CAL_A_ANCHORS}
            for c in CAL_A_GRID
        }
        s1 = {cid: sum(scores.values()) / len(CAL_A_ANCHORS) for cid, scores in anchor_scores.items()}
        ranking = sorted(s1, key=lambda cid: (-s1[cid], int(cid)))
        values = list(s1.values())
        summary.update({
            "anchor_scores": anchor_scores,
            "S1": s1,
            "ranking": [int(cid) for cid in ranking],
            "selected_config_id": int(ranking[0]),
            "tie_at_top": sum(1 for v in values if v == s1[ranking[0]]) > 1,
            "cal_a_discrimination": "NONE" if len(set(values)) == 1 else "YES",
        })

    # Proveniência do banco e diagnósticos operacionais (sem efeito na seleção).
    live = [u for u in BANK.uses if u["source"] == "live"]
    tokens = Counter()
    for u in live:
        for k, v in (u.get("usage") or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tokens[k] += v
    traces = []
    for item in evaluations:
        traces.extend((item, r) for r in load_trace((ROOT / item["runs_root"] / item["run_dir"] / "llm_calls.jsonl").read_bytes()))
    by_config = defaultdict(Counter)
    for item, record in traces:
        by_config[item["config_id"]][record.request.stage] += 1
    paired = defaultdict(set)
    for item, record in traces:
        if record.request.stage == "technical_analyst":
            paired[(item["anchor"], item["replicate"])].add(
                (item["config_id"], record.request.analyst_id, record.provider_response_id,
                 hashlib.sha256(json.dumps(record.validated_response, sort_keys=True).encode()).hexdigest())
            )
    pairing_ok = all(
        len({(aid, rid, h) for _, aid, rid, h in rows}) == 5 for rows in paired.values()
    ) and all(len({c for c, *_ in rows}) == len(CAL_A_GRID) for rows in paired.values())
    # Tentativas desta execução e as da execução abortada retomada (operacional).
    all_attempts = prior_attempts + ATTEMPTS.attempts
    latencies = sorted(a["latency_ms"] for a in all_attempts)
    summary["operational"] = {
        "logical_calls_in_traces": len(traces),
        "logical_calls_by_config_and_stage": {str(k): dict(v) for k, v in sorted(by_config.items())},
        "live_calls": len(live),
        "live_calls_by_stage": dict(Counter(u["stage"] for u in live)),
        "bank_hits": len(BANK.uses) - len(live),
        "http_attempts": len(all_attempts),
        "http_attempts_in_aborted_run": len(prior_attempts),
        "attempt_outcomes": dict(Counter(a["outcome"] for a in all_attempts)),
        "http_status_counts": dict(Counter(str(a.get("status")) for a in all_attempts if a.get("status"))),
        "attempt_latency_ms": {
            "p50": latencies[len(latencies) // 2] if latencies else None,
            "p90": latencies[int(len(latencies) * 0.9)] if latencies else None,
        },
        "live_token_usage": dict(tokens),
        "cost": "not computed: no versioned API pricing source in the repository",
        "wall_clock_seconds": round(time.perf_counter() - clock, 1),
    }
    summary["paired_technical_audit"] = {
        "anchor_replicates": len(paired),
        "same_five_technical_responses_in_all_configs": pairing_ok,
    }
    summary["cal_b_audit"] = {
        "bank_sessions": sorted({u["anchor"] for u in BANK.uses}),
        "cal_b_sessions_touched": sorted({u["anchor"] for u in BANK.uses} & set(CAL_B_ANCHORS)),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    (out / "call_bank.jsonl").write_text("".join(canonical_json(u) + "\n" for u in BANK.uses), encoding="utf-8")
    (out / "attempts.jsonl").write_text("".join(canonical_json(a) + "\n" for a in ATTEMPTS.attempts), encoding="utf-8")
    print(out.as_posix())
    print(json.dumps({k: summary.get(k) for k in ("complete", "failure", "S1", "ranking", "selected_config_id",
                                                     "tie_at_top", "cal_a_discrimination", "paired_technical_audit",
                                                     "cal_b_audit")}, indent=1, default=str))
    if not complete:
        sys.exit(1)


if __name__ == "__main__":
    main()
