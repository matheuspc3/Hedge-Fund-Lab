"""Structured fact truth, fail-closed graph boundary and exact trace replay."""

import asyncio
import itertools
import json
from pathlib import Path
from typing import get_args

import pytest

from src.agents.feature_semantics import (audit_rationale, FEATURE_SEMANTICS, contradictions, transitions,
                                         UNSUPPORTED_TEMPORAL_STATE_CLAIM)
from src.agents.features import canonical_prompt_json
from src.agents.graph import build_graph
from src.agents.llm_client import MockLLMClient, GeminiLLMClient, RetryingLLMClient, LLMCallMetadata
from src.agents.llm_trace import RecordingLLMClient, ReplayLLMClient, load_trace, dump_trace, schema_digest
from src.agents.participant import FailureRecordingClient, LLMParticipant
from src.agents.risk_manager import RiskConfig
from src.agents.portfolio_manager import PortfolioConfig, SIZING_MODE_QUALITATIVE
from src.agents.state import TechnicalSignal, RiskVerdict, PortfolioAction
from src.agents.technical_analyst import AnalystEnsembleConfig, create_technical_analyst_ensemble_node, system_prompt_for
from src.agents.technical_evidence import (
    TechnicalEvidenceResponse, EvidenceRole, EVIDENCE_CODES, allowed_evidence_codes,
    canonical_features, evidence_user_prompt, validate_technical_evidence,
    render_technical_evidence, technical_evidence_ui,
)
from src.agents.technical_prompt_v5 import TECHNICAL_SYSTEM_PROMPT_V5
from src.experiments import treatment
from src.artifacts import canonical_json
from src.experiments.spec import ParticipantSpec

F = {"sma50_gap": .1, "sma200_gap": -.1, "bb_upper_gap": -.02, "bb_lower_gap": .03,
     "macd_ratio": .01, "macd_signal_ratio": .005, "rsi": 50.0, "bb_width": .08}


def response(features=F, role="NEUTRAL", signal="MANTER"):
    return {"signal": signal, "confidence": .72,
            "evidence": [{"code": c, "role": role} for c in allowed_evidence_codes(features)]}


@pytest.mark.parametrize("upper,lower,code", [(-.02,.03,"CLOSE_INSIDE_BOLLINGER"),
    (.01,.05,"CLOSE_ABOVE_BB_UPPER"),(-.05,-.01,"CLOSE_BELOW_BB_LOWER"),
    (0,.04,"CLOSE_AT_BB_UPPER"),(-.04,0,"CLOSE_AT_BB_LOWER")])
def test_allowed_truth(upper, lower, code):
    facts = allowed_evidence_codes({**F, "bb_upper_gap": upper, "bb_lower_gap": lower})
    assert facts == ["CLOSE_ABOVE_SMA50", "CLOSE_BELOW_SMA200", code, "MACD_POSITIVE",
                     "MACD_ABOVE_SIGNAL", "RSI_CURRENT", "BB_WIDTH_CURRENT"]


@pytest.mark.parametrize("changes", [{"bb_upper_gap": .1, "bb_lower_gap": -.1},
    {"bb_upper_gap": 0, "bb_lower_gap": 0}, {"rsi": 101}, {"bb_width": -1},
    {"macd_ratio": float('nan')}, {"sma50_gap": -1}, {"rsi": True}])
def test_inconsistent_input_rejected(changes):
    with pytest.raises(ValueError):
        allowed_evidence_codes({**F, **changes})


def test_canonical_zero_and_request_boundaries():
    assert "CLOSE_AT_SMA50" in allowed_evidence_codes({**F, "sma50_gap": .0000001})
    assert "CLOSE_AT_SMA50" in allowed_evidence_codes({**F, "sma50_gap": -.0000001})
    with pytest.raises(ValueError):
        allowed_evidence_codes({"rsi": 50})
    p = json.loads(evidence_user_prompt(F))
    assert set(p) == {"features", "allowed_evidence_codes"}
    assert p["features"] == canonical_features(F)


