"""Read the archived replay; export a reproducible position/coverage audit offline.

Run: .venv/Scripts/python.exe scripts/audit_replay_positions.py
Assertions reconcile all six books and fail on coverage/accounting discrepancies.
"""
import csv
import io
import json
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal as D, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "output/replay-continuo-20261113"
OUT = PROJECT / "output/auditoria-replay-20261115"


def money(value):
    return D(value).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def table(name, rows):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v
                          for k, v in row.items()} for row in rows)


def audit():
    archive = SOURCE / "explorador_replay_2026-04_2026-11.zip"
    archive_hash = sha256(archive.read_bytes()).hexdigest()
    assert archive_hash == json.loads((SOURCE / "backup_verificado.json").read_text())["portable_sha256"]
    with zipfile.ZipFile(archive) as z:
        names = ["explorer.json", "calls.json", "manifest.json", "daily.csv", "operations.csv", "decisions.csv", "dividends.csv", "calls.csv"]
        originals = {name: z.read(name) for name in names}
    data = json.loads(originals["explorer.json"])
    calls = json.loads(originals["calls.json"])["logical_calls"]
    sessions = data["campaign"]["sessions"]
    tickers = sorted(data["market"])
    assert len(sessions) == len(set(sessions)) == 153 and data["completed"]
    assert sessions == [day["day"] for day in data["days"]]
    assert set(sessions) == set(data["analyses"]) == set(data["managers"])
    prices = {t: {r["date"]: D(str(r["close"])) for r in data["market"][t]["rows"]} for t in tickers}
    prompts, call_groups = {}, defaultdict(list)
    for call in calls:
        record = call["record"]
        assert record and record["status"] == "ok"
        for field in ("user_prompt", "system_prompt"):
            assert sha256(record[field].encode()).hexdigest() == record[field + "_sha256"]
        parts = call["bank"].split("/")
        day, ticker = parts[1], parts[3] if parts[2] == "radar" else "MANAGER"
        call_groups[day, ticker, record["stage"]].append(record)
        if ticker == "MANAGER":
            assert day not in prompts
            prompts[day] = json.loads(record["user_prompt"])

    # Reconstruct positions/cash from economic dates, independently of daily.csv.
    operations, attribution, daily_rows = [], [], []
    for strategy, events in data["events"].items():
        assert len({e["id"] for e in events}) == len(events)
        initial = next(e["request"]["capital"] for e in events if e["request"]["kind"] == "CREATE")
        cash, costs, quantity = D(initial), D(0), dict.fromkeys(tickers, 0)
        by_day, flows, payments = defaultdict(list), defaultdict(D), defaultdict(D)
        for event in events:
            req = event["request"]
            if req["kind"] == "TRADE":
                by_day[req["trade"]["economic_date"]].append(event)
            elif req["kind"] == "DIVIDEND":
                by_day[req["dividend"]["payment_date"]].append(event)
        for day in data["days"]:
            date = day["day"]
            for event in by_day[date]:
                req = event["request"]
                if req["kind"] == "DIVIDEND":
                    div = req["dividend"]
                    cash += D(div["net"])
                    payments[div["ticker"]] += D(div["net"])
                    continue
                tr = req["trade"]
                t, side, n = tr["ticker"], tr["side"], int(tr["quantity"])
                before = quantity[t]
                assert n > 0 and side in ("BUY", "SELL")
                quantity[t] += n if side == "BUY" else -n
                assert quantity[t] >= 0
                gross, cost = money(D(tr["price"]) * n), D(tr["costs"])
                flow = (gross if side == "SELL" else -gross) - cost
                cash += flow
                costs += cost
                flows[t] += flow
                operations.append({"strategy": strategy, "date": date, "ticker": t, "side": side, "quantity": n,
                                   "quantity_before": before, "quantity_after": quantity[t],
                                   "initial": event["source"].get("kind") == "CONTINUOUS_REPLAY_INITIALIZATION",
                                   "full_exit": before > 0 and quantity[t] == 0,
                                   "entry_from_zero": before == 0 and quantity[t] > 0,
                                   "price": tr["price"], "costs": cost, "event_id": event["id"]})
            state = day["valuation"][strategy]
            assert quantity == {t: int(state["positions"].get(t, 0)) for t in tickers}
            assert cash == D(state["cash"]) and costs == D(state["costs"]) and cash >= 0
            invested = sum(quantity[t] * prices[t][date] for t in tickers)
            assert cash + invested + D(state["receivable"]) == D(state["equity"])
            if strategy == "MULTIAGENT":
                for t in tickers:
                    daily_rows.append({"date": date, "ticker": t, "quantity": quantity[t],
                                       "value": quantity[t] * prices[t][date],
                                       "weight_equity_pct": quantity[t] * prices[t][date] / D(state["equity"]) * 100,
                                       "cash": cash, "equity": state["equity"]})
        for t in tickers:
            receivable = sum((D(e["net"]) for e in data["entitlements"][sessions[-1]][strategy]
                              if e["ticker"] == t and e["state"] == "A_RECEBER"), D(0))
            end_value = quantity[t] * prices[t][sessions[-1]]
            attribution.append({"strategy": strategy, "ticker": t, "net_trade_cashflow_including_initial": flows[t],
                                "paid_dividends": payments[t], "receivable": receivable, "final_market_value": end_value,
                                "pnl": flows[t] + payments[t] + receivable + end_value})
        assert sum(r["pnl"] for r in attribution if r["strategy"] == strategy) == D(state["equity"]) - D(initial)

    multi = [o for o in operations if o["strategy"] == "MULTIAGENT"]
    coverage, votes, signals, exceptions = [], [], [], []
    for day in sessions:
        prompt = prompts[day]
        assert set(prompt["prices"]) == set(prompt["opinions"]) == set(tickers)
        assert prompt["target_date"] == day and prompt["reference_session"] < day
        assert set(data["analyses"][day]) == set(tickers)
        assert len(call_groups[day, "MANAGER", "global_portfolio_manager"]) == 1
        actions = data["managers"][day]["rows"]
        assert len(actions) == 5 and {a["ticker"] for a in actions} == set(tickers)
        raw_response = json.loads(call_groups[day, "MANAGER", "global_portfolio_manager"][0]["raw_response"])
        assert raw_response == data["managers"][day]["response"]
        executed = {(o["ticker"], o["side"], o["quantity"]) for o in multi if o["date"] == day and not o["initial"]}
        assert executed == {(r["ticker"], r["side"], int(r["quantity"])) for r in actions if r["side"] != "HOLD"}
        for t in tickers:
            a = data["analyses"][day][t]
            row = next(r for r in actions if r["ticker"] == t)
            assert a["status"] == "COMPLETED" and a["session"] == prompt["reference_session"]
            assert len(a["votes"]) == len(call_groups[day, t, "technical_analyst"]) == 5
            assert {v["analyst_id"] for v in a["votes"]} == {1, 2, 3, 4, 5}
            assert prompt["opinions"][t]["recommendation"] == a["recommendation"]
            assert prompt["opinions"][t]["risk_verdict"] == a["risk"]["verdict"]
            hard = a["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"
            assert len(call_groups[day, t, "risk_manager"]) == (0 if hard else 1)
            held = next((p["quantity"] for p in prompt["wallet"]["positions"] if p["ticker"] == t), "0")
            assert D(row["quantity_before"]) == D(held)
            coverage.append({"date": day, "ticker": t, "analyst_calls": 5, "risk_calls": 0 if hard else 1,
                             "hard_veto": hard, "in_manager_prompt": True, "in_manager_response": True,
                             "quantity_before": held})
            approved = a["risk"]["verdict"] == "APROVADO"
            affordable = int(D(prompt["wallet"]["cash"]) / (D(prompt["prices"][t]) * D("1.0003")))
            record = {"date": day, "ticker": t, "technical_signal_before_risk": a["technical_signal"]["signal"],
                      "recommendation": a["recommendation"],
                      "risk_verdict": a["risk"]["verdict"], "hard_veto": hard,
                      "manager_side": row["side"], "quantity_before": held,
                      "cash_before": prompt["wallet"]["cash"], "reference_price": prompt["prices"][t],
                      "affordable_shares_before_other_trades": affordable, "reasoning": row["reasoning"]}
            signals.append(record)
            if not approved:
                assert row["side"] == "HOLD"
            if D(held) == 0 and a["recommendation"] == "COMPRA" and approved and row["side"] == "HOLD":
                exceptions.append(record)
            for v in a["votes"]:
                votes.append({"date": day, "ticker": t, "analyst_id": v["analyst_id"],
                              "signal": v["signal"]["signal"], "confidence": v["signal"]["confidence"]})

    summary, episodes = [], []
    for t in tickers:
        ops = [o for o in multi if o["ticker"] == t]
        after = [o for o in ops if not o["initial"]]
        entries = [o["date"] for o in ops if o["entry_from_zero"]]
        exits = [o["date"] for o in ops if o["full_exit"]]
        for date in exits:
            returned = next((entry for entry in entries if entry > date), None)
            flat = [day for day in sessions if day >= date and (returned is None or day < returned)]
            episodes.append({"ticker": t, "exit": date, "reentry": returned or "", "flat_sessions": len(flat),
                             "no_return_until": sessions[-1] if returned is None else ""})
        counts = Counter(o["side"] for o in after)
        summary.append({"ticker": t, "initial_quantity": ops[0]["quantity"], "buys_after_initial": counts["BUY"],
                        "sells": counts["SELL"], "holding_episodes_including_initial": len(entries),
                        "full_exits": len(exits), "reentries": len(entries) - 1,
                        "sessions_held_at_close": sum(r["quantity"] > 0 for r in daily_rows if r["ticker"] == t),
                        "final_quantity": ops[-1]["quantity_after"],
                        "recommendations": dict(Counter(r["recommendation"] for r in signals if r["ticker"] == t))})
    assert len(multi) == 91 and sum(r["buys_after_initial"] + r["sells"] for r in summary) == 86
    assert len(votes) == 3825 and len(coverage) == 765 and len(calls) == 4703

    # Additional diagnostics for the 5 findings (unanimity, RSI/features by signal, avg buy/sell prices, concentration).
    unanimous_days = 0
    feature_by_signal = defaultdict(list)
    for day in sessions:
        for t in tickers:
            a = data["analyses"][day][t]
            counts = a["consensus"]["counts"]
            if max(counts.values()) == 5:
                unanimous_days += 1
            feature_by_signal[a["consensus"]["winning_signal"]].append(a["features"])
    assert unanimous_days == 635  # 83.01% of 765 asset-days are 5-0-0 unanimous

    significant_assets_per_day = Counter()
    for day in sessions:
        n_sig = sum(1 for r in daily_rows if r["date"] == day and r["weight_equity_pct"] >= D("2"))
        significant_assets_per_day[n_sig] += 1
    assert significant_assets_per_day[2] == 101  # 66.01% of days held only 2 assets with weight >= 2%

    price_comparison = []
    for t in tickers:
        ma_buys = [o for o in operations if o["strategy"] == "MULTIAGENT" and o["ticker"] == t and o["side"] == "BUY" and not o["initial"]]
        ma_sells = [o for o in operations if o["strategy"] == "MULTIAGENT" and o["ticker"] == t and o["side"] == "SELL"]
        bb_buys = [o for o in operations if o["strategy"] == "BOLLINGER_20_2" and o["ticker"] == t and o["side"] == "BUY" and not o["initial"]]
        bb_sells = [o for o in operations if o["strategy"] == "BOLLINGER_20_2" and o["ticker"] == t and o["side"] == "SELL"]
        avg_p = lambda rows: (sum(D(r["price"]) * r["quantity"] for r in rows) / sum(r["quantity"] for r in rows)).quantize(D("0.01")) if rows else D("0.00")
        price_comparison.append({
            "ticker": t,
            "multiagent_buy_qty": sum(r["quantity"] for r in ma_buys),
            "multiagent_avg_buy": str(avg_p(ma_buys)),
            "multiagent_sell_qty": sum(r["quantity"] for r in ma_sells),
            "multiagent_avg_sell": str(avg_p(ma_sells)),
            "bollinger_buy_qty": sum(r["quantity"] for r in bb_buys),
            "bollinger_avg_buy": str(avg_p(bb_buys)),
            "bollinger_sell_qty": sum(r["quantity"] for r in bb_sells),
            "bollinger_avg_sell": str(avg_p(bb_sells)),
        })
    csv_rows = {name: list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
                for name, raw in originals.items() if name.endswith(".csv")}
    assert len(csv_rows["daily.csv"]) == 918 and len(csv_rows["operations.csv"]) == len(operations)
    assert len(csv_rows["calls.csv"]) == len(calls)
    for row in csv_rows["daily.csv"]:
        state = data["days"][sessions.index(row["session"])]["valuation"][row["strategy"]]
        assert json.loads(row["positions"]) == state["positions"] and row["equity"] == state["equity"]
    assert Counter(r["event_id"] for r in csv_rows["operations.csv"]) == Counter(o["event_id"] for o in operations)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "originais").mkdir(exist_ok=True)
    for name, raw in originals.items():
        (OUT / "originais" / name).write_bytes(raw)
    for name, rows in [("posicoes_por_ativo.csv", summary), ("saidas_e_retornos.csv", episodes),
                       ("operacoes_classificadas.csv", operations), ("cobertura_diaria.csv", coverage),
                       ("sinais_e_decisoes.csv", signals), ("votos_individuais.csv", votes),
                       ("compra_sem_reentrada.csv", exceptions), ("atribuicao_contabil.csv", attribution),
                       ("posicoes_diarias.csv", daily_rows), ("precos_medios_compra_venda.csv", price_comparison)]:
        table(name, rows)
    signal_features_summary = {
        sig: {
            "count": len(flist),
            "avg_rsi": round(sum(x["rsi"] for x in flist) / len(flist), 2),
            "avg_sma50_gap": round(sum(x["sma50_gap"] for x in flist) / len(flist), 4),
            "avg_sma200_gap": round(sum(x["sma200_gap"] for x in flist) / len(flist), 4),
            "avg_bb_upper_gap": round(sum(x["bb_upper_gap"] for x in flist) / len(flist), 4),
            "avg_bb_lower_gap": round(sum(x["bb_lower_gap"] for x in flist) / len(flist), 4),
        }
        for sig, flist in feature_by_signal.items()
    }
    result = {"status": "PASS", "source_archive_sha256": archive_hash,
              "original_files_sha256": {n: sha256(raw).hexdigest() for n, raw in originals.items()},
              "daily_states_reconciled": 918, "asset_days_covered": len(coverage), "calls": len(calls),
              "unanimous_5_0_asset_days": unanimous_days,
              "days_by_significant_assets_ge_2pct": dict(sorted(significant_assets_per_day.items())),
              "signal_features_summary": signal_features_summary,
              "price_comparison": price_comparison,
              "summary": summary, "episodes": episodes,
              "audit_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT / "verificacao.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    audit()
