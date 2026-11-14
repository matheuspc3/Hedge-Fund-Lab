"""New, immutable Radar analyses linked to a personal wallet; no inference here."""

import re
from datetime import timedelta

import manual_portfolio_api as manual
import market_base_api as base
import pilot_observed_data as observed
import platform_api as platform
import radar_api

radar, runs, b = platform.radar, platform.runs, platform.b
CONTEXT = "wallet-analysis.json"
IDENTITY = "HFL-WALLET-RADAR-ANALYSIS-V1"


def choices():
    at = radar.now()
    days = observed.calendar()["trading_sessions"]
    tomorrow = (at.date() + timedelta(days=1)).isoformat()
    target = next((d for d in days if d >= tomorrow), None)
    if target is None:
        raise ValueError("analysis_calendar_coverage_insufficient")
    closed, published = radar.last_closed(at), base.published()
    # B3 publishes a session's COTAHIST hours after the close: default (and latest
    # accepted) reference is the last session already in the official base (DP-27).
    # ponytail: an empty base falls back to the calendar (the sealed prepare may then
    # block with a raw KeyError); upgrade: refuse analyses until the base is loaded.
    reference = min(closed, published) if published else closed
    br = lambda d: "/".join(reversed(d.split("-")))  # noqa: E731
    return {
        "today": at.date().isoformat(),
        "target_date": target,
        "reference_session": reference,
        "last_closed_session": closed,
        "reference_note": None
        if reference == closed
        else f"Pregão de {br(closed)} encerrado, mas ainda não publicado pela B3 "
        f"(arquivo oficial sai à noite ou na manhã seguinte): dados até {br(reference)}. "
        "Após a publicação, atualize a base de mercado para usar o pregão mais recente.",
        "sessions": days,
        "calendar_basis": "DOCUMENTED_PLAN_NOT_OBSERVATION",
        "reference_cutoff": "last session in the official B3 market base (DP-27), "
        "never after 18:00 America/Sao_Paulo of the session",
    }


def wallet_snapshot(wallet):
    return {
        k: wallet.get(k)
        for k in (
            "id",
            "name",
            "nature",
            "nature_label",
            "strategy",
            "comparison_group",
            "start_date",
            "capital",
            "cash",
            "positions",
            "revision",
        )
    }


def default_tickers(wallet):
    """DP-07/34: selling a Multiagentes position never removes its buy candidate."""
    if wallet.get("strategy") == "MULTIAGENT":
        return list(radar.EXAMPLES)
    return [p["ticker"] for p in wallet["positions"]] or list(radar.EXAMPLES)


def context(entry):
    path = runs.root_of(entry) / CONTEXT
    if not path.exists():
        if entry["id"].startswith("radar-ui-"):
            raise ValueError("analysis_context_missing")
        return None
    value = b.check_seal(radar.read(path))
    if (
        value["identity"] != IDENTITY
        or value["run"] != entry["id"]
        or value["reference_session"] != entry["session"]
        or value["request"]["tickers"] != entry["universe"]
    ):
        raise ValueError("analysis_context_mismatch")
    return value


def get(query):
    if set(query) - {"run"}:
        raise ValueError("invalid_analysis_query")
    registry = runs.load()
    if "run" in query:
        value = context(runs.run(query["run"], registry))
        current = next(
            (
                w
                for w in manual.get({})["wallets"]
                if value and w["id"] == value["wallet"]["id"]
            ),
            None,
        )
        return {
            "context": value,
            "wallet_changed": bool(
                value and (current or {}).get("revision") != value["wallet"]["revision"]
            ),
        }
    return {
        **choices(),
        "wallets": [
            {**wallet_snapshot(w), "analysis_tickers": default_tickers(w)}
            for w in manual.get({})["wallets"]
            if w.get("strategy") not in manual.RULE_STRATEGIES
        ],
        "examples": list(radar.EXAMPLES),
        "selected": registry["selected"],
        "csrf_token": platform.forward_jobs.JOBS.csrf,
        "history": [
            {
                "run": entry["id"],
                "wallet": value["wallet"]["id"],
                "wallet_name": value["wallet"]["name"],
                "target_date": value["target_date"],
                "reference_session": value["reference_session"],
                "created_at": value["created_at"],
                "classification": value["classification"],
            }
            for entry in registry["runs"].values()
            if (value := context(entry)) is not None
        ],
    }


