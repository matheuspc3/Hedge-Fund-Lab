"""DP-35/36: one continuous, isolated, resumable six-wallet exploratory campaign.

Frozen strategy sources are reused. Campaign adapters repair dividend component
identity and SLSQP objective scale, with unchanged financial definitions.
"""
import argparse
import asyncio
import csv
import importlib.util
import json
import os
import sys
import uuid
import math
from contextlib import closing
from datetime import datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "data/cache/continuous-replay/april-november-2026-flash"
RUN_ROOT = ROOT / "qualified-v2"
SOURCE = Path("C:/Users/LUCAS/Meu Canto/TCC/Hedge-Fund-Lab")
sys.path[:0] = [str(PROJECT), str(PROJECT / "scripts"), str(PROJECT / "dashboard")]

# Keep the common core bound to this checkout before loading the current app book.
import multiasset_portfolio as b
import multiasset_radar as radar


def snapshot():
    for name in ("dashboard/manual_portfolio_api.py", "dashboard/dividends_api.py", "dashboard/rule_portfolios.py", "src/strategies/sma_cross.py", "src/strategies/bollinger_bands.py", "src/backtesting/portfolio.py"):
        out = ROOT / "engine" / name
        if not out.exists():
            radar.write(out, (SOURCE / name).read_bytes(), immutable=True)


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "engine/dashboard" / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


snapshot()
manual = module("manual_portfolio_api")
import market_base_api as market
dividends = module("dividends_api")
import replay_multiasset as r
import wallet_manager_api as wm
import auction_orders as orders
import radar_analysis_api as analysis
from pilot_paper import bind
from continuous_replay_runtime import Budget, BudgetStop, RecoveryStop, Transport, recording_retry
from continuous_replay_dividends import install as install_dividends
from src.experiments.h2_evaluation_production import JournalIntegrityError
rules = module("rule_portfolios")
from src.backtesting.portfolio import EqualWeightPortfolio, MinVariancePortfolio
import src.backtesting.portfolio as portfolio
import pandas as pd

PORTFOLIOS = {"EQUAL_WEIGHT_63": EqualWeightPortfolio(), "MIN_VARIANCE_252_63": MinVariancePortfolio(window=252, allow_short=False)}
manual.RULE_STRATEGIES.update({"EQUAL_WEIGHT_63": "Equal Weight 63", "MIN_VARIANCE_252_63": "Mínima Variância 252/63"})
STRATEGIES = ("MULTIAGENT", "BUY_HOLD", *rules.RULES, *PORTFOLIOS)
install_dividends(dividends, manual, RecoveryStop)

IDENTITY = "HFL-CONTINUOUS-EXPLORATORY-REPLAY-V1"


class RadarClient(Transport, radar.RadarGeminiClient):
    pass


class ManagerClient(Transport, wm.WalletClient):
    propose = bind(wm.WalletClient.propose, RecordingLLMClient=recording_retry)


def sources():
    paths = [Path(__file__), PROJECT / "scripts/continuous_replay_runtime.py", PROJECT / "scripts/continuous_replay_dividends.py", Path(r.__file__), Path(wm.__file__), Path(orders.__file__), Path(portfolio.__file__), *sorted((ROOT / "engine").rglob("*.py"))]
    return {**radar.frozen_sources(), **{str(p.relative_to(PROJECT)).replace("\\", "/"): b.sha_file(p) for p in paths}, "manager_contract": wm.contracts()}


def campaign_path(root):
    revisions = sorted(root.glob("campaign-v*.json"), key=lambda p: int(p.stem.split("-v")[-1]))
    return revisions[-1] if revisions else root / "campaign.json"


def budget_path(root):
    return ROOT / "budget.sqlite" if root.resolve() == RUN_ROOT.resolve() else root / "budget.sqlite"


def numerical_minimize(objective, initial, *args, **kwargs):
    # Daily covariance is small relative to SLSQP's absolute ftol. A positive
    # scalar preserves the minimizer and constraints; frozen legacy code stays intact.
    scale = max(float(objective(v)) for v in portfolio.np.eye(len(initial))) or 1.0
    result = portfolio.minimize(lambda w: objective(w) / scale, initial, *args, **kwargs)
    result["objective_scale"] = scale
    result["unscaled_fun"] = float(objective(result.x))
    return result


