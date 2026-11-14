"""DP-35 / REPLAY-01: isolated exploratory replay of the current wallet flow.

prepare reads local market snapshots only. offline exercises native schemas with
explicit test responses. live requires an explicit aggregate USD ceiling; each
session has a durable claim and is never automatically retried after a failure.
Run this CLI in its own process: module roots are private to that process.
"""

# ruff: noqa: E402
import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT), str(PROJECT / "scripts"), str(PROJECT / "dashboard")]

import auction_orders as orders
import dividends_api as dividends
import manual_portfolio_api as manual
import market_base_api as market
import multiasset_portfolio as b
import multiasset_radar as radar
import pandas as pd
import radar_analysis_api as analysis
import stock_history_api as stock
import wallet_manager_api as wm

from src.experiments.h2_evaluation_offline import no_network

IDENTITY = "HFL-MULTIASSET-HISTORICAL-REPLAY-V1"
OUTPUT = PROJECT / "data/cache/historical-replay"
START, END = "2026-04-06", "2026-04-17"
RATE = "0.03"
CAPITAL = "100000.00"
FIELDS = {
    "abertura": "open",
    "maxima": "high",
    "minima": "low",
    "fechamento": "close",
    "volume": "volume",
}
LIMITATIONS = [
    "Exploratório, produzido agora; cutoff declarado não certifica ausência de contaminação.",
    "OHLCV RAW B3 e fatores Yahoo reconstituídos; aquisição posterior, sem alegação point-in-time.",
    "Saldo inicial hipotético igual nas duas carteiras: 20% por ativo em unidades inteiras aos preços da referência anterior, sem fill de mercado (DP-20).",
    "Custos iniciais zero como no cadastro DP-20; movimentações a 0,03%, escolha existente do gestor.",
    "Caixa econômico do livro atual, venda disponível na cesta; sem liquidação de corretora D+2.",
    "Decisão simulada às 09h; execução pelo OPEN RAW B3 seguinte. PREABE é proxy diário, sem microestrutura do leilão, spread ou impacto.",
    "Prévia/cotação intradiária e alerta de tese velha não reconstituídos; aprovação hipotética às 09h, sem equivalência integral à DP-34.",
    "Sem tentativas de slots 12h/16h, notícias, memória, cache de resultados externos ou comparação de modelos.",
    "Snapshots de proventos B3/Yahoo são reconstituídos; revisão histórica de anúncio não é conhecida. Splits no bloco impedem execução.",
]


def root_of(name):
    b.key(name)
    path = OUTPUT / name
    if path.resolve() != path.absolute() or OUTPUT.resolve() != OUTPUT.absolute():
        raise ValueError("replay_root_must_not_redirect")
    return path


def checked(path):
    return b.check_seal(radar.read(path))


def save(path, value):
    radar.write(path, b.sealed(value), immutable=True)


def sessions(start=START, end=END):
    return [
        str(d)
        for d in radar.B3Calendar().sessions_between(
            date.fromisoformat(start), date.fromisoformat(end)
        )
    ]


def previous(day):
    d = date.fromisoformat(day)
    return sessions(str(d - timedelta(days=10)), str(d - timedelta(days=1)))[-1]


def contracts():
    paths = [
        Path(__file__),
        Path(wm.__file__),
        Path(manual.__file__),
        Path(orders.__file__),
        Path(dividends.__file__),
    ]
    return {
        **radar.frozen_sources(),
        **{str(p.relative_to(PROJECT)).replace("\\", "/"): b.sha_file(p) for p in paths},
        "manager_contract": wm.contracts(),
    }


