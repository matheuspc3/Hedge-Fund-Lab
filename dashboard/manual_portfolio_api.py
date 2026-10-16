"""APP-01/02: independent, append-only personal accounting; never an order executor."""

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import multiasset_portfolio as b
from pilot_paper import bind
from zoneinfo import ZoneInfo

IDENTITY = "HFL-MANUAL-PORTFOLIO-V1"
PROJECT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = PROJECT / "data/platform/manual-v1"
ROOT = Path(os.environ.get("HFL_MANUAL_ROOT", DEFAULT_ROOT))
NATURES = {"SIMULATION": "Simulação manual", "EXTERNAL": "Operações reais externas"}
SCHEMA = (
    "CREATE TABLE identity (name TEXT NOT NULL)",
    "CREATE TABLE events (sequence INTEGER PRIMARY KEY, wallet TEXT NOT NULL, "
    "id TEXT NOT NULL UNIQUE, command TEXT NOT NULL UNIQUE, request TEXT NOT NULL, "
    "body TEXT NOT NULL)",
    "CREATE TRIGGER immutable_update BEFORE UPDATE ON events "
    "BEGIN SELECT RAISE(ABORT, 'immutable_event'); END",
    "CREATE TRIGGER immutable_delete BEFORE DELETE ON events "
    "BEGIN SELECT RAISE(ABORT, 'immutable_event'); END",
)


class Invalid(ValueError):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field


