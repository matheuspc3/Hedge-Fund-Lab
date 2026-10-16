"""V7 aggregates existing authorities; only explicit global commands can write.

Never calls reconciliation, order approval, market downloads or shell commands.
"""

import math
import os
import re
import sqlite3
import threading
from pathlib import Path

import forward_api as forward
import forward_jobs
import global_pm_api as global_api
import h2_api
import market_api
import network_scope
import portfolio_api
import radar_api
import radar_runs as runs
import run_global_pm_v2 as cli2

b, pm, cli, radar = global_api.b, global_api.pm, global_api.cli, global_api.radar
committee_outcome = runs.committee_outcome
ROOT = forward.ROOT
OPERATIONS = ROOT / "data/platform/v7"
RADAR_DISPATCH_LOCK = threading.RLock()
ID = re.compile(r"v7-[0-9a-f]{32}")
#: Global PM V2 records are read-only here; prepare/preflight/run are CLI-only (V7.4).
ID2 = re.compile(r"v74-[a-z0-9-]{1,64}")
pm2 = cli2.pm
FIELDS = {
    "prepare": {
        "id",
        "mode",
        "session",
        "tickers",
        "capital",
        "confirm_hypothetical",
        "ack_fixture_policy",
    },
    "run": {"id", "max_usd", "confirmation_token", "authorize_paid", "confirm"},
    "replay": {"id", "confirm"},
}
#: V7.3: a prepare from a registered Radar run names it and the opinions it saw.
RUN_PREPARE = FIELDS["prepare"] | {"radar_run", "opinion_hashes"}
COMMON = {
    "NO_PROPOSAL": "NOT_PREPARED",
    "AWAITING_PREFLIGHT": "PREPARED",
    "READY_FOR_INFERENCE": "READY",
    "DECIDED": "DECISION_EXISTS",
    "INFERENCE_RUNNING": "RUNNING",
    "RUNNING": "RUNNING",
    "COMPLETE": "COMPLETED",
    "COMPLETED": "COMPLETED",
    "VALID_PROPOSAL": "COMPLETED",
    "PROPOSALS_AVAILABLE": "COMPLETED",
    "PREPARED": "PREPARED",
    "NOT_PREPARED": "NOT_PREPARED",
    "READY": "READY",
    "DECISION_EXISTS": "DECISION_EXISTS",
    "FAILED": "FAILED",
    "PROVIDER_FAILED": "FAILED",
    "RECOVERY_REQUIRED": "RECOVERY_REQUIRED",
    "FAILED_REPLAY_ONLY": "RECOVERY_REQUIRED",
    "INTERRUPTED_REVIEW_LOCK_AND_REPLAY": "RECOVERY_REQUIRED",
    "PROPOSAL_EXPIRED": "EXPIRED",
    "EXPIRED": "EXPIRED",
    "EXPIRADA": "EXPIRED",
    "AGUARDANDO_APROVACAO": "PREPARED",
    "APROVADA": "READY",
    "AJUSTADA_CONCENTRACAO": "READY",
    "PENDENTE_ABERTURA": "READY",
    "EXECUTADA": "COMPLETED",
    "BLOCKED": "BLOCKED",
    "REJECTED_BY_VALIDATOR": "BLOCKED",
    "INTEGRITY_ERROR": "BLOCKED",
    "INSUFFICIENT_DATA": "BLOCKED",
    "REJEITADA": "BLOCKED",
    "CANCELADA": "BLOCKED",
}


def visual_state(native):
    return {"native_state": native, "state": COMMON.get(native, "BLOCKED")}


def analysis_root(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("invalid_analysis_id")
    return pm.root_path(pm.OUTPUT / value)


def source_root(mode):
    if mode not in pm.MODES:
        raise ValueError("invalid_analysis_mode")
    return (
        global_api.SYNTHETIC_RADAR
        if mode == "SYNTHETIC_DEMO"
        else global_api.OFFICIAL_RADAR
    )


def attempt(call):
    try:
        return {"available": True, "data": call()}
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError, sqlite3.Error):
        return {
            "available": False,
            "state": "BLOCKED",
            "error": "local_record_unavailable_or_integrity_failed",
        }


def forward_integrity(root):
    """Check recorded references, without opening any reserved scientific data."""
    radar.frozen_sources()
    manifest = forward.fwd.CANDIDATE.with_suffix(".sha256").read_text().strip()
    state = forward.fwd.load_state(root, manifest)
    if not (root / "state.json").exists():
        return {"ok": False, "state": "NOT_PREPARED", "scope": "recorded_references"}
    count = 0
    for entry in state["decisions"]:
        folder = root / "sessions" / forward.session_name(entry["session"])
        d = forward.read(folder / "decision.json")
        if not d or b.sha_file(folder / "decision.json") != entry["decision_sha256"]:
            raise ValueError("original_decision_changed")
        data = forward.read(folder / "input.json")
        if (
            b.sha_file(folder / "input.json") != d["input_sha256"]
            or b.sha_file(folder / "bars.csv") != data["history"]["sha256"]
            or b.sha_file(folder / "llm_trace.jsonl") != d["llm_trace_sha256"]
            or b.sha_file(folder / "provider_journal.jsonl")
            != d["provider_journal_sha256"]
            or d["manifest_sha256"] != manifest
            or d["participant_sha256"] != forward.fwd.PARTICIPANT_SHA256
        ):
            raise ValueError("original_references_changed")
        count += 1
    return {
        "ok": True,
        "decisions": count,
        "manifest_sha256": manifest,
        "scope": "identity_and_recorded_input_bars_trace_journal_hashes",
    }


PREPARE_COMMAND = (
    ".venv/Scripts/python.exe -B scripts/radar_corporate_events.py prepare "
    "--session {day} --tickers {tickers}"
)
CORPORATE_ERRORS = ("split-like mismatch", "corporate event")
RUN_PREPARE_COMMAND = (
    ".venv/Scripts/python.exe -B scripts/radar_runs.py prepare --run {run}"
)


OUTCOME_ACTIONS = {
    "COMMITTEE_COMPLETED": "Parecer oficial completo e íntegro.",
    "RECOVERABLE_OFFLINE": "Envelopes gravados: recuperar somente offline (replay, sem nova chamada).",
    "COMMITTEE_PARTIAL": "Comitê parcial: votos gravados insuficientes; não repetir chamadas deste claim.",
    "UNCERTAIN_CALLS": "Chamada de resultado incerto: não repetir; conferir uso no console do provedor.",
    "NO_RECOVERABLE_ENVELOPE": "Incidente imutável: nenhuma resposta gravada, replay não reconstrói. Nova "
    "tentativa só em identidade operacional separada, com orçamento e autorização novos.",
}


