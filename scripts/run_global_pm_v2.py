"""Global PM V2 CLI: prepare/preflight/run/replay/status/qualify/incident.

Paid inference needs a new preflight token, ``--authorize-paid``, a Radar origin that
still verifies and the key in the backend environment. ``qualify`` and ``incident`` are
offline. V1 records are only read; V1 code (``run_global_pm.py``) is imported, never
edited, because its hash is sealed into every V1 context.

Usage (PowerShell, project root):
  .venv/Scripts/python.exe -B scripts/run_global_pm_v2.py incident
  .venv/Scripts/python.exe -B scripts/run_global_pm_v2.py qualify
  .venv/Scripts/python.exe -B scripts/run_global_pm_v2.py prepare --radar-run RUN \
      --confirm-hypothetical --ack-fixture-policy
  .venv/Scripts/python.exe -B scripts/run_global_pm_v2.py preflight --id v74-...
  .venv/Scripts/python.exe -B scripts/run_global_pm_v2.py run --id v74-... --confirm TOKEN --authorize-paid
"""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import asyncio
import base64
import copy
import hashlib
import json
import os
import sqlite3
import sys
import uuid
from contextlib import closing
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parent),
]
import multiasset_global_pm as v1
import multiasset_global_pm_v2 as pm
import multiasset_portfolio as b
import multiasset_radar as radar
import radar_runs as runs
import run_global_pm as v1cli
import run_multiasset_portfolio as v5_cli

from src.agents.llm_client import LLMCallMetadata
from src.agents.llm_trace import (
    LLMCallRequest,
    RecordingLLMClient,
    ReplayLLMClient,
    load_trace,
    schema_digest,
    schema_name,
)
from src.backtesting.daily_agent import _exclusive_state_lock
from src.experiments.h2_evaluation_offline import no_network
from src.experiments.h2_evaluation_production import (
    _PENDING_CALL,
    CallBank,
    JournalIntegrityError,
)

DAY = "2026-10-09"
QUALIFICATION = "v74-qual"
#: First real V1 inference: read-only evidence. Bytes pinned at the V7.4 investigation.
INCIDENT = "v7-5a78ea5d15214e37bcae18f167ffcee3"
INCIDENT_SHA256 = {
    "authorization.json": "052d29dd37fd7161cf5f1202b8a5309e7cdf96750a350c62a0c9d91ceebf4e4f",
    "claim.json": "ce02b18b5de40544ec623f89b85856146e9ed3c341b4bd9b249d5b6d668a72b5",
    "context.json": "36f0fc6f38aeb7a08ff158355b9aa779d5ccb765c7b5b2be24648c6c0305757d",
    "private/calls.sqlite": "5ca3198bd6135d53fc192c93f230de707ef97a14710758e5e865ef6ef879797a",
    "private/provider_journal.jsonl": "a3869ca2760df73e18e53ef6af1a7e25c69f3c18f0189d860b943f688f2681bb",
    "result.json": "c8069e128a331fee5c9a170800a1da4442782b5ec83c9be458a1ca146f60e140",
}
PRICES = {
    "PETR4": "40.00",
    "VALE3": "60.00",
    "ITUB4": "30.00",
    "WEGE3": "50.00",
    "BBAS3": "25.00",
}