@pytest.mark.parametrize("patch", [{"justification": "texto"}, {"reasoning": "texto"},
    {"comment": "texto"}, {"confidence": True}, {"confidence": "0.7"}, {"confidence": 1.1},
    {"signal": "BUY"}, {"evidence": []},
    {"evidence": [{"code": "RECOVERY", "role": "NEUTRAL"}]},
    {"evidence": [{"code": "RSI_CURRENT", "role": "BUY"}]},
    {"evidence": [{"code": "RSI_CURRENT", "role": "NEUTRAL", "comment": "x"}]}])
def test_strict_schema(patch):
    with pytest.raises(ValueError):
        TechnicalEvidenceResponse.model_validate({**response(), **patch})


def test_subset_uniqueness_and_incompatible_code():
    subset = {**response(), "evidence": [{"code": "RSI_CURRENT", "role": "SUPPORTS_VENDA"}]}
    assert validate_technical_evidence(subset, F, allowed_evidence_codes(F)).signal == "MANTER"
    for items in ([subset["evidence"][0]] * 2, [{"code": "CLOSE_BELOW_SMA50", "role": "NEUTRAL"}]):
        with pytest.raises(ValueError, match="INVALID_RESPONSE"):
            validate_technical_evidence({**subset, "evidence": items}, F, allowed_evidence_codes(F))
    with pytest.raises(ValueError):
        validate_technical_evidence(subset, F, ["RSI_CURRENT"])


def test_all_renderer_codes_and_roles_against_frozen_checker():
    seen = set()
    bands = ((-.02,.03),(.01,.05),(-.05,-.01),(0,.04),(-.04,0))
    for sma50,sma200,band,macd,relation,role in itertools.product(
            (-.1,0,.1),(-.1,0,.1),bands,(-.01,0,.01),(-.005,0,.005),get_args(EvidenceRole)):
        f = {**F, "sma50_gap": sma50,"sma200_gap": sma200,"bb_upper_gap": band[0],
             "bb_lower_gap": band[1],"macd_ratio": macd,"macd_signal_ratio": macd-relation}
        codes = allowed_evidence_codes(f); seen.update(codes)
        text = render_technical_evidence(response(f, role), f, codes)
        findings = audit_rationale(text, f)
        assert not contradictions(findings) and not transitions(findings), text
        assert not any(row["claim"] == UNSUPPORTED_TEMPORAL_STATE_CLAIM for row in findings), text
    assert seen == set(EVIDENCE_CODES)


def state():
    return {"features": F, "current_price": 100., "equity": 100000., "cash": 100000.,
            "position": 0., "current_drawdown": 0., "recent_volatility": .1, "errors": []}


def test_invalid_evidence_records_failure_before_consensus():
    invalid = {**response(), "evidence": [{"code": "CLOSE_BELOW_SMA50", "role": "NEUTRAL"}]}
    mock = MockLLMClient({TechnicalEvidenceResponse: invalid})
    failures = FailureRecordingClient(RetryingLLMClient(mock, max_attempts=3, base_delay=0))
    recording = RecordingLLMClient(failures, provider="mock", requested_model="offline")
    recording.begin_session("2020-05-13")
    node = create_technical_analyst_ensemble_node(recording, AnalystEnsembleConfig(analyst_count=1, prompt_version=5))
    result = asyncio.run(node(state()))
    assert result["technical_consensus"].valid_votes == 0 and result["errors"]
    assert len(mock.calls) == 1 and len(failures.failures) == 1
    assert recording.records[0].status == "error"
    from scripts.h2_v6 import technical_audit
    assert technical_audit(recording.records)["V6-E"] == 1


