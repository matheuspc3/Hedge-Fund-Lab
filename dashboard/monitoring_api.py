"""Presentation-only views over existing ledgers. No persistence or execution."""

from datetime import datetime, timezone

import forward_api as forward
import platform_api as platform


def catalog():
    records = platform.global_records()
    official = [r for r in records if r.get("mode") == "CONSULTATIVE_SANDBOX"]
    return {
        "wallets": [
            {
                "id": "global:" + r["id"],
                "label": "Global PM V2 · snapshot " + r["id"][:12] + "…",
                "classification": "OFFICIAL_HYPOTHETICAL_SNAPSHOT",
            }
            for r in official
            if r.get("identity", "").endswith("-V2")
        ]
        + [
            {"id": "h2:" + key, "label": label, "classification": "H2_PAPER_LEDGER"}
            for key, label in forward.STRATEGIES.items()
        ],
        "records": official,
        "read_only": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def event(kind, session, at, status, evidence, sha=None):
    return {
        "kind": kind,
        "session": session,
        "at": at,
        "status": status,
        "evidence": evidence,
        "sha256": sha,
    }


def global_snapshot(record_id):
    d = platform.public_global(record_id)
    if d.get("mode") != "CONSULTATIVE_SANDBOX" or not d["identity"].endswith("-V2"):
        raise ValueError("not_an_official_v2_snapshot")
    p, r = d["portfolio"], d.get("result") or {}
    evidence = "/api/platform/global?id=" + record_id
    timeline = [
        event(
            "Contexto preparado",
            d["valuation_session"],
            d["created_at"],
            "SNAPSHOT",
            evidence,
            d["context_sha256"],
        )
    ]
    if r:
        timeline.extend(
            [
                event(
                    "Inferência concluída",
                    d["valuation_session"],
                    r["completed_at"],
                    r["status"],
                    evidence,
                    r["sha256"],
                ),
                event(
                    "Validação",
                    d["valuation_session"],
                    r["validation_at"],
                    r["validation"]["status"],
                    evidence,
                    r["validation"]["sha256"],
                ),
            ]
        )
    return {
        "id": "global:" + record_id,
        "label": "Global PM V2 · snapshot hipotético",
        "identity": d["identity"],
        "classification": "OFFICIAL_HYPOTHETICAL_SNAPSHOT",
        "available": True,
        "persistent_execution": False,
        "source": evidence,
        "limitation": "Fotografia hipotética persistida usada pelo gestor. Este snapshot não registra operações paper. O novo ledger está qualificado somente com dados sintéticos isolados. "
        "Novas sessões não são atualizadas automaticamente; execução financeira indisponível.",
        "summary": {
            "initial_capital": p["initial_capital"],
            "equity": p["equity"],
            "cash": p["cash"]["available"],
            "reserved": p["cash"]["reserved"],
            "receivable": p["cash"]["receivable"],
            "exposure": p["exposure"],
            "realized_pnl": p["realized_pnl"],
            "unrealized_pnl": p["unrealized_pnl"],
            "costs": p["costs"],
            "pnl": str(
                platform.b.dec(p["equity"]) - platform.b.dec(p["initial_capital"])
            ),
            "drawdown": None,
            "volatility": None,
            "invested": str(
                sum(
                    (
                        platform.b.dec(pos["market_value"])
                        for pos in p["positions"].values()
                    ),
                    platform.b.ZERO,
                )
            ),
        },
        # The snapshot is authoritative only about its own holdings, never future fills.
        "positions": [
            {"ticker": t, **pos}
            for t, pos in p["positions"].items()
            if float(pos["quantity"]) > 0
        ],
        "allocation": [
            {"asset": t, "value": pos["market_value"], "weight": pos["weight"]}
            for t, pos in p["positions"].items()
        ]
        + [
            {
                "asset": "Caixa liquidado",
                "value": p["cash"]["settled"],
                "weight": str(
                    platform.b.dec(p["cash_weight"])
                    - platform.b.dec(p["receivable_weight"])
                ),
            },
            {
                "asset": "Recebíveis",
                "value": p["cash"]["receivable"],
                "weight": p["receivable_weight"],
            },
        ],
        "mark": d["marks"],
        "curve": [],
        "trades": [],
        "future": [],
        "timeline": timeline,
        "decision": d,
        "operation_status": "SEM_EXECUCAO_FINANCEIRA",
        "authorization_status": "Nenhuma autorização financeira neste snapshot",
    }


def h2_wallet(key):
    data = forward.portfolios()
    w = next((w for w in data["wallets"] if w["key"] == key), None)
    source = "/api/forward/portfolios"
    if not w or not w.get("available"):
        return {
            "id": "h2:" + key,
            "label": forward.STRATEGIES[key],
            "available": False,
            "classification": "H2_PAPER_LEDGER",
            "source": source,
            "limitation": (w or {}).get("reason", "Ledger H2 não disponível."),
        }
    if w.get("comparable") is False:
        return {
            "id": "h2:" + key,
            "label": w["label"],
            "available": False,
            "classification": "H2_PAPER_LEDGER",
            "source": source,
            "limitation": "Identidade, início ou preços incompatíveis com a linha H2. "
            "Consulte os registros de origem antes de comparar patrimônios.",
        }
    integrity = platform.forward_integrity(forward.OUTPUT)
    if not integrity["ok"]:
        raise ValueError("h2_integrity_unavailable")
    supervised = key == forward.sup.STRATEGY
    sup = forward.supervision() if supervised else None
    if sup and not sup["audit"]["ok"]:
        raise ValueError("supervised_integrity_failed")
    latest = w.get("last_decision")
    session = latest and latest.get("session")
    d = (
        forward.decision(session)
        if session and key in ("ai", forward.sup.STRATEGY)
        else None
    )
    selected = (sup or {}).get("selected")
    status = (
        selected["order_state"]
        if selected
        else (
            d["order"]["state"]
            if d and d.get("order")
            else "PENDENTE"
            if w["pending"]
            else "SEM_PENDENCIA"
        )
    )
    timeline = []
    if latest:
        timeline.append(
            event(
                "Decisão registrada",
                session,
                latest.get("generated_at"),
                latest["status"],
                "/api/forward/decision?session=" + session if d else source,
            )
        )
    if selected:
        ref = "/api/forward/supervision?session=" + selected["decision_session"]
        for kind, record in (
            ("Autorização humana", selected["approval"]),
            ("Cancelamento", selected["cancel"]),
            ("Reconciliação", selected["outcome"]),
        ):
            if record:
                timeline.append(
                    event(
                        kind,
                        selected["decision_session"],
                        record.get("created_at"),
                        record.get("action", status),
                        ref,
                    )
                )
        if status == "EXPIRADA":
            timeline.append(
                event(
                    "Expiração do prazo (derivada na consulta)",
                    selected["decision_session"],
                    selected["deadline"],
                    status,
                    ref,
                )
            )
    trades = [
        {
            **t,
            "ticker": t["asset"],
            "status": "EXECUCAO_PAPER_REGISTRADA",
            "settlement": None,
            "source": source,
        }
        for t in w["trades"]
    ]
    for t in trades:
        timeline.append(event("Execução paper", t["session"], None, t["status"], source))
    for point in w["curve"]:
        timeline.append(
            event(
                "Fechamento reconciliado", point["session"], None, "RECONCILIADO", source
            )
        )
    mark = w["mark"]
    position = next(p for p in w["composition"] if p["asset"] == "PETR4")
    future = []
    if w["pending"]:
        future.append({"kind": "Intenção pendente de reconciliação", **w["pending"]})
    if selected and status == "AGUARDANDO_APROVACAO":
        future.append(
            {
                "kind": "Aguardando autorização humana",
                "deadline": selected["deadline"],
                "target_session": selected["target_session"],
            }
        )
    return {
        "id": "h2:" + key,
        "label": w["label"],
        "identity": "H2_V6/" + key,
        "classification": "H2_PAPER_LEDGER",
        "available": True,
        "persistent_execution": True,
        "source": source,
        "limitation": "Ledger H2 independente. Preços ajustados do ledger; sem D+2, "
        "reservas, custo médio ou decomposição de PnL publicados. "
        "Consulta não atualiza preços nem reconcilia. Patrimônios não se somam.",
        "summary": {
            "initial_capital": w["initial_capital"],
            "equity": w["equity"],
            "cash": w["cash"],
            "reserved": None,
            "receivable": None,
            "exposure": w["exposure"],
            "realized_pnl": None,
            "unrealized_pnl": None,
            "costs": w["costs"],
            "pnl": w["pnl"],
            "drawdown": w["max_drawdown"],
            "volatility": None,
            "invested": w["marked_value"],
        },
        "positions": [
            {
                "ticker": "PETR4",
                "quantity": position["units"],
                "available": None,
                "reserved": None,
                "unsettled": None,
                "average_cost": None,
                "raw_mark": mark["close"] if mark else None,
                "market_value": position["value"],
                "weight": position["weight"],
                "unrealized_pnl": None,
            }
        ]
        if position["units"] > 0
        else [],
        "allocation": w["composition"],
        "mark": mark,
        "curve": w["curve"],
        "trades": trades,
        "timeline": timeline,
        "future": future,
        "decision": d or latest,
        "supervision": selected,
        "operation_status": status,
        "authorization_status": (selected["approval"] or {}).get(
            "action", "Sem aprovação registrada"
        )
        if selected
        else "Não se aplica a esta estratégia",
    }


def get(query):
    if not query:
        return catalog()
    if set(query) != {"wallet"}:
        raise ValueError("invalid_monitoring_query")
    wallet = query["wallet"]
    if not isinstance(wallet, str) or len(wallet) > 100:
        raise ValueError("invalid_wallet")
    if wallet.startswith("h2:") and wallet[3:] in forward.STRATEGIES:
        result = h2_wallet(wallet[3:])
    elif wallet.startswith("global:") and platform.ID2.fullmatch(wallet[7:]):
        result = global_snapshot(wallet[7:])
    else:
        raise ValueError("invalid_wallet")
    return {
        **result,
        "read_only": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
