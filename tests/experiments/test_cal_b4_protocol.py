"""Offline guard/recovery checks; synthetic payloads only, no holdout features."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from scripts import run_cal_b4 as cb
from src.agents.llm_client import LLMCallMetadata, ProviderTransportError
from src.agents.technical_evidence import TechnicalEvidenceResponse, evidence_user_prompt

FEATURES = {"sma50_gap": 0.1, "sma200_gap": 0.1, "macd_ratio": 0.01,
            "macd_signal_ratio": 0.0, "rsi": 50.0, "bb_upper_gap": -0.1,
            "bb_lower_gap": 0.1, "bb_width": 0.2}
RESPONSE = {"signal": "COMPRA", "confidence": 0.5,
            "evidence": [{"code": "CLOSE_ABOVE_SMA50", "role": "SUPPORTS_COMPRA"}]}


def authorization():
    f = cb.read(cb.FREEZE)
    doc = {k: f[k] for k in ("phase", "commitment_sha256", "anchors", "repetitions", "treatment_version",
        "technical_prompt_version", "technical_response_schema_version", "technical_evidence_vocabulary_version",
        "technical_evidence_validator_version", "risk_prompt_version", "participant_spec_sha256")}
    doc.update(authorized=True, host="generativelanguage.googleapis.com", accepts_normal_api_charges=True,
        identity_clarification="USE_EXISTING_FINAL_PARTICIPANT_SPEC_WITH_STRESS_PROVENANCE",
        scientific_payloads_only=True, validation_final_authorized=False, system_freeze_authorized=False)
    return doc, f


def test_limited_authorization_and_every_frozen_field_fail_closed():
    doc, f = authorization()
    auth = cb.limited_authorization(doc, f)
    assert auth.anchors == cb.anchors.CAL_B4_ANCHORS
    assert auth.require_anchor(auth.anchors[0]) == auth.anchors[0]
    with pytest.raises(ValueError):
        auth.require_anchor("2024-09-02")
    for key in doc:
        changed = {**doc, key: None}
        with pytest.raises(ValueError):
            cb.limited_authorization(changed, f)
    with pytest.raises(ValueError):
        cb.limited_authorization({**doc, "repetitions": True}, f)
    with pytest.raises(ValueError):
        cb.limited_authorization({**doc, "anchors": list(reversed(doc["anchors"]))}, f)
    assert cb.anchors.CAL_B_AUTHORIZED is False


def test_primary_review_four_fields_and_partial_fail():
    assert cb.status_value(False, None) == cb.FAIL
    assert cb.status_value(True, None) == cb.AWAITING
    rows = {a: dict.fromkeys(cb.FIELDS, "PASS") for a in cb.anchors.CAL_B4_ANCHORS}
    assert cb.status_value(True, {"anchors": rows}) == cb.PASS
    rows[cb.anchors.CAL_B4_ANCHORS[0]][cb.FIELDS[0]] = None
    assert cb.status_value(True, {"anchors": rows}) == cb.AWAITING
    rows[cb.anchors.CAL_B4_ANCHORS[1]][cb.FIELDS[1]] = "FAIL"
    assert cb.status_value(True, {"anchors": rows}) == cb.FAIL


def test_degeneracy_literal_boundary():
    assert cb.cal_b.hold_rates(["TECH_EXPLICIT_HOLD"] * 8 + ["ACTION_BUY"] * 2)["total_hold_rate"] == 0.8
    assert cb.cal_b.hold_rates(["TECH_EXPLICIT_HOLD"] * 9 + ["ACTION_BUY"])["degenerate_inactive"]


def test_path_guard_rejects_outside_workspace():
    with pytest.raises(ValueError):
        cb.inside(cb.ROOT.parent, cb.OUT)


def test_raw_persistence_invalid_schema_and_exact_recovery(tmp_path, monkeypatch):
    journal = cb.RawJournal()
    anchor = "2000-01-03"  # Synthetic session, outside every reserved holdout.
    journal.open(tmp_path / "journal.jsonl", anchor)
    monkeypatch.setattr(cb.base, "JOURNAL", journal)
    monkeypatch.setattr(cb.base, "AUTH", cb.anchors.CalBAuthorization("CAL-B4", "synthetic", (anchor,), 1))
    requests = []
    output = dict(RESPONSE)
    def transport(method, url, headers, body):
        requests.append(body)
        return json.dumps({"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(output)}]}}],
            "modelVersion": "gemini-3.8-flash", "responseId": "synthetic"}).encode()
    monkeypatch.setattr(cb.base, "ATTEMPTS", transport)
    client = cb.CalB4GeminiClient(model="gemini-3.8-flash", api_key="synthetic-no-network")
    client.begin_session(anchor)
    options = {"temperature": 1.0, "max_output_tokens": 8192, "thinking_level": "low"}
    def call(analyst=1):
        return asyncio.run(client.generate(cb.system_prompt_for({"features": FEATURES}, 5),
            evidence_user_prompt(FEATURES), TechnicalEvidenceResponse, options,
            metadata=LLMCallMetadata(stage="technical_analyst", analyst_id=str(analyst))))
    assert call().model_dump() == RESPONSE
    assert len(requests) == 1 and journal.raw_path.stat().st_size > 0
    envelope = json.loads(journal.raw_path.read_text())
    assert "synthetic-no-network" not in json.dumps(envelope)
    # A second valid scientific response is durably saved even if strict schema
    # parsing rejects it; recovery cannot obtain a replacement response.
    output["extra"] = "forbidden"
    with pytest.raises(ValueError):
        call(2)
    assert len(journal.raw_path.read_text().splitlines()) == 2
    journal.open(tmp_path / "journal.jsonl", anchor)
    assert call().model_dump() == RESPONSE
    with pytest.raises(ValueError):
        call(2)
    with pytest.raises(ValueError, match="fresh inference refused"):
        call(3)
    assert len(requests) == 2


def test_transient_error_does_not_consume_identity(tmp_path, monkeypatch):
    journal = cb.RawJournal()
    journal.open(tmp_path / "journal.jsonl", "2000-01-03")
    request = SimpleNamespace(identity_digest="synthetic", requested_model="gemini-3.8-flash")
    token = cb.PENDING_REQUEST.set(request)
    calls = []
    def transient(*args):
        calls.append(1)
        if len(calls) == 1:
            raise ProviderTransportError("synthetic transient", status=503)
        return b'{"candidates": []}'
    monkeypatch.setattr(cb.base, "ATTEMPTS", transient)
    try:
        args = ("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", {}, {})
        with pytest.raises(ProviderTransportError):
            journal.transport(*args)
        assert not journal.raw_path.exists()
        assert json.loads(journal.transport(*args)) == {"candidates": []}
        assert len(calls) == 2
    finally:
        cb.PENDING_REQUEST.reset(token)


def test_success_without_raw_envelope_blocks_new_inference(tmp_path, monkeypatch):
    (tmp_path / "provider_attempts.jsonl").write_text('{"outcome":"http_200"}\n', encoding="utf-8")
    journal = cb.RawJournal()
    journal.open(tmp_path / "journal.jsonl", "2000-01-03")
    monkeypatch.setattr(cb.base, "ATTEMPTS", lambda *args: pytest.fail("network must be unreachable"))
    token = cb.PENDING_REQUEST.set(SimpleNamespace(identity_digest="missing", requested_model="gemini-3.8-flash"))
    try:
        with pytest.raises(ValueError, match="fresh inference refused"):
            journal.transport("POST", "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent", {}, {})
    finally:
        cb.PENDING_REQUEST.reset(token)


def test_loader_parses_only_calendar_prefix_without_t_plus_one(tmp_path, monkeypatch):
    calendar = tmp_path / "docs/evidence/calendar/b3_official_sessions_2016-01-04_2026-08-31.txt"
    calendar.parent.mkdir(parents=True)
    calendar.write_text("2016-01-04\n2016-01-05\n2016-01-06\n", encoding="utf-8")
    csv = tmp_path / "synthetic.csv"
    csv.write_text("date,fechamento\n2016-01-04,1\n2016-01-05,2\n2016-01-06,999999\n", encoding="utf-8")
    snapshot = SimpleNamespace(path=tmp_path, files=[{"ticker": cb.base.STRESS_TICKER, "path": csv.name}],
        scientific_ready=True, identity_digest=cb.base.H_REAL_SNAPSHOT_IDENTITY_DIGEST)
    monkeypatch.setattr(cb, "ROOT", tmp_path)
    monkeypatch.setattr(cb.base, "ANCHORS", ("2016-01-05",))
    monkeypatch.setattr(cb.base, "load_dataset_snapshot", lambda path: snapshot)
    monkeypatch.setattr(cb.base, "verify_snapshot_integrity", lambda snapshot: None)
    _, frame = cb.load_causal_frame()
    assert len(frame) == 2 and frame["fechamento"].tolist() == [1, 2]


def test_audit_adapter_on_existing_development_records(tmp_path, monkeypatch):
    # Exercise the real structured/legacy audit bridge without recalculating any
    # CAL-B4 feature. This input is already-public v6 Stress development evidence.
    run = next((cb.ROOT / "docs/evidence/stress_v6/run_20261008T025207Z/runs").iterdir())
    decisions = [json.loads(s) for s in (run / "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    decision = next(d for d in decisions if d["risk_source"] == "LLM")
    anchor = decision["decision_session"]
    assert anchor not in cb.anchors.CAL_B4_ANCHORS
    records = [r for r in cb.load_trace((run / "llm_calls.jsonl").read_bytes()) if r.request.decision_session == anchor]
    feature_payload = json.loads(next(r.request.user_prompt for r in records if r.request.stage == "technical_analyst"))
    volatility = json.loads(next(r.request.user_prompt for r in records if r.request.stage == "risk_manager"))["risk_metrics"]["recent_volatility"]
    f = cb.read(cb.FREEZE)
    f["anchors"] = [anchor]
    batch = {"freeze": "CAL_B4_PROTOCOL_FREEZE_V1", "git_commit": "synthetic-test"}
    adir = tmp_path / "anchors" / anchor
    adir.mkdir(parents=True)
    cb.write(adir / "anchor.json", {"history_last_session": anchor})
    (adir / "decisions.jsonl").write_text(json.dumps(decision) + "\n", encoding="utf-8")
    (adir / "llm_calls.jsonl").write_text("".join(json.dumps(r.to_json_dict()) + "\n" for r in records), encoding="utf-8")
    (adir / "provider_attempts.jsonl").write_text("".join('{"outcome":"http_200"}\n' for r in records), encoding="utf-8")
    monkeypatch.setattr(cb, "verified_batch", lambda target: (f, batch))
    def configure(freeze):
        monkeypatch.setattr(cb.base, "ANCHORS", (anchor,))
        monkeypatch.setattr(cb.base, "PARAMS", freeze["participant_spec"]["params"])
    monkeypatch.setattr(cb, "configure", configure)
    frame = cb.base.pd.DataFrame({"fechamento": [1.0]}, index=cb.base.pd.to_datetime([anchor]))
    monkeypatch.setattr(cb.base, "load_frame", lambda: (None, frame))
    monkeypatch.setattr(cb.base.LLMParticipant, "_agent_state", lambda *args: {"features": feature_payload["features"], "recent_volatility": volatility})
    cb.audit(tmp_path)
    report = cb.read(tmp_path / "automatic_gates.json")
    assert report["gates"]["CB4-A"]["pass"] is False  # Only one development anchor, never a CAL-B4 pass.
    assert all(g["pass"] for k, g in report["gates"].items() if k != "CB4-A")
    assert report["financial_outcome"] == "NOT COMPUTED"
    assert all(v is None for v in cb.read(tmp_path / "review/PRIMARY_AUTHOR.json")["anchors"][anchor].values())
    assert (tmp_path / "AUDIT_SEAL.json").exists()
