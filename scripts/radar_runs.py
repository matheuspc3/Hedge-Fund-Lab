"""Radar runs: separate operational instances of the one sealed Radar treatment.

``data/radar/registry.json`` is an allowlist and an index, never an authority: every
answer below is re-derived from each run's own frozen inputs, claims, journals,
reservations and results, which this module only reads (``multiasset_radar``,
``run_multiasset_radar`` and ``radar_api`` stay sealed; they take a root).

A run is a root directly under ``data/radar/`` with its own session, universe,
claims, journals, reservations and budget. A run registered as ``--instance-of``
another must carry the same treatment manifest (model, prompts, parameters,
contracts): it is a new operational instance, never a silent new treatment.
Nothing is copied between runs.

Budget: each run keeps the sealed per-root ledger. Across runs the conservative
reserved exposure is compared with ``AGGREGATE_CAP_USD`` (the original US$ 5 local
limit); above it a paid batch needs a separate, explicit, run-specific budget
authorization bound to the current exposure (``authorize-budget``). Old reserves
are never released or copied.

Commands (PowerShell, project root; class in brackets):
  list | status [--run ID] | budget --run ID | compare --run A --with B   [CONSULTA]
  preflight --run ID [--tickers ...]                                     [CONSULTA]
  register ... | select --run ID | prepare --run ID                      [GRAVA]
  authorize-budget --run ID --confirm BUDGET_TOKEN                       [GRAVA]
  run --run ID --confirm TOKEN --authorize-paid                          [PAGA]
"""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

import pandas as pd

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).parent)]
import multiasset_radar as radar

from src.backtesting.daily_agent import _exclusive_state_lock
from src.pipeline.b3_official import FACTOR_NEIGHBOR_TOLERANCE

RADAR_DIR = radar.ROOT / "data/radar"
REGISTRY = RADAR_DIR / "registry.json"
RUN_ID = re.compile(r"radar-[a-z0-9][a-z0-9-]{0,60}")
FOLDER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
MODES = {"CONSULTATIVE_SANDBOX": "live", "SYNTHETIC_DEMO": "synthetic"}
AGGREGATE_CAP_USD = radar.GLOBAL_BUDGET_USD
#: Incident catalog: external metadata only; the incident records are never rewritten.
INCIDENTS = {
    "INCIDENT_2026_10_12_NETWORK_GUARD": {
        "classification": "Falha local confirmada — lote preservado — não reutilizável para novas chamadas.",
        "evidence": "docs/evidence/hfl_incident_2026_10_12/",
        "billing": "Reserva local, não custo faturado; uso no provedor a confirmar no console.",
    }
}
FIELDS = {
    "id",
    "path",
    "mode",
    "classification",
    "source",
    "treatment",
    "instance_of",
    "reference_run",
    "session",
    "universe",
    "budget_usd",
    "accepts_new_calls",
    "incident",
    "registered_at",
    "note",
}
STATES = (
    "INCIDENT_PRESERVED",
    "INPUTS_READY",
    "AWAITING_AUTHORIZATION",
    "RUNNING",
    "COMPLETED",
    "PARTIAL",
    "RECOVERY_REQUIRED",
    "BLOCKED",
    "INTEGRITY_ERROR",
)
GUARD_MESSAGE = "offline qualification forbids network"
#: Comparison tolerances, declared and reported, never applied to the data: adjusted
#: prices use the pipeline's own "same factor" bound; features and metrics are
#: canonical to 6 decimals, so 2 units in the last decimal is a rounding step.
PRICE_TOLERANCE = FACTOR_NEIGHBOR_TOLERANCE
FEATURE_TOLERANCE = 2e-6


def sealed(value):
    body = {k: v for k, v in value.items() if k != "sha256"}
    return {**body, "sha256": radar.digest(body)}


# Registry ------------------------------------------------------------------------


def root_of(entry):
    """Resolved root of an allowlisted entry; refuses traversal, links and protected areas."""
    path = entry.get("path") if isinstance(entry, dict) else None
    if not isinstance(path, str) or not path.startswith("data/radar/"):
        raise ValueError("run_path_not_allowed")
    name = path.removeprefix("data/radar/")
    if not FOLDER.fullmatch(name):  # no separators, no "..", no drive or UNC
        raise ValueError("run_path_not_allowed")
    base = RADAR_DIR.resolve()
    candidate = base / name
    resolved = candidate.resolve()
    # A symlink or junction anywhere on the way resolves elsewhere: refused.
    if resolved != candidate or resolved.parent != base:
        raise ValueError("run_path_escapes_radar_storage")
    return radar.storage_root(resolved)


