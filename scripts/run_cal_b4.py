"""Frozen CAL-B4 adapter: preflight/run/audit/status, no development unlock.

Reuses the historical decision-only executor and gates. Provider envelopes are
fsynced before schema parsing. Recovery of a consumed anchor is replay-only.
"""

import argparse
import json
import os
import sys
import threading
from collections import Counter
from contextvars import ContextVar
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import h2_v6
import run_cal_b as base
from src.agents.llm_client import GeminiLLMClient, LLMCallMetadata, _decode_json_body, current_call_telemetry
from src.agents.llm_trace import LLMCallRequest, _jsonable_options, load_trace, schema_digest, schema_name
from src.agents.risk_contract import audit_risk_rationale, gate_counts
from src.agents.state import TechnicalEvidenceResponse
from src.agents.technical_analyst import build_prompt, system_prompt_for
from src.agents.technical_evidence import evidence_user_prompt, render_technical_evidence, technical_evidence_ui
from src.experiments import anchors, cal_b, treatment
from src.experiments.spec import ParticipantSpec

OUT = ROOT / "docs/evidence/cal_b4"
FREEZE = OUT / "protocol_freeze_v1.json"
GUARDS = OUT / "guards_freeze.json"
AUTH = OUT / "execution_authorization.json"
FIELDS = ("technical_evidence_factual_validity", "technical_role_signal_coherence",
          "material_unsupported_claim", "rationale_action_coherence")
FAIL = "CAL_B4_FAIL — HOLDOUT CONSUMED"
INVALID = "CAL_B4_INVALID — PARTIAL HOLDOUT CONSUMED"
AWAITING = "CAL_B4_AWAITING_PRIMARY_AUTHOR_REVIEW"
PASS = "CAL_B4_PASS — SANITY CHECK ONLY"
PENDING_REQUEST = ContextVar("cal_b4_pending_request")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def committed(path):
    rel = path.relative_to(ROOT).as_posix()
    if base.git("hash-object", rel) != base.git("rev-parse", f"HEAD:{rel}"):
        raise ValueError(f"artifact must be committed: {rel}")


def limited_authorization(document, freeze):
    """Exact identity, explicit CAL-B4 egress permission, no global bypass."""
    required = {k: freeze[k] for k in (
        "phase", "commitment_sha256", "anchors", "repetitions", "treatment_version",
        "technical_prompt_version", "technical_response_schema_version",
        "technical_evidence_vocabulary_version", "technical_evidence_validator_version",
        "risk_prompt_version", "participant_spec_sha256")}
    required.update(authorized=True, host="generativelanguage.googleapis.com",
                    accepts_normal_api_charges=True,
                    identity_clarification="USE_EXISTING_FINAL_PARTICIPANT_SPEC_WITH_STRESS_PROVENANCE",
                    scientific_payloads_only=True, validation_final_authorized=False,
                    system_freeze_authorized=False)
    if any(type(document.get(k)) is not type(v) or document[k] != v for k, v in required.items()):
        raise ValueError("CAL-B4 specific authorization/identity differs from the freeze")
    if anchors.CAL_B_AUTHORIZED is not False or anchors.CAL_B4_STATUS != "SEALED":
        raise ValueError("global unlock or consumed historical CAL-B4 is forbidden")
    if freeze["commitment_sha256"] != anchors.CAL_B4_COMMITMENT_SHA256 or (
        tuple(freeze["anchors"]) != anchors.CAL_B4_ANCHORS
        or anchors.digest(anchors.CAL_B4_ANCHORS) != freeze["commitment_sha256"]
    ):
        raise ValueError("CAL-B4 commitment/ordered anchors mismatch")
    return anchors.CalBAuthorization("CAL-B4", freeze["commitment_sha256"], tuple(freeze["anchors"]), 1)


