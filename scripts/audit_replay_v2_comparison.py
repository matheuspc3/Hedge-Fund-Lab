"""Reconcile REPLAY-02 (v2) exports, verify v1 preservation, and compare v1 vs v2."""

import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal as D, ROUND_HALF_UP
from hashlib import sha256
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
V1_EXPORTS = PROJECT / "data/replays/april-november-2026-flash/exports"
V2_EXPORTS = PROJECT / "data/replays/april-november-2026-flash-v2/exports"
V2_CACHE_EXPORTS = PROJECT / "data/cache/continuous-replay/april-november-2026-flash-v2/exports"
OUT_DIR = PROJECT / "output/auditoria-replay-v2"

V1_EXPECTED_HASHES = {
    "explorer.json": "88c3a0e1f45ffa15d9033a74714821a863c14033c182ce54d3915fa087e5f6e4",
    "calls.json": "b5ef95859304e40d21ef41232ebf2f9187f9c56eede4d91cfff30d85fdaba6fb",
}
REFERENCE_STRATEGIES = (
    "BUY_HOLD",
    "SMA_50_200",
    "BOLLINGER_20_2",
    "EQUAL_WEIGHT_63",
    "MIN_VARIANCE_252_63",
)


def money(value):
    return D(str(value)).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (list, dict)) else v
                for k, v in row.items()
            }
            for row in rows
        )


def verify_v1_preserved(v1_dir):
    hashes = {}
    for name, expected in V1_EXPECTED_HASHES.items():
        path = v1_dir / name
        assert path.exists(), f"missing v1 export: {path}"
        actual = sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"v1 {name} hash changed: {actual} != {expected}"
        hashes[name] = actual
    return hashes


