"""H2-V6-FORWARD-PAPER: operação prospectiva da H2 v6 congelada, só em paper trading.

Avaliação prospectiva EXPLORATÓRIA de PETR4.SA. Não é Validation nem Final Test,
não é inferência confirmatória e não alimenta retuning. Não existe código de
corretora: nenhuma ordem real sai daqui.

    prepare    baixa COTAHIST (B3) x fator yfinance e congela a entrada da sessão S.
               Grátis; nenhuma chamada LLM.
    preflight  offline (rede bloqueada): identidade do tratamento, calendário, dados,
               reconciliação prevista e custo estimado. Nenhuma chamada paga.
    run        reconcilia abertura/fechamento e decide S (Gemini, pago). Exige --confirm.

Reaproveita sem alterar um byte inventariado: manifesto candidato (identidade),
LLMParticipant via build_with_client, CallBank/DurableGeminiClient (reserva FULL
antes do transporte, replay-only na recuperação), ExecutionEngine._settle
(fracionário, custos-base), B3OfficialAdjustedExtractor e B3Calendar. Registros
só em data/forward/h2_v6_paper, separados de Validation e Final Test.
"""

# ruff: noqa: E402 -- standalone entrypoint establishes repository imports.
import argparse
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, cast
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd
import run_h2_v6_provisional as oa1

from src.agents.llm_client import LLMClient
from src.agents.participant import LLMDecisionError
from src.backtesting.arena import ExecutionEngine, MarketObservation, OrderIntent
from src.backtesting.b3_calendar import B3_CALENDAR_VERSION, B3Calendar
from src.backtesting.daily_agent import _exclusive_state_lock, _timestamp
from src.experiments.h2_evaluation import (
    BASE_COSTS,
    CAPITAL,
    EXECUTION,
    PARTICIPANT_SHA256,
    PHASE_WINDOWS,
    TICKER,
    digest,
)
from src.experiments.h2_evaluation_manifest import (
    CANDIDATE,
    read,
    sha_file,
    verify_manifest,
)
from src.experiments.h2_evaluation_offline import (
    _write_once,
    build_with_client,
    no_network,
)
from src.experiments.h2_evaluation_production import (
    CallBank,
    DurableGeminiClient,
    JournalIntegrityError,
)
from src.experiments.spec import ParticipantSpec
from src.pipeline.b3_official import (
    COTAHIST_URL,
    B3OfficialAdjustedExtractor,
    read_cotahist,
)

TREATMENT = "H2-V6-FORWARD-PAPER"
CLASSIFICATION = "PROSPECTIVE EXPLORATORY PAPER TRADING - NOT CONFIRMATORY, NOT FINAL TEST, NO RETUNING"
OUTPUT = ROOT / "data/forward/h2_v6_paper"
PHASE, SLOT, TZ = "FORWARD_PAPER", "L01", "America/Sao_Paulo"
#: Mesmo início de cobertura do snapshot reservado: a MACD usa ewm(adjust=False)
#: e herda a inicialização da série; outro início mudaria as features.
HISTORY_START = "2016-01-01"
#: Decisões só depois de toda janela reservada (Final Test termina em 2026-08-31).
FORWARD_FLOOR = pd.Timestamp(PHASE_WINDOWS["FINAL_TEST"].end)
CALENDAR_VERIFIED_THROUGH = "2026-08-31"
#: Anos completos no cache COTAHIST científico local, lidos sem alteração.
SCIENCE_CACHE, SCIENCE_CACHE_LAST_YEAR = ROOT / "data/raw/cotahist", 2025
# ponytail: grade fixa do pregão regular (sem horário de verão desde 2019). A
# barra presente no COTAHIST continua sendo o juiz final de sessão encerrada.
SESSION_CLOSED, TARGET_OPEN = time(18, 0), time(10, 0)
IDENTITY_KEYS = (
    "kind", "schema_version", "treatment", "classification", "paper_only", "ticker",
    "manifest_sha256", "participant_sha256", "initial_capital", "costs", "execution",
    "history_start",
)  # fmt: skip


def now():
    return pd.Timestamp.now(tz=TZ)


