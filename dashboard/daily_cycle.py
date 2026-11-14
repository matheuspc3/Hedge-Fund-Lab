"""DP-34: autonomous daily cycle of the Multiagentes wallet, inside the server process.

On every B3 session, slots 09:00, 12:00 and 16:00 (America/Sao_Paulo); a later slot runs
only while no earlier attempt closed the day. One attempt does what Lucas does in /radar,
through the same Python functions the UI endpoints call (no HTTP):

  market update (DP-27) -> analysis (target today, data until the last closed session,
  which must already be published by B3) -> free prepare -> analysts (paid) -> manager
  prepare/preflight/paid call -> preview (DP-33 delayed quotes) -> approval, only when
  the backend accepts it with no stale-thesis alert.

Every budget, paid-call and approval step is recorded here as made by ACTOR (never by
Lucas), within CAP_USD of reservations per day (analysts + manager, all attempts). The
sealed records under data/platform/daily-cycle/<day>/ are immutable: one
``attempt-*.json`` per attempt and ``day.json`` once the day is closed (CONCLUIDO,
AGUARDANDO_LUCAS or SEM_ANALISE); a closed day never runs again.

Enabled only with HFL_DAILY_CYCLE=1 (``start``). ``python dashboard/daily_cycle.py`` runs
one attempt on the same code path; use it only with the server stopped, because the
radar_api / wallet_manager_api locks are per process.

Outbound calls (B3, Yahoo, Gemini, Resend) run in this plain thread or in the workers it
starts: network_scope only blocks sockets inside a ``no_network()`` context, and plain
threads start outside it.
"""

import json
import logging
import os
import sys
import threading
import time
import urllib.request
import uuid
from datetime import datetime, time as clock
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

# Standalone CLI (`python dashboard/daily_cycle.py`): same import roots as the server.
_PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_PROJECT), str(_PROJECT / "scripts")]
import market_base_api as market  # noqa: E402
import radar_analysis_api as analysis  # noqa: E402
import wallet_manager_api as wm  # noqa: E402

platform, radar, runs, b = analysis.platform, analysis.radar, analysis.runs, analysis.b
manual, orders, radar_api = analysis.manual, wm.orders, analysis.radar_api
log = logging.getLogger("hedgefund.daily_cycle")

IDENTITY = "HFL-DAILY-CYCLE-V1"
ACTOR = "DP-34 rotina diária"
SLOTS = ("09:00", "12:00", "16:00")
CAP_USD = Decimal("4.00")
FOLDER = platform.ROOT / "data/platform/daily-cycle"
POLL = 5  # seconds between job checks
TIMEOUT = {"mercado": 1800, "preparo": 1800, "analistas": 3600, "gestor": 900}
SLEEP = time.sleep  # tests replace it
LOCK = threading.Lock()
SP = orders.SP
LABELS = {
    "CONCLUIDO": "concluído",
    "RETRY": "nova tentativa agendada",
    "AGUARDANDO_LUCAS": "aguardando Lucas",
    "SEM_ANALISE": "dia sem análise",
}
RESEND_URL = "https://api.resend.com/emails"
# Without a verified domain Resend only delivers from onboarding@resend.dev, and only to
# the address of the Resend account owner.
DEFAULT_FROM = "Hedge Fund Lab <onboarding@resend.dev>"
# ponytail: same ceiling as run_global_pm_v2.estimate (full input bytes + output limit at
# the higher announced rates) so analysts never leave the manager without room; the
# manager preflight re-checks its real reserve before the paid call.
_c = wm.CONFIG
MANAGER_RESERVE = (
    b.dec(_c["input_bytes_max"]) * b.dec(_c["input_usd_million_ceiling"])
    + b.dec(_c["options"]["max_output_tokens"]) * b.dec(_c["output_usd_million_ceiling"])
) / 1000000


class Stop(Exception):
    """Ends one attempt. retry=True: the next slot tries again; otherwise Lucas decides."""

    def __init__(self, reason, retry=False):
        super().__init__(reason)
        self.reason, self.retry = reason, retry