def check_entry(key, entry):
    if not RUN_ID.fullmatch(key) or not isinstance(entry, dict) or set(entry) != FIELDS:
        raise ValueError("registry_entry_invalid")
    if entry["id"] != key or entry["mode"] not in MODES:
        raise ValueError("registry_entry_invalid")
    radar.session(entry["session"])
    if entry["universe"] != radar.tickers(entry["universe"], empty=False):
        raise ValueError("registry_entry_invalid")
    budget = entry["budget_usd"]
    if (
        type(budget) not in (int, float)
        or not math.isfinite(budget)
        or not 0 < budget <= radar.GLOBAL_BUDGET_USD
        or type(entry["accepts_new_calls"]) is not bool
    ):
        raise ValueError("registry_entry_invalid")
    incident = entry["incident"]
    if incident is not None and (
        incident.get("id") not in INCIDENTS or entry["accepts_new_calls"]
    ):
        raise ValueError("registry_incident_must_be_read_only")
    treatment = entry["treatment"]
    if not isinstance(treatment, dict) or treatment.get("identity") != radar.IDENTITY:
        raise ValueError("registry_entry_invalid")
    root_of(entry)


def load(path=None):
    """Validated registry or ValueError; callers never fall back to another run."""
    path = path or REGISTRY
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("registry_unavailable") from exc
    except (OSError, ValueError) as exc:
        raise ValueError("registry_corrupted") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or not isinstance(data.get("runs"), dict)
        or data.get("sha256") != sealed(data)["sha256"]
    ):
        raise ValueError("registry_corrupted")
    seen = {}
    for key, entry in data["runs"].items():
        check_entry(key, entry)
        alias = os.path.normcase(str(root_of(entry)))
        if alias in seen:
            raise ValueError("registry_root_aliased")
        seen[alias] = key
    for key in ("instance_of", "reference_run"):
        if any(e[key] not in (None, *data["runs"]) for e in data["runs"].values()):
            raise ValueError("registry_entry_invalid")
    if data.get("selected") not in data["runs"]:
        raise ValueError("registry_selection_invalid")
    return data


def run(run_id, registry=None):
    registry = registry or load()
    if not isinstance(run_id, str) or run_id not in registry["runs"]:
        raise ValueError("unknown_radar_run")
    return registry["runs"][run_id]


def run_for_root(root, registry):
    """Registered run that owns ``root`` (compared resolved), or None."""
    target = os.path.normcase(str(Path(root).resolve()))
    return next(
        (
            e
            for e in registry["runs"].values()
            if os.path.normcase(str(root_of(e))) == target
        ),
        None,
    )


def treatment(mode):
    return {
        "identity": radar.IDENTITY,
        "manifest_sha256": radar.digest(radar.manifest(MODES[mode])),
        "model": radar.MODEL,
    }


def register(
    run_id,
    path,
    session,
    universe,
    mode="CONSULTATIVE_SANDBOX",
    *,
    budget_usd=radar.GLOBAL_BUDGET_USD,
    existing=False,
    read_only=False,
    incident=None,
    instance_of=None,
    select=False,
    note="",
    registry_path=None,
):
    registry_path = Path(registry_path or REGISTRY)
    entry = {
        "id": run_id,
        "path": path,
        "mode": mode,
        "classification": "OFFICIAL" if mode == "CONSULTATIVE_SANDBOX" else "SYNTHETIC",
        "source": "B3_COTAHIST_YFINANCE_ADJUSTED"
        if mode == "CONSULTATIVE_SANDBOX"
        else "SYNTHETIC_OFFLINE_NOT_MARKET_DATA",
        "treatment": treatment(mode) if mode in MODES else None,
        "instance_of": instance_of,
        "reference_run": instance_of,
        "session": session,
        "universe": universe,
        "budget_usd": budget_usd,
        "accepts_new_calls": not read_only and incident is None,
        "incident": None
        if incident is None
        else {"id": incident, **INCIDENTS.get(incident, {})},
        "registered_at": radar.now().isoformat(),
        "note": note,
    }
    check_entry(run_id, entry)
    root = root_of(entry)
    with _exclusive_state_lock(registry_path):
        if registry_path.exists():
            data = load(registry_path)
        else:
            data = {
                "schema_version": 1,
                "revision": 0,
                "selected": run_id,
                "runs": {},
                "history": [],
            }
        if run_id in data["runs"] or run_for_root(root, data):
            raise ValueError("run_or_root_already_registered")
        if existing:
            if not root.is_dir():
                raise ValueError("existing_root_missing")
            # Cataloguing never re-labels a different treatment as this one.
            for item in (root / "analyses").glob("*/*/input.json"):
                if (
                    radar.read(item)["manifest_sha256"]
                    != entry["treatment"]["manifest_sha256"]
                ):
                    raise ValueError("existing_root_has_other_treatment")
        elif root.exists() and any(root.iterdir()):
            raise ValueError("new_run_root_must_be_empty_nothing_is_copied")
        if instance_of is not None:
            parent = run(instance_of, data)
            if parent["mode"] != mode or parent["treatment"] != entry["treatment"]:
                raise ValueError("instance_must_share_treatment_register_new_identity")
        data["runs"][run_id] = entry
        if select:
            data["selected"] = run_id
        data["revision"] += 1
        data["history"].append(
            {
                "revision": data["revision"],
                "at": entry["registered_at"],
                "action": "REGISTER",
                "run": run_id,
            }
        )
        radar.write(registry_path, sealed(data))
    return entry


