"""Read-only H2 v6 dashboard API. Reads sealed artifacts and journals; never writes.

No endpoint starts inference, reads credentials or touches Final Test results.
Demo payloads are generated synthetic data and always carry ``synthetic: true``.
"""

import csv
import json
import random
import re
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.backtesting.metrics import drawdown_series, performance_metrics  # noqa: E402
from src.experiments.h2_evaluation import aggregate, aligned_returns  # noqa: E402

CANDIDATE = ROOT / "docs/evidence/h2_v6_evaluation/system_freeze_candidate.json"
AMENDMENT = ROOT / "docs/H2_V6_OPERATIONAL_AMENDMENT_OA1.md"
EVIDENCE = ROOT / "docs/evidence/h2_v6_provisional"
CAL_B4_STATUS = ROOT / "docs/evidence/cal_b4/run_20261008T221200Z/status.json"
SOURCES = {
    "provisional": ROOT / "data/runs/h2_v6_provisional/VALIDATION",
    "official": ROOT / "data/runs/h2_v6_evaluation/VALIDATION",
}
SOURCE_LABELS = {
    "provisional": "Validation provisória OA-1 (somente autor, não ratificada)",
    "official": "Validation oficial (exige aprovação acadêmica + System Freeze)",
    "demo": "DEMONSTRAÇÃO — DADOS SINTÉTICOS",
}
LLM = ("L01", "L02", "L03")
BENCHMARKS = ("buy_and_hold", "sma_regime_h2_proposed", "bollinger_state_h2_proposed")
LABELS = {
    "L01": "H2 v6 · L01",
    "L02": "H2 v6 · L02",
    "L03": "H2 v6 · L03",
    "buy_and_hold": "Buy & Hold",
    "sma_regime_h2_proposed": "SMA Regime",
    "bollinger_state_h2_proposed": "Bollinger Estado",
}
ROOT_FILES = ("summary.json", "cost_closure.json", "validation_release.json")
CAPITAL = 100000.0
DEMO_BANNER = "DEMONSTRAÇÃO — DADOS SINTÉTICOS"


def _json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _sha(path):
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _query(path, sql, args=()):
    if not path.is_file():
        return None
    # ponytail: immutable=1 takes no locks, so a live run's FULL commits never
    # wait on the dashboard (a busy journal would fail the run closed). A torn
    # read during a write only fails this request; it is polled again.
    try:
        uri = path.as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            return db.execute(sql, args).fetchall()
    except sqlite3.Error:
        return None


def _run_dir(root, slot):
    pattern = re.compile(rf"H2-V6(-OA1)?-VALIDATION-{re.escape(slot)}-[0-9a-f]{{12}}")
    runs = root / "runs"
    found = (
        [p for p in runs.iterdir() if pattern.fullmatch(p.name)] if runs.is_dir() else []
    )
    return found[0] if len(found) == 1 else None


def source_state(root):
    if not (root / "evaluation.sqlite").is_file():
        return "NÃO INICIADA"
    if (root / "execution.lock").is_file():
        return "EM EXECUÇÃO"
    slots = dict(_query(root / "evaluation.sqlite", "SELECT slot,state FROM slots") or [])
    if all(slots.get(s) == "COMPLETE" for s in (*LLM, *BENCHMARKS)):
        if (root / "summary.json").is_file() and (
            root / "validation_release.json"
        ).is_file():
            return "CONCLUÍDA E SELADA"
        return "RUNS COMPLETAS — FECHAMENTO PENDENTE"
    return "INTERROMPIDA — investigar (recuperação é replay-only)"


