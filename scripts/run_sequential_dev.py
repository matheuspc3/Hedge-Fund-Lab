"""Sequential Development do H2 (Amendment 5): D01-D03 x R=3, pareados.

Cada avaliação (repetição, configuração) é UM run sequencial normal do
``ExperimentRunner`` sobre a fase inteira: decisões de 2024-03-01 a 2024-08-29,
liquidação e marcação final em 2024-08-30, portfólio próprio e dependente do
caminho. O banco de chamadas de ``run_cal_a`` (por repetição e
``LLMCallRequest.identity()``) faz o pareamento:

- o Technical SC de cada (sessão, repetição) é chamado uma vez, em D01, e
  reproduzido byte a byte em D02 e D03 (o prompt técnico não depende da grade);
- Risk/Portfolio só reaproveitam resposta com identidade idêntica; prompt
  diferente (ex.: drawdown diferente porque o caminho divergiu) é chamada nova.

Escore: ``S2[c] = mean(Sharpe[c, 1..3])`` com o Sharpe científico v1.
Retomada: o bloco mínimo é a repetição completa (as três configurações); uma
repetição interrompida é descartada inteira e refeita com Technical novo.

Uso: ``python scripts/run_sequential_dev.py [--resume docs/evidence/sequential_dev/run_X]``.
Runs vão para ``data/runs`` (ignorado) e são copiados para
``docs/evidence/sequential_dev/`` no fim.
"""

import hashlib
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_cal_a import ATTEMPTS, BANK, BankedGeminiClient, git  # noqa: E402
from run_h2_hardening import load_key  # noqa: E402

import src.agents.participant as participant_module  # noqa: E402
from src.agents.llm_trace import load_trace  # noqa: E402
from src.artifacts import canonical_json  # noqa: E402
from src.backtesting import metrics  # noqa: E402
from src.experiments import anchors  # noqa: E402
from src.experiments.anchors import (  # noqa: E402
    ANCHOR_SNAPSHOT_ID,
    CAL_A_COST_SPEC,
    CAL_A_INITIAL_CAPITAL,
    CAL_A_MINIMUM_HISTORY_SESSIONS,
    CAL_A_SELECTED_CONFIG,
    CAL_B_ANCHORS,
)
from src.experiments.context import RunContext  # noqa: E402
from src.experiments.hardening import (  # noqa: E402
    H2_FROZEN_THINKING_LEVEL,
    h2_freeze_v1_params,
)
from src.experiments.phases import (  # noqa: E402
    SEQUENTIAL_DEV_GRID,
    SEQUENTIAL_DEV_REPETITIONS,
    SEQUENTIAL_DEVELOPMENT_END,
    SEQUENTIAL_DEVELOPMENT_LAST_DECISION,
    SEQUENTIAL_DEVELOPMENT_START,
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

OUT_ROOT = ROOT / "docs" / "evidence" / "sequential_dev"
#: Base de volatilidade e extra de tratamento; ``--treatment 2`` (Amendment 8)
#: troca pela seleção da CAL-A v2 e pelo prompt técnico v2.
BASE_VOL: dict[str, Any] = {k: CAL_A_SELECTED_CONFIG[k] for k in ("volatility_window", "risk_max_volatility")}
TREATMENT_EXTRA: dict[str, Any] = {}
#: v3 (Amendment 10): respostas v2 do componente congelado por repetição.
FROZEN: dict[int, dict[str, Any]] = {}
HARD_VETOES = {"RISK_VETO_VOLATILITY", "RISK_VETO_DRAWDOWN", "RISK_VETO_CONCENTRATION"}


def spec_for(config: dict[str, Any]) -> ExperimentSpec:
    params = {
        "ticker": "PETR4.SA",
        **h2_freeze_v1_params(H2_FROZEN_THINKING_LEVEL),
        "volatility_window": BASE_VOL["volatility_window"],
        "risk_max_volatility": BASE_VOL["risk_max_volatility"],
        "risk_max_drawdown": config["risk_max_drawdown"],
        **TREATMENT_EXTRA,
    }
    return ExperimentSpec(
        snapshot_id=ANCHOR_SNAPSHOT_ID,
        participant=ParticipantSpec("llm_agent", params),
        initial_capital=CAL_A_INITIAL_CAPITAL,
        costs=CostSpec(**CAL_A_COST_SPEC),
        metrics=MetricSpec(),
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start=SEQUENTIAL_DEVELOPMENT_START,
            decision_end=SEQUENTIAL_DEVELOPMENT_LAST_DECISION,
            minimum_history_sessions=CAL_A_MINIMUM_HISTORY_SESSIONS,
        ),
    )