def select(run_id, registry_path=None):
    registry_path = Path(registry_path or REGISTRY)
    with _exclusive_state_lock(registry_path):
        data = load(registry_path)
        run(run_id, data)
        data["selected"] = run_id
        data["revision"] += 1
        data["history"].append(
            {
                "revision": data["revision"],
                "at": radar.now().isoformat(),
                "action": "SELECT",
                "run": run_id,
            }
        )
        radar.write(registry_path, sealed(data))
    return data


# Read-only inventory ---------------------------------------------------------------


def committee_outcome(root, ticker, day):
    """What happened to each reserved call of one claim; read-only, codes only."""
    folder = radar.folder_for(root, ticker, day)
    if (folder / "result.sha256").exists():
        synthetic = radar.read(folder / "result.json")["mode"] == "synthetic"
        return {
            "state": "COMMITTEE_COMPLETED",
            "billing": "SYNTHETIC_NO_PROVIDER"
            if synthetic
            else "PROVIDER_USAGE_RECORDED",
        }
    if not (folder / "claim.json").exists():
        return None
    kinds, usage = [], False
    if (folder / "calls.sqlite").exists():
        uri = (folder / "calls.sqlite").as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as db:
            last = {
                seq: json.loads(evidence)
                for seq, evidence in db.execute(
                    "SELECT sequence, evidence FROM attempts WHERE slot='L01' "
                    "ORDER BY sequence, attempt"
                )
            }
            rows = db.execute(
                "SELECT sequence, raw IS NOT NULL, record FROM calls WHERE slot='L01' "
                "ORDER BY sequence"
            ).fetchall()
        for seq, raw, record in rows:
            record = json.loads(record) if record else None
            evidence = last.get(seq, {})
            usage |= bool(record and record.get("token_usage"))
            kinds.append(
                "UNCERTAIN"  # reserved, no durable outcome: the request may have left
                if record is None
                else "OK"
                if record.get("status") == "ok"
                else "ENVELOPE_RECORDED"
                if raw
                else "BLOCKED_BEFORE_CONNECT"
                if evidence.get("type") == "RuntimeError"
                and evidence.get("message") == GUARD_MESSAGE
                and evidence.get("http_status") is None
                else "PROVIDER_HTTP_ERROR"
                if evidence.get("http_status") is not None
                else "TRANSPORT_ERROR"
            )
    if "UNCERTAIN" in kinds:
        state = "UNCERTAIN_CALLS"
    elif kinds and set(kinds) <= {"OK", "ENVELOPE_RECORDED"}:
        state = "RECOVERABLE_OFFLINE"
    elif "OK" in kinds:
        state = "COMMITTEE_PARTIAL"
    else:
        state = "NO_RECOVERABLE_ENVELOPE"
    return {
        "state": state,
        "calls_reserved": len(kinds),
        "calls": dict(Counter(kinds)),
        # A local guard refusal happens before any socket exists; provider-side usage
        # is still to be confirmed in its console, never assumed from a null status.
        "billing": "PROVIDER_USAGE_RECORDED"
        if usage
        else "NO_SEND_EVIDENCE"
        if kinds and set(kinds) == {"BLOCKED_BEFORE_CONNECT"}
        else "UNKNOWN",
    }


def calls(folder):
    path = folder / "calls.sqlite"
    if not path.exists():
        return 0, 0
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        return db.execute("SELECT COUNT(*), COUNT(raw) FROM calls").fetchone()


def reservations(root):
    """Each reserved batch and what its claims tell about the reserve; never a release."""
    claims = {}
    for path in (root / "analyses").glob("*/*/claim.json"):
        claims.setdefault(radar.read(path).get("batch_token"), []).append(path.parent)
    result = []
    for path in sorted((root / "reservations").glob("*.json")):
        report = radar.read(path)
        if report.get("confirmation_token") != path.stem:
            raise ValueError("reservation_integrity_failed")
        folders = claims.get(path.stem, [])
        outcomes = [
            committee_outcome(root, f.parent.name, f.name) or {"state": "NO_CLAIM"}
            for f in folders
        ]
        settled = bool(outcomes) and all(
            o["state"] == "COMMITTEE_COMPLETED" for o in outcomes
        )
        billing = sorted({o.get("billing", "UNKNOWN") for o in outcomes}) or ["UNKNOWN"]
        result.append(
            {
                "batch": path.stem[:12],
                "usd_estimated": report.get("usd_estimated"),
                "usd_reserved": report["usd_reserved"],
                "claims": len(folders),
                "outcome": "SETTLED_BY_RESULTS" if settled else "OUTCOME_UNCERTAIN",
                # Forensics of an unsettled reserve, e.g. LOCAL_BLOCK: guard refused
                # before any socket; billing still unconfirmed at the provider.
                "forensic": "SETTLED"
                if settled
                else "LOCAL_BLOCK_BEFORE_CONNECT_BILLING_UNCONFIRMED"
                if billing == ["NO_SEND_EVIDENCE"]
                else "UNCERTAIN_" + "+".join(billing),
            }
        )
    return result