def last_closed_session(at):
    """Última sessão B3 cujo fechamento já ocorreu no instante ``at``."""
    day = at.date() if at.time() >= SESSION_CLOSED else at.date() - timedelta(days=1)
    return _timestamp(B3Calendar().sessions_between(day - timedelta(days=31), day)[-1])


def target_open(session):
    target = B3Calendar().next_session(session.date())
    return pd.Timestamp(datetime.combine(target, TARGET_OPEN), tz=TZ)


def _once(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"immutable forward record changed: {path.name}")
        return
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


class ForwardExtractor(B3OfficialAdjustedExtractor):
    """Anos fechados vêm do cache científico (só leitura); o resto é baixado de novo."""

    def __init__(self, cache_dir):
        super().__init__(cache_dir=cache_dir)
        self.paths = {}

    def _cotahist(self, year):
        path = SCIENCE_CACHE / f"COTAHIST_A{year}.ZIP"
        if year > SCIENCE_CACHE_LAST_YEAR or not path.exists():
            path = self.cache_dir / path.name
            # A B3 responde 403 ao urllib sem User-Agent.
            url = request.Request(
                COTAHIST_URL.format(year=year), headers={"User-Agent": "Mozilla/5.0"}
            )
            with request.urlopen(url, timeout=600) as response:
                path.with_suffix(".tmp").write_bytes(response.read())
            path.with_suffix(".tmp").replace(path)
        self.files[path.name] = sha_file(path)
        self.paths[year] = path
        return path

    def official_bar(self, session):
        """Barra oficial bruta (sem fator de ajuste): o preço real da sessão."""
        raw = read_cotahist(self.paths[session.year], TICKER.removesuffix(".SA"))
        return {k: float(v) for k, v in raw.loc[session].items()}


def prepare(root=OUTPUT, clock=now, extractor=None):
    """Congela, uma única vez, a entrada causal da última sessão encerrada."""
    at = clock()
    session = last_closed_session(at)
    if session <= FORWARD_FLOOR:
        raise ValueError("forward sessions must follow every reserved evaluation window")
    folder = root / "sessions" / str(session.date())
    if (folder / "input.json").exists():
        return folder / "input.json"  # nunca rebaixa nem substitui a entrada de S
    extractor = extractor or ForwardExtractor(str(root / "cotahist"))
    bars = extractor.download(TICKER, HISTORY_START, str(session.date()))
    calendar, first = B3Calendar(), cast(pd.Timestamp, bars.index[0])
    expected = pd.DatetimeIndex(calendar.sessions_between(first.date(), session.date()))
    if not pd.DatetimeIndex(bars.index).equals(expected):
        observed = pd.DatetimeIndex(bars.index)
        raise ValueError(
            "bars differ from the B3 calendar ending at the decision session: "
            f"missing {[str(d.date()) for d in expected.difference(observed)][:10]}, "
            f"extra {[str(d.date()) for d in observed.difference(expected)][:10]}"
        )
    folder.mkdir(parents=True, exist_ok=True)
    csv = bars.to_csv(lineterminator="\n").encode()
    _once(folder / "bars.csv", csv)
    target = calendar.next_session(session.date())
    gap = pd.date_range(
        session + pd.Timedelta(days=1), pd.Timestamp(target), inclusive="left"
    )
    _write_once(
        folder / "input.json",
        {
            "kind": "H2_V6_FORWARD_PAPER_INPUT",
            "treatment": TREATMENT,
            "classification": CLASSIFICATION,
            "ticker": TICKER,
            "decision_session": str(session.date()),
            "target_session": str(target),
            "target_open_deadline": target_open(session).isoformat(),
            "fetched_at": at.isoformat(),
            "history": {
                "file": "bars.csv",
                "sha256": hashlib.sha256(csv).hexdigest(),
                "start": str(first.date()),
                "end": str(session.date()),
                "bars": len(bars),
            },
            "close_used": float(bars.at[session, "fechamento"]),
            "last_bar_adjusted": {k: float(v) for k, v in bars.loc[session].items()},
            "last_bar_official_raw": extractor.official_bar(session),
            "source": extractor.source_description(),
            "calendar": {
                "version": B3_CALENDAR_VERSION,
                "verified_against_cotahist_through": CALENDAR_VERIFIED_THROUGH,
                "data_matches_calendar_from_history_start": True,
                "closed_days_before_target": [
                    {"date": str(d.date()), "weekday": d.day_name()} for d in gap
                ],
            },
        },
    )
    return folder / "input.json"