def prepare(root, *, offline=False, count=None):
    m = r.checked(ROOT / "inputs/manifest.json")
    assets = r.checked(ROOT / "inputs/market.json")["assets"]
    if b.sha_file(ROOT / "inputs/market.json") != m["market_sha256"]:
        raise RecoveryStop("frozen_market_changed")
    # The actual strategy imports must match the current app sources copied above.
    for name in ("sma_cross.py", "bollinger_bands.py"):
        if b.sha_file(PROJECT / "src/strategies" / name) != b.sha_file(ROOT / "engine/src/strategies" / name):
            raise RecoveryStop("current_rule_strategy_source_differs")
    days = m["sessions"][:count]
    if b.sha_file(portfolio.__file__) != b.sha_file(ROOT / "engine/src/backtesting/portfolio.py"):
        raise RecoveryStop("current_portfolio_strategy_source_differs")
    manifest = {"identity": IDENTITY, "mode": "OFFLINE_TEST_ONLY" if offline else "REAL_INFERENCE", "data_manifest_sha256": b.sha_file(ROOT / "inputs/manifest.json"), "sessions": days, "strategies": list(STRATEGIES), "source_hashes": sources(), "rule_policy": rules.policy(r.RATE), "portfolio_policy": {"rebalance_sessions": 63, "minimum_variance_returns": 252, "allow_short": False, "optimizer": "SLSQP defaults with objective divided by max diagonal covariance (positive scalar), same minimizer and constraints; scale/unscaled variance/result recorded", "initial": "Shared DP20 integer basket", "first_signal": "First campaign close, then every 63 sessions", "execution": "Next B3 RAW open; shared auction planner scales buys proportionally to available cash", "dividends": "Cash, excluded from reinvestible capital"}, "aggregate_budget_path": str(budget_path(root).resolve()), "optimizer_diagnostic_sha256": b.sha_file(ROOT / "optimizer_diagnostic.json"), "max_usd": "34.78", "max_attempts_per_logical_call": 2, "retry_delay_seconds": "1, or provider Retry-After up to 30; larger waits stop", "billing": "known provider usage + full unknown/in-flight reservations; never reset", "unknown_reservation_analyst_usd": "0.110592", "unknown_reservation_manager_usd": "0.159744", "authorization": "Lucas authorized this continuous April-to-November six-wallet campaign, operational/numerical/accounting repairs, and references before paid inference on 2026-11-13", "classification": "EXPLORATORY_RETROSPECTIVE_NOT_POINT_IN_TIME", "limitations": [*r.LIMITATIONS, "Six independent R$100000 books. References first signal uses the first campaign close; AI first pre-open decision uses the preceding close.", "Gemini 3.8 Flash declared cutoff March 2026 has no exact training-end guarantee; model alias and reconstructed adjustments may contain later knowledge."]}
    if campaign_path(root).exists():
        old = r.checked(campaign_path(root))
        if {k: v for k, v in old.items() if k != "sha256"} != manifest:
            raise RecoveryStop("campaign_identity_changed")
    else:
        r.save(campaign_path(root), manifest)
    manual.ROOT = root / "book"
    market.ROOT = ROOT / "inputs/market"
    # Every official open is read from the same frozen bundle as the marks.
    orders.session_rows = lambda day: {t: next(x for x in assets[t]["rows"] if x["date"] == day) for t in m["universe"]}
    return m, assets, days


