"""CAL-B do H2 (Amendment 7, CAL_B_PROTOCOL_FREEZE_V1): sanity check one-shot.

Três passos, cada um sobre um commit limpo:

``run``     batch selado: as 10 âncoras comprometidas x R=1, uma realização live
            cada, só com o information set até close(t). Nenhuma execução em
            open(t+1), nenhum preço posterior, nenhuma métrica financeira. O
            progresso impresso não mostra conteúdo de decisão. Cada resposta
            live é gravada (fsync) num journal por âncora ANTES de seguir:
            depois de um crash, ``run --resume DIR`` reaproveita as respostas já
            observadas por replay exato de identidade (nunca nova inferência
            para substituí-las); âncora sem nenhuma resposta não foi consumida.
``audit``   depois do selo: gates automáticos CB-A/S/C/R/D, pacote
            comportamental para os autores e fichas de revisão em branco.
``status``  aplica a regra congelada aos gates e às duas revisões humanas.

Uso: ``python scripts/run_cal_b.py run [--resume data/runs/cal_b_X]`` ·
``audit docs/evidence/cal_b/run_X`` · ``status docs/evidence/cal_b/run_X``.
"""

import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_h2_hardening import AttemptLog, git, load_key  # noqa: E402

import src.agents.participant as participant_module  # noqa: E402
from src.agents.features import canonical_number  # noqa: E402
from src.agents.llm_client import GeminiLLMClient, LLMCallMetadata, MockLLMClient, current_call_telemetry  # noqa: E402
from src.agents.llm_trace import (  # noqa: E402
    STAGE_UNDECLARED,
    LLMCallRequest,
    _jsonable_options,
    load_trace,
    schema_digest,
    schema_name,
    session_key,
)
from src.agents.participant import LLMDecisionError, LLMParticipant  # noqa: E402
from src.experiments import anchors, cal_b  # noqa: E402
from src.experiments.anchors import CAL_B_ANCHORS, CAL_B_COMMITMENT_SHA256, CAL_B_PHASE, CAL_B_REPETITIONS  # noqa: E402
from src.experiments.hardening import H_REAL_SNAPSHOT_IDENTITY_DIGEST, HardeningState, frozen_observation  # noqa: E402
from src.experiments.participants import build_participant, preflight_participant  # noqa: E402
from src.experiments.spec import ParticipantSpec  # noqa: E402
from src.experiments.stress import STRESS_SNAPSHOT_ID, STRESS_TICKER  # noqa: E402
from src.pipeline.snapshot import load_dataset_snapshot, load_snapshot_frames, verify_snapshot_integrity  # noqa: E402

OUT = ROOT / "docs" / "evidence" / "cal_b"
ATTEMPTS = AttemptLog(timeout=120.0)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frame() -> tuple[Any, pd.DataFrame]:
    snapshot = load_dataset_snapshot(ROOT / "data" / "snapshots" / STRESS_SNAPSHOT_ID)
    verify_snapshot_integrity(snapshot)
    if not snapshot.scientific_ready or snapshot.identity_digest != H_REAL_SNAPSHOT_IDENTITY_DIGEST:
        sys.exit("CAL-B snapshot is not the READY corrected snapshot")
    return snapshot, load_snapshot_frames(snapshot, (STRESS_TICKER,))[STRESS_TICKER]


def history_until(frame: pd.DataFrame, anchor: str) -> pd.DataFrame:
    """Information set: barras até close(t), nada depois."""
    history = frame.loc[: pd.Timestamp(anchor)]
    if str(history.index[-1].date()) != anchor:
        raise ValueError(f"{anchor} is not a snapshot session")
    return history


# ── journal: cada resposta live persistida antes de seguir ───────


class Journal:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.anchor: str | None = None
        self.replay: dict[str, dict[str, Any]] = {}
        self.replayed: set[str] = set()
        self.live = 0

    def open(self, path: Path, anchor: str) -> None:
        self.path, self.anchor, self.replayed, self.live = path, anchor, set(), 0
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        self.replay = {e["identity_digest"]: e for e in map(json.loads, lines)}

    def append(self, entry: dict[str, Any]) -> None:
        assert self.path is not None
        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self.live += 1


JOURNAL = Journal()
AUTH: anchors.CalBAuthorization | None = None