class GlobalGeminiClient(v1cli.GlobalGeminiClient):
    """Same durable native transport; only the V2 prompt, schema and input differ."""

    async def propose(self, context):
        self.begin_session(context["snapshot"]["valuation_session"])
        user = pm.prompt_input(context)
        metadata = LLMCallMetadata(stage="global_portfolio_manager")
        request = LLMCallRequest(
            stage=metadata.stage,
            analyst_id=None,
            decision_session=self.session,
            provider="gemini",
            requested_model=self.native.model,
            system_prompt=pm.PROMPT,
            user_prompt=user,
            response_schema=schema_name(pm.GlobalProposal),
            response_schema_sha256=schema_digest(pm.GlobalProposal),
            requested_options=pm.CONFIG["options"],
        )
        row = self.bank.reserve(self.slot, 0, request, fresh=self.fresh)
        self.sequence = 1
        if row[4] is None:
            if not self.fresh and row[2] is None:
                raise JournalIntegrityError("uncertain_response_no_replacement_inference")
            recorder = RecordingLLMClient(
                self.native, provider="gemini", requested_model=self.native.model
            )
            recorder.begin_session(self.session)
            token = _PENDING_CALL.set((self.slot, 0))
            try:
                try:
                    await recorder.generate(
                        pm.PROMPT,
                        user,
                        pm.GlobalProposal,
                        pm.CONFIG["options"],
                        metadata=metadata,
                    )
                except JournalIntegrityError:
                    raise
                except Exception:
                    pass  # The recorder preserves the failed schema/provider response.
                record = replace(
                    recorder.records[0],
                    attempt_count=self.bank.attempt_count(self.slot, 0),
                    error_message=None
                    if recorder.records[0].error_message is None
                    else "provider_or_response_validation_failed",
                )
                self.bank.response(self.slot, 0, record)
            finally:
                _PENDING_CALL.reset(token)
            row = self.bank.row(self.slot, 0)
        replay = ReplayLLMClient(
            load_trace((row[4] + "\n").encode()),
            provider="gemini",
            requested_model=self.native.model,
        )
        replay.begin_session(self.session)
        response = await replay.generate(
            pm.PROMPT, user, pm.GlobalProposal, pm.CONFIG["options"], metadata=metadata
        )
        replay.assert_complete()
        self.assert_complete()
        return response.model_dump(mode="json")


def radar_source(run_id, tickers, day, mode, at):
    """Opinions read from a registered run's own root; the origin is sealed in the context."""
    registry = runs.load()
    entry = runs.run(run_id, registry)
    if entry["mode"] != mode:
        raise ValueError("synthetic_official_mix")
    if entry["session"] != day:
        raise ValueError("session_differs_from_radar_run")
    if not set(radar.tickers(tickers, empty=False)) <= set(entry["universe"]):
        raise ValueError("selection_outside_run_identity")
    opinions, histories = v1.load_opinions(runs.root_of(entry), tickers, day, mode, at)
    origin = {
        "radar_run": {
            k: entry[k]
            for k in ("id", "path", "mode", "classification", "session", "universe")
        },
        "incident": (entry["incident"] or {}).get("id"),
        "registry_revision": registry["revision"],
        "registry_sha256": registry["sha256"],
        "opinion_sha256": {t: o["sha256"] for t, o in opinions.items()},
    }
    return opinions, histories, origin


def origin_state(context):
    origin = context["radar_origin"]
    if origin is None:
        return "MISSING"
    try:
        entry = runs.run(origin["radar_run"]["id"])
    except ValueError:
        return "MISMATCH"
    same = (
        entry["path"] == origin["radar_run"]["path"]
        and entry["mode"] == context["mode"]
        and origin["opinion_sha256"]
        == {t: o["sha256"] for t, o in context["opinions"].items()}
    )
    return "VERIFIED" if same else "MISMATCH"


def prepare(
    root,
    snapshot,
    opinions,
    histories,
    *,
    at=None,
    ack_fixture_policy=False,
    radar_origin=None,
):
    root = pm.root_path(root)
    context = pm.freeze(
        snapshot,
        opinions,
        histories,
        root.name,
        at,
        ack_fixture_policy=ack_fixture_policy,
        radar_origin=radar_origin,
    )
    with _exclusive_state_lock(pm.OUTPUT / "operation"):
        if any(root.iterdir()) if root.exists() else False:
            raise ValueError("analysis_already_prepared_no_overwrite")
        b.write(root / "context.json", context, immutable=True)
    return context


def context_for(root):
    root = pm.root_path(root)
    context = pm.checked_context(b.read(root / "context.json"))
    if context["record_id"] != root.name:
        raise ValueError("analysis_identity_mismatch")
    return context


