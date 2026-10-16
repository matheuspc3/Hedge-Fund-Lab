"""Read-only V6 selection, cost previews, sealed proposals and pure projections."""

import os
import sys
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[1] / "scripts"),
]
import multiasset_global_pm as pm  # noqa: E402
import multiasset_portfolio as b  # noqa: E402
import multiasset_radar as radar  # noqa: E402
import run_global_pm as cli  # noqa: E402

ROOT = Path(os.environ.get("HFL_GLOBAL_PM_ROOT", pm.DEFAULT_ROOT))
OFFICIAL_RADAR = radar.OUTPUT
SYNTHETIC_RADAR = b.ROOT / "data/radar/demo-v4"


def selection(mode, day, symbols):
    if mode not in pm.MODES:
        raise ValueError("invalid_analysis_mode")
    radar.session(day)
    symbols = radar.tickers(symbols, empty=False)
    root = SYNTHETIC_RADAR if mode == "SYNTHETIC_DEMO" else OFFICIAL_RADAR
    items = []
    for symbol in symbols:
        try:
            opinions, _ = pm.load_opinions(root, [symbol], day, mode, pm.now())
            o = opinions[symbol]
            items.append(
                {
                    "ticker": symbol,
                    "status": "ELIGIBLE",
                    "opinion_sha256": o["sha256"],
                    "recommendation": o["recommendation"],
                    "generated_at": o["generated_at"],
                    "detail_url": "/radar",
                    "synthetic": mode == "SYNTHETIC_DEMO",
                }
            )
        except (ValueError, KeyError, OSError, TypeError):
            items.append(
                {
                    "ticker": symbol,
                    "status": "MISSING_OR_INELIGIBLE",
                    "reason": "Parecer completo e íntegro desta fonte/sessão necessário; nada foi gerado.",
                }
            )
    missing = [i["ticker"] for i in items if i["status"] != "ELIGIBLE"]
    asset_cost = radar.estimate({"manifest": {"mode": "live"}})
    return {
        "identity": pm.IDENTITY,
        "mode": mode,
        "session": day,
        "items": items,
        "status": "INSUFFICIENT_DATA" if missing else "READY_FOR_CONTEXT_PREPARATION",
        "missing": missing,
        "selected": symbols,
        "provider_calls": 0,
        "radar_cost_preview": {
            "authorization_scope": "RADAR_ONLY_SEPARATE",
            "missing_count": len(missing),
            "calls_max": 6 * len(missing),
            "usd_estimated": str(b.dec(str(asset_cost["usd_estimated"])) * len(missing))
            if mode == "CONSULTATIVE_SANDBOX"
            else "0",
            "usd_reserved": str(b.dec(str(asset_cost["usd_reserved"])) * len(missing))
            if mode == "CONSULTATIVE_SANDBOX"
            else "0",
            "planning_only": True,
        },
        "global_pm_cost_preview": {
            "authorization_scope": "GLOBAL_PM_ONLY_SEPARATE",
            "calls_max": 1,
            "usd_reserved_ceiling": str(
                (
                    b.dec(pm.CONFIG["input_bytes_max"])
                    * b.dec(pm.CONFIG["input_usd_million_ceiling"])
                    + b.dec(pm.CONFIG["options"]["max_output_tokens"])
                    * b.dec(pm.CONFIG["output_usd_million_ceiling"])
                )
                / 1000000
            )
            if mode == "CONSULTATIVE_SANDBOX"
            else "0",
            "usd_estimated": None,
            "estimate_note": "Estimativa depende do contexto congelado; nenhum custo autorizado nesta consulta.",
        },
        "execution_enabled": False,
    }


def public_detail(root):
    data = cli.detail(root)
    if not data.get("context"):
        return data
    c, result = data["context"], data["result"]
    observed = b.view(c["snapshot"]["financial_state"])
    breaches = []
    if b.dec(observed["exposure"]) > b.dec(b.POLICY["max_exposure"]):
        breaches.append("exposure_above_fixture_limit")
    if any(
        b.dec(p["market_value"])
        > b.dec(b.POLICY["max_concentration"]) * b.dec(observed["equity"])
        for p in observed["positions"].values()
    ):
        breaches.append("concentration_above_fixture_limit")
    return {
        "identity": pm.IDENTITY,
        "status": data["status"],
        "mode": c["mode"],
        "source_classification": c["source_classification"],
        "portfolio": observed,
        "marks": c["snapshot"]["financial_state"]["marks"],
        "snapshot_sha256": c["snapshot"]["sha256"],
        "context_sha256": c["sha256"],
        "created_at": c["created_at"],
        "expires_at": c["expires_at"],
        "valuation_session": c["snapshot"]["valuation_session"],
        "opinions": c["opinions"],
        "risk_current": c["risk_current"],
        "current_limit_breaches": breaches,
        "current_weights": c["current_weights"],
        "contracts": c["contracts"],
        "estimate": cli.estimate(c),
        "result": result,
        "execution_enabled": False,
        "simulation_note": "Simulação contábil em memória à marca conhecida. Projeção condicionada mantém preços hipotéticos, nunca preços futuros observados.",
    }


def demo_index():
    root = pm.root_path(ROOT)
    path = root / "demo.json"
    if not path.exists():
        return None
    index = b.check_seal(b.read(path))
    if index["identity"] != pm.IDENTITY or index["mode"] != "SYNTHETIC_DEMO":
        raise ValueError("demo_identity_changed")
    return index


def get(command, query):
    if command == "selection" and set(query) == {"mode", "session", "tickers"}:
        return selection(query["mode"], query["session"], query["tickers"].split(","))
    if command == "status" and not query:
        index = demo_index()
        return {
            "identity": pm.IDENTITY,
            "status": "NO_PROPOSAL" if index is None else "PROPOSALS_AVAILABLE",
            "cases": index["cases"] if index else [],
            "prepared": public_detail(ROOT) if (ROOT / "context.json").exists() else None,
            "execution_enabled": False,
            "paid_inference_available_in_ui": False,
        }
    if (
        command in ("case", "simulate")
        and set(query) == {"case"}
        and query["case"] in tuple("ABCDEF")
    ):
        index = demo_index()
        if index is None:
            raise ValueError("offline_demo_not_initialized")
        entry = next(i for i in index["cases"] if i["case"] == query["case"])
        data = public_detail(pm.OUTPUT / entry["root_id"])
        if (
            data["result"]["sha256"] != entry["result_sha256"]
            or data["context_sha256"] != entry["context_sha256"]
        ):
            raise ValueError("demo_case_integrity_changed")
        return {
            **data,
            "case": entry["case"],
            "simulation_requested": command == "simulate",
        }
    if command == "prepared" and not query:
        return public_detail(ROOT)
    if command == "preflight" and set(query) == {"max_usd"}:
        return cli.preflight(ROOT, query["max_usd"])
    raise ValueError("invalid_global_pm_query")