def analyze_campaign(export_dir, expected_identity, *, allow_partial=False):
    export_dir = Path(export_dir)
    manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
    explorer_bytes = (export_dir / "explorer.json").read_bytes()
    assert sha256(explorer_bytes).hexdigest() == manifest["export_sha256"], (
        f"explorer.json sha mismatch in {export_dir}"
    )

    data = json.loads(explorer_bytes)
    calls = json.loads((export_dir / "calls.json").read_text(encoding="utf-8"))["logical_calls"]
    assert data["campaign"]["identity"] == expected_identity
    assert data["completed"] is True
    assert data["budget_audit"]["status"] == "PASS"
    assert D(data["budget"]["exposure_usd"]) <= D("34.78")

    sessions = data["campaign"]["sessions"]
    tickers = sorted(data["market"])
    assert len(sessions) == len(set(sessions)) >= 1
    if not allow_partial:
        assert len(sessions) == 153
    assert sessions == [d["day"] for d in data["days"]]
    prices = {t: {r["date"]: D(str(r["close"])) for r in data["market"][t]["rows"]} for t in tickers}

    call_groups = defaultdict(list)
    manager_prompts = {}
    for call in calls:
        rec = call["record"]
        if rec is None:
            continue
        for field in ("user_prompt", "system_prompt"):
            if rec.get(field) is not None and rec.get(field + "_sha256") is not None:
                assert sha256(rec[field].encode()).hexdigest() == rec[field + "_sha256"]
        parts = call["bank"].split("/")
        day, ticker = parts[1], parts[3] if parts[2] == "radar" else "MANAGER"
        call_groups[day, ticker, rec["stage"]].append(rec)
        if ticker == "MANAGER" and rec["status"] == "ok":
            manager_prompts[day] = json.loads(rec["user_prompt"])

    # Reconstruct all 918 daily wallet states (153 days x 6 strategies) from events.
    operations, attribution, daily_rows = [], [], []
    reconciled_states = 0
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
                operations.append(
                    {
                        "strategy": strategy,
                        "date": date,
                        "ticker": t,
                        "side": side,
                        "quantity": n,
                        "quantity_before": before,
                        "quantity_after": quantity[t],
                        "gross": gross,
                        "initial": "INITIALIZATION" in ((event.get("source") or {}).get("kind") or ""),
                        "full_exit": before > 0 and quantity[t] == 0,
                        "entry_from_zero": before == 0 and quantity[t] > 0,
                        "price": tr["price"],
                        "costs": cost,
                        "event_id": event["id"],
                    }
                )
            state = day["valuation"][strategy]
            assert quantity == {t: int(state["positions"].get(t, 0)) for t in tickers}
            assert cash == D(state["cash"]) and costs == D(state["costs"]) and cash >= 0
            invested = sum(quantity[t] * prices[t][date] for t in tickers)
            assert cash + invested + D(state["receivable"]) == D(state["equity"])
            reconciled_states += 1
            if strategy == "MULTIAGENT":
                for t in tickers:
                    val = quantity[t] * prices[t][date]
                    daily_rows.append(
                        {
                            "date": date,
                            "ticker": t,
                            "quantity": quantity[t],
                            "value": val,
                            "weight_equity_pct": val / D(state["equity"]) * 100,
                            "cash": cash,
                            "equity": state["equity"],
                        }
                    )

        for t in tickers:
            receivable = sum(
                (
                    D(e["net"])
                    for e in data["entitlements"][sessions[-1]][strategy]
                    if e["ticker"] == t and e["state"] == "A_RECEBER"
                ),
                D(0),
            )
            end_value = quantity[t] * prices[t][sessions[-1]]
            attribution.append(
                {
                    "strategy": strategy,
                    "ticker": t,
                    "net_trade_cashflow_including_initial": flows[t],
                    "paid_dividends": payments[t],
                    "receivable": receivable,
                    "final_market_value": end_value,
                    "pnl": flows[t] + payments[t] + receivable + end_value,
                }
            )
        assert sum(r["pnl"] for r in attribution if r["strategy"] == strategy) == D(state["equity"]) - D(initial)

    assert reconciled_states == len(sessions) * len(data["events"])

    # Cross-check CSV exports against explorer.json / events / calls.json.
    csv_rows = {
        name: list(csv.DictReader((export_dir / name).open("r", encoding="utf-8-sig")))
        for name in ("daily.csv", "operations.csv", "calls.csv")
    }
    assert len(csv_rows["daily.csv"]) == reconciled_states
    assert len(csv_rows["operations.csv"]) == len(operations)
    assert len(csv_rows["calls.csv"]) == len(calls)
    for row in csv_rows["daily.csv"]:
        state = data["days"][sessions.index(row["session"])]["valuation"][row["strategy"]]
        assert json.loads(row["positions"]) == state["positions"] and row["equity"] == state["equity"]
    assert Counter(r["event_id"] for r in csv_rows["operations.csv"]) == Counter(o["event_id"] for o in operations)

    # Diagnostics for MULTIAGENT committee, manager, concentration, R7, Trim-to-Fund.
    multi_ops = [o for o in operations if o["strategy"] == "MULTIAGENT"]
    multi_after = [o for o in multi_ops if not o["initial"]]
    vote_splits = Counter()
    feature_by_signal = defaultdict(list)
    feature_by_exec_side = defaultdict(list)
    lens_disagreements = 0
    vetoed_days = []
    r7_executed = []
    trim_to_fund_executed = []
    dust_buys = []
    adjustments_counts = Counter()

    completed_days = [d["day"] for d in data["days"] if d.get("status") == "COMPLETED"]
    gaps = [d["day"] for d in data["days"] if d.get("status") != "COMPLETED"]

    for day in completed_days:
        mgr = data["managers"][day]
        actions = mgr["rows"]
        for adj in mgr.get("adjustments", []):
            adjustments_counts[adj.get("reason", "UNKNOWN")] += 1
        executed_day = {o["ticker"]: o for o in multi_after if o["date"] == day}
        assert {(o["ticker"], o["side"], o["quantity"]) for o in executed_day.values()} == {
            (r["ticker"], r["side"], int(r["quantity"])) for r in actions if r["side"] != "HOLD"
        }

        for t in tickers:
            a = data["analyses"][day][t]
            row = next(r for r in actions if r["ticker"] == t)
            counts = a["consensus"]["counts"]
            top_votes = max(counts.values())
            if top_votes == 5:
                vote_splits["5-0"] += 1
            elif top_votes == 4:
                vote_splits["4-1"] += 1
            elif top_votes == 3:
                vote_splits["3-2"] += 1
            else:
                vote_splits["no_consensus"] += 1

            win = a["consensus"]["winning_signal"] or "MANTER"
            feature_by_signal[win].append(a["features"])

            votes_map = {v["analyst_id"]: v["signal"]["signal"] for v in a["votes"]}
            if len({votes_map[1], votes_map[2], votes_map[3], votes_map[4]}) > 1:
                lens_disagreements += 1

            hard_veto = a["risk_source"] == "HARD_ASSET_VOLATILITY_RULE"
            if a["risk"]["verdict"] == "VETADO":
                vetoed_days.append(
                    {
                        "date": day,
                        "ticker": t,
                        "risk_source": a["risk_source"],
                        "technical_signal": a["technical_signal"]["signal"],
                        "recommendation": a["recommendation"],
                        "executed_side": row["side"],
                        "executed_qty": int(row["quantity"]),
                    }
                )

            if t in executed_day:
                op = executed_day[t]
                feature_by_exec_side[op["side"]].append(a["features"])
                if op["side"] == "BUY":
                    ref_gross = money(D(row["quantity"]) * D(row["price"]))
                    if ref_gross < D("2000.00") or op["gross"] < D("2000.00"):
                        dust_buys.append(
                            {
                                "date": day,
                                "ticker": t,
                                "quantity": op["quantity"],
                                "ref_gross": str(ref_gross),
                                "exec_gross": str(op["gross"]),
                            }
                        )
                if op["side"] == "SELL" and a["risk"]["verdict"] == "VETADO":
                    r7_executed.append(
                        {
                            "date": day,
                            "ticker": t,
                            "risk_source": a["risk_source"],
                            "technical_signal": a["technical_signal"]["signal"],
                            "recommendation": a["recommendation"],
                            "quantity": op["quantity"],
                            "price": op["price"],
                            "gross": str(op["gross"]),
                        }
                    )
                if op["side"] == "SELL" and a["recommendation"] in ("MANTER", "COMPRA"):
                    trim_to_fund_executed.append(
                        {
                            "date": day,
                            "ticker": t,
                            "recommendation": a["recommendation"],
                            "quantity": op["quantity"],
                            "weight_before": row.get("weight_before"),
                            "weight_after": row.get("weight_after"),
                            "gross": str(op["gross"]),
                        }
                    )

    # Concentration metrics
    sig_assets_dist = Counter()
    for day in sessions:
        n_sig = sum(1 for r in daily_rows if r["date"] == day and r["weight_equity_pct"] >= D("2"))
        sig_assets_dist[n_sig] += 1
    max_weight_by_ticker = {
        t: round(max(float(r["weight_equity_pct"]) for r in daily_rows if r["ticker"] == t), 2)
        for t in tickers
    }

    # Episodes & per-asset summary + avg buy/sell prices
    episodes = []
    per_asset = []
    for t in tickers:
        ops = [o for o in multi_ops if o["ticker"] == t]
        after = [o for o in ops if not o["initial"]]
        buys = [o for o in after if o["side"] == "BUY"]
        sells = [o for o in after if o["side"] == "SELL"]
        entries = [o["date"] for o in ops if o["entry_from_zero"]]
        exits = [o["date"] for o in ops if o["full_exit"]]
        for d_exit in exits:
            ret = next((e for e in entries if e > d_exit), None)
            flat = [day for day in sessions if day >= d_exit and (ret is None or day < ret)]
            episodes.append(
                {
                    "ticker": t,
                    "exit": d_exit,
                    "reentry": ret or "",
                    "flat_sessions": len(flat),
                    "no_return_until": sessions[-1] if ret is None else "",
                }
            )
        avg_p = lambda rows: (
            str((sum(D(r["price"]) * r["quantity"] for r in rows) / sum(r["quantity"] for r in rows)).quantize(D("0.01")))
            if rows
            else "0.00"
        )
        attr = next(a for a in attribution if a["strategy"] == "MULTIAGENT" and a["ticker"] == t)
        per_asset.append(
            {
                "ticker": t,
                "buys_after_initial": len(buys),
                "buy_qty": sum(o["quantity"] for o in buys),
                "avg_buy_price": avg_p(buys),
                "sells": len(sells),
                "sell_qty": sum(o["quantity"] for o in sells),
                "avg_sell_price": avg_p(sells),
                "full_exits": len(exits),
                "reentries": max(0, len(entries) - 1),
                "sessions_held": sum(r["quantity"] > 0 for r in daily_rows if r["ticker"] == t),
                "final_qty": ops[-1]["quantity_after"],
                "pnl": str(attr["pnl"]),
            }
        )

    final_val = data["days"][-1]["valuation"]
    wallets_summary = {}
    for strat, v in final_val.items():
        strat_after = [o for o in operations if o["strategy"] == strat and not o["initial"]]
        wallets_summary[strat] = {
            "equity": v["equity"],
            "return_pct": str(D(v["return_pct"]).quantize(D("0.0001"))),
            "cash": v["cash"],
            "receivable": v["receivable"],
            "costs": v["costs"],
            "trades_after_initial": len(strat_after),
            "buys_after_initial": sum(o["side"] == "BUY" for o in strat_after),
            "sells": sum(o["side"] == "SELL" for o in strat_after),
            "positions": v["positions"],
        }

    def summarize_features(groups):
        out = {}
        for k, flist in groups.items():
            out[k] = {
                "count": len(flist),
                "avg_rsi": round(sum(x["rsi"] for x in flist) / len(flist), 2),
                "avg_sma50_gap": round(sum(x["sma50_gap"] for x in flist) / len(flist), 4),
                "avg_sma200_gap": round(sum(x["sma200_gap"] for x in flist) / len(flist), 4),
                "avg_bb_upper_gap": round(sum(x["bb_upper_gap"] for x in flist) / len(flist), 4),
                "avg_bb_lower_gap": round(sum(x["bb_lower_gap"] for x in flist) / len(flist), 4),
            }
        return out

    total_asset_days = len(completed_days) * len(tickers)
    return {
        "identity": expected_identity,
        "sessions": len(sessions),
        "completed_days": len(completed_days),
        "gaps": gaps,
        "daily_states_reconciled": reconciled_states,
        "wallets": wallets_summary,
        "per_asset_multiagent": per_asset,
        "episodes": episodes,
        "concentration": {
            "days_by_significant_assets_ge_2pct": dict(sorted(sig_assets_dist.items())),
            "days_with_ge_3_significant_assets": sum(c for n, c in sig_assets_dist.items() if n >= 3),
            "max_weight_pct_by_ticker": max_weight_by_ticker,
            "max_single_asset_weight_pct": max(max_weight_by_ticker.values()),
            "dust_buys_below_2000": dust_buys,
        },
        "trim_to_fund_executed": trim_to_fund_executed,
        "r7": {
            "vetoed_asset_days": len(vetoed_days),
            "vetoed_venda_technical": sum(1 for x in vetoed_days if x["technical_signal"] == "VENDA"),
            "r7_sells_executed_under_veto": r7_executed,
        },
        "committee": {
            "total_asset_days": total_asset_days,
            "vote_splits": dict(vote_splits),
            "unanimity_5_0_pct": round(100 * vote_splits["5-0"] / total_asset_days, 2) if total_asset_days else 0.0,
            "lens_disagreements_trend_vs_reversion": lens_disagreements,
            "features_by_winning_signal": summarize_features(feature_by_signal),
            "features_by_executed_side": summarize_features(feature_by_exec_side),
        },
        "manager_adjustments": dict(adjustments_counts),
        "last_session": sessions[-1],
        "day_valuations": {d["day"]: d["valuation"] for d in data["days"]},
        "budget": data["budget"],
        "budget_audit": data["budget_audit"],
        "manifest": manifest,
        "operations_multiagent": multi_after,
    }