def status():
    candidate = _json(CANDIDATE)
    protocol = candidate["protocol"]
    authorization = _json(EVIDENCE / "AUTHOR_AUTHORIZATION_OA1.json")
    amendment_sha = _sha(AMENDMENT) if AMENDMENT.is_file() else None
    checkpoint = EVIDENCE / "VALIDATION_PROVISIONAL_CHECKPOINT.json"
    return {
        "identity": {
            "manifest_sha256": CANDIDATE.with_suffix(".sha256").read_text().strip(),
            "state": candidate["state"],
            "live_authorized": candidate["live_authorized"],
            "approvals": candidate["approvals"],
            "freeze_record": candidate["freeze_record"],
            "participant_sha256": protocol["participant_sha256"],
            "model": protocol["participant_spec"]["params"],
            "R": protocol["R"],
            "aggregation": protocol["aggregation"],
            "hypotheses": protocol["hypotheses"],
            "test": protocol["test"],
            "costs": protocol["costs"],
            "cost_grid": protocol["cost_grid"],
            "initial_capital": protocol["initial_capital"],
            "benchmarks": protocol["benchmarks"],
            "snapshot": protocol["snapshot"],
            "windows": {p: w["evaluation"] for p, w in protocol["windows"].items()},
            "run_identities": protocol["run_identities"],
            "environment": {
                k: v for k, v in candidate["environment"].items() if k != "packages"
            },
            "inventory_sizes": {
                k: len(candidate[k])
                for k in (
                    "documents_sha256",
                    "sources_sha256",
                    "historical_bindings_sha256",
                )
            },
            "cal_b4_status": (_json(CAL_B4_STATUS) or {}).get("status"),
        },
        "governance": {
            "academic": "NÃO APROVADO / NÃO CONGELADO — coautor, orientador e System Freeze pendentes",
            "amendment": {
                "id": "H2-V6-OA1",
                "sha256": amendment_sha,
                "present": bool(amendment_sha),
            },
            "author_authorization": None
            if authorization is None
            else {
                "signatory": authorization.get("signatory"),
                "recorded_at": authorization.get("recorded_at"),
                "binds_current_amendment": authorization.get("amendment_sha256")
                == amendment_sha,
                "sha256": _sha(EVIDENCE / "AUTHOR_AUTHORIZATION_OA1.json"),
                "note": "verificação completa (hashes, árvore limpa, ambiente) apenas no preflight",
            },
            "provisional_checkpoint_sha256": _sha(checkpoint)
            if checkpoint.is_file()
            else None,
        },
        "phases": {
            "VALIDATION": {s: source_state(r) for s, r in SOURCES.items()},
            "FINAL_TEST": "BLOQUEADO — exige manifesto APPROVED/FROZEN, consentimento próprio e checkpoint oficial de Validation",
        },
    }


def _participant(slot, equity, trades, manifest_metrics=None):
    metrics = manifest_metrics or performance_metrics(equity)
    notional = sum(abs(t["price"] * t["quantity"]) for t in trades)
    return {
        "id": slot,
        "label": LABELS[slot],
        "kind": "llm" if slot in LLM else "benchmark",
        "metrics": {
            "initial": float(equity.iloc[0]),
            "final": float(equity.iloc[-1]),
            "net_return": metrics["total_return"],
            "sharpe": metrics["sharpe_ratio"],
            "sortino": metrics["sortino_ratio"],
            "max_drawdown": metrics["max_drawdown"],
            "turnover": notional / CAPITAL,
            "trades": len(trades),
            "total_cost": sum(t["cost"] for t in trades),
        },
    }


def _curves(equities):
    first = next(iter(equities.values()))
    return {
        "dates": [d.strftime("%Y-%m-%d") for d in first.index],
        "equity": {
            k: [round(float(v), 2) for v in e.reindex(first.index)]
            for k, e in equities.items()
        },
        "drawdown": {
            k: [round(float(v), 6) for v in drawdown_series(e).reindex(first.index)]
            for k, e in equities.items()
        },
    }


def _deltas(participants, statistics):
    bh = next(
        (p for p in participants if p["id"] == "buy_and_hold" and p["metrics"]), None
    )
    for p in participants:
        if p["metrics"]:
            p["metrics"]["delta_sharpe"] = (
                None if bh is None else p["metrics"]["sharpe"] - bh["metrics"]["sharpe"]
            )
    return statistics


def _progress(root, total):
    calls = _query(
        root / "provider.sqlite",
        "SELECT slot,count(*),sum(record IS NOT NULL),"
        "count(DISTINCT json_extract(request,'$.decision_session')),"
        "max(json_extract(request,'$.decision_session')),"
        "sum(record IS NOT NULL AND json_extract(record,'$.status')!='ok') FROM calls GROUP BY slot",
    )
    attempts = _query(
        root / "provider.sqlite",
        "SELECT slot,count(*),count(DISTINCT sequence),"
        "sum(json_extract(evidence,'$.state')='TRANSPORT_ERROR'),"
        "sum(json_extract(evidence,'$.state')='RESERVED_BEFORE_TRANSPORT') FROM attempts GROUP BY slot",
    )
    if calls is None:
        return None
    a = {r[0]: r[1:] for r in attempts or []}
    return {
        r[0]: {
            "sessions_started": r[3],
            "sessions_total": total,
            "last_session": r[4],
            "calls_reserved": r[1],
            "calls_recorded": r[2],
            "error_records": r[5],
            "http_attempts": a.get(r[0], (0, 0, 0, 0))[0],
            "retries": a.get(r[0], (0, 0, 0, 0))[0] - a.get(r[0], (0, 0, 0, 0))[1],
            "transport_errors": a.get(r[0], (0, 0, 0, 0))[2],
            "in_flight": a.get(r[0], (0, 0, 0, 0))[3],
        }
        for r in calls
    }