def radar_job(root=None):
    """``radar_api.job()`` plus committee outcomes: a finished job is not a successful batch."""
    root = Path(root or radar_api.ROOT)
    if root.resolve() == Path(radar_api.ROOT).resolve():
        job = radar_api.job()
    else:  # another run: its job.json is history; only the runner can be RUNNING
        path = root / "job.json"
        job = radar.read(path) if path.exists() else None
        if job and job["status"] == "RUNNING":
            job = {**job, "status": "INTERRUPTED_REVIEW_LOCK_AND_REPLAY"}
    if not job or job.get("command") != "run" or job.get("status") != "COMPLETED":
        return job
    start, end = b.instant(job["started_at"]), b.instant(job["finished_at"])
    states = {}
    for item in job.get("items", []):
        ticker = radar.tickers([item["ticker"]])[0]
        claims = [
            path
            for path in (root / "analyses" / ticker).glob("*/claim.json")
            if start <= b.instant(radar.read(path)["created_at"]) <= end
        ]
        outcome = (
            committee_outcome(root, ticker, claims[-1].parent.name) if claims else None
        )
        states[ticker] = outcome["state"] if outcome else "UNKNOWN"
    done = sum(state == "COMMITTEE_COMPLETED" for state in states.values())
    return {
        **job,
        "outcome": {
            "state": "COMPLETED"
            if done == len(states)
            else "PARTIAL"
            if done
            else "FAILED",
            "committees_completed": done,
            "committees": len(states),
            "states": states,
            "summary": f"Infraestrutura concluída · {done}/{len(states)} comitês concluídos",
        },
    }


def input_facts(root, ticker, day):
    """Frozen-input projection; ``checked_input`` raises on any integrity drift."""
    data = radar.checked_input(root, ticker, day)
    corporate = data["source"].get("corporate_events") or {}
    volatility = data["risk_metrics"]["asset_volatility_21"]
    limit = data["manifest"]["risk"]["max_asset_volatility"]
    return {
        "input_sha256": radar.sha_file(
            radar.folder_for(root, ticker, day) / "input.json"
        ),
        "prepared_at": data["prepared_at"],
        "mode": data["manifest"]["mode"],
        "manifest_sha256": data["manifest_sha256"],
        "bars": data["history"]["bars"],
        "history_start": data["history"]["start"],
        "bars_sha256": data["history"]["sha256"],
        "source": data["source"]["name"],
        "cotahist_sha256": data["source"].get("cotahist_sha256"),
        "raw_close": data["raw_bar"]["fechamento"],
        "adjusted_close": data["adjusted_close"],
        "normalization": {
            # An original-extractor input passed the split guard: no event in window.
            "state": "NORMALIZED_CONFIRMED_EVENT"
            if corporate.get("events")
            else "NO_NORMALIZATION_NEEDED",
            "extractor": corporate.get("normalization", "ORIGINAL_V4_GUARD_PASSED"),
            "events": corporate.get("events", []),
        },
        "risk": {
            "asset_volatility_21": volatility,
            "limit": limit,
            "restricted": volatility > limit,
        },
    }


def run_selection(mode, day, symbols, root):
    """``global_pm_api.selection`` over an explicit run root (that file is pinned by the
    V7 preservation baseline, so it cannot take the root as a parameter)."""
    legacy = (
        global_api.SYNTHETIC_RADAR
        if mode == "SYNTHETIC_DEMO"
        else global_api.OFFICIAL_RADAR
    )
    if Path(root).resolve() == Path(legacy).resolve():
        return global_api.selection(mode, day, symbols)
    # ponytail: mirrors global_pm_api.selection's eligibility and cost preview; the
    # opinion check itself is the sealed pm.load_opinions. Upgrade path: a root
    # parameter in global_pm_api.selection when that baseline is next renewed.
    if mode not in pm.MODES:
        raise ValueError("invalid_analysis_mode")
    radar.session(day)
    symbols = radar.tickers(symbols, empty=False)
    items = []
    for symbol in symbols:
        try:
            o = pm.load_opinions(root, [symbol], day, mode, pm.now())[0][symbol]
            items.append(
                {
                    "ticker": symbol,
                    "status": "ELIGIBLE",
                    "opinion_sha256": o["sha256"],
                    "recommendation": o["recommendation"],
                    "generated_at": o["generated_at"],
                    "synthetic": mode == "SYNTHETIC_DEMO",
                }
            )
        except (ValueError, KeyError, OSError, TypeError):
            items.append(
                {
                    "ticker": symbol,
                    "status": "MISSING_OR_INELIGIBLE",
                    "reason": "Parecer completo e íntegro desta execução/sessão necessário; nada foi gerado.",
                }
            )
    missing = [i["ticker"] for i in items if i["status"] != "ELIGIBLE"]
    paid = mode == "CONSULTATIVE_SANDBOX"
    asset = radar.estimate({"manifest": {"mode": "live"}})
    ceiling = (
        b.dec(pm.CONFIG["input_bytes_max"])
        * b.dec(pm.CONFIG["input_usd_million_ceiling"])
        + b.dec(pm.CONFIG["options"]["max_output_tokens"])
        * b.dec(pm.CONFIG["output_usd_million_ceiling"])
    ) / 1000000
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
            "usd_estimated": str(b.dec(str(asset["usd_estimated"])) * len(missing))
            if paid
            else "0",
            "usd_reserved": str(b.dec(str(asset["usd_reserved"])) * len(missing))
            if paid
            else "0",
            "planning_only": True,
        },
        "global_pm_cost_preview": {
            "authorization_scope": "GLOBAL_PM_ONLY_SEPARATE",
            "calls_max": 1,
            "usd_reserved_ceiling": str(ceiling) if paid else "0",
            "usd_estimated": None,
            "estimate_note": "Estimativa depende do contexto congelado; nenhum custo autorizado nesta consulta.",
        },
        "execution_enabled": False,
    }