def estimate(context):
    size = (
        len(pm.prompt_input(context).encode())
        + len(pm.PROMPT.encode())
        + len(json.dumps(pm.GlobalProposal.model_json_schema()).encode())
        + 1024
    )
    reserve = (
        b.dec(pm.CONFIG["input_bytes_max"])
        * b.dec(pm.CONFIG["input_usd_million_ceiling"])
        + b.dec(pm.CONFIG["options"]["max_output_tokens"])
        * b.dec(pm.CONFIG["output_usd_million_ceiling"])
    ) / 1000000
    approximate = (
        b.dec(size) / 4 * b.dec(pm.CONFIG["input_usd_million_2026"])
        + 2500 * b.dec(pm.CONFIG["output_usd_million_2026"])
    ) / 1000000
    return {
        "calls_max": 1,
        "http_attempts_max": 1,
        "usd_estimated": str(approximate),
        "usd_reserved": str(reserve),
        "input_bytes_estimated": size,
        "input_bytes_max": pm.CONFIG["input_bytes_max"],
        "output_tokens_max": pm.CONFIG["options"]["max_output_tokens"],
        "estimate_basis": "Planning: 4 UTF-8 bytes/input token, 2500 output incl thinking; not observed usage.",
        "reserve_basis": "Full input byte ceiling + output limit at higher announced rates; uncertain reservations never released.",
        "price_source": pm.CONFIG["price_source"],
        "price_checked": pm.CONFIG["price_checked"],
    }


def used_budget():
    """V1 and V2 reservations share one cap; none is ever released."""
    total = b.ZERO
    for module in (v1, pm):
        for path in (module.OUTPUT / "reservations").glob("*.json"):
            reserve = b.check_seal(b.read(path))
            if reserve["identity"] != module.IDENTITY:
                raise ValueError("reservation_identity_changed")
            total += b.dec(reserve["usd_reserved"])
    return total


def preflight(root, max_usd="0.25", *, at=None):
    root = pm.root_path(root)
    context = context_for(root)
    at = at or pm.now()
    budget = b.dec(max_usd)
    if not 0 < budget <= b.dec(pm.CONFIG["root_budget_usd"]):
        raise ValueError("invalid_budget")
    costs = estimate(context)
    paid = context["mode"] == "CONSULTATIVE_SANDBOX"
    total = b.dec(costs["usd_reserved"]) if paid else b.ZERO
    used = used_budget()
    origin = origin_state(context)
    errors = []
    if b.instant(at) >= b.instant(context["expires_at"]) or b.instant(at) < b.instant(
        context["created_at"]
    ):
        errors.append("context_expired_or_future")
    if costs["input_bytes_estimated"] > pm.CONFIG["input_bytes_max"]:
        errors.append("context_too_large")
    if b.instant(at).date().isoformat() > pm.CONFIG["price_valid_until"]:
        errors.append("price_contract_expired")
    if any(
        (root / p).exists()
        for p in ("claim.json", "private/calls.sqlite", "result.json", "failure.json")
    ):
        errors.append("already_claimed_replay_only")
    if total > budget or used + total > b.dec(pm.CONFIG["root_budget_usd"]):
        errors.append("budget_exceeded")
    if paid and origin != "VERIFIED":
        errors.append("radar_origin_missing_or_mismatch")
    report = {
        "schema_version": 2,
        "identity": pm.IDENTITY,
        "record_id": root.name,
        "context_sha256": context["sha256"],
        "snapshot_sha256": context["snapshot"]["sha256"],
        "opinion_hashes": {t: o["sha256"] for t, o in context["opinions"].items()},
        "contracts_sha256": context["contracts"]["sha256"],
        "mode": context["mode"],
        "radar_origin": origin,
        "expires_at": context["expires_at"],
        "max_usd": str(budget),
        "paid": paid,
        "usd_estimated": costs["usd_estimated"] if paid else "0",
        "usd_reserved": str(total),
        "budget_used": str(used),
        "budget_cap": pm.CONFIG["root_budget_usd"],
        "estimate": costs,
        "ready": not errors,
        "errors": errors,
        "execution_enabled": False,
    }
    return b.sealed({**report, "confirmation_token": b.digest(report)})


CASES = {
    "A": [],
    "B": [("PETR4", "BUY", "400")],
    "C": [("VALE3", "SELL", "100")],
    "D": [("PETR4", "SELL", "500"), ("WEGE3", "BUY", "250")],
    "F": [],
}
WHY = {
    "A": "Manter 100% em caixa. Sinais favoráveis com cautela técnica ficam em observação, sem operação, reserva ou dependência.",
    "B": "Comprar PETR4 com caixa liquidado disponível; demais ativos não selecionados.",
    "C": "Fixture inválida: venda de VALE3 sem custódia. Sinal VENDA não autoriza venda a descoberto.",
    "D": "Reduzir PETR4; a compra de WEGE3 depende do recebível D+2 da venda e aguarda a liquidação confirmada.",
    "F": "Fixture inválida: oportunidades de mercado declaradas como operações adiadas por liquidação (forma do incidente V1).",
}
HOLDINGS = {
    "D": (
        {
            t: {"quantity": q, "basis": basis}
            for t, q, basis in (
                ("PETR4", "1000", "40000.00"),
                ("VALE3", "500", "30000.00"),
                ("ITUB4", "700", "21000.00"),
            )
        },
        "9000.00",
    ),
}


