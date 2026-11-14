"""DP-36: SMA/Bollinger wallets in the existing book; no network or LLM calls.

Close t -> frozen signal -> official B3 open t+1. Historical reconstruction is
identified as such, with its actual recording time. Each decision and execution
(including holds) is an append-only receipt in the same SQLite transaction as
its trades. The market-update worker advances only explicitly initialized wallets.
"""

import argparse
import math
import sys
import uuid
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[1] / "scripts"),
]
import auction_orders as orders  # noqa: E402
import dividends_api as dividends  # noqa: E402
import manual_portfolio_api as manual  # noqa: E402
import market_base_api as base  # noqa: E402

from src.backtesting.b3_calendar import B3Calendar  # noqa: E402
from src.strategies.bollinger_bands import BollingerParticipant  # noqa: E402
from src.strategies.sma_cross import SMACrossParticipant  # noqa: E402

b, radar = manual.b, base.radar
RULES = {"SMA_50_200": SMACrossParticipant, "BOLLINGER_20_2": BollingerParticipant}
START = "2026-10-14"
IDENTITY = "HFL-RULE-PORTFOLIOS-V1"


def policy(rate):
    rate = manual.number(rate, "cost_rate_pct")
    manual.require(b.dec(rate) <= 2, "cost_rate_pct", "Custo acima de 2% por operação.")
    return {
        "identity": IDENTITY,
        "cost_rate_pct": rate,
        "parameters": {"SMA_50_200": [50, 200], "BOLLINGER_20_2": [20, 2]},
        "allocation": "INDEPENDENT_20_PERCENT_SLEEVES_INTEGER_SHARES",
        "dividends": "CASH_NOT_REINVESTED",
        "signals": "B3_CLOSE_X_YAHOO_FACTOR_FROZEN_VINTAGE",
        "execution": "B3_RAW_OPEN_NEXT_SESSION",
        "sources": {
            name: b.sha_file(Path(__file__).resolve().parents[1] / path)
            for name, path in {
                "engine": "dashboard/rule_portfolios.py",
                "sma": "src/strategies/sma_cross.py",
                "bollinger": "src/strategies/bollinger_bands.py",
            }.items()
        },
    }


def initialize(baseline, rate):
    """Atomic creation of both independent books; retry never clones a wallet twice."""
    config = policy(rate)
    with closing(manual.connect(write=True)) as conn, conn:
        original = manual.replay(manual.events(conn, baseline))
        initial = original["trades"]
        manual.require(
            original.get("strategy") == "BUY_HOLD"
            and original["nature"] == "SIMULATION"
            and original["start_date"] == START
            and b.dec(original["capital"]) == 100000
            and original["comparison_group"]
            and len(initial) == len(base.TICKERS)
            and {t["ticker"] for t in initial} == set(base.TICKERS)
            and all(
                t["economic_date"] == START
                and t["side"] == "BUY"
                and b.dec(t["costs"]) == 0
                and b.dec(t["quantity"]) == int(b.dec(t["quantity"]))
                for t in initial
            ),
            "wallet",
            "A referência deve ser a cesta inicial Buy & Hold de 14/10/2026.",
        )
        seed = [
            {
                k: t[k]
                for k in ("ticker", "side", "quantity", "price", "costs", "economic_date")
            }
            for t in initial
        ]
        source = {
            "kind": "RULE_STRATEGY_INITIALIZATION",
            "baseline": baseline,
            "initial_basket_sha256": b.digest(seed),
            "policy": config,
        }
        found = manual.catalog(conn)
        result = []
        for strategy, name in manual.RULE_STRATEGIES.items():
            existing = [
                w
                for w in found
                if w.get("strategy") == strategy
                and w.get("comparison_group") == original["comparison_group"]
            ]
            manual.require(len(existing) <= 1, "wallet", "Carteiras de regra ambíguas.")
            if existing:
                wallet = existing[0]
                manual.require(
                    manual.events(conn, wallet["id"])[0].get("source") == source,
                    "wallet",
                    "A carteira já existe com outra política; preserve o histórico.",
                )
                result.append(wallet["id"])
                continue
            wallet = "manual-" + uuid.uuid4().hex
            create = manual.request(
                {
                    "kind": "CREATE",
                    "name": name,
                    "nature": "SIMULATION",
                    "capital": original["capital"],
                    "start_date": START,
                    "strategy": strategy,
                    "comparison_group": original["comparison_group"],
                    "initialization_note": "Mesma cesta inicial de 14/10. Regra automática, sem IA; "
                    "sinais históricos reconstruídos e identificados. Sinal no fechamento; execução "
                    "na abertura seguinte. 20% independentes por ativo; proventos ficam em caixa. "
                    f"Custos posteriores: {config['cost_rate_pct']}% por operação.",
                }
            )
            previous = None
            for i, req in enumerate(
                [create, *[{"kind": "TRADE", "wallet": wallet, "trade": t} for t in seed]]
            ):
                event = manual.append(
                    conn,
                    req,
                    f"rule-init-{wallet}-{i}",
                    manual.canonical(req),
                    wallet,
                    previous,
                    source,
                )
                previous = event["sha256"]
            manual.replay(manual.events(conn, wallet))
            result.append(wallet)
        return result