def carried_replicates(previous: Path | None) -> tuple[list[dict], list[dict], list[dict]]:
    """Repetições COMPLETAS (D01-D03) de uma execução abortada; o resto é refeito."""
    if previous is None:
        return [], [], []
    summary = json.loads((previous / "summary.json").read_text(encoding="utf-8"))
    if summary["complete"]:
        sys.exit("--resume needs an aborted Sequential Development run")
    if summary["git_commit"] != git("rev-parse", "HEAD"):
        sys.exit("--resume must run on the same freeze commit")
    counts = Counter(e["replicate"] for e in summary["evaluations"])
    kept = {r for r, n in counts.items() if n == len(SEQUENTIAL_DEV_GRID)}
    root = previous.relative_to(ROOT).as_posix() + "/runs"
    evaluations = [
        {**e, "runs_root": e.get("runs_root") if e.get("carried_from") else root,
         "carried_from": e.get("carried_from") or previous.name}
        for e in summary["evaluations"] if e["replicate"] in kept
    ]
    def lines(name: str) -> list[dict]:
        return [json.loads(x) for x in (previous / name).read_text(encoding="utf-8").splitlines()]
    uses = [u for u in lines("call_bank.jsonl") if u["replicate"] in kept]
    return evaluations, uses, lines("attempts.jsonl")


def run_dir(item: dict[str, Any]) -> Path:
    return ROOT / item["runs_root"] / item["run_dir"]