def prepare(root, source):
    """Freeze only local market evidence. No read of production wallet/LLM ledgers."""
    if (root / "manifest.json").exists():
        m, assets = load(root)
        for day in m["sessions"]:
            for ticker in m["universe"]:
                freeze_input(root, m, assets, ticker, day)
        return m
    market.ROOT, stock.ROOT = source / "market-base-v1", source / "stock-history-v1"
    days = sessions()
    first = previous(days[0])
    warmup = str(date.fromisoformat(first) - timedelta(days=450))
    bundle = {}
    with no_network():
        sources = [
            {k: f[k] for k in ("file_name", "sha256", "raw_sha256", "url", "acquired_at")}
            for f in market.acquired()
        ]
        for ticker in radar.EXAMPLES:
            series = market.series(ticker, END)
            rows = [r for r in series["rows"] if r["date"] >= warmup]
            expected = sessions(warmup, END)
            if [r["date"] for r in rows] != expected:
                raise ValueError("market_calendar_coverage_" + ticker)
            if any(
                r["conflict"]
                or not r["factor"]
                or any(not pd.notna(r[k]) or r[k] <= 0 for k in market.FIELDS)
                or not pd.notna(r["factor"])
                or r["factor"] <= 0
                for r in rows
            ):
                raise ValueError("market_missing_conflicting_or_nonpositive_" + ticker)
            snap = stock.load(ticker)
            csv = stock.ROOT / ticker / (snap["raw_sha256"] + ".csv")
            if b.sha_file(csv) != snap["raw_sha256"]:
                raise ValueError("yahoo_action_source_changed")
            actions = pd.read_csv(csv)
            action_days = actions["Date"].str[:10]
            actions = actions[(action_days >= days[0]) & (action_days <= END)]
            if (actions["Stock Splits"] != 0).any():
                raise ValueError("split_requires_explicit_adapter_" + ticker)
            ds = dividends.snapshot(ticker)
            if ds is None:
                raise ValueError("dividend_snapshot_missing_" + ticker)
            # A Yahoo dividend without a matching B3 entitlement is an unresolved event.
            ex_dates = {
                radar.B3Calendar()
                .next_session(date.fromisoformat(e["data_com"]))
                .isoformat()
                for e in ds["events"]
            }
            if any(
                r["Date"][:10] not in ex_dates
                for r in actions.to_dict("records")
                if r["Dividends"]
            ):
                raise ValueError("unmatched_dividend_" + ticker)
            target = root / "market/dividends" / ticker
            radar.write(target / (ds["sha256"] + ".json"), ds, immutable=True)
            radar.write(
                target / "latest.json",
                b.sealed({"snapshot": ds["sha256"]}),
                immutable=True,
            )
            bundle[ticker] = {
                "rows": rows,
                "factor_source": series["factor_source"],
                "dividend_snapshot": ds["sha256"],
                "actions": actions.to_dict("records"),
                "actions_source_sha256": snap["raw_sha256"],
            }
        save(
            root / "market.json",
            {"identity": IDENTITY, "sources": sources, "assets": bundle},
        )
        manifest = {
            "identity": IDENTITY,
            "created_at": radar.now().isoformat(),
            "sessions": days,
            "references": {d: previous(d) for d in days},
            "universe": list(radar.EXAMPLES),
            "market_sha256": b.sha_file(root / "market.json"),
            "capital": CAPITAL,
            "cost_rate_pct": RATE,
            "cost_source": "Current wallet-manager choice 2026-10-20; DP-24/34",
            "contracts": contracts(),
            "limitations": LIMITATIONS,
        }
        save(root / "manifest.json", manifest)
        for day in days:
            for ticker in radar.EXAMPLES:
                freeze_input(root, manifest, bundle, ticker, day)
    return checked(root / "manifest.json")


def freeze_input(root, manifest, assets, ticker, day):
    ref = manifest["references"][day]
    start = str(date.fromisoformat(ref) - timedelta(days=450))
    rows = [r for r in assets[ticker]["rows"] if start <= r["date"] <= ref]
    bars = pd.DataFrame(
        [
            {k: r[v] * (r["factor"] if k != "volume" else 1) for k, v in FIELDS.items()}
            for r in rows
        ],
        index=pd.DatetimeIndex([r["date"] for r in rows]),
    )
    features, metrics = radar.technical_input(bars)
    csv = bars.to_csv(lineterminator="\n").encode()
    folder = radar.folder_for(root / "sessions" / day / "radar", ticker, ref)
    doc = radar.manifest("live")
    radar.write(folder / "bars.csv", csv, immutable=True)
    radar.write(
        folder / "input.json",
        {
            "schema_version": 1,
            "identity": radar.IDENTITY,
            "ticker": ticker,
            "session": ref,
            "prepared_at": manifest["created_at"],
            "manifest": doc,
            "manifest_sha256": radar.digest(doc),
            "history": {
                "sha256": hashlib.sha256(csv).hexdigest(),
                "start": rows[0]["date"],
                "bars": len(rows),
            },
            "adjusted_close": float(bars.iloc[-1]["fechamento"]),
            "raw_bar": {k: rows[-1][v] for k, v in FIELDS.items()},
            "source": {
                "identity": IDENTITY,
                "market_sha256": manifest["market_sha256"],
                "factor_source": assets[ticker]["factor_source"],
                "availability": "RECONSTRUCTED_NOT_POINT_IN_TIME",
            },
            "features": features,
            "risk_metrics": metrics,
        },
        immutable=True,
    )
    radar.checked_input(folder.parents[2], ticker, ref)