def signal_data(strategy, day, datasets):
    """Reuse the causal strategy adapters, with exactly 201/21 past sessions.

    ponytail: current Yahoo adjustment vintage for reconstruction; freeze the exact
    inputs instead of claiming historical availability. A point-in-time factor archive
    is the upgrade; future closes never enter the window.
    """
    size = 201 if strategy == "SMA_50_200" else 21
    cal = B3Calendar()
    days = [
        d.isoformat()
        for d in cal.sessions_between(
            date.fromisoformat(day) - timedelta(days=450), date.fromisoformat(day)
        )
    ][-size:]
    out = {}
    for ticker in base.TICKERS:
        data = datasets[ticker]
        rows = {r["date"]: r for r in data["rows"]}
        selected = [rows.get(d) for d in days]
        if len(selected) != size or any(
            not r
            or r["conflict"]
            or not r.get("adjusted_close")
            or not math.isfinite(r["adjusted_close"])
            or r["adjusted_close"] <= 0
            or not r.get("volume")
            for r in selected
        ):
            raise ValueError(f"rule_signal_history_missing:{ticker}:{day}")
        values = [r["adjusted_close"] for r in selected]
        out[ticker] = {
            "signal": RULES[strategy](ticker)._signal(
                pd.Series(values, index=pd.to_datetime(days))
            ),
            "factor_source": data["factor_source"],
            "inputs": [[d, v] for d, v in zip(days, values, strict=True)],
            "raw_inputs_sha256": b.digest(selected),
        }
    return out


def classification(target):
    return (
        "PROSPECTIVE_SIMULATION"
        if radar.now() < orders.cutoffs(target)[0]
        else "HISTORICAL_RECONSTRUCTION"
    )


def receipt(conn, wallet, kind, key, source):
    req = {"kind": kind, "wallet": wallet, "trade": None}
    previous = manual.events(conn, wallet)[-1]["sha256"]
    return manual.append(
        conn, req, key, manual.canonical(source), wallet, previous, source
    )


def trades_for(wallet, decision, prices, rate):
    """Each sleeve reuses only its own sale proceeds; dividends remain in book cash."""
    requests = []
    held = {p["ticker"]: int(b.dec(p["quantity"])) for p in wallet["positions"]}
    for ticker, data in decision["signals"].items():
        signal, q = data["signal"], held.get(ticker, 0)
        if not (signal == -1 and q or signal == 1 and not q):
            continue
        p = orders.price_of(prices.get(ticker), "open")
        if not p or p <= 0:
            raise ValueError(
                f"rule_open_missing:{ticker}:{decision['execution_session']}"
            )
        fee = lambda n, price=p: b.money(b.money(n * price) * rate / 100)  # noqa: E731
        if signal == 1:
            budget = b.dec(wallet["capital"]) / len(base.TICKERS)
            for t in wallet["trades"]:
                if t["ticker"] == ticker:
                    gross = b.money(b.dec(t["quantity"]) * b.dec(t["price"]))
                    budget += (
                        gross - b.dec(t["costs"])
                        if t["side"] == "SELL"
                        else -gross - b.dec(t["costs"])
                    )
            budget = min(budget, b.dec(wallet["cash"]))
            q = max(0, int(budget / (p * (1 + rate / 100))))
            while q and b.money(q * p) + fee(q) > budget:
                q -= 1
        if q:
            requests.append(
                manual.request(
                    {
                        "kind": "TRADE",
                        "wallet": wallet["id"],
                        "trade": {
                            "ticker": ticker,
                            "side": "BUY" if signal == 1 else "SELL",
                            "quantity": str(q),
                            "price": str(p),
                            "costs": str(fee(q)),
                            "economic_date": decision["execution_session"],
                        },
                    }
                )
            )
    return sorted(
        requests, key=lambda r: (r["trade"]["side"] != "SELL", r["trade"]["ticker"])
    )