def radar_readiness(day, symbols, root=None, mode="CONSULTATIVE_SANDBOX", run=None):
    """Per official ticker: input, normalization, risk restriction, opinion and next step."""
    root = root or global_api.OFFICIAL_RADAR
    selection = run_selection(mode, day, symbols, root)
    job = radar_job(root) or {}
    preparing = job.get("command") == "prepare" and job.get("status") == "RUNNING"
    last = root / "last_prepare.json"
    # last_prepare.json only reports the latest prepare call; inputs are the authority.
    blocked = {
        i["ticker"]: i.get("error", "")
        for i in (radar.read(last)["items"] if last.exists() else [])
        if i["session"] == day and i["status"] == "BLOCKED"
    }
    try:
        preflight = radar.preflight(selection["selected"], root, day=day)
    except (ValueError, OSError) as exc:
        preflight = {"ready": False, "items": [], "error": str(exc)}
    checks = {i["ticker"]: i for i in preflight["items"]}
    command = (
        RUN_PREPARE_COMMAND.format(run=run)
        if run
        else PREPARE_COMMAND.format(day=day, tickers=" ".join(selection["selected"]))
    )
    items = []
    for entry in selection["items"]:
        ticker = entry["ticker"]
        check = checks.get(ticker, {})
        item = {
            "ticker": ticker,
            "session": day,
            "input": None,
            "opinion": "NONE",
            "risk_verdict": None,
            "preflight": "READY" if check.get("ready") else check.get("error"),
        }
        if not (radar.folder_for(root, ticker, day) / "input.json").exists():
            if preparing:
                item.update(
                    state="PREPARING",
                    input_state="PREPARING",
                    preflight="PREPARING",
                    error=None,
                    action="Preparo em andamento; aguarde o resultado desta tentativa no Radar.",
                )
                items.append(item)
                continue
            error = blocked.get(ticker)
            corporate = bool(error) and any(k in error for k in CORPORATE_ERRORS)
            item.update(
                preflight="INPUT_REQUIRED",
                state="INPUT_BLOCKED" if error else "NO_INPUT",
                input_state="UNRESOLVED_DIVERGENCE"
                if corporate
                else "BLOCKED_DATA"
                if error
                else "PREPARATION_REQUIRED",
                error=error,
                action="Fator de ajuste Yahoo indisponível para a sessão. Aguarde a fonte "
                "fornecer uma linha válida e prepare novamente; preços RAW B3 sozinhos "
                "não completam o histórico ajustado dos agentes."
                if error and "no adjustment factor" in error
                else "Preparar dados em /radar (botão 1) ou pelo CLI equivalente; "
                "gratuito, grava inputs, sem Gemini."
                + (
                    " O bloqueio registrado é anterior ou não confirmado pela B3: se "
                    "persistir após o preparo normalizado, o ativo fica fora."
                    if corporate
                    else ""
                ),
            )
            items.append(item)
            continue
        try:
            item["input"] = input_facts(root, ticker, day)
            detail = radar.detail(ticker, day, root)
        except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
            item.update(
                state="INTEGRITY_ERROR",
                input_state="INTEGRITY_ERROR",
                error=str(exc),
                action="Input divergente da identidade Radar atual; não reutilizar nem sobrescrever.",
            )
            items.append(item)
            continue
        native = detail["status"]
        outcome = committee_outcome(root, ticker, day)
        item.update(
            outcome=outcome,
            input_state="FROZEN",
            opinion={
                "PREPARED": "PENDING",
                "COMPLETED": "COMPLETED",
                "FAILED_REPLAY_ONLY": "RECOVERY_REQUIRED",
            }.get(native, native),
            risk_verdict=(detail.get("risk") or {}).get("verdict"),
        )
        risk = item["input"]["risk"]
        restriction = (
            f" Restrição de risco: volatilidade 21d {risk['asset_volatility_21']:.3f} acima do"
            f" limite {risk['limit']}; o Risk vetará por regra determinística (parecer completo,"
            " recomendação MANTER)."
            if risk["restricted"] and native != "COMPLETED"
            else ""
        )
        if entry["status"] == "ELIGIBLE":
            item.update(state="ELIGIBLE", action="Parecer oficial completo e íntegro.")
        else:
            item.update(
                state={
                    "PREPARED": "AWAITING_RADAR_AUTHORIZATION",
                    "FAILED_REPLAY_ONLY": "RECOVERY_REQUIRED",
                }.get(native, "INELIGIBLE"),
                action={
                    "PREPARED": "Input congelado; parecer pendente: preflight Radar e "
                    "autorização paga própria do lote." + restriction,
                    "FAILED_REPLAY_ONLY": OUTCOME_ACTIONS[outcome["state"]]
                    if outcome
                    else "Recuperar somente offline; nunca repetir a chamada.",
                }.get(
                    native, "Parecer incompatível com sessão/fonte; consultar detalhe."
                ),
            )
        items.append(item)
    inputs = sum(i["input_state"] == "FROZEN" for i in items)
    opinions = len(items) - len(selection["missing"])
    return {
        "session": day,
        "items": items,
        "missing": selection["missing"],
        "inputs_ready": inputs,
        "opinions_complete": opinions,
        "summary": f"{inputs} inputs prontos; {opinions}/{len(items)} pareceres oficiais",
        "prepare_command": command,
        "radar_preflight": {
            k: preflight.get(k)
            for k in (
                "ready",
                "usd_reserved",
                "usd_estimated",
                "global_budget_used",
                "error",
            )
        },
        "gemini_pending": sorted(
            {
                i["preflight"]
                for i in items
                if i["input_state"] == "FROZEN" and i["preflight"] not in (None, "READY")
            }
        ),
        "global_pm_ready": not selection["missing"],
        "provider_calls": 0,
    }


def global_records():
    result = []
    for path in sorted(
        [*pm.OUTPUT.glob("v7-*/context.json"), *pm2.OUTPUT.glob("v74-*/context.json")],
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    ):
        v2 = ID2.fullmatch(path.parent.name)
        if not v2 and not ID.fullmatch(path.parent.name):
            continue
        detail = cli2.public_detail if v2 else global_api.public_detail
        entry = attempt(lambda path=path, detail=detail: detail(path.parent))
        if entry["available"]:
            d = entry["data"]
            result.append(
                {
                    "id": path.parent.name,
                    **visual_state(d["status"]),
                    "identity": d["identity"],
                    "validation_status": (d["result"] or {}).get("status"),
                    "mode": d["mode"],
                    "created_at": d["created_at"],
                    "expires_at": d["expires_at"],
                    "context_sha256": d["context_sha256"],
                    "cost_usd": (d["result"] or {}).get("cost_usd"),
                    "href": "/portfolio?analysis=" + path.parent.name,
                }
            )
        else:
            result.append(
                {
                    "id": path.parent.name,
                    **visual_state("INTEGRITY_ERROR"),
                    "error": entry["error"],
                }
            )
    return result