def create(payload):
    manual.fields(
        payload,
        (
            "command_id",
            "wallet",
            "wallet_revision",
            "target_date",
            "reference_session",
            "tickers",
            "confirm",
        ),
    )
    if payload["confirm"] is not True:
        raise ValueError("analysis_confirmation_required")
    if not isinstance(payload["command_id"], str) or not re.fullmatch(
        r"[0-9a-f]{32}", payload["command_id"]
    ):
        raise ValueError("invalid_analysis_command")
    request = {**payload, "tickers": radar.tickers(payload["tickers"], empty=False)}
    run_id = "radar-ui-" + request["command_id"]
    root = runs.root_of({"path": "data/radar/analysis-" + request["command_id"]})
    # ponytail: one shared process lock protects the sealed worker's global ROOT;
    # multi-worker service migration needs explicit per-run worker parameters.
    with platform.RADAR_DISPATCH_LOCK, radar._exclusive_state_lock(
        runs.RADAR_DIR / "analysis-create"
    ):
        if radar_api.ACTIVE or (radar_api.ROOT / "operation.lock").exists():
            raise ValueError("radar_busy_or_stale_lock")
        registry = runs.load()
        path = root / CONTEXT
        if path.exists():
            value = b.check_seal(radar.read(path))
            if value.get("identity") != IDENTITY or value.get("request") != request:
                raise ValueError("analysis_command_conflict")
        else:
            options = choices()
            target, reference = request["target_date"], request["reference_session"]
            if not isinstance(target, str) or target not in options["sessions"]:
                raise ValueError("analysis_target_not_a_planned_session")
            if (
                not isinstance(reference, str)
                or reference not in options["sessions"]
                or not reference < target
                or reference > options["reference_session"]
            ):
                raise ValueError("analysis_reference_must_be_closed_before_target")
            wallet = next(
                (w for w in manual.get({})["wallets"] if w["id"] == request["wallet"]),
                None,
            )
            if wallet is None:
                raise ValueError("analysis_wallet_not_found")
            if wallet.get("strategy") in manual.RULE_STRATEGIES:
                raise ValueError("analysis_rule_wallet_has_no_agents")
            if wallet["revision"] != request["wallet_revision"]:
                raise ValueError("analysis_wallet_changed_reload")
            if target < wallet["start_date"]:
                raise ValueError("analysis_target_before_wallet_start")
            if wallet.get("strategy") == "MULTIAGENT" and set(request["tickers"]) != set(
                default_tickers(wallet)
            ):
                raise ValueError("analysis_multiagent_requires_full_universe")
            value = b.sealed(
                {
                    "identity": IDENTITY,
                    "run": run_id,
                    "request": request,
                    "wallet": wallet_snapshot(wallet),
                    "target_date": target,
                    "reference_session": reference,
                    "created_at": radar.now().isoformat(),
                    "classification": "HISTORICAL_REANALYSIS"
                    if target < options["today"]
                    else "SAME_DAY_ANALYSIS"
                    if target == options["today"]
                    else "FUTURE_ANALYSIS",
                    "scope": "ASSET_COMMITTEES_WITH_WALLET_SNAPSHOT; portfolio proposal/application not implemented",
                    "target_semantics": "INTENDED_USE_DATE; existing asset prompts do not consume target date or wallet positions",
                    "availability": "Data acquired during prepare; no historical availability or pre-opening decision claimed",
                    "provider_calls": 0,
                }
            )
            if root.exists() and any(root.iterdir()):
                raise ValueError("new_analysis_root_not_empty")
            radar.write(path, value, immutable=True)
        if run_id not in registry["runs"]:
            # Context first, then the registry completion marker. Interrupted
            # registration is retried with the same command, never reconstructed.
            runs.register(
                run_id,
                "data/radar/" + root.name,
                value["reference_session"],
                request["tickers"],
                existing=True,
                select=True,
                note="Wallet analysis; target " + value["target_date"],
            )
        else:
            entry = runs.run(run_id, registry)
            if runs.root_of(entry) != root or context(entry) != value:
                raise ValueError("analysis_context_mismatch")
            if registry["selected"] != run_id:
                runs.select(run_id)
        if not (root / "universe.json").exists():
            radar.configure(request["tickers"], root)
        radar_api.ROOT = root
        return {
            "run": run_id,
            "context": value,
            "provider_calls": 0,
            "financial_operations": 0,
        }