def identity(clean=True):
    """Mesma identidade da Validation OA-1: manifesto candidato + participante H2 v6."""
    sha = oa1.candidate_sha()
    document = verify_manifest(CANDIDATE, sha, clean=clean)
    spec = ParticipantSpec(**document["protocol"]["participant_spec"])
    if digest(spec.to_dict()) != PARTICIPANT_SHA256:
        raise ValueError("H2 v6 treatment identity changed")
    return sha, spec


def new_state(manifest_sha):
    return {
        "kind": "H2_V6_FORWARD_PAPER_STATE",
        "schema_version": 1,
        "treatment": TREATMENT,
        "classification": CLASSIFICATION,
        "paper_only": True,
        "ticker": TICKER,
        "manifest_sha256": manifest_sha,
        "participant_sha256": PARTICIPANT_SHA256,
        "initial_capital": CAPITAL,
        "costs": BASE_COSTS.to_dict(),
        "execution": EXECUTION.to_dict(),
        "history_start": HISTORY_START,
        "portfolio": {"cash": CAPITAL, "units": 0.0},
        "benchmark": {
            "kind": "buy_and_hold",
            "cash": CAPITAL,
            "units": 0.0,
            "invested": False,
        },
        "peak_equity": CAPITAL,
        "mark": None,
        "pending": None,
        "sessions": [],
        "decisions": [],
    }


def load_state(root, manifest_sha):
    path = root / "state.json"
    expected = new_state(manifest_sha)
    if not path.exists():
        return expected
    state = read(path)
    for key in IDENTITY_KEYS:
        if state.get(key) != expected[key]:
            raise ValueError(
                f"forward ledger identity differs ({key}); start a new ledger"
            )
    return state


def save_state(root, state):
    path = root / "state.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def load_bars(folder):
    return pd.read_csv(folder / "bars.csv", index_col=0, parse_dates=True)


def _engine(bars):
    return ExecutionEngine(
        cast(Any, None),  # só liquidação: ninguém decide neste motor
        {TICKER: bars},
        CAPITAL,
        BASE_COSTS.build(),
        quantity_mode=EXECUTION.quantity_mode,
    )


def _settle(engine, book, weight, day, decided):
    positions = {TICKER: book["units"]}
    intent = OrderIntent(
        ticker=TICKER, target_weight=weight, decision_time=_timestamp(decided)
    )
    opening = {TICKER: float(engine.data[TICKER].at[day, "abertura"])}
    book["cash"], trades = engine._settle([intent], day, opening, book["cash"], positions)
    book["units"] = positions[TICKER]
    return [
        {"type": t.type, "price": t.price, "quantity": t.quantity, "cost": t.cost}
        for t in trades
    ]