class FakeGlobalPortfolioManager:
    """Scripted V2 responses for qualification; never Gemini, never a seal of a real run."""

    @staticmethod
    def propose(context, case="A"):
        state, calc = (
            context["snapshot"]["financial_state"],
            context["calculation_context"],
        )
        rid = context["record_id"]
        operations = []
        for i, (ticker, side, quantity) in enumerate(CASES[case]):
            op = v5_cli.make_operation(
                rid + "-" + str(i),
                ticker,
                side,
                quantity,
                calc,
                dependencies=[rid + "-0"] if case == "D" and side == "BUY" else [],
            )
            op["reasoning"] = WHY[case]
            operations.append(op)
        if case == "C":  # the projection itself refuses the uncovered sale
            targets = dict(context["current_weights"])
            cash = b.view(state)["cash_weight"]
        else:
            bridge = v5_cli.manual(state, calc, operations, "fixture-preview", WHY[case])
            targets = {
                t: bridge["target_weights"].get(t, "0") for t in context["opinions"]
            }
            cash = bridge["target_cash_weight"]
        reasons = {}
        for t, opinion in context["opinions"].items():
            metrics = context["verifiable_metrics"][t]
            reasons[t] = {
                "action": pm.expected_action(
                    state, t, targets[t], [o for o in operations if o["ticker"] == t]
                ),
                "reasoning": WHY[case],
                "opinion_sha256": opinion["sha256"],
                "evidence_codes": sorted(
                    {
                        e["code"]
                        for v in opinion["votes"]
                        for e in v["signal"].get("evidence", [])
                    }
                ),
                "cited_metrics": {
                    k: str(b.money(metrics[k]))
                    for k in ("rsi", "technical_confidence")
                    if k in metrics
                },
            }
        traded = {o["ticker"] for o in operations}
        return {
            "schema_version": 2,
            "identity": pm.IDENTITY,
            "record_id": rid,
            "decision_session": context["snapshot"]["valuation_session"],
            "created_at": context["created_at"],
            "expires_at": context["expires_at"],
            "snapshot_sha256": context["snapshot"]["sha256"],
            "context_sha256": context["sha256"],
            "summary": WHY[case],
            "current_weights": context["current_weights"],
            "target_weights": targets,
            "target_cash_weight": cash,
            "operations": operations,
            "asset_reasoning": reasons,
            "global_reasoning": WHY[case],
            "not_selected": [
                t for t, r in reasons.items() if r["action"] == "NOT_SELECTED"
            ],
            "settlement_deferred_operations": ["ITUB4", "PETR4"]
            if case == "F"
            else [o["operation_id"] for o in operations if o["dependencies"]],
            "watchlist_candidates": [
                {
                    "ticker": t,
                    "radar_signal": context["opinions"][t]["recommendation"],
                    "observation": "Sinal registrado no parecer; sem operação nesta proposta.",
                    "reassessment_condition": "Reavaliar com novo parecer e novo contexto em sessão futura.",
                }
                for t in ("ITUB4", "PETR4")
                if t in context["opinions"] and t not in traded and case in "AF"
            ],
            "risks": [
                "Custos e limites didáticos; nenhuma aprovação prospectiva.",
                "Recebíveis não financiam compras antes da confirmação.",
            ],
            "opinion_refs": {t: o["sha256"] for t, o in context["opinions"].items()},
        }