def inventory(entry):
    """Per-run facts for UI, diagnostic and gates. Reads only; never repairs."""
    root = root_of(entry)
    mode, day = MODES[entry["mode"]], entry["session"]
    items, errors = [], []
    observed = 0.0
    for ticker in entry["universe"]:
        folder = radar.folder_for(root, ticker, day)
        item = {
            "ticker": ticker,
            "input": False,
            "opinion": False,
            "claim": (folder / "claim.json").exists(),
            "failure": (folder / "failure.json").exists(),
            "restricted": None,
            "prepared_at": None,
            "outcome": None,
        }
        try:
            item["calls_reserved"], item["responses_recorded"] = calls(folder)
            if (folder / "input.json").exists():
                data = radar.checked_input(root, ticker, day)
                if data["manifest"]["mode"] != mode:
                    raise ValueError("synthetic_official_mix")
                if data["manifest_sha256"] != entry["treatment"]["manifest_sha256"]:
                    raise ValueError("input_treatment_differs_from_run")
                limit = data["manifest"]["risk"]["max_asset_volatility"]
                item.update(
                    input=True,
                    input_sha256=radar.sha_file(folder / "input.json"),
                    prepared_at=data["prepared_at"],
                    restricted=data["risk_metrics"]["asset_volatility_21"] > limit,
                )
                detail = radar.detail(ticker, day, root)
                item["opinion"] = detail["status"] == "COMPLETED"
                if item["opinion"] and mode == "live":
                    observed += detail["cost_usd"]
            item["outcome"] = committee_outcome(root, ticker, day)
        except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
            errors.append(
                f"{ticker}:{exc}"
                if re.fullmatch(r"[a-z_0-9]+", str(exc))
                else f"{ticker}:integrity_failed"
            )
        items.append(item)
    stray = sorted(
        f"{p.parent.parent.name}/{p.parent.name}"
        for p in (root / "analyses").glob("*/*/input.json")
        if p.parent.name != day or p.parent.parent.name not in entry["universe"]
    )
    try:
        batches = reservations(root)
    except (ValueError, KeyError, OSError, sqlite3.Error):
        batches, errors = [], [*errors, "reservations:integrity_failed"]
    return {
        "items": items,
        "errors": errors,
        "outside_identity": stray,  # analyses outside the run's session/universe
        "inputs": sum(i["input"] for i in items),
        "opinions": sum(i["opinion"] for i in items),
        "claims": sum(i["claim"] for i in items),
        "failures": sum(i["failure"] for i in items),
        "calls_reserved": sum(i.get("calls_reserved", 0) for i in items),
        "responses_recorded": sum(i.get("responses_recorded", 0) for i in items),
        "reservations": batches,
        "usd_reserved": round(sum(b["usd_reserved"] for b in batches), 6),
        "usd_reserved_uncertain": round(
            sum(
                b["usd_reserved"] for b in batches if b["outcome"] != "SETTLED_BY_RESULTS"
            ),
            6,
        ),
        # Provider token usage priced at the public table: an estimate, not an invoice.
        "usd_observed_provider_tokens": round(observed, 6),
        "usd_billed_confirmed": None,
        "running": (root / "operation.lock").exists(),
        "prepared_at": max(
            (i["prepared_at"] for i in items if i["prepared_at"]), default=None
        ),
    }


def gaps(new, old):
    """{key: [old, new]} of differing values, or None when the key sets differ."""
    if set(new) != set(old):
        return None
    return {k: [old[k], new[k]] for k in new if new[k] != old[k]}


def near(differences):
    return differences is not None and all(
        abs(a - b) <= FEATURE_TOLERANCE for a, b in differences.values()
    )