def verify_freeze():
    f = read(FREEZE)
    committed(FREEZE)
    protocol = OUT / "PROTOCOL_FREEZE_V1.md"
    committed(protocol)
    if base.sha256_file(protocol) != f["protocol_sha256"]:
        raise ValueError("CAL-B4 frozen protocol changed")
    for path, digest in f["source_and_scientific_artifact_sha256"].items():
        if base.sha256_file(ROOT / path) != digest:
            raise ValueError(f"frozen source/scientific artifact changed: {path}")
    committed(GUARDS)
    for path, digest in read(GUARDS)["sources_sha256"].items():
        committed(ROOT / path)
        if base.sha256_file(ROOT / path) != digest:
            raise ValueError(f"CAL-B4 operational guard changed: {path}")
    if base.spec_sha256(ParticipantSpec(**f["participant_spec"])) != f["participant_spec_sha256"]:
        raise ValueError("participant hash mismatch")
    endpoint = urlsplit(os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"))
    if (endpoint.scheme != "https" or endpoint.hostname != "generativelanguage.googleapis.com"
        or endpoint.port not in (None, 443) or endpoint.path.rstrip("/") != "/v1beta"
        or endpoint.username or endpoint.query or endpoint.fragment):
        raise ValueError("only the native Gemini endpoint is allowed")
    return f


def integrity_preflight():
    f = verify_freeze()
    # Calendar-only reproduction; this check never constructs a CAL-B4 feature.
    from tests.experiments.test_cal_b4_safety import test_cal_b4_commitment_selection_and_ranking
    from select_cal_b4 import used_sessions

    test_cal_b4_commitment_selection_and_ranking()
    if set(used_sessions()) & set(anchors.CAL_B4_ANCHORS):
        raise ValueError("CAL-B4 already has scientific decision identities; fresh batch refused")
    if list((ROOT / "data/runs").glob("cal_b4_*")) or list(OUT.glob("run_*")):
        raise ValueError("existing CAL-B4 batch: only exact recovery is permitted")
    for phase in h2_v6.PHASES:
        h2_v6.committed_phase(phase)
    return f


class RawJournal(base.Journal):
    """One raw envelope per identity; any existing response disables fresh calls."""

    def __init__(self):
        super().__init__()
        self.lock = threading.Lock()

    def open(self, path, anchor):
        super().open(path, anchor)
        self.raw_path = path.with_name("provider_journal.jsonl")
        rows = [json.loads(s) for s in self.raw_path.read_text(encoding="utf-8").splitlines()] if self.raw_path.exists() else []
        self.raw_replay = {r["identity_digest"]: r["provider_envelope"] for r in rows}
        if len(rows) != len(self.raw_replay):
            raise ValueError("duplicate raw journal identity")
        self.raw_used = set()
        self.current_identities = set()
        self.attempt_path = path.with_name("provider_attempts.jsonl")
        old_attempts = [json.loads(s) for s in self.attempt_path.read_text(encoding="utf-8").splitlines()] if self.attempt_path.exists() else []
        # An HTTP success without its envelope is an uncertain crash boundary:
        # fail closed rather than make a replacement scientific inference.
        self.recovery = bool(self.raw_replay or self.replay or any(a["outcome"] == "http_200" for a in old_attempts))
        self.attempt_offset = len(getattr(base.ATTEMPTS, "attempts", []))

    def transport(self, method, url, headers, body):
        request = PENDING_REQUEST.get()
        identity = request.identity_digest
        endpoint = urlsplit(url)
        expected_path = f"/v1beta/models/{request.requested_model}:generateContent"
        if endpoint.scheme != "https" or endpoint.netloc != "generativelanguage.googleapis.com" or (
            endpoint.path != expected_path or endpoint.query or endpoint.fragment
        ):
            raise ValueError("unauthorized Gemini endpoint")
        with self.lock:
            if identity in self.raw_replay:
                if identity in self.raw_used:
                    raise ValueError("raw identity requested twice")
                self.raw_used.add(identity)
                if identity in self.replay:
                    self.replayed.add(identity)
                return json.dumps(self.raw_replay[identity]).encode("utf-8")
            if self.recovery:
                raise ValueError("consumed anchor: exact replay unavailable; fresh inference refused")
            # Transient retries have the same identity and no usable response.
            if identity in self.current_identities:
                raise ValueError("scientific identity already produced a response")
        try:
            raw = base.ATTEMPTS(method, url, headers, body)
        finally:
            with self.lock:
                rows = getattr(base.ATTEMPTS, "attempts", [])[self.attempt_offset:]
                if rows:
                    with self.attempt_path.open("a", encoding="utf-8", newline="\n") as fh:
                        for row in rows:
                            fh.write(json.dumps(row, sort_keys=True) + "\n")
                        fh.flush()
                        os.fsync(fh.fileno())
                    self.attempt_offset += len(rows)
        envelope = _decode_json_body(raw)
        with self.lock:
            with self.raw_path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps({"identity_digest": identity, "provider_envelope": envelope}, sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            self.current_identities.add(identity)
        return json.dumps(envelope).encode("utf-8")


class CalB4GeminiClient(GeminiLLMClient):
    def __init__(self, model="", **kwargs):
        super().__init__(model=model, transport=base.JOURNAL.transport, **kwargs)
        self._session = None

    def begin_session(self, session):
        self._session = base.AUTH.require_anchor(session)
        if self._session != base.JOURNAL.anchor:
            raise ValueError("session differs from active authorized anchor")

    async def generate(self, system_prompt, user_prompt, response_schema=None, options=None, *, metadata=None):
        if self._session is None:
            raise ValueError("undeclared CAL-B4 session")
        declared = metadata or LLMCallMetadata(stage="UNDECLARED")
        if declared.stage not in ("technical_analyst", "risk_manager", "portfolio_manager"):
            raise ValueError("only declared scientific stages are authorized")
        if self.model != "gemini-3.8-flash" or self.transport_options(options) != {
            "max_output_tokens": 8192, "temperature": 1.0, "thinking_level": "low"
        }:
            raise ValueError("model/generation runtime differs from development v6")
        if declared.stage == "technical_analyst":
            payload = json.loads(user_prompt)
            if user_prompt != evidence_user_prompt(payload["features"]) or (
                system_prompt != system_prompt_for({"features": payload["features"]}, 5)
                or schema_name(response_schema) != "TechnicalEvidenceResponse"
            ):
                raise ValueError("Technical scientific contract mismatch before egress")
        else:
            expected_prompt, expected_schema = {
                "risk_manager": (cal_b.RISK_SYSTEM_PROMPT_V2, "RiskVerdict"),
                "portfolio_manager": (cal_b.QUALITATIVE_SYSTEM_PROMPT, "PortfolioAction")
            }[declared.stage]
            if system_prompt != expected_prompt or schema_name(response_schema) != expected_schema:
                raise ValueError("Risk/Portfolio frozen prompt or schema mismatch")
        request = LLMCallRequest(stage=declared.stage, analyst_id=declared.analyst_id,
            decision_session=self._session, provider="gemini", requested_model=self.model,
            system_prompt=system_prompt, user_prompt=user_prompt, response_schema=schema_name(response_schema),
            response_schema_sha256=schema_digest(response_schema), requested_options=_jsonable_options(options))
        token = PENDING_REQUEST.set(request)
        try:
            response = await super().generate(system_prompt, user_prompt, response_schema, options, metadata=metadata)
            slot = current_call_telemetry()
            evidence = {} if slot is None else {n: getattr(slot, n) for n in (
                "provider_response_id", "resolved_model", "finish_reason", "raw_response", "usage", "transport_system_prompt")}
            if request.identity_digest not in base.JOURNAL.replay:
                base.JOURNAL.append({"identity_digest": request.identity_digest,
                    "stage": declared.stage, "analyst_id": declared.analyst_id,
                    "response": response.model_dump(mode="json"), "evidence": evidence})
                if request.identity_digest in base.JOURNAL.raw_replay:
                    base.JOURNAL.live -= 1
            return response
        finally:
            PENDING_REQUEST.reset(token)


def load_causal_frame():
    snapshot = base.load_dataset_snapshot(ROOT / "data/snapshots" / base.STRESS_SNAPSHOT_ID)
    base.verify_snapshot_integrity(snapshot)  # Hash bytes only, never outcomes.
    if not snapshot.scientific_ready or snapshot.identity_digest != base.H_REAL_SNAPSHOT_IDENTITY_DIGEST:
        raise ValueError("snapshot differs from corrected development snapshot")
    calendar = (ROOT / "docs/evidence/calendar/b3_official_sessions_2016-01-04_2026-08-31.txt").read_text().splitlines()
    days = [d for d in calendar if "2016-01-04" <= d <= max(base.ANCHORS)]
    record = next(r for r in snapshot.files if r["ticker"] == base.STRESS_TICKER)
    frame = base.pd.read_csv(snapshot.path / record["path"], index_col="date", parse_dates=["date"], nrows=len(days))
    frame.index = base.pd.DatetimeIndex(frame.index)
    if [str(d.date()) for d in frame.index] != days:
        raise ValueError("snapshot rows differ from causal official-calendar prefix")
    return snapshot, frame


def configure(f):
    # ponytail: process-local adapter reuses the historical runner; frozen files
    # and the global CAL-B unlock stay untouched. No other CLI uses this routing.
    base.OUT, base.PHASE, base.ANCHORS, base.PARAMS = OUT, "CAL-B4", tuple(f["anchors"]), f["participant_spec"]["params"]
    base.FREEZE, base.INVALID = "CAL_B4_PROTOCOL_FREEZE_V1", INVALID
    base.JOURNAL = RawJournal()
    base.CalBGeminiClient = CalB4GeminiClient
    base.load_frame = load_causal_frame
    base.phase_status = lambda: "SEALED"
    treatment.H2_TREATMENT_VERSION = 6
    def authorize(spec):
        committed(AUTH)
        if base.spec_sha256(spec) != f["participant_spec_sha256"]:
            raise ValueError("runtime spec differs from approved frozen spec")
        return limited_authorization(read(AUTH), f)
    base.authorize = authorize


def run(resume):
    f = verify_freeze() if resume else integrity_preflight()
    if not AUTH.exists():
        raise ValueError("CAL-B4 specific external authorization is required; development authorization is insufficient")
    configure(f)
    if resume:
        resume = inside(resume, ROOT / "data/runs")
        batch = read(resume / "batch.json")
        if batch["freeze"] != base.FREEZE or batch["participant_spec"] != f["participant_spec"] or (
            batch["authorization"]["anchors"] != f["anchors"] or batch["authorization"]["commitment_sha256"] != f["commitment_sha256"]
        ):
            raise ValueError("resume is not the exact CAL-B4 batch")
    try:
        base.run(resume)
    except (SystemExit, Exception):
        raw = list((ROOT / "data/runs").glob("cal_b4_*/anchors/*/provider_journal.jsonl"))
        if any(p.stat().st_size for p in raw):
            write(OUT / "partial_consumption.json", {"status": INVALID, "raw_journals": [p.relative_to(ROOT).as_posix() for p in raw],
                "fresh_inference_on_consumed_anchor": "FORBIDDEN", "financial_outcome": "NOT COMPUTED"})
        raise


def inside(path, parent):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(parent.resolve()) or resolved == parent.resolve():
        raise ValueError("target must be a batch inside its authorized workspace directory")
    return resolved


def status_value(automatic_pass, review):
    if not automatic_pass:
        return FAIL
    rows = (review or {}).get("anchors", {})
    values = [rows.get(a, {}).get(field) for a in anchors.CAL_B4_ANCHORS for field in FIELDS]
    if "FAIL" in values:
        return FAIL
    return PASS if all(v == "PASS" for v in values) else AWAITING


def verified_batch(target):
    f = verify_freeze()
    batch = base.verify_seal(target)
    if batch["freeze"] != "CAL_B4_PROTOCOL_FREEZE_V1" or batch["participant_spec"] != f["participant_spec"]:
        raise ValueError("batch identity differs from CAL-B4 freeze")
    if tuple(batch["anchor_seals"]) != anchors.CAL_B4_ANCHORS:
        raise ValueError("batch does not contain exactly ten ordered anchors")
    limited_authorization(read(AUTH), f)
    committed(AUTH)
    for path in target.rglob("*"):
        if path.is_file() and path.name not in ("automatic_gates.json", "audit_packet.json", "AUDIT_PACKET.md", "status.json") and "review" not in path.parts:
            committed(path)
    if base.git("status", "--porcelain"):
        raise ValueError("raw sealed batch must be committed on a clean tree before audit")
    for a, digest in batch["anchor_seal_sha256"].items():
        if base.sha256_file(target / "anchors" / a / "sealed.json") != digest:
            raise ValueError("anchor seal changed")
    return f, batch


def audit(target):
    f, batch = verified_batch(target)
    if (target / "automatic_gates.json").exists():
        raise ValueError("automatic audit already exists; no overwrite of review/results")
    configure(f)
    _, frame = base.load_frame()
    p = base.PARAMS
    packets, issues_by_anchor, technical, risk_rows, verdicts, causes, all_records, attempts = [], {}, [], [], [], [], [], []
    for anchor in base.ANCHORS:
        adir = target / "anchors" / anchor
        info = read(adir / "anchor.json")
        lines = (adir / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
        decision = json.loads(lines[0]) if len(lines) == 1 else None
        records = list(load_trace((adir / "llm_calls.jsonl").read_bytes()))
        history = base.history_until(frame, anchor)
        probe = base.LLMParticipant(base.STRESS_TICKER, llm_client=base.MockLLMClient(), strict_inputs=True, volatility_window=21)
        state = probe._agent_state(base.frozen_observation(base.HardeningState(anchor, base.STRESS_TICKER, history), 100000.0),
            history, 100000.0, float(history["fechamento"].iloc[-1]))
        # The legacy gate accepts free-text Technical v1. Adapt only an audit
        # copy after validating the real structured payload via the v6 validator.
        compatible, extra, structural = [], [], []
        for r in records:
            if r.request.stage == "technical_analyst" and r.status == "ok":
                try:
                    payload = json.loads(r.request.user_prompt)
                    rendered = render_technical_evidence(r.validated_response, payload["features"], payload["allowed_evidence_codes"])
                    if r.request.user_prompt != evidence_user_prompt(state["features"]):
                        extra.append(f"{r.call_id}: real v6 payload differs from causal features/allowed set")
                    if r.request.response_schema != "TechnicalEvidenceResponse":
                        structural.append(f"{r.call_id}: real schema version mismatch")
                    compatible.append(replace(r, request=replace(r.request, response_schema="TechnicalSignal",
                        user_prompt=build_prompt({"features": state["features"]})),
                        validated_response={"signal": r.validated_response["signal"], "confidence": r.validated_response["confidence"], "justification": rendered}))
                except (ValueError, TypeError, KeyError):
                    compatible.append(r)
                    extra.append(f"{r.call_id}: invalid structured payload")
            else:
                compatible.append(r)
        issues = cal_b.anchor_issues(anchor, decision, compatible, state["features"], base.canonical_number(state["recent_volatility"]), info["history_last_session"], p)
        issues["CB-C"].extend(extra)
        issues["CB-S"].extend(structural)
        for r in records:
            expected_schema = {"technical_analyst": "TechnicalEvidenceResponse", "risk_manager": "RiskVerdict", "portfolio_manager": "PortfolioAction"}.get(r.request.stage)
            if r.request.response_schema != expected_schema or r.request.response_schema_sha256 != schema_digest({
                "TechnicalEvidenceResponse": TechnicalEvidenceResponse,
                "RiskVerdict": cal_b.SCHEMAS["RiskVerdict"], "PortfolioAction": cal_b.SCHEMAS["PortfolioAction"]}.get(expected_schema)):
                issues["CB-S"].append(f"{r.call_id}: schema identity mismatch")
            if r.request.stage == "technical_analyst" and any(t in r.request.system_prompt + r.request.user_prompt for t in (anchor, p["ticker"].split(".")[0], "R$")):
                issues["CB-C"].append(f"{r.call_id}: forbidden Technical identity/price")
        issues_by_anchor[anchor] = issues
        ta = h2_v6.technical_audit(records)
        technical.append(ta)
        per_risk = []
        for r in records:
            if r.request.stage == "risk_manager" and r.status == "ok":
                v = r.validated_response
                found = audit_risk_rationale(v["analysis"], v["verdict"], json.loads(r.request.user_prompt))
                per_risk.append({"call_id": r.call_id, "gates": gate_counts(found), "findings": found})
                verdicts.append(v["verdict"])
        risk_rows.extend(per_risk)
        causes.append(decision["final_cause"] if decision else None)
        calls = [dict(r.to_json_dict(), **({"technical_ui": technical_evidence_ui(r.validated_response,
            json.loads(r.request.user_prompt)["features"], json.loads(r.request.user_prompt)["allowed_evidence_codes"])}
            if r.request.stage == "technical_analyst" and r.status == "ok" else {})) for r in records]
        packets.append({"anchor": anchor, "features": state["features"], "allowed_evidence_codes": json.loads(evidence_user_prompt(state["features"]))["allowed_evidence_codes"],
            "decision": decision, "calls": calls, "technical_audit": ta, "risk_audit": per_risk,
            "hard_risk": {"recent_volatility": state["recent_volatility"], "current_drawdown": 0.0, "current_concentration": 0.0,
                "volatility_exercised": bool(decision and decision["risk_rule"] == "VOLATILITY"), "drawdown_coverage": "NOT_EXERCISED", "concentration_coverage": "NOT_EXERCISED"}})
        all_records.extend(records)
        attempts.extend(json.loads(s) for s in (adir / "provider_attempts.jsonl").read_text(encoding="utf-8").splitlines())
    gates = {}
    for old, new in (("CB-A", "CB4-A"), ("CB-S", "CB4-S"), ("CB-C", "CB4-C"), ("CB-R", "CB4-HR")):
        problems = {a: row[old] for a, row in issues_by_anchor.items() if row[old]}
        value = sum(len(v) for v in problems.values())
        if new == "CB4-A" and sum(c is not None for c in causes) != 10:
            value += 1
        gates[new] = {"value": value, "threshold": "== 0", "issues": problems, "pass": value == 0}
    for name in ("E", "S1", "S2", "S3"):
        value = sum(t[f"V6-{name}"] for t in technical)
        gates[f"CB4-{name}"] = {"value": value, "threshold": "== 0", "pass": value == 0}
    for name in ("R1", "R2", "R3"):
        value = sum(r["gates"][f"V3-{name}"] for r in risk_rows)
        gates[f"CB4-{name}"] = {"value": value, "threshold": "== 0", "pass": value == 0}
    rates = cal_b.hold_rates(causes)
    gates["CB4-D"] = {"value": rates["total_hold_rate"], "threshold": "< 0.90", "pass": rates["total_hold_rate"] is not None and rates["total_hold_rate"] < 0.90}
    activity = cal_b.risk_activity(verdicts)
    if not activity["VETOED"]:
        activity["RISK_LLM_DISCRETIONARY_VETO"] = "NOT_OBSERVED"
    usage = [r.token_usage or {} for r in all_records]
    latency = [r.duration_ms for r in all_records]
    report = {"kind": "CAL_B4_AUTOMATIC_GATES", "freeze": batch["freeze"], "batch_git_commit": batch["git_commit"],
        "audit_git_commit": base.git("rev-parse", "HEAD"), "gates": gates, "automatic_pass": all(g["pass"] for g in gates.values()),
        "hold_rates": rates, "action_distribution": {"final_cause": dict(Counter(causes)), "technical_consensus": dict(Counter(
            p["decision"]["technical_outcome"] for p in packets if p["decision"])), "technical_votes": dict(Counter(
            r.validated_response["signal"] for r in all_records if r.request.stage == "technical_analyst" and r.status == "ok"))},
        "risk_discretionary_activity": activity, "financial_outcome": "NOT COMPUTED", "validation_final_access": False,
        "system_freeze_executed": False, "second_review": "NOT_REVIEWED — NONBLOCKING",
        "operational": {"logical_calls": len(all_records), "http_attempts": len(attempts), "retries": max(0, len(attempts) - len(all_records)),
            "transient_errors": sum(a["outcome"] != "http_200" for a in attempts), "final_errors": sum(r.status != "ok" for r in all_records),
            "latency_ms_p50": float(base.np.percentile(latency, 50)) if latency else None,
            "latency_ms_p90": float(base.np.percentile(latency, 90)) if latency else None,
            **{k: sum(u.get(source) or 0 for u in usage) for k, source in (("input_tokens", "prompt_tokens"), ("output_tokens", "completion_tokens"), ("thinking_tokens", "thoughts_tokens"))},
            "monetary_cost": "NOT COMPUTED — NO FROZEN PRICING"}}
    report["status"] = status_value(report["automatic_pass"], None)
    write(target / "automatic_gates.json", report)
    write(target / "audit_packet.json", packets)
    write(target / "review/PRIMARY_AUTHOR.json", {"reviewer": None, "reviewed_utc": None, "instructions": "PASS/FAIL por campo; apenas o usuário preenche. Incoerência material; discordância do sinal não é FAIL.",
        "anchors": {a: dict.fromkeys(FIELDS) for a in base.ANCHORS}})
    write(target / "review/SECOND_AUTHOR_OPTIONAL.json", {"status": "NOT_REVIEWED — NONBLOCKING"})
    md = ["# CAL-B4 audit packet", "", "FINANCIAL_OUTCOME = NOT COMPUTED", "",
        "Revisão obrigatória: PRIMARY_AUTHOR.json. Quatro campos por anchor; nenhuma regra determinística roles/signal.",
        "FAIL apenas por incoerência material, fatos/regra não fornecidos ou rationale/ação incoerentes.",
        "Não reprovar porque escolheria outro sinal. Segunda revisão NOT_REVIEWED — NONBLOCKING.", ""]
    for row in packets:
        md += [f"## {row['anchor']}", "", "```json", json.dumps(row, indent=2, ensure_ascii=False), "```", ""]
    (target / "AUDIT_PACKET.md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    write(target / "AUDIT_SEAL.json", {name: base.sha256_file(target / name) for name in (
        "automatic_gates.json", "audit_packet.json", "AUDIT_PACKET.md")})
    print(report["status"])


def status(target):
    verified_batch(target)
    report = read(target / "automatic_gates.json")
    committed(target / "automatic_gates.json")
    committed(target / "AUDIT_SEAL.json")
    for name, digest in read(target / "AUDIT_SEAL.json").items():
        if base.sha256_file(target / name) != digest:
            raise ValueError("automatic gates/packet changed after audit")
    expected = {f"CB4-{k}" for k in ("A", "E", "S", "C", "HR", "S1", "S2", "S3", "R1", "R2", "R3", "D")}
    if set(report["gates"]) != expected or report["automatic_pass"] != all(g["pass"] for g in report["gates"].values()):
        raise ValueError("automatic gate status is inconsistent")
    review = read(target / "review/PRIMARY_AUTHOR.json")
    state = status_value(report["automatic_pass"], review)
    if state in (PASS, FAIL) and report["automatic_pass"]:
        committed(target / "review/PRIMARY_AUTHOR.json")
        if not review.get("reviewer") or not review.get("reviewed_utc"):
            raise ValueError("completed primary review requires the user's reviewer identity and date")
    write(target / "status.json", {"status": state, "SYSTEM_CALIBRATION_COMPLETE": state == PASS,
        "H2_FINAL_TREATMENT_VERSION": 6, "H2_FINAL_PARAMETERS": "21 / 0.50 / 0.25 / 1.0",
        "next_step": "READY FOR SYSTEM FREEZE DESIGN" if state == PASS else "STOP — NO RERUN",
        "system_freeze_executed": False, "validation_final_access": False, "financial_outcome": "NOT COMPUTED"})
    print(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "run", "audit", "status"))
    parser.add_argument("target", nargs="?", type=Path)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    if args.command == "preflight":
        integrity_preflight()
        print("CAL_B4_HOLDOUT_INTEGRITY = PRESERVED; SEALED — NOT EXECUTED")
        print("External authorization and spec hash clarification required before live.")
    elif args.command == "run":
        run(args.resume)
    elif args.target:
        target = inside(args.target, OUT)
        {"audit": audit, "status": status}[args.command](target)
    else:
        parser.error("audit/status require a sealed batch target")


if __name__ == "__main__":
    main()