def runner():
    """Registered run the Radar API worker writes to, or None: then prepare/run are refused."""
    try:
        return runs.run_for_root(radar_api.ROOT, runs.load())
    except ValueError:
        return None


def radar_post_gate(command, payload, headers):
    """Server-side gate before the sealed ``radar_api.post``: the browser cannot pick a
    root, a stale page cannot write to another run, a paid batch needs the run's budget
    gate and a qualified (scoped) network guard."""
    if command == "preflight":
        return None  # read-only and sealed
    if command == "universe":
        # Operator selection file; refused on the preserved incident root in any case.
        owner = runner()
        if (owner and not owner["accepts_new_calls"]) or (
            not owner
            and Path(radar_api.ROOT).resolve() == global_api.OFFICIAL_RADAR.resolve()
        ):
            raise ValueError("run_not_accepting_new_calls")
        return None
    registry = runs.load()
    owner = runs.run_for_root(radar_api.ROOT, registry)
    if owner is None:
        raise ValueError("runner_not_a_registered_run")
    if headers != [owner["id"]]:
        raise ValueError("radar_run_header_mismatch_reload_page")
    if (
        not isinstance(payload, dict)
        or "tickers" not in payload
        or "session" not in payload
    ):
        raise ValueError("invalid_payload")
    tickers = radar.tickers(payload["tickers"], empty=False)
    report = None
    if command == "prepare" and payload.get("mode") != runs.MODES[owner["mode"]]:
        raise ValueError("synthetic_official_mix")
    if command == "run":
        if not network_scope.qualified():
            raise ValueError("network_isolation_not_qualified_restart_server")
        report = radar.preflight(
            tickers,
            runs.root_of(owner),
            day=payload["session"],
            max_usd=payload.get("max_usd"),
            replay=payload.get("replay") is True,
        )
    return runs.gate(
        owner["id"], command, tickers, payload["session"], registry, report=report
    )