def compare(entry, reference):
    """Economic content of two runs' frozen inputs for the same session; read-only."""
    if entry["session"] != reference["session"] or entry["mode"] != reference["mode"]:
        return {
            "comparable": False,
            "material": True,
            "reason": "session_or_mode_differs",
        }
    a_root, b_root, day = root_of(entry), root_of(reference), entry["session"]
    items = []
    for ticker in entry["universe"]:
        a = radar.folder_for(a_root, ticker, day)
        b = radar.folder_for(b_root, ticker, day)
        if not (a / "input.json").exists() or not (b / "input.json").exists():
            items.append({"ticker": ticker, "status": "NOT_COMPARABLE_INPUT_MISSING"})
            continue
        x, y = radar.read(a / "input.json"), radar.read(b / "input.json")
        bars = [
            pd.read_csv(
                f / "bars.csv",
                index_col=0,
                parse_dates=True,
                float_precision="round_trip",
            )
            for f in (a, b)
        ]
        same_sessions = bars[0].index.equals(bars[1].index)
        prices = ["abertura", "maxima", "minima", "fechamento"]
        drift = (
            float((bars[0][prices] / bars[1][prices] - 1).abs().max().max())
            if same_sessions
            else None
        )
        events = [(v["source"].get("corporate_events") or {}) for v in (x, y)]

        features, metrics = (gaps(x[key], y[key]) for key in ("features", "risk_metrics"))
        checks = {
            "sessions": same_sessions,
            "volume": same_sessions and bars[0]["volume"].equals(bars[1]["volume"]),
            "raw_bar": x["raw_bar"] == y["raw_bar"],
            "adjusted_close_last": x["adjusted_close"] == y["adjusted_close"],
            "adjusted_series": drift is not None and drift <= PRICE_TOLERANCE,
            "features": near(features),
            "risk_metrics": near(metrics),
            "corporate_events": (events[0].get("events") or [])
            == (events[1].get("events") or []),
            "inherited_factors": list(x["source"].get("inherited_factors", {}).values())
            == list(y["source"].get("inherited_factors", {}).values()),
            "treatment_manifest": x["manifest_sha256"] == y["manifest_sha256"],
        }
        exact = (
            x["history"]["sha256"] == y["history"]["sha256"]
            and not features
            and not metrics
        )
        items.append(
            {
                "ticker": ticker,
                "status": "MATERIAL_DIVERGENCE"
                if not all(checks.values())
                else "IDENTICAL"
                if exact
                else "EQUIVALENT_WITHIN_TOLERANCE",
                "checks": checks,
                "differences": {
                    "adjusted_series_max_relative": drift,
                    "adjusted_series_sessions_differing": int(
                        (bars[0][prices] != bars[1][prices]).any(axis=1).sum()
                    )
                    if same_sessions
                    else None,
                    "features": features,
                    "risk_metrics": metrics,
                },
                "tolerances": {
                    "price_relative": PRICE_TOLERANCE,
                    "feature_absolute": FEATURE_TOLERANCE,
                },
                "bars_sha256_identical": x["history"]["sha256"] == y["history"]["sha256"],
                "input_sha256_identical": radar.sha_file(a / "input.json")
                == radar.sha_file(b / "input.json"),
                # Provenance that may differ without economic effect (download time,
                # cache, or a pre-V7.2 input prepared by the original extractor).
                "provenance": {
                    "cotahist_sha256_identical": x["source"].get("cotahist_sha256")
                    == y["source"].get("cotahist_sha256"),
                    "source_name_identical": x["source"].get("name")
                    == y["source"].get("name"),
                    "normalizer": [
                        events[1].get("normalization", "ORIGINAL_V4_EXTRACTOR"),
                        events[0].get("normalization", "ORIGINAL_V4_EXTRACTOR"),
                    ],
                    "prepared_at": [y["prepared_at"], x["prepared_at"]],
                },
            }
        )
    return {
        "comparable": True,
        "run": entry["id"],
        "reference": reference["id"],
        "session": day,
        "items": items,
        "material": any(i["status"] == "MATERIAL_DIVERGENCE" for i in items),
    }


def planned(entry, inv, tickers=None):
    """Calls and reserve a new batch would need: tickers with input and no claim."""
    chosen = [
        i
        for i in inv["items"]
        if i["input"] and not i["claim"] and (tickers is None or i["ticker"] in tickers)
    ]
    cost = radar.estimate({"manifest": {"mode": MODES[entry["mode"]]}})
    paid = cost["paid"]
    return {
        "tickers": [i["ticker"] for i in chosen],
        "calls_max": cost["calls_max"] * len(chosen),
        # A restricted asset is vetoed by the deterministic rule: no Risk call.
        "calls_planned": sum(5 + (0 if i["restricted"] else 1) for i in chosen),
        "usd_estimated": round(cost["usd_estimated"] * len(chosen), 6) if paid else 0,
        "usd_reserved": round(cost["usd_reserved"] * len(chosen), 6) if paid else 0,
    }