def step(rec, name, **info):
    rec["steps"].append({"step": name, "at": radar.now().isoformat(), **info})


def wait(done, what):
    deadline = time.monotonic() + TIMEOUT[what]
    while not done():
        if time.monotonic() > deadline:
            raise Stop(f"{what}_sem_conclusao_no_prazo", retry=True)
        SLEEP(POLL)


# ---- records ---------------------------------------------------------------------


def earlier(day):
    """Sealed attempt records of `day`, oldest first."""
    found = [b.check_seal(radar.read(p)) for p in (FOLDER / day).glob("attempt-*.json")]
    return sorted(found, key=lambda a: a["started_at"])


def final(day):
    path = FOLDER / day / "day.json"
    return b.check_seal(radar.read(path)) if path.exists() else None


def links(day):
    merged = {}
    for a in earlier(day):
        merged.update({k: v for k, v in a["links"].items() if v})
    return merged


def close_day(day, status, reason):
    path = FOLDER / day / "day.json"
    if not path.exists():
        value = {
            "identity": IDENTITY,
            "day": day,
            "status": status,
            "reason": reason,
            "actor": ACTOR,
            "closed_at": radar.now().isoformat(),
            "attempts": [
                {k: a[k] for k in ("slot", "status", "sha256")} for a in earlier(day)
            ],
        }
        radar.write(path, b.sealed(value), immutable=True)


def latest(limit=5):
    """Last days of the routine for read-only views (e.g. /radar 'rodada automática')."""
    try:
        days = sorted((p.name for p in FOLDER.glob("????-??-??")), reverse=True)
        return {
            "enabled": os.environ.get("HFL_DAILY_CYCLE") == "1",
            "slots": list(SLOTS),
            "cap_usd": str(CAP_USD),
            "days": [
                {
                    "day": d,
                    "closed": final(d),
                    "attempts": [
                        {
                            k: a.get(k)
                            for k in (
                                "slot",
                                "status",
                                "reason",
                                "outcome",
                                "started_at",
                                "finished_at",
                                "links",
                                "reservations",
                                "email",
                            )
                        }
                        for a in earlier(d)
                    ],
                }
                for d in days[:limit]
            ],
        }
    except (ValueError, OSError, KeyError) as e:
        return {"error": f"daily_cycle_records_unreadable: {type(e).__name__}"}


# ---- budget ----------------------------------------------------------------------


def spent_in(root):
    """USD reserved (never released) in one run root: analyst batches + manager calls."""
    total = Decimal(str(round(radar.budget_used(root), 6)))
    for p in (root / "wallet-manager").glob("*/authorization.json"):
        total += b.dec(b.check_seal(radar.read(p))["usd_reserved"])
    return total


def day_spent(day, rec):
    names = {a["links"].get("run") for a in earlier(day)} | {rec["links"].get("run")}
    return sum((spent_in(runs.root_of(runs.run(n))) for n in names if n), Decimal(0))


def within_cap(rec, day, planned, what):
    """Remaining daily room before `planned`; Stop (Lucas decides) when it would not fit."""
    spent = day_spent(day, rec)
    rec["reservations"]["day_before"] = str(spent)
    if spent + planned > CAP_USD:
        raise Stop(
            f"teto_diario_excedido: {what} reservaria US$ {planned:.6f} com US$ "
            f"{spent:.6f} já reservados hoje (teto US$ {CAP_USD})"
        )
    return CAP_USD - spent


# ---- steps -----------------------------------------------------------------------


def update_market(rec):
    """Same path as the "Atualizar dados" button (POST market-base/update)."""
    market.start()
    wait(lambda: not market.JOB["running"], "mercado")
    if market.JOB["error"]:
        raise Stop("atualizacao_de_mercado_falhou: " + market.JOB["error"], retry=True)
    step(rec, "mercado_atualizado", published=market.published())


def multiagent_wallet():
    found = [
        w
        for w in manual.get({})["wallets"]
        if w["nature"] == "SIMULATION"
        and w.get("strategy") not in ("BUY_HOLD", *manual.RULE_STRATEGIES)
    ]
    if len(found) != 1:
        raise Stop("carteira_multiagentes_ausente_ou_ambigua")
    return found[0]


