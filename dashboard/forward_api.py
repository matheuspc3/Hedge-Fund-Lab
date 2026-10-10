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
        record = (d or {}).get("record") or {}
        result[session] = {
            "session": session,
            "status": d["status"] if d else "AGUARDANDO",
            "target_session": read(path)["target_session"],
            "has_decision": d is not None,
            # Recorded summaries only, so past votes compare without opening traces.
            **pick(record, "vote_counts", "technical_outcome", "target_weight"),
            "final_decision": ((d or {}).get("portfolio_action") or {}).get("decision"),
        }
    return sorted(result.values(), key=lambda r: r["session"])


def trace_rows(folder):
    path = folder / "llm_trace.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def evidence_labels(evidence, explanation):
    """Labels come from the recorded rendering, which carries RSI/width values.

    ponytail: splits the canonical "display — role; ..." rendering; if its shape
    ever differs from the evidence list, fall back to the closed vocabulary.
    """
    from src.agents.technical_evidence import EVIDENCE_DISPLAY

    parts = (explanation or "").split("; ")
    if len(parts) == len(evidence) and all(" — " in p for p in parts):
        return [p.split(" — ")[0] for p in parts]
    return [EVIDENCE_DISPLAY.get(e["code"], e["code"]) for e in evidence]


def stance(role, outcome):
    """Evidence role relative to the aggregated technical outcome."""
    if role == "CAUTION":
        return "caution"
    if role == "NEUTRAL":
        return "neutral"
    if outcome not in ("COMPRA", "VENDA"):
        # Without a directional outcome, "favorable" has no referent.
        return role.lower()
    return "favorable" if role == f"SUPPORTS_{outcome}" else "contrary"


def br(value):
    return "/".join(reversed(value.split("-"))) if value else "N/D"


def share(value):
    return "N/D" if value is None else f"{value * 100:.4g}%".replace(".", ",")


def order_state(d):
    """Separate the recommended target from what the ledger actually did."""
    p, status = d["portfolio"], d["status"]
    if status == "FAILED":
        return {
            "state": "SEM_ORDEM",
            "label": "Sem ordem",
            "detail": "Falha registrada; posição mantida.",
        }
    if status == "LATE_NOT_EXECUTABLE":
        return {
            "state": "NAO_EXECUTAVEL",
            "label": "Não executável",
            "detail": "Decisão concluída após a abertura-alvo; nenhuma ordem foi criada.",
        }
    if status != "DECIDED":
        return {
            "state": "SEM_DECISAO",
            "label": "Sem decisão",
            "detail": "Nenhuma decisão gravada para esta sessão; posição mantida.",
        }
    if d["execution"]:
        n = len(d["execution"]["trades"])
        return {
            "state": "EXECUTADA" if n else "RECONCILIADA",
            "label": "Executada" if n else "Reconciliada sem operação",
            "detail": f"{n} operação(ões) na abertura de {br(d['execution']['session'])}, ao preço observado."
            if n
            else f"Reconciliada na abertura de {br(d['execution']['session'])}; nenhuma operação foi necessária.",
        }
    if d["pending"]:
        return {
            "state": "PENDENTE",
            "label": "Pendente",
            "detail": f"Alvo {share(d['pending']['target_weight'])} na abertura de {br(d['pending']['target_session'])}; aguarda o preço observado e a reconciliação.",
        }
    if p.get("target_weight") is not None and p.get("target_weight") == p.get(
        "observed_weight"
    ):
        return {
            "state": "SEM_ALTERACAO",
            "label": "Sem ordem necessária",
            "detail": "Alvo igual à posição observada no fechamento.",
        }
    return {
        "state": "PRETENDIDA",
        "label": "Pretendida",
        "detail": "Intenção registrada, sem pendência no ledger atual.",
    }