def _read_trades(path):
    with path.open(encoding="utf-8") as stream:
        return [
            {
                **r,
                "price": float(r["price"]),
                "quantity": float(r["quantity"]),
                "cost": float(r["cost"]),
            }
            for r in csv.DictReader(stream)
        ]


def validation(source):
    if source == "demo":
        return demo()
    root = SOURCES[source]
    total = len(_validation_sessions()) - 1
    slots = dict(_query(root / "evaluation.sqlite", "SELECT slot,state FROM slots") or [])
    participants, equities, files = [], {}, {}
    for slot in (*LLM, *BENCHMARKS):
        run = _run_dir(root, slot) if slots.get(slot) == "COMPLETE" else None
        if run is None:
            participants.append(
                {
                    "id": slot,
                    "label": LABELS[slot],
                    "kind": "llm" if slot in LLM else "benchmark",
                    "state": slots.get(slot, "NÃO INICIADO"),
                    "metrics": None,
                }
            )
            continue
        manifest = _json(run / "manifest.json")
        equity = pd.read_csv(run / "equity.csv", index_col="date", parse_dates=True)[
            "equity"
        ]
        equities[slot] = equity
        participants.append(
            {
                **_participant(
                    slot, equity, _read_trades(run / "trades.csv"), manifest["metrics"]
                ),
                "state": "COMPLETE",
                "run_id": run.name,
            }
        )
        files[slot] = [
            {"name": p.name, "sha256": _sha(p), "bytes": p.stat().st_size}
            for p in sorted(run.iterdir())
            if p.is_file()
        ]
    summary = _json(root / "summary.json")
    closure = _json(root / "cost_closure.json")
    dispositions = _query(
        root / "evaluation.sqlite",
        "SELECT spread,participant,state FROM dispositions ORDER BY spread,participant",
    )
    return {
        "source": source,
        "label": SOURCE_LABELS[source],
        "synthetic": False,
        "banner": None,
        "state": source_state(root),
        "participants": participants,
        "curves": _curves(equities) if equities else None,
        "statistics": _deltas(participants, summary and summary["statistics"]),
        "progress": _progress(root, total),
        "costs": _costs(closure["report"]) if closure else None,
        "dispositions": [
            {"spread": r[0], "participant": r[1], "state": r[2]}
            for r in dispositions or []
        ],
        "files": files,
        "root_files": [
            {"name": n, "sha256": _sha(root / n)}
            for n in ROOT_FILES
            if (root / n).is_file()
        ],
    }


def _costs(report):
    out = {}
    for spread, scenario in report.items():
        rows = [
            {
                "id": r["slot"],
                "label": LABELS[r["slot"]],
                "status": r["status"],
                "sharpe": (r.get("metrics") or {}).get("sharpe_ratio"),
                "net_return": (r.get("metrics") or {}).get("total_return"),
                "reason": r.get("reason"),
            }
            for r in scenario["individual"]
        ] + [
            {
                "id": b["kind"],
                "label": LABELS[b["kind"]],
                "status": "COMPLETE_DETERMINISTIC",
                "sharpe": b["metrics"]["sharpe_ratio"],
                "net_return": b["metrics"]["total_return"],
                "reason": None,
            }
            for b in scenario["benchmarks"]
        ]
        out[spread] = {"statistics": scenario["statistics"], "rows": rows}
    return out


def _validation_sessions():
    return _json(CANDIDATE)["protocol"]["windows"]["VALIDATION"]["sessions"]


def run_detail(source, slot):
    """Decisions + trades timeline of one sealed run."""
    if source == "demo":
        return demo_detail(slot)
    run = _run_dir(SOURCES[source], slot)
    if run is None:
        return None
    decisions = []
    if (run / "decisions.jsonl").is_file():
        for line in (run / "decisions.jsonl").read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            decisions.append(
                {
                    k: d.get(k)
                    for k in (
                        "decision_session",
                        "technical_outcome",
                        "vote_counts",
                        "valid_votes",
                        "consensus_reached",
                        "risk_verdict",
                        "risk_source",
                        "risk_rule",
                        "portfolio_decision",
                        "portfolio_source",
                        "portfolio_rule",
                        "final_cause",
                        "target_weight",
                        "observed_weight",
                    )
                }
                | {"errors": len(d.get("errors") or [])}
            )
    return {
        "slot": slot,
        "run_id": run.name,
        "decisions": decisions,
        "trades": _read_trades(run / "trades.csv"),
    }