def load(root):
    m = checked(root / "manifest.json")
    if (
        m["identity"] != IDENTITY
        or m["contracts"] != contracts()
        or b.sha_file(root / "market.json") != m["market_sha256"]
    ):
        raise ValueError("replay_contract_or_market_changed")
    return m, checked(root / "market.json")["assets"]


def preflight(root, max_usd=None):
    m, _ = load(root)
    analyst = (
        b.dec(str(radar.estimate({"manifest": {"mode": "live"}})["usd_reserved"])) * 5
    )
    c = wm.CONFIG
    manager = (
        b.dec(c["input_bytes_max"]) * b.dec(c["input_usd_million_ceiling"])
        + b.dec(c["options"]["max_output_tokens"])
        * b.dec(c["output_usd_million_ceiling"])
    ) / 1000000
    total = (analyst + manager) * len(m["sessions"])
    errors = []
    if (root / "execution_mode.json").exists() and checked(root / "execution_mode.json")[
        "mode"
    ] != "REAL_INFERENCE":
        errors.append("offline_root_cannot_run_live")
    for day in m["sessions"]:
        ref = m["references"][day]
        for t in m["universe"]:
            data = radar.checked_input(root / "sessions" / day / "radar", t, ref)
            if data["session"] >= day:
                raise ValueError("decision_input_lookahead")
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        errors.append("gemini_api_key_missing")
    if max_usd is None:
        errors.append(
            "aggregate_replay_usd_ceiling_required_DP34_only_covers_daily_routine"
        )
    elif b.dec(max_usd) < total:
        errors.append("aggregate_ceiling_below_full_reservation")
    report = {
        "identity": IDENTITY,
        "manifest_sha256": m["sha256"],
        "sessions": m["sessions"],
        "calls_max": len(m["sessions"]) * 31,
        "http_attempts_per_call": 1,
        "reservation_per_session_usd": str(analyst + manager),
        "reservation_total_usd": str(total),
        "maximum_at_current_2026_rates_usd": str(total / 2),
        "planning_estimate_analysts_usd": str(b.dec("0.14625") * len(m["sessions"])),
        "manager_planning_estimate": "Depends on daily opinions and holdings; reserve is the upper bound",
        "max_usd": max_usd,
        "credit_eligibility": "NOT_VERIFIED; USD ceiling allows API billing independent of promotional credit",
        "price_checked": "2026-11-12",
        "price_source": "https://aistudio.google.com/docs/pricing#gemini-3.8-flash",
        "ready": not errors,
        "errors": errors,
    }
    return {**report, "confirmation_token": b.digest(report)}


def wallets():
    return {w["strategy"]: w for w in manual.get({})["wallets"]}


def post_trade(wallet, trade, command):
    req = {"kind": "TRADE", "wallet": wallet, "trade": trade}
    token = manual.post("preview", {"request": req})["preview_token"]
    return manual.post(
        "confirm",
        {"request": req, "command_id": command, "preview_token": token, "confirm": True},
    )


