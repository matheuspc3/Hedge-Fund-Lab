"""V7.6 experimental protocol: V7.5 audit, Radar token erratum, plan, validation,
offline scenario qualification and readiness.

Offline only. There is no paid path here: ``paid_gate`` always refuses until a human
authorization record exists, and V7.6 never writes one. Nothing is written under data/;
scenario contexts are frozen in memory on the official frozen opinions (read-only) and
answered by scripted responses, validated by the sealed V2 validator.

Usage (PowerShell, project root):
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py audit       # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py erratum     # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py plan        # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py validate    # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py qualify     # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py readiness   # CONSULTA
  .venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py build       # GRAVA 3 JSON nesta pasta
"""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import base64
import copy
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import multiasset_global_pm as v1
import multiasset_global_pm_v2 as pm
import multiasset_portfolio as b
import multiasset_radar as radar
import radar_runs as runs
import run_global_pm_v2 as cli
import run_multiasset_portfolio as v5_cli
import verify_consolidation_v75 as v75

from src.backtesting.b3_calendar import B3Calendar
from src.experiments.h2_evaluation import PHASE_WINDOWS
from src.experiments.h2_evaluation_offline import no_network

OUT = ROOT / "docs/evidence/hfl_experimental_protocol_v76"
V75 = ROOT / v75.OUT
DAY = "2026-10-09"
TICKERS = ("PETR4", "VALE3", "ITUB4", "WEGE3", "BBAS3")
RADAR = ROOT / v75.RADAR
V1_REAL = ROOT / v75.V1
V2_REAL = ROOT / v75.V2
STATES = (
    "DRAFT",
    "QUALIFIED_OFFLINE",
    "FROZEN_FOR_FUTURE_EVALUATION",
    "AUTHORIZED_FOR_PAID_EXECUTION",
    "EXECUTED",
)
#: Fixed instant for scenario contexts: identical inputs give identical hashes.
QUAL_AT = "2026-10-12T21:00:00+00:00"
#: Conservative reserve per call, as computed by the sealed runners (never released).
GPM_RESERVE = Decimal("0.159744")
RADAR_COMMITTEE_RESERVE = Decimal("0.663552")
#: Observed lower bounds per unit in the real records (V7.5 METRICS), for reference only.
GPM_OBSERVED_FLOOR = (Decimal("0.02354175") + Decimal("0.02626725")) / 2
RADAR_COMMITTEE_OBSERVED_FLOOR = Decimal("0.04313925") / 5
METRIC_FIELDS = (
    "name",
    "dimension",
    "objective",
    "formula",
    "unit",
    "numerator",
    "denominator",
    "applicability",
    "source",
    "limitations",
    "missing_data",
)
#: Inputs a session-selection rule may use; anything after the decision instant leaks.
SELECTION_INPUTS = {"b3_calendar", "cotahist_session_presence", "seed"}
LEAK = re.compile(r"future|forward|post_session|return|close_after|next_", re.I)
CLAIMS = re.compile(
    r"é superior|foi superior|superou|melhor(?:a|ou) o desempenho|reduz(?:iu)? o risco"
    r"|gerou retorno|maximiz|alfa de|sharpe de|rentabilidade de",
    re.I,
)
NEGATION = re.compile(r"\b(não|nem|sem|nenhum|nenhuma|jamais)\b", re.I)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


# --- V7.5 audit and Radar token erratum ------------------------------------------------