def open_analysis(rec, day):
    """Today's analysis: reused across the day's attempts unless the wallet changed."""
    options = analysis.choices()
    reference = options["last_closed_session"]
    if options["reference_session"] != reference:  # B3 has not published it yet
        raise Stop("reference_session_not_yet_published_by_b3", retry=True)
    request, reused = links(day).get("analysis_request"), True
    if request:
        seen = analysis.get({"run": "radar-ui-" + request["command_id"]})
        if seen["wallet_changed"] or seen["context"]["reference_session"] != reference:
            step(
                rec,
                "analise_anterior_descartada",
                run="radar-ui-" + request["command_id"],
            )
            request = None
    if request is None:
        w, reused = multiagent_wallet(), False
        request = {
            "command_id": uuid.uuid4().hex,
            "wallet": w["id"],
            "wallet_revision": w["revision"],
            "target_date": day,
            "reference_session": reference,
            "tickers": analysis.default_tickers(w),
            "confirm": True,
        }
    out = analysis.create(request)  # idempotent; selects the run as the Radar runner
    rec["links"].update(run=out["run"], analysis_request=request)
    step(
        rec,
        "analise",
        run=out["run"],
        reused=reused,
        classification=out["context"]["classification"],
    )
    return out["run"]


def prepare_data(rec, run):
    """Free prepare (re-run on retries; frozen inputs are kept) until every input exists."""
    entry = runs.run(run)
    root, day, tickers = runs.root_of(entry), entry["session"], entry["universe"]

    def missing():
        r = platform.radar_readiness(day, tickers, root, entry["mode"], run)
        return [i for i in r["items"] if i["input_state"] != "FROZEN"]

    if bad := missing():
        payload = {"tickers": tickers, "session": day, "mode": runs.MODES[entry["mode"]]}
        with platform.RADAR_DISPATCH_LOCK:
            platform.radar_post_gate("prepare", payload, [run])
            radar_api.post("prepare", payload)
        wait(lambda: not radar_api.ACTIVE, "preparo")
        bad = missing()
    if bad:
        raise Stop(
            "dados_nao_consolidados: "
            + "; ".join(
                f"{i['ticker']}: {i.get('error') or i['input_state']}" for i in bad
            ),
            retry=True,
        )
    step(rec, "dados_prontos", session=day, tickers=tickers)
    return entry, root


def analysts(rec, entry, root, day):
    run, ref, tickers = entry["id"], entry["session"], entry["universe"]

    def states():
        return {
            t: (runs.committee_outcome(root, t, ref) or {}).get("state") for t in tickers
        }

    s = states()
    if all(v == "COMMITTEE_COMPLETED" for v in s.values()):
        return step(rec, "analistas_concluidos", reused=True)
    if any(s.values()):  # reserved calls are never repeated: offline replay is Lucas's
        raise Stop(f"analistas_com_reserva_sem_parecer_completo: {s}")
    if Path(radar_api.ROOT).resolve() != root.resolve():
        raise Stop("radar_runner_mudou", retry=True)
    room = within_cap(rec, day, MANAGER_RESERVE, "a reserva do gestor") - MANAGER_RESERVE
    max_usd = float(min(room, Decimal("5")).quantize(Decimal("0.000001"), ROUND_DOWN))
    if max_usd <= 0:
        raise Stop(
            f"teto_diario_excedido: sem saldo para os analistas (teto US$ {CAP_USD})"
        )
    check = {"tickers": tickers, "session": ref, "max_usd": max_usd, "replay": False}
    with platform.RADAR_DISPATCH_LOCK:
        report = radar_api.post("preflight", check)
        planned = Decimal(str(report["usd_reserved"]))
        within_cap(rec, day, planned + MANAGER_RESERVE, "analistas + gestor")
        if not report["ready"]:
            errors = {i["error"] for i in report["items"] if not i["ready"]}
            raise Stop(
                "preflight_analistas_bloqueado: "
                + (", ".join(sorted(errors)) or "limite_do_lote")
            )
        money = runs.budget(run, runs.load())
        if (
            money["authorization"]["required"]
            and money["authorization"]["state"] != "VALID"
        ):
            # Same fields as the /radar budget review; the record of who authorized is ours.
            platform.authorize_radar_budget(
                {
                    "run": run,
                    "budget_token": money["budget_token"],
                    "max_aggregate_usd": money["aggregate_exposure_usd"],
                    "confirm": True,
                },
                [run],
            )
            step(
                rec,
                "orcamento_agregado_autorizado",
                by=ACTOR,
                budget_token=money["budget_token"],
                aggregate_exposure_usd=str(money["aggregate_exposure_usd"]),
            )
        payload = {
            **check,
            "confirmation_token": report["confirmation_token"],
            "authorize_paid": True,
            "confirm": True,
        }
        platform.radar_post_gate("run", payload, [run])
        radar_api.post("run", payload)
    rec["reservations"]["analysts"] = str(planned)
    step(
        rec,
        "analistas_autorizados",
        by=ACTOR,
        usd_reserved=str(planned),
        confirmation_token=report["confirmation_token"],
    )
    wait(lambda: not radar_api.ACTIVE, "analistas")
    s = states()
    if not all(v == "COMMITTEE_COMPLETED" for v in s.values()):
        raise Stop(f"comites_incompletos: {s}")
    step(rec, "analistas_concluidos", reused=False)