def authorize_radar_budget(payload, headers):
    """Web review of the existing immutable budget authorization; never starts calls."""
    fields = {"run", "budget_token", "max_aggregate_usd", "confirm"}
    if (
        not isinstance(payload, dict)
        or set(payload) != fields
        or payload["confirm"] is not True
    ):
        raise ValueError("explicit_budget_authorization_required")
    limit = payload["max_aggregate_usd"]
    if type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0:
        raise ValueError("invalid_aggregate_budget")
    if not isinstance(payload["budget_token"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", payload["budget_token"]
    ):
        raise ValueError("invalid_budget_token")
    owner = runner()
    if not owner or owner["id"] != payload["run"] or headers != [owner["id"]]:
        raise ValueError("radar_run_header_mismatch_reload_page")
    if not owner["accepts_new_calls"] or owner["mode"] != "CONSULTATIVE_SANDBOX":
        raise ValueError("run_not_accepting_new_calls")
    if radar_api.ACTIVE or (runs.root_of(owner) / "operation.lock").exists():
        raise ValueError("radar_busy_or_stale_lock")
    money = runs.budget(owner["id"], runs.load())
    if limit < money["aggregate_exposure_usd"]:
        raise ValueError("aggregate_budget_below_exposure")
    record = runs.authorize_budget(owner["id"], payload["budget_token"])
    return {
        "run": owner["id"],
        "authorized_exposure_usd": record["aggregate_exposure_usd"],
        "budget_token": record["budget_token"],
        "provider_calls": 0,
    }


def jobs_status(*, include_legacy=True):
    result = []
    # ponytail: local JSON jobs are scanned on demand; archive/index if this grows
    # beyond a local laboratory. Existing runners remain the state authority.
    for path in sorted(
        forward_jobs.JOBS.root.glob("job-*.json") if include_legacy else (),
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    ):
        job = forward_jobs.JOBS.status(path.stem.removeprefix("job-"))["job"]
        if not job:
            continue
        native = job["state"]
        if native == "RUNNING" and job["id"] not in forward_jobs.JOBS.active:
            native = "RECOVERY_REQUIRED"
        progress = job.get("progress") or {}
        result.append(
            {
                "module": "H2",
                **forward.pick(
                    job, "id", "command", "session", "stage", "started_at", "finished_at"
                ),
                **visual_state(native),
                "native_state": job["state"],
                "error": "runner_failed_consult_local_diagnostics"
                if job.get("error")
                else None,
                "calls_reserved": progress.get("reserved"),
                "calls_recorded": progress.get("recorded"),
                "cost_usd": None,
                "href": "/paper#sala",
            }
        )
    rjob, owner = radar_job(), runner()
    if rjob:
        outcome = rjob.get("outcome") or {}
        result.append(
            {
                "module": "Radar",
                "run": owner["id"] if owner else None,
                **forward.pick(rjob, "id", "command", "started_at", "finished_at"),
                **visual_state(rjob["status"]),
                **(
                    {
                        "state": {"PARTIAL": "RECOVERY_REQUIRED"}.get(
                            outcome["state"], outcome["state"]
                        ),
                        "result_state": outcome["summary"],
                    }
                    if outcome
                    else {}
                ),
                "cost_usd": None,
                "href": "/radar?run=" + owner["id"] if owner else "/radar",
            }
        )
    result += GLOBAL_JOBS.status()
    return sorted(result, key=lambda j: j.get("started_at", ""), reverse=True)


def active_overview():
    """Home/audit of the active platform; no independent PETR4/H2 reads."""
    registry = attempt(runs.overview)
    chosen = next(
        (r for r in (registry.get("data") or {}).get("runs", []) if r["selected"]), None
    )
    root = runs.root_of(chosen) if chosen else global_api.OFFICIAL_RADAR
    selection = (
        attempt(
            lambda: radar_readiness(
                chosen["session"], chosen["universe"], root, chosen["mode"], chosen["id"]
            )
        )
        if chosen
        else {"available": False}
    )
    return {
        "identity": "HFL-PLATFORM-V7",
        "observed_at": pm.now(),
        "read_only": True,
        "radar_runs": registry,
        "radar_run_selected": (chosen or {}).get("id"),
        "official_selection": selection,
        "global_records": global_records(),
        "synthetic_v5": attempt(lambda: portfolio_api.get("status", {})),
        "jobs": attempt(lambda: jobs_status(include_legacy=False)),
        "execution_multiasset_available": False,
        "provider_calls": 0,
    }


def overview(at=None):
    at = at or forward.fwd.now()
    wallets = attempt(forward.portfolios)
    decision = attempt(forward.decision)
    supervision = attempt(lambda: forward.supervision(clock=lambda: at))
    integrity = attempt(lambda: forward_integrity(forward.OUTPUT))
    radar_runs = attempt(runs.overview)
    chosen = next(
        (r for r in (radar_runs.get("data") or {}).get("runs", []) if r["selected"]), None
    )
    # Registry unavailable: show the legacy official root read-only; never a runner.
    radar_root = runs.root_of(chosen) if chosen else global_api.OFFICIAL_RADAR
    live_radar = attempt(lambda: radar.status(radar_root))
    day = str(forward.fwd.last_closed_session(at).date())
    universe = (
        (chosen or {}).get("universe")
        or (live_radar.get("data") or {}).get("universe")
        or list(radar.EXAMPLES)
    )
    selection = attempt(
        lambda: radar_readiness(
            chosen["session"] if chosen else day,
            universe,
            radar_root,
            chosen["mode"] if chosen else "CONSULTATIVE_SANDBOX",
            (chosen or {}).get("id"),
        )
    )
    v5 = attempt(lambda: portfolio_api.get("status", {}))
    v6 = attempt(lambda: global_api.get("status", {}))
    science = attempt(h2_api.status)
    selected = (supervision.get("data") or {}).get("selected") or {}
    current = decision.get("data") or {}
    records = global_records()
    processes = attempt(jobs_status)
    alerts = []
    for name, value in [
        ("Carteiras", wallets),
        ("Decisão H2", decision),
        ("Supervisão", supervision),
        ("Integridade H2", integrity),
        ("Radar", live_radar),
        ("Execuções Radar (registry)", radar_runs),
        ("Global PM", v6),
    ]:
        if not value["available"]:
            alerts.append(name + ": registro indisponível ou integridade divergente.")
    if selected.get("order_state") == "AGUARDANDO_APROVACAO":
        alerts.append("Supervisão aguarda ação humana até " + selected["deadline"] + ".")
    missing = (selection.get("data") or {}).get("missing")
    if missing:
        alerts.append(
            "Pareceres oficiais completos ausentes: " + ", ".join(missing) + "."
        )
    if (integrity.get("data") or {}).get("ok") is False:
        alerts.append("H2 sem ledger inicializado; consulta não cria carteira.")
    for job in processes.get("data") or []:
        if job["state"] in ("RUNNING", "FAILED", "RECOVERY_REQUIRED", "BLOCKED"):
            alerts.append(job["module"] + ": " + job["state"] + "; consultar processo.")
    observations = [
        w.get("mark", {}).get("session")
        for w in (wallets.get("data") or {}).get("wallets", [])
        if w.get("mark")
    ]
    inputs = sorted((forward.OUTPUT / "sessions").glob("????-??-??/input.json"))
    latest_input = forward.read(inputs[-1]) if inputs else None
    report = {
        "identity": "HFL-PLATFORM-V7",
        "observed_at": at.isoformat(),
        "read_only": True,
        "state": "BLOCKED"
        if not integrity["available"]
        else "COMPLETED"
        if current.get("status") == "DECIDED"
        else "NOT_PREPARED",
        "wallets": wallets,
        "decision": decision,
        "supervision": supervision,
        "integrity": integrity,
        "radar": live_radar,
        "radar_runs": radar_runs,
        "radar_run_selected": (chosen or {}).get("id"),
        "official_selection": selection,
        "global_records": records,
        "synthetic_v5": v5,
        "synthetic_v6": v6,
        "jobs": processes,
        "calendar": market_api.session_clock(at),
        "last_observed_session": max(observations) if observations else None,
        "last_input_observed_at": (latest_input or {}).get("fetched_at"),
        "last_closed_session": day,
        "intraday": {
            "available": False,
            "reason": "Consulta local sem provider intradiário; verificar Mercado.",
        },
        "alerts": alerts,
        "scientific": {
            "validation": "Validation OA-1 provisória · "
            + (
                (science.get("data") or {})
                .get("phases", {})
                .get("VALIDATION", {})
                .get("provisional", "indisponível")
            ),
            "academic": ((science.get("data") or {}).get("governance") or {}).get(
                "academic", "Governança indisponível"
            ),
            "final_test": ((science.get("data") or {}).get("phases") or {}).get(
                "FINAL_TEST", "Final Test bloqueado"
            ),
            "interpretation": "Resultados descritivos, não confirmatórios",
        },
        "manual_next_steps": [
            "Consultar a decisão de 09/10; não repetir sua inferência.",
            "Revisar a supervisão antes de 13/10 às 10h BRT; não há aprovação automática.",
            "Após dados oficiais de 13/10 disponíveis, preparar e conferir reconciliação no runner original; cada nova inferência exige autorização.",
            "Conferir SMA/Bollinger e supervisionada com os mesmos inputs observados, mediante ação explícita.",
            "Autorizar comitês Radar separadamente; só depois preparar contexto Global PM dentro de sua validade de 24 h.",
        ],
        "execution_multiasset_available": False,
        "provider_calls": 0,
    }
    report["attention"] = attention(report, at)
    return report


def attention(d, at):
    """Compact "Atenção necessária": derived only from the records read above."""
    br = lambda day: "/".join(reversed(day.split("-")))  # noqa: E731
    data = lambda key: d[key].get("data") if d[key]["available"] else None  # noqa: E731
    decision, sup = data("decision"), (data("supervision") or {}).get("selected")
    readiness, cal = data("official_selection"), d["calendar"]
    observed, closed = d["last_observed_session"], d["last_closed_session"]
    items = []
    if not (data("integrity") or {}).get("ok"):
        items.append(
            (
                "blocked",
                "Integridade H2 indisponível ou divergente: investigar antes de qualquer ação.",
                "/#audit",
            )
        )
    for job in (d["jobs"].get("data") or []) if d["jobs"]["available"] else []:
        if job["state"] in ("RUNNING", "FAILED", "RECOVERY_REQUIRED", "BLOCKED"):
            items.append(
                (
                    "blocked",
                    f"{job['module']} · {job.get('command')}: {job['state']}; consultar o registro, sem nova chamada.",
                    job["href"],
                )
            )
    pending = sup and sup.get("order_state") == "AGUARDANDO_APROVACAO"
    if pending:
        items.append(
            (
                "action",
                "Aprovar ou rejeitar a supervisionada até "
                + br(sup["deadline"][:10])
                + " "
                + sup["deadline"][11:16]
                + " BRT.",
                "/paper#supervisao",
            )
        )
    if observed and observed < closed:
        items.append(
            (
                "action",
                f"Preparar o fechamento oficial de {br(closed)} no runner original (grava; sem inferência).",
                "/paper#sala",
            )
        )
    target = (decision or {}).get("target_session")
    if target and cal.get("next_session") and target >= cal["next_session"]:
        items.append(
            (
                "info",
                f"Após o COTAHIST de {br(target)}: preparar o novo fechamento e conferir a reconciliação da intenção.",
                "/paper#sala",
            )
        )
    for run in ((d.get("radar_runs") or {}).get("data") or {}).get("runs", []):
        if run["incident"]:
            items.append(
                (
                    "info",
                    f"Radar {run['id']}: {run['incident']['classification']} ({run['incident']['id']})",
                    "/radar?run=" + run["id"],
                )
            )
        elif run["state"] in ("INTEGRITY_ERROR", "RECOVERY_REQUIRED", "PARTIAL"):
            items.append(
                (
                    "blocked",
                    f"Radar {run['id']}: {run['state']}; consultar a execução, sem nova chamada.",
                    "/radar?run=" + run["id"],
                )
            )
    if readiness and readiness["missing"]:
        blocked = [
            i["ticker"]
            for i in readiness["items"]
            if i["state"] in ("INPUT_BLOCKED", "INTEGRITY_ERROR", "RECOVERY_REQUIRED")
        ]
        items.append(
            (
                "lab",
                f"Radar {d.get('radar_run_selected') or 'oficial'}: {readiness['summary']}"
                + (f"; bloqueados: {', '.join(blocked)}" if blocked else "")
                + ". Global PM aguarda os pareceres de todos.",
                "/radar?run=" + d["radar_run_selected"]
                if d.get("radar_run_selected")
                else "/radar",
            )
        )
    for record in d["global_records"]:
        if record["state"] in ("PREPARED", "READY") and b.instant(
            record["expires_at"]
        ) < b.instant(at.isoformat()):
            items.append(
                (
                    "info",
                    f"Contexto Global {record['id'][:11]}… expirou; preparar outro ID quando for usar.",
                    record["href"],
                )
            )
    rank = {"blocked": 0, "action": 1, "info": 2, "lab": 3}
    items.sort(key=lambda x: rank[x[0]])
    return {
        "next_action": items[0][1] if items else "Nenhuma ação pendente nos registros.",
        "level": items[0][0] if items else "ok",
        "items": [{"level": a, "text": b, "href": c} for a, b, c in items],
        "decision": None
        if not decision
        else {
            "label": f"{(decision.get('portfolio') or {}).get('decision') or decision['status']} {decision.get('ticker', 'PETR4').removesuffix('.SA')}",
            "session": decision["session"],
            "target_session": target,
            "status": decision["status"],
            "votes": "{}/{}".format(
                (decision.get("committee") or {}).get("responded", "N/D"),
                (decision.get("committee") or {}).get("analyst_count", "N/D"),
            ),
            "order": (decision.get("order") or {}).get("label"),
        },
        "approval": None
        if not sup
        else {
            "state": sup["order_state"],
            "deadline": sup.get("deadline"),
            "pending": bool(pending),
        },
        "next_session": {
            "day": cal.get("next_session"),
            "expected_open": cal.get("expected_open"),
        },
        "data": {
            "last_observed_session": observed,
            "last_closed_session": closed,
            "current": bool(observed) and observed >= closed,
            "radar_eligible": None
            if not readiness
            else len(readiness["items"]) - len(readiness["missing"]),
            "radar_selected": None if not readiness else len(readiness["items"]),
        },
    }


def radar_source(payload):
    """(root, run, registry) a prepare reads: a registered run, or the legacy synthetic demo."""
    if "radar_run" not in payload:
        if payload["mode"] != "SYNTHETIC_DEMO":
            raise ValueError("radar_run_required")
        return source_root(payload["mode"]), None, None
    registry = runs.load()
    entry = runs.run(payload["radar_run"], registry)
    if entry["mode"] != payload["mode"]:
        raise ValueError("synthetic_official_mix")
    if entry["session"] != payload["session"]:
        raise ValueError("session_differs_from_radar_run")
    if not set(radar.tickers(payload["tickers"], empty=False)) <= set(entry["universe"]):
        raise ValueError("selection_outside_run_identity")
    hashes = payload["opinion_hashes"]
    if not isinstance(hashes, dict) or set(hashes) != set(payload["tickers"]):
        raise ValueError("opinion_hashes_required")
    return runs.root_of(entry), entry, registry


def checked_opinions(payload, at):
    """Every opinion re-read and verified in the run's own root; the browser's hashes
    only have to agree with it, never replace it."""
    root, entry, registry = radar_source(payload)
    opinions, histories = pm.load_opinions(
        root, payload["tickers"], payload["session"], payload["mode"], at
    )
    if entry and any(
        payload["opinion_hashes"][t] != o["sha256"] for t, o in opinions.items()
    ):
        raise ValueError("radar_selection_changed_review_again")
    return opinions, histories, entry, registry


def origin_record(analysis_id, entry, registry, opinions):
    return b.sealed(
        {
            "schema_version": 1,
            "analysis_id": analysis_id,
            "radar_run": {
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
                        "treatment",
                        "instance_of",
                    )
                },
                "incident": (entry["incident"] or {}).get("id"),
            },
            "registry_revision": registry["revision"],
            "registry_sha256": registry["sha256"],
            "opinions": {
                t: {
                    "opinion_sha256": o["sha256"],
                    "result_sha256": o["result_sha256"],
                    "input_sha256": o["input_sha256"],
                    "manifest_sha256": o["manifest_sha256"],
                    "session": o["session"],
                    "mode": o["mode"],
                    "input_ref": f"{entry['path']}/analyses/{t}/{o['session']}/input.json",
                }
                for t, o in opinions.items()
            },
            "recorded_at": pm.now(),
        }
    )