def run(
    root,
    token=None,
    max_usd="0.25",
    *,
    authorize_paid=False,
    replay=False,
    transport=None,
    fake_case="A",
    crash=None,
):
    root = pm.root_path(root)
    # ponytail: one local process lock across the V2 identity; multi-host needs a transaction store.
    with _exclusive_state_lock(root / "inference"), _exclusive_state_lock(
        pm.OUTPUT / "operation"
    ):
        context = context_for(root)
        synthetic = context["mode"] == "SYNTHETIC_DEMO"
        if replay:
            claim = b.check_seal(b.read(root / "claim.json"))
            if (
                claim["context_sha256"] != context["sha256"]
                or not (root / "private/calls.sqlite").exists()
            ):
                raise ValueError("missing_or_mismatched_claim_journal")
            if (root / "result.json").exists():
                return detail(root)
        else:
            report = preflight(root, max_usd)
            if not report["ready"] or report["confirmation_token"] != token:
                raise ValueError("preflight_or_confirmation_changed")
            if not synthetic and (
                authorize_paid is not True
                or not os.environ.get("GEMINI_API_KEY", "").strip()
            ):
                raise ValueError("new_explicit_paid_authorization_and_key_required")
            authorization = b.sealed(
                {
                    "identity": pm.IDENTITY,
                    "action": "AUTHORIZE_INFERENCE_ONLY",
                    "confirmation_token": token,
                    "context_sha256": context["sha256"],
                    "preflight": report,
                    "authorized_at": pm.now(),
                    "usd_reserved": report["usd_reserved"],
                    "paid": not synthetic,
                }
            )
            b.write(
                pm.OUTPUT / "reservations" / (token + ".json"),
                authorization,
                immutable=True,
            )
            b.write(root / "authorization.json", authorization, immutable=True)
            claim = b.sealed(
                {
                    "identity": pm.IDENTITY,
                    "record_id": root.name,
                    "context_sha256": context["sha256"],
                    "authorization_sha256": authorization["sha256"],
                    "created_at": pm.now(),
                }
            )
            b.write(root / "claim.json", claim, immutable=True)
            if crash == "after_claim":
                raise v1cli.SimulatedCrash("after_claim_before_callbank")
        reserved = b.read(root / "authorization.json")["usd_reserved"]
        private = root / "private"
        private.mkdir(parents=True, exist_ok=True)
        bank = CallBank(private / "calls.sqlite", context["sha256"], pm.IDENTITY)

        def gate():
            if context_for(root) != context:
                raise ValueError("context_changed_before_transport")
            if not replay and b.instant(pm.now()) >= b.instant(context["expires_at"]):
                raise ValueError("context_expired_before_transport")

        try:
            delegate = transport
            if synthetic and delegate is None:

                def delegate(*args):
                    return v1cli.fake_response(
                        FakeGlobalPortfolioManager.propose(context, fake_case)
                    )

            client = GlobalGeminiClient(
                bank,
                "L01",
                {"model": pm.CONFIG["model"], "retry_attempts": 1, "retry_base_delay": 0},
                fresh=not replay,
                gate=gate,
                transport=delegate,
                synthetic=synthetic,
                crash=crash,
            )
            if synthetic or replay:
                with no_network():
                    raw = asyncio.run(client.propose(context))
            else:
                raw = asyncio.run(client.propose(context))
            journal = bank.export("L01")
            record = json.loads(journal.splitlines()[0])["record"]
            usage = record.get("token_usage")
            cost = pm.usage_accounting(usage, claim["created_at"], synthetic, reserved)
            checked_at = (
                b.instant(record["started_at"])
                + timedelta(milliseconds=record["duration_ms"])
            ).isoformat()
            validation = pm.validate(context, raw, checked_at)
            result = b.sealed(
                {
                    "schema_version": 2,
                    "identity": pm.IDENTITY,
                    "record_id": root.name,
                    "mode": context["mode"],
                    "planner": "FAKE_GLOBAL_PM_NOT_GEMINI"
                    if synthetic
                    else "GEMINI_GLOBAL_PM",
                    "context_sha256": context["sha256"],
                    "claim_sha256": claim["sha256"],
                    "completed_at": pm.now(),
                    "validation_at": checked_at,
                    "status": validation["status"],
                    "response": raw,
                    "validation": validation,
                    "tokens": usage,
                    "cost_usd": cost["usd_estimated"],
                    "cost": cost,
                    "journal_sha256": hashlib.sha256(journal).hexdigest(),
                    "execution_enabled": False,
                    "portfolio_changed": False,
                }
            )
            b.write(private / "provider_journal.jsonl", journal, immutable=True)
            if crash == "before_result":
                raise v1cli.SimulatedCrash("after_journal_before_result")
            b.write(root / "result.json", result, immutable=True)
            return result
        except Exception as exc:
            row = bank.row("L01", 0)
            record = json.loads(row[4]) if row is not None and row[4] else {}
            failure = b.sealed(
                {
                    "identity": pm.IDENTITY,
                    "context_sha256": context["sha256"],
                    "status": "RECOVERY_REQUIRED"
                    if isinstance(exc, JournalIntegrityError)
                    or (
                        row is not None
                        and row[2] is None
                        and bank.attempt_count("L01", 0)
                    )
                    else "REJECTED_BY_VALIDATOR"
                    if record.get("error_type") == "ValidationError"
                    else "PROVIDER_FAILED",
                    "error_type": type(exc).__name__,
                    "errors": [
                        {"stage": "RESPONSE_SCHEMA", "code": "response_schema_invalid"}
                    ]
                    if record.get("error_type") == "ValidationError"
                    else [],
                    "tokens": record.get("token_usage"),
                    "cost": pm.usage_accounting(
                        record.get("token_usage"),
                        claim["created_at"],
                        synthetic,
                        reserved,
                    ),
                    "usd_reserved": reserved,
                    "automatic_retry": False,
                    "execution_enabled": False,
                }
            )
            b.write(root / "failure.json", failure)
            raise
        finally:
            bank.close()