def last_cost_rate(wallet):
    """Cost rate of the newest manager proposal of this wallet (Lucas's last choice)."""
    found = wm.latest({"wallet": wallet})["latest"]
    if not found:
        raise Stop("sem_taxa_de_custo_anterior: nenhuma proposta anterior desta carteira")
    return wm.checked(wm.folder(found["run"], found["proposal"]))["cost_rate_pct"]


def manager(rec, entry, day):
    run, wallet = entry["id"], analysis.context(entry)["wallet"]["id"]
    known = links(day)
    proposal = known.get("proposal") if known.get("run") == run else None
    if proposal is None:
        rate, proposal = last_cost_rate(wallet), uuid.uuid4().hex
        wm.post("prepare", {"run": run, "proposal": proposal, "cost_rate_pct": rate})
        step(rec, "gestor_preparado", proposal=proposal, cost_rate_pct=rate)
    rec["links"]["proposal"] = proposal
    base = {"run": run, "proposal": proposal}
    s = wm.status(run, proposal)
    if s["status"] == "PREPARED":
        cap = within_cap(rec, day, Decimal(0), "o gestor").quantize(
            Decimal("0.01"), ROUND_DOWN
        )
        if cap <= 0:
            raise Stop(
                f"teto_diario_excedido: sem saldo para o gestor (teto US$ {CAP_USD})"
            )
        report = wm.post("preflight", {**base, "max_usd": str(cap)})
        within_cap(rec, day, b.dec(report["usd_reserved"]), "o gestor")
        if not report["ready"]:
            raise Stop("preflight_gestor_bloqueado: " + ", ".join(report["errors"]))
        wm.post(
            "run",
            {
                **base,
                "max_usd": report["max_usd"],
                "confirmation_token": report["confirmation_token"],
                "authorize_paid": True,
            },
        )
        rec["reservations"]["manager"] = report["usd_reserved"]
        step(
            rec,
            "gestor_autorizado",
            by=ACTOR,
            usd_reserved=report["usd_reserved"],
            confirmation_token=report["confirmation_token"],
        )
        wait(
            lambda: wm.status(run, proposal)["status"]
            not in ("RUNNING", "CLAIMED_RECOVERY_ONLY"),
            "gestor",
        )
        s = wm.status(run, proposal)
    if s["order"] or s["applied"]:
        rec["outcome"] = "Proposta já aprovada anteriormente."
        return step(rec, "ja_aprovada")
    if s["status"] != "VALID_PROPOSAL":
        raise Stop(f"gestor_{s['status'].lower()}: proposta {proposal} exige revisão")
    if not s["result"]["trades"]:
        rec["outcome"] = "Gestor manteve a carteira: nenhuma operação."
        return step(rec, "gestor_manteve")
    preview = {**base, "economic_date": day}
    try:
        d = wm.post("preview", preview)
        if d["stale_alert"]:
            raise Stop("alerta_tese_velha: " + " ".join(d["stale_alert"]))
        step(rec, "previa", schedule=d["schedule"])
        out = wm.post(
            "apply", {**preview, "preview_token": d["preview_token"], "confirm": True}
        )
    except manual.Invalid as e:  # band, stale or accounting refusal: Lucas reviews
        raise Stop(f"aprovacao_recusada: {e.field}: {e}") from e
    except ValueError as e:  # e.g. expired, pending order of the wallet
        raise Stop(f"aprovacao_recusada: {e}") from e
    order = out["order"]
    rec["links"]["order"] = {
        k: order[k] for k in ("session", "leg", "basket", "approved_at", "sha256")
    }
    rec["outcome"] = (
        "Ordem aprovada: "
        + ", ".join(f"{t['side']} {t['quantity']} {t['ticker']}" for t in order["basket"])
        + (
            f" na simulação intradiária de {order['session']}, aguardando barra posterior à aprovação."
            if order["leg"] == "INTRADAY"
            else f" no leilão de {'abertura' if order['leg'] == 'OPEN' else 'fechamento'} de {order['session']}."
        )
    )
    step(rec, "aprovada", by=ACTOR, session=order["session"], leg=order["leg"])


