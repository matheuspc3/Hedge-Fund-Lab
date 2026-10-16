"""H2 v6 supervisionada: aprovação humana sobre decisões H2 v6 já gravadas.

Paper trading exploratório. Nunca chama o modelo e nunca escreve no Forward Test
original: lê decision.json, input.json e bars.csv por hash e mantém carteira
própria em data/forward/h2_v6_supervised. Contrato completo em
docs/H2_V6_HUMAN_SUPERVISION_SPEC.md.

    sync                           reconcilia até o último fechamento e registra a proposta
    approve|reject|cancel S SHA    ação humana write-once, antes da abertura-alvo
    verify                         confere offline a cadeia de auditoria
"""

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_h2_v6_forward as fwd  # noqa: E402

STRATEGY = "h2_v6_supervised"
OUTPUT = ROOT / "data/forward/h2_v6_supervised"
#: Mesma tolerância de vizinhança do fator de ajuste no extrator B3.
FACTOR_TOLERANCE = 1e-6
#: Direção só a partir da causa final validada; nunca do texto dos agentes.
DIRECTIONS = {
    "ACTION_BUY": "COMPRA",
    "ACTION_SELL": "VENDA",
    "TECH_EXPLICIT_HOLD": "MANTER",
    "TECH_NO_MAJORITY": "MANTER",
    "PORTFOLIO_HOLD": "MANTER",
    "RISK_VETO_VOLATILITY": "VETO",
    "RISK_VETO_DRAWDOWN": "VETO",
    "RISK_VETO_CONCENTRATION": "VETO",
    "RISK_VETO_LLM": "VETO",
    "BUY_AT_TARGET_NOOP": "NOOP",
}
#: limite -> (direção exigida, ou None para ambas; máximo aceito)
LIMITS = {
    "max_buy_price": ("COMPRA", 1e6),
    "min_sell_price": ("VENDA", 1e6),
    "max_gap_up": (None, 1.0),
    "max_gap_down": (None, 1.0),
    "max_concentration": ("COMPRA", 1.0),
    "max_volatility": (None, 10.0),
}
PENDING_EFFECTS = ("APROVADA", "AJUSTADA_CONCENTRACAO")
SIDE = {"COMPRA": "BUY", "VENDA": "SELL"}


class Conflict(ValueError):
    """Ação recusada pelo estado atual (HTTP 409)."""


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def stamp(value):
    return fwd.pd.Timestamp(value)