def detail(root, *, at=None):
    """Sealed status never changes with time: expiry is reported beside it."""
    root = pm.root_path(root)
    if not (root / "context.json").exists():
        return {
            "identity": pm.IDENTITY,
            "status": "NO_PROPOSAL",
            "execution_enabled": False,
        }
    context = context_for(root)
    result = None
    if (root / "result.json").exists():
        result = b.check_seal(b.read(root / "result.json"))
        claim = b.check_seal(b.read(root / "claim.json"))
        authorization = b.check_seal(b.read(root / "authorization.json"))
        journal = root / "private/provider_journal.jsonl"
        synthetic = context["mode"] == "SYNTHETIC_DEMO"
        if (
            result["identity"] != pm.IDENTITY
            or result["mode"] != context["mode"]
            or claim["identity"] != pm.IDENTITY
            or claim["record_id"] != root.name
            or authorization["preflight"]["context_sha256"] != context["sha256"]
            or result["cost"]
            != pm.usage_accounting(
                result["tokens"],
                claim["created_at"],
                synthetic,
                authorization["usd_reserved"],
            )
            or result["cost_usd"] != result["cost"]["usd_estimated"]
            or result["context_sha256"] != context["sha256"]
            or result["claim_sha256"] != claim["sha256"]
            or claim["authorization_sha256"] != authorization["sha256"]
            or b.sha_file(journal) != result["journal_sha256"]
            or pm.validate(context, result["response"], result["validation_at"])
            != result["validation"]
        ):
            raise ValueError("global_pm_result_integrity")
        # Read-only SQLite verification: HTTP does not open a writable CallBank.
        with closing(
            sqlite3.connect(
                (root / "private/calls.sqlite").as_uri() + "?mode=ro", uri=True
            )
        ) as db:
            rows = db.execute(
                "SELECT raw,raw_sha,record,record_sha FROM calls WHERE slot='L01'"
            ).fetchall()
            call_count = db.execute("SELECT count(*) FROM calls").fetchone()[0]
            reservation_count = db.execute(
                "SELECT count FROM reservations WHERE slot='L01'"
            ).fetchone()[0]
        exported = [json.loads(line) for line in journal.read_bytes().splitlines()]
        if (
            len(rows) != 1
            or call_count != 1
            or reservation_count != 1
            or len(exported) != 1
            or json.loads(rows[0][2]) != exported[0]["record"]
            or rows[0][0] != base64.b64decode(exported[0]["raw_base64"])
            or result["response"] != exported[0]["record"]["validated_response"]
            or result["tokens"] != exported[0]["record"]["token_usage"]
            or any(
                hashlib.sha256(
                    data.encode() if isinstance(data, str) else data
                ).hexdigest()
                != sha
                for data, sha in ((rows[0][0], rows[0][1]), (rows[0][2], rows[0][3]))
            )
        ):
            raise ValueError("journal_export_or_response_mismatch")
        status = result["status"]
    elif (root / "failure.json").exists():
        status = b.check_seal(b.read(root / "failure.json"))["status"]
    elif (root / "claim.json").exists():
        status = (
            "INFERENCE_RUNNING"
            if v1cli.active_lock(root / "inference.lock")
            else "RECOVERY_REQUIRED"
        )
    else:
        status = "AWAITING_PREFLIGHT"
    return {
        "identity": pm.IDENTITY,
        "status": status,
        "expired": b.instant(at or pm.now()) >= b.instant(context["expires_at"]),
        "mode": context["mode"],
        "context": context,
        "result": result,
        "execution_enabled": False,
    }


