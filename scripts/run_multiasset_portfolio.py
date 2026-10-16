"""Explicit synthetic demo, read-only verify/status, and journal-only recovery."""

# ruff: noqa: E402 -- CLI establishes repository imports.
import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import multiasset_manager as manager
import multiasset_portfolio as b

from src.experiments.h2_evaluation_offline import no_network


def make_operation(oid, symbol, side, quantity, context, *, dependencies=None):
    deps = dependencies or []
    price = context["marks"]["prices"][symbol]
    return {
        "operation_id": oid,
        "ticker": symbol,
        "side": side,
        "quantity": quantity,
        "limit_price": price,
        "cost_ceiling": str(b.cost(b.dec(price) * b.dec(quantity))),
        "funding_source": ("SETTLEMENT" if deps else "SETTLED_CASH")
        if side == "BUY"
        else None,
        "priority": 1 if side == "SELL" else 2,
        "dependencies": deps,
        "reasoning": "Demonstração sintética; seleção explícita, sem sizing por confiança.",
    }


def manual(state, context, operations, rid, reasoning):
    preview = copy.deepcopy(state)
    ready = [
        op
        for op in operations
        if all(d in state["settlements"] for d in op["dependencies"])
    ]
    if ready:
        b.reserve(preview, ready)
        b.fill(preview, ready, state["marks"]["session"])
    view = b.view(preview)
    day = state["marks"]["session"]
    result = manager.proposal(
        state,
        context,
        operations,
        {t: p["weight"] for t, p in view["positions"].items()},
        view["cash_weight"],
        record_id=rid,
        at=day + "T19:00:00-03:00",
        expires_at=day + "T22:00:00-03:00",
        reasoning=reasoning,
    )
    if any(op["dependencies"] for op in operations):
        report = manager.validate(state, result, context, result["created_at"])
        future = report["future_conditional"]
        if future:
            result = b.sealed(
                {
                    **{k: v for k, v in result.items() if k != "sha256"},
                    "target_weights": {
                        t: p["weight"] for t, p in future["positions"].items()
                    },
                    "target_cash_weight": future["cash_weight"],
                }
            )
    return result


def scenario(state, context, name):
    held = sorted(t for t, p in state["positions"].items() if b.dec(p["quantity"]) > 0)
    first = held[0] if held else "PETR4"
    quantity = b.dec(state["positions"].get(first, b.position())["quantity"])
    oid = "simulation-" + name
    ops = []
    why = {
        "buy": "Comprar usando apenas caixa liquidado disponível.",
        "sell_cash": "Vender toda uma posição e manter caixa; nenhuma compra substituta.",
        "partial": "Reduzir parte da posição e preservar recebível até a liquidação.",
        "rebalance": "Rebalanceamento ilustrativo com empresas selecionadas e caixa remanescente.",
        "hold": "Nenhuma operação: manter posições e preservar caixa.",
        "rotation": "Vender e aguardar liquidação confirmada antes de uma nova proposta de compra.",
    }
    if name not in why:
        raise ValueError("invalid_scenario")
    if name == "buy":
        ops = [make_operation(oid, "BBAS3", "BUY", "20", context)]
    elif name in ("sell_cash", "partial", "rotation") and quantity > 0:
        q = (
            quantity
            if name == "sell_cash"
            else max(
                b.dec(1), (quantity / 4).to_integral_value(rounding=b.ROUND_HALF_EVEN)
            )
        )
        ops = [make_operation(oid, first, "SELL", str(q), context)]
        if name == "rotation":
            ops.append(
                make_operation(
                    oid + "-later", "BBAS3", "BUY", "10", context, dependencies=[oid]
                )
            )
    elif name == "rebalance":
        day = state["marks"]["session"]
        return manager.FakePortfolioManager().propose(
            state,
            context,
            {"PETR4": "0.15", "VALE3": "0.20", "ITUB4": "0.20", "WEGE3": "0.10"},
            "0.35",
            record_id=oid,
            at=day + "T19:00:00-03:00",
            expires_at=day + "T22:00:00-03:00",
            reasoning=why[name],
        )
    return manual(state, context, ops, oid, why[name])