def reconcile(state, bars, session):
    """Mesmo laço do ExecutionEngine.run sobre as sessões novas do ledger.

    Abertura liquida o pendente decidido no fechamento anterior; fechamento marca
    o patrimônio. Sessões sem decisão no meio do caminho ficam MISSED (posição
    mantida). O B&H compra na primeira abertura após a primeira decisão.
    """
    engine, mark = _engine(bars), state["mark"]
    days = [session]
    if mark is not None:
        previous = _timestamp(mark["session"])
        days = list(
            pd.DatetimeIndex(
                B3Calendar().sessions_between(
                    previous.date() + timedelta(days=1), session.date()
                )
            )
        )
        if not days or days[-1] != session:
            raise ValueError("decision session does not advance the forward ledger")
        # ponytail: cada provento novo reescala a série de retorno total inteira;
        # preservar o valor marcado no último fechamento mantém o retorno total
        # entre marcas. Teto: exige a barra marcada anterior na série nova.
        ratio = mark["close"] / float(bars.at[previous, "fechamento"])
        for book in (state["portfolio"], state["benchmark"]):
            book["units"] *= ratio
    rows = []
    for day in days:
        if day not in bars.index:
            raise ValueError(f"missing bar for B3 session {day.date()}")
        row = {
            "session": str(day.date()),
            "open": float(bars.at[day, "abertura"]),
            "close": float(bars.at[day, "fechamento"]),
            "executed_decision": None,
            "trades": [],
            "benchmark_trades": [],
        }
        pending = state["pending"]
        if pending and pd.Timestamp(pending["target_session"]) == day:
            row["trades"] = _settle(
                engine, state["portfolio"], pending["target_weight"], day,
                pending["decision_session"],
            )  # fmt: skip
            row["executed_decision"], state["pending"] = pending["decision_session"], None
        if mark is not None and not state["benchmark"]["invested"]:
            row["benchmark_trades"] = _settle(
                engine, state["benchmark"], 1.0, day, mark["session"]
            )
            state["benchmark"]["invested"] = True
        for name, book in (
            ("equity", state["portfolio"]),
            ("benchmark_equity", state["benchmark"]),
        ):
            row[name] = book["cash"] + book["units"] * row["close"]
        state["peak_equity"] = max(state["peak_equity"], row["equity"])
        row["decision"] = "MISSED" if day != session else "PENDING_AT_CLOSE"
        rows.append(row)
    if state["pending"] is not None:
        raise ValueError("pending decision targets a session that was not processed")
    state["mark"] = {
        "session": str(session.date()),
        "close": float(bars.at[session, "fechamento"]),
    }
    state["sessions"].extend(rows)
    return rows


def estimate():
    """Por sessão, com as médias observadas e o preço registrados no runner OA-1."""
    price, tokens, calls = oa1.PRICE_PER_M, oa1.TOKENS, oa1.CALLS_PER_SESSION
    per_call = (
        tokens["input"] * price["input"] + tokens["output"] * price["output"]
    ) / 1e6
    worst = (
        tokens["input"] * price["input"] + oa1.MAX_OUTPUT_TOKENS * price["output"]
    ) / 1e6
    return {
        "logical_calls_expected": calls["expected"],
        "logical_calls_max": calls["max"],
        "http_attempts_max": calls["max"] * oa1.MAX_ATTEMPTS,
        "usd_expected": round(calls["expected"] * per_call, 4),
        "usd_prudent_budget": round(calls["expected"] * per_call * 2.5, 4),
        "usd_theoretical_ceiling": round(calls["max"] * oa1.MAX_ATTEMPTS * worst, 2),
        "usd_expected_per_21_sessions": round(21 * calls["expected"] * per_call, 2),
        "price_per_million_tokens_usd": price,
        "price_note": "Gemini 3.8 Flash introductory price until 2026-12-31; reconfirm in billing",
    }