def describe(item: dict[str, Any]) -> dict[str, Any]:
    """Métricas descritivas e auditoria de drawdown, só dos artefatos persistidos.

    NOT USED FOR SELECTION.
    """
    path = run_dir(item)
    curve = pd.read_csv(path / "equity.csv", index_col="date", parse_dates=True)["equity"]
    trades = pd.read_csv(path / "trades.csv")
    decisions = [json.loads(x) for x in (path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    causes = Counter(d["final_cause"] for d in decisions)
    # Drawdown canônico em close(t): pico interno ao run, começando no capital.
    peak = curve.cummax().clip(lower=CAL_A_INITIAL_CAPITAL)
    drawdown = (peak - curve) / peak
    limit = item["risk_max_drawdown"]
    dd_vetoes = [d["decision_session"] for d in decisions if d["final_cause"] == "RISK_VETO_DRAWDOWN"]
    breached_buys = [
        {"session": d["decision_session"], "final_cause": d["final_cause"]}
        for d in decisions
        if d["technical_outcome"] == "COMPRA" and drawdown[pd.Timestamp(d["decision_session"])] > limit
    ]
    above = drawdown[drawdown > limit]
    return {
        "terminal_return": float(curve.iloc[-1] / curve.iloc[0] - 1.0),
        "max_drawdown": metrics.max_drawdown(curve),
        "sortino": metrics.sortino_ratio(metrics.periodic_returns(curve)),
        "turnover_traded_notional_over_capital": float((trades["price"] * trades["quantity"]).abs().sum()
                                                       / CAL_A_INITIAL_CAPITAL),
        "trades": len(trades),
        "time_in_market": sum(1 for d in decisions if d["observed_weight"] > 0) / len(decisions),
        "hard_risk_vetoes": sum(causes[c] for c in HARD_VETOES),
        "llm_risk_vetoes": causes["RISK_VETO_LLM"],
        "final_causes": dict(sorted(causes.items())),
        "decision_sessions": len(decisions),
        "first_decision": decisions[0]["decision_session"],
        "last_decision": decisions[-1]["decision_session"],
        "last_curve_session": str(curve.index[-1].date()),
        "drawdown_audit": {
            "limit": limit,
            "max_canonical_drawdown": float(drawdown.max()),
            "first_session_above_limit": None if above.empty else str(above.index[0].date()),
            "drawdown_vetoes": len(dd_vetoes),
            "drawdown_vetoes_all_above_limit": all(drawdown[pd.Timestamp(s)] > limit for s in dd_vetoes),
            "buys_with_drawdown_above_limit": len(breached_buys),
            "buys_above_limit_by_cause": dict(Counter(b["final_cause"] for b in breached_buys)),
            # O limite veta ENTRADA; não é stop-loss. Já no alvo, a COMPRA é
            # BUY_AT_TARGET_NOOP (sem ordem). Invariante: nenhuma ordem de compra.
            "buy_orders_above_limit": [b["session"] for b in breached_buys if b["final_cause"] == "ACTION_BUY"],
        },
    }


def paired_audit(evaluations: list[dict[str, Any]]) -> dict[str, Any]:
    technical: dict[tuple[str, int], dict[int, list]] = defaultdict(lambda: defaultdict(list))
    for item in evaluations:
        for record in load_trace((run_dir(item) / "llm_calls.jsonl").read_bytes()):
            if record.request.stage == "technical_analyst":
                technical[(record.request.decision_session, item["replicate"])][item["config_id"]].append((
                    record.request.analyst_id,
                    record.request.identity_digest,
                    record.provider_response_id,
                    hashlib.sha256((record.raw_response or "").encode()).hexdigest(),
                    hashlib.sha256(canonical_json(record.validated_response).encode()).hexdigest(),
                ))
    mismatched = [
        f"{session} r{replicate}"
        for (session, replicate), by_config in technical.items()
        if len(by_config) != len(SEQUENTIAL_DEV_GRID)
        or len({tuple(sorted(rows)) for rows in by_config.values()}) != 1
        or any(len(rows) != 5 for rows in by_config.values())
    ]
    return {
        "session_replicates": len(technical),
        "decision_sessions": len({s for s, _ in technical}),
        "same_five_technical_responses_in_all_configs": not mismatched,
        "mismatched": mismatched[:20],
    }


def summarize(out: Path, evaluations: list[dict], uses: list[dict], attempts: list[dict],
              base: dict[str, Any]) -> dict[str, Any]:
    total = SEQUENTIAL_DEV_REPETITIONS * len(SEQUENTIAL_DEV_GRID)
    evaluations.sort(key=lambda e: (e["replicate"], e["config_id"]))
    complete = base["failure"] is None and len(evaluations) == total
    summary: dict[str, Any] = {**base, "complete": complete, "evaluations": evaluations}
    if complete:
        sharpe = {
            str(c["config_id"]): [e["sharpe"]["sharpe"] for e in evaluations if e["config_id"] == c["config_id"]]
            for c in SEQUENTIAL_DEV_GRID
        }
        s2 = {cid: sum(values) / SEQUENTIAL_DEV_REPETITIONS for cid, values in sharpe.items()}
        ranking = sorted(s2, key=lambda cid: (-s2[cid], int(cid)))
        discrimination = "NONE" if len(set(s2.values())) == 1 else "YES"
        summary.update({
            "sharpe_by_replicate": sharpe,
            "S2": s2,
            "ranking": [int(cid) for cid in ranking],
            "selected_config_id": int(ranking[0]),
            "tie_at_top": sum(1 for v in s2.values() if v == s2[ranking[0]]) > 1,
            "sequential_dev_discrimination": discrimination,
            "selection_basis": "PROTOCOL_TIE_FALLBACK" if discrimination == "NONE" else "EMPIRICAL_S2",
        })
        summary["descriptive_metrics_NOT_USED_FOR_SELECTION"] = {
            f"{e['config_id']}-r{e['replicate']}": describe(e) for e in evaluations
        }
        summary["paired_technical_audit"] = paired_audit(evaluations)
    if FROZEN:
        from h2_v3 import replay_audit, risk_audit

        traces = [(e, r) for e in evaluations for r in load_trace((run_dir(e) / "llm_calls.jsonl").read_bytes())]
        summary["frozen_component_replay"] = replay_audit((r, FROZEN[e["replicate"]]) for e, r in traces)
        summary["risk_audit"] = risk_audit(r for _, r in traces)

    live = [u for u in uses if u["source"] == "live"]
    tokens: Counter = Counter()
    for u in live:
        for k, v in (u.get("usage") or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tokens[k] += v
    latencies = sorted(a["latency_ms"] for a in attempts)
    summary["operational"] = {
        "logical_calls": len(uses),
        "live_calls": len(live),
        "bank_hits": len(uses) - len(live),
        "frozen_v2_hits_by_stage": dict(Counter(u["stage"] for u in uses if u["source"] == "frozen_v2")),
        "calls_by_config_stage_source": {
            f"{c}/{stage}/{source}": n
            for (c, stage, source), n in sorted(Counter((u["config_id"], u["stage"], u["source"]) for u in uses).items())
        },
        "http_attempts": len(attempts),
        "attempt_outcomes": dict(Counter(a["outcome"] for a in attempts)),
        "http_status_counts": dict(Counter(str(a.get("status")) for a in attempts if a.get("status"))),
        "attempt_latency_ms": {
            "p50": latencies[len(latencies) // 2] if latencies else None,
            "p90": latencies[int(len(latencies) * 0.9)] if latencies else None,
        },
        "live_token_usage": dict(tokens),
        "cost": "not computed: no versioned API pricing source in the repository",
    }
    sessions = {u["decision_session"] for u in uses}
    if summary["treatment_version"] in (4, 5, 6):
        if summary["treatment_version"] == 6:
            from h2_v6 import require_pre_live_freeze, technical_audit
        elif summary["treatment_version"] == 5:
            from h2_v5 import require_pre_live_freeze, technical_audit
        else:
            from h2_v4 import require_pre_live_freeze, technical_audit

        summary["checker_freeze"] = require_pre_live_freeze(full_development=True)
        summary["technical_audit"] = technical_audit(
            r for e in evaluations for r in load_trace((run_dir(e) / "llm_calls.jsonl").read_bytes()))
    if summary["treatment_version"] == 6:
        from h2_v6 import apply_structural_gates
        apply_structural_gates(summary)
    summary["cal_b_audit"] = {
        "cal_b_authorized": anchors.CAL_B_AUTHORIZED,
        "decision_sessions_reaching_provider_or_bank": len(sessions),
        "cal_b_sessions_touched": sorted(sessions & set(anchors.sealed_holdout_anchors())),
    }
    summary["validation_audit"] = {
        "last_decision_session": max(sessions) if sessions else None,
        "max_settlement_session": max((e["settlement_session"] for e in evaluations), default=None),
        "max_data_end": max((e["data_end"] for e in evaluations), default=None),
        "phase_end": SEQUENTIAL_DEVELOPMENT_END,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    (out / "call_bank.jsonl").write_text("".join(canonical_json(u) + "\n" for u in uses), encoding="utf-8")
    (out / "attempts.jsonl").write_text("".join(canonical_json(a) + "\n" for a in attempts), encoding="utf-8")
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--treatment", type=int, choices=(1, 2, 3, 4, 5, 6), default=1)
    args = parser.parse_args()
    out_root = OUT_ROOT
    if args.treatment == 3:  # Amendment 10: base = CAL-A v3, Risk prompt v2, Technical v2 por replay
        from h2_v3 import by_replicate, seed_bank

        from src.experiments import treatment

        treatment.require_cal_b3_committed()
        if treatment.CAL_A_V3_SELECTED_CONFIG is None:
            sys.exit("Sequential Development v3 needs the committed CAL-A v3 selection")
        BASE_VOL.update({k: treatment.CAL_A_V3_SELECTED_CONFIG[k] for k in BASE_VOL})
        TREATMENT_EXTRA.update(technical_prompt_version=2, risk_prompt_version=treatment.SCIENTIFIC_RISK_PROMPT_VERSION)
        out_root = ROOT / "docs" / "evidence" / "sequential_dev_v3"
        FROZEN.update(by_replicate(treatment.FROZEN_V2_EVIDENCE["sequential_dev"], "evaluations"))
        seed_bank(BANK, FROZEN)
    if args.treatment == 2:
        from src.experiments import treatment

        if treatment.CAL_A_V2_SELECTED_CONFIG is None:
            sys.exit("Sequential Development v2 needs the committed CAL-A v2 selection")
        BASE_VOL.update({k: treatment.CAL_A_V2_SELECTED_CONFIG[k] for k in BASE_VOL})
        TREATMENT_EXTRA["technical_prompt_version"] = 2
        out_root = ROOT / "docs" / "evidence" / "sequential_dev_v2"
    if args.treatment in (4, 5, 6):
        if args.treatment == 6:
            from h2_v6 import require_pre_live_freeze, require_sessions, technical_audit
        elif args.treatment == 5:
            from h2_v5 import require_pre_live_freeze, require_sessions
            require_sessions((SEQUENTIAL_DEVELOPMENT_START, SEQUENTIAL_DEVELOPMENT_LAST_DECISION))
            anchors.require_cal_b_locked(SEQUENTIAL_DEVELOPMENT_START, SEQUENTIAL_DEVELOPMENT_LAST_DECISION)
        else:
            from h2_v4 import require_pre_live_freeze

        from src.experiments import treatment

        if args.treatment == 6:
            require_sessions((SEQUENTIAL_DEVELOPMENT_START, SEQUENTIAL_DEVELOPMENT_LAST_DECISION))
            require_pre_live_freeze(full_development=True, phase="sequential")
        else:
            require_pre_live_freeze(full_development=True)
        if args.treatment == 6:
            from h2_v6 import load_v6_selections
            load_v6_selections()
        selected = getattr(treatment, f"CAL_A_V{args.treatment}_SELECTED_CONFIG")
        if selected is None:
            sys.exit(f"Sequential Development v{args.treatment} needs its committed CAL-A selection")
        BASE_VOL.update({k: selected[k] for k in BASE_VOL})
        TREATMENT_EXTRA.update(technical_prompt_version=args.treatment - 1, risk_prompt_version=2)
        if args.treatment == 6:
            TREATMENT_EXTRA["technical_response_schema_version"] = 2
        out_root = ROOT / f"docs/evidence/sequential_dev_v{args.treatment}"
    previous = None if args.resume is None else (ROOT / args.resume).resolve()
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit the freeze before Sequential Development")
    if anchors.CAL_B_AUTHORIZED is not False:
        sys.exit("CAL-B must stay locked")
    load_key()
    commit = git("rev-parse", "HEAD")
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    runs_dir = ROOT / "data" / "runs" / f"seqdev_{stamp}"
    participant_module.PROVIDER_CLIENTS["gemini"] = BankedGeminiClient  # type: ignore[index]

    evaluations, carried_uses, prior_attempts = carried_replicates(previous)
    BANK.uses.extend(carried_uses)
    carried = {e["replicate"] for e in evaluations}
    out = out_root / f"run_{stamp}"
    new_root = out.relative_to(ROOT).as_posix() + "/runs"
    failure: str | None = None
    clock = time.perf_counter()
    try:
        for replicate in range(1, SEQUENTIAL_DEV_REPETITIONS + 1):
            if replicate in carried:
                continue
            for config in sorted(SEQUENTIAL_DEV_GRID, key=lambda item: item["config_id"]):
                BANK.context = {"replicate": replicate, "config_id": config["config_id"]}
                runner = ExperimentRunner(
                    spec_for(config),
                    context=RunContext("CALIBRATION", f"seqdev-{config['name'].lower()}-r{replicate}"),
                    runs_dir=runs_dir,
                    repository_dir=ROOT,
                )
                result, path = runner.run_and_persist()
                evaluations.append({
                    **BANK.context,
                    "name": config["name"],
                    "risk_max_drawdown": config["risk_max_drawdown"],
                    "spec_hash": result.spec_hash,
                    "run_id": result.run_id,
                    "run_dir": path.name,
                    "runs_root": new_root,
                    "settlement_session": str(result.evaluation.settlement_session.date()),
                    "data_end": str(result.evaluation.data_end.date()),
                    "sharpe": metrics.scientific_sharpe(result.equity_curve),
                })
                print(f"[r{replicate} {config['name']}] done in {time.perf_counter() - clock:.0f}s", flush=True)
    except Exception as exc:  # integridade do conjunto perdida: registra e para
        failure = f"{type(exc).__name__}: {exc}"
        print("SEQUENTIAL DEVELOPMENT STOPPED:", failure, flush=True)

    out.mkdir(parents=True, exist_ok=True)
    if runs_dir.exists():
        shutil.copytree(runs_dir, out / "runs")
    base = {
        "kind": {1: "SEQUENTIAL_DEVELOPMENT", 2: "SEQUENTIAL_DEVELOPMENT_V2", 3: "SEQUENTIAL_DEVELOPMENT_V3", 4: "SEQUENTIAL_DEVELOPMENT_V4", 5: "SEQUENTIAL_DEVELOPMENT_V5", 6: "SEQUENTIAL_DEVELOPMENT_V6"}[
            args.treatment],
        "treatment_version": args.treatment,
        "base_volatility_config": dict(BASE_VOL),
        "resumed_from": None if previous is None else previous.name,
        "started_utc": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "wall_clock_seconds": round(time.perf_counter() - clock, 1),
        "git_commit": commit,
        "snapshot_id": ANCHOR_SNAPSHOT_ID,
        "phase": {"start": SEQUENTIAL_DEVELOPMENT_START, "last_decision": SEQUENTIAL_DEVELOPMENT_LAST_DECISION,
                  "end": SEQUENTIAL_DEVELOPMENT_END},
        "grid": list(SEQUENTIAL_DEV_GRID),
        "repetitions": SEQUENTIAL_DEV_REPETITIONS,
        "sharpe_definition": metrics.SCIENTIFIC_SHARPE_DEFINITION,
        "cost_spec": CAL_A_COST_SPEC,
        "failure": failure,
    }
    summary = summarize(out, evaluations, BANK.uses, prior_attempts + ATTEMPTS.attempts, base)
    print(out.as_posix())
    print(json.dumps({k: summary.get(k) for k in (
        "complete", "failure", "S2", "ranking", "selected_config_id", "tie_at_top",
        "sequential_dev_discrimination", "selection_basis", "paired_technical_audit", "cal_b_audit",
        "validation_audit")}, indent=1, default=str))
    if not summary["complete"] or anchors.CAL_B_AUTHORIZED is not False:
        sys.exit(1)


if __name__ == "__main__":
    main()