def budget(run_id, registry, tickers=None, inventories=None):
    """Run ledger, every official run's reserve and the aggregate gate; read-only."""
    entry = run(run_id, registry)
    inventories = inventories or {}
    rows = []
    for rid, other in registry["runs"].items():
        if other["mode"] != "CONSULTATIVE_SANDBOX":
            continue  # synthetic runs never reserve provider money
        inv = inventories.get(rid) or inventory(other)
        inventories[rid] = inv
        rows.append(
            {
                "run": rid,
                "incident": (other["incident"] or {}).get("id"),
                "budget_usd": other["budget_usd"],
                "usd_reserved": inv["usd_reserved"],
                "usd_reserved_uncertain": inv["usd_reserved_uncertain"],
                "usd_observed_provider_tokens": inv["usd_observed_provider_tokens"],
                "usd_billed_confirmed": None,
                "reservations": inv["reservations"],
            }
        )
    own = inventories.get(run_id) or inventory(entry)
    plan = planned(entry, own, tickers)
    others = round(sum(r["usd_reserved"] for r in rows if r["run"] != run_id), 6)
    exposure = round(others + own["usd_reserved"] + plan["usd_reserved"], 6)
    report = {
        "run": run_id,
        "run_budget_usd": entry["budget_usd"],
        "run_reserved_usd": own["usd_reserved"],
        "planned": plan,
        "runs": rows,
        "other_runs_reserved_usd": others,
        "aggregate_exposure_usd": exposure,
        "aggregate_cap_usd": AGGREGATE_CAP_USD,
        "aggregate_policy": "NO_APPROVED_AGGREGATE_CAP_ORIGINAL_LOCAL_LIMIT_APPLIES",
        "within_run_budget": own["usd_reserved"] + plan["usd_reserved"]
        <= entry["budget_usd"],
        "within_aggregate_cap": exposure <= AGGREGATE_CAP_USD,
    }
    report["budget_token"] = radar.digest(
        {k: report[k] for k in ("run", "run_budget_usd", "run_reserved_usd", "planned")}
        | {"runs": [(r["run"], r["usd_reserved"]) for r in rows]}
    )
    report["authorization"] = authorization(entry, report)
    return report


def authorization(entry, report):
    needed = report["planned"]["usd_reserved"] > 0 and not report["within_aggregate_cap"]
    folder = root_of(entry) / "budget_authorizations"
    path = folder / (report["budget_token"] + ".json")
    if path.exists():
        record = radar.read(path)
        valid = (
            record.get("sha256") == sealed(record)["sha256"]
            and record.get("run") == entry["id"]
            and record.get("budget_token") == report["budget_token"]
        )
        return {"state": "VALID" if valid else "INTEGRITY_ERROR", "required": needed}
    stale = folder.exists() and any(folder.glob("*.json"))
    return {
        "state": "NOT_REQUIRED" if not needed else "STALE" if stale else "ABSENT",
        "required": needed,
    }


def status(entry, registry, inventories=None):
    """Conceptual state (module doc / runbook) from the run's own records."""
    inventories = inventories if inventories is not None else {}
    inv = inventories.get(entry["id"]) or inventory(entry)
    inventories[entry["id"]] = inv
    n, reasons = len(entry["universe"]), []
    comparison = None
    if entry["reference_run"] and inv["inputs"]:
        comparison = compare(entry, run(entry["reference_run"], registry))
        if comparison["material"]:
            reasons.append("material_divergence_from_reference_run")
    money = (
        budget(entry["id"], registry, inventories=inventories)
        if entry["mode"] == "CONSULTATIVE_SANDBOX"
        else None
    )
    unsettled = inv["claims"] - inv["opinions"]
    if inv["outside_identity"]:
        reasons.append("analyses_outside_run_identity")
    if inv["errors"] or (money and money["authorization"]["state"] == "INTEGRITY_ERROR"):
        state = "INTEGRITY_ERROR"
    elif entry["incident"]:
        state = "INCIDENT_PRESERVED"
    elif inv["running"]:
        state = "RUNNING"
    elif inv["opinions"] == n:
        state = "COMPLETED"
    elif inv["opinions"] and unsettled:
        state = "PARTIAL"
    elif unsettled:
        state = "RECOVERY_REQUIRED"
    elif reasons:
        state = "BLOCKED"
    elif inv["inputs"] < n:
        state, reasons = "BLOCKED", ["inputs_missing"]
    elif not entry["accepts_new_calls"]:
        state, reasons = "BLOCKED", ["run_read_only"]
    elif (
        money
        and money["authorization"]["required"]
        and money["authorization"]["state"] != "VALID"
    ):
        state, reasons = "INPUTS_READY", ["aggregate_budget_authorization_required"]
    else:
        state = "AWAITING_AUTHORIZATION"
    return {
        "id": entry["id"],
        "state": state,
        "reasons": reasons,
        "inventory": inv,
        "comparison": comparison,
        "budget": money,
        "global_pm_available": state == "COMPLETED",
    }