def flow(d):
    """Technical → Consensus → Risk → Portfolio → order, from recorded fields only."""
    c, risk, p, committee = d["consensus"], d["risk"], d["portfolio"], d["committee"]
    outcome, verdict, final = (
        c.get("technical_outcome"),
        risk.get("verdict"),
        p.get("decision"),
    )
    votes = " · ".join(f"{k} {v}" for k, v in (c.get("vote_counts") or {}).items())
    if verdict == "APROVADO":
        risk_detail, risk_changed = "Aprovou o sinal; não alterou a decisão.", False
    elif verdict == "VETADO":
        risk_detail = f"Vetou ({risk.get('risk_source') or 'origem N/D'}{' · ' + risk['risk_rule'] if risk.get('risk_rule') else ''}). Efeito: {risk.get('veto_effect') or 'não determinável'}."
        risk_changed = risk.get("veto_effect") == "EFETIVO"
    else:
        risk_detail, risk_changed = "Sem veredito registrado.", None
    if final is None:
        portfolio_detail, portfolio_changed = "Sem decisão registrada.", None
    elif final == outcome:
        portfolio_detail, portfolio_changed = (
            "Confirmou o sinal agregado; não alterou a decisão.",
            False,
        )
    else:
        portfolio_detail = f"Decisão {final} difere do sinal técnico {outcome or 'sem consenso'} (causa {p.get('final_cause') or 'N/D'})."
        portfolio_changed = True
    return [
        {
            "stage": "Technical Analysts",
            "result": f"{committee['responded']}/{committee.get('analyst_count') or 'N/D'} respostas",
            "detail": votes or "Sem votos gravados.",
            "changed": None,
        },
        {
            "stage": "Consenso",
            "result": outcome
            if c.get("consensus_reached")
            else "SEM CONSENSO"
            if c.get("consensus_reached") is False
            else "N/D",
            "detail": f"{(c.get('signal') or {}).get('justification') or 'Sem justificativa gravada'} · limiar {share(c.get('consensus_threshold'))}",
            "changed": None,
        },
        {
            "stage": "Risk Manager",
            "result": verdict or "N/D",
            "detail": risk_detail,
            "changed": risk_changed,
        },
        {
            "stage": "Portfolio Manager",
            "result": final or "N/D",
            "detail": portfolio_detail,
            "changed": portfolio_changed,
        },
        {
            "stage": "Intenção de ordem",
            "result": f"Alvo {share(p.get('target_weight'))}",
            "detail": f"Posição no fechamento {share(p.get('observed_weight'))} → alvo {share(p.get('target_weight'))}. {d['order']['label']}.",
            "changed": None,
        },
    ]


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
    for r in trace_rows(folder):
        if r.get("stage") != "technical_analyst":
            continue
        response = r.get("validated_response") or {}
        explanation = (r.get("technical_evidence") or {}).get("rendered_explanation")
        evidence = [pick(e, "code", "role") for e in response.get("evidence", [])]
        for e, label in zip(evidence, evidence_labels(evidence, explanation)):
            e["label"] = label
        analysts.append(
            {
                **pick(
                    r, "analyst_id", "sequence", "status", "retry_count", "error_type"
                ),
                **pick(response, "signal", "confidence"),
                "evidence": evidence,
                "explanation": explanation,
            }
        )
    counts = collections.Counter(
        (e["code"], e["role"]) for a in analysts for e in a["evidence"]
    )
    cited = collections.defaultdict(list)
    for a in analysts:
        for e in a["evidence"]:
            cited[e["code"], e["role"]].append(a["analyst_id"])
    labels = {e["code"]: e["label"] for a in analysts for e in a["evidence"]}
    roles_by_code = collections.defaultdict(set)
    for code, role in counts:
        roles_by_code[code].add(role)
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
    outcome = record.get("technical_outcome")
    signals = collections.Counter(a["signal"] for a in analysts if a.get("signal"))
    divergences = (
        [f"Votos divididos: {', '.join(f'{k} {v}' for k, v in signals.most_common())}"]
        if len(signals) > 1
        else []
    ) + [
        f"{labels[code]}: classificada de formas diferentes ({', '.join(sorted(roles))})"
        for code, roles in roles_by_code.items()
        if len(roles) > 1
    ]
    pending = (
        pick(state.get("pending"), "decision_session", "target_session", "target_weight")
        if (state.get("pending") or {}).get("decision_session") == session
        else None
    )
    result = {
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
            {
                "code": code,
                "role": role,
                "count": n,
                "label": labels[code],
                "stance": stance(role, outcome),
                "analysts": cited[code, role],
            }
            for (code, role), n in counts.most_common()
        ],
        "divergences": divergences,
        "committee": {
            **pick(params, "analyst_count", "consensus_threshold", "require_all_votes"),
            "responded": sum(a.get("signal") is not None for a in analysts),
        },
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
        "pending": pending,
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
        "intent_weight": next(
            (i.get("target_weight") for i in d.get("intents") or []), None
        ),
    }
    result["order"] = order_state(result)
    result["flow"] = flow(result)
    return result


def wallet(key, book, rows, mark, pending, initial, decisions):
    close = mark["close"] if mark else 0
    value = book.get("units", 0) * close
    equity = book.get("cash", initial) + value
    trade_key = "benchmark_trades" if key == "buy_and_hold" else "trades"
    equity_key = "benchmark_equity" if key == "buy_and_hold" else "equity"
    trades = [
        {
            "session": r["session"],
            # B&H follows a one-off rule; its row's executed_decision belongs to the AI.
            "decision_session": None
            if key == "buy_and_hold"
            else r.get("executed_decision"),
            "asset": "PETR4",
            **pick(t, "type", "price", "quantity", "cost"),
            "equity_after": r.get(equity_key),
        }
        for r in rows
        for t in r.get(trade_key, [])
    ]
    curve = [{"session": r["session"], "equity": r[equity_key]} for r in rows]
    peak, drawdown = 0, 0
    for point in curve:
        peak = max(peak, point["equity"])
        drawdown = max(drawdown, (peak - point["equity"]) / peak if peak else 0)
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
        "cash": book.get("cash", initial),
        "pnl": equity - initial,
        "observations": len(curve),
        # One reconciled close has no path yet; report N/D instead of a fake 0%.
        "max_drawdown": drawdown if len(curve) >= 2 else None,
        "dividends": None,
        "curve": curve,
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