def check_session(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("invalid_session")
    fwd._timestamp(value)
    return value


def params():
    return fwd.read(fwd.CANDIDATE)["protocol"]["participant_spec"]["params"]


def weight(book, close):
    equity = book["cash"] + book["units"] * close
    return book["units"] * close / equity if equity else 0.0


def records(root, session):
    folder = root / "approvals"
    approval, cancel = folder / f"{session}.json", folder / f"{session}.cancel.json"
    return (
        fwd.read(approval) if approval.exists() else None,
        fwd.read(cancel) if cancel.exists() else None,
    )


# ── Proposta e estados ──────────────────────────────────────────────────────


def propose(state, session, forward_root, at):
    """Proposta de S para a posição supervisionada marcada no fechamento de S."""
    folder = forward_root / "sessions" / session
    path = folder / "decision.json"
    held = weight(state["portfolio"], state["mark"]["close"])
    base = {
        "decision_session": session,
        "weight_at_close": held,
        "created_at": at.isoformat(),
    }
    if not path.exists():
        deadline = fwd.target_open(fwd._timestamp(session))
        if at < deadline:
            return None  # os agentes ainda podem decidir S
        return {
            **base,
            "target_session": str(deadline.date()),
            "deadline": deadline.isoformat(),
            "direction": None,
            "state": "SEM_DECISAO",
            "reason": "Nenhuma decisão original gravada antes do prazo.",
        }
    decision = fwd.read(path)
    cause = (decision.get("record") or {}).get("final_cause")
    proposal = {
        **base,
        "target_session": decision["target_session"],
        "deadline": decision["target_open_deadline"],
        "generated_at": decision["generated_at"],
        "decision_sha256": fwd.sha_file(path),
        "input_sha256": decision["input_sha256"],
        "original_status": decision["status"],
        "final_cause": cause,
        "recent_volatility": (
            (decision.get("risk_verdict") or {}).get("risk_metrics") or {}
        ).get("recent_volatility"),
        "raw_close": fwd.read(folder / "input.json")["last_bar_official_raw"][
            "fechamento"
        ],
        "created_after_deadline": at >= stamp(decision["target_open_deadline"]),
        "direction": None,
        "recommended_target": None,
    }

    def closed(state_name, reason, direction=None):
        return {**proposal, "direction": direction, "state": state_name, "reason": reason}

    if decision["status"] != "DECIDED":
        return closed(
            "SEM_DECISAO", f"Decisão original {decision['status']}; nenhuma ordem."
        )
    direction, long_target = DIRECTIONS.get(cause), params()["long_target_weight"]
    if direction == "MANTER":
        return closed(
            "SEM_ORDEM_NECESSARIA",
            f"MANTER ({cause}): posição supervisionada preservada.",
            "MANTER",
        )
    if direction == "VETO":
        return closed(
            "SEM_ORDEM_NECESSARIA",
            f"Veto de risco ({cause}), avaliado sobre a carteira original; nenhuma nova ordem.",
            "VETO",
        )
    if direction == "NOOP":
        if held >= long_target:
            return closed(
                "SEM_ORDEM_NECESSARIA",
                "Carteira supervisionada já está no alvo de COMPRA.",
            )
        return closed(
            "SEM_DECISAO",
            "COMPRA técnica sem aprovação de Risk/Portfolio (BUY_AT_TARGET_NOOP na original); nenhuma ordem para outra posição.",
        )
    if direction is None:
        return closed("SEM_DECISAO", f"Causa {cause}: sem decisão executável.")
    target = long_target if direction == "COMPRA" else 0.0
    intents = [i["target_weight"] for i in decision.get("intents") or []]
    if intents != [target]:
        return closed(
            "SEM_DECISAO",
            f"Intenção gravada {intents} incoerente com {cause}; nenhuma ordem.",
        )
    # COMPRA nunca reduz exposição; VENDA nunca aumenta (posições podem divergir).
    if direction == "COMPRA" and held >= target:
        return closed(
            "SEM_ORDEM_NECESSARIA",
            "Carteira supervisionada já está no alvo de COMPRA.",
            direction,
        )
    if direction == "VENDA" and state["portfolio"]["units"] <= 0:
        return closed(
            "SEM_ORDEM_NECESSARIA",
            "Carteira supervisionada sem PETR4 para vender.",
            direction,
        )
    return {
        **proposal,
        "direction": direction,
        "recommended_target": target,
        "state": "AGUARDANDO_APROVACAO",
        "reason": f"{direction} para alvo {target:.0%} aguarda decisão humana até o prazo.",
    }


def effect(proposal, limits):
    """Limites conhecidos antes da abertura: volatilidade gravada e concentração."""
    volatility, cap = limits.get("max_volatility"), limits.get("max_concentration")
    recorded = proposal["recent_volatility"]
    if volatility is not None and (recorded is None or recorded > volatility):
        return {
            "state": "BLOQUEADA_VOLATILIDADE",
            "target_weight": None,
            "reason": f"Volatilidade registrada na sessão original ({recorded}) acima do limite {volatility} ou ausente.",
        }
    target = proposal["recommended_target"]
    if cap is not None and cap < target:
        if proposal["weight_at_close"] >= cap:
            return {
                "state": "SEM_ORDEM_NECESSARIA",
                "target_weight": None,
                "reason": f"Exposição supervisionada já atinge o limite de concentração {cap:.0%}.",
            }
        return {
            "state": "AJUSTADA_CONCENTRACAO",
            "target_weight": cap,
            "reason": f"Alvo reduzido de {target:.0%} para {cap:.0%} pelo limite de concentração.",
        }
    return {
        "state": "APROVADA",
        "target_weight": target,
        "reason": "Recomendação aprovada.",
    }


def order_state(proposal, approval, cancel, outcome, at):
    """Estado derivado só de registros imutáveis e do relógio."""
    if outcome:
        return outcome["state"]
    if proposal["state"] != "AGUARDANDO_APROVACAO":
        return proposal["state"]
    deadline = stamp(proposal["deadline"])
    if approval is None:
        return "EXPIRADA" if at >= deadline else "AGUARDANDO_APROVACAO"
    if approval["action"] == "REJECT":
        return "REJEITADA"
    if cancel:
        return "CANCELADA"
    current = approval["effect"]["state"]
    return (
        "PENDENTE_ABERTURA" if current in PENDING_EFFECTS and at >= deadline else current
    )


def validate_limits(limits, direction):
    if not isinstance(limits, dict) or set(limits) - set(LIMITS):
        raise ValueError("invalid_limits")
    clean = {}
    for key, value in limits.items():
        need, top = LIMITS[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0 < value <= top
        ):
            raise ValueError(f"invalid_limit:{key}")
        if need and need != direction:
            raise ValueError(f"limit_incoherent_with_direction:{key}")
        clean[key] = float(value)
    return clean


# ── Auditoria ───────────────────────────────────────────────────────────────


def journal(root, repair_tail=True):
    path = root / "audit.jsonl"
    if not path.exists():
        return []
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        if repair_tail is False:
            raise ValueError("audit journal has an incomplete tail")
        # ponytail: a torn append is re-derived from the immutable records below.
        data = data[: data.rfind(b"\n") + 1]
        if repair_tail:
            with path.open("r+b") as stream:
                stream.truncate(len(data))
                stream.flush()
                os.fsync(stream.fileno())
    return [json.loads(line) for line in data.decode("utf-8").splitlines()]


def expected_events(root, state):
    """Eventos que os registros write-once e o state.json salvo exigem."""
    events = []
    for session, proposal in sorted(state["proposals"].items()):
        events.append(("PROPOSED", session, sha(proposal), proposal["created_at"]))
        approval, cancel = records(root, session)
        if approval:
            name = "APPROVED" if approval["action"] == "APPROVE" else "REJECTED"
            path = root / "approvals" / f"{session}.json"
            events.append((name, session, fwd.sha_file(path), approval["created_at"]))
        if cancel:
            path = root / "approvals" / f"{session}.cancel.json"
            events.append(
                ("CANCELLED", session, fwd.sha_file(path), cancel["created_at"])
            )
        outcome = state["outcomes"].get(session)
        if outcome:
            events.append(("RESOLVED", session, sha(outcome), outcome["resolved_at"]))
    return events


def repair(root, state):
    """Anexa, em ordem determinística, todo evento exigido ainda ausente."""
    events = journal(root)
    seen = {(e["event"], e["session"]) for e in events}
    for name, session, digest, at in expected_events(root, state):
        if (name, session) in seen:
            continue
        line = {
            "seq": len(events),
            "event": name,
            "session": session,
            "record_sha256": digest,
            "recorded_at": at,
            "previous_sha256": events[-1]["sha256"] if events else None,
        }
        line["sha256"] = sha(line)
        with (root / "audit.jsonl").open("ab") as stream:
            stream.write((canonical(line) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        events.append(line)
    return events


def verify(root=OUTPUT, forward_root=fwd.OUTPUT, state=None, allow_missing=False):
    """Offline e somente leitura: cadeia, registros, hashes e prazos."""
    errors = []
    try:
        # Recovery may ignore a torn tail, but must verify complete events before
        # repair writes anything. The ordinary offline verifier stays strict.
        events = journal(root, repair_tail=None if allow_missing else False)
    except ValueError as exc:
        return {"ok": False, "events": 0, "errors": [str(exc)]}
    previous = None
    for index, event in enumerate(events):
        body = {k: v for k, v in event.items() if k != "sha256"}
        if (
            event.get("seq") != index
            or event.get("previous_sha256") != previous
            or sha(body) != event.get("sha256")
        ):
            errors.append(f"chain broken at event {index}")
        previous = event.get("sha256")
    path = root / "state.json"
    if state is None:  # the dashboard passes its share-delete read on Windows
        state = fwd.read(path) if path.exists() else {"proposals": {}, "outcomes": {}}
    expected = {(n, s): d for n, s, d, _ in expected_events(root, state)}
    seen = {}
    for event in events:
        key = (event["event"], event["session"])
        if key in seen:
            errors.append(f"duplicate event {key}")
        seen[key] = event["record_sha256"]
    errors += [
        f"missing or altered event {k}"
        for k, d in expected.items()
        if (k in seen or not allow_missing) and seen.get(k) != d
    ]
    errors += [f"event without record {k}" for k in seen if k not in expected]
    for session, proposal in state["proposals"].items():
        approval, cancel = records(root, session)
        decision = forward_root / "sessions" / session / "decision.json"
        if proposal.get("decision_sha256") and (
            not decision.exists() or fwd.sha_file(decision) != proposal["decision_sha256"]
        ):
            errors.append(f"{session}: original decision changed")
        source = forward_root / "sessions" / session / "input.json"
        if proposal.get("input_sha256") and (
            not source.exists() or fwd.sha_file(source) != proposal["input_sha256"]
        ):
            errors.append(f"{session}: original input changed")
        for record in (approval, cancel):
            if record and (
                record["decision_sha256"] != proposal.get("decision_sha256")
                or stamp(record["created_at"]) >= stamp(proposal["deadline"])
                or stamp(record["created_at"]) < stamp(proposal["generated_at"])
                or record["idempotency_key"]
                != hashlib.sha256(
                    f"{STRATEGY}|{session}|{record['decision_sha256']}".encode()
                ).hexdigest()
            ):
                errors.append(f"{session}: invalid {record['action']} record")
        if cancel and (not approval or approval["action"] != "APPROVE"):
            errors.append(f"{session}: cancel without approval")
        outcome = state["outcomes"].get(session) or {}
        if outcome.get("state") == "EXECUTADA" and (
            not approval or approval["action"] != "APPROVE" or cancel
        ):
            errors.append(f"{session}: execution without valid approval")
    return {"ok": not errors, "events": len(events), "errors": errors}


# ── Ação humana ─────────────────────────────────────────────────────────────


def act(
    action,
    session,
    decision_sha256,
    limits=None,
    root=OUTPUT,
    forward_root=fwd.OUTPUT,
    clock=fwd.now,
):
    """APPROVE, REJECT ou CANCEL: um registro write-once e seu evento de auditoria."""
    if action not in ("APPROVE", "REJECT", "CANCEL"):
        raise ValueError("invalid_action")
    check_session(session)
    if not isinstance(decision_sha256, str) or not re.fullmatch(
        r"[0-9a-f]{64}", decision_sha256
    ):
        raise ValueError("invalid_decision_sha256")
    if not (root / "state.json").exists():
        raise Conflict("supervised_ledger_missing; sync_required")
    try:
        lock = fwd._exclusive_state_lock(root / "state.json")
        lock.__enter__()
    except RuntimeError as exc:
        raise Conflict("supervision_busy; retry") from exc
    try:
        state = fwd.read(root / "state.json")
        if not verify(root, forward_root, state, allow_missing=True)["ok"]:
            raise Conflict("supervision_integrity_failed")
        events = repair(root, state)
        proposal = state["proposals"].get(session)
        if proposal is None:
            raise Conflict("proposal_missing; sync_required")
        folder = forward_root / "sessions" / session
        if (
            decision_sha256 != proposal.get("decision_sha256")
            or not (folder / "decision.json").exists()
            or fwd.sha_file(folder / "decision.json") != decision_sha256
        ):
            raise Conflict("decision_hash_mismatch")
        if fwd.sha_file(folder / "input.json") != proposal["input_sha256"]:
            raise Conflict("input_hash_mismatch")
        at = clock()
        if at >= stamp(proposal["deadline"]):
            raise Conflict("deadline_passed")
        if at < stamp(proposal["generated_at"]):
            raise Conflict("before_decision")
        approval, cancel = records(root, session)
        current = order_state(
            proposal, approval, cancel, state["outcomes"].get(session), at
        )
        record = {
            "kind": "H2_V6_SUPERVISED_ACTION",
            "schema_version": 1,
            "strategy": STRATEGY,
            "action": action,
            "decision_session": session,
            "target_session": proposal["target_session"],
            "decision_sha256": decision_sha256,
            "input_sha256": proposal["input_sha256"],
            "created_at": at.isoformat(),
            "expires_at": proposal["deadline"],
            "idempotency_key": hashlib.sha256(
                f"{STRATEGY}|{session}|{decision_sha256}".encode()
            ).hexdigest(),
            "previous_audit_sha256": events[-1]["sha256"] if events else None,
        }
        if action == "CANCEL":
            if current not in PENDING_EFFECTS or limits:
                raise Conflict(f"invalid_transition:{current}->CANCELADA")
            record["approval_sha256"] = fwd.sha_file(
                root / "approvals" / f"{session}.json"
            )
            name = f"{session}.cancel.json"
        else:
            if current != "AGUARDANDO_APROVACAO":
                raise Conflict(f"invalid_transition:{current}")
            if action == "REJECT" and limits:
                raise ValueError("reject_has_no_limits")
            clean = validate_limits(limits or {}, proposal["direction"])
            record["limits"] = clean
            record["effect"] = effect(proposal, clean) if action == "APPROVE" else None
            name = f"{session}.json"
        (root / "approvals").mkdir(exist_ok=True)
        try:
            with (root / "approvals" / name).open("xb") as stream:
                stream.write((canonical(record) + "\n").encode())
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as exc:
            raise Conflict("duplicate_action") from exc
        repair(root, state)
        return record
    finally:
        lock.__exit__(None, None, None)


# ── Reconciliação ───────────────────────────────────────────────────────────


def raw_bar(day, forward_root, latest):
    """Barra bruta oficial de T: input.json de T ou COTAHIST com SHA registrado."""
    path = forward_root / "sessions" / day / "input.json"
    if path.exists() and fwd.read(path)["decision_session"] == day:
        return fwd.read(path)["last_bar_official_raw"], f"sessions/{day}/input.json"
    name = f"COTAHIST_A{day[:4]}.ZIP"
    source = (
        fwd.read(forward_root / "sessions" / latest / "input.json").get("source") or {}
    )
    expected = (source.get("cotahist_sha256") or {}).get(name)
    for cached in (forward_root / "cotahist" / name, fwd.SCIENCE_CACHE / name):
        if expected and cached.exists() and fwd.sha_file(cached) == expected:
            frame = fwd.read_cotahist(cached, fwd.TICKER.removesuffix(".SA"))
            if fwd._timestamp(day) in frame.index:
                bar = frame.loc[fwd._timestamp(day)]
                return {
                    k: float(v) for k, v in bar.items()
                }, f"{name} sha256 {expected[:12]}"
    return None, None


def prices(proposal, bars, forward_root, latest):
    day = proposal["target_session"]
    raw, source = raw_bar(day, forward_root, latest)
    adjusted = bars.loc[fwd._timestamp(day)]
    result = {
        "raw_previous_close": proposal["raw_close"],
        "raw_previous_close_source": f"sessions/{proposal['decision_session']}/input.json",
        "raw_open": raw and raw["abertura"],
        "raw_close": raw and raw["fechamento"],
        "raw_source": source,
        "adjusted_open": float(adjusted["abertura"]),
        "adjusted_close": float(adjusted["fechamento"]),
        "adjusted_source": f"sessions/{latest}/bars.csv",
    }
    if raw is None:
        return (
            result,
            "Preço bruto oficial da abertura indisponível nos registros; execução bloqueada.",
        )
    ratio = (result["adjusted_open"] / raw["abertura"]) / (
        result["adjusted_close"] / raw["fechamento"]
    )
    if abs(ratio - 1) > FACTOR_TOLERANCE:
        return (
            result,
            "Fator ajustado/bruto da abertura difere do fechamento; bases de preço incompatíveis.",
        )
    result["raw_gap"] = raw["abertura"] / proposal["raw_close"] - 1
    return result, None


def opening_conditions(proposal, limits, raw_open=None):
    """Pure raw-price intersection and checks, shared with informational views."""
    reference = proposal.get("raw_close")
    low, high, checks = 0.0, None, []
    bounds = {
        "max_gap_up": reference * (1 + limits["max_gap_up"])
        if reference and "max_gap_up" in limits
        else None,
        "max_gap_down": reference * (1 - limits["max_gap_down"])
        if reference and "max_gap_down" in limits
        else None,
        "max_buy_price": limits.get("max_buy_price"),
        "min_sell_price": limits.get("min_sell_price"),
    }
    for key in ("max_gap_up", "max_gap_down", "max_buy_price", "min_sell_price"):
        if key not in limits:
            continue
        bound = bounds[key]
        upper = key in ("max_gap_up", "max_buy_price")
        if bound is not None:
            if upper:
                high = min(high, bound) if high is not None else bound
            else:
                low = max(low, bound)
        # Inclusive bounds: a ratio like 54.88 / 56 - 1 can round below -2%.
        passed = (
            None
            if raw_open is None or bound is None
            else (raw_open <= bound if upper else raw_open >= bound)
            or math.isclose(raw_open, bound, rel_tol=1e-12, abs_tol=1e-12)
        )
        checks.append(
            {
                "key": key,
                "limit": limits[key],
                "raw_bound": bound,
                "observed": raw_open,
                "passed": passed,
            }
        )
    if "max_volatility" in limits:
        observed = proposal.get("recent_volatility")
        checks.append(
            {
                "key": "max_volatility",
                "limit": limits["max_volatility"],
                "observed": observed,
                "passed": observed is not None and observed <= limits["max_volatility"],
            }
        )
    return {
        "lower": low,
        "upper": high,
        "inclusive": True,
        "empty": high is not None and (high < low or high <= 0),
        "redundant_gap_up": bounds["max_buy_price"] is not None
        and bounds["max_gap_up"] is not None
        and bounds["max_buy_price"] <= bounds["max_gap_up"],
        "checks": checks,
    }


def evaluate_opening(state, proposal, limits, target, found, bars, latest):
    """Pure dry run. Only resolve may install the returned pending order."""
    gap, raw_open = found["raw_gap"], found["raw_open"]
    conditions = opening_conditions(proposal, limits, raw_open)
    for check in conditions["checks"]:
        key = check["key"]
        if check["passed"] is False and key in ("max_gap_up", "max_gap_down"):
            name = "alta" if key == "max_gap_up" else "baixa"
            return (
                {
                    "state": "NAO_EXECUTADA_GAP",
                    "reason": f"Gap de {name} {abs(gap):.2%} acima do limite {limits[key]:.2%}.",
                },
                None,
                None,
            )
    pending = {
        "decision_session": proposal["decision_session"],
        "target_session": proposal["target_session"],
        "target_weight": target,
    }
    if proposal["direction"] == "COMPRA" and "max_concentration" in limits:
        # ponytail: closed-form sizing for this frozen single-asset proportional
        # cost model; nonlinear costs would require solving against _settle.
        ratio = state["mark"]["close"] / float(
            bars.at[fwd._timestamp(state["mark"]["session"]), "fechamento"]
        )
        invested = state["portfolio"]["units"] * ratio * found["adjusted_open"]
        equity = state["portfolio"]["cash"] + invested
        rate = fwd.BASE_COSTS.build().apply_buy(1.0)
        pending["target_weight"] = (
            target * (1 + rate * invested / equity) / (1 + target * rate)
        )
    dry = copy.deepcopy(state)
    dry["pending"] = pending
    trades = fwd.reconcile(dry, bars, fwd._timestamp(latest))[0]["trades"]
    side = SIDE[proposal["direction"]]
    if not trades or any(t["type"] != side for t in trades):
        return (
            {
                "state": "SEM_ORDEM_NECESSARIA",
                "reason": "A abertura não exigiu operação na direção aprovada.",
            },
            None,
            None,
        )
    for check in conditions["checks"]:
        if check["passed"] is False and check["key"] in (
            "max_buy_price",
            "min_sell_price",
        ):
            return (
                {
                    "state": "NAO_EXECUTADA_LIMITE_PRECO",
                    "reason": f"Abertura bruta R$ {raw_open:.2f} viola o limite de preço R$ {check['limit']:.2f}.",
                },
                None,
                None,
            )
    return (
        {
            "state": "EXECUTADA",
            "target_weight": target,
            "settlement_target_weight": pending["target_weight"],
            "reason": "Execução virtual confirmada pela abertura oficial reconciliada.",
            "trades": trades,
        },
        pending,
        dry,
    )


def resolve(state, session, bars, latest, root, forward_root, at):
    """Decide se a proposta de S executa na abertura de T; nunca liquida aqui."""
    proposal = state["proposals"][session]
    approval, cancel = records(root, session)
    current = order_state(proposal, approval, cancel, None, at)
    state["pending"] = None
    out = {
        "state": current,
        "resolved_at": at.isoformat(),
        "target_session": proposal["target_session"],
    }
    if current != "PENDENTE_ABERTURA":
        reasons = {
            "EXPIRADA": "Sem decisão humana até o prazo; nenhuma ordem."
            + (
                " Proposta registrada após o prazo."
                if proposal.get("created_after_deadline")
                else ""
            ),
            "REJEITADA": "Recomendação rejeitada pelo operador; nenhuma ordem.",
            "CANCELADA": "Aprovação cancelada antes do prazo; nenhuma ordem.",
        }
        reason = reasons.get(current) or (approval or {}).get("effect", {}).get("reason")
        return {**out, "reason": reason or proposal["reason"]}
    found, problem = prices(proposal, bars, forward_root, latest)
    out["prices"] = found
    if problem:
        return {**out, "state": "BLOQUEADA_BASE_PRECOS", "reason": problem}
    result, pending, _ = evaluate_opening(
        state,
        proposal,
        approval["limits"],
        approval["effect"]["target_weight"],
        found,
        bars,
        latest,
    )
    state["pending"] = pending
    # The official reconciliation records trades; the dry run is never persisted.
    result.pop("trades", None)
    return {**out, **result}


def sync(root=OUTPUT, forward_root=fwd.OUTPUT, clock=fwd.now):
    """Idempotente por sessão; só cria ordens para a abertura seguinte à marcação."""
    at = clock()
    session = fwd.last_closed_session(at)
    name = str(session.date())
    folder = forward_root / "sessions" / name
    frozen, bars = fwd.read(folder / "input.json"), fwd.load_bars(folder)
    if (
        frozen["decision_session"] != name
        or fwd.sha_file(folder / "bars.csv") != frozen["history"]["sha256"]
        or bars.index[-1] != session
    ):
        raise ValueError("frozen forward input differs")
    ai = fwd.read(forward_root / "state.json")
    if not ai["sessions"]:
        raise ValueError("AI inception not recorded")
    inception = ai["sessions"][0]["session"]
    manifest, _ = fwd.identity()
    root.mkdir(parents=True, exist_ok=True)
    with fwd._exclusive_state_lock(root / "state.json"):
        path = root / "state.json"
        if path.exists():
            state = fwd.read(path)
            expected = fwd.new_state(manifest)
            if (
                any(state[k] != expected[k] for k in fwd.IDENTITY_KEYS)
                or state["strategy"] != STRATEGY
                or state["inception"] != inception
            ):
                raise ValueError("supervised ledger identity drift")
            if state["mark"]["session"] > name:
                raise ValueError("supervised clock cannot go backwards")
        else:
            if (
                name != inception
                or len(ai["sessions"]) != 1
                or at >= fwd.target_open(session)
            ):
                raise ValueError(
                    "NOT_COMPARABLE: missed inception; retrospective approvals forbidden"
                )
            state = fwd.new_state(manifest)
            state.update(
                strategy=STRATEGY,
                inception=inception,
                initialized_at=at.isoformat(),
                proposals={},
                outcomes={},
            )
        if not verify(root, forward_root, state, allow_missing=True)["ok"]:
            raise Conflict("supervision_integrity_failed")
        repair(root, state)
        before = canonical(state)
        if state["mark"] is None:
            fwd.reconcile(state, bars, session)  # marca o fechamento de início, em caixa
        elif state["mark"]["session"] < name:
            previous = state["mark"]["session"]
            if previous not in state["proposals"]:
                state["proposals"][previous] = propose(state, previous, forward_root, at)
            outcome = resolve(state, previous, bars, name, root, forward_root, at)
            rows = fwd.reconcile(state, bars, session)
            if rows[0]["session"] != outcome["target_session"]:
                raise ValueError("supervised order target is not the next session")
            if outcome["state"] == "EXECUTADA":
                outcome.update(trades=rows[0]["trades"], equity_after=rows[0]["equity"])
            state["outcomes"][previous] = outcome
            # ponytail: sessions closed without a supervised sync are never offered
            # retroactively; they are recorded as SEM_DECISAO with their reason.
            for row in rows[:-1]:
                day = row["session"]
                reason = "Sessão sem sincronização supervisionada antes da abertura seguinte; decisão não oferecida à aprovação."
                state["proposals"][day] = {
                    "decision_session": day,
                    "direction": None,
                    "state": "SEM_DECISAO",
                    "reason": reason,
                    "created_at": at.isoformat(),
                    "weight_at_close": None,
                }
                state["outcomes"][day] = {
                    "state": "SEM_DECISAO",
                    "reason": reason,
                    "resolved_at": at.isoformat(),
                    "target_session": None,
                }
        if name not in state["proposals"]:
            proposal = propose(state, name, forward_root, at)
            if proposal:
                state["proposals"][name] = proposal
        if canonical(state) != before or not path.exists():
            fwd.save_state(root, state)
        repair(root, state)
    return state


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "command", choices=("sync", "approve", "reject", "cancel", "verify")
    )
    parser.add_argument("session", nargs="?")
    parser.add_argument("decision_sha256", nargs="?")
    parser.add_argument("--limit", action="append", default=[], metavar="NAME=VALUE")
    args = parser.parse_args()
    if args.command == "sync":
        state = sync()
        print(
            json.dumps(
                {
                    "strategy": STRATEGY,
                    "session": state["mark"]["session"],
                    "status": "SYNCED",
                }
            )
        )
    elif args.command == "verify":
        report = verify()
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report["ok"] else 2)
    else:
        limits = {k: float(v) for k, v in (item.split("=", 1) for item in args.limit)}
        record = act(args.command.upper(), args.session, args.decision_sha256, limits)
        print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
