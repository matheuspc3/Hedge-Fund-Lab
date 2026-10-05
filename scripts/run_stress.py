"""Stress Probing do H2 (Amendment 6, STRESS_PROBING_FREEZE_V1).

Dois passos, cada um num commit limpo próprio:

``select``  só dados de MERCADO dos 20 estratos não-CAL-B: métricas M1-M4,
            rankings, as 4 janelas e os probes determinísticos de risco. Nenhuma
            chamada ao provedor. Grava ``docs/evidence/stress/selection.json``
            e ``risk_probes.json``; o compromisso das janelas é commitado antes
            de ``run``.
``run``     4 janelas x R=3 trajetórias live independentes com o H2 congelado.
            Cada trajetória é um run normal do ``ExperimentRunner`` com a janela
            declarada como fronteira (decisões até a penúltima sessão do
            estrato, liquidação na última, dados cortados nela). Para na
            primeira falha final; nada é imputado.

Tudo financeiro é DESCRIPTIVE ONLY — NO SELECTION AUTHORITY.

Uso: ``python scripts/run_stress.py select`` / ``python scripts/run_stress.py run``.
"""

import json
import math
import shutil
import sys
import time
from collections import Counter
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
from src.agents.features import canonical_number  # noqa: E402
from src.agents.llm_trace import load_trace, session_key  # noqa: E402
from src.backtesting import metrics  # noqa: E402
from src.experiments import anchors, stress  # noqa: E402
from src.experiments.anchors import (  # noqa: E402
    CAL_A_COST_SPEC,
    CAL_A_INITIAL_CAPITAL,
    CAL_A_MINIMUM_HISTORY_SESSIONS,
    CAL_B_STRATA,
    STRATA,
)
from src.experiments.context import RunContext  # noqa: E402
from src.experiments.hardening import H_REAL_SNAPSHOT_IDENTITY_DIGEST  # noqa: E402
from src.experiments.phases import SEQUENTIAL_DEVELOPMENT_START  # noqa: E402
from src.experiments.runner import ExperimentRunner  # noqa: E402
from src.experiments.spec import (  # noqa: E402
    CostSpec,
    EvaluationSpec,
    ExecutionSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
)
from src.pipeline.snapshot import (  # noqa: E402
    PRICE_REPRESENTATION,
    load_dataset_snapshot,
    load_snapshot_frames,
    verify_snapshot_integrity,
)

OUT = ROOT / "docs" / "evidence" / "stress"
SELECTION = OUT / "selection.json"
PROBES = OUT / "risk_probes.json"
STRATUM = {s.stratum_id: s for s in STRATA}
DESCRIPTIVE = "DESCRIPTIVE ONLY — NO SELECTION AUTHORITY"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def require_clean_and_locked() -> str:
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit before Stress")
    if anchors.CAL_B_AUTHORIZED is not False:
        sys.exit("CAL-B must stay locked during Stress")
    return git("rev-parse", "HEAD")