def require(ok, field, message):
    if not ok:
        raise Invalid(field, message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def fields(value, expected):
    require(
        isinstance(value, dict) and set(value) == set(expected),
        "form",
        "Campos ausentes ou desconhecidos. Atualize a página.",
    )


def text(value, field, limit):
    require(
        isinstance(value, str)
        and 0 < len(value.strip()) <= limit
        and all(ord(c) >= 32 for c in value),
        field,
        "Informe um texto válido.",
    )
    return value.strip()


def number(value, field, *, positive=False, units=False):
    try:
        result = b.units(value) if units else b.amount(value, positive=positive)
        # Bound intermediate products and keep all arithmetic exact with Decimal.
        require(result <= Decimal("1e10"), field, "Valor acima do limite de cadastro.")
        return str(result)
    except (ValueError, TypeError, ArithmeticError) as exc:
        raise Invalid(
            field,
            "Informe um número válido, positivo para preço/quantidade; valores em centavos.",
        ) from exc


def day(value, field):
    try:
        require(
            isinstance(value, str) and date.fromisoformat(value).isoformat() == value,
            field,
            "Informe uma data válida.",
        )
        require(
            value <= datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat(),
            field,
            "A data não pode estar no futuro.",
        )
        return value
    except (ValueError, TypeError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid(field, "Informe uma data válida.") from exc


def trade(value):
    fields(value, ("ticker", "side", "quantity", "price", "costs", "economic_date"))
    try:
        symbol = b.ticker(value["ticker"])
    except (ValueError, TypeError) as exc:
        raise Invalid("ticker", "Use o código da ação, por exemplo PETR4.") from exc
    require(value["side"] in ("BUY", "SELL"), "side", "Escolha compra ou venda.")
    return {
        "ticker": symbol,
        "side": value["side"],
        "quantity": number(value["quantity"], "quantity", units=True),
        "price": number(value["price"], "price", positive=True),
        "costs": number(value["costs"], "costs"),
        "economic_date": day(value["economic_date"], "economic_date"),
    }


def request(value):
    require(isinstance(value, dict), "form", "Informe os dados do cadastro.")
    kind = value.get("kind")
    if kind == "CREATE":
        metadata = {"strategy", "comparison_group", "initialization_note"}
        fields(
            value,
            {"kind", "name", "nature", "capital", "start_date"}
            | (metadata if metadata & value.keys() else set()),
        )
        require(value["nature"] in NATURES, "nature", "Escolha a natureza da carteira.")
        result = {
            "kind": kind,
            "name": text(value["name"], "name", 100),
            "nature": value["nature"],
            "capital": number(value["capital"], "capital"),
            "start_date": day(value["start_date"], "start_date"),
        }
        if metadata & value.keys():
            require(
                value["nature"] == "SIMULATION"
                and value["strategy"] in ("BUY_HOLD", "MULTIAGENT"),
                "strategy",
                "Estratégia simulada inválida.",
            )
            result.update(
                strategy=value["strategy"],
                comparison_group=text(value["comparison_group"], "comparison_group", 100),
                initialization_note=text(
                    value["initialization_note"], "initialization_note", 600
                ),
            )
        return result
    if kind == "ARCHIVE":
        fields(value, ("kind", "wallet", "reason"))
        return {
            "kind": kind,
            "wallet": text(value["wallet"], "wallet", 100),
            "reason": text(value["reason"], "reason", 300),
            "trade": None,
        }
    require(kind in ("TRADE", "CORRECTION"), "form", "Tipo de registro inválido.")
    expected = (
        ("kind", "wallet", "trade")
        if kind == "TRADE"
        else ("kind", "wallet", "trade", "target", "reason")
    )
    fields(value, expected)
    wallet = text(value["wallet"], "wallet", 100)
    result = {
        "kind": kind,
        "wallet": wallet,
        "trade": trade(value["trade"]) if value["trade"] is not None else None,
    }
    if kind == "TRADE":
        require(result["trade"] is not None, "form", "Informe a operação.")
    else:
        result.update(
            target=text(value["target"], "target", 100),
            reason=text(value["reason"], "reason", 300),
        )
    return result


def path():
    root = ROOT.resolve()
    # Configuration may isolate tests outside the project, never point at old stores.
    require(
        root == DEFAULT_ROOT.absolute()
        or (
            ROOT.absolute() != DEFAULT_ROOT.absolute()
            and (
                not root.is_relative_to(PROJECT)
                or root.is_relative_to(PROJECT / "data/cache")
                or root.is_relative_to(PROJECT / ".pytest_cache")
            )
        ),
        "form",
        "Diretório de carteiras pessoais inválido.",
    )
    target = root / "manual.sqlite3"
    require(
        target.resolve() == target,
        "form",
        "O banco pessoal não pode redirecionar para outro arquivo.",
    )
    return target


def connect(write=False):
    target = path()
    if write:
        target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        target.as_uri() + ("?mode=rwc" if write else "?mode=ro"), uri=True, timeout=10
    )
    try:
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        if not conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall():
            require(write, "form", "Banco de carteiras indisponível.")
            for statement in SCHEMA:
                conn.execute(statement)
            conn.execute("INSERT INTO identity VALUES (?)", (IDENTITY,))
            conn.execute("PRAGMA user_version=1")
        require(
            conn.execute("PRAGMA user_version").fetchone()[0] == 1
            and conn.execute("SELECT name FROM identity").fetchall() == [(IDENTITY,)]
            and conn.execute("PRAGMA quick_check").fetchone()[0] == "ok",
            "form",
            "Banco incompatível ou danificado. Preserve o arquivo para recuperação.",
        )
        return conn
    except BaseException:
        conn.close()
        raise


def events(conn, wallet):
    result, previous = [], None
    for seq, eid, raw in conn.execute(
        "SELECT sequence,id,body FROM events WHERE wallet=? ORDER BY sequence", (wallet,)
    ):
        event = b.check_seal(json.loads(raw))
        require(
            (event["sequence"], event["id"], event["wallet"], event["previous"])
            == (seq, eid, wallet, previous)
            and event["identity"] == IDENTITY,
            "form",
            "Histórico da carteira inconsistente.",
        )
        result.append(event)
        previous = event["sha256"]
    require(
        bool(result) and result[0]["request"]["kind"] == "CREATE",
        "wallet",
        "Carteira não encontrada.",
    )
    return result


def invariant(state):
    cash = b.dec(state["settled_cash"])
    receivable = sum((b.dec(r["amount"]) for r in state["receivables"].values()), b.ZERO)
    require(
        cash + receivable >= 0
        and all(
            b.dec(p["quantity"]) >= 0 and b.dec(p["basis"]) >= 0
            for p in state["positions"].values()
        ),
        "form",
        "Saldo contábil inválido.",
    )
    require(
        cash
        + receivable
        + sum((b.dec(p["basis"]) for p in state["positions"].values()), b.ZERO)
        == b.dec(state["initial_capital"]) + b.dec(state["realized_pnl"]),
        "form",
        "A reconciliação contábil falhou.",
    )


def replay(history):
    meta = history[0]["request"]
    active, audit, archived = {}, [], False
    for e in history[1:]:
        r = e["request"]
        require(
            not archived, "wallet", "Carteira excluída; não aceita novos lançamentos."
        )
        if r["kind"] == "ARCHIVE":
            # ponytail: exclusion is limited to unused wallets; a full lifecycle
            # for funded/closed portfolios belongs to a later product increment.
            require(
                not audit,
                "wallet",
                "Somente carteiras sem lançamentos podem ser excluídas.",
            )
            archived = True
        order = e["sequence"]
        if r["kind"] == "CORRECTION":
            require(
                r["target"] in active,
                "target",
                "Lançamento já corrigido ou anulado. Atualize a consulta.",
            )
            order = active.pop(r["target"])["order"]
        if r["trade"] is not None:
            active[e["id"]] = {
                **r["trade"],
                "id": e["id"],
                "order": order,
                "recorded_at": e["recorded_at"],
                **({"source": e["source"]} if "source" in e else {}),
            }
        audit.append(
            {
                "id": e["id"],
                "recorded_at": e["recorded_at"],
                **r,
                **({"source": e["source"]} if "source" in e else {}),
            }
        )
    state = {
        "settled_cash": meta["capital"],
        "initial_capital": meta["capital"],
        "positions": {},
        "pending": {},
        "executions": {},
        "receivables": {},
        "costs": "0.00",
        "realized_pnl": "0.00",
    }
    timeline = []
    for op in sorted(active.values(), key=lambda t: (t["economic_date"], t["order"])):
        require(
            op["economic_date"] >= meta["start_date"],
            "economic_date",
            "A operação deve ocorrer na data de início da carteira ou depois dela.",
        )
        q, price, fees = map(b.dec, (op["quantity"], op["price"], op["costs"]))
        gross = b.money(q * price)
        pos = state["positions"].setdefault(op["ticker"], b.position())
        suffix = f" em {op['economic_date']} ({op['ticker']}). Verifique também lançamentos posteriores."
        require(
            op["side"] != "BUY" or gross + fees <= b.dec(state["settled_cash"]),
            "quantity",
            "Caixa insuficiente" + suffix,
        )
        require(
            op["side"] != "SELL" or q <= b.dec(pos["quantity"]),
            "quantity",
            "Quantidade insuficiente" + suffix,
        )
        require(
            op["side"] != "SELL" or b.dec(state["settled_cash"]) + gross >= fees,
            "costs",
            "Caixa insuficiente para cobrir os custos da venda.",
        )
        oid = op["id"]
        state["pending"][oid] = {"cash_reserved": str(gross + fees)}
        pos["reserved"] = op["quantity"] if op["side"] == "SELL" else "0"
        state["marks"] = {
            "session": op["economic_date"],
            "prices": {op["ticker"]: op["price"]},
            "sha256": None,
        }
        state["as_of_session"] = op["economic_date"]
        # Reuse V5 quantity/basis/realization accounting with declared costs. This
        # economic book has no settlement calendar, reservation or execution authority.
        fill = bind(
            b.fill,
            cost=lambda _, fees=fees: fees,
            settlement_day=lambda _: None,
            safety=invariant,
        )
        fill(state, [{**op, "operation_id": oid, "priority": 0}], op["economic_date"])
        state["settled_cash"] = str(
            b.dec(state["settled_cash"])
            + sum((b.dec(r["amount"]) for r in state["receivables"].values()), b.ZERO)
        )
        state["receivables"].clear()
        pos["unsettled"] = "0"
        invariant(state)
        timeline.append(
            {
                **op,
                "cash_after": state["settled_cash"],
                "quantity_after": pos["quantity"],
                "basis_after": pos["basis"],
            }
        )
    positions = [
        {
            "ticker": t,
            "quantity": p["quantity"],
            "basis": p["basis"],
            "average_cost": str(
                (b.dec(p["basis"]) / b.dec(p["quantity"])).quantize(Decimal("0.00000001"))
            ),
            "reference_price": None,
            "market_value": None,
        }
        for t, p in sorted(state["positions"].items())
        if b.dec(p["quantity"]) > 0
    ]
    return {
        "id": history[0]["wallet"],
        **meta,
        "nature_label": NATURES[meta["nature"]],
        "created_at": history[0]["recorded_at"],
        "revision": history[-1]["sha256"],
        "cash": state["settled_cash"],
        "cash_basis": "ECONOMIC_NOT_BROKER_SETTLEMENT",
        "costs": state["costs"],
        "realized_pnl": state["realized_pnl"],
        "positions": positions,
        "trades": timeline,
        "audit": audit,
        "equity": None if positions else state["settled_cash"],
        "return_pct": None,
        "price_source": None,
        "daily_history": [],
        "comparison_group": meta.get("comparison_group"),
        "archived": archived,
    }


def catalog(conn):
    # ponytail: replay O(n) per wallet/read; verified checkpoints are the upgrade
    # once personal histories justify them. No parallel balance storage today.
    return [
        replay(events(conn, row[0]))
        for row in conn.execute(
            "SELECT wallet FROM events GROUP BY wallet ORDER BY MIN(sequence)"
        ).fetchall()
    ]


def get(query):
    require(set(query) <= {"wallet"}, "form", "Consulta inválida.")
    wallets = []
    if path().exists():
        with closing(connect()) as conn:
            wallets = [w for w in catalog(conn) if not w["archived"]]
    selected = next((w for w in wallets if w["id"] == query.get("wallet")), None)
    require(
        not query.get("wallet") or selected is not None,
        "wallet",
        "Carteira não encontrada.",
    )
    return {
        "identity": IDENTITY,
        "wallets": wallets,
        "selected": selected,
        "pilot": {
            "status": "PENDING",
            "capital_per_wallet": "100000.00",
            "initial_weights": dict.fromkeys(
                ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3"), "0.20"
            ),
            "message": "Base comum agentes/Buy & Hold pendente: preços, quantidades, custos, entrada e revisão do limite de 85%.",
        },
    }


def candidate(conn, r):
    history = events(conn, r["wallet"])
    before = replay(history)
    require(
        not before["archived"],
        "wallet",
        "Carteira excluída; não aceita novos lançamentos.",
    )
    e = {
        "id": "preview",
        "wallet": r["wallet"],
        "sequence": history[-1]["sequence"] + 1,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "request": r,
        "sha256": "preview",
    }
    after = replay([*history, e])
    return history, before, after


def append(conn, r, cid, stored_request, wallet, previous, source=None):
    seq = conn.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM events").fetchone()[0]
    event = b.sealed(
        {
            "identity": IDENTITY,
            "sequence": seq,
            "wallet": wallet,
            "id": "entry-" + uuid.uuid4().hex,
            "previous": previous,
            "request": r,
            "origin": r.get("nature") or replay(events(conn, wallet))["nature"],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            **({"source": source} if source is not None else {}),
        }
    )
    conn.execute(
        "INSERT INTO events VALUES (?,?,?,?,?,?)",
        (seq, wallet, event["id"], cid, stored_request, canonical(event)),
    )
    return event


def batch(wallet, revision, requests, source, *, confirm=False, token=None):
    """One SQLite transaction; reuse TRADE replay, corrections and hash chaining."""
    require(bool(requests) and len(requests) <= 5, "form", "Cesta vazia ou excessiva.")
    normalized = [request(r) for r in requests]
    require(
        all(r["kind"] == "TRADE" and r["wallet"] == wallet for r in normalized),
        "form",
        "Cesta de outra carteira ou tipo de registro inválido.",
    )
    signature = b.digest(
        {"wallet": wallet, "revision": revision, "requests": normalized, "source": source}
    )
    with closing(connect(write=confirm)) as conn, conn:
        history = events(conn, wallet)
        before = replay(history)
        require(
            before["nature"] == "SIMULATION",
            "wallet",
            "A cesta automática exige carteira simulada.",
        )
        require(
            before.get("strategy") != "BUY_HOLD",
            "wallet",
            "Buy & Hold não aceita rebalanceamento automático.",
        )
        prior = conn.execute(
            "SELECT request FROM events WHERE command=?",
            ("manager-" + source["proposal_sha256"] + "-0",),
        ).fetchone()
        if prior:
            require(
                prior[0] == signature,
                "form",
                "Cesta já registrada com outros parâmetros.",
            )
            return {"wallet": before, "replayed": True}
        require(
            before["revision"] == revision,
            "wallet",
            "A carteira mudou. Abra uma nova análise.",
        )
        for i, r in enumerate(normalized):
            history.append(
                {
                    "id": "preview-" + str(i),
                    "wallet": wallet,
                    "sequence": history[-1]["sequence"] + 1,
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "request": r,
                    "sha256": "preview",
                }
            )
        after = replay(history)
        if not confirm:
            return {"before": before, "after": after, "preview_token": signature}
        require(token == signature, "form", "A prévia mudou. Revise a cesta novamente.")
        previous = before["revision"]
        for i, r in enumerate(normalized):
            event = append(
                conn,
                r,
                "manager-" + source["proposal_sha256"] + "-" + str(i),
                signature,
                wallet,
                previous,
                source,
            )
            previous = event["sha256"]
        return {"wallet": replay(events(conn, wallet)), "replayed": False}


def post(command, payload):
    require(command in ("preview", "confirm"), "form", "Ação desconhecida.")
    fields(
        payload,
        ("request",)
        if command == "preview"
        else ("request", "command_id", "preview_token", "confirm"),
    )
    r = request(payload["request"])
    if command == "preview":
        require(r["kind"] != "CREATE", "form", "Cadastro não precisa de prévia.")
        require(path().exists(), "wallet", "Crie uma carteira primeiro.")
        with closing(connect()) as conn:
            _, before, after = candidate(conn, r)
        return {
            "before": before,
            "after": after,
            "preview_token": b.digest({"revision": before["revision"], "request": r}),
        }
    require(payload["confirm"] is True, "form", "Confirme o registro.")
    cid = text(payload["command_id"], "form", 100)
    require(
        isinstance(payload["preview_token"], (str, type(None))),
        "form",
        "Prévia inválida.",
    )
    stored_request = canonical({"request": r, "preview_token": payload["preview_token"]})
    with closing(connect(write=True)) as conn, conn:
        prior = conn.execute(
            "SELECT wallet,id,request FROM events WHERE command=?", (cid,)
        ).fetchone()
        if prior:
            require(
                prior[2] == stored_request,
                "form",
                "Confirmação repetida com dados diferentes.",
            )
            return {
                "wallet": replay(events(conn, prior[0])),
                "event_id": prior[1],
                "replayed": True,
            }
        if r["kind"] == "CREATE":
            require(payload["preview_token"] is None, "form", "Cadastro inválido.")
            wallet, previous = "manual-" + uuid.uuid4().hex, None
        else:
            history, before, _ = candidate(conn, r)
            require(
                payload["preview_token"]
                == b.digest({"revision": before["revision"], "request": r}),
                "form",
                "A carteira mudou. Refaça a prévia antes de confirmar.",
            )
            wallet, previous = r["wallet"], history[-1]["sha256"]
        event = append(conn, r, cid, stored_request, wallet, previous)
        result = replay(events(conn, wallet))
    return {"wallet": result, "event_id": event["id"], "replayed": False}