def demo(root):
    store = b.Store(root)
    if (store.root / "events").exists():
        raise ValueError("demo_already_exists_use_status_or_recover")
    context = manager.fixture_context("2026-10-09")
    store.append(
        "INITIALIZED",
        {
            "policy": b.POLICY,
            "portfolio_id": store.root.name,
            "capital": "100000.00",
            "marks": context["marks"],
        },
        "init",
    )
    cases = []

    def record(label, p, execute=True):
        before = b.view(store.load()[0])
        at = p["created_at"]
        validation = manager.publish(store, p, context, at)
        if execute:
            if not validation["valid"]:
                raise ValueError("demo_accounting_failed:" + str(validation["errors"]))
            approval = manager.approve_demo(store, p, context, at)
            manager.execute_demo(store, p, context, approval, at)
        else:
            approval = None
        cases.append(
            {
                "label": label,
                "before": before,
                "proposal": p,
                "validation": validation,
                "approval": approval,
                "after": b.view(store.load()[0]),
            }
        )

    state = store.load()[0]
    p = manager.FakePortfolioManager().propose(
        state,
        context,
        {"PETR4": "0.20", "VALE3": "0.20", "ITUB4": "0.15"},
        "0.45",
        record_id="a-initial",
        at="2026-10-09T19:00:00-03:00",
        expires_at="2026-10-09T22:00:00-03:00",
        reasoning="A · Construir carteira com três empresas; WEGE3 e BBAS3 não recebem alocação apesar dos sinais de compra. Preservar caixa.",
    )
    record("A · Construção inicial", p)
    for oid in store.load()[0]["executions"]:
        store.append(
            "SETTLED",
            {
                "operation_id": oid,
                "session": "2026-10-14",
                "confirmation_source": "SYNTHETIC_CUSTODIAN",
            },
            "settle-" + oid,
        )
    context = manager.fixture_context("2026-10-14")
    store.append("MARKED", {"marks": context["marks"]}, "mark-14")
    p = manual(
        store.load()[0],
        context,
        [make_operation("b-sale", "PETR4", "SELL", "100", context)],
        "b-partial",
        "B · Venda parcial de PETR4. R$ 3.996,00 ficam a receber; nenhuma compra automática.",
    )
    record("B · Venda parcial, recebível indisponível", p)
    store.append(
        "SETTLED",
        {
            "operation_id": "b-sale",
            "session": "2026-10-16",
            "confirmation_source": "SYNTHETIC_CUSTODIAN",
        },
        "settle-b-sale",
    )
    context = manager.fixture_context("2026-10-16")
    store.append("MARKED", {"marks": context["marks"]}, "mark-16")
    p = manual(
        store.load()[0],
        context,
        [make_operation("c-buy", "WEGE3", "BUY", "70", context, dependencies=["b-sale"])],
        "c-after-settlement",
        "C · Recebimento confirmado, nova oportunidade sintética, validação e aprovação novas. Comprar WEGE3 usando caixa já liquidado.",
    )
    record("C · Compra após liquidação", p)
    p = manual(
        store.load()[0],
        context,
        [],
        "d-hold",
        "D · Recomendar nenhuma operação. Preservar posições e caixa.",
    )
    record("D · Não operar", p)
    p = manual(
        store.load()[0],
        context,
        [],
        "e-invalid",
        "E · Exemplo deliberadamente inválido: pesos somam mais de 100%.",
    )
    p = b.sealed(
        {
            **{k: v for k, v in p.items() if k != "sha256"},
            "target_weights": {"PETR4": "0.30", "VALE3": "0.30", "ITUB4": "0.30"},
            "target_cash_weight": "0.30",
        }
    )
    record("E · Alocação impossível bloqueada", p, execute=False)
    report = b.sealed(
        {
            "schema_version": 1,
            "identity": b.IDENTITY,
            "mode": "synthetic",
            "portfolio_id": store.root.name,
            "classification": "OFFLINE_SYNTHETIC_NOT_AI_PERFORMANCE",
            "provider_calls": 0,
            "real_orders": 0,
            "policy": b.POLICY,
            "cases": cases,
            "context": context,
            "verification": store.verify(),
        }
    )
    b.write(store.root / "demo.json", report, immutable=True)
    return report


def recover_demo(store):
    state = store.recover()
    if state and state["pending"]:
        _, events = store.load()
        reservation = next(e for e in reversed(events) if e["kind"] == "RESERVED")
        command = reservation["record_id"].removeprefix("reserve-")
        state = store.append(
            "FILLED",
            {
                "reserved_state_sha256": b.financial_hash(state),
                "session": state["marks"]["session"],
                "at": reservation["payload"]["at"],
            },
            "fill-" + command,
        )
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "verify", "status", "recover"))
    parser.add_argument("--root", type=Path, default=b.OUTPUT / "demo-qualified-v5")
    args = parser.parse_args()
    with no_network():
        store = b.Store(args.root)
        if args.command == "demo":
            demo(args.root)
            result = store.verify()
        elif args.command == "verify":
            result = store.verify()
        elif args.command == "recover":
            result = b.view(recover_demo(store))
        else:
            state, _ = store.load()
            result = b.view(state) if state else {"status": "NOT_INITIALIZED"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("ok") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