def radar_origin(value, detail, jobs=None):
    """Origin frozen beside the context; later run selections never change it."""
    path = (jobs or GLOBAL_JOBS).root / "radar_origins" / (value + ".json")
    if not path.exists():
        return {
            "state": "LEGACY_SYNTHETIC_DEMO"
            if detail["mode"] == "SYNTHETIC_DEMO"
            else "MISSING"
        }
    origin = b.check_seal(b.read(path))
    same = origin["analysis_id"] == value and {
        t: o["opinion_sha256"] for t, o in origin["opinions"].items()
    } == {t: o["sha256"] for t, o in detail["opinions"].items()}
    return {"state": "VERIFIED" if same else "MISMATCH", **origin}


def run_root(run_id):
    """Only allowlisted IDs reach the disk; the browser never names a path."""
    entry = runs.run(run_id, runs.load())
    return entry, runs.root_of(entry)


def radar_view(run_id):
    registry = runs.load()
    entry = runs.run(run_id, registry)
    root, owner = runs.root_of(entry), runs.run_for_root(radar_api.ROOT, registry)
    runner_run = bool(owner) and owner["id"] == entry["id"]
    return {
        **radar.status(root),
        "run": runs.public(entry, registry),
        "runner": owner["id"] if owner else None,
        "mode_view": entry["mode"],
        "job": radar_job(root),
        "network_isolation": network_scope.qualified(),
        "csrf_token": forward_jobs.JOBS.csrf,
        "read_only": True,
        # Writes go only to the server's runner, and only when it accepts new calls.
        "mutation_available": runner_run and entry["accepts_new_calls"],
    }