def initialize(root, m, assets):
    manual.ROOT = root / "book"
    market.ROOT = root / "market"  # dividend snapshots only; no production source writes
    if manual.path().exists():
        checked(root / "initialization.json")
        return
    day, ref = m["sessions"][0], m["references"][m["sessions"][0]]
    for strategy in ("MULTIAGENT", "BUY_HOLD"):
        request = {
            "kind": "CREATE",
            "name": IDENTITY + " " + strategy,
            "nature": "SIMULATION",
            "capital": m["capital"],
            "start_date": day,
            "strategy": strategy,
            "comparison_group": root.name,
            "initialization_note": "HYPOTHETICAL_INITIAL_REFERENCE_ALLOCATION; no historical market fill; reference "
            + ref,
        }
        w = manual.post(
            "confirm",
            {
                "request": request,
                "command_id": "create-" + strategy,
                "preview_token": None,
                "confirm": True,
            },
        )["wallet"]
        for t in m["universe"]:
            price = b.dec(
                str(next(r for r in assets[t]["rows"] if r["date"] == ref)["close"])
            )
            q = int(b.dec(m["capital"]) / 5 / price)
            post_trade(
                w["id"],
                {
                    "ticker": t,
                    "side": "BUY",
                    "quantity": str(q),
                    "price": str(price),
                    "costs": "0.00",
                    "economic_date": day,
                },
                "initial-" + strategy + "-" + t,
            )
    save(
        root / "initialization.json",
        {
            "classification": "HYPOTHETICAL_INITIAL_REFERENCE_ALLOCATION",
            "wallets": wallets(),
            "reference": ref,
        },
    )


def fake_manager(method, url, headers, body):
    c = json.loads(body["contents"][0]["parts"][0]["text"])
    # Test-only: make an eligible reduction so propagation is exercised, never a result.
    held = {p["ticker"]: int(b.dec(p["quantity"])) for p in c["wallet"]["positions"]}
    actions = [
        {
            "ticker": t,
            "side": "SELL"
            if held.get(t, 0)
            and o["recommendation"] == "VENDA"
            and o["risk_verdict"] == "APROVADO"
            else "HOLD",
            "quantity": "1"
            if held.get(t, 0)
            and o["recommendation"] == "VENDA"
            and o["risk_verdict"] == "APROVADO"
            else "0",
            "reasoning": "OFFLINE_TEST_ONLY",
        }
        for t, o in c["opinions"].items()
    ]
    return json.dumps(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "summary": "OFFLINE_TEST_ONLY",
                                        "actions": actions,
                                        "risks": [],
                                    }
                                )
                            }
                        ]
                    },
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 80,
                "thoughtsTokenCount": 20,
                "totalTokenCount": 200,
            },
            "modelVersion": radar.MODEL,
            "responseId": "OFFLINE_TEST_ONLY",
        }
    ).encode()


def manager(root, c, offline):
    save(root / "context.json", c)
    bank = wm.global_cli.CallBank(root / "calls.sqlite", b.digest(c), IDENTITY)

    def gate():
        load(root.parents[2])
        if checked(root / "context.json")["sha256"] != b.digest(c):
            raise ValueError("manager_context_changed")

    try:
        client = wm.WalletClient(
            bank,
            "L01",
            {"model": wm.CONFIG["model"], "retry_attempts": 1, "retry_base_delay": 0},
            fresh=True,
            gate=gate,
            transport=fake_manager if offline else None,
            synthetic=offline,
        )
        raw = asyncio.run(client.propose(c))
        return wm.compile_proposal(c, raw)
    finally:
        journal = bank.export("L01")
        radar.write(root / "provider_journal.jsonl", journal, immutable=True)
        bank.close()


def valuation(w, rows, day):
    items = dividends.entitlements(w, day)
    _, receivable = dividends.on(items, day)
    equity = (
        b.dec(w["cash"])
        + receivable
        + sum(
            (
                b.dec(p["quantity"]) * b.dec(str(rows[p["ticker"]]["close"]))
                for p in w["positions"]
            ),
            b.ZERO,
        )
    )
    return {
        "equity": str(b.money(equity)),
        "cash": w["cash"],
        "receivable": str(receivable),
        "costs": w["costs"],
        "positions": {p["ticker"]: p["quantity"] for p in w["positions"]},
        "return_pct": str((equity / b.dec(CAPITAL) - 1) * 100),
    }