def public_detail(root):
    """Same public shape as the V1 view, plus the V2 lists and error descriptions."""
    data = detail(root)
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
        "expired": data["expired"],
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
        "radar_origin": {"state": origin_state(c), **(c["radar_origin"] or {})},
        "estimate": estimate(c),
        "result": result,
        "execution_enabled": False,
        "simulation_note": "Simulação contábil em memória à marca conhecida. Projeção condicionada mantém preços hipotéticos, nunca preços futuros observados.",
    }


def qualify(prefix=QUALIFICATION):
    """Offline A-F (no E: veto needs official opinions; see tests) on synthetic demo-v4."""
    b.key(prefix)
    with no_network():
        opinions, histories = v1.load_opinions(
            b.ROOT / "data/radar/demo-v4", list(PRICES), DAY, "SYNTHETIC_DEMO", pm.now()
        )
        entries = []
        for case in CASES:
            child = pm.OUTPUT / (prefix + "-" + case.lower())
            holdings, cash = HOLDINGS.get(case, ({}, "100000.00"))
            snapshot = pm.make_snapshot(
                child.name, "SYNTHETIC_DEMO", DAY, PRICES, holdings, cash
            )
            context = prepare(
                child, snapshot, opinions, histories, ack_fixture_policy=True
            )
            result = run(child, preflight(child)["confirmation_token"], fake_case=case)
            if result["validation"]["valid"] != (case in "ABD"):
                raise ValueError("qualification_case_failed:" + case)
            entries.append(
                {
                    "case": case,
                    "root_id": child.name,
                    "summary": WHY[case],
                    "status": result["status"],
                    "errors": result["validation"]["errors"],
                    "result_sha256": result["sha256"],
                    "context_sha256": context["sha256"],
                }
            )
    index = b.sealed(
        {
            "identity": pm.IDENTITY,
            "schema_version": 2,
            "mode": "SYNTHETIC_DEMO",
            "contracts_sha256": pm.contracts()["sha256"],
            "cases": entries,
            "real_provider_calls": 0,
            "portfolio_writes": 0,
        }
    )
    b.write(pm.OUTPUT / prefix / "qualification.json", index, immutable=True)
    return index