def run_comparison(v1_dir=V1_EXPORTS, v2_dir=V2_EXPORTS, out_dir=OUT_DIR, *, allow_partial=False):
    v1_hashes = verify_v1_preserved(v1_dir)
    if not (v2_dir / "explorer.json").exists() and (V2_CACHE_EXPORTS / "explorer.json").exists():
        v2_dir = V2_CACHE_EXPORTS

    v1 = analyze_campaign(v1_dir, "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V1")
    v2 = analyze_campaign(v2_dir, "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2", allow_partial=allow_partial)

    # Verify all 5 deterministic reference strategies in v2 remain identical to v1 at v2's last session.
    v1_ref_val = v1["day_valuations"][v2["last_session"]]
    reference_parity = {}
    for strat in REFERENCE_STRATEGIES:
        same = (
            v1_ref_val[strat]["equity"] == v2["wallets"][strat]["equity"]
            and v1_ref_val[strat]["cash"] == v2["wallets"][strat]["cash"]
            and v1_ref_val[strat]["receivable"] == v2["wallets"][strat]["receivable"]
            and v1_ref_val[strat]["costs"] == v2["wallets"][strat]["costs"]
            and v1_ref_val[strat]["positions"] == v2["wallets"][strat]["positions"]
        )
        assert same, f"reference mismatch for {strat} on {v2['last_session']}: v1={v1_ref_val[strat]} vs v2={v2['wallets'][strat]}"
        reference_parity[strat] = True

    # v2 invariants
    assert len(v2["concentration"]["dust_buys_below_2000"]) == 0, (
        f"dust buys found in v2: {v2['concentration']['dust_buys_below_2000']}"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "comparacao_carteiras.csv",
        [
            {"version": "v1", "strategy": s, **vals}
            for s, vals in v1["wallets"].items()
        ]
        + [
            {"version": "v2", "strategy": s, **vals}
            for s, vals in v2["wallets"].items()
        ],
    )
    write_csv(
        out_dir / "atribuicao_v1_vs_v2.csv",
        [
            {
                "ticker": a1["ticker"],
                "v1_pnl": a1["pnl"],
                "v2_pnl": a2["pnl"],
                "delta_pnl": str(D(a2["pnl"]) - D(a1["pnl"])),
                "v1_avg_buy": a1["avg_buy_price"],
                "v2_avg_buy": a2["avg_buy_price"],
                "v1_avg_sell": a1["avg_sell_price"],
                "v2_avg_sell": a2["avg_sell_price"],
                "v1_sessions_held": a1["sessions_held"],
                "v2_sessions_held": a2["sessions_held"],
                "v1_final_qty": a1["final_qty"],
                "v2_final_qty": a2["final_qty"],
            }
            for a1, a2 in zip(v1["per_asset_multiagent"], v2["per_asset_multiagent"])
        ],
    )
    write_csv(out_dir / "episodios_v2.csv", v2["episodes"])
    write_csv(out_dir / "operacoes_v2.csv", v2["operations_multiagent"])
    write_csv(out_dir / "r7_veto_sells_v2.csv", v2["r7"]["r7_sells_executed_under_veto"])
    write_csv(out_dir / "trim_to_fund_v2.csv", v2["trim_to_fund_executed"])

    summary = {
        "status": "PASS",
        "v1_preserved_hashes": v1_hashes,
        "reference_parity_v1_v2": reference_parity,
        "v1": {k: v for k, v in v1.items() if k not in ("operations_multiagent", "day_valuations")},
        "v2": {k: v for k, v in v2.items() if k not in ("operations_multiagent", "day_valuations")},
        "deltas_multiagent_v2_minus_v1": {
            "equity_brl": str(D(v2["wallets"]["MULTIAGENT"]["equity"]) - D(v1["wallets"]["MULTIAGENT"]["equity"])),
            "return_pp": str(D(v2["wallets"]["MULTIAGENT"]["return_pct"]) - D(v1["wallets"]["MULTIAGENT"]["return_pct"])),
            "vs_buy_hold_v2_brl": str(D(v2["wallets"]["MULTIAGENT"]["equity"]) - D(v2["wallets"]["BUY_HOLD"]["equity"])),
            "vs_bollinger_v2_brl": str(D(v2["wallets"]["MULTIAGENT"]["equity"]) - D(v2["wallets"]["BOLLINGER_20_2"]["equity"])),
            "unanimity_5_0_pp": round(v2["committee"]["unanimity_5_0_pct"] - v1["committee"]["unanimity_5_0_pct"], 2),
        },
    }
    (out_dir / "comparacao_v1_v2.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1", type=Path, default=V1_EXPORTS)
    parser.add_argument("--v2", type=Path, default=V2_EXPORTS)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_comparison(args.v1, args.v2, args.out, allow_partial=args.allow_partial), indent=2, ensure_ascii=False))