class CalBGeminiClient(GeminiLLMClient):
    """Gemini nativo com a tranca da CAL-B e o journal de recuperação exata."""

    def __init__(self, model: str = "", **kwargs: Any) -> None:
        super().__init__(model=model, transport=ATTEMPTS, **kwargs)
        self._session: str | None = None

    def begin_session(self, session: Any) -> None:
        assert AUTH is not None
        key = AUTH.require_anchor(session)
        if key != JOURNAL.anchor:
            raise RuntimeError(f"session {key} is not the CAL-B anchor being executed")
        self._session = key

    async def generate(self, system_prompt: str, user_prompt: str, response_schema: type[BaseModel] | None = None,
                       options: dict[str, Any] | None = None, *, metadata: LLMCallMetadata | None = None):
        declared = metadata or LLMCallMetadata(stage=STAGE_UNDECLARED)
        if self._session is None:
            raise RuntimeError("CAL-B call without a declared anchor")
        request = LLMCallRequest(
            stage=declared.stage, analyst_id=declared.analyst_id, decision_session=self._session,
            provider="gemini", requested_model=self.model, system_prompt=system_prompt, user_prompt=user_prompt,
            response_schema=schema_name(response_schema), response_schema_sha256=schema_digest(response_schema),
            requested_options=_jsonable_options(options),
        )
        slot = current_call_telemetry()
        hit = JOURNAL.replay.get(request.identity_digest)
        if hit is not None:  # resposta já observada: replay exato, nunca nova inferência
            if request.identity_digest in JOURNAL.replayed:
                raise RuntimeError("journal identity requested twice")
            JOURNAL.replayed.add(request.identity_digest)
            if slot is not None:
                for name, value in hit["evidence"].items():
                    setattr(slot, name, value)
            return hit["response"] if response_schema is None else response_schema.model_validate(hit["response"])
        response = await super().generate(system_prompt, user_prompt, response_schema, options, metadata=metadata)
        evidence = {} if slot is None else {
            name: getattr(slot, name) for name in ("provider_response_id", "resolved_model", "finish_reason",
                                                   "raw_response", "usage", "transport_system_prompt")}
        JOURNAL.append({
            "identity_digest": request.identity_digest, "stage": request.stage, "analyst_id": request.analyst_id,
            "response": response.model_dump(mode="json") if isinstance(response, BaseModel) else response,
            "evidence": evidence,
        })
        return response


# ── run: batch selado ────────────────────────────────────────────