def public(entry, registry, inventories=None):
    """Projection for UI and diagnostic: no journals, prompts, keys or raw envelopes."""
    s = status(entry, registry, inventories)
    inv = s["inventory"]
    return {
        **{
            k: entry[k]
            for k in (
                "id",
                "path",
                "mode",
                "classification",
                "source",
                "session",
                "universe",
                "budget_usd",
                "accepts_new_calls",
                "incident",
                "instance_of",
                "registered_at",
                "note",
            )
        },
        "treatment": entry["treatment"],
        "same_treatment_as": entry["instance_of"],
        "selected": registry["selected"] == entry["id"],
        "state": s["state"],
        "reasons": s["reasons"],
        "inputs": inv["inputs"],
        "opinions": inv["opinions"],
        "claims": inv["claims"],
        "failures": inv["failures"],
        "calls_reserved": inv["calls_reserved"],
        "responses_recorded": inv["responses_recorded"],
        "prepared_at": inv["prepared_at"],
        "usd_reserved": inv["usd_reserved"],
        "usd_reserved_uncertain": inv["usd_reserved_uncertain"],
        "usd_observed_provider_tokens": inv["usd_observed_provider_tokens"],
        "usd_billed_confirmed": None,
        "integrity": "ERROR" if inv["errors"] else "OK",
        "errors": inv["errors"],
        "outside_identity": inv["outside_identity"],
        "items": [
            {
                k: i[k]
                for k in (
                    "ticker",
                    "input",
                    "opinion",
                    "claim",
                    "failure",
                    "restricted",
                    "outcome",
                )
            }
            for i in inv["items"]
        ],
        "comparison": s["comparison"],
        "budget": s["budget"],
        "global_pm_available": s["global_pm_available"],
    }


def overview(registry_path=None):
    registry = load(registry_path)
    cache = {}
    return {
        "revision": registry["revision"],
        "selected": registry["selected"],
        "registry_sha256": registry["sha256"],
        "runs": [public(e, registry, cache) for e in registry["runs"].values()],
    }


# Gates for commands that write records or call the provider ------------------------


def gate(run_id, command, tickers, day, registry, *, report=None):
    """Raise unless ``command`` may act on this run; ``report`` = sealed radar preflight."""
    entry = run(run_id, registry)
    if not entry["accepts_new_calls"]:
        raise ValueError("run_not_accepting_new_calls")
    if day != entry["session"] or not set(tickers) <= set(entry["universe"]):
        raise ValueError("selection_outside_run_identity")
    if command in ("prepare", "universe"):
        return entry
    s = status(entry, registry)
    if s["state"] == "INTEGRITY_ERROR" or s["reasons"] and s["state"] == "BLOCKED":
        raise ValueError("run_blocked_" + (s["reasons"] or ["integrity_error"])[0])
    if (
        report is None
        or report.get("replay")
        or not any(i.get("mode") == "live" for i in report["items"])
    ):
        return entry
    ready = [i["ticker"] for i in report["items"] if i.get("ready")]
    money = budget(run_id, registry, tickers=ready)
    if not money["within_run_budget"]:
        raise ValueError("run_budget_exceeded")
    if money["authorization"]["required"] and money["authorization"]["state"] != "VALID":
        raise ValueError("aggregate_budget_authorization_required")
    return entry


def authorize_budget(run_id, token, registry_path=None):
    """Write the separate budget authorization (GRAVA, never a provider call)."""
    registry = load(registry_path)
    entry = run(run_id, registry)
    if not entry["accepts_new_calls"]:
        raise ValueError("run_not_accepting_new_calls")
    report = budget(run_id, registry)
    if token != report["budget_token"]:
        raise ValueError("budget_changed_review_again")
    if not report["within_run_budget"] or not report["planned"]["usd_reserved"]:
        raise ValueError("nothing_to_authorize_within_run_budget")
    record = sealed(
        {
            "schema_version": 1,
            "run": run_id,
            "budget_token": token,
            "authorized_at": radar.now().isoformat(),
            "run_budget_usd": report["run_budget_usd"],
            "planned": report["planned"],
            "runs": [
                {
                    k: r[k]
                    for k in ("run", "incident", "usd_reserved", "usd_reserved_uncertain")
                }
                for r in report["runs"]
            ],
            "aggregate_exposure_usd": report["aggregate_exposure_usd"],
            "aggregate_cap_usd": report["aggregate_cap_usd"],
            "exceeds_original_local_limit": not report["within_aggregate_cap"],
            "statement": "Autorização humana separada do orçamento desta execução; não libera nem copia reservas de outras execuções e não autoriza chamadas (o lote exige preflight e token próprios).",
        }
    )
    radar.write(
        root_of(entry) / "budget_authorizations" / (token + ".json"),
        record,
        immutable=True,
    )
    return record


