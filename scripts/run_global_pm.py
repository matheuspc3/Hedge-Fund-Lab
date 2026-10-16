"""Offline V6 demo/prepare/preflight/replay; paid inference requires a new explicit token."""

# ruff: noqa: E402 -- standalone CLI establishes repository imports.
import argparse
import asyncio
import base64
import hashlib
import json
import os
import sqlite3
import sys
from contextlib import closing
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parent),
]
import multiasset_global_pm as pm
import multiasset_portfolio as b
import multiasset_radar as radar
import run_multiasset_portfolio as v5_cli

from src.agents.llm_client import LLMCallMetadata, LLMClient
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
    DurableGeminiClient,
    JournalIntegrityError,
)


class SimulatedCrash(BaseException):
    """Qualification-only process death; never converts to a provider outcome."""


class GlobalGeminiClient(DurableGeminiClient):
    """Reuse durable native transport; H2's stage/schema gate stays untouched."""

    def __init__(self, *args, crash=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.crash = crash

    def begin_session(self, session):
        self.session = str(b.session(session))
        LLMClient.begin_session(self, session)

    def _transport(self, method, url, headers, body):
        if (
            len(json.dumps(body, ensure_ascii=False).encode()) + 1024
            > pm.CONFIG["input_bytes_max"]
        ):
            raise ValueError("request_exceeds_reserved_bound")
        if self.crash == "before_transport":
            raise SimulatedCrash("after_request_journal_before_transport")
        raw = super()._transport(method, url, headers, body)
        if self.crash == "after_envelope":
            raise SimulatedCrash("after_durable_envelope")
        return raw

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


def prepare(root, snapshot, opinions, histories, *, at=None, ack_fixture_policy=False):
    root = pm.root_path(root)
    context = pm.freeze(
        snapshot,
        opinions,
        histories,
        root.name,
        at,
        ack_fixture_policy=ack_fixture_policy,
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
    total = b.ZERO
    for path in (pm.OUTPUT / "reservations").glob("*.json"):
        reserve = b.check_seal(b.read(path))
        if reserve["identity"] != pm.IDENTITY:
            raise ValueError("reservation_identity_changed")
        total += b.dec(reserve["usd_reserved"])
    return total


def billing(usage, created_at, synthetic):
    if synthetic:
        return "0"
    if not usage or not all(
        type(usage.get(k)) is int and usage[k] >= 0
        for k in ("prompt_tokens", "completion_tokens", "thoughts_tokens")
    ):
        return None
    suffix = "2026" if b.instant(created_at).year <= 2026 else "ceiling"
    return str(
        (
            usage["prompt_tokens"] * b.dec(pm.CONFIG["input_usd_million_" + suffix])
            + (usage["completion_tokens"] + usage["thoughts_tokens"])
            * b.dec(pm.CONFIG["output_usd_million_" + suffix])
        )
        / 1000000
    )


def active_lock(path):
    if not path.exists():
        return False
    try:
        pid = int(path.read_text(encoding="utf-8"))
        if pid <= 0:
            return False
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            ctypes.windll.kernel32.OpenProcess.restype = wintypes.HANDLE
            ctypes.windll.kernel32.OpenProcess.argtypes = [
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            ]
            ctypes.windll.kernel32.GetExitCodeProcess.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.DWORD),
            ]
            ctypes.windll.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            try:
                code = ctypes.c_ulong()
                return (
                    bool(
                        ctypes.windll.kernel32.GetExitCodeProcess(
                            handle, ctypes.byref(code)
                        )
                    )
                    and code.value == 259
                )
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


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
    report = {
        "schema_version": 1,
        "identity": pm.IDENTITY,
        "record_id": root.name,
        "context_sha256": context["sha256"],
        "snapshot_sha256": context["snapshot"]["sha256"],
        "opinion_hashes": {t: o["sha256"] for t, o in context["opinions"].items()},
        "contracts_sha256": context["contracts"]["sha256"],
        "mode": context["mode"],
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


def fake_response(body):
    """Native envelope fixture, same parser/schema/journal as Gemini; never inference."""
    return json.dumps(
        {
            "candidates": [
                {
                    "content": {"parts": [{"text": json.dumps(body)}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 1500,
                "candidatesTokenCount": 700,
                "thoughtsTokenCount": 50,
                "totalTokenCount": 2250,
            },
            "modelVersion": "SYNTHETIC_NOT_GEMINI",
            "responseId": "offline-fixture",
        }
    ).encode()


class FakeGlobalPortfolioManager:
    """Scripted response examples, distinct from V5 DEMO_RULE_BASED and real Gemini."""

    @staticmethod
    def propose(context, case="A"):
        state, calc = (
            context["snapshot"]["financial_state"],
            context["calculation_context"],
        )
        actions = {
            "A": [
                ("PETR4", "BUY", "400"),
                ("VALE3", "BUY", "300"),
                ("ITUB4", "BUY", "400"),
            ],
            "B": [("PETR4", "SELL", "300")],
            "C": [("PETR4", "SELL", "100")],
            "D": [("PETR4", "SELL", "500"), ("WEGE3", "BUY", "250")],
            "E": [],
            "F": [],
        }
        why = {
            "A": "Iniciar três posições e preservar caixa. Cinco sinais favoráveis não obrigam cinco compras.",
            "B": "Reduzir PETR4: concentração atual de 50% excede o teto didático de 40%, apesar do parecer favorável.",
            "C": "Reduzir PETR4 e manter o recebível; nenhuma compra substituta. Caixa só após confirmação.",
            "D": "Caixa disponível de R$ 9.000 não financia WEGE3. Reduzir PETR4 e aguardar liquidação antes de considerar a compra.",
            "E": "Manter posições e caixa; sinais favoráveis não justificam obrigatoriamente nova operação.",
            "F": "Fixture inválida de LLM: pesos somam 120%, sem efeito financeiro.",
        }
        operations = []
        for i, (ticker, side, quantity) in enumerate(actions[case]):
            op = v5_cli.make_operation(
                context["record_id"] + "-" + str(i),
                ticker,
                side,
                quantity,
                calc,
                dependencies=[context["record_id"] + "-0"]
                if case == "D" and side == "BUY"
                else [],
            )
            op["reasoning"] = why[case]
            operations.append(op)
        # Derive fixture targets from a pure V5 projection, never change LLM targets in validation.
        bridge = v5_cli.manual(state, calc, operations, "fixture-preview", why[case])
        targets = {t: bridge["target_weights"].get(t, "0") for t in context["opinions"]}
        reasons = {}
        for t, opinion in context["opinions"].items():
            ops = [o for o in operations if o["ticker"] == t]
            action = "HOLD" if b.dec(targets[t]) else "NOT_SELECTED"
            if ops:
                op = ops[0]
                held = b.dec(state["positions"].get(t, b.position())["quantity"])
                action = (
                    (
                        "WAIT_SETTLEMENT"
                        if op["dependencies"]
                        else "INCREASE"
                        if held
                        else "BUY"
                    )
                    if op["side"] == "BUY"
                    else "EXIT"
                    if b.dec(op["quantity"]) == held
                    else "REDUCE"
                )
            reasons[t] = {
                "action": action,
                "reasoning": why[case]
                if ops
                else "Parecer favorável considerado; preservar posição/caixa e não ampliar o universo investido nesta proposta.",
                "opinion_sha256": opinion["sha256"],
                "evidence_codes": sorted(
                    {
                        e["code"]
                        for v in opinion["votes"]
                        for e in v["signal"].get("evidence", [])
                    }
                ),
            }
        if case == "F":
            targets = {t: "0.20" for t in targets}
        return {
            "schema_version": 1,
            "identity": pm.IDENTITY,
            "record_id": context["record_id"],
            "decision_session": context["snapshot"]["valuation_session"],
            "created_at": context["created_at"],
            "expires_at": context["expires_at"],
            "snapshot_sha256": context["snapshot"]["sha256"],
            "context_sha256": context["sha256"],
            "summary": why[case],
            "current_weights": context["current_weights"],
            "target_weights": targets,
            "target_cash_weight": "0.20" if case == "F" else bridge["target_cash_weight"],
            "operations": operations,
            "asset_reasoning": reasons,
            "global_reasoning": why[case],
            "not_selected": [
                t for t, r in reasons.items() if r["action"] == "NOT_SELECTED"
            ],
            "deferred_opportunities": [
                o["ticker"] for o in operations if o["dependencies"]
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
    # ponytail: one local process lock across the V6 identity; multi-host needs a transaction store.
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
                raise SimulatedCrash("after_claim_before_callbank")
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
                    return fake_response(
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
            records = [json.loads(line)["record"] for line in journal.splitlines()]
            usage = records[0].get("token_usage")
            cost = billing(usage, claim["created_at"], synthetic)
            record = records[0]
            checked_at = (
                b.instant(record["started_at"])
                + timedelta(milliseconds=record["duration_ms"])
            ).isoformat()
            validation = pm.validate(context, raw, checked_at)
            result = b.sealed(
                {
                    "schema_version": 1,
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
                    "cost_usd": cost,
                    "cost_basis": "synthetic zero"
                    if synthetic
                    else "provider tokens incl thinking; estimate, not invoice; null if incomplete",
                    "journal_sha256": hashlib.sha256(journal).hexdigest(),
                    "execution_enabled": False,
                    "portfolio_changed": False,
                }
            )
            b.write(private / "provider_journal.jsonl", journal, immutable=True)
            if crash == "before_result":
                raise SimulatedCrash("after_journal_before_result")
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
                    "cost_usd": billing(
                        record.get("token_usage"), claim["created_at"], synthetic
                    ),
                    "usd_reserved": b.read(root / "authorization.json")["usd_reserved"],
                    "automatic_retry": False,
                    "execution_enabled": False,
                }
            )
            b.write(root / "failure.json", failure)
            raise
        finally:
            bank.close()


def detail(root, *, at=None):
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
        if (
            result["identity"] != pm.IDENTITY
            or result["mode"] != context["mode"]
            or claim["identity"] != pm.IDENTITY
            or claim["record_id"] != root.name
            or authorization["preflight"]["context_sha256"] != context["sha256"]
            or result["cost_usd"]
            != billing(
                result["tokens"], claim["created_at"], context["mode"] == "SYNTHETIC_DEMO"
            )
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
        ):
            raise ValueError("journal_export_or_response_mismatch")
        if len(rows) != 1 or any(
            data is None
            or hashlib.sha256(
                data.encode() if isinstance(data, str) else data
            ).hexdigest()
            != sha
            for data, sha in ((rows[0][0], rows[0][1]), (rows[0][2], rows[0][3]))
        ):
            raise ValueError("private_journal_integrity")
        status = result["status"]
    elif (root / "failure.json").exists():
        status = b.check_seal(b.read(root / "failure.json"))["status"]
    elif (root / "claim.json").exists():
        status = (
            "INFERENCE_RUNNING"
            if active_lock(root / "inference.lock")
            else "RECOVERY_REQUIRED"
        )
    else:
        status = "AWAITING_PREFLIGHT"
    if result and b.instant(at or pm.now()) >= b.instant(context["expires_at"]):
        status = "PROPOSAL_EXPIRED"
    return {
        "identity": pm.IDENTITY,
        "status": status,
        "mode": context["mode"],
        "context": context,
        "result": result,
        "execution_enabled": False,
    }


def demo(root=pm.DEFAULT_ROOT):
    root = pm.root_path(root)
    opinions, histories = pm.load_opinions(
        b.ROOT / "data/radar/demo-v4",
        list(radar.EXAMPLES),
        "2026-10-09",
        "SYNTHETIC_DEMO",
        pm.now(),
    )
    prices = {
        "PETR4": "40.00",
        "VALE3": "60.00",
        "ITUB4": "30.00",
        "WEGE3": "50.00",
        "BBAS3": "25.00",
    }
    entries = []
    for case in "ABCDEF":
        child = pm.OUTPUT / (root.name + "-" + case.lower())
        holdings, cash = {}, "100000.00"
        if case == "B":
            holdings, cash = (
                {"PETR4": {"quantity": "1250", "basis": "50000.00"}},
                "50000.00",
            )
        elif case in "CE":
            holdings, cash = (
                {"PETR4": {"quantity": "500", "basis": "20000.00"}},
                "80000.00",
            )
        elif case == "D":
            holdings, cash = (
                {
                    t: {"quantity": q, "basis": basis}
                    for t, q, basis in (
                        ("PETR4", "1000", "40000.00"),
                        ("VALE3", "500", "30000.00"),
                        ("ITUB4", "700", "21000.00"),
                    )
                },
                "9000.00",
            )
        snapshot = pm.make_snapshot(
            child.name, "SYNTHETIC_DEMO", "2026-10-09", prices, holdings, cash
        )
        context = prepare(child, snapshot, opinions, histories, ack_fixture_policy=True)
        report = preflight(child)
        result = run(child, report["confirmation_token"], fake_case=case)
        if result["validation"]["valid"] != (case != "F"):
            raise ValueError("demo_financial_qualification_failed:" + case)
        entries.append(
            {
                "case": case,
                "root_id": child.name,
                "summary": result["response"]["summary"],
                "valid": result["validation"]["valid"],
                "result_sha256": result["sha256"],
                "context_sha256": context["sha256"],
            }
        )
    index = b.sealed(
        {
            "identity": pm.IDENTITY,
            "schema_version": 1,
            "mode": "SYNTHETIC_DEMO",
            "cases": entries,
            "real_provider_calls": 0,
            "portfolio_writes": 0,
        }
    )
    b.write(root / "demo.json", index, immutable=True)
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("demo", "prepare", "preflight", "run", "replay", "status")
    )
    parser.add_argument("--root", type=Path, default=pm.DEFAULT_ROOT)
    parser.add_argument("--radar-root", type=Path, default=radar.OUTPUT)
    parser.add_argument("--tickers", nargs="+", default=list(radar.EXAMPLES))
    parser.add_argument("--session", default="2026-10-09")
    parser.add_argument("--mode", choices=pm.MODES, default="CONSULTATIVE_SANDBOX")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--capital", default="100000.00")
    parser.add_argument("--confirm-hypothetical", action="store_true")
    parser.add_argument("--ack-fixture-policy", action="store_true")
    parser.add_argument("--max-usd", default="0.25")
    parser.add_argument("--confirm")
    parser.add_argument("--authorize-paid", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        if not args.confirm_hypothetical:
            parser.error(
                "--confirm-hypothetical is required; this never creates an executable wallet"
            )
        with no_network():
            at = pm.now()
            opinions, histories = pm.load_opinions(
                args.radar_root, args.tickers, args.session, args.mode, at
            )
            prices = {
                t: str(b.money(o["raw_close"]))
                if args.mode == "SYNTHETIC_DEMO"
                else o["raw_close"]
                for t, o in opinions.items()
            }
            if args.snapshot:
                snapshot = b.read(args.snapshot)
                if snapshot["mode"] != args.mode:
                    raise ValueError("snapshot_mode_mismatch")
            else:
                snapshot = pm.make_snapshot(
                    pm.root_path(args.root).name,
                    args.mode,
                    args.session,
                    prices,
                    cash=args.capital,
                    at=at,
                )
            result = prepare(
                args.root,
                snapshot,
                opinions,
                histories,
                at=at,
                ack_fixture_policy=args.ack_fixture_policy,
            )
        print(
            json.dumps(
                {
                    "prepared": True,
                    "context_sha256": result["sha256"],
                    "execution_enabled": False,
                },
                indent=2,
            )
        )
        return
    if args.command == "run":
        result = run(
            args.root, args.confirm, args.max_usd, authorize_paid=args.authorize_paid
        )
    else:
        with no_network():
            if args.command == "demo":
                result = demo(args.root)
            elif args.command == "replay":
                result = run(args.root, replay=True)
            elif args.command == "preflight":
                result = preflight(args.root, args.max_usd)
            else:
                result = detail(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
