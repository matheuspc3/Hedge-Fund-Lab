"""Read-only H2 v6 dashboard API. Reads sealed artifacts and journals; never writes.

No endpoint starts inference, reads credentials or touches Final Test results.
Demo payloads are generated synthetic data and always carry ``synthetic: true``.
"""

import collections
import csv
import functools
import itertools
import json
import math
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
            "annualized_return": metrics["annualized_return"],
            "volatility": metrics["annualized_volatility"],
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
        "return": {
            k: [round(float(v / e.iloc[0] - 1), 6) for v in e.reindex(first.index)]
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
                "id": b["kind"].split("-cost-")[0],
                "label": LABELS[b["kind"].split("-cost-")[0]],
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


# ── Post-Validation analysis (sealed artifacts only) ───────────────────────
# Prices are the closes implied by the sealed Buy & Hold curve plus the opens of
# executed trades; SMAs come from the sma*_gap features the analysts received.
# The snapshot is never opened (it holds the Final Test period). Nothing here
# selects, tunes or re-runs anything: it reshapes what the runs recorded.

OA1_BANNER = "VALIDATION OA-1 — NÃO RATIFICADA ACADEMICAMENTE"
TA, RISK, PM = "technical_analyst", "risk_manager", "portfolio_manager"
# Order of the hard rules a COMPRA goes through (src/agents/risk_manager.py).
RISK_CHAIN = (
    ("VOLATILITY", "recent_volatility", "risk_max_volatility", ">"),
    ("DRAWDOWN", "current_drawdown", "risk_max_drawdown", ">"),
    ("CONCENTRATION", "current_concentration", "risk_max_concentration", "≥"),
)


@functools.lru_cache(maxsize=32)
def _cached(path, _stamp, parse):
    return parse(Path(path))


def _load(path, parse):
    """Parse a file once per version (mtime); None if absent."""
    return _cached(str(path), path.stat().st_mtime_ns, parse) if path.is_file() else None


def _parse_equity(path):
    # round_trip: the default parser is 1 ulp off (OA-1 diagnostic §0).
    frame = pd.read_csv(path, index_col="date", parse_dates=True, float_precision="round_trip")
    return dict(zip(frame.index.strftime("%Y-%m-%d"), frame["equity"].tolist()))


def _parse_decisions(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    return {d["decision_session"]: d for d in map(json.loads, filter(None, lines))}


def _prompt(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def _parse_calls(path):
    """LLM trace slimmed to what the analysis shows; raw envelopes stay on disk."""
    sessions = collections.defaultdict(list)
    with path.open(encoding="utf-8") as stream:
        for line in filter(str.strip, stream):
            r = json.loads(line)
            sessions[r["decision_session"]].append(
                {
                    "sequence": r.get("sequence"),
                    "stage": r.get("stage"),
                    "analyst_id": r.get("analyst_id"),
                    "status": r.get("status"),
                    "response": r.get("validated_response"),
                    "prompt": _prompt(r.get("user_prompt")),
                    "explanation": (r.get("technical_evidence") or {}).get(
                        "rendered_explanation"
                    ),
                    "response_id": r.get("provider_response_id"),
                }
            )
    return dict(sessions)


def _runs(root):
    """Sealed runs of a source (COMPLETE slots only, never a run in progress)."""
    slots = dict(_query(root / "evaluation.sqlite", "SELECT slot,state FROM slots") or [])
    out = {}
    for slot in (*LLM, *BENCHMARKS):
        run = _run_dir(root, slot) if slots.get(slot) == "COMPLETE" else None
        if run is None or not (run / "equity.csv").is_file():
            continue
        manifest = _json(run / "manifest.json") or {}
        out[slot] = {
            "dir": run,
            "equity": _load(run / "equity.csv", _parse_equity),
            "trades": _read_trades(run / "trades.csv"),
            "decisions": _load(run / "decisions.jsonl", _parse_decisions),
            "calls": _load(run / "llm_calls.jsonl", _parse_calls) or {},
            "params": manifest.get("participant", {}).get("params", {}),
        }
    return out


def _market(runs):
    """Closes from the B&H curve: close = (equity - cash) / quantity, cash ≈ 1e-12."""
    bh = runs.get("buy_and_hold")
    if bh is None or not bh["trades"]:
        return None
    first, equity = bh["trades"][0], bh["equity"]
    cash = CAPITAL - first["price"] * first["quantity"] - first["cost"]
    close = {
        d: (v - cash) / first["quantity"] if d >= first["date"] else None
        for d, v in equity.items()
    }
    features = next(
        (
            {
                s: next(((c["prompt"] or {}).get("features") for c in cs if c["stage"] == TA), None)
                or {}
                for s, cs in runs[slot]["calls"].items()
            }
            for slot in LLM
            if slot in runs and runs[slot]["calls"]
        ),
        {},
    )

    def level(key):  # gap = close / level - 1, recorded with 6 decimals
        return [
            None
            if close[d] is None or key not in features.get(d, {})
            else round(close[d] / (1 + features[d][key]), 4)
            for d in equity
        ]

    return {
        "dates": list(equity),
        "close": [None if v is None else round(v, 6) for v in close.values()],
        "sma50": level("sma50_gap"),
        "sma200": level("sma200_gap"),
    }


def _states(dates, trades):
    """Position at each session close; execution days are entry/exit."""
    # ponytail: one order per session (true for 0%/100% sizing); two orders on
    # the same day would keep only the last one.
    kinds = {t["date"]: t["type"] for t in trades}
    held, out = False, []
    for day in dates:
        kind = kinds.get(day)
        held = {"BUY": True, "SELL": False}.get(kind, held)
        out.append({"BUY": "entry", "SELL": "exit"}.get(kind, "long" if held else "cash"))
    return out


def _exposure(states, asset_log):
    """Two different denominators, kept apart: positions at the decision closes
    (dates[:-1]) and the attribution of the daily returns (dates[1:])."""
    closes, days = states[:-1], states[1:]
    long_closes = sum(s in ("long", "entry") for s in closes)
    return {
        "closes": {
            "long": long_closes,
            "cash": len(closes) - long_closes,
            "total": len(closes),
            "share": long_closes / len(closes) if closes else None,
        },
        "daily": {
            k: {
                "days": days.count(k),
                "asset_return": math.expm1(sum(r for s, r in zip(days, asset_log) if s == k)),
            }
            for k in ("long", "cash", "entry", "exit")
        },
        "daily_total": len(days),
    }


def _ledger(trades, equity, prev):
    cash, out = CAPITAL, []
    for t in trades:
        notional = t["price"] * t["quantity"]
        cash += -(notional + t["cost"]) if t["type"] == "BUY" else notional - t["cost"]
        out.append(
            {
                **t,
                "decision_session": prev.get(t["date"]),
                "notional": notional,
                "cash_after": cash,
                "equity_close": equity.get(t["date"]),
            }
        )
    return out


def _cycles(ledger, equity, dates, close):
    """BUY→SELL round trips; a position still open is marked at the last close."""
    out, entry = [], None
    for t in [*ledger, None]:
        if t is not None and t["type"] == "BUY":
            entry = t
            continue
        if entry is None:
            continue
        end = t["date"] if t else dates[-1]
        exit_price = t["price"] if t else close.get(end)
        costs = entry["cost"] + (t["cost"] if t else 0.0)
        out.append(
            {
                "entry_decision": entry["decision_session"],
                "entry": entry["date"],
                "entry_price": entry["price"],
                "exit_decision": t["decision_session"] if t else None,
                "exit": end,
                "exit_price": exit_price,
                "status": "CLOSED" if t else "OPEN",
                "sessions": dates.index(end) - dates.index(entry["date"]),
                "price_change": None if exit_price is None else exit_price / entry["price"] - 1,
                "pnl": None
                if exit_price is None
                else entry["quantity"] * (exit_price - entry["price"]) - costs,
                "costs": costs,
                "equity_after": equity.get(end),
            }
        )
        entry = None
    return out


def _implied(d, target):
    """Order the technical consensus alone implies, given the position at t."""
    weight = d.get("observed_weight")
    if weight is None:
        return None
    if d["technical_outcome"] == "COMPRA" and weight < target:
        return "BUY"
    return "SELL" if d["technical_outcome"] == "VENDA" and weight > 0 else None


def _executed(run, nxt):
    traded = {t["date"]: t["type"] for t in run["trades"]}
    return {s: traded.get(nxt.get(s)) for s in run["decisions"]}


def _agents(run, nxt):
    """Called / decided / changed the trajectory, per layer of one LLM run."""
    decisions, target = run["decisions"], run["params"].get("long_target_weight", 1.0)
    executed = _executed(run, nxt)
    implied = {s: _implied(d, target) for s, d in decisions.items()}
    calls = [c for cs in run["calls"].values() for c in cs]
    by_stage = {k: [c for c in calls if c["stage"] == k] for k in (TA, RISK, PM)}
    analysts = collections.defaultdict(collections.Counter)
    for c in by_stage[TA]:
        analysts[c["analyst_id"]][(c["response"] or {}).get("signal", "INVÁLIDO")] += 1
    vetoes = [s for s, d in decisions.items() if d["risk_verdict"] == "VETADO"]
    pm_called = [s for s, d in decisions.items() if d.get("portfolio_called")]
    pm_changed = [
        s for s in pm_called if decisions[s].get("portfolio_decision") != decisions[s]["technical_outcome"]
    ]
    margins = collections.Counter(
        f"{max(d['vote_counts'].values())}/{d['valid_votes']}" if d.get("consensus_reached") else "sem maioria"
        for d in decisions.values()
    )
    flow = collections.Counter(
        (
            d["technical_outcome"],
            "VETADO" if d["risk_verdict"] == "VETADO" else d.get("portfolio_decision") or "—",
            executed[s] or "—",
        )
        for s, d in decisions.items()
    )
    return {
        "sessions": len(decisions),
        "technical": {
            "calls": len(by_stage[TA]),
            "valid_votes": sum(d.get("valid_votes") or 0 for d in decisions.values()),
            "consensus": collections.Counter(d["technical_outcome"] for d in decisions.values()),
            "margins": margins,
            "analysts": {str(k): analysts[k] for k in sorted(analysts)},
            "implied_orders": sum(v is not None for v in implied.values()),
        },
        "risk": {
            "evaluated": sum(d.get("risk_verdict") is not None for d in decisions.values()),
            "rules": [
                {"source": k[0], "rule": k[1], "verdict": k[2], "count": n}
                for k, n in collections.Counter(
                    (d["risk_source"], d["risk_rule"], d["risk_verdict"]) for d in decisions.values()
                ).most_common()
            ],
            "llm_calls": len(by_stage[RISK]),
            "llm_approved": sum((c["response"] or {}).get("verdict") == "APROVADO" for c in by_stage[RISK]),
            "vetoes": len(vetoes),
            "vetoes_effective": sum(implied[s] == "BUY" for s in vetoes),
        },
        "portfolio": {
            "called": len(pm_called),
            "llm_calls": len(by_stage[PM]),
            "decisions": collections.Counter(decisions[s].get("portfolio_decision") for s in pm_called),
            "followed": len(pm_called) - len(pm_changed),
            "changed": len(pm_changed),
            "changed_effective": sum(implied[s] != executed[s] for s in pm_changed),
        },
        "orders": {
            "executed": len(run["trades"]),
            "differs_from_consensus": sum(implied[s] != executed[s] for s in decisions),
        },
        "flow": [
            {"technical": k[0], "final": k[1], "executed": k[2], "count": n}
            for k, n in sorted(flow.items())
        ],
    }


def _cross(runs, nxt):
    """Agreement among L01/L02/L03: votes, outcomes, orders and financial bytes."""
    present = [s for s in LLM if s in runs and runs[s]["decisions"]]
    if len(present) < 2:
        return None
    votes = {
        s: {
            (day, c["analyst_id"]): (c["response"] or {}).get("signal")
            for day, cs in runs[s]["calls"].items()
            for c in cs
            if c["stage"] == TA
        }
        for s in present
    }
    executed = {s: _executed(runs[s], nxt) for s in present}
    common = sorted(set.intersection(*(set(runs[s]["decisions"]) for s in present)))

    def outcome(s, day):
        return runs[s]["decisions"][day]["technical_outcome"]

    def same_bytes(a, b, name):
        return (runs[a]["dir"] / name).read_bytes() == (runs[b]["dir"] / name).read_bytes()

    return {
        "sessions": len(common),
        "outcome_divergent": sum(len({outcome(s, d) for s in present}) > 1 for d in common),
        "order_divergent": sum(len({executed[s][d] for s in present}) > 1 for d in common),
        "pairs": [
            {
                "pair": f"{a} vs {b}",
                "votes": len(votes[a]),
                "same_votes": sum(votes[a][k] == votes[b].get(k) for k in votes[a]),
                "vote_counts_divergent": sum(
                    runs[a]["decisions"][d]["vote_counts"] != runs[b]["decisions"][d]["vote_counts"]
                    for d in common
                ),
                "outcome_divergent": sum(outcome(a, d) != outcome(b, d) for d in common),
                "order_divergent": sum(executed[a][d] != executed[b][d] for d in common),
                "identical_equity_and_trades": same_bytes(a, b, "equity.csv")
                and same_bytes(a, b, "trades.csv"),
            }
            for a, b in itertools.combinations(present, 2)
        ],
    }


def analysis(source):
    """Prices x decisions, positions, cycles, exposure and multi-agent behaviour."""
    root = SOURCES.get(source)  # demo has no traces; unknown sources never resolve
    runs = _runs(root) if root else {}
    market = _market(runs)
    if market is None:
        return None
    dates = market["dates"]
    prev, nxt = dict(zip(dates[1:], dates[:-1])), dict(zip(dates[:-1], dates[1:]))
    close = dict(zip(dates, market["close"]))
    bh = list(runs["buy_and_hold"]["equity"].values())
    asset_log = [math.log(b / a) for a, b in zip(bh, bh[1:])]
    participants = {}
    for slot, run in runs.items():
        states = _states(dates, run["trades"])
        ledger = _ledger(run["trades"], run["equity"], prev)
        participants[slot] = {
            "label": LABELS[slot],
            "kind": "llm" if slot in LLM else "benchmark",
            "run_id": run["dir"].name,
            "trades": ledger,
            "long": [int(s in ("long", "entry")) for s in states],
            "cycles": _cycles(ledger, run["equity"], dates, close),
            "exposure": _exposure(states, asset_log),
        }
    return {
        "source": source,
        "label": SOURCE_LABELS[source],
        "synthetic": False,
        "banner": OA1_BANNER if source == "provisional" else None,
        "state": source_state(root),
        "market": market,
        "participants": participants,
        "agents": {s: _agents(runs[s], nxt) for s in LLM if s in runs and runs[s]["decisions"]},
        "cross_runs": _cross(runs, nxt),
    }


def decision(source, slot, session):
    """Technical → Risk → Portfolio → execution for one decision session."""
    root = SOURCES.get(source)
    run = _runs(root).get(slot) if root and slot in LLM else None
    if run is None or not run["decisions"] or session not in run["decisions"]:
        return None
    d, params = run["decisions"][session], run["params"]
    dates = list(run["equity"])
    i = dates.index(session)
    nxt = dates[i + 1] if i + 1 < len(dates) else None
    sessions = sorted(run["decisions"])
    k = sessions.index(session)
    calls = run["calls"].get(session, [])
    ta = sorted((c for c in calls if c["stage"] == TA), key=lambda c: c["analyst_id"] or 0)
    risk = next((c for c in calls if c["stage"] == RISK), None)
    pm = next((c for c in calls if c["stage"] == PM), None)
    equity = list(run["equity"].values())[: i + 1]
    drawdown = round(1 - equity[-1] / max(equity), 6) + 0.0  # canonical_number
    recorded = (risk and (risk["prompt"] or {}).get("risk_metrics")) or (
        pm and ((pm["prompt"] or {}).get("risk_verdict") or {}).get("risk_metrics")
    )
    sent = ((pm or risk or {}).get("prompt") or {}).get("technical_signal")
    target = params.get("long_target_weight", 1.0)
    implied = _implied(d, target)

    if d["risk_source"] == "AUTO_APPROVE":
        rules = [{"rule": "AUTO_APPROVE", "status": "APLICADA", "limit": None, "value": None}]
    else:
        chain, fired = [r[0] for r in RISK_CHAIN], d.get("risk_rule")
        stop = chain.index(fired) if fired in chain else (-1 if fired else len(chain))
        rules = [{"rule": fired, "status": "DISPAROU", "limit": None, "value": None}] if stop == -1 else []
        for j, (rule, metric, param, op) in enumerate(RISK_CHAIN):
            value = (recorded or {}).get(metric)
            rules.append(
                {
                    "rule": rule,
                    "status": "PASSOU" if j < stop else "DISPAROU" if j == stop else "NÃO AVALIADA",
                    "limit": f"{op} {params.get(param)}",
                    "value": drawdown if value is None and rule == "DRAWDOWN" else value,
                }
            )
        rules.append(
            {
                "rule": "RISK_LLM",
                "status": d["risk_verdict"] if d["risk_source"] == "LLM" else "NÃO CHAMADO",
                "limit": None,
                "value": None,
            }
        )
    trade = next(
        (
            t
            for t in _ledger(run["trades"], run["equity"], dict(zip(dates[1:], dates[:-1])))
            if t["date"] == nxt
        ),
        None,
    )
    before = d.get("observed_weight")
    evidence = collections.Counter(
        (e.get("code"), e.get("role"))
        for c in ta
        for e in (c["response"] or {}).get("evidence") or []
    )
    return {
        "slot": slot,
        "run_id": run["dir"].name,
        "session": session,
        "execution_session": nxt,
        "prev_session": sessions[k - 1] if k else None,
        "next_session": sessions[k + 1] if k + 1 < len(sessions) else None,
        "final_cause": d.get("final_cause"),
        "errors": d.get("errors") or [],
        "technical": {
            "analysts": [
                {
                    "analyst_id": c["analyst_id"],
                    "sequence": c["sequence"],
                    "status": c["status"],
                    "signal": (c["response"] or {}).get("signal"),
                    "confidence": (c["response"] or {}).get("confidence"),
                    "evidence": (c["response"] or {}).get("evidence"),
                    "explanation": c["explanation"],
                    "response_id": c["response_id"],
                }
                for c in ta
            ],
            "features": (ta[0]["prompt"] or {}).get("features") if ta else None,
            "evidence_summary": [
                {"code": code, "role": role, "count": n} for (code, role), n in evidence.most_common()
            ],
            "vote_counts": d.get("vote_counts"),
            "valid_votes": d.get("valid_votes"),
            "threshold": d.get("consensus_threshold"),
            "consensus_reached": d.get("consensus_reached"),
            "outcome": d["technical_outcome"],
            "signal_sent": sent,
        },
        "risk": {
            "verdict": d["risk_verdict"],
            "source": d["risk_source"],
            "rule": d.get("risk_rule"),
            "rules": rules,
            "analysis": (risk["response"] or {}).get("analysis") if risk else None,
            "sequence": risk["sequence"] if risk else None,
            "recorded_metrics": recorded,
            "drawdown": drawdown,
            "veto_effect": None
            if d["risk_verdict"] != "VETADO"
            else "EFETIVO"
            if implied == "BUY"
            else "SEM EFEITO",
        },
        "portfolio": {
            "called": bool(d.get("portfolio_called")),
            "source": d.get("portfolio_source"),
            "rule": d.get("portfolio_rule"),
            "decision": d.get("portfolio_decision"),
            "reasoning": (pm["response"] or {}).get("reasoning") if pm else None,
            "sequence": pm["sequence"] if pm else None,
            "followed_consensus": None
            if d.get("portfolio_decision") is None
            else d["portfolio_decision"] == d["technical_outcome"],
            "weight_before": before,
            "weight_after": {"BUY": target, "SELL": 0.0}[trade["type"]] if trade else before,
            "target_weight": d.get("target_weight"),
        },
        "execution": {
            "implied_by_consensus": implied,
            "trade": trade,
            "equity_at_decision": equity[-1],
        },
    }


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