def incident(root=None):
    """Read-only V1 reproduction + in-memory counterfactual; bytes checked before/after."""
    root = Path(root or v1.OUTPUT / INCIDENT)
    hashes = {name: b.sha_file(root / name) for name in INCIDENT_SHA256}
    if hashes != INCIDENT_SHA256:
        raise ValueError("incident_record_bytes_changed")
    result = b.check_seal(b.read(root / "result.json"))
    claim = b.check_seal(b.read(root / "claim.json"))
    authorization = b.check_seal(b.read(root / "authorization.json"))
    at_validation = v1cli.detail(root, at=result["validation_at"])
    context = at_validation["context"]
    replayed = v1.validate(context, result["response"], result["validation_at"])
    counterfactual = copy.deepcopy(result["response"])
    counterfactual.update(
        not_selected=sorted(context["opinions"]), deferred_opportunities=[]
    )
    alternative = v1.validate(context, counterfactual, result["validation_at"])
    financial = replayed["financial_validation"]
    report = {
        "identity": v1.IDENTITY,
        "record_id": root.name,
        "planner": result["planner"],
        "mode": result["mode"],
        "context_sha256": context["sha256"],
        "result_sha256": result["sha256"],
        "file_sha256": hashes,
        "status_at_validation": at_validation["status"],
        "status_now": v1cli.detail(root)["status"],
        "replayed_validation_identical": replayed == result["validation"],
        "errors": replayed["errors"],
        "financial_validation": {
            "valid": financial["valid"],
            "risk_projected": financial["risk_projected"]["status"],
            "operations": len(replayed["operations"]),
            "estimated_costs": financial["estimated_costs"],
            "projected_exposure": financial["projected"]["exposure"],
            "projected_cash_available": financial["projected"]["cash"]["available"],
            "sector_status": financial["risk_projected"]["sector_status"],
        },
        "declared_lists": {
            k: result["response"][k] for k in ("not_selected", "deferred_opportunities")
        },
        "derived_lists": {
            "not_selected": sorted(
                t
                for t, r in result["response"]["asset_reasoning"].items()
                if r["action"] == "NOT_SELECTED"
            ),
            "deferred_opportunities": sorted(
                o["ticker"] for o in financial["deferred_operations"]
            ),
        },
        "counterfactual": {
            "classification": "DIAGNOSTIC_IN_MEMORY_ONLY_NOT_A_CORRECTION_NOT_SEALED",
            "changed_fields": {
                "not_selected": counterfactual["not_selected"],
                "deferred_opportunities": [],
            },
            "status": alternative["status"],
            "errors": alternative["errors"],
        },
        "usage": pm.usage_accounting(
            result["tokens"], claim["created_at"], False, authorization["usd_reserved"]
        ),
        "v1_cost_usd_recorded": result["cost_usd"],
    }
    if {name: b.sha_file(root / name) for name in INCIDENT_SHA256} != INCIDENT_SHA256:
        raise ValueError("incident_record_bytes_changed")
    return report


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "command",
        choices=(
            "prepare",
            "preflight",
            "run",
            "replay",
            "status",
            "qualify",
            "incident",
        ),
    )
    parser.add_argument("--id", help="V2 record id (prepare default: new v74-<hex>)")
    parser.add_argument("--radar-run", help="registered Radar run (prepare)")
    parser.add_argument("--tickers", nargs="+", default=list(radar.EXAMPLES))
    parser.add_argument("--session", default=DAY)
    parser.add_argument("--capital", default="100000.00")
    parser.add_argument("--confirm-hypothetical", action="store_true")
    parser.add_argument("--ack-fixture-policy", action="store_true")
    parser.add_argument("--max-usd", default="0.25")
    parser.add_argument("--confirm")
    parser.add_argument("--authorize-paid", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.command == "run":
        result = run(
            pm.OUTPUT / args.id,
            args.confirm,
            args.max_usd,
            authorize_paid=args.authorize_paid,
        )
    else:
        with no_network():
            if args.command == "prepare":
                if not args.confirm_hypothetical or not args.radar_run:
                    parser.error(
                        "--confirm-hypothetical and --radar-run are required; this never creates an executable wallet"
                    )
                at = pm.now()
                mode = runs.run(args.radar_run)["mode"]
                opinions, histories, origin = radar_source(
                    args.radar_run, args.tickers, args.session, mode, at
                )
                record = args.id or "v74-" + uuid.uuid4().hex
                snapshot = pm.make_snapshot(
                    record,
                    mode,
                    args.session,
                    {
                        t: str(b.money(o["raw_close"]))
                        if mode == "SYNTHETIC_DEMO"
                        else o["raw_close"]
                        for t, o in opinions.items()
                    },
                    cash=args.capital,
                    at=at,
                )
                context = prepare(
                    pm.OUTPUT / record,
                    snapshot,
                    opinions,
                    histories,
                    at=at,
                    ack_fixture_policy=args.ack_fixture_policy,
                    radar_origin=origin,
                )
                result = {
                    "prepared": True,
                    "id": record,
                    "identity": pm.IDENTITY,
                    "context_sha256": context["sha256"],
                    "execution_enabled": False,
                }
            elif args.command == "qualify":
                result = qualify()
            elif args.command == "incident":
                result = incident()
            elif args.command == "replay":
                result = run(pm.OUTPUT / args.id, replay=True)
            elif args.command == "preflight":
                result = preflight(pm.OUTPUT / args.id, args.max_usd)
            else:
                result = detail(pm.OUTPUT / args.id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