def load_frame() -> tuple[Any, pd.DataFrame]:
    snapshot = load_dataset_snapshot(ROOT / "data" / "snapshots" / stress.STRESS_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    if not snapshot.scientific_ready or snapshot.identity_digest != H_REAL_SNAPSHOT_IDENTITY_DIGEST:
        sys.exit("Stress snapshot is not the READY corrected snapshot")
    return snapshot, load_snapshot_frames(snapshot, (stress.STRESS_TICKER,))[stress.STRESS_TICKER]


def cal_b_ranges() -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    return [(pd.Timestamp(STRATUM[i].first), pd.Timestamp(STRATUM[i].last)) for i in CAL_B_STRATA]


def in_cal_b(day: Any) -> bool:
    day = pd.Timestamp(day)
    return any(low <= day <= high for low, high in cal_b_ranges())


# ── select ───────────────────────────────────────────────────────


def select() -> None:
    commit = require_clean_and_locked()
    snapshot, frame = load_frame()
    scores = {s.stratum_id: stress.market_stress_metrics(stress.stratum_frame(frame, s))
              for s in stress.STRESS_ELIGIBLE_STRATA}
    ranked = stress.rankings(scores)
    chosen = stress.select_stress_windows(ranked)
    sessions = frame.index
    windows = []
    for k, (category, sid) in enumerate(chosen, 1):
        s = STRATUM[sid]
        inside = sessions[(sessions >= pd.Timestamp(s.first)) & (sessions <= pd.Timestamp(s.last))]
        after = sessions[sessions > pd.Timestamp(s.last)][0]
        key = next(key for c, key, _ in stress.STRESS_CATEGORIES if c == category)
        windows.append({
            "stress_id": f"S{k}", "category": category, "stratum_id": sid,
            "start": s.first, "last_decision": str(inside[-2].date()), "end": s.last,
            "decision_sessions": len(inside) - 1, "stratum_sessions": len(inside),
            "market_score_metric": key, "market_score": scores[sid][key],
            "next_session_after_window": str(after.date()),
            "next_session_stratum_is_cal_b": in_cal_b(after),
        })
    probes = stress.risk_contract_probes()
    if not all(row["pass"] for row in probes):
        sys.exit("deterministic risk probe failed: objective bug, stop")
    selection = {
        "kind": "STRESS_WINDOW_SELECTION",
        "freeze": stress.STRESS_PROBING_FREEZE,
        "computed_utc": now(),
        "git_commit": commit,
        "inputs": "market data only (adjusted close/open inside each eligible stratum); no LLM response, "
                  "no treatment result; CAL-B strata never read for any metric",
        "snapshot": {"snapshot_id": snapshot.snapshot_id, "identity_digest": snapshot.identity_digest,
                     "files": [dict(f) for f in snapshot.files], "source": json.loads(snapshot.manifest_json)["source"],
                     "price_representation": PRICE_REPRESENTATION},
        "eligible_strata": [s.stratum_id for s in stress.STRESS_ELIGIBLE_STRATA],
        "excluded_cal_b_strata": list(CAL_B_STRATA),
        "tie_break": stress.STRESS_TIE_BREAK,
        "categories": [{"category": c, "metric": key, "adverse_order": "descending" if desc else "ascending"}
                       for c, key, desc in stress.STRESS_CATEGORIES],
        "metrics_by_stratum": {str(sid): m for sid, m in scores.items()},
        "rankings": {c: ranked[c] for c, _, _ in stress.STRESS_CATEGORIES},
        "ranking_sha256": {c: stress.ranking_digest(ranked[c], scores, key)
                           for c, key, _ in stress.STRESS_CATEGORIES},
        "windows": windows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8", newline="\n")
    PROBES.write_text(json.dumps({
        "kind": "STRESS_DETERMINISTIC_RISK_PROBES", "computed_utc": now(), "git_commit": commit,
        "risk_config": {k: stress.STRESS_FROZEN_PARAMS[k]
                        for k in ("risk_max_volatility", "risk_max_drawdown", "risk_max_concentration")},
        "rule": "hard veto iff canonical (6 decimals) value > limit, volatility checked before drawdown; "
                "VENDA/MANTER auto-approved; no LLM risk call when a hard rule vetoes",
        "financial_performance": "none",
        "all_pass": all(row["pass"] for row in probes),
        "cases": probes,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(windows, indent=1))


# ── run ──────────────────────────────────────────────────────────

ALLOWED: set[str] = set()


class StressGeminiClient(BankedGeminiClient):
    """Cliente do banco com a tranca do Stress: só sessões de decisão da janela."""

    def begin_session(self, session: Any) -> None:
        key = session_key(session)
        if key not in ALLOWED or in_cal_b(key):
            raise RuntimeError(f"session {key} is outside the current Stress window")
        super().begin_session(session)


def committed_windows() -> list[dict[str, Any]]:
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    windows = [{k: w[k] for k in ("stress_id", "category", "stratum_id", "start", "last_decision", "end")}
               for w in selection["windows"]]
    if not stress.STRESS_SELECTED_WINDOWS or windows != [dict(w) for w in stress.STRESS_SELECTED_WINDOWS]:
        sys.exit("Stress windows are not committed or differ from selection.json")
    if selection["git_commit"] != stress.STRESS_SELECTION_COMMIT:
        sys.exit("selection.json was not computed on the committed selection commit")
    return windows


def spec_for(window: dict[str, Any]) -> ExperimentSpec:
    return ExperimentSpec(
        snapshot_id=stress.STRESS_SNAPSHOT_ID,
        participant=ParticipantSpec("llm_agent", dict(stress.STRESS_FROZEN_PARAMS)),
        initial_capital=CAL_A_INITIAL_CAPITAL,
        costs=CostSpec(**CAL_A_COST_SPEC),
        metrics=MetricSpec(),
        execution=ExecutionSpec(quantity_mode="fractional_notional"),
        evaluation=EvaluationSpec(
            decision_start=window["start"],
            decision_end=window["last_decision"],
            minimum_history_sessions=CAL_A_MINIMUM_HISTORY_SESSIONS,
        ),
    )


def run() -> None:
    commit = require_clean_and_locked()
    windows = committed_windows()
    _, frame = load_frame()
    load_key()
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    runs_dir = ROOT / "data" / "runs" / f"stress_{stamp}"
    out = OUT / f"run_{stamp}"
    participant_module.PROVIDER_CLIENTS["gemini"] = StressGeminiClient  # type: ignore[index]
    trajectories: list[dict[str, Any]] = []
    failure: str | None = None
    clock = time.perf_counter()
    try:
        for window in windows:
            sessions = frame.index[(frame.index >= pd.Timestamp(window["start"]))
                                   & (frame.index <= pd.Timestamp(window["last_decision"]))]
            ALLOWED.clear()
            ALLOWED.update(str(day.date()) for day in sessions)
            boundary = stress.stress_boundary(window["stress_id"], STRATUM[window["stratum_id"]])
            for replicate in range(1, stress.STRESS_REPETITIONS + 1):
                BANK.context = {"stress_id": window["stress_id"], "replicate": replicate}
                tick = time.perf_counter()
                runner = ExperimentRunner(
                    spec_for(window),
                    context=RunContext("CALIBRATION", f"stress-{window['stress_id'].lower()}-r{replicate}"),
                    runs_dir=runs_dir,
                    repository_dir=ROOT,
                    boundaries=(boundary,),
                )
                result, path = runner.run_and_persist()
                trajectories.append({
                    **window, "replicate": replicate, "spec_hash": result.spec_hash, "run_id": result.run_id,
                    "run_dir": path.name, "runs_root": out.relative_to(ROOT).as_posix() + "/runs",
                    "settlement_session": str(result.evaluation.settlement_session.date()),
                    "data_end": str(result.evaluation.data_end.date()),
                    "wall_clock_seconds": round(time.perf_counter() - tick, 1),
                })
                print(f"[{window['stress_id']} r{replicate}] done in {time.perf_counter() - clock:.0f}s", flush=True)
    except Exception as exc:  # integridade perdida: registra e para, nada é imputado
        failure = f"{type(exc).__name__}: {exc}"
        print("STRESS STOPPED:", failure, flush=True)

    out.mkdir(parents=True, exist_ok=True)
    if runs_dir.exists():
        shutil.copytree(runs_dir, out / "runs")
    summary = summarize(out, trajectories, frame, {
        "kind": "STRESS_PROBING", "freeze": stress.STRESS_PROBING_FREEZE, "started_utc":
        started.isoformat(timespec="seconds").replace("+00:00", "Z"), "finished_utc": now(),
        "wall_clock_seconds": round(time.perf_counter() - clock, 1), "git_commit": commit,
        "freeze_commit": stress.STRESS_FREEZE_COMMIT, "snapshot_id": stress.STRESS_SNAPSHOT_ID,
        "frozen_params": dict(stress.STRESS_FROZEN_PARAMS), "calibration_provenance":
        dict(stress.CALIBRATION_PROVENANCE), "repetitions": stress.STRESS_REPETITIONS,
        "cost_spec": CAL_A_COST_SPEC, "sharpe_definition": metrics.SCIENTIFIC_SHARPE_DEFINITION,
        "windows": windows, "failure": failure,
    })
    print(out.as_posix())
    print(json.dumps({k: summary.get(k) for k in ("complete", "failure", "gates", "coverage", "status")},
                     indent=1, default=str))
    if summary["status"] != "STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL":
        sys.exit(1)


# ── auditoria e diagnósticos (a partir dos artefatos persistidos) ─


def canonical_volatility(frame: pd.DataFrame, day: pd.Timestamp) -> float:
    """Mesmo caminho de ``LLMParticipant._agent_state`` sobre o histórico até t."""
    window = int(stress.STRESS_FROZEN_PARAMS["volatility_window"])
    returns = frame.loc[:day, "fechamento"].pct_change().dropna().tail(window)
    return canonical_number(float(returns.std(ddof=1) * math.sqrt(252)))


def describe(item: dict[str, Any], frame: pd.DataFrame) -> dict[str, Any]:
    path = ROOT / item["runs_root"] / item["run_dir"]
    curve = pd.read_csv(path / "equity.csv", index_col="date", parse_dates=True)["equity"]
    trades = pd.read_csv(path / "trades.csv", parse_dates=["date"])
    decisions = [json.loads(x) for x in (path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    records = list(load_trace((path / "llm_calls.jsonl").read_bytes()))
    first, last_decision, end = (pd.Timestamp(item[k]) for k in ("start", "last_decision", "end"))
    max_dd, max_vol = float(stress.STRESS_FROZEN_PARAMS["risk_max_drawdown"]), float(
        stress.STRESS_FROZEN_PARAMS["risk_max_volatility"])

    # S-C: fronteira, CAL-B, dado futuro.
    days = [pd.Timestamp(d["decision_session"]) for d in decisions]
    expected_days = list(frame.index[(frame.index >= first) & (frame.index <= last_decision)])
    boundary = {
        "decision_sessions_equal_window": days == expected_days and all(d["eligible"] for d in decisions),
        "orders_outside_window": [str(t.date()) for t in trades["date"] if not first < t <= end],
        "equity_first_last": [str(curve.index[0].date()), str(curve.index[-1].date())],
        "equity_bounds_ok": curve.index[0] == first and curve.index[-1] == end,
        "settlement_is_window_end": item["settlement_session"] == item["end"],
        "data_end_is_window_end": item["data_end"] == item["end"],
        "trace_sessions_outside_decisions": sorted({r.request.decision_session for r in records}
                                                   - {str(d.date()) for d in expected_days}),
        "cal_b_sessions_touched": sorted({str(d.date()) for d in [*days, *curve.index, *trades["date"]]
                                          if in_cal_b(d)}),
        "validation_or_final_access": max(curve.index) >= pd.Timestamp(SEQUENTIAL_DEVELOPMENT_START),
    }
    boundary["violations"] = (
        (not boundary["decision_sessions_equal_window"]) + len(boundary["orders_outside_window"])
        + (not boundary["equity_bounds_ok"]) + (not boundary["settlement_is_window_end"])
        + (not boundary["data_end_is_window_end"]) + len(boundary["trace_sessions_outside_decisions"])
        + len(boundary["cal_b_sessions_touched"]) + boundary["validation_or_final_access"]
    )

    # S-R: drawdown canônico em close(t) (pico interno, começa no capital) e
    # volatilidade recalculada; conferidos contra o prompt do LLM de risco.
    peak = curve.cummax().clip(lower=CAL_A_INITIAL_CAPITAL)
    drawdown = ((peak - curve) / peak).map(canonical_number)
    risk_calls = Counter(r.request.decision_session for r in records if r.request.stage == "risk_manager")
    prompts = {r.request.decision_session: json.loads(r.request.user_prompt)["risk_metrics"]
               for r in records if r.request.stage == "risk_manager"}
    rows, violations, mismatches = [], [], []
    for d, day in zip(decisions, days):
        dd, vol = float(drawdown[day]), canonical_volatility(frame, day)
        if d["decision_session"] in prompts:
            seen = prompts[d["decision_session"]]
            if seen["current_drawdown"] != dd or seen["recent_volatility"] != vol:
                mismatches.append(d["decision_session"])
        rows.append((d, dd, vol))
        if d["risk_rule"] == "VOLATILITY" and not vol > max_vol or (
                d["risk_rule"] == "DRAWDOWN" and not (dd > max_dd and vol <= max_vol)):
            violations.append({"session": d["decision_session"], "issue": "hard rule without breach"})
        if d["technical_outcome"] == "COMPRA" and (vol > max_vol or dd > max_dd):
            expected = "VOLATILITY" if vol > max_vol else "DRAWDOWN"
            if d["risk_source"] != "HARD_RULE" or d["risk_rule"] != expected or risk_calls[d["decision_session"]]:
                violations.append({"session": d["decision_session"], "issue": "breach not hard-vetoed before LLM",
                                   "risk_source": d["risk_source"], "risk_rule": d["risk_rule"]})
    buys = [(d, dd, vol) for d, dd, vol in rows if d["technical_outcome"] == "COMPRA"]
    vol_buys = [d for d, dd, vol in buys if vol > max_vol]
    dd_buys = [d for d, dd, vol in buys if dd > max_dd and vol <= max_vol]
    masked = [d for d, dd, vol in buys if dd > max_dd and vol > max_vol]
    causes = Counter(d["final_cause"] for d in decisions)
    tokens: Counter = Counter()
    for r in records:
        for k, v in (r.token_usage or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tokens[k] += v
    latency = sorted(r.duration_ms for r in records)
    return {
        "boundary_audit": boundary,
        "risk_audit": {
            "violations": violations,
            "trace_metric_mismatches": mismatches,
            "buy_decisions": len(buys),
            "volatility_rule_exercised": "YES" if vol_buys else "NO",
            "buys_with_volatility_above_limit": len(vol_buys),
            "drawdown_rule_exercised": "YES" if dd_buys else "NO",
            "buys_with_drawdown_above_limit_deciding": len(dd_buys),
            "buys_with_drawdown_above_limit_masked_by_volatility": len(masked),
            "breach_buys_by_final_cause": dict(Counter(d["final_cause"] for d in [*vol_buys, *dd_buys, *masked])),
        },
        "truncations": sum(r.finish_reason in ("MAX_TOKENS", "length") for r in records),
        "final_failed_calls": sum(r.status != "ok" for r in records),
        DESCRIPTIVE: {
            "scientific_sharpe": metrics.scientific_sharpe(curve)["sharpe"],
            "terminal_net_return": float(curve.iloc[-1] / CAL_A_INITIAL_CAPITAL - 1.0),
            "max_strategy_drawdown": -metrics.max_drawdown(curve),
            "sortino": metrics.sortino_ratio(metrics.periodic_returns(curve)),
            "turnover_traded_notional_over_capital": float((trades["price"] * trades["quantity"]).abs().sum()
                                                           / CAL_A_INITIAL_CAPITAL),
            "trades": len(trades),
            "time_in_market": sum(1 for d in decisions if d["observed_weight"] > 0) / len(decisions),
            "max_current_drawdown_at_decisions": max(dd for _, dd, _ in rows),
            "max_recent_volatility_at_decisions": max(vol for _, _, vol in rows),
            "technical_explicit_holds": causes["TECH_EXPLICIT_HOLD"],
            "technical_no_majority": causes["TECH_NO_MAJORITY"],
            "hard_volatility_vetoes": causes["RISK_VETO_VOLATILITY"],
            "hard_drawdown_vetoes": causes["RISK_VETO_DRAWDOWN"],
            "llm_risk_vetoes": causes["RISK_VETO_LLM"],
            "portfolio_holds": causes["PORTFOLIO_HOLD"],
            "buy_at_target_noop": causes["BUY_AT_TARGET_NOOP"],
            "final_causes": dict(sorted(causes.items())),
            "risk_rule_counts": dict(Counter(str(d["risk_rule"]) for d in decisions)),
        },
        "operational": {
            "decision_sessions": len(decisions),
            "logical_calls": len(records),
            "logical_calls_by_stage": dict(Counter(r.request.stage for r in records)),
            "provider_retries": sum(r.retry_count for r in records),
            "token_usage": dict(tokens),
            "call_latency_ms": {"p50": latency[len(latency) // 2] if latency else None,
                                "p90": latency[int(len(latency) * 0.9)] if latency else None,
                                "total": round(sum(latency), 1)},
            "wall_clock_seconds": item["wall_clock_seconds"],
        },
        "_series": {"technical": [d["technical_outcome"] for d in decisions],
                    "final_cause": [d["final_cause"] for d in decisions],
                    "weights": [d["observed_weight"] for d in decisions],
                    "last_decision": decisions[-1]["final_cause"]},
    }


def spread(values: list[float]) -> dict[str, float]:
    return {"min": min(values), "max": max(values), "range": max(values) - min(values)}


def robustness(described: list[dict[str, Any]]) -> dict[str, Any]:
    """Sensibilidade à inferência estocástica entre as 3 repetições (descritivo)."""
    series = [d["_series"] for d in described]
    fin = [d[DESCRIPTIVE] for d in described]
    differ = lambda key: sum(len(set(col)) > 1 for col in zip(*(s[key] for s in series)))  # noqa: E731
    divergence = next((i for i, col in enumerate(zip(*(s["weights"] for s in series))) if len(set(col)) > 1), None)
    return {
        "sessions_technical_consensus_differs": differ("technical"),
        "sessions_final_cause_differs": differ("final_cause"),
        "first_decision_index_where_exposure_diverges": divergence,
        "identical_trajectories": divergence is None,
        "last_decision_final_cause_by_replicate": [s["last_decision"] for s in series],
        "trade_count": spread([f["trades"] for f in fin]),
        "scientific_sharpe": spread([f["scientific_sharpe"] for f in fin]),
        "terminal_net_return": spread([f["terminal_net_return"] for f in fin]),
        "max_strategy_drawdown": spread([f["max_strategy_drawdown"] for f in fin]),
    }


def summarize(out: Path, trajectories: list[dict], frame: pd.DataFrame, base: dict[str, Any]) -> dict[str, Any]:
    total = stress.STRESS_WINDOW_COUNT * stress.STRESS_REPETITIONS
    complete = base["failure"] is None and len(trajectories) == total
    described = {f"{t['stress_id']}-r{t['replicate']}": describe(t, frame) for t in trajectories}
    live = [u for u in BANK.uses if u["source"] == "live"]
    s_c = sum(d["boundary_audit"]["violations"] + len(d["risk_audit"]["trace_metric_mismatches"])
              for d in described.values())
    s_r = sum(len(d["risk_audit"]["violations"]) for d in described.values())
    failures = sum(d["final_failed_calls"] for d in described.values()) + (base["failure"] is not None)
    truncations = sum(d["truncations"] for d in described.values())
    gates = {
        "S-A": {"result": f"{failures} final failures; {total - len(trajectories)} trajectories missing",
                "pass": complete and failures == 0},
        "S-T": {"result": f"{truncations} truncations", "pass": truncations == 0},
        "S-C": {"result": f"{s_c} boundary/causal violations", "pass": complete and s_c == 0},
        "S-R": {"result": f"{s_r} hard-risk contract violations", "pass": complete and s_r == 0},
    }
    vol_ex = any(d["risk_audit"]["volatility_rule_exercised"] == "YES" for d in described.values())
    dd_ex = any(d["risk_audit"]["drawdown_rule_exercised"] == "YES" for d in described.values())
    coverage = {
        "drawdown_rule": "EXERCISED" if dd_ex else "NOT_EXERCISED",
        "volatility_rule": "EXERCISED" if vol_ex else "NOT_EXERCISED",
        "flags": [f for f, ok in (("HISTORICAL_STRESS_DRAWDOWN_RULE_NOT_EXERCISED", dd_ex),
                                  ("HISTORICAL_STRESS_VOLATILITY_RULE_NOT_EXERCISED", vol_ex)) if not ok],
    }
    by_window = {}
    for w in base["windows"]:
        reps = [described[k] for k in described if k.startswith(w["stress_id"] + "-")]
        if len(reps) == stress.STRESS_REPETITIONS:
            by_window[w["stress_id"]] = robustness(reps)
    for d in described.values():
        d.pop("_series")
    ok = all(g["pass"] for g in gates.values()) and anchors.CAL_B_AUTHORIZED is False
    summary = {
        **base, "complete": complete, "trajectories": trajectories, "gates": gates, "coverage": coverage,
        "per_trajectory": described, "stochastic_robustness_" + DESCRIPTIVE: by_window,
        "operational": {
            "live_calls": len(live), "bank_hits": len(BANK.uses) - len(live),
            "every_call_live_and_independent": len(BANK.uses) == len(live),
            "http_attempts": len(ATTEMPTS.attempts),
            "attempt_outcomes": dict(Counter(a["outcome"] for a in ATTEMPTS.attempts)),
            "http_status_counts": dict(Counter(str(a.get("status")) for a in ATTEMPTS.attempts if a.get("status"))),
            "cost": "not computed: no versioned API pricing source in the repository",
        },
        "cal_b_authorized": anchors.CAL_B_AUTHORIZED,
        "status": "STRESS PROBING COMPLETE — READY FOR CAL-B PROTOCOL" if ok else "STRESS PROBING INCOMPLETE OR FAILED",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str, ensure_ascii=False) + "\n",
                                      encoding="utf-8", newline="\n")
    (out / "attempts.jsonl").write_text("".join(json.dumps(a, sort_keys=True) + "\n" for a in ATTEMPTS.attempts),
                                        encoding="utf-8", newline="\n")
    (out / "call_bank.jsonl").write_text("".join(json.dumps(u, sort_keys=True, default=str) + "\n"
                                                 for u in BANK.uses), encoding="utf-8", newline="\n")
    return summary


if __name__ == "__main__":
    {"select": select, "run": run}[sys.argv[1] if len(sys.argv) > 1 else ""]()