def initialize(root, m, assets):
    """All four initial baskets commit together; no partial initial book on crash."""
    first, ref = m["sessions"][0], m["references"][m["sessions"][0]]
    with closing(manual.connect(write=True)) as conn, conn:
        existing = manual.catalog(conn)
        if existing:
            if len(existing) != 6 or {w["strategy"] for w in existing} != set(STRATEGIES):
                raise RecoveryStop("initial_books_incomplete")
        else:
            for strategy in STRATEGIES:
                wallet = "manual-" + uuid.uuid4().hex
                req = manual.request({"kind": "CREATE", "name": IDENTITY + " " + strategy, "nature": "SIMULATION", "capital": r.CAPITAL, "start_date": first, "strategy": strategy, "comparison_group": root.name, "initialization_note": "HYPOTHETICAL_INITIAL_REFERENCE_ALLOCATION; reference " + ref + "; no market fill; dividends in cash; subsequent costs 0.03%"})
                source = {"kind": "CONTINUOUS_REPLAY_INITIALIZATION", "reference": ref}
                if strategy in rules.RULES:
                    source["policy"] = rules.policy(r.RATE)
                requests = [req]
                for t in m["universe"]:
                    price = b.dec(str(next(v for v in assets[t]["rows"] if v["date"] == ref)["close"]))
                    requests.append(manual.request({"kind": "TRADE", "wallet": wallet, "trade": {"ticker": t, "side": "BUY", "quantity": str(int(b.dec(r.CAPITAL) / 5 / price)), "price": str(price), "costs": "0.00", "economic_date": first}}))
                previous = None
                for i, req in enumerate(requests):
                    event = manual.append(conn, req, f"initial-{strategy}-{i}", manual.canonical(req), wallet, previous, source)
                    previous = event["sha256"]
                manual.replay(manual.events(conn, wallet))
    if not (root / "initialization.json").exists():
        r.save(root / "initialization.json", {"reference": ref, "wallets": r.wallets()})


def advance_portfolio(wallet_id, strategy, reference, day, m, datasets):
    if reference < m["sessions"][0]:
        return
    with closing(manual.connect(write=True)) as conn, conn:
        history = manual.events(conn, wallet_id)
        if any(e["request"]["kind"] == "RULE_EXECUTION" and e["source"]["execution_session"] == day for e in history):
            return
        wallet = manual.replay(history)
        rebalance = m["sessions"].index(reference) % 63 == 0
        source = {"strategy": strategy, "decision_session": reference, "execution_session": day, "rebalance": rebalance, "classification": "HISTORICAL_RECONSTRUCTION", "weights": None, "optimizer": None, "inputs": None}
        requests = []
        if rebalance:
            past = {t: pd.DataFrame({"fechamento": [x["adjusted_close"] for x in v["rows"] if x["date"] <= reference]}, index=pd.to_datetime([x["date"] for x in v["rows"] if x["date"] <= reference])).iloc[-253:] for t, v in datasets.items()}
            source["inputs"] = {t: [[str(d.date()), float(v)] for d, v in f["fechamento"].items()] for t, f in past.items()}
            source["factor_sources"] = {t: v["factor_source"] for t, v in datasets.items()}
            captured = []
            def minimize(*args, **kwargs):
                result = numerical_minimize(*args, **kwargs)
                captured.append({"success": bool(result.success), "status": int(result.status), "message": str(result.message), "iterations": int(result.nit), "fun": float(result.fun), "unscaled_variance": result.unscaled_fun, "objective_scale": result.objective_scale, "x": [float(v) for v in result.x]})
                return result
            strategy_object = PORTFOLIOS[strategy]
            get_weights = bind(type(strategy_object).get_weights, minimize=minimize)
            weights = get_weights(strategy_object, past, pd.Timestamp(reference))
            if set(weights) != set(m["universe"]) or any(not math.isfinite(x) or x < 0 for x in weights.values()) or abs(sum(weights.values()) - 1) > 1e-8:
                raise RecoveryStop("portfolio_invalid_weights")
            source.update(weights=weights, optimizer=captured, fallback=("EQUAL_WEIGHT_OPTIMIZER_FAILURE" if captured and not captured[0]["success"] else "EQUAL_WEIGHT_INSUFFICIENT_HISTORY" if strategy.startswith("MIN_") and not captured else None))
            rows = orders.session_rows(day)
            held = {p["ticker"]: int(b.dec(p["quantity"])) for p in wallet["positions"]}
            cash = b.dec(wallet["cash"]) - b.dec(wallet["dividends_received"])
            equity = cash + sum((b.dec(held.get(t, 0)) * b.dec(str(rows[t]["open"])) for t in m["universe"]), b.ZERO)
            targets = {t: int(equity * b.dec(str(weights[t])) / b.dec(str(rows[t]["open"]))) for t in m["universe"]}
            basket = [{"ticker": t, "side": "BUY" if targets[t] > held.get(t, 0) else "SELL", "quantity": str(abs(targets[t] - held.get(t, 0)))} for t in m["universe"] if targets[t] != held.get(t, 0)]
            order = {"basket": basket, "leg": "OPEN", "cost_rate_pct": r.RATE, "quotes": None, "run": IDENTITY, "proposal": strategy + day, "proposal_sha256": b.digest(source), "context_sha256": b.digest(source), "reference_session": reference, "target_date": day, "session": day, "approved_at": day + "T09:00:00-03:00", "wallet": {"id": wallet_id}, "decision_prices": {t: str(next(x for x in datasets[t]["rows"] if x["date"] == reference)["close"]) for t in m["universe"]}}
            requests, execution = orders.plan(order, {**wallet, "cash": str(cash)}, rows)
            source["execution"] = execution
        rules.receipt(conn, wallet_id, "RULE_DECISION", f"portfolio-decision-{strategy}-{reference}", source)
        previous = manual.events(conn, wallet_id)[-1]["sha256"]
        for i, req in enumerate(requests):
            event = manual.append(conn, manual.request(req), f"portfolio-trade-{strategy}-{day}-{i}", manual.canonical(req), wallet_id, previous, source)
            previous = event["sha256"]
        rules.receipt(conn, wallet_id, "RULE_EXECUTION", f"portfolio-execution-{strategy}-{day}", source)
        manual.replay(manual.events(conn, wallet_id))