def trace(source, slot, session):
    """LLM calls (Technical/Risk/Portfolio evidence) for one decision session."""
    if source == "demo":
        return demo_trace(slot, session)
    run = _run_dir(SOURCES[source], slot)
    if run is None or not (run / "llm_calls.jsonl").is_file():
        return None
    keys = (
        "sequence",
        "stage",
        "analyst_id",
        "status",
        "validated_response",
        "technical_evidence",
        "token_usage",
        "attempt_count",
        "retry_count",
        "duration_ms",
        "error_type",
        "error_message",
        "resolved_model",
        "provider_response_id",
        "finish_reason",
        "identity_digest",
        "user_prompt",
    )
    calls = []
    with (run / "llm_calls.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            if f'"decision_session":"{session}"' in line:
                record = json.loads(line)
                calls.append({k: record.get(k) for k in keys})
    return {"slot": slot, "session": session, "calls": calls}


def artifact_path(source, slot, name):
    """Whitelisted file path for download, or None."""
    root = SOURCES.get(source)
    if root is None:
        return None
    if slot == "_root":
        return root / name if name in ROOT_FILES and (root / name).is_file() else None
    run = _run_dir(root, slot) if slot in (*LLM, *BENCHMARKS) else None
    if run is None:
        return None
    names = {p.name for p in run.iterdir() if p.is_file()}
    return run / name if name in names else None


# ── Demo (synthetic, never mixed with real data) ───────────────────────────


def _demo_series():
    rng = random.Random(20261009)
    dates = pd.DatetimeIndex(_validation_sessions())
    price = [30.0]
    for _ in dates[1:]:
        price.append(price[-1] * (1 + rng.gauss(0.0001, 0.019)))
    price = pd.Series(price, index=dates)
    returns = price.pct_change().fillna(0.0)
    positions = {"buy_and_hold": pd.Series(1.0, index=dates)}
    sma = price.rolling(20, min_periods=1).mean()
    positions["sma_regime_h2_proposed"] = (price > sma).astype(float).shift(1).fillna(0.0)
    mid, sd = (
        price.rolling(20, min_periods=1).mean(),
        price.rolling(20, min_periods=2).std().fillna(0),
    )
    positions["bollinger_state_h2_proposed"] = (
        (price < mid - sd).astype(float).shift(1).fillna(0.0)
    )
    for j, slot in enumerate(LLM):
        state, values = 1.0, []
        for _ in dates:
            if rng.random() < 0.04 + 0.01 * j:
                state = 1.0 - state
            values.append(state)
        positions[slot] = pd.Series(values, index=dates).shift(1).fillna(0.0)
    equities, trades = {}, {}
    for slot, pos in positions.items():
        changes = pos.diff().fillna(pos.iloc[0])
        cost = changes.abs() * 0.00082  # 5 bps spread + 3.2 bps taxa sobre o notional
        equity = CAPITAL * (1 + returns * pos - cost).cumprod()
        equity.iloc[0] = CAPITAL
        equities[slot] = equity
        trades[slot] = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "ticker": "PETR4.SA",
                "type": "BUY" if c > 0 else "SELL",
                "price": float(price[d]),
                "quantity": float(equity[d] / price[d]),
                "cost": float(equity[d] * 0.00082),
            }
            for d, c in changes.items()
            if c != 0 and d != dates[0]
        ]
    return dates, price, equities, trades