def run(resume: Path | None) -> None:
    global AUTH
    if git("status", "--porcelain"):
        sys.exit("working tree is not clean: commit the CAL-B freeze first")
    if anchors.CAL_B_AUTHORIZED is not False:
        sys.exit("the global CAL-B unlock must stay False; only the limited authorization opens CAL-B")
    if anchors.digest(CAL_B_ANCHORS) != CAL_B_COMMITMENT_SHA256:
        sys.exit("CAL-B anchors do not match the full commitment hash")
    AUTH = anchors.authorize_cal_b(CAL_B_PHASE, CAL_B_COMMITMENT_SHA256, CAL_B_ANCHORS, CAL_B_REPETITIONS)
    commit = git("rev-parse", "HEAD")
    snapshot, frame = load_frame()
    spec = ParticipantSpec("llm_agent", dict(cal_b.CAL_B_FROZEN_PARAMS))
    preflight_participant(spec, scientific=True)
    if resume is None:
        out = ROOT / "data" / "runs" / f"cal_b_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        out.mkdir(parents=True)
        batch = {"kind": "CAL_B_SEALED_BATCH", "freeze": cal_b.CAL_B_PROTOCOL_FREEZE, "git_commit": commit,
                 "started_utc": now(), "authorization": {
                     "phase": AUTH.phase, "commitment_sha256": AUTH.commitment_sha256,
                     "anchors": list(AUTH.anchors), "repetitions": AUTH.repetitions,
                     "global_cal_b_authorized": anchors.CAL_B_AUTHORIZED, "cal_b_status_at_start": anchors.CAL_B_STATUS},
                 "snapshot": {"snapshot_id": snapshot.snapshot_id, "identity_digest": snapshot.identity_digest,
                              "files": [dict(f) for f in snapshot.files]},
                 "participant_spec": spec.to_dict(), "spec_hash_inputs": "ParticipantSpec only; no evaluation window",
                 "initial_capital": cal_b.CAL_B_INITIAL_CAPITAL}
        (out / "batch.json").write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8", newline="\n")
    else:
        out = (ROOT / resume).resolve()
        batch = json.loads((out / "batch.json").read_text(encoding="utf-8"))
        if batch["git_commit"] != commit:
            sys.exit("--resume must run on the same commit: no code change in the middle of the batch")
    load_key()
    participant_module.PROVIDER_CLIENTS["gemini"] = CalBGeminiClient  # type: ignore[index]
    clock = time.perf_counter()
    for k, anchor in enumerate(AUTH.anchors, 1):
        adir = out / "anchors" / anchor
        if (adir / "sealed.json").exists():
            continue  # consumida: nunca reexecutada
        adir.mkdir(parents=True, exist_ok=True)
        JOURNAL.open(adir / "journal.jsonl", anchor)
        recovery = bool(JOURNAL.replay)
        history = history_until(frame, anchor)
        participant = build_participant(spec)
        assert isinstance(participant, LLMParticipant)
        attempts_before = len(ATTEMPTS.attempts)
        tick = time.perf_counter()
        try:
            intents = participant.decide(frozen_observation(HardeningState(f"cal-b:{anchor}", STRESS_TICKER, history),
                                                            cal_b.CAL_B_INITIAL_CAPITAL))
            failure = None
        except LLMDecisionError as exc:
            intents, failure = [], f"{exc.reason}: {exc}"
        unused = set(JOURNAL.replay) - JOURNAL.replayed
        if failure is not None or unused:
            attempt = len(list(adir.glob("failed_*"))) + 1
            fdir = adir / f"failed_{attempt}"
            fdir.mkdir()
            (fdir / "llm_calls.jsonl").write_bytes(participant.trace.artifact().content)
            (fdir / "failure.json").write_text(json.dumps({"failure": failure, "unused_journal": sorted(unused),
                                                           "at_utc": now()}, indent=2), encoding="utf-8")
            consumed = (adir / "journal.jsonl").exists() and (adir / "journal.jsonl").stat().st_size > 0
            if unused:
                print(cal_b.CAL_B_INVALID, f"({anchor}: persisted responses could not be replayed exactly)", flush=True)
                sys.exit(2)
            print(f"[{k}/10] {anchor} FAILED; holdout {'PARTIALLY CONSUMED (resume replays it)' if consumed else 'NOT consumed'}",
                  flush=True)
            sys.exit(1)
        decisions = participant.decisions_artifact().content
        (adir / "llm_calls.jsonl").write_bytes(participant.trace.artifact().content)
        (adir / "decisions.jsonl").write_bytes(decisions)
        (adir / "intents.json").write_text(json.dumps(
            [{"ticker": i.ticker, "target_weight": i.target_weight} for i in intents], indent=2) + "\n",
            encoding="utf-8", newline="\n")
        attempts = ATTEMPTS.attempts[attempts_before:]
        (adir / "attempts.jsonl").write_text("".join(json.dumps(a, sort_keys=True) + "\n" for a in attempts),
                                             encoding="utf-8", newline="\n")
        (adir / "anchor.json").write_text(json.dumps({
            "anchor": anchor, "repetition": 1, "history_rows": len(history),
            "history_first_session": str(history.index[0].date()), "history_last_session": str(history.index[-1].date()),
            "execution": "none: decision and intent only; open(t+1) never read",
            "recovery_used": recovery, "replayed_calls": len(JOURNAL.replayed), "live_calls": JOURNAL.live,
            "wall_clock_seconds": round(time.perf_counter() - tick, 1), "sealed_utc": now(),
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
        files = sorted(p for p in adir.iterdir() if p.is_file() and p.name != "sealed.json")
        (adir / "sealed.json").write_text(json.dumps({p.name: sha256_file(p) for p in files}, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
        print(f"[{k}/10] {anchor} sealed ({time.perf_counter() - clock:.0f}s)", flush=True)

    seals = {a: json.loads((out / "anchors" / a / "sealed.json").read_text(encoding="utf-8")) for a in AUTH.anchors}
    batch.update({"finished_utc": now(), "complete": True, "anchor_seals": seals,
                  "anchor_seal_sha256": {a: sha256_file(out / "anchors" / a / "sealed.json") for a in AUTH.anchors}})
    (out / "batch.json").write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8", newline="\n")
    target = OUT / out.name.replace("cal_b_", "run_")
    shutil.copytree(out, target)
    (target / "BATCH_SEAL.sha256").write_text(sha256_file(target / "batch.json") + "  batch.json\n",
                                              encoding="utf-8", newline="\n")
    print("SEALED", target.as_posix(), flush=True)


# ── audit: depois do selo ────────────────────────────────────────


def verify_seal(target: Path) -> dict[str, Any]:
    batch = json.loads((target / "batch.json").read_text(encoding="utf-8"))
    expected = (target / "BATCH_SEAL.sha256").read_text(encoding="utf-8").split()[0]
    if sha256_file(target / "batch.json") != expected or not batch.get("complete"):
        sys.exit("batch seal does not verify")
    for anchor, files in batch["anchor_seals"].items():
        for name, digest in files.items():
            if sha256_file(target / "anchors" / anchor / name) != digest:
                sys.exit(f"artifact {anchor}/{name} changed after sealing")
    return batch


def audit(target: Path) -> None:
    batch = verify_seal(target)
    _, frame = load_frame()
    p = cal_b.CAL_B_FROZEN_PARAMS
    gates_by_anchor, packet, flags, causes, operational = {}, [], {}, [], []
    for anchor in CAL_B_ANCHORS:
        adir = target / "anchors" / anchor
        info = json.loads((adir / "anchor.json").read_text(encoding="utf-8"))
        lines = (adir / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
        decision = json.loads(lines[0]) if len(lines) == 1 else None
        records = list(load_trace((adir / "llm_calls.jsonl").read_bytes()))
        history = history_until(frame, anchor)  # só até t, como na decisão
        probe = LLMParticipant(STRESS_TICKER, llm_client=MockLLMClient(), strict_inputs=True,
                            volatility_window=p["volatility_window"])
        state = probe._agent_state(frozen_observation(HardeningState(anchor, STRESS_TICKER, history),
                                                      cal_b.CAL_B_INITIAL_CAPITAL),
                                   history, cal_b.CAL_B_INITIAL_CAPITAL, float(history["fechamento"].iloc[-1]))
        volatility = canonical_number(state["recent_volatility"])
        issues = cal_b.anchor_issues(anchor, decision, records, state["features"], volatility,
                                     info["history_last_session"])
        gates_by_anchor[anchor] = issues
        causes.append(decision["final_cause"] if decision else None)
        calls, anchor_flags = [], []
        for r in records:
            text = (r.validated_response or {}).get(cal_b.RATIONALE_FIELDS[r.request.response_schema], "")
            hits = cal_b.prescreen(text)
            anchor_flags += [{"call_id": r.call_id, **h} for h in hits]
            calls.append({"call_id": r.call_id, "stage": r.request.stage, "analyst_id": r.request.analyst_id,
                          "system_prompt": r.request.system_prompt, "user_prompt": r.request.user_prompt,
                          "visible_output": r.validated_response, "finish_reason": r.finish_reason,
                          "prescreen_flags": hits})
        flags[anchor] = anchor_flags
        packet.append({
            "anchor": anchor, "technical_feature_payload": state["features"],
            "consensus": {k: decision[k] for k in ("vote_counts", "valid_votes", "consensus_reached",
                                                   "technical_outcome")} if decision else None,
            "reason_codes": {k: decision[k] for k in ("risk_verdict", "risk_source", "risk_rule", "portfolio_called",
                                                      "portfolio_source", "portfolio_rule", "portfolio_decision",
                                                      "target_weight", "final_cause")} if decision else None,
            "calls": calls,
        })
        usage = [r.token_usage or {} for r in records]
        attempts = [json.loads(x) for x in (adir / "attempts.jsonl").read_text(encoding="utf-8").splitlines()]
        operational.append({
            "anchor": anchor, "logical_calls": len(records),
            "by_stage": {s: sum(r.request.stage == s for r in records)
                         for s in ("technical_analyst", "risk_manager", "portfolio_manager")},
            "http_attempts": len(attempts), "retries": sum(r.retry_count for r in records),
            "attempt_outcomes": {o: sum(a["outcome"] == o for a in attempts) for o in {a["outcome"] for a in attempts}},
            "input_tokens": sum(u.get("prompt_tokens") or 0 for u in usage),
            "output_tokens": sum(u.get("completion_tokens") or 0 for u in usage),
            "thinking_tokens": sum(u.get("thoughts_tokens") or 0 for u in usage),
            "latency_ms_total": round(sum(r.duration_ms for r in records), 1),
            "recovery_used": info["recovery_used"],
        })
    rates = cal_b.hold_rates([c for c in causes if c is not None])
    gates = {g: {"issues": {a: i[g] for a, i in gates_by_anchor.items() if i[g]},
                 "pass": not any(i[g] for i in gates_by_anchor.values())} for g in ("CB-A", "CB-S", "CB-C", "CB-R")}
    gates["CB-A"]["pass"] = gates["CB-A"]["pass"] and sum(c is not None for c in causes) == len(CAL_B_ANCHORS)
    gates["CB-D"] = {"total_hold_rate": rates["total_hold_rate"], "threshold": ">= 0.90 fails",
                     "pass": not rates["degenerate_inactive"]}
    report = {
        "kind": "CAL_B_AUTOMATIC_GATES", "freeze": cal_b.CAL_B_PROTOCOL_FREEZE, "computed_utc": now(),
        "git_commit": git("rev-parse", "HEAD"), "batch_commit": batch["git_commit"],
        "anchors_x_repetitions": f"{len(CAL_B_ANCHORS)} x {CAL_B_REPETITIONS}",
        "gates": gates, "automatic_pass": all(g["pass"] for g in gates.values()),
        "hold_rates": rates, "action_distribution": {
            "final_cause": dict(sorted(pd.Series(causes).value_counts().items())),
            "technical_outcome": dict(sorted(pd.Series([e["consensus"]["technical_outcome"] for e in packet
                                                        if e["consensus"]]).value_counts().items()))},
        "prescreen_flags_by_anchor": flags,
        "prescreen_note": "lexical flags only point reviewers to text; classification is human",
        "operational": operational,
        "financial_outcome": "NOT COMPUTED (no t+1 price read, no return/P&L/Sharpe/Sortino/MDD/accuracy)",
    }
    (target / "automatic_gates.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=int) + "\n",
                                                 encoding="utf-8", newline="\n")
    (target / "audit_packet.json").write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8", newline="\n")
    md = ["# CAL-B — pacote comportamental (sem resultado financeiro)", "",
          "Classifique cada âncora de forma independente em `review/AUTHOR_1.json` ou `review/AUTHOR_2.json`:",
          "`material_hallucination` e `rationale_action_coherence` = PASS ou FAIL. Avalie só o texto visível de",
          "cada estágio contra o prompt daquele estágio. Marcas do pré-filtro léxico são só ponteiros.", ""]
    for e in packet:
        md += [f"## {e['anchor']}", "", f"Features: `{json.dumps(e['technical_feature_payload'], sort_keys=True)}`", "",
               f"Consenso: `{json.dumps(e['consensus'], ensure_ascii=False)}`", "",
               f"Códigos: `{json.dumps(e['reason_codes'], ensure_ascii=False)}`", ""]
        for c in e["calls"]:
            md += [f"### {c['stage']}" + (f" #{c['analyst_id']}" if c["analyst_id"] else ""), "",
                   "System prompt:", "", "```text", c["system_prompt"], "```", "", "User prompt:", "", "```text",
                   c["user_prompt"], "```", "", "Saída visível:", "", "```json",
                   json.dumps(c["visible_output"], indent=2, ensure_ascii=False), "```", ""]
            if c["prescreen_flags"]:
                md += ["Pré-filtro: " + ", ".join(f"`{h['category']}:{h['match']}`" for h in c["prescreen_flags"]), ""]
    (target / "audit_packet.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    review = target / "review"
    review.mkdir(exist_ok=True)
    for author in ("AUTHOR_1", "AUTHOR_2"):
        path = review / f"{author}.json"
        if not path.exists():
            path.write_text(json.dumps({"reviewer": None, "reviewed_utc": None, "anchors": {
                a: {"material_hallucination": None, "rationale_action_coherence": None, "notes": ""}
                for a in CAL_B_ANCHORS}}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("automatic_pass", "hold_rates", "action_distribution")},
                     indent=1, default=int))
    print(json.dumps({g: v["pass"] for g, v in gates.items()}))


def status(target: Path) -> None:
    verify_seal(target)
    report = json.loads((target / "automatic_gates.json").read_text(encoding="utf-8"))
    reviews = [json.loads((target / "review" / f"{a}.json").read_text(encoding="utf-8"))
               for a in ("AUTHOR_1", "AUTHOR_2") if (target / "review" / f"{a}.json").exists()]
    result = cal_b.cal_b_status(report["automatic_pass"], reviews, CAL_B_ANCHORS)
    record = {"kind": "CAL_B_STATUS", "computed_utc": now(), "status": result,
              "automatic_pass": report["automatic_pass"], "consumption": "CONSUMED (10/10 anchors, R=1)",
              "system_calibration_complete": result == cal_b.CAL_B_PASS,
              "next": "READY FOR SYSTEM FREEZE" if result == cal_b.CAL_B_PASS else None}
    (target / "status.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "run":
        run(Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[2] == "--resume" else None)
    elif command in ("audit", "status"):
        {"audit": audit, "status": status}[command]((ROOT / sys.argv[2]).resolve())
    else:
        sys.exit(__doc__)
