"""Allowlisted projections of prospective paper records; no provider envelopes."""

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_h2_v6_forward as fwd  # noqa: E402

OUTPUT = fwd.OUTPUT
STRATEGIES = {
    "ai": "IA H2 v6",
    "buy_and_hold": "Buy & Hold",
    "sma_regime_h2_proposed": "SMA Regime 50/200",
    "bollinger_state_h2_proposed": "Bollinger Estado 20/2",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def pick(value, *keys):
    return {k: (value or {}).get(k) for k in keys}


def session_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("invalid session")
    from datetime import date

    date.fromisoformat(value)
    return value


def history(root=OUTPUT):
    state = read(root / "state.json") or {}
    sessions = root / "sessions"
    result = {
        r["session"]: {"session": r["session"], "status": r.get("decision", "MISSED")}
        for r in state.get("sessions", [])
    }
    for path in sorted(sessions.glob("????-??-??/input.json")):
        session = session_name(path.parent.name)
        d = read(path.parent / "decision.json")
        result[session] = {
            "session": session,
            "status": d["status"] if d else "AGUARDANDO",
            "target_session": read(path)["target_session"],
        }
    return sorted(result.values(), key=lambda r: r["session"])


def decision(session=None, root=OUTPUT):
    entries = history(root)
    session = (
        session_name(session)
        if session
        else (entries[-1]["session"] if entries else None)
    )
    if session is None:
        return None
    folder = root / "sessions" / session
    data, d = read(folder / "input.json"), read(folder / "decision.json")
    if data is None:
        return {"session": session, "status": "MISSED", "analysts": []}
    d = d or {}
    record, risk = d.get("record") or {}, d.get("risk_verdict") or {}
    analysts = []
    # A trace may have several failed attempts for one analyst. Preserve them;
    # never manufacture a missing vote or promote a failed response to a vote.
    trace = folder / "llm_trace.jsonl"
    if trace.is_file():
        for line in trace.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("stage") != "technical_analyst":
                continue
            response = r.get("validated_response") or {}
            analysts.append(
                {
                    **pick(r, "analyst_id", "sequence", "status"),
                    **pick(response, "signal", "confidence"),
                    "evidence": [
                        pick(e, "code", "role") for e in response.get("evidence", [])
                    ],
                    "explanation": (r.get("technical_evidence") or {}).get(
                        "rendered_explanation"
                    ),
                }
            )
    counts = collections.Counter(
        (e["code"], e["role"]) for a in analysts for e in a["evidence"]
    )
    state = read(root / "state.json") or {}
    execution = next(
        (r for r in state.get("sessions", []) if r.get("executed_decision") == session),
        None,
    )
    params = read(fwd.CANDIDATE)["protocol"]["participant_spec"]["params"]
    rules = []
    chain = (
        ("VOLATILITY", "recent_volatility", "risk_max_volatility", ">"),
        ("DRAWDOWN", "current_drawdown", "risk_max_drawdown", ">"),
        ("CONCENTRATION", "current_concentration", "risk_max_concentration", ">="),
    )
    stopped = record.get("risk_source") == "AUTO_APPROVE"
    for name, metric, limit, operator in chain:
        status = (
            "NÃO AVALIADA"
            if stopped or not record
            else "DISPAROU"
            if record.get("risk_rule") == name
            else "PASSOU"
        )
        rules.append(
            {
                "rule": name,
                "value": (risk.get("risk_metrics") or {}).get(metric),
                "limit": params.get(limit),
                "operator": operator,
                "status": status,
            }
        )
        stopped = stopped or status == "DISPAROU"
    before = record.get("observed_weight")
    effective = (
        record.get("technical_outcome") == "COMPRA"
        and before is not None
        and before < params.get("long_target_weight", 1)
    )
    return {
        "session": session,
        "ticker": data["ticker"],
        **pick(data, "target_session", "target_open_deadline", "close_used"),
        "status": d.get("status", "AGUARDANDO"),
        **pick(d, "generated_at", "replayed_from_journal", "llm_calls"),
        "failure": "Falha registrada; consultar diagnóstico local / recuperação por replay."
        if d.get("failure")
        else None,
        "analysts": analysts,
        "evidence_summary": [
            {"code": code, "role": role, "count": n}
            for (code, role), n in counts.most_common()
        ],
        "consensus": {
            **pick(
                record,
                "vote_counts",
                "valid_votes",
                "consensus_threshold",
                "consensus_reached",
                "technical_outcome",
            ),
            "signal": pick(
                d.get("technical_signal"), "signal", "confidence", "justification"
            ),
        },
        "risk": {
            **pick(risk, "verdict", "analysis"),
            "metrics": pick(
                risk.get("risk_metrics"),
                "recent_volatility",
                "current_drawdown",
                "current_concentration",
            ),
            **pick(record, "risk_source", "risk_rule"),
            "rules": rules,
            "veto_effect": ("EFETIVO" if effective else "SEM EFEITO")
            if risk.get("verdict") == "VETADO"
            else None,
        },
        "portfolio": {
            **pick(d.get("portfolio_action"), "decision", "reasoning"),
            **pick(
                record,
                "portfolio_source",
                "portfolio_rule",
                "final_cause",
                "observed_weight",
                "target_weight",
            ),
        },
        "pending": pick(
            state.get("pending"), "decision_session", "target_session", "target_weight"
        )
        if (state.get("pending") or {}).get("decision_session") == session
        else None,
        "execution": {
            "session": execution["session"],
            "trades": [
                pick(t, "type", "price", "quantity", "cost") for t in execution["trades"]
            ],
        }
        if execution
        else None,
        "position_at_decision": pick(
            d.get("portfolio_at_close"), "cash", "units", "equity"
        ),
    }


def wallet(key, book, rows, mark, pending, initial, decisions):
    close = mark["close"] if mark else 0
    value = book.get("units", 0) * close
    equity = book.get("cash", initial) + value
    trade_key = "benchmark_trades" if key == "buy_and_hold" else "trades"
    trades = [
        {"session": r["session"], **pick(t, "type", "price", "quantity", "cost")}
        for r in rows
        for t in r.get(trade_key, [])
    ]
    return {
        "key": key,
        "label": STRATEGIES[key],
        "available": True,
        "equity": equity,
        "return": equity / initial - 1,
        "composition": [
            {
                "asset": "PETR4",
                "value": value,
                "weight": value / equity if equity else 0,
                "units": book.get("units", 0),
            },
            {
                "asset": "Caixa",
                "value": book.get("cash", initial),
                "weight": book.get("cash", initial) / equity if equity else 0,
            },
        ],
        "position_count": int(book.get("units", 0) > 0),
        "marked_value": value,
        "exposure": value / equity if equity else 0,
        "costs": sum(t["cost"] for t in trades),
        "curve": [
            {
                "session": r["session"],
                "equity": r["benchmark_equity" if key == "buy_and_hold" else "equity"],
            }
            for r in rows
        ],
        "trades": trades,
        "pending": pending,
        "last_decision": decisions[-1] if decisions else None,
        "mark": mark,
        "initial_capital": initial,
    }


def portfolios(root=OUTPUT):
    state = read(root / "state.json")
    if state is None:
        return {"classification": fwd.CLASSIFICATION, "wallets": []}
    rows, mark = state["sessions"], state["mark"]
    bh_pending = (
        {
            "target_session": str(
                fwd.target_open(fwd._timestamp(mark["session"])).date()
            ),
            "target_weight": 1,
        }
        if mark and not state["benchmark"]["invested"]
        else None
    )
    wallets = [
        wallet(
            "ai",
            state["portfolio"],
            rows,
            mark,
            state["pending"],
            state["initial_capital"],
            state["decisions"],
        ),
        wallet(
            "buy_and_hold",
            state["benchmark"],
            rows,
            mark,
            bh_pending,
            state["initial_capital"],
            [],
        ),
    ]
    wallets.extend(
        {
            "key": k,
            "label": STRATEGIES[k],
            "available": False,
            "reason": "Carteira prospectiva ainda não inicializada; nenhuma curva histórica utilizada.",
        }
        for k in tuple(STRATEGIES)[2:]
    )
    return {
        "classification": fwd.CLASSIFICATION,
        "paper_only": True,
        "wallets": wallets,
        "mark": mark,
    }