def preflight(root=OUTPUT, clock=now):
    """Offline e com rede bloqueada. Nada é reservado, escrito ou chamado."""
    at, checks = clock(), {}
    session = last_closed_session(at)
    folder = root / "sessions" / str(session.date())
    deadline = target_open(session)
    report = {
        "treatment": TREATMENT,
        "classification": CLASSIFICATION,
        "paper_only": True,
        "now": at.isoformat(),
        "output": str(root),
        "calendar": {
            "decision_session": str(session.date()),
            "target_session": str(deadline.date()),
            "target_open_deadline": deadline.isoformat(),
            "calendar_version": B3_CALENDAR_VERSION,
            "verified_against_cotahist_through": CALENDAR_VERIFIED_THROUGH,
        },
    }
    with no_network():
        sha = None
        try:
            sha, spec = identity()
            report["identity"] = {
                "manifest": str(CANDIDATE.relative_to(ROOT)),
                "manifest_sha256": sha,
                "participant_sha256": PARTICIPANT_SHA256,
                "params": spec.params,
                "costs": BASE_COSTS.to_dict(),
                "execution": EXECUTION.to_dict(),
                "initial_capital": CAPITAL,
                "runner_sha256": sha_file(__file__),
                "git_head": oa1.git("rev-parse", "HEAD").stdout.strip(),
            }
            checks["treatment_identity"] = True
        except Exception as exc:  # report every identity failure, never proceed
            checks["treatment_identity"] = f"FAIL: {exc}"
        checks["after_reserved_windows"] = bool(session > FORWARD_FLOOR)
        checks["before_target_open"] = bool(at < deadline)
        checks["not_yet_decided"] = not (folder / "decision.json").exists()
        checks["no_active_lock"] = not (root / "state.json.lock").exists()
        checks["gemini_api_key_present"] = oa1.load_key()
        if (folder / "input.json").exists():
            data = read(folder / "input.json")
            report["input"] = {
                "sha256": sha_file(folder / "input.json"),
                "fetched_at": data["fetched_at"],
                "close_used": data["close_used"],
                "last_bar_official_raw": data["last_bar_official_raw"],
                "history": data["history"],
                "closed_days_before_target": data["calendar"][
                    "closed_days_before_target"
                ],
            }
            checks["input_frozen"] = (
                data["decision_session"] == str(session.date())
                and sha_file(folder / "bars.csv") == data["history"]["sha256"]
                and load_bars(folder).index[-1] == session
            )
        else:
            checks["input_frozen"] = "FAIL: run prepare first"
        if sha and checks["input_frozen"] is True:
            try:
                state = load_state(root, sha)
                preview = copy.deepcopy(state)
                report["reconciliation_preview"] = reconcile(
                    preview, load_bars(folder), session
                )
                report["portfolio_at_close"] = {
                    **preview["portfolio"],
                    "peak_equity": preview["peak_equity"],
                    "pending_before_reconciliation": state["pending"],
                }
                checks["ledger_reconciles"] = True
            except (ValueError, KeyError) as exc:
                checks["ledger_reconciles"] = f"FAIL: {exc}"
        report["estimate_per_session"] = estimate()
    report["checks"] = checks
    report["ready"] = all(value is True for value in checks.values())
    if report["ready"]:
        report["command"] = (
            ".venv\\Scripts\\python.exe -B scripts/run_h2_v6_forward.py run "
            f"--confirm {report['input']['sha256'][:12]}"
        )
    return report


class ForwardGeminiClient(DurableGeminiClient):
    """DurableGeminiClient preso a uma única sessão forward, fora das janelas reservadas."""

    def begin_session(self, session):
        self.session = str(pd.Timestamp(session).date())
        if self.bank.phase != f"{PHASE}:{self.session}":
            raise ValueError("call session differs from the forward call bank")
        LLMClient.begin_session(self, session)