def execute(root, m, assets, *, offline=False, max_usd=None, only=None):
    save(
        root / "execution_mode.json",
        {"mode": "OFFLINE_TEST_ONLY" if offline else "REAL_INFERENCE"},
    )
    initialize(root, m, assets)
    for day in m["sessions"][:only]:
        folder = root / "sessions" / day
        if (folder / "day.json").exists():
            continue
        # A crash at any stage is review-only: no replacement paid calls or new fills.
        if (folder / "claim.json").exists():
            raise ValueError("session_claimed_review_required_" + day)
        ref, rr = m["references"][day], folder / "radar"
        report = preflight(root, max_usd) if not offline else None
        if report and not report["ready"]:
            raise ValueError("replay_paid_preflight_blocked")
        save(
            folder / "claim.json",
            {
                "identity": IDENTITY,
                "day": day,
                "offline": offline,
                "preflight": report,
                "created_at": radar.now().isoformat(),
            },
        )
        dividends.book_received(ref)
        before = wallets()
        check = radar.preflight(m["universe"], rr, day=ref, max_usd=4)
        if offline:
            # Existing radar records retain live-market provenance; only transport is fake.
            outcomes = radar.run(
                m["universe"],
                check["confirmation_token"],
                rr,
                day=ref,
                max_usd=4,
                authorize_paid=True,
                transport=radar.fake_gemini,
            )
        else:
            outcomes = radar.run(
                m["universe"],
                check["confirmation_token"],
                rr,
                day=ref,
                max_usd=4,
                authorize_paid=True,
            )
        if any(o.get("status") != "COMPLETED" for o in outcomes):
            raise ValueError("incomplete_committee_review_required_" + day)
        opinions = {
            o["ticker"]: {
                "recommendation": o["recommendation"],
                "risk_verdict": o["risk"]["verdict"],
                "confidence": o["technical_signal"]["confidence"],
                "features": o["features"],
                "individual_risk": o["risk"],
                "technical_signal": o["technical_signal"],
            }
            for o in outcomes
        }
        prices = {o["ticker"]: str(o["raw_bar"]["fechamento"]) for o in outcomes}
        c = {
            "wallet": analysis.wallet_snapshot(before["MULTIAGENT"]),
            "reference_session": ref,
            "target_date": day,
            "prices": prices,
            "opinions": opinions,
            "cost_rate_pct": m["cost_rate_pct"],
            "classification": "EXPLORATORY_HISTORICAL_REPLAY_CREATED_NOW",
            "snapshot": {"valuation_session": ref},
        }
        compiled = manager(folder / "manager", c, offline)
        save(folder / "proposal.json", compiled)
        at = datetime.fromisoformat(day + "T09:00:00").replace(tzinfo=orders.SP)
        auction_day, leg = orders.first_auction(at)
        if (auction_day, leg) != (day, "OPEN"):
            raise ValueError("unexpected_auction")
        rows = {
            t: next(r for r in assets[t]["rows"] if r["date"] == day)
            for t in m["universe"]
        }
        w = before["MULTIAGENT"]
        order = {
            "basket": compiled["trades"],
            "leg": leg,
            "cost_rate_pct": m["cost_rate_pct"],
            "quotes": None,
            "run": root.name,
            "proposal": day,
            "proposal_sha256": b.digest(compiled),
            "context_sha256": b.digest(c),
            "reference_session": ref,
            "target_date": day,
            "session": day,
            "approved_at": at.isoformat(),
            "wallet": {"id": w["id"]},
            "decision_prices": prices,
        }
        requests, source = orders.plan(order, w, rows)
        if requests:
            preview = manual.batch(w["id"], w["revision"], requests, source)
            manual.batch(
                w["id"],
                w["revision"],
                requests,
                source,
                confirm=True,
                token=preview["preview_token"],
            )
        dividends.book_received(day)
        after = wallets()
        save(
            folder / "day.json",
            {
                "identity": IDENTITY,
                "day": day,
                "reference": ref,
                "offline": offline,
                "created_at": radar.now().isoformat(),
                "context_sha256": b.digest(c),
                "before": {
                    k: {
                        "cash": v["cash"],
                        "revision": v["revision"],
                        "positions": v["positions"],
                    }
                    for k, v in before.items()
                },
                "operations": requests,
                "execution_source": source,
                "valuation": {k: valuation(w, rows, day) for k, w in after.items()},
            },
        )
        print(
            json.dumps(
                {
                    "day": day,
                    "offline": offline,
                    "operations": len(requests),
                    "valuation": {
                        k: valuation(w, rows, day)["equity"] for k, w in after.items()
                    },
                }
            ),
            flush=True,
        )
    return write_report(root)