def agents(root=OUTPUT):
    """32-slot catalog. H2 v6 uses only the first Technical slots it declares.

    Observations come from recorded traces/decisions; inactive slots carry no
    history, and nothing here ranks competence from votes.
    """
    params = read(fwd.CANDIDATE)["protocol"]["participant_spec"]["params"]
    price = fwd.oa1.PRICE_PER_M
    calls = collections.defaultdict(list)
    for folder in sorted((root / "sessions").glob("????-??-??")):
        session = session_name(folder.name)
        record = (read(folder / "decision.json") or {}).get("record") or {}
        winner = (
            record.get("technical_outcome") if record.get("consensus_reached") else None
        )
        for r in trace_rows(folder):
            stage = r.get("stage")
            key = (
                f"TA-{r.get('analyst_id'):02d}"
                if stage == "technical_analyst"
                else {"risk_manager": "RM", "portfolio_manager": "PM"}.get(stage)
            )
            if key is None:
                continue
            usage = r.get("token_usage") or {}
            response = r.get("validated_response") or {}
            prompt, output = usage.get("prompt_tokens"), usage.get("completion_tokens")
            calls[key].append(
                {
                    "session": session,
                    **pick(
                        r,
                        "status",
                        "retry_count",
                        "attempt_count",
                        "duration_ms",
                        "error_type",
                    ),
                    "output": response.get("signal")
                    or response.get("verdict")
                    or response.get("decision")
                    if r.get("status") == "ok"
                    else None,
                    "confidence": response.get("confidence")
                    if r.get("status") == "ok"
                    else None,
                    # Agreement is only meaningful for votes, not verdicts/actions.
                    "consensus": winner if stage == "technical_analyst" else None,
                    "tokens": usage.get("total_tokens"),
                    # ponytail: priced at the runner's registered list price; an estimate, not billing.
                    "cost_usd": (
                        prompt * price["input"]
                        + (output + (usage.get("thoughts_tokens") or 0)) * price["output"]
                    )
                    / 1e6
                    if prompt is not None and output is not None
                    else None,
                    "seed": (r.get("requested_options") or {}).get("seed"),
                }
            )

    def observed(rows):
        if not rows:
            return None
        known = lambda field: [r[field] for r in rows if r[field] is not None]  # noqa: E731
        compared = [r for r in rows if r["consensus"] and r["output"]]
        return {
            "calls": len(rows),
            "sessions": len({r["session"] for r in rows}),
            "decisions": len(known("output")),
            "outputs": dict(collections.Counter(known("output"))),
            "mean_confidence": sum(known("confidence")) / len(known("confidence"))
            if known("confidence")
            else None,
            "agreement": sum(r["output"] == r["consensus"] for r in compared)
            / len(compared)
            if compared
            else None,
            "agreement_n": len(compared),
            "error_rate": sum(r["status"] != "ok" for r in rows) / len(rows),
            "retries": sum(r["retry_count"] or 0 for r in rows),
            "retry_rate": sum((r["retry_count"] or 0) > 0 for r in rows) / len(rows),
            "tokens": sum(known("tokens")) if known("tokens") else None,
            "cost_usd": sum(known("cost_usd")) if known("cost_usd") else None,
            "token_coverage": len(known("tokens")) / len(rows),
            "history": [{k: v for k, v in r.items() if k != "consensus"} for r in rows],
        }

    common = pick(
        params,
        "provider",
        "model",
        "temperature",
        "thinking_level",
        "max_output_tokens",
        "retry_attempts",
    )
    catalog = (
        [
            {
                "id": f"TA-{i:02d}",
                "role": "Technical Analyst",
                "active": i <= params["analyst_count"],
                **(
                    {
                        "prompt_version": f"technical v{params['technical_prompt_version']} · schema v{params['technical_response_schema_version']}",
                        "params": common,
                    }
                    if i <= params["analyst_count"]
                    else {"prompt_version": None, "params": None}
                ),
                "observations": observed(calls[f"TA-{i:02d}"]),
            }
            for i in range(1, 31)
        ]
        + [
            {
                "id": "RM",
                "role": "Risk Manager",
                "active": True,
                "prompt_version": f"risk v{params['risk_prompt_version']}",
                "params": {
                    **common,
                    **pick(
                        params,
                        "risk_max_volatility",
                        "risk_max_drawdown",
                        "risk_max_concentration",
                        "volatility_window",
                    ),
                },
                "observations": observed(calls["RM"]),
            },
            {
                "id": "PM",
                "role": "Portfolio Manager",
                "active": True,
                "prompt_version": None,  # the frozen manifest declares no Portfolio prompt version
                "params": {
                    **common,
                    **pick(params, "long_target_weight", "portfolio_inversion_policy"),
                },
                "observations": observed(calls["PM"]),
            },
        ]
    )
    return {
        "configuration": {
            "name": "H2 v6",
            "frozen": True,
            **pick(
                params,
                "analyst_count",
                "consensus_threshold",
                "require_all_votes",
                "provider",
                "model",
                "temperature",
                "thinking_level",
            ),
            "slots": len(catalog),
        },
        "price_per_million_tokens_usd": price,
        "agents": catalog,
    }