def cycle(rec, day):
    update_market(rec)
    wallet = multiagent_wallet()
    for root in orders.folders():
        order = orders.read(root / "order.json")
        if (
            order
            and order["wallet"]["id"] == wallet["id"]
            and not (root / "execution.json").exists()
        ):
            raise Stop(
                (
                    "ordem_aguardando_preco_intradiario"
                    if order["leg"] == "INTRADAY"
                    else "ordem_aguardando_leilao_oficial"
                )
                + f": {order['session']} {order['leg']}",
                retry=True,
            )
    run = open_analysis(rec, day)
    entry, root = prepare_data(rec, run)
    analysts(rec, entry, root, day)
    manager(rec, entry, day)


# ---- attempts, notification and scheduler ----------------------------------------


def send(subject, text):
    """Resend e-mail; never raises into the cycle. Returns what the record shows."""
    key = os.environ.get("HFL_RESEND_API_KEY", "").strip()
    to = [t.strip() for t in os.environ.get("HFL_NOTIFY_TO", "").split(",") if t.strip()]
    if not key or not to:
        log.info("DP-34 e-mail não configurado: %s", subject)
        return "e-mail não configurado"
    body = {
        "from": os.environ.get("HFL_NOTIFY_FROM", "").strip() or DEFAULT_FROM,
        "to": to,
        "subject": subject,
        "text": text,
    }
    req = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "User-Agent": "HedgeFundLab/1.0 (DP-34)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
        return "enviado"
    except Exception as e:  # a notification never fails the cycle
        log.warning("DP-34 e-mail falhou: %s", type(e).__name__)
        return f"falha no e-mail: {type(e).__name__}"


def notify(rec):
    status = rec["day_status"] or rec["status"]
    br = "/".join(reversed(rec["day"].split("-")))
    lines = [
        f"Ciclo diário da carteira Multiagentes · {br} · tentativa {rec['slot']}",
        f"Resultado: {LABELS[status]}",
        rec["outcome"] or "",
        f"Motivo: {rec['reason']}" if rec["reason"] else "",
        f"Próxima tentativa: {rec['next_slot']}" if rec["next_slot"] else "",
        f"Reservas (US$): {rec['reservations']}",
        f"Análise: {rec['links'].get('run') or '—'} · proposta: {rec['links'].get('proposal') or '—'}",
        f"Etapas: {', '.join(s['step'] for s in rec['steps']) or '—'}",
        f"Autorizações automáticas registradas como: {ACTOR}.",
    ]
    return send(
        f"[HFL] Ciclo {br} {rec['slot']}: {LABELS[status]}",
        "\n".join(x for x in lines if x),
    )