def references(root, m, assets, days):
    datasets = {t: {**v, "rows": [{**x, "adjusted_close": x["close"] * x["factor"]} for x in v["rows"]]} for t, v in assets.items()}
    for day in days:
        path = root / "references" / (day + ".json")
        if path.exists():
            r.checked(path)
            continue
        ref, wallets = m["references"][day], r.wallets()
        status(root, "BUILDING_REFERENCES", session=day)
        for strategy in rules.RULES:
            rules.advance_wallet(wallets[strategy]["id"], [ref], datasets, day)
        for strategy in PORTFOLIOS:
            advance_portfolio(wallets[strategy]["id"], strategy, ref, day, m, datasets)
        after = [w for k, w in r.wallets().items() if k != "MULTIAGENT"]
        paid = dividends.book_received(day, wallets=after)
        if paid.get("refused"):
            raise RecoveryStop("reference_dividend_booking_refused")
        after = {k: w for k, w in r.wallets().items() if k != "MULTIAGENT"}
        r.save(path, {"day": day, "valuation": {k: r.valuation(w, orders.session_rows(day), day) for k, w in after.items()}, "revisions": {k: w["revision"] for k, w in after.items()}})
    r.save(root / "references_complete.json", {"sessions": len(days), "first": days[0], "last": days[-1], "strategies": [x for x in STRATEGIES if x != "MULTIAGENT"]})


def committee(root, day, ref, ticker, budget, offline, transport=None, crash=False):
    folder = root / "sessions" / day / "radar" / ticker
    if (folder / "result.json").exists():
        return r.checked(folder / "result.json")
    if (folder / "failure.json").exists():
        return r.checked(folder / "failure.json")
    data = radar.checked_input(ROOT / "inputs/sessions" / day / "radar", ticker, ref)
    r.save(folder / "input.json", data)
    bank = radar.CallBank(folder / "calls.sqlite", b.digest({"input": b.digest(data), "identity": IDENTITY}), IDENTITY)
    try:
        def gate():
            if radar.checked_input(ROOT / "inputs/sessions" / day / "radar", ticker, ref) != data:
                raise RecoveryStop("input_changed_before_transport")
        client = RadarClient(bank, "L01", {"model": radar.MODEL, "retry_attempts": 1, "retry_base_delay": 0}, fresh=True, gate=gate, transport=transport or (radar.fake_gemini if offline else None), synthetic=offline, budget=budget, bank_name=f"{day}/{ticker}", crash=crash)
        async def invoke():
            client.semaphore = asyncio.Semaphore(1)
            return await radar.committee(data, client)
        result = asyncio.run(invoke())
        client.assert_complete()
        result.update({"ticker": ticker, "session": ref, "status": "COMPLETED", "raw_bar": data["raw_bar"], "features": data["features"], "input_sha256": b.digest(data)})
        r.save(folder / "result.json", result)
        radar.write(folder / "provider_journal.jsonl", bank.export("L01"), immutable=True)
        return result
    except JournalIntegrityError:
        raise
    except Exception as exc:
        if client.fatal is not None:
            raise client.fatal
        # Preserve the original failure record and every sibling vote; never replace it.
        result = {"ticker": ticker, "session": ref, "status": "NO_ANALYSIS", "error": type(exc).__name__}
        r.save(folder / "failure.json", result)
        return result
    finally:
        bank.close()