def audit(root, result, synthetic):
    """Sealed validation status beside lifecycle, described codes and token accounting.
    Read-only: the V1 record keeps its recorded ``cost_usd``; nothing is rewritten."""
    if not result:
        return {"validation_status": None, "error_details": [], "usage_accounting": None}
    claim = b.check_seal(b.read(root / "claim.json"))
    authorization = b.check_seal(b.read(root / "authorization.json"))
    return {
        "validation_status": result["status"],
        "error_details": [
            {**e, "description": pm2.ERRORS.get(e["code"], e["code"])}
            for e in result["validation"]["errors"]
        ],
        "financial_status": None
        if result["validation"]["financial_validation"] is None
        else {
            "valid": result["validation"]["financial_validation"]["valid"],
            "risk_projected": (
                result["validation"]["financial_validation"]["risk_projected"] or {}
            ).get("status"),
        },
        "usage_accounting": pm2.usage_accounting(
            result["tokens"],
            claim["created_at"],
            synthetic,
            authorization["usd_reserved"],
        ),
    }


def public_global(value):
    if isinstance(value, str) and ID2.fullmatch(value):
        root = pm2.root_path(pm2.OUTPUT / value)
        d = cli2.public_detail(root)
        origin = d.get("radar_origin")
        model = pm2.CONFIG["model"]
    else:
        root = analysis_root(value)
        d = global_api.public_detail(root)
        origin, model = None, pm.CONFIG["model"]
    if d["status"] == "NO_PROPOSAL":
        return {"id": value, **d, **visual_state(d["status"])}
    return {
        "id": value,
        **d,
        **visual_state(d["status"]),
        **audit(root, d["result"], d["mode"] == "SYNTHETIC_DEMO"),
        "radar_origin": origin or radar_origin(value, d),
        "model": model,
        "classification": "DEMONSTRAÇÃO SINTÉTICA"
        if d["mode"] == "SYNTHETIC_DEMO"
        else "CONSULTIVO COM GEMINI",
        "planner": (d["result"] or {}).get("planner"),
        # V2 prepare/preflight/run stay in the CLI with a separate human authorization.
        "ui_operations": d["identity"] == pm.IDENTITY,
        "execution_enabled": False,
    }