def demo():
    dates, _, equities, trades = _demo_series()
    participants = [
        {
            **_participant(s, equities[s], trades[s]),
            "state": "COMPLETE",
            "run_id": f"DEMO-{s}",
        }
        for s in (*LLM, *BENCHMARKS)
    ]
    frame_series = {"buy_and_hold": equities["buy_and_hold"].pct_change().iloc[1:]}
    frame_series.update(
        {f"llm_{j}": equities[s].pct_change().iloc[1:] for j, s in enumerate(LLM, 1)}
    )
    statistics = {
        **aggregate(aligned_returns(frame_series, dates[1:])),
        "inference": "DESCRIPTIVE_ONLY",
    }
    costs = {}
    for spread in (0, 5, 10, 20):
        rows = []
        for p in participants:
            shift = (5 - spread) * 0.0004 * p["metrics"]["trades"] / 10
            invalid = spread == 20 and p["id"] == "L02"
            rows.append(
                {
                    "id": p["id"],
                    "label": p["label"],
                    "status": "COST_SENSITIVITY_NOT_ESTIMABLE — EXACT_REPLAY_INVALID"
                    if invalid
                    else (
                        "BASELINE_REUSED"
                        if spread == 5
                        else "COMPLETE_EXACT_REPLAY"
                        if p["kind"] == "llm"
                        else "COMPLETE_DETERMINISTIC"
                    ),
                    "sharpe": None if invalid else p["metrics"]["sharpe"] + shift,
                    "net_return": None
                    if invalid
                    else p["metrics"]["net_return"] + shift / 10,
                    "reason": "ReplayMismatchError (demonstração)" if invalid else None,
                }
            )
        llm = [r["sharpe"] for r in rows if r["id"] in LLM]
        bh = next(r["sharpe"] for r in rows if r["id"] == "buy_and_hold")
        costs[str(spread)] = {
            "statistics": None
            if None in llm
            else {"mean": sum(llm) / 3, "delta": sum(llm) / 3 - bh},
            "rows": rows,
        }
    progress = {
        s: {
            "sessions_started": len(dates) - 1,
            "sessions_total": len(dates) - 1,
            "last_session": str(dates[-2].date()),
            "calls_reserved": 1284 + j,
            "calls_recorded": 1284 + j,
            "error_records": 0,
            "http_attempts": 1286 + 2 * j,
            "retries": 2 + j,
            "transport_errors": 2 + j,
            "in_flight": 0,
        }
        for j, s in enumerate(LLM)
    }
    return {
        "source": "demo",
        "label": SOURCE_LABELS["demo"],
        "synthetic": True,
        "banner": DEMO_BANNER,
        "state": "DEMONSTRAÇÃO",
        "participants": participants,
        "curves": _curves(equities),
        "statistics": _deltas(participants, statistics),
        "progress": progress,
        "costs": costs,
        "dispositions": [],
        "files": {},
        "root_files": [],
    }


def demo_detail(slot):
    if slot not in (*LLM, *BENCHMARKS):
        return None
    dates, _, equities, trades = _demo_series()
    rng = random.Random(f"{slot}-decisions")
    decisions = []
    for d in dates[:-1]:
        votes = {"COMPRA": rng.randint(0, 5)}
        votes["VENDA"] = rng.randint(0, 5 - votes["COMPRA"])
        votes["MANTER"] = 5 - votes["COMPRA"] - votes["VENDA"]
        outcome = max(votes, key=votes.get)
        decisions.append(
            {
                "decision_session": str(d.date()),
                "technical_outcome": outcome,
                "vote_counts": votes,
                "valid_votes": 5,
                "consensus_reached": votes[outcome] >= 3,
                "risk_verdict": "APROVADO",
                "risk_source": "AUTO_APPROVE",
                "risk_rule": None,
                "portfolio_decision": outcome,
                "portfolio_source": "RULE",
                "portfolio_rule": None,
                "final_cause": "DEMO",
                "target_weight": None,
                "observed_weight": None,
                "errors": 0,
            }
        )
    return {
        "slot": slot,
        "run_id": f"DEMO-{slot}",
        "synthetic": True,
        "banner": DEMO_BANNER,
        "decisions": decisions if slot in LLM else [],
        "trades": trades[slot],
    }


def demo_trace(slot, session):
    rng = random.Random(f"{slot}-{session}")
    calls = [
        {
            "sequence": i,
            "stage": "technical_analyst",
            "analyst_id": i + 1,
            "status": "ok",
            "validated_response": {
                "signal": rng.choice(["COMPRA", "MANTER", "VENDA"]),
                "confidence": round(rng.uniform(0.4, 0.9), 2),
            },
            "technical_evidence": None,
            "token_usage": {"prompt_tokens": 1100, "completion_tokens": 180},
            "attempt_count": 1,
            "retry_count": 0,
            "duration_ms": rng.randint(2000, 4000),
            "error_type": None,
            "error_message": None,
            "resolved_model": "demo",
            "provider_response_id": None,
            "finish_reason": "STOP",
            "identity_digest": None,
            "user_prompt": "(demonstração — sem prompt real)",
        }
        for i in range(5)
    ]
    return {
        "slot": slot,
        "session": session,
        "synthetic": True,
        "banner": DEMO_BANNER,
        "calls": calls,
    }