def attempt(slot="manual"):
    """One attempt for today; idempotent once the day is closed."""
    if not LOCK.acquire(blocking=False):
        raise ValueError("daily_cycle_already_running")
    try:
        now = radar.now()
        day = now.date().isoformat()
        if closed := final(day):
            return closed
        if not orders.B3Calendar().is_session(now.date()):
            return {"day": day, "status": "SEM_PREGAO"}
        rec = {
            "identity": IDENTITY,
            "day": day,
            "slot": slot,
            "actor": ACTOR,
            "started_at": now.isoformat(),
            "steps": [],
            "links": {},
            "reservations": {"cap": str(CAP_USD)},
            "outcome": None,
            "reason": None,
        }
        try:
            cycle(rec, day)
            status = "CONCLUIDO"
        except Stop as e:
            status, rec["reason"] = ("RETRY" if e.retry else "AGUARDANDO_LUCAS"), e.reason
        except Exception as e:  # unexpected: recorded, the next slot retries
            log.exception("DP-34 tentativa %s falhou", slot)
            status, rec["reason"] = "RETRY", f"{type(e).__name__}: {e}"[:500]
        try:
            rec["reservations"]["day_total"] = str(day_spent(day, rec))
        except Exception as e:
            rec["reservations"]["day_total"] = f"indisponível: {type(e).__name__}"
        later = [s for s, start, _ in windows(now.date()) if start > now]
        rec.update(
            status=status,
            finished_at=radar.now().isoformat(),
            day_status=status
            if status != "RETRY"
            else "SEM_ANALISE"
            if slot == SLOTS[-1]
            else None,
            next_slot=later[0] if status == "RETRY" and later else None,
        )
        rec["email"] = notify(rec)
        record = b.sealed(rec)
        name = f"attempt-{now:%H%M%S}-{slot.replace(':', '')}-{uuid.uuid4().hex[:6]}.json"
        radar.write(FOLDER / day / name, record, immutable=True)
        if rec["day_status"]:
            close_day(day, rec["day_status"], rec["reason"])
        return record
    finally:
        LOCK.release()


def windows(day):
    """(slot, start, end): a slot runs once inside its window; the last ends at the
    DP-33 closing-auction approval cutoff of the day."""
    starts = [datetime.combine(day, clock.fromisoformat(s), SP) for s in SLOTS]
    return list(zip(SLOTS, starts, [*starts[1:], orders.cutoffs(day.isoformat())[1]]))


def tick(now=None):
    now = now or radar.now()
    now = getattr(now, "to_pydatetime", lambda: now)().astimezone(SP)
    day = now.date()
    if not orders.B3Calendar().is_session(day) or final(day.isoformat()):
        return None
    done = {a["slot"] for a in earlier(day.isoformat())}
    spans = windows(day)
    for slot, start, end in spans:
        if start <= now < end:
            return None if slot in done else attempt(slot)
    if now >= spans[-1][2]:  # every window passed without closing the day
        reason = "nenhuma tentativa concluída nas janelas do dia (servidor indisponível?)"
        br = "/".join(reversed(day.isoformat().split("-")))
        email = send(f"[HFL] Ciclo {br}: {LABELS['SEM_ANALISE']}", reason)
        close_day(day.isoformat(), "SEM_ANALISE", f"{reason} · e-mail: {email}")
    return None


def start():
    """Scheduler thread, only with HFL_DAILY_CYCLE=1 (local dev and tests never start it)."""
    if os.environ.get("HFL_DAILY_CYCLE") != "1":
        return None

    def loop():
        while True:
            try:
                tick()
            except Exception:  # the scheduler itself never dies
                log.exception("DP-34 agendador")
            SLEEP(60)

    worker = threading.Thread(target=loop, name="hfl-daily-cycle", daemon=True)
    worker.start()
    log.info("DP-34 ciclo diário ativo: %s (America/Sao_Paulo)", ", ".join(SLOTS))
    return worker


if __name__ == "__main__":
    import server

    server.setup()
    print(json.dumps(attempt(), ensure_ascii=False, indent=2, default=str))
