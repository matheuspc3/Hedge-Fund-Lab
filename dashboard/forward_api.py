"""Allowlisted projections of prospective paper records; no provider envelopes."""

import collections
import json
import os
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
    if os.name != "nt":
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    # Windows readers must share DELETE or they can block the runner's atomic
    # state.json replacement. O_TEMPORARY also shares DELETE but deletes data.
    import ctypes
    import msvcrt
    from ctypes import wintypes

    create = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
    create.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create.restype = wintypes.HANDLE
    handle = create(str(path), 0x80000000, 7, None, 3, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        error = ctypes.get_last_error()
        if error in (2, 3):
            return None
        raise ctypes.WinError(error)
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except OSError:
        ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(handle))
        raise
    with os.fdopen(fd, "r", encoding="utf-8") as stream:
        contents = stream.read()
    return json.loads(contents)


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
            "has_decision": d is not None,
        }
    return sorted(result.values(), key=lambda r: r["session"])


def decision(session=None, root=OUTPUT):
    entries = history(root)
    recorded = [entry for entry in entries if entry.get("has_decision")]
    session = (
        session_name(session)
        if session
        else ((recorded or entries)[-1]["session"] if entries else None)
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
    stopped = record.get("risk_source") not in ("LLM", "HARD_RULE") or record.get(
        "risk_rule"
    ) in ("MISSING_SIGNAL", "MISSING_METRICS")
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
    known_effect = record.get("technical_outcome") in ("VENDA", "MANTER") or (
        record.get("technical_outcome") == "COMPRA" and before is not None
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
            if risk.get("verdict") == "VETADO" and known_effect
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
        "pending": pick(pending, "decision_session", "target_session", "target_weight")
        if pending
        else None,
        "last_decision": pick(
            decisions[-1],
            "session",
            "status",
            "target_weight",
            "target_session",
            "generated_at",
        )
        if decisions
        else None,
        "mark": pick(mark, "session", "close") if mark else None,
        "initial_capital": initial,
    }


def portfolios(root=OUTPUT, benchmark_root=None):
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
    benchmark_root = benchmark_root or ROOT / "data/forward/h2_v6_benchmarks"
    notes = []
    for key in tuple(STRATEGIES)[2:]:
        benchmark = read(benchmark_root / key / "state.json")
        if benchmark is None:
            wallets.append(
                {
                    "key": key,
                    "label": STRATEGIES[key],
                    "available": False,
                    "reason": "Sem carteira prospectiva. Inicialização só é permitida antes da primeira abertura; backfill e ordens retroativas são proibidos.",
                }
            )
            continue
        comparable = (
            benchmark["strategy"] == key
            and benchmark["strategy_sha256"]
            == next(
                b["sha256"]
                for b in read(fwd.CANDIDATE)["protocol"]["benchmarks"]
                if b["spec"]["kind"] == key
            )
            and benchmark["inception"] == rows[0]["session"]
            and benchmark["initial_capital"] == state["initial_capital"]
            and benchmark["costs"] == state["costs"]
            and benchmark["execution"] == state["execution"]
            and benchmark["manifest_sha256"] == state["manifest_sha256"]
            and [(r["session"], r["open"], r["close"]) for r in benchmark["sessions"]]
            == [(r["session"], r["open"], r["close"]) for r in rows]
        )
        item = wallet(
            key,
            benchmark["portfolio"],
            benchmark["sessions"],
            benchmark["mark"],
            benchmark["pending"],
            benchmark["initial_capital"],
            benchmark["decisions"],
        )
        item["comparable"] = comparable
        item["initialized_at"] = benchmark["initialized_at"]
        if not comparable:
            notes.append(
                f"{STRATEGIES[key]}: marcação/início/identidade divergente; excluída do gráfico comparativo. Sincronize os ledgers com os mesmos inputs observados."
            )
        wallets.append(item)
    return {
        "classification": fwd.CLASSIFICATION,
        "paper_only": True,
        "wallets": wallets,
        "mark": pick(mark, "session", "close") if mark else None,
        "comparison_note": " ".join(notes)
        or "Curvas prospectivas na mesma data de início, com mesmo capital, custos e preços observados. Um único fechamento não permite medir evolução.",
    }