def test_participant_invalid_response_is_not_a_hold_or_trade():
    from src.agents.participant import LLMDecisionError, INVALID_RESPONSE
    from src.experiments.hardening import synthetic_states, frozen_observation
    snapshot = synthetic_states()[0]
    invalid = {"signal":"MANTER","confidence":.7,"evidence":[{"code":"RSI_CURRENT","role":"NEUTRAL"}],
               "justification":"invented narrative"}
    participant = LLMParticipant(snapshot.ticker, llm_client=MockLLMClient({TechnicalEvidenceResponse:invalid}),
        **{k:v for k,v in treatment.H2_V6_HARDENING_PARAMS.items() if k != "ticker"})
    with pytest.raises(LLMDecisionError) as error:
        participant.decide(frozen_observation(snapshot,100000.))
    assert error.value.reason == INVALID_RESPONSE
    assert participant.decisions[-1].target_weight is None
    assert participant.decisions[-1].final_cause == INVALID_RESPONSE
    assert all(r.status == "error" and r.error_type == "ValueError" for r in participant.trace.records)
    assert not any(r.request.stage == "risk_manager" for r in participant.trace.records)


def test_graph_risk_contract_trace_and_replay():
    answers = {TechnicalEvidenceResponse: response(signal="COMPRA"),
               RiskVerdict: {"verdict": "APROVADO", "analysis": "Métricas fornecidas adequadas"},
               PortfolioAction: {"decision": "COMPRA", "reasoning": "Sinal aprovado"}}
    mock = MockLLMClient(answers)
    recorder = RecordingLLMClient(FailureRecordingClient(mock), provider="mock", requested_model="offline")
    def graph(client):
        return build_graph(client, ensemble_config=AnalystEnsembleConfig(analyst_count=5,prompt_version=5,
            consensus_threshold=.6, temperature_min=1,temperature_max=1), risk_config=RiskConfig(prompt_version=2),
            portfolio_config=PortfolioConfig(sizing_mode=SIZING_MODE_QUALITATIVE))
    recorder.begin_session("2020-05-13")
    output = asyncio.run(graph(recorder).ainvoke(state()))
    assert output["technical_signal"].justification == "Consenso coletivo: 5/5 votos em COMPRA"
    risk = json.loads(mock.calls[5].user_prompt)
    assert risk["technical_signal"] == output["technical_signal"].model_dump()
    assert "evidence" not in canonical_prompt_json(risk) and "classificado" not in canonical_prompt_json(risk)
    records = load_trace(dump_trace(recorder.records))
    trace = records[0].to_json_dict()
    assert set(trace["validated_response"]) == {"signal","confidence","evidence"}
    assert trace["technical_evidence"]["ui"]["display_explanation"]
    replay = ReplayLLMClient(records, provider="mock",requested_model="offline")
    replay.begin_session("2020-05-13")
    again = asyncio.run(graph(FailureRecordingClient(replay)).ainvoke(state()))
    replay.assert_complete()
    assert output == again
    from scripts.h2_v6 import technical_audit
    audit = technical_audit(records)
    assert audit["technical_votes"] == 5
    assert all(audit[k] == 0 for k in ("V6-E","V6-S1","V6-S2","V6-S3"))


def test_versions_and_historical_schemas():
    v5,v6 = dict(treatment.H2_V5_DEFECT_PARAMS),dict(treatment.H2_V6_DEFECT_PARAMS)
    assert canonical_json(ParticipantSpec("llm_agent",v5).to_dict()) != canonical_json(ParticipantSpec("llm_agent",v6).to_dict())
    assert (v6["volatility_window"],v6["risk_max_volatility"],v6["risk_max_drawdown"],v6["risk_max_concentration"]) == (21,.4,.15,1)
    assert schema_digest(TechnicalSignal) != schema_digest(TechnicalEvidenceResponse)
    for version in range(1,5):
        assert "justification" in system_prompt_for({"features": F},version)
        LLMParticipant("PETR4.SA",llm_client=MockLLMClient(),technical_prompt_version=version)
    LLMParticipant(llm_client=MockLLMClient(), **v6)
    for key, definition in FEATURE_SEMANTICS.items():
        assert f"- {key} = {definition}" in TECHNICAL_SYSTEM_PROMPT_V5
    assert set(TechnicalEvidenceResponse.model_json_schema()["properties"]) == {"signal","confidence","evidence"}
    assert TechnicalEvidenceResponse.model_json_schema()["additionalProperties"] is False


