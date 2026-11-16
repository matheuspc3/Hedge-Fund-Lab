"""Reconcile REPLAY-03 (v3) exports, verify v1 & v2 preservation, and compare v1 vs v2 vs v3."""

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
V3_EXPORTS = PROJECT / "data/replays/april-november-2026-flash-v3/exports"
V3_CACHE_EXPORTS = PROJECT / "data/cache/continuous-replay/april-november-2026-flash-v3/exports"
OUT_DIR = PROJECT / "output/auditoria-replay-v3"

V1_EXPECTED_HASHES = {
    "explorer.json": "88c3a0e1f45ffa15d9033a74714821a863c14033c182ce54d3915fa087e5f6e4",
    "calls.json": "b5ef95859304e40d21ef41232ebf2f9187f9c56eede4d91cfff30d85fdaba6fb",
}
V2_EXPECTED_HASHES = {
    "explorer.json": "4f517224253e8e34d2b47dc2cf0f0c61f25df5664af0137aa5973aa71233d932",
    "calls.json": "f5c013450ddb64fedefc7067a19d92ed0f8071dd0d1fcc46a4cb1363f3649561",
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


def verify_preserved(export_dir, expected_hashes, label):
    export_dir = Path(export_dir)
    hashes = {}
    for name, expected in expected_hashes.items():
        path = export_dir / name
        assert path.exists(), f"missing {label} export: {path}"
        actual = sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f"{label} {name} hash changed: {actual} != {expected}"
        hashes[name] = actual
    return hashes


def verify_v1_preserved(v1_dir=V1_EXPORTS):
    return verify_preserved(v1_dir, V1_EXPECTED_HASHES, "v1")


def verify_v2_preserved(v2_dir=V2_EXPORTS):
    return verify_preserved(v2_dir, V2_EXPECTED_HASHES, "v2")


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
    if not allow_partial:
        assert data["completed"] is True
    assert data["budget_audit"]["status"] == "PASS"
    assert D(data["budget"]["exposure_usd"]) <= D("34.78")

    all_days = data["days"]
    active_days = [d for d in all_days if d.get("status") != "REFERENCES_ONLY"] if allow_partial else all_days
    assert len(active_days) >= 1, f"no executed days found in {export_dir}"

    sessions = [d["day"] for d in active_days]
    all_sessions = [d["day"] for d in all_days]
    tickers = sorted(data["market"])
    assert len(sessions) == len(set(sessions)) >= 1
    if not allow_partial:
        assert len(sessions) == 153
        assert data["campaign"]["sessions"] == sessions
    else:
        assert data["campaign"]["sessions"][: len(all_sessions)] == all_sessions
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

    # Reconstruct daily wallet states from events for all active sessions x 6 strategies.
    operations, attribution, daily_rows = [], [], []
    reconciled_states = 0
    for strategy, events in data["events"].items():
        assert len({e["id"] for e in events}) == len(events)
        initial = next(e["request"]["capital"] for e in events if e["request"]["kind"] == "CREATE")
        cash, costs, quantity = D(initial), D(0), dict.fromkeys(tickers, 0)
        avg_cost = dict.fromkeys(tickers, None)
        by_day, flows, payments = defaultdict(list), defaultdict(D), defaultdict(D)
        for event in events:
            req = event["request"]
            if req["kind"] == "TRADE":
                by_day[req["trade"]["economic_date"]].append(event)
            elif req["kind"] == "DIVIDEND":
                by_day[req["dividend"]["payment_date"]].append(event)

        last_state = None
        for day in active_days:
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
                price_d = D(tr["price"])
                gross, cost = money(price_d * n), D(tr["costs"])
                avg_cost_before = avg_cost[t]
                if side == "BUY":
                    total_cost_basis = (avg_cost[t] * before if avg_cost[t] is not None and before > 0 else D(0)) + gross + cost
                    quantity[t] += n
                    avg_cost[t] = (total_cost_basis / quantity[t]).quantize(D("0.0001"))
                else:
                    quantity[t] -= n
                    if quantity[t] == 0:
                        avg_cost[t] = None
                assert quantity[t] >= 0
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
                        "avg_cost_before": str(avg_cost_before.quantize(D("0.01"))) if avg_cost_before is not None else "",
                        "event_id": event["id"],
                    }
                )
            state = day["valuation"][strategy]
            last_state = state
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
                            "cash_pct": cash / D(state["equity"]) * 100,
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
        assert sum(r["pnl"] for r in attribution if r["strategy"] == strategy) == D(last_state["equity"]) - D(initial)

    assert reconciled_states == len(sessions) * len(data["events"])

    # Cross-check CSV exports against explorer.json / events / calls.json.
    csv_rows = {
        name: list(csv.DictReader((export_dir / name).open("r", encoding="utf-8-sig")))
        for name in ("daily.csv", "operations.csv", "calls.csv")
    }
    expected_csv_states = sum(len(d["valuation"]) for d in all_days)
    assert len(csv_rows["daily.csv"]) == expected_csv_states
    assert len(csv_rows["operations.csv"]) == len(operations)
    assert len(csv_rows["calls.csv"]) == len(calls)
    day_lookup = {d["day"]: d for d in all_days}
    for row in csv_rows["daily.csv"]:
        state = day_lookup[row["session"]]["valuation"][row["strategy"]]
        assert json.loads(row["positions"]) == state["positions"] and row["equity"] == state["equity"]
    assert Counter(r["event_id"] for r in csv_rows["operations.csv"]) == Counter(o["event_id"] for o in operations)

    # Diagnostics for MULTIAGENT committee, guards, manager, concentration, R7, trims, dip-rebalance.
    multi_ops = [o for o in operations if o["strategy"] == "MULTIAGENT"]
    multi_after = [o for o in multi_ops if not o["initial"]]
    vote_splits = Counter()
    committee_guard_counts = Counter()
    committee_guard_events = []
    feature_by_signal = defaultdict(list)
    feature_by_technical_signal = defaultdict(list)
    feature_by_exec_side = defaultdict(list)
    lens_disagreements = 0
    vetoed_days = []
    r7_executed = []
    trim_to_fund_executed = []
    trim_on_strength_executed = []
    dip_rebalance_buys_executed = []
    dust_buys = []
    adjustments_counts = Counter()
    full_exits_non_r7 = 0

    completed_days = [d for d in active_days if d.get("status") == "COMPLETED"]
    gaps = [d["day"] for d in active_days if d.get("status") != "COMPLETED"]
    auction_cash_adjustments = []

    for day_obj in completed_days:
        day = day_obj["day"]
        mgr = data["managers"][day]
        actions = mgr["rows"]
        for adj in mgr.get("adjustments", []):
            adjustments_counts[adj.get("reason", "UNKNOWN")] += 1
        executed_day = {o["ticker"]: o for o in multi_after if o["date"] == day}
        exec_adjs = {
            adj["ticker"]: adj
            for adj in ((day_obj.get("execution_source") or {}).get("adjustments") or [])
        }
        for r in actions:
            t_act = r["ticker"]
            prop_qty = int(r["quantity"])
            if r["side"] == "HOLD":
                assert t_act not in executed_day, (day, t_act, r, executed_day.get(t_act))
            elif t_act in exec_adjs:
                adj = exec_adjs[t_act]
                assert int(adj["ordered"]) == prop_qty, (day, t_act, adj, r)
                exec_qty = executed_day[t_act]["quantity"] if t_act in executed_day else 0
                assert int(adj["executed"]) == exec_qty, (day, t_act, adj, exec_qty)
                if exec_qty > 0:
                    assert executed_day[t_act]["side"] == r["side"]
                auction_cash_adjustments.append({"date": day, **adj})
            else:
                assert t_act in executed_day, (day, t_act, r)
                assert executed_day[t_act]["side"] == r["side"]
                assert executed_day[t_act]["quantity"] == prop_qty, (day, t_act, r, executed_day[t_act])
        has_surviving_compra_buy = any(
            r["side"] == "BUY"
            and data["analyses"][day][r["ticker"]]["recommendation"] == "COMPRA"
            and data["analyses"][day][r["ticker"]]["risk"]["verdict"] == "APROVADO"
            for r in actions
        )

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

            guard = a.get("committee_guard")
            if guard:
                committee_guard_counts[guard] += 1
                committee_guard_events.append(
                    {
                        "date": day,
                        "ticker": t,
                        "guard": guard,
                        "winning_signal": a["consensus"]["winning_signal"],
                        "technical_signal": a["technical_signal"]["signal"],
                        "rsi": a["features"]["rsi"],
                        "sma50_gap": a["features"]["sma50_gap"],
                        "sma200_gap": a["features"]["sma200_gap"],
                        "bb_upper_gap": a["features"]["bb_upper_gap"],
                        "bb_lower_gap": a["features"]["bb_lower_gap"],
                    }
                )

            win = a["consensus"]["winning_signal"] or "MANTER"
            feature_by_signal[win].append(a["features"])
            feature_by_technical_signal[a["technical_signal"]["signal"]].append(a["features"])

            votes_map = {v["analyst_id"]: v["signal"]["signal"] for v in a["votes"]}
            if len(set(votes_map.values())) > 1:
                lens_disagreements += 1

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
                if op["full_exit"] and a["risk"]["verdict"] != "VETADO":
                    full_exits_non_r7 += 1

                if op["side"] == "BUY":
                    ref_gross = money(D(row["quantity"]) * D(row["price"]))
                    if ref_gross < D("2000.00") or (
                        op["gross"] < D("2000.00") and op["quantity"] == int(row["quantity"])
                    ):
                        dust_buys.append(
                            {
                                "date": day,
                                "ticker": t,
                                "quantity": op["quantity"],
                                "ref_gross": str(ref_gross),
                                "exec_gross": str(op["gross"]),
                            }
                        )
                    if a["recommendation"] == "MANTER":
                        dip_rebalance_buys_executed.append(
                            {
                                "date": day,
                                "ticker": t,
                                "recommendation": a["recommendation"],
                                "quantity": op["quantity"],
                                "weight_before": row.get("weight_before"),
                                "weight_after": row.get("weight_after"),
                                "gross": str(op["gross"]),
                                "rsi": a["features"]["rsi"],
                                "sma50_gap": a["features"]["sma50_gap"],
                                "bb_lower_gap": a["features"]["bb_lower_gap"],
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
                    reasoning = (row.get("reasoning") or "").upper()
                    w_before = D(str(row.get("weight_before") or "0"))
                    w_after = D(str(row.get("weight_after") or "0"))
                    strength_cond = (
                        a["features"]["rsi"] >= 63 or a["features"]["bb_upper_gap"] >= -0.02
                    ) and w_before > D("0.14")
                    is_strength = (
                        "STRENGTH" in reasoning
                        or (
                            "TRIM_TO_FUND" not in reasoning
                            and (
                                w_before <= D("0.25")
                                or w_after < D("0.15")
                                or (not has_surviving_compra_buy and w_before <= D("0.30"))
                                or strength_cond
                            )
                        )
                    )
                    entry_rec = {
                        "date": day,
                        "ticker": t,
                        "recommendation": a["recommendation"],
                        "quantity": op["quantity"],
                        "weight_before": row.get("weight_before"),
                        "weight_after": row.get("weight_after"),
                        "gross": str(op["gross"]),
                        "rsi": a["features"]["rsi"],
                        "bb_upper_gap": a["features"]["bb_upper_gap"],
                    }
                    if is_strength:
                        trim_on_strength_executed.append(entry_rec)
                    else:
                        trim_to_fund_executed.append(entry_rec)

    # Concentration & cash drag metrics
    sig_assets_dist = Counter()
    for day in sessions:
        n_sig = sum(1 for r in daily_rows if r["date"] == day and r["weight_equity_pct"] >= D("2"))
        sig_assets_dist[n_sig] += 1
    max_weight_by_ticker = {
        t: round(max(float(r["weight_equity_pct"]) for r in daily_rows if r["ticker"] == t), 2)
        for t in tickers
    }
    cash_pcts = []
    for day in sessions:
        day_row = next(r for r in daily_rows if r["date"] == day)
        cash_pcts.append(float(day_row["cash_pct"]))

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

    final_val = active_days[-1]["valuation"]
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
            "full_exits": sum(1 for o in strat_after if o["full_exit"]),
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
    total_full_exits = sum(a["full_exits"] for a in per_asset)
    return {
        "identity": expected_identity,
        "sessions": len(sessions),
        "completed_days": len(completed_days),
        "gaps": gaps,
        "daily_states_reconciled": reconciled_states,
        "wallets": wallets_summary,
        "per_asset_multiagent": per_asset,
        "full_exits_total": total_full_exits,
        "full_exits_non_r7": full_exits_non_r7,
        "episodes": episodes,
        "concentration": {
            "days_by_significant_assets_ge_2pct": dict(sorted(sig_assets_dist.items())),
            "days_with_ge_3_significant_assets": sum(c for n, c in sig_assets_dist.items() if n >= 3),
            "max_weight_pct_by_ticker": max_weight_by_ticker,
            "max_single_asset_weight_pct": max(max_weight_by_ticker.values()),
            "avg_cash_pct": round(sum(cash_pcts) / len(cash_pcts), 2) if cash_pcts else 0.0,
            "end_cash_pct": round(cash_pcts[-1], 2) if cash_pcts else 0.0,
            "dust_buys_below_2000": dust_buys,
        },
        "trim_to_fund_executed": trim_to_fund_executed,
        "trim_on_strength_executed": trim_on_strength_executed,
        "dip_rebalance_buys_executed": dip_rebalance_buys_executed,
        "r7": {
            "vetoed_asset_days": len(vetoed_days),
            "vetoed_venda_technical": sum(1 for x in vetoed_days if x["technical_signal"] == "VENDA"),
            "r7_sells_executed_under_veto": r7_executed,
        },
        "committee": {
            "total_asset_days": total_asset_days,
            "vote_splits": dict(vote_splits),
            "unanimity_5_0_pct": round(100 * vote_splits["5-0"] / total_asset_days, 2) if total_asset_days else 0.0,
            "lens_disagreements": lens_disagreements,
            "committee_guards": dict(committee_guard_counts),
            "committee_guard_events": committee_guard_events,
            "features_by_winning_signal": summarize_features(feature_by_signal),
            "features_by_technical_signal": summarize_features(feature_by_technical_signal),
            "features_by_executed_side": summarize_features(feature_by_exec_side),
        },
        "manager_adjustments": dict(adjustments_counts),
        "auction_cash_adjustments": auction_cash_adjustments,
        "last_session": sessions[-1],
        "day_valuations": {d["day"]: d["valuation"] for d in active_days},
        "budget": data["budget"],
        "budget_audit": data["budget_audit"],
        "manifest": manifest,
        "operations_multiagent": multi_after,
    }


def _assert_reference_parity(ref_val, target_wallets, last_session, label):
    parity = {}
    for strat in REFERENCE_STRATEGIES:
        same = (
            ref_val[strat]["equity"] == target_wallets[strat]["equity"]
            and ref_val[strat]["cash"] == target_wallets[strat]["cash"]
            and ref_val[strat]["receivable"] == target_wallets[strat]["receivable"]
            and ref_val[strat]["costs"] == target_wallets[strat]["costs"]
            and ref_val[strat]["positions"] == target_wallets[strat]["positions"]
        )
        assert same, f"reference mismatch for {strat} ({label}) on {last_session}: ref={ref_val[strat]} vs target={target_wallets[strat]}"
        parity[strat] = True
    return parity


def run_comparison(
    v1_dir=V1_EXPORTS,
    v2_dir=V2_EXPORTS,
    v3_dir=V3_EXPORTS,
    out_dir=OUT_DIR,
    *,
    allow_partial=False,
):
    v1_dir = Path(v1_dir)
    v2_dir = Path(v2_dir)
    v3_dir = Path(v3_dir)
    out_dir = Path(out_dir)

    v1_hashes = verify_v1_preserved(v1_dir)
    if not (v2_dir / "explorer.json").exists() and (V2_CACHE_EXPORTS / "explorer.json").exists():
        v2_dir = V2_CACHE_EXPORTS
    v2_hashes = verify_v2_preserved(v2_dir)

    if not (v3_dir / "explorer.json").exists() and (V3_CACHE_EXPORTS / "explorer.json").exists():
        v3_dir = V3_CACHE_EXPORTS

    v1 = analyze_campaign(v1_dir, "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V1")
    v2 = analyze_campaign(v2_dir, "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V2")
    v3 = analyze_campaign(v3_dir, "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V3", allow_partial=allow_partial)

    # Verify all 5 deterministic reference strategies in v2 and v3 match v1 at their last session.
    ref_parity_v1_v2 = _assert_reference_parity(
        v1["day_valuations"][v2["last_session"]], v2["wallets"], v2["last_session"], "v1 vs v2"
    )
    ref_parity_v1_v3 = _assert_reference_parity(
        v1["day_valuations"][v3["last_session"]], v3["wallets"], v3["last_session"], "v1 vs v3"
    )

    # v3 invariants
    assert len(v3["concentration"]["dust_buys_below_2000"]) == 0, (
        f"dust buys found in v3: {v3['concentration']['dust_buys_below_2000']}"
    )
    assert v3["full_exits_non_r7"] == 0, (
        f"non-R7 full exits found in v3 (Core Floor violated): {v3['full_exits_non_r7']}"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "comparacao_carteiras.csv",
        [
            {"version": ver, "strategy": s, **vals}
            for ver, payload in (("v1", v1), ("v2", v2), ("v3", v3))
            for s, vals in payload["wallets"].items()
        ],
    )
    write_csv(
        out_dir / "atribuicao_v1_v2_v3.csv",
        [
            {
                "ticker": a1["ticker"],
                "v1_pnl": a1["pnl"],
                "v2_pnl": a2["pnl"],
                "v3_pnl": a3["pnl"],
                "delta_v3_v1_pnl": str(D(a3["pnl"]) - D(a1["pnl"])),
                "delta_v3_v2_pnl": str(D(a3["pnl"]) - D(a2["pnl"])),
                "v1_avg_buy": a1["avg_buy_price"],
                "v2_avg_buy": a2["avg_buy_price"],
                "v3_avg_buy": a3["avg_buy_price"],
                "v1_avg_sell": a1["avg_sell_price"],
                "v2_avg_sell": a2["avg_sell_price"],
                "v3_avg_sell": a3["avg_sell_price"],
                "v1_full_exits": a1["full_exits"],
                "v2_full_exits": a2["full_exits"],
                "v3_full_exits": a3["full_exits"],
                "v1_sessions_held": a1["sessions_held"],
                "v2_sessions_held": a2["sessions_held"],
                "v3_sessions_held": a3["sessions_held"],
                "v1_final_qty": a1["final_qty"],
                "v2_final_qty": a2["final_qty"],
                "v3_final_qty": a3["final_qty"],
            }
            for a1, a2, a3 in zip(
                v1["per_asset_multiagent"], v2["per_asset_multiagent"], v3["per_asset_multiagent"]
            )
        ],
    )
    write_csv(out_dir / "episodios_v3.csv", v3["episodes"])
    write_csv(out_dir / "operacoes_v3.csv", v3["operations_multiagent"])
    write_csv(out_dir / "r7_veto_sells_v3.csv", v3["r7"]["r7_sells_executed_under_veto"])
    write_csv(out_dir / "trim_to_fund_v3.csv", v3["trim_to_fund_executed"])
    write_csv(out_dir / "trim_on_strength_v3.csv", v3["trim_on_strength_executed"])
    write_csv(out_dir / "dip_rebalance_buys_v3.csv", v3["dip_rebalance_buys_executed"])
    write_csv(out_dir / "committee_guards_v3.csv", v3["committee"]["committee_guard_events"])

    omit = ("operations_multiagent", "day_valuations")
    summary = {
        "status": "PASS",
        "v1_preserved_hashes": v1_hashes,
        "v2_preserved_hashes": v2_hashes,
        "reference_parity_v1_v2": ref_parity_v1_v2,
        "reference_parity_v1_v3": ref_parity_v1_v3,
        "v1": {k: v for k, v in v1.items() if k not in omit},
        "v2": {k: v for k, v in v2.items() if k not in omit},
        "v3": {k: v for k, v in v3.items() if k not in omit},
        "deltas_multiagent_v3_minus_v1": {
            "equity_brl": str(D(v3["wallets"]["MULTIAGENT"]["equity"]) - D(v1["wallets"]["MULTIAGENT"]["equity"])),
            "return_pp": str(D(v3["wallets"]["MULTIAGENT"]["return_pct"]) - D(v1["wallets"]["MULTIAGENT"]["return_pct"])),
            "full_exits_delta": v3["full_exits_total"] - v1["full_exits_total"],
            "trades_delta": v3["wallets"]["MULTIAGENT"]["trades_after_initial"] - v1["wallets"]["MULTIAGENT"]["trades_after_initial"],
            "unanimity_5_0_pp": round(v3["committee"]["unanimity_5_0_pct"] - v1["committee"]["unanimity_5_0_pct"], 2),
        },
        "deltas_multiagent_v3_minus_v2": {
            "equity_brl": str(D(v3["wallets"]["MULTIAGENT"]["equity"]) - D(v2["wallets"]["MULTIAGENT"]["equity"])),
            "return_pp": str(D(v3["wallets"]["MULTIAGENT"]["return_pct"]) - D(v2["wallets"]["MULTIAGENT"]["return_pct"])),
            "vs_buy_hold_v3_brl": str(D(v3["wallets"]["MULTIAGENT"]["equity"]) - D(v3["wallets"]["BUY_HOLD"]["equity"])),
            "vs_bollinger_v3_brl": str(D(v3["wallets"]["MULTIAGENT"]["equity"]) - D(v3["wallets"]["BOLLINGER_20_2"]["equity"])),
            "full_exits_delta": v3["full_exits_total"] - v2["full_exits_total"],
            "trades_delta": v3["wallets"]["MULTIAGENT"]["trades_after_initial"] - v2["wallets"]["MULTIAGENT"]["trades_after_initial"],
            "unanimity_5_0_pp": round(v3["committee"]["unanimity_5_0_pct"] - v2["committee"]["unanimity_5_0_pct"], 2),
        },
    }
    (out_dir / "comparacao_v1_v2_v3.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1", type=Path, default=V1_EXPORTS)
    parser.add_argument("--v2", type=Path, default=V2_EXPORTS)
    parser.add_argument("--v3", type=Path, default=V3_EXPORTS)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run_comparison(
                args.v1,
                args.v2,
                args.v3,
                args.out,
                allow_partial=args.allow_partial,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