def advance_wallet(wallet_id, days, datasets, today):
    completed = 0
    for day in days:
        with closing(manual.connect(write=True)) as conn, conn:
            history = manual.events(conn, wallet_id)
            config = history[0].get("source", {}).get("policy")
            if not config or config != policy(config["cost_rate_pct"]):
                raise ValueError("rule_policy_changed_preserve_history")
            wallet = manual.replay(history)
            if day < wallet["start_date"]:
                continue
            done = next(
                (
                    e
                    for e in history
                    if e["request"]["kind"] == "RULE_EXECUTION"
                    and e["source"]["decision_session"] == day
                ),
                None,
            )
            if done:
                continue
            decision = next(
                (
                    e
                    for e in history
                    if e["request"]["kind"] == "RULE_DECISION"
                    and e["source"]["decision_session"] == day
                ),
                None,
            )
            if decision is None:
                target = B3Calendar().next_session(date.fromisoformat(day)).isoformat()
                source = {
                    "kind": "RULE_STRATEGY_DECISION",
                    "strategy": wallet["strategy"],
                    "decision_session": day,
                    "execution_session": target,
                    "classification": classification(target),
                    "signals": signal_data(wallet["strategy"], day, datasets),
                }
                decision = receipt(
                    conn,
                    wallet_id,
                    "RULE_DECISION",
                    f"rule-decision-{wallet_id}-{day}",
                    source,
                )
        # The pending decision is durable before looking for a future opening price.
        target = decision["source"]["execution_session"]
        if target > today:
            break
        prices = orders.session_rows(target)
        with closing(manual.connect(write=True)) as conn, conn:
            history = manual.events(conn, wallet_id)
            if any(
                e["request"]["kind"] == "RULE_EXECUTION"
                and e["source"]["decision_session"] == day
                for e in history
            ):
                continue
            wallet = manual.replay(history)
            requests = trades_for(
                wallet, decision["source"], prices, b.dec(config["cost_rate_pct"])
            )
            source = {
                "kind": "RULE_STRATEGY_EXECUTION",
                "strategy": wallet["strategy"],
                "decision_session": day,
                "execution_session": target,
                "classification": decision["source"]["classification"],
                "decision_sha256": decision["sha256"],
                "cost_rate_pct": config["cost_rate_pct"],
                "prices": prices,
                "price_basis": "B3_OFFICIAL_RAW_OPEN_PREABE",
            }
            previous = history[-1]["sha256"]
            for i, req in enumerate(requests):
                event = manual.append(
                    conn,
                    req,
                    f"rule-trade-{wallet_id}-{day}-{i}",
                    manual.canonical(req),
                    wallet_id,
                    previous,
                    source,
                )
                previous = event["sha256"]
            receipt(
                conn,
                wallet_id,
                "RULE_EXECUTION",
                f"rule-execution-{wallet_id}-{day}",
                source,
            )
            manual.replay(
                manual.events(conn, wallet_id)
            )  # rollback the whole basket on any failure
            completed += 1
    wallet = manual.get({"wallet": wallet_id})["selected"]
    # No cash reinvestment: book only after the historical positions have caught up.
    paid = dividends.book_received(today, wallets=[wallet])
    return {"completed": completed, "dividends": paid}


def advance():
    """Called after the market update, never by a GET; each wallet fails independently."""
    wallets = [w for w in manual.get({})["wallets"] if w.get("strategy") in RULES]
    if not wallets:
        return {}
    now = radar.now()
    days = [
        d.isoformat()
        for d in B3Calendar().sessions_between(
            date.fromisoformat(START), date.fromisoformat(radar.last_closed(now))
        )
    ]
    datasets = {t: base.series(t) for t in base.TICKERS}
    out = {}
    for w in wallets:
        try:
            out[w["id"]] = advance_wallet(w["id"], days, datasets, now.date().isoformat())
        except (ValueError, OSError, KeyError, ArithmeticError) as e:
            out[w["id"]] = {"blocked": str(e)}
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--cost-rate-pct", required=True)
    parser.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args()
    print(
        manual.canonical(
            {
                "wallets": initialize(args.baseline, args.cost_rate_pct),
                "progress": advance(),
            }
        )
    )