def write_report(root):
    days = [checked(p) for p in sorted((root / "sessions").glob("*/day.json"))]
    records = []
    for p in (root / "sessions").glob("**/provider_journal.jsonl"):
        records.extend(
            json.loads(line)["record"]
            for line in p.read_text(encoding="utf-8").splitlines()
        )
    usage = [r.get("token_usage") or {} for r in records]
    keys = ("prompt_tokens", "completion_tokens", "thoughts_tokens", "total_tokens")
    tokens = {
        k: sum(u[k] for u in usage)
        if usage and all(isinstance(u.get(k), int) for u in usage)
        else None
        for k in keys
    }
    cost = None
    if all(tokens[k] is not None for k in keys[:3]):
        cost = (
            tokens["prompt_tokens"] * 0.75
            + (tokens["completion_tokens"] + tokens["thoughts_tokens"]) * 3.75
        ) / 1e6
    report = {
        "identity": IDENTITY,
        "classification": "OFFLINE_TEST_NOT_INVESTMENT_RESULT"
        if (root / "execution_mode.json").exists()
        and checked(root / "execution_mode.json")["mode"] == "OFFLINE_TEST_ONLY"
        else "EXPLORATORY_REAL_INFERENCE"
        if records or days
        else "NOT_EXECUTED",
        "completed_sessions": len(days),
        "calls_recorded": len(records),
        "tokens": tokens,
        "estimated_cost_usd_not_invoice": 0 if any(d["offline"] for d in days) else cost,
        "latency_ms_total": sum(r["duration_ms"] for r in records),
        "resolved_models": sorted(
            {r["resolved_model"] for r in records if r.get("resolved_model")}
        ),
        "failures": [checked(p) for p in root.glob("**/failure.json")],
        "days": days,
        "limitations": LIMITATIONS,
    }
    radar.write(root / "report.json", b.sealed(report))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "command", choices=("prepare", "preflight", "offline", "live", "report")
    )
    p.add_argument("--id", required=True)
    p.add_argument("--source-platform", type=Path)
    p.add_argument("--max-usd")
    p.add_argument("--confirm")
    p.add_argument("--only", type=int, choices=range(1, 11))
    args = p.parse_args()
    root = root_of(args.id)
    if args.command == "prepare":
        if args.source_platform is None:
            p.error("--source-platform required")
        prepare(root, args.source_platform.resolve())
    m, assets = load(root)
    if args.command in ("prepare", "preflight"):
        report = preflight(root, args.max_usd)
        radar.write(root / "preflight.json", b.sealed(report))
        print(json.dumps(report, indent=2))
    elif args.command == "report":
        print(json.dumps(write_report(root), indent=2))
    else:
        offline = args.command == "offline"
        if not offline:
            report = preflight(root, args.max_usd)
            if not report["ready"] or args.confirm != report["confirmation_token"]:
                p.error(
                    "explicit aggregate ceiling and current preflight --confirm token required"
                )
        with radar._exclusive_state_lock(root / "operation"):
            try:
                if offline:
                    # No credential or sockets needed even when market mode is historical/live.
                    os.environ["GEMINI_API_KEY"] = "OFFLINE_TEST_NO_SECRET"
                    with no_network():
                        execute(root, m, assets, offline=True, only=args.only)
                else:
                    execute(root, m, assets, max_usd=args.max_usd, only=args.only)
            except Exception as exc:
                # Preserve the banks; a failure never becomes a synthetic investment result.
                radar.write(
                    root / "failure.json",
                    b.sealed(
                        {
                            "error_type": type(exc).__name__,
                            "automatic_retry": False,
                            "created_at": radar.now().isoformat(),
                        }
                    ),
                )
                write_report(root)
                raise


if __name__ == "__main__":
    main()