def preflight(run_id, tickers=None, registry=None):
    """Sealed Radar preflight for the run, plus the cross-run budget view. Reads only."""
    registry = registry or load()
    entry = run(run_id, registry)
    tickers = radar.tickers(tickers or entry["universe"], empty=False)
    report = radar.preflight(
        tickers, root_of(entry), day=entry["session"], max_usd=entry["budget_usd"]
    )
    # Budget is shown for the requested batch even while e.g. the key is absent.
    money = budget(run_id, registry, tickers=tickers)
    blockers = sorted({i["error"] for i in report["items"] if not i.get("ready")})
    if report["ready"] is False and not blockers:
        blockers.append("radar_budget_or_limit")
    try:
        gate(run_id, "run", tickers, entry["session"], registry, report=report)
    except ValueError as exc:
        blockers.append(str(exc))
    if money["authorization"]["required"] and money["authorization"]["state"] != "VALID":
        blockers.append("aggregate_budget_authorization_required")
    ready = [i["ticker"] for i in report["items"] if i.get("ready")]
    return {
        "run": run_id,
        "session": entry["session"],
        "treatment": entry["treatment"],
        "radar_preflight": report,
        "budget": money,
        "blockers": sorted(set(blockers)),
        "gate": "READY_FOR_HUMAN_AUTHORIZATION" if not blockers else "BLOCKED",
        "consent": "Autorizo chamadas pagas Gemini somente para a execução "
        f"{run_id}, sessão {entry['session']}, ativos {', '.join(ready) or '—'}, "
        f"teto reservado US$ {report['usd_reserved']}.",
        "provider_calls": 0,
    }


def bind(radar_api, registry_path=None):
    """Server start: the selected run, if it accepts calls, is the Radar API runner."""
    try:
        registry = load(registry_path)
        entry = run(registry["selected"], registry)
    except ValueError:
        return None  # no runner: prepare/run are refused; never a fallback run
    if not entry["accepts_new_calls"]:
        return None
    # ponytail: the sealed radar_api reads one module-level ROOT (HFL_RADAR_ROOT);
    # one runner per server process. Upgrade path: a root parameter when resealed.
    radar_api.ROOT = root_of(entry)
    return entry["id"]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "command",
        choices=(
            "list",
            "status",
            "budget",
            "compare",
            "preflight",
            "register",
            "select",
            "prepare",
            "authorize-budget",
            "run",
        ),
    )
    parser.add_argument("--run")
    parser.add_argument("--with", dest="other")
    parser.add_argument("--path")
    parser.add_argument("--session")
    parser.add_argument("--tickers", nargs="*")
    parser.add_argument("--mode", choices=tuple(MODES), default="CONSULTATIVE_SANDBOX")
    parser.add_argument("--budget-usd", type=float, default=radar.GLOBAL_BUDGET_USD)
    parser.add_argument("--existing", action="store_true")
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--incident", choices=tuple(INCIDENTS))
    parser.add_argument("--instance-of")
    parser.add_argument("--select", action="store_true")
    parser.add_argument("--note", default="")
    parser.add_argument("--confirm")
    parser.add_argument("--authorize-paid", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    import network_scope

    # Explicit safe configuration: offline checks here guard only their own context.
    network_scope.install()
    code = 0
    if args.command == "register":
        result = register(
            args.run,
            args.path,
            args.session,
            args.tickers,
            args.mode,
            budget_usd=args.budget_usd,
            existing=args.existing,
            read_only=args.read_only,
            incident=args.incident,
            instance_of=args.instance_of,
            select=args.select,
            note=args.note,
        )
    elif args.command == "select":
        result = select(args.run)["selected"]
    elif args.command == "list":
        result = overview()
    elif args.command == "status":
        data = overview()
        result = [r for r in data["runs"] if args.run in (None, r["id"])] or None
    elif args.command == "budget":
        result = budget(args.run, load(), tickers=args.tickers)
    elif args.command == "compare":
        registry = load()
        result = compare(run(args.run, registry), run(args.other, registry))
        code = 1 if result["material"] else 0
    elif args.command == "preflight":
        result = preflight(args.run, args.tickers)
        code = 0 if result["gate"] == "READY_FOR_HUMAN_AUTHORIZATION" else 2
    elif args.command == "prepare":
        registry = load()
        entry = run(args.run, registry)
        gate(args.run, "prepare", entry["universe"], entry["session"], registry)
        import radar_corporate_events

        radar_corporate_events.install()  # the same normalized path as /radar
        result = radar.prepare(
            entry["universe"],
            root_of(entry),
            end=entry["session"],
            mode=MODES[entry["mode"]],
        )
        code = 1 if any(i["status"] == "BLOCKED" for i in result) else 0
    elif args.command == "authorize-budget":
        result = authorize_budget(args.run, args.confirm)
    else:  # run: PAID. The sealed run() recomputes its preflight and token under lock.
        registry = load()
        entry = run(args.run, registry)
        report = preflight(args.run, args.tickers, registry)
        if report["gate"] != "READY_FOR_HUMAN_AUTHORIZATION":
            raise SystemExit("blocked: " + ", ".join(report["blockers"]))
        # ponytail: gate and sealed lock are separate steps; one local operator. A
        # concurrent reservation in another run between them is the known ceiling.
        result = radar.run(
            [i["ticker"] for i in report["radar_preflight"]["items"]],
            args.confirm,
            root_of(entry),
            day=entry["session"],
            max_usd=entry["budget_usd"],
            authorize_paid=args.authorize_paid,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