class GlobalJobs:
    def __init__(self, root=OPERATIONS):
        self.root = root
        self.active = set()
        self.mutex = threading.Lock()

    def status(self):
        result = []
        for path in sorted(
            self.root.glob("v7-*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True
        ):
            job = b.check_seal(b.read(path))
            native = job["state"]
            if native == "RUNNING" and job["job_id"] not in self.active:
                native = "RECOVERY_REQUIRED"
            result.append(
                {
                    **forward.pick(
                        job,
                        "module",
                        "job_id",
                        "id",
                        "command",
                        "started_at",
                        "finished_at",
                        "result_state",
                        "cost_usd",
                    ),
                    **visual_state(native),
                    "native_state": job["state"],
                    "error": "global_operation_failed_consult_record_no_automatic_retry"
                    if job.get("error")
                    else None,
                    "href": "/portfolio?analysis=" + job["id"],
                }
            )
        return result

    def start(self, command, payload):
        if (
            command not in FIELDS
            or not isinstance(payload, dict)
            or set(payload)
            not in (FIELDS[command], RUN_PREPARE if command == "prepare" else None)
        ):
            raise ValueError("invalid_payload")
        root = analysis_root(payload["id"])
        if command == "prepare":
            if (
                payload["confirm_hypothetical"] is not True
                or payload["ack_fixture_policy"] is not True
            ):
                raise ValueError("explicit_hypothetical_and_fixture_ack_required")
            source_root(payload["mode"])
            radar.session(payload["session"])
            radar.tickers(payload["tickers"], empty=False)
            if not isinstance(payload["capital"], str) or not 0 < b.amount(
                payload["capital"], positive=True
            ) <= b.dec("1000000000"):
                raise ValueError("invalid_hypothetical_capital")
            if root.exists():
                raise forward_jobs.Conflict("analysis_already_prepared_no_overwrite")
            # Eligibility is checked together, not merely one ticker at a time.
            checked_opinions(payload, pm.now())
        elif payload["confirm"] is not True:
            raise ValueError("explicit_confirmation_required")
        elif command == "run":
            if type(payload["authorize_paid"]) is not bool or not isinstance(
                payload["max_usd"], str
            ):
                raise ValueError("invalid_payload")
            report = cli.preflight(root, payload["max_usd"])
            if (
                not report["ready"]
                or payload["confirmation_token"] != report["confirmation_token"]
            ):
                raise ValueError("preflight_or_confirmation_changed")
            if report["paid"] and (
                payload["authorize_paid"] is not True
                or not os.environ.get("GEMINI_API_KEY", "").strip()
            ):
                raise ValueError("new_explicit_paid_authorization_and_key_required")
            if not report["paid"] and payload["authorize_paid"]:
                raise ValueError("synthetic_is_not_paid_inference")
            if (
                report["paid"]
                and radar_origin(payload["id"], global_api.public_detail(root), self)[
                    "state"
                ]
                != "VERIFIED"
            ):
                raise ValueError("radar_origin_missing_or_mismatch")
        else:
            cli.context_for(root)
            if (
                not (root / "claim.json").exists()
                or not (root / "private/calls.sqlite").exists()
            ):
                raise ValueError("missing_claim_journal")
        job_id = payload["id"] + "-" + command
        path = self.root / (job_id + ".json")
        with self.mutex:
            if self.active or path.exists():
                raise forward_jobs.Conflict("global_job_exists_or_busy_consult_recovery")
            job = {
                "module": "Global PM",
                "job_id": job_id,
                "id": payload["id"],
                "command": command,
                "state": "RUNNING",
                "started_at": pm.now(),
                "cost_usd": None,
            }
            b.write(path, b.sealed(job), immutable=True)
            self.active.add(job_id)
            try:
                threading.Thread(
                    target=self._work,
                    args=(command, dict(payload), job, path),
                    daemon=True,
                ).start()
            except RuntimeError as exc:
                self.active.discard(job_id)
                job.update(
                    state="FAILED",
                    error="global_worker_start_failed",
                    finished_at=pm.now(),
                )
                b.write(path, b.sealed(job))
                raise OSError("global_worker_start_failed") from exc
        return {**job, "execution_enabled": False}

    def _work(self, command, payload, job, path):
        try:
            root = analysis_root(payload["id"])
            if command == "prepare":
                at = pm.now()
                opinions, histories, entry, registry = checked_opinions(payload, at)
                if entry:  # written first: an origin without context is harmless
                    b.write(
                        self.root / "radar_origins" / (payload["id"] + ".json"),
                        origin_record(payload["id"], entry, registry, opinions),
                        immutable=True,
                    )
                snapshot = pm.make_snapshot(
                    payload["id"],
                    payload["mode"],
                    payload["session"],
                    {
                        t: str(b.money(o["raw_close"]))
                        if payload["mode"] == "SYNTHETIC_DEMO"
                        else o["raw_close"]
                        for t, o in opinions.items()
                    },
                    cash=payload["capital"],
                    at=at,
                )
                cli.prepare(
                    root, snapshot, opinions, histories, at=at, ack_fixture_policy=True
                )
            else:
                # Fake E is the existing all-cash proposal, valid for any observed
                # fixture prices; the original A fixture has fixed share counts.
                cli.run(
                    root,
                    payload.get("confirmation_token"),
                    payload.get("max_usd", "0.25"),
                    authorize_paid=payload.get("authorize_paid", False),
                    replay=command == "replay",
                    fake_case="E",
                )
            data = cli.detail(root)
            state = (
                "COMPLETED"
                if command == "prepare"
                else visual_state(data["status"])["state"]
            )
            job.update(
                state=state,
                result_state=data["status"],
                cost_usd=(data["result"] or {}).get("cost_usd"),
            )
        except Exception:
            # No provider exception, credential, raw envelope or prompt is public.
            root = analysis_root(payload["id"])
            job.update(
                state="RECOVERY_REQUIRED" if (root / "claim.json").exists() else "FAILED",
                error="global_operation_failed_consult_record_no_automatic_retry",
            )
        finally:
            job["finished_at"] = pm.now()
            try:
                b.write(path, b.sealed(job))
            finally:
                with self.mutex:
                    self.active.discard(job["job_id"])


GLOBAL_JOBS = GlobalJobs()


def get(command, query):
    if command == "overview" and not query:
        return active_overview()
    if command in ("legacy-overview", "readiness") and not query:
        return overview()
    if command == "jobs" and not query:
        return {
            "jobs": jobs_status(include_legacy=False),
            "global_records": global_records(),
            "read_only": True,
        }
    if command == "global" and set(query) == {"id"}:
        return public_global(query["id"])
    if command == "global-preflight" and set(query) == {"id", "max_usd"}:
        report = cli.preflight(analysis_root(query["id"]), query["max_usd"])
        return {
            **report,
            **visual_state(
                "READY_FOR_INFERENCE"
                if report["ready"]
                else "PROPOSAL_EXPIRED"
                if "context_expired_or_future" in report["errors"]
                else "BLOCKED"
            ),
        }
    if command == "radar-runs" and not query:
        return {
            **runs.overview(),
            "runner": (runner() or {}).get("id"),
            "read_only": True,
        }
    if command == "radar-budget" and set(query) == {"run"}:
        return {**runs.budget(query["run"], runs.load()), "read_only": True}
    if command == "radar-view" and set(query) == {"run"}:
        return radar_view(query["run"])
    if command == "radar-view" and set(query) == {"mode"}:
        mutable = (
            query["mode"] == "CONSULTATIVE_SANDBOX"
            and radar_api.ROOT.resolve() == global_api.OFFICIAL_RADAR.resolve()
            and (runner() or {}).get("accepts_new_calls") is True
        )
        return {
            **radar.status(source_root(query["mode"])),
            "mode_view": query["mode"],
            "job": radar_job() if mutable else None,
            # False in a server started without network_scope.install(): an offline
            # check there can block (or stay installed against) the paid worker.
            "network_isolation": network_scope.qualified(),
            "csrf_token": forward_jobs.JOBS.csrf,
            "read_only": True,
            "mutation_available": mutable,
        }
    if command == "radar-readiness" and set(query) == {"session", "tickers"}:
        return radar_readiness(query["session"], query["tickers"].split(","))
    if command == "radar-readiness" and set(query) == {"run", "session", "tickers"}:
        entry, root = run_root(query["run"])
        return {
            **radar_readiness(
                query["session"],
                query["tickers"].split(","),
                root,
                entry["mode"],
                entry["id"],
            ),
            "run": entry["id"],
        }
    if command == "radar-detail" and set(query) == {"mode", "ticker", "session"}:
        return radar.detail(query["ticker"], query["session"], source_root(query["mode"]))
    if command == "radar-detail" and set(query) == {"run", "ticker", "session"}:
        return radar.detail(query["ticker"], query["session"], run_root(query["run"])[1])
    if command == "radar-selection" and set(query) == {"run", "session", "tickers"}:
        entry, root = run_root(query["run"])
        if query["session"] != entry["session"]:
            raise ValueError("session_differs_from_radar_run")
        d = run_selection(
            entry["mode"], query["session"], query["tickers"].split(","), root
        )
        if not set(d["selected"]) <= set(entry["universe"]):
            raise ValueError("selection_outside_run_identity")
        return {
            **d,
            "radar_run": {
                k: entry[k]
                for k in (
                    "id",
                    "mode",
                    "classification",
                    "source",
                    "session",
                    "treatment",
                )
            },
            "opinion_hashes": {
                i["ticker"]: i["opinion_sha256"]
                for i in d["items"]
                if i["status"] == "ELIGIBLE"
            },
        }
    raise ValueError("invalid_platform_query")