def manager(folder, context, budget, offline, transport=None):
    r.save(folder / "context.json", context)
    if (folder / "proposal.json").exists():
        return r.checked(folder / "proposal.json")
    bank = wm.global_cli.CallBank(folder / "calls.sqlite", b.digest(context), IDENTITY)
    try:
        def gate():
            if r.checked(folder / "context.json")["sha256"] != b.digest(context):
                raise RecoveryStop("manager_context_changed_before_transport")
        client = ManagerClient(bank, "L01", {"model": wm.CONFIG["model"], "retry_attempts": 1, "retry_base_delay": 0}, fresh=True, gate=gate, transport=transport or (r.fake_manager if offline else None), synthetic=offline, budget=budget, bank_name=f"{context['target_date']}/manager")
        proposal = wm.compile_proposal(context, asyncio.run(client.propose(context)))
        r.save(folder / "proposal.json", proposal)
        radar.write(folder / "provider_journal.jsonl", bank.export("L01"), immutable=True)
        return proposal
    finally:
        bank.close()


def status(root, state, **kw):
    radar.write(root / "status.json", b.sealed({"state": state, "pid": os.getpid(), "at": radar.now().isoformat(), **kw}))


def execute(root=RUN_ROOT, *, offline=False, count=None, transport=None, references_only=False):
    m, assets, days = prepare(root, offline=offline, count=count)
    budget = Budget(budget_path(root))
    initialize(root, m, assets)
    with radar._exclusive_state_lock(root / "operation"):
        try:
            references(root, m, assets, days)
            if references_only:
                status(root, "REFERENCES_COMPLETE", sessions=len(days), budget=budget.summary())
                return {"references": r.checked(root / "references_complete.json"), "budget": budget.summary()}
            for day in days:
                folder = root / "sessions" / day
                if (folder / "day.json").exists():
                    r.checked(folder / "day.json")
                    continue
                ref = m["references"][day]
                status(root, "RUNNING", session=day, stage="committee", budget=budget.summary())
                if not (folder / "before.json").exists():
                    dividends.book_received(ref)
                    r.save(folder / "before.json", r.wallets())
                before = r.checked(folder / "before.json")
                outcomes = [committee(root, day, ref, t, budget, offline, transport=transport) for t in m["universe"]]
                requests, source, failure = [], None, None
                if all(o["status"] == "COMPLETED" for o in outcomes):
                    opinions = {o["ticker"]: {"recommendation": o["recommendation"], "risk_verdict": o["risk"]["verdict"], "confidence": o["technical_signal"]["confidence"], "features": o["features"], "individual_risk": o["risk"], "technical_signal": o["technical_signal"]} for o in outcomes}
                    prices = {o["ticker"]: str(o["raw_bar"]["fechamento"]) for o in outcomes}
                    context = {"wallet": analysis.wallet_snapshot(before["MULTIAGENT"]), "reference_session": ref, "target_date": day, "prices": prices, "opinions": opinions, "cost_rate_pct": r.RATE, "classification": "EXPLORATORY_HISTORICAL_REPLAY_CREATED_NOW", "snapshot": {"valuation_session": ref}}
                    status(root, "RUNNING", session=day, stage="manager", budget=budget.summary())
                    try:
                        proposal = manager(folder / "manager", context, budget, offline)
                        if not (folder / "execution.json").exists():
                            at = datetime.fromisoformat(day + "T09:00:00").replace(tzinfo=orders.SP)
                            order = {"basket": proposal["trades"], "leg": "OPEN", "cost_rate_pct": r.RATE, "quotes": None, "run": root.name, "proposal": day, "proposal_sha256": b.digest(proposal), "context_sha256": b.digest(context), "reference_session": ref, "target_date": day, "session": day, "approved_at": at.isoformat(), "wallet": {"id": before["MULTIAGENT"]["id"]}, "decision_prices": prices}
                            requests, source = orders.plan(order, before["MULTIAGENT"], orders.session_rows(day))
                            r.save(folder / "execution.json", {"requests": requests, "source": source})
                        plan = r.checked(folder / "execution.json")
                        requests, source = plan["requests"], plan["source"]
                        if requests:
                            w = before["MULTIAGENT"]
                            preview = manual.batch(w["id"], w["revision"], requests, source)
                            if not preview.get("replayed"):
                                manual.batch(w["id"], w["revision"], requests, source, confirm=True, token=preview["preview_token"])
                    except JournalIntegrityError:
                        raise
                    except Exception as exc:
                        # An invalid manager response or an unfillable basket remains a failed day.
                        failure = {"stage": "manager_or_execution", "error": type(exc).__name__}
                        r.save(folder / "failure.json", failure)
                else:
                    failure = {"stage": "committee", "tickers": [o["ticker"] for o in outcomes if o["status"] != "COMPLETED"]}
                dividends.book_received(day)
                after = r.wallets()
                reference_state = r.checked(root / "references" / (day + ".json"))
                r.save(folder / "day.json", {"identity": IDENTITY, "day": day, "reference": ref, "status": "NO_ANALYSIS" if failure else "COMPLETED", "failure": failure, "operations": requests, "execution_source": source, "valuation": {**reference_state["valuation"], "MULTIAGENT": r.valuation(after["MULTIAGENT"], orders.session_rows(day), day)}, "revisions": {**reference_state["revisions"], "MULTIAGENT": after["MULTIAGENT"]["revision"]}, "budget": budget.summary()})
                status(root, "RUNNING", session=day, stage="day_complete", budget=budget.summary())
                print(json.dumps({"day": day, "status": "NO_ANALYSIS" if failure else "COMPLETED", "operations": len(requests), "budget": budget.summary()}), flush=True)
            result = report(root)
            status(root, "COMPLETED", sessions=len(days), budget=budget.summary())
            return result
        except BaseException as exc:
            status(root, "STOPPED", session=locals().get("day"), error=type(exc).__name__, budget=budget.summary())
            raise


def report(root=RUN_ROOT):
    days = [r.checked(p) for p in sorted((root / "sessions").glob("*/day.json"))]
    rows = [{"session": d["day"], "status": d["status"], "strategy": strategy, **v, "positions": json.dumps(v["positions"], sort_keys=True)} for d in days for strategy, v in d["valuation"].items()]
    if rows:
        with (root / "daily.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    result = {"identity": IDENTITY, "sessions_completed": len(days), "complete_analysis_days": sum(d["status"] == "COMPLETED" for d in days), "gaps": [d["day"] for d in days if d["status"] != "COMPLETED"], "final": days[-1]["valuation"] if days else {}, "budget": Budget(budget_path(root)).summary()}
    radar.write(root / "summary.json", b.sealed(result))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--offline", type=Path)
    parser.add_argument("--count", type=int)
    parser.add_argument("--references-only", action="store_true")
    args = parser.parse_args()
    if args.live == bool(args.offline):
        parser.error("choose exactly one of --live or --offline dedicated-root")
    if args.live and args.count is not None:
        parser.error("live campaign period is fixed; resume uses the same root and budget")
    print(json.dumps(execute(args.offline or RUN_ROOT, offline=bool(args.offline), count=args.count, references_only=args.references_only), indent=2))