@pytest.mark.parametrize("root", ("h2","h2_v2","h2_v3","h2_v4","h2_v5"))
def test_historical_actual_technical_requests_replay_unchanged(root):
    base = Path(__file__).resolve().parents[2] / "docs/evidence" / root
    path = sorted(base.glob("*/traces/*.jsonl"))[0]
    records = [r for r in load_trace(path.read_bytes()) if r.request.stage == "technical_analyst" and r.status == "ok"]
    record = records[0]
    assert record.request.response_schema_sha256 == schema_digest(TechnicalSignal)
    req = record.request
    replay = ReplayLLMClient([record],provider=req.provider,requested_model=req.requested_model)
    replay.begin_session(req.decision_session)
    result = asyncio.run(replay.generate(req.system_prompt,req.user_prompt,TechnicalSignal,
        dict(req.requested_options),metadata=LLMCallMetadata(stage=req.stage,analyst_id=req.analyst_id)))
    replay.assert_complete()
    assert result.model_dump(mode="json") == record.validated_response


def test_current_fact_derivation_accepts_existing_development_corpus():
    from src.experiments.hardening import synthetic_states, scientific_payload
    for snapshot in synthetic_states():
        allowed_evidence_codes(json.loads(scientific_payload(snapshot))["features"])
    base = Path(__file__).resolve().parents[2] / "docs/evidence"
    paths = [*sorted((base / "h2_v5").glob("*/traces/*.jsonl")),
             *sorted((base / "cal_a_v5").glob("run_*/runs/*/llm_calls.jsonl")),
             *sorted((base / "sequential_dev_v5").glob("run_*/runs/*/llm_calls.jsonl"))]
    assert paths
    seen=set()
    for path in paths:
        for record in load_trace(path.read_bytes()):
            if record.request.stage != "technical_analyst":
                continue
            line=record.request.user_prompt.splitlines()[0].removeprefix("Features: ")
            if line in seen:
                continue
            seen.add(line)
            allowed_evidence_codes(json.loads(line))
    assert len(seen) >= 150


def test_gemini_native_schema_raw_preservation_and_replay_hashes():
    captured = []
    raw = canonical_json(response())
    def transport(method, url, headers, body):
        captured.append(body)
        return json.dumps({"candidates":[{"content":{"parts":[{"text":raw}]},"finishReason":"STOP"}],
                           "responseId":"offline-response","modelVersion":"offline"}).encode()
    client = GeminiLLMClient(api_key="offline-key",model="gemini-3.8-flash",transport=transport)
    rec = RecordingLLMClient(FailureRecordingClient(client),provider="gemini",requested_model="gemini-3.8-flash")
    rec.begin_session("2020-05-13")
    async def ask(c):
        return await c.generate(TECHNICAL_SYSTEM_PROMPT_V5,evidence_user_prompt(F),TechnicalEvidenceResponse,
                                {"temperature":1.,"thinking_level":"low","max_output_tokens":8192})
    asyncio.run(ask(rec))
    assert captured[0]["generationConfig"]["responseJsonSchema"] == TechnicalEvidenceResponse.model_json_schema()
    assert "offline-key" not in canonical_json(captured[0])
    record = rec.records[0]; assert record.raw_response == raw
    replay = ReplayLLMClient(load_trace(dump_trace(rec.records)),provider="gemini",requested_model="gemini-3.8-flash")
    rerec = RecordingLLMClient(FailureRecordingClient(replay),provider="gemini",requested_model="gemini-3.8-flash")
    rerec.begin_session("2020-05-13")
    asyncio.run(ask(rerec)); replay.assert_complete()
    assert record.to_json_dict()["technical_evidence"] == rerec.records[0].to_json_dict()["technical_evidence"]