def raw_calls(ticker):
    """Provider envelopes of one committee, checked against their recorded hash."""
    base = RADAR / "analyses" / ticker / DAY
    for line in (
        (base / "provider_journal.jsonl").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        entry = json.loads(line)
        raw = base64.b64decode(entry["raw_base64"])
        if hashlib.sha256(raw).hexdigest() != entry["raw_sha256"]:
            raise ValueError("raw_envelope_hash_mismatch:" + ticker)
        yield json.loads(raw)["usageMetadata"], entry["record"]


def field_state(usage, key):
    """ABSENT (key missing), NULL (explicit null), ZERO (explicit 0) or VALUE."""
    if key not in usage:
        return "ABSENT"
    value = usage[key]
    return "NULL" if value is None else "ZERO" if value == 0 else "VALUE"


def erratum():
    rates = read(V2_REAL / "result.json")["cost"]["rates_usd_million"]
    tickers = {}
    for t in TICKERS:
        base = RADAR / "analyses" / t / DAY
        result = read(base / "result.json")
        calls = [
            {
                "stage": record["stage"],
                "analyst_id": record["analyst_id"],
                "thoughts_field": field_state(usage, "thoughtsTokenCount"),
                "thoughts_raw": usage.get("thoughtsTokenCount"),
                "thoughts_normalized": record["token_usage"]["thoughts_tokens"],
                "prompt": usage["promptTokenCount"],
                "output": usage["candidatesTokenCount"],
                "total": usage["totalTokenCount"],
            }
            for usage, record in raw_calls(t)
        ]
        states = Counter(c["thoughts_field"] for c in calls)
        reported = sum(
            c["thoughts_raw"] or 0
            for c in calls
            if c["thoughts_field"] in ("ZERO", "VALUE")
        )
        prompt, output = sum(c["prompt"] for c in calls), sum(c["output"] for c in calls)
        floor = (
            Decimal(prompt) * Decimal(rates["input"])
            + Decimal(output + reported) * Decimal(rates["output"])
        ) / 10**6
        recorded = result["tokens"]["thoughts_tokens"]
        absent = states["ABSENT"] + states["NULL"]
        tickers[t] = {
            "result_json": rel(base / "result.json"),
            "result_sha256": sha(base / "result.json"),
            "result_sha256_pin": (base / "result.sha256").read_text().strip(),
            "journal_sha256": sha(base / "provider_journal.jsonl"),
            "recorded": {
                "thoughts_tokens": recorded,
                "cost_usd": str(result["cost_usd"]),
                "cost_basis": result["cost_basis"],
            },
            "calls": len(calls),
            "thoughts_field_states": dict(sorted(states.items())),
            "explicit_zero_calls": states["ZERO"],
            "reported_thoughts_sum": reported,
            "aggregation_turned_absence_into_zero": absent > 0 and recorded == reported,
            "classification": "RECORDED_ZERO_ALL_ABSENT"
            if recorded == 0 and absent == len(calls)
            else "RECORDED_PARTIAL_SUM"
            if absent and reported
            else "CONSISTENT",
            "corrected_interpretation": {
                "thoughts_tokens": "NOT_REPORTED"
                if absent == len(calls)
                else f"PARTIALLY_REPORTED: {reported} in {len(calls) - absent}/{len(calls)} calls",
                "usd_observed_lower_bound": str(floor),
                "recorded_cost_equals_lower_bound": Decimal(str(result["cost_usd"]))
                == floor,
                "usd_estimated": "UNKNOWN",
                "usd_billed": "UNKNOWN",
            },
            "per_call": calls,
        }
    code = (ROOT / "scripts/multiasset_radar.py").read_text(encoding="utf-8")
    return {
        "identity": "HFL-V76-RADAR-TOKEN-ERRATUM",
        "non_destructive": True,
        "aggregation_rule_found": "sum((u.get(key) or 0) for u in usage)" in code,
        "aggregation_source": "scripts/multiasset_radar.py",
        "aggregation_source_sha256": sha(ROOT / "scripts/multiasset_radar.py"),
        "recorded_zero_tickers": sorted(
            t
            for t, v in tickers.items()
            if v["classification"] == "RECORDED_ZERO_ALL_ABSENT"
        ),
        "partial_sum_tickers": sorted(
            t for t, v in tickers.items() if v["classification"] == "RECORDED_PARTIAL_SUM"
        ),
        "field_states_total": dict(
            sorted(
                sum(
                    (Counter(v["thoughts_field_states"]) for v in tickers.values()),
                    Counter(),
                ).items()
            )
        ),
        "tickers": tickers,
    }


def forbidden_claims(paths):
    """Affirmative performance claims; a hit inside a negated sentence is allowed."""
    hits = []
    for path in paths:
        text = Path(path).read_text(encoding="utf-8")
        for sentence in re.split(r"(?<=[.!?])\s+|\n\n", text):
            if CLAIMS.search(sentence) and not NEGATION.search(sentence):
                hits.append(
                    {"file": rel(path), "sentence": " ".join(sentence.split())[:240]}
                )
    return hits


def audit_v75():
    check = v75.check()
    manifest = read(V75 / "EVIDENCE_MANIFEST.json")
    metrics = read(V75 / "METRICS.json")["metrics"]
    summary = re.findall(
        r"(\d+) failed, (\d+) passed",
        (V75 / "regression.txt").read_text(encoding="utf-8"),
    )
    # Independent path: raw provider envelopes, not the normalized token_usage V7.5 used.
    radar = Counter()
    for t in TICKERS:
        for usage, _ in raw_calls(t):
            radar.update(
                input=usage["promptTokenCount"],
                output=usage["candidatesTokenCount"],
                total=usage["totalTokenCount"],
                thoughts=usage.get("thoughtsTokenCount") or 0,
                calls=1,
            )
    gpm = {}
    for name, root in (("v1", V1_REAL), ("v2", V2_REAL)):
        line = (
            (root / "private/provider_journal.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        usage = json.loads(base64.b64decode(json.loads(line)["raw_base64"]))[
            "usageMetadata"
        ]
        gpm[name] = (
            usage["promptTokenCount"],
            usage["candidatesTokenCount"],
            usage["totalTokenCount"],
        )
    expected = metrics["radar.tokens"]["value"]
    synthetic = [
        s["path"] for s in manifest["sources"] if s["classification"] == "SYNTHETIC"
    ]
    leaked = sorted(
        k
        for k, m in metrics.items()
        if k != "gpm.records_by_planner" and set(m["sources"]) & set(synthetic)
    )
    planners = {
        i: read(
            ROOT
            / "data/global_pm"
            / ("hfl_global_pm_v1" if i.startswith("v7-") else "hfl_global_pm_v2")
            / i
            / "result.json"
        )["planner"]
        for i in metrics["gpm.records_by_planner"]["value"]["real_ids"]
    }
    per_asset = metrics["radar.per_asset"]["value"]
    report_text = (V75 / "SCIENTIFIC_REPORT.md").read_text(encoding="utf-8")
    table_values = [
        f"{v['asset_volatility_21'] * 100:.2f}%".replace(".", ",")
        for v in per_asset.values()
    ] + [f"{v['rsi']:.2f}".replace(".", ",") for v in per_asset.values()]
    comparison = (V75 / "COMPARISON_V1_V2.md").read_text(encoding="utf-8")
    v2ctx = read(V2_REAL / "context.json")
    checks = {
        "v75_verifier_ok": check["ok"],
        "sources_inventoried": len(manifest["sources"]),
        "metrics_defined": len(metrics),
        "regression_failed_passed": [int(x) for x in summary[-1]] if summary else None,
        "missing_primary_sources": check["missing"],
        "hash_violations": check["violations"],
        "raw_radar_tokens_match_v75": (
            radar["input"],
            radar["output"],
            radar["total"],
            radar["thoughts"],
            radar["calls"],
        )
        == (
            expected["input"],
            expected["output"],
            expected["total"],
            expected["thoughts_reported"],
            expected["calls"],
        ),
        "raw_gpm_tokens_match_v75": all(
            gpm[n]
            == tuple(
                metrics[f"gpm_{n}.usage"]["value"][k]
                for k in ("input", "output", "total")
            )
            for n in gpm
        ),
        "real_records_are_gemini": set(planners.values()) == {"GEMINI_GLOBAL_PM"},
        "metrics_citing_synthetic_sources": leaked,
        "sealed_statuses_in_comparison_table": "| Resultado final selado | `REJECTED_BY_VALIDATOR` | `VALID_PROPOSAL` |"
        in comparison,
        "radar_table_values_in_report": [v for v in table_values if v not in report_text],
        "forbidden_financial_claims": forbidden_claims(
            [
                V75 / n
                for n in (
                    "SCIENTIFIC_REPORT.md",
                    "TCC_RESULTS_DRAFT.md",
                    "COMPARISON_V1_V2.md",
                    "README.md",
                )
            ]
        ),
        "v1_status_sealed": read(V1_REAL / "result.json")["status"],
        "v2_status_sealed": read(V2_REAL / "result.json")["status"],
        "v2_contract_unchanged": pm.contracts()["sha256"] == v2ctx["contracts"]["sha256"],
        "v1_contract_unchanged": v1.contracts()
        == read(V1_REAL / "context.json")["contracts"],
    }
    ok = (
        checks["v75_verifier_ok"]
        and checks["sources_inventoried"] == 64
        and checks["metrics_defined"] == 32
        and checks["regression_failed_passed"] == [15, 1706]
        and checks["raw_radar_tokens_match_v75"]
        and checks["raw_gpm_tokens_match_v75"]
        and checks["real_records_are_gemini"]
        and not checks["metrics_citing_synthetic_sources"]
        and checks["sealed_statuses_in_comparison_table"]
        and not checks["radar_table_values_in_report"]
        and not checks["forbidden_financial_claims"]
        and (checks["v1_status_sealed"], checks["v2_status_sealed"])
        == ("REJECTED_BY_VALIDATOR", "VALID_PROPOSAL")
        and checks["v2_contract_unchanged"]
        and checks["v1_contract_unchanged"]
    )
    return {
        "identity": "HFL-V76-V75-AUDIT",
        "ok": ok,
        "checks": checks,
        "v75_check": check,
    }


# --- Offline scenario qualification ----------------------------------------------------


def official_inputs():
    c = read(V2_REAL / "context.json")
    return (
        c["opinions"],
        c["histories"],
        {t: o["raw_close"] for t, o in c["opinions"].items()},
    )


def frozen(record_id, cash, holdings, at=QUAL_AT, origin=None):
    """A V2 context frozen in memory on the official opinions; never written."""
    opinions, histories, prices = official_inputs()
    snapshot = pm.make_snapshot(
        record_id, "CONSULTATIVE_SANDBOX", DAY, prices, holdings, cash, at=at
    )
    return pm.freeze(
        snapshot,
        opinions,
        histories,
        record_id,
        at,
        ack_fixture_policy=True,
        radar_origin=origin,
    )


def scripted(context, specs, watchlist=()):
    """Scripted V2 response (FAKE, never Gemini) for an explicit list of operations."""
    state, calc = context["snapshot"]["financial_state"], context["calculation_context"]
    rid = context["record_id"]
    operations = []
    for i, s in enumerate(specs):
        deps = [f"{rid}-{j}" for j in s.get("depends_on", [])] + s.get(
            "raw_dependencies", []
        )
        op = v5_cli.make_operation(
            f"{rid}-{i}", s["ticker"], s["side"], s["quantity"], calc, dependencies=deps
        )
        op["reasoning"] = "Qualificação V7.6: operação roteirizada."
        operations.append(op)
    try:
        bridge = v5_cli.manual(state, calc, operations, "fixture-preview", "V7.6")
        targets = {t: bridge["target_weights"].get(t, "0") for t in context["opinions"]}
        cash = bridge["target_cash_weight"]
    except (ValueError, KeyError, ArithmeticError):  # the validator must reject it itself
        targets, cash = dict(context["current_weights"]), b.view(state)["cash_weight"]
    reasons = {
        t: {
            "action": pm.expected_action(
                state, t, targets[t], [o for o in operations if o["ticker"] == t]
            ),
            "reasoning": "Qualificação V7.6: resposta roteirizada, não é inferência.",
            "opinion_sha256": o["sha256"],
            "evidence_codes": sorted(
                {e["code"] for v in o["votes"] for e in v["signal"].get("evidence", [])}
            ),
            "cited_metrics": {
                "technical_confidence": context["verifiable_metrics"][t][
                    "technical_confidence"
                ]
            },
        }
        for t, o in context["opinions"].items()
    }
    deferred = [
        o["operation_id"]
        for o in operations
        if o["dependencies"] and not o["dependencies"][0].startswith("missing")
    ]
    return {
        "schema_version": 2,
        "identity": pm.IDENTITY,
        "record_id": rid,
        "decision_session": context["snapshot"]["valuation_session"],
        "created_at": context["created_at"],
        "expires_at": context["expires_at"],
        "snapshot_sha256": context["snapshot"]["sha256"],
        "context_sha256": context["sha256"],
        "summary": "Qualificação offline V7.6.",
        "current_weights": context["current_weights"],
        "target_weights": targets,
        "target_cash_weight": cash,
        "operations": operations,
        "asset_reasoning": reasons,
        "global_reasoning": "Qualificação offline V7.6; resposta roteirizada.",
        "not_selected": [t for t, r in reasons.items() if r["action"] == "NOT_SELECTED"],
        "settlement_deferred_operations": deferred,
        "watchlist_candidates": [
            {
                "ticker": t,
                "radar_signal": context["opinions"][t]["recommendation"],
                "observation": "Sinal registrado no parecer; sem operação.",
                "reassessment_condition": "Novo parecer em sessão futura.",
            }
            for t in watchlist
        ],
        "risks": ["Fixture didática; nenhuma aprovação prospectiva."],
        "opinion_refs": {t: o["sha256"] for t, o in context["opinions"].items()},
    }


def mutate(context, proposal, mutation):
    name, _, arg = (mutation or "").partition(":")
    if name == "declare_not_selected":
        proposal["asset_reasoning"][arg]["action"] = "NOT_SELECTED"
        proposal["not_selected"] = sorted({*proposal["not_selected"], arg})
    elif name == "vetoed_weight":
        cash = Decimal(proposal["target_cash_weight"]) - Decimal("0.10")
        proposal["target_weights"][arg], proposal["target_cash_weight"] = (
            "0.10",
            str(cash),
        )
        proposal["asset_reasoning"][arg]["action"] = "HOLD"
        proposal["not_selected"].remove(arg)
    elif name == "clear_settlement_deferred":
        proposal["settlement_deferred_operations"] = []
    elif name == "opinion_hash":
        proposal["opinion_refs"][arg] = "0" * 64
    elif name == "context_hash":
        proposal["context_sha256"] = "0" * 64
    elif name == "drop_asset":
        del proposal["target_weights"][arg]
    elif name == "tamper_context_opinion":
        context = copy.deepcopy(context)
        context["opinions"][arg]["recommendation"] = "VENDA"
    elif name == "v1_sealed_response":
        proposal = copy.deepcopy(read(V1_REAL / "result.json")["response"])
    elif name:
        raise ValueError("unknown_mutation:" + name)
    return context, proposal


def run_case(matrix, case):
    scenario = matrix["scenarios"][case["scenario"]]
    holdings, cash = scenario["holdings"], scenario["cash"]
    if case.get("variant"):
        holdings = scenario["variants"][case["variant"]]["holdings"]
        cash = scenario["variants"][case["variant"]]["cash"]
    rid = "v76-qual-" + case["id"].lower()
    context = frozen(rid, cash, holdings)
    proposal = scripted(context, case["operations"], case.get("watchlist", ()))
    context, proposal = mutate(context, proposal, case.get("mutation"))
    at = (
        context["expires_at"]
        if case.get("validate_at") == "expires_at"
        else context["created_at"]
    )
    report = pm.validate(context, proposal, at)
    codes = [e["code"] for e in report["errors"]]
    exp = case["expected"]
    checks = [report["status"] == exp["status"]]
    if "code" in exp:
        checks.append(codes == [exp["code"]])
    actions = {
        t: r["action"]
        for t, r in (report["proposal"] or {}).get("asset_reasoning", {}).items()
    }
    for t, action in exp.get("action", {}).items():
        checks.append(actions.get(t) == action)
    if exp.get("receivable_not_available"):
        before = b.view(context["snapshot"]["financial_state"])["cash"]["available"]
        projection = report["projection"]["cash"]
        checks.append(
            b.dec(projection["receivable"]) > 0 and projection["available"] == before
        )
    if "settlement_deferred" in exp:
        checks.append(
            len(report["financial_validation"]["deferred_operations"])
            == exp["settlement_deferred"]
        )
    return {
        "case": case["id"],
        "scenario": case["scenario"],
        "response": "SCRIPTED_FAKE_NOT_GEMINI",
        "status": report["status"],
        "codes": codes,
        "expected": exp,
        "passed": all(checks),
        "operations": len(report["operations"]),
        "context_sha256": context["sha256"],
    }


def origin_checks():
    """Radar origin of a frozen context: VERIFIED, MISMATCH or MISSING (read-only registry)."""
    real = read(V2_REAL / "context.json")["radar_origin"]
    wrong = copy.deepcopy(real)
    wrong["opinion_sha256"]["PETR4"] = "0" * 64
    return {
        name: cli.origin_state(
            frozen("v76-origin-" + name, "100000.00", {}, origin=origin)
        )
        for name, origin in (("verified", real), ("mismatch", wrong), ("missing", None))
    }


IDENTITY_KEYS = {"portfolio_id", "state_sha256", "sha256"}


def economic_fingerprint(context):
    """Hash of the economic input only: record ids, timestamps and seals are excluded,
    so replications of one scenario share it while each context hash stays unique."""

    def strip(value):
        return {k: v for k, v in value.items() if k not in IDENTITY_KEYS}

    return digest(
        {
            "opinions": context["opinions"],
            "histories": context["histories"],
            "calculation_context": context["calculation_context"],
            "current_weights": context["current_weights"],
            "verifiable_metrics": context["verifiable_metrics"],
            "risk_policy": context["risk_policy"],
            "validation_policy": context["validation_policy"],
            "contracts_sha256": context["contracts"]["sha256"],
            "portfolio": strip(b.view(context["snapshot"]["financial_state"])),
            "risk_current": strip(context["risk_current"]),
        }
    )


def replication_identity():
    """Two attempts of one scenario: different record, time and context hash; same input."""
    a = frozen("v76-rep-a", "100000.00", {})
    c = frozen("v76-rep-b", "100000.00", {}, at="2026-10-12T22:30:00+00:00")
    return {
        "context_sha256_differ": a["sha256"] != c["sha256"],
        "economic_fingerprint_equal": economic_fingerprint(a) == economic_fingerprint(c),
        "fingerprint": economic_fingerprint(a),
        "bytes_identical_claimed": False,
    }


def tree(path):
    return {
        p.relative_to(ROOT).as_posix(): sha(p)
        for p in sorted(Path(path).rglob("*"))
        if p.is_file()
    }


def qualify(matrix=None):
    matrix = matrix or read(OUT / "SCENARIO_MATRIX.json")
    watched = [
        V1_REAL,
        V2_REAL,
        RADAR / "analyses",
        pm.OUTPUT / "reservations",
        v1.OUTPUT / "reservations",
    ]
    before = {rel(p): tree(p) for p in watched}
    with no_network():
        rows = [run_case(matrix, case) for case in matrix["cases"]]
        origins = origin_checks()
        replication = replication_identity()
    after = {rel(p): tree(p) for p in watched}
    return {
        "identity": "HFL-V76-OFFLINE-QUALIFICATION",
        "category": matrix["category"],
        "real_provider_calls": 0,
        "cases": rows,
        "passed": sum(r["passed"] for r in rows),
        "total": len(rows),
        "scenarios_covered": sorted({r["scenario"] for r in rows}),
        "radar_origin": origins,
        "origin_ok": origins
        == {"verified": "VERIFIED", "mismatch": "MISMATCH", "missing": "MISSING"},
        "replication_identity": replication,
        "sealed_trees_unchanged": before == after,
        "qualification_sha256": digest(
            [(r["case"], r["status"], r["codes"], r["context_sha256"]) for r in rows]
        ),
    }


# --- Decisions, variability and rates ------------------------------------------------


def decision(sealed):
    """Comparable view of a sealed result (or validation report)."""
    p = sealed.get("response") or sealed.get("proposal")
    weights = {t: Decimal(w) for t, w in p["target_weights"].items()}
    weights["CASH"] = Decimal(p["target_cash_weight"])
    return {
        "status": sealed["status"],
        "validated": sealed["status"] == "VALID_PROPOSAL",
        "weights": weights,
        "actions": {t: r["action"] for t, r in p["asset_reasoning"].items()},
        "operations": len(p["operations"]),
        "watchlist": sorted(w["ticker"] for w in p.get("watchlist_candidates", [])),
    }


def compare(a, b_, *, raw_intent=False):
    """A rejected response is not a decision: only RAW_LLM_INTENT may compare it."""
    if not raw_intent and not (a["validated"] and b_["validated"]):
        return {
            "comparable": False,
            "reason": "rejected_response_is_not_a_validated_decision",
        }
    keys = sorted(set(a["weights"]) | set(b_["weights"]))
    tickers = sorted(set(a["actions"]) | set(b_["actions"]))
    union = set(a["watchlist"]) | set(b_["watchlist"])
    return {
        "comparable": True,
        "basis": "RAW_LLM_INTENT" if raw_intent else "VALIDATED_DECISION",
        "weight_l1": format(
            sum(
                abs(a["weights"].get(k, 0) - b_["weights"].get(k, 0)) for k in keys
            ).normalize(),
            "f",
        ),
        "action_agreement": f"{sum(a['actions'].get(t) == b_['actions'].get(t) for t in tickers)}/{len(tickers)}",
        "both_all_cash": a["weights"]["CASH"] == b_["weights"]["CASH"] == 1,
        "watchlist_jaccard": None
        if not union
        else f"{len(set(a['watchlist']) & set(b_['watchlist']))}/{len(union)}",
    }


def rate(numerator, denominator, min_n):
    """Proportion with a 95% Wilson interval, or INSUFFICIENT_SAMPLE below min_n."""
    out = {"numerator": numerator, "denominator": denominator, "min_n": min_n}
    if denominator < min_n:
        return {**out, "status": "INSUFFICIENT_SAMPLE", "value": None, "wilson95": None}
    z, p = 1.959963984540054, numerator / denominator
    centre = (p + z * z / (2 * denominator)) / (1 + z * z / denominator)
    half = (
        z
        * math.sqrt(p * (1 - p) / denominator + z * z / (4 * denominator**2))
        / (1 + z * z / denominator)
    )
    return {
        **out,
        "status": "ESTIMATED",
        "value": round(p, 6),
        "wilson95": [round(centre - half, 6), round(centre + half, 6)],
    }


def zero_event_upper_bound(n, alpha=0.05):
    """One-sided exact upper bound for a rate when 0 events occur in n trials."""
    return round(1 - alpha ** (1 / n), 6)


# --- Sessions, plan, budget ----------------------------------------------------------


def eligible_sessions(rule):
    start, end = (date.fromisoformat(d) for d in rule["retrospective_window"])
    excluded = set(rule["development_sessions"])
    windows = [
        (date.fromisoformat(w.start), date.fromisoformat(w.end))
        for w in PHASE_WINDOWS.values()
    ]
    return [
        s.isoformat()
        for s in B3Calendar().sessions_between(start, end)
        if s.isoformat() not in excluded and not any(a <= s <= z for a, z in windows)
    ]


def session_order(rule):
    """Seeded permutation of eligible calendar sessions; never uses prices or returns.
    The first ``count`` are the sample; later ones are the pre-registered replacements."""
    pool = eligible_sessions(rule)
    return random.Random(rule["seed"]).sample(pool, len(pool))


def select_sessions(rule):
    return sorted(session_order(rule)[: rule["count"]])


def leakage(rule, campaigns, today):
    """Temporal-leakage and scope findings for the session design."""
    found = [
        f"forbidden_selection_input:{i}"
        for i in rule["selection_inputs"]
        if i not in SELECTION_INPUTS or LEAK.search(i)
    ]
    for w in PHASE_WINDOWS.values():
        a, z = date.fromisoformat(w.start), date.fromisoformat(w.end)
        found += [
            f"session_in_h2_window:{s}"
            for c in campaigns
            for s in c.get("sessions", [])
            if not s.startswith("AFTER_FREEZE") and a <= date.fromisoformat(s) <= z
        ]
    for c in campaigns:
        sessions = [s for s in c.get("sessions", []) if not s.startswith("AFTER_FREEZE")]
        found += [
            f"development_session_reused:{c['id']}:{s}"
            for s in sessions
            if s in rule["development_sessions"]
            and not c["evaluation"].endswith("_ON_DEVELOPMENT_INPUTS")
        ]
        if c["evaluation"] == "PROSPECTIVE" and any(
            date.fromisoformat(s) <= today for s in sessions
        ):
            found.append(f"prospective_label_on_known_session:{c['id']}")
        if c.get("decision_information_cutoff", "SESSION_CLOSE") != "SESSION_CLOSE":
            found.append(f"information_after_decision:{c['id']}")
    return found


def campaign_sessions(campaign, rule):
    if campaign["sessions"] == ["SELECTED_OUT_OF_SAMPLE"]:
        return select_sessions(rule)
    if campaign["sessions"] == [
        "AFTER_FREEZE"
    ]:  # dates unknown until the protocol is frozen
        return [
            f"AFTER_FREEZE_{i:02d}" for i in range(1, campaign["decisions_planned"] + 1)
        ]
    return campaign["sessions"]


def attempt_ids(campaign, sessions):
    return [
        f"v76-{campaign['id']}-{s.replace('-', '')}-r{k:03d}".lower()
        for s in sessions
        for k in range(1, campaign["replications"] + 1)
    ]


def radar_reserved():
    """Reservations of every registered Radar run (read-only)."""
    registry = runs.load()
    return sum(
        (
            Decimal(str(read(p)["usd_reserved"]))
            for r in registry["runs"].values()
            for p in (ROOT / r["path"] / "reservations").glob("*.json")
        ),
        Decimal(0),
    )


def plan(manifest=None):
    manifest = manifest or read(OUT / "EXPERIMENT_MANIFEST.json")
    rule = manifest["session_selection"]
    oos = select_sessions(rule)
    gpm_cap = Decimal(pm.CONFIG["root_budget_usd"])
    gpm_used = cli.used_budget()
    radar_cap, radar_used = Decimal(str(radar.GLOBAL_BUDGET_USD)), radar_reserved()
    campaigns, seen, errors = [], set(), []
    for c in manifest["campaigns"]:
        sessions = campaign_sessions(c, rule)
        ids = attempt_ids(c, sessions)
        duplicates = sorted({i for i in ids if i in seen or ids.count(i) > 1})
        existing = sorted(
            i for i in ids if (pm.OUTPUT / i).exists() or (v1.OUTPUT / i).exists()
        )
        errors += [f"duplicate_attempt_id:{i}" for i in duplicates] + [
            f"attempt_id_already_used:{i}" for i in existing
        ]
        seen.update(ids)
        attempts = len(ids)
        gpm_calls = attempts * c["calls_per_attempt"]["global_pm"]
        committees = (
            len(sessions) * c["calls_per_attempt"]["radar_committees"]
            if c["calls_per_attempt"]["radar_committees"]
            else 0
        )
        gpm_reserve, radar_reserve = (
            gpm_calls * GPM_RESERVE,
            committees * RADAR_COMMITTEE_RESERVE,
        )
        blocks = list(c.get("requires", []))
        if gpm_reserve > gpm_cap - gpm_used:
            blocks.append(
                "BUDGET_EXCEEDS_SEALED_V2_CAP_REQUIRES_NEW_TREATMENT_OR_DECISION"
            )
        if radar_reserve and radar_used + radar_reserve > radar_cap:
            blocks.append(
                "RADAR_AGGREGATE_EXCEEDS_CAP_REQUIRES_HUMAN_BUDGET_AUTHORIZATION"
            )
        campaigns.append(
            {
                "id": c["id"],
                "evaluation": c["evaluation"],
                "treatment": c["treatment"],
                "scenario": c["scenario"],
                "sessions": sessions,
                "replications": c["replications"],
                "attempts": attempts,
                "first_attempt_id": ids[0] if ids else None,
                "attempt_ids_sha256": digest(ids),
                "calls": {
                    "global_pm": gpm_calls,
                    "radar_committees": committees,
                    "radar_calls_max": committees * 6,
                },
                "usd": {
                    "reserve_global_pm": str(gpm_reserve),
                    "reserve_radar": str(radar_reserve),
                    "reserve_total": str(gpm_reserve + radar_reserve),
                    "observed_floor_reference": str(
                        gpm_calls * GPM_OBSERVED_FLOOR
                        + committees * RADAR_COMMITTEE_OBSERVED_FLOOR
                    ),
                    "billed": "UNKNOWN_UNTIL_PROVIDER_INVOICE",
                },
                "precision": {
                    "normal_approx_half_width95_at_p50": round(
                        1.959963984540054 * math.sqrt(0.25 / attempts), 4
                    )
                    if attempts
                    else None,
                    "zero_rejection_upper_bound95": zero_event_upper_bound(attempts)
                    if attempts
                    else None,
                },
                "status": "BLOCKED" if blocks else "PLANNED_NOT_AUTHORIZED",
                "blocks": blocks,
            }
        )
    body = {
        "identity": "HFL-V76-BUDGET-PLAN",
        "schema_version": 1,
        "paid_calls_authorized": 0,
        "caps": {
            "global_pm_sealed_v2_cap_usd": str(gpm_cap),
            "global_pm_reserved_v1_v2_usd": str(gpm_used),
            "global_pm_remaining_usd": str(gpm_cap - gpm_used),
            "global_pm_max_new_calls": int((gpm_cap - gpm_used) // GPM_RESERVE),
            "radar_aggregate_cap_usd": str(radar_cap),
            "radar_reserved_all_runs_usd": str(radar_used),
        },
        "unit_reserves_usd": {
            "global_pm_call": str(GPM_RESERVE),
            "radar_committee": str(RADAR_COMMITTEE_RESERVE),
        },
        "out_of_sample_sessions": oos,
        "campaigns": campaigns,
        "errors": errors,
    }
    return {**body, "plan_sha256": digest(body)}


def paid_gate(manifest):
    """The only door to paid execution; V7.6 never opens it."""
    auth = manifest.get("authorization")
    if (
        manifest.get("state") != "AUTHORIZED_FOR_PAID_EXECUTION"
        or not auth
        or auth.get("protocol_sha256") != manifest.get("protocol_sha256")
        or not auth.get("signatory")
        or not auth.get("max_usd")
    ):
        raise PermissionError("paid_execution_not_authorized")
    raise PermissionError("paid_execution_not_implemented_in_v76")


# --- Protocol validation and readiness -----------------------------------------------

PROTOCOL_DOCS = (
    "EXPERIMENTAL_PROTOCOL.md",
    "PREREGISTRATION_DRAFT.md",
    "REPETABILITY_DESIGN.md",
    "OUT_OF_SAMPLE_DESIGN.md",
    "PAPER_TRADING_PROTOCOL.md",
    "BASELINES_AND_CONTROLS.md",
    "SCENARIO_MATRIX.json",
    "METRIC_CATALOG.json",
    "BUDGET_PLAN.json",
)
SUPPORTING_DOCS = (
    "README.md",
    "V75_INDEPENDENT_AUDIT.md",
    "RADAR_TOKEN_ERRATUM.md",
    "TEST_FAILURE_TRIAGE.md",
    "REPRODUCIBILITY.md",
    "RESEARCH_ROADMAP.md",
    "READINESS_REPORT.json",
    "preservation_before.json",
)


def documents(names):
    return {n: sha(OUT / n) if (OUT / n).exists() else None for n in names}


def validate_protocol(manifest=None, matrix=None, catalog=None, today=None):
    manifest = manifest or read(OUT / "EXPERIMENT_MANIFEST.json")
    matrix = matrix or read(OUT / "SCENARIO_MATRIX.json")
    catalog = catalog or read(OUT / "METRIC_CATALOG.json")
    today = today or date.fromisoformat(pm.now()[:10])
    errors = []
    if manifest.get("identity") != "HFL-V76-ROBUSTNESS-PROTOCOL" or not manifest.get(
        "version"
    ):
        errors.append("protocol_identity_or_version")
    state = manifest.get("state")
    if state not in STATES:
        errors.append("unknown_state")
    elif STATES.index(state) >= STATES.index("FROZEN_FOR_FUTURE_EVALUATION") and not (
        manifest.get("frozen_at") and manifest.get("human_review")
    ):
        errors.append("frozen_without_human_review")
    if state in ("AUTHORIZED_FOR_PAID_EXECUTION", "EXECUTED"):
        try:
            paid_gate(manifest)
        except PermissionError as exc:
            if str(exc) == "paid_execution_not_authorized":
                errors.append("paid_state_without_valid_authorization")
    if state == "EXECUTED" and not all(
        (pm.OUTPUT / i / "result.json").exists()
        for i in (manifest.get("execution") or {}).get("records", []) or ["-"]
    ):
        errors.append("executed_without_execution_evidence")
    if manifest.get("documents") and manifest["documents"] != documents(PROTOCOL_DOCS):
        errors.append(
            "frozen_protocol_modified"
            if state in STATES[2:]
            else "protocol_documents_changed_rebuild_required"
        )
    treatments = manifest["treatments"]
    v2 = treatments.get("HFL-MULTIASSET-GLOBAL-PM-V2", {})
    if not (
        v2.get("contracts_sha256")
        == pm.contracts()["sha256"]
        == read(V2_REAL / "context.json")["contracts"]["sha256"]
    ):
        errors.append("v2_treatment_contract_changed")
    radar_t = treatments.get("HFL-MULTIASSET-RADAR-V1", {})
    if (
        radar_t.get("manifest_sha256")
        != runs.run("radar-2026-10-09-recovery-01")["treatment"]["manifest_sha256"]
    ):
        errors.append("radar_treatment_manifest_changed")
    for name in treatments:
        if "H2" in name.upper():
            errors.append("h2_out_of_scope:" + name)
    for c in manifest["campaigns"]:
        if c["treatment"] not in treatments:
            errors.append(f"campaign_treatment_unknown:{c['id']}")
        if c["treatment"] == v1.IDENTITY or treatments.get(c["treatment"], {}).get(
            "closed"
        ):
            errors.append(f"closed_treatment_in_campaign:{c['id']}")
        if c["scenario"] not in matrix["scenarios"]:
            errors.append(f"campaign_scenario_unknown:{c['id']}")
    groups = Counter(
        (c["replication_group"], c["treatment"]) for c in manifest["campaigns"]
    )
    by_group = Counter(g for g, _ in groups)
    errors += [
        f"treatments_mixed_in_replication_group:{g}" for g, n in by_group.items() if n > 1
    ]
    rule = manifest["session_selection"]
    errors += leakage(
        rule,
        [{**c, "sessions": campaign_sessions(c, rule)} for c in manifest["campaigns"]],
        today,
    )
    metrics = catalog["metrics"]
    for mid, m in metrics.items():
        missing = [f for f in METRIC_FIELDS if not m.get(f)]
        if missing:
            errors.append(f"metric_definition_incomplete:{mid}:{','.join(missing)}")
    for sid, s in matrix["scenarios"].items():
        errors += [
            f"metric_undefined:{sid}:{m}" for m in s["metrics"] if m not in metrics
        ]
    ids = [c["id"] for c in matrix["cases"]]
    errors += [f"duplicate_case:{i}" for i, n in Counter(ids).items() if n > 1]
    for c in matrix["cases"]:
        if c["scenario"] not in matrix["scenarios"]:
            errors.append(f"case_scenario_unknown:{c['id']}")
        code = c["expected"].get("code")
        if (
            code
            and code not in pm.ERRORS
            and code not in matrix.get("undescribed_codes", {})
        ):
            errors.append(f"expected_code_unknown:{c['id']}:{code}")
    errors += [
        f"undescribed_code_now_described:{k}"
        for k in matrix.get("undescribed_codes", {})
        if k in pm.ERRORS
    ]
    if set(matrix["scenarios"]) != {f"S{i}" for i in range(10)}:
        errors.append("scenario_matrix_must_cover_s0_s9")
    return errors


def readiness(audit=None, qualification=None, budget=None, errors=None, manifest=None):
    manifest = manifest or read(OUT / "EXPERIMENT_MANIFEST.json")
    audit = audit or audit_v75()
    qualification = qualification or qualify()
    budget = budget or plan(manifest)
    errors = validate_protocol(manifest) if errors is None else errors
    sources = (
        all((p / "context.json").exists() for p in (V1_REAL, V2_REAL))
        and (RADAR / "analyses").exists()
    )
    gates = {
        "structurally_defined": not errors,
        "methodologically_reviewable": all(
            (OUT / n).exists() for n in PROTOCOL_DOCS if n != "BUDGET_PLAN.json"
        ),
        "qualified_offline": qualification["passed"] == qualification["total"]
        and qualification["origin_ok"]
        and qualification["replication_identity"]["context_sha256_differ"]
        and qualification["replication_identity"]["economic_fingerprint_equal"]
        and qualification["sealed_trees_unchanged"],
        "v75_audit_ok": audit["ok"],
        "sources_available": sources,
        "budget_plan_consistent": not budget["errors"],
        "human_review_recorded": bool(manifest.get("human_review")),
        "paid_execution_authorized": False,
    }
    blocked = sorted(
        {"HUMAN_REVIEW_OF_PREREGISTRATION", "PAID_EXECUTION_AUTHORIZATION"}
        | {blk for c in budget["campaigns"] for blk in c["blocks"]}
    )
    offline = all(
        gates[k]
        for k in (
            "structurally_defined",
            "methodologically_reviewable",
            "qualified_offline",
            "v75_audit_ok",
            "sources_available",
            "budget_plan_consistent",
        )
    )
    return {
        "identity": "HFL-V76-READINESS",
        "state": "QUALIFIED_OFFLINE" if offline else "DRAFT",
        "max_state_reachable_in_v76": "QUALIFIED_OFFLINE",
        "gates": gates,
        "blocked_by": blocked,
        "protocol_errors": errors,
        "campaigns": {
            c["id"]: {"status": c["status"], "blocks": c["blocks"]}
            for c in budget["campaigns"]
        },
        "qualification": {
            k: qualification[k]
            for k in (
                "passed",
                "total",
                "scenarios_covered",
                "radar_origin",
                "replication_identity",
                "sealed_trees_unchanged",
                "qualification_sha256",
                "real_provider_calls",
            )
        },
        "qualification_cases": [
            {k: r[k] for k in ("case", "status", "codes", "passed")}
            for r in qualification["cases"]
        ],
        "v75_audit": audit["checks"],
        "plan_sha256": budget["plan_sha256"],
    }


def write(path, data):
    # ponytail: LF bytes so the Windows working copy matches the committed blob.
    Path(path).write_bytes(
        (json.dumps(data, ensure_ascii=False, indent=1, default=str) + "\n").encode()
    )


def build():
    manifest = read(OUT / "EXPERIMENT_MANIFEST.json")
    budget = plan(manifest)
    write(OUT / "BUDGET_PLAN.json", budget)
    unsealed = {**manifest, "documents": None}
    report = readiness(
        budget=budget, errors=validate_protocol(unsealed), manifest=manifest
    )
    write(OUT / "READINESS_REPORT.json", report)
    docs = documents(PROTOCOL_DOCS)
    manifest.update(
        state=report["state"],
        documents=docs,
        protocol_sha256=digest(docs),
        supporting_documents=documents(SUPPORTING_DOCS),
    )
    write(OUT / "EXPERIMENT_MANIFEST.json", manifest)
    return {
        "state": report["state"],
        "protocol_sha256": manifest["protocol_sha256"],
        "written": [
            "BUDGET_PLAN.json",
            "READINESS_REPORT.json",
            "EXPERIMENT_MANIFEST.json",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "command",
        choices=("audit", "erratum", "plan", "validate", "qualify", "readiness", "build"),
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with no_network():
        result = {
            "audit": audit_v75,
            "erratum": erratum,
            "plan": plan,
            "validate": lambda: {"errors": validate_protocol()},
            "qualify": qualify,
            "readiness": readiness,
            "build": build,
        }[args.command]()
    print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    ok = (
        result.get("ok", True)
        and not result.get("errors")
        and result.get("state", "QUALIFIED_OFFLINE") == "QUALIFIED_OFFLINE"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