def run(confirm, root=OUTPUT, clock=now, transport=None):
    """Reconcilia e decide S uma única vez. ``transport`` só existe para testes offline."""
    report = preflight(root, clock)
    if not report["ready"]:
        raise SystemExit(
            f"preflight NOT READY; nothing reserved or called: {report['checks']}"
        )
    input_sha = report["input"]["sha256"]
    if confirm != input_sha[:12]:
        raise SystemExit("--confirm must equal the first 12 hex of the input.json SHA256")
    sha, spec = identity()
    session = _timestamp(report["calendar"]["decision_session"])
    folder, deadline = root / "sessions" / str(session.date()), target_open(session)

    def gate():  # antes de cada transporte HTTP
        if sha_file(CANDIDATE) != sha or sha_file(folder / "input.json") != input_sha:
            raise JournalIntegrityError("manifest or frozen forward input changed")

    with _exclusive_state_lock(root / "state.json"):
        if (folder / "decision.json").exists():
            raise ValueError(
                "session already decided; forward inference is never repeated"
            )
        state, bars = load_state(root, sha), load_bars(folder)
        rows = reconcile(state, bars, session)
        bank = CallBank(folder / "provider.sqlite", sha, f"{PHASE}:{session.date()}")
        try:
            fresh = bank.never_reserved(
                SLOT
            )  # reservado antes: só replay, nunca nova inferência
            client = ForwardGeminiClient(
                bank, SLOT, spec.params, fresh=fresh, gate=gate,
                transport=transport, synthetic=transport is not None,
            )  # fmt: skip
            participant = build_with_client(spec, client)
            # O drawdown do Risk segue o pico da carteira forward, como na arena.
            participant._peak_equity = state["peak_equity"]
            book = state["portfolio"]
            observation = MarketObservation(
                session=session,
                history={TICKER: bars.loc[:session].copy()},
                positions={TICKER: book["units"]},
                cash=book["cash"],
                equity=rows[-1]["equity"],
            )
            failure = None
            try:
                intents = participant.decide(observation)
            except LLMDecisionError as exc:
                intents, failure = [], str(exc)
            client.assert_complete()
            _engine(bars)._validate_intents(intents, observation)
            decided_at = clock()
            status = "FAILED" if failure else "DECIDED"
            if decided_at >= deadline:
                status, intents = "LATE_NOT_EXECUTABLE", []
            trace, journal = participant.trace.artifact().content, bank.export(SLOT)
        finally:
            bank.close()
        _once(folder / "llm_trace.jsonl", trace)
        _once(folder / "provider_journal.jsonl", journal)
        last = participant.decisions[-1] if participant.decisions else None

        def dump(value):
            return None if value is None else value.model_dump(mode="json")

        equity = rows[-1]["equity"]
        decision = {
            "kind": "H2_V6_FORWARD_PAPER_DECISION",
            "treatment": TREATMENT,
            "classification": CLASSIFICATION,
            "paper_only": True,
            "decision_session": str(session.date()),
            "target_session": str(deadline.date()),
            "target_open_deadline": deadline.isoformat(),
            "generated_at": decided_at.isoformat(),
            "persisted_before_target_open": bool(decided_at < deadline),
            "status": status,
            "failure": failure,
            "close_used": float(bars.at[session, "fechamento"]),
            "input_sha256": input_sha,
            "manifest_sha256": sha,
            "participant_sha256": PARTICIPANT_SHA256,
            "runner_sha256": sha_file(__file__),
            "git_head": oa1.git("rev-parse", "HEAD").stdout.strip(),
            "replayed_from_journal": not fresh,
            "record": None if last is None else last.to_json_dict(TICKER),
            "technical_signal": None if last is None else dump(last.technical_signal),
            "risk_verdict": None if last is None else dump(last.risk_verdict),
            "portfolio_action": None if last is None else dump(last.portfolio_action),
            "intents": [
                {"ticker": i.ticker, "target_weight": i.target_weight} for i in intents
            ],
            "portfolio_at_close": {
                **book,
                "equity": equity,
                "peak_equity": state["peak_equity"],
                "drawdown": (state["peak_equity"] - equity) / state["peak_equity"],
            },
            "llm_calls": len(participant.llm_calls),
            "llm_trace_sha256": hashlib.sha256(trace).hexdigest(),
            "provider_journal_sha256": hashlib.sha256(journal).hexdigest(),
        }
        _write_once(folder / "decision.json", decision)
        rows[-1]["decision"] = status
        _write_once(
            folder / "reconciliation.json",
            {"decision_session": str(session.date()), "sessions": rows},
        )
        state["pending"] = (
            {
                "decision_session": str(session.date()),
                "target_session": str(deadline.date()),
                "target_weight": intents[0].target_weight,
            }
            if intents
            else None
        )
        state["decisions"].append(
            {
                "session": str(session.date()),
                "status": status,
                "final_cause": None if last is None else last.final_cause,
                "target_weight": intents[0].target_weight if intents else None,
                "decision_sha256": sha_file(folder / "decision.json"),
            }
        )
        # ponytail: state.json é o último passo; uma queda entre decision.json e
        # aqui deixa a sessão travada (decision existe), nunca reinferida.
        save_state(root, state)
    return decision


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=("prepare", "preflight", "run"))
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.command == "prepare":
        path = prepare()
        print(
            json.dumps({"input": str(path.relative_to(ROOT)), "sha256": sha_file(path)})
        )
        print("Next: preflight (offline).")
    elif args.command == "preflight":
        report = preflight()
        print(json.dumps(report, indent=2))
        print(
            "\nPREFLIGHT:",
            "READY" if report["ready"] else "NOT READY - no execution possible",
        )
        raise SystemExit(0 if report["ready"] else 2)
    else:
        decision = run(args.confirm)
        print(json.dumps({k: decision[k] for k in (
            "decision_session", "target_session", "status", "intents", "generated_at",
            "persisted_before_target_open", "llm_calls",
        )}, indent=2))  # fmt: skip


if __name__ == "__main__":
    main()
