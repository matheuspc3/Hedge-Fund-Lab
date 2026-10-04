"""Cliente nativo da Gemini API e a evidência observada no trace.

Nenhum teste faz rede: o transporte é injetado ou ``urlopen`` é substituído.
"""

import asyncio
import io
import json
from http.client import IncompleteRead
from typing import Any, cast
from urllib import error

import pytest

from src.agents.llm_client import (
    GeminiLLMClient,
    LLMCallMetadata,
    ProviderRequestRejected,
    ProviderTransportError,
    RetryingLLMClient,
)
from src.agents.llm_trace import (
    LLM_TRACE_SCHEMA_VERSION,
    RecordingLLMClient,
    ReplayLLMClient,
    dump_trace,
    load_trace,
)
from src.agents.participant import (
    CAPABILITY_DECLARED_UNQUALIFIED,
    INVALID_RESPONSE,
    PROVIDER_FAILURE,
    PROVIDER_REQUEST_REJECTED,
    FailureRecordingClient,
    LLMParticipant,
    classify_decision,
)
from src.agents.state import TechnicalSignal

MODEL = "gemini-model-under-test"
ANSWER = '{"signal":"COMPRA","justification":"ok","confidence":0.6}'


def response(
    text: str = ANSWER,
    finish: str | None = "STOP",
    *,
    thought: str | None = None,
) -> dict[str, Any]:
    parts = ([{"text": thought, "thought": True}] if thought else []) + [{"text": text}]
    return {
        "candidates": [
            {"content": {"role": "model", "parts": parts}, "finishReason": finish}
        ],
        "usageMetadata": {
            "promptTokenCount": 11,
            "candidatesTokenCount": 7,
            "thoughtsTokenCount": 5,
            "totalTokenCount": 23,
        },
        "modelVersion": f"{MODEL}-001",
        "responseId": "resp-123",
    }


class Stub:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str, dict[str, str], dict[str, Any]]] = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        return json.dumps(self.payload).encode("utf-8")


def gemini(payload: dict[str, Any] | None = None) -> tuple[GeminiLLMClient, Stub]:
    stub = Stub(payload or response())
    return GeminiLLMClient(api_key="k", model=MODEL, transport=stub, timeout=1.0), stub


OPTIONS = {
    "temperature": 1.0,
    "thinking_level": "low",
    "max_output_tokens": 2048,
    "seed": 10_001,
    "analyst_id": 1,
}


def run(awaitable):
    return asyncio.run(awaitable)


def recorded(client: GeminiLLMClient, options: dict[str, Any] | None = OPTIONS):
    recorder = RecordingLLMClient(client, provider="gemini", requested_model=MODEL)
    recorder.begin_session("2024-01-02")
    try:
        run(
            recorder.generate(
                "system",
                "user",
                TechnicalSignal,
                options,
                metadata=LLMCallMetadata(stage="technical_analyst", analyst_id=1),
            )
        )
    except ValueError:
        pass
    return recorder.records[-1]


def test_payload_nativo_com_opcoes_qualificadas_e_sem_seed() -> None:
    client, stub = gemini()
    result = run(client.generate("system", "user", TechnicalSignal, OPTIONS))

    assert isinstance(result, TechnicalSignal) and result.signal == "COMPRA"
    method, url, headers, body = stub.calls[0]
    assert method == "POST"
    assert url.endswith(f"/models/{MODEL}:generateContent")
    assert headers["x-goog-api-key"] == "k" and "k" not in url
    assert body["systemInstruction"] == {"parts": [{"text": "system"}]}
    assert body["contents"] == [{"role": "user", "parts": [{"text": "user"}]}]
    config = body["generationConfig"]
    assert config["temperature"] == 1.0
    assert config["maxOutputTokens"] == 2048
    assert config["thinkingConfig"] == {"thinkingLevel": "LOW"}
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"] == TechnicalSignal.model_json_schema()
    assert "seed" not in json.dumps(body) and "analyst_id" not in json.dumps(body)


def test_transport_options_separa_metadado() -> None:
    client, _ = gemini()
    assert client.transport_options(OPTIONS) == {
        "temperature": 1.0,
        "thinking_level": "low",
        "max_output_tokens": 2048,
    }


def test_evidencia_observada_vai_para_o_trace_fora_da_identidade() -> None:
    client, _ = gemini()
    record = recorded(client)

    assert (record.provider_response_id, record.resolved_model, record.finish_reason) == (
        "resp-123",
        f"{MODEL}-001",
        "STOP",
    )
    assert record.token_usage is not None and record.token_usage["thoughts_tokens"] == 5
    # Prompt lógico == prompt de transporte: o schema viaja em generationConfig.
    assert record.transport_system_prompt_sha256 == record.request.system_prompt_sha256
    identity = record.request.identity()
    assert not {"provider_response_id", "resolved_model", "finish_reason"} & set(identity)
    assert record.to_json_dict()["resolved_model"] == f"{MODEL}-001"


def test_replay_ignora_evidencia_observada() -> None:
    client, _ = gemini()
    payload = recorded(client).to_json_dict()
    payload.update(
        resolved_model="outro-modelo", finish_reason="OTHER", provider_response_id="x"
    )
    replay = ReplayLLMClient(
        load_trace(json.dumps(payload)), provider="gemini", requested_model=MODEL
    )
    replay.begin_session("2024-01-02")

    result = run(
        replay.generate(
            "system",
            "user",
            TechnicalSignal,
            OPTIONS,
            metadata=LLMCallMetadata(stage="technical_analyst", analyst_id=1),
        )
    )
    assert isinstance(result, TechnicalSignal) and result.signal == "COMPRA"


def test_trace_sem_campos_de_evidencia_continua_legivel() -> None:
    client, _ = gemini()
    payload = recorded(client).to_json_dict()
    for key in ("provider_response_id", "resolved_model", "finish_reason"):
        del payload[key]
    (loaded,) = load_trace(json.dumps(payload))
    assert payload["schema_version"] == LLM_TRACE_SCHEMA_VERSION
    assert (loaded.provider_response_id, loaded.resolved_model, loaded.finish_reason) == (
        None,
        None,
        None,
    )
    assert dump_trace([loaded])


def test_saida_truncada_e_resposta_invalida_com_finish_reason_registrado() -> None:
    client, _ = gemini(response(text='{"signal":"COM', finish="MAX_TOKENS"))
    with pytest.raises(ValueError, match="MAX_TOKENS"):
        run(client.generate("system", "user", TechnicalSignal, OPTIONS))
    record = recorded(gemini(response(text='{"signal":"COM', finish="MAX_TOKENS"))[0])
    assert record.status == "error" and record.finish_reason == "MAX_TOKENS"


def test_partes_de_raciocinio_nao_sao_resposta() -> None:
    client, _ = gemini(response(thought="pensando em voz alta"))
    result = run(client.generate("s", "u", TechnicalSignal))
    assert isinstance(result, TechnicalSignal) and result.signal == "COMPRA"


def test_resposta_bloqueada_sem_candidato() -> None:
    client, _ = gemini({"promptFeedback": {"blockReason": "SAFETY"}})
    with pytest.raises(ValueError, match="SAFETY"):
        run(client.generate("s", "u", TechnicalSignal))


def test_nivel_de_thinking_nao_declarado_e_recusado_localmente() -> None:
    client, stub = gemini()
    with pytest.raises(ProviderRequestRejected, match="not declared"):
        run(client.generate("s", "u", TechnicalSignal, {"thinking_level": "minimal"}))
    assert stub.calls == []


def test_sem_credencial_falha_antes_da_rede_e_sem_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    stub = Stub(response())
    retrying = RetryingLLMClient(
        GeminiLLMClient(model=MODEL, transport=stub), max_attempts=3, base_delay=0
    )
    with pytest.raises(ProviderRequestRejected, match="GEMINI_API_KEY") as raised:
        run(retrying.generate("s", "u"))
    assert stub.calls == []
    assert cause_of(raised.value) == PROVIDER_REQUEST_REJECTED
    with pytest.raises(ValueError, match="explicit model"):
        GeminiLLMClient(api_key="k", model=" ")


def test_model_ja_prefixado_nao_duplica_models() -> None:
    client = GeminiLLMClient(api_key="k", model=f"models/{MODEL}", transport=Stub(response()))
    assert client.provider_endpoint() == (
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    )


# ── Taxonomia HTTP / retry ───────────────────────────────────────


def http_failure(code: int, body: str = "", headers: dict[str, str] | None = None):
    """``urlopen`` falso que conta tentativas e devolve sempre o mesmo erro."""
    calls = {"n": 0}

    def urlopen(req, timeout):
        calls["n"] += 1
        raise error.HTTPError(
            req.full_url, code, "x", cast(Any, headers or {}), io.BytesIO(body.encode())
        )

    return urlopen, calls


def retrying_gemini() -> RetryingLLMClient:
    return RetryingLLMClient(
        GeminiLLMClient(api_key="k", model=MODEL, timeout=1.0), max_attempts=3, base_delay=0
    )


def cause_of(exc: BaseException) -> str:
    return classify_decision(
        consensus=None,
        risk_verdict=None,
        risk_source=None,
        risk_rule=None,
        portfolio_action=None,
        portfolio_rule=None,
        observed_weight=0.0,
        long_target_weight=1.0,
        failures=(exc,),
    )


@pytest.mark.parametrize(
    ("status", "kind", "attempts", "cause"),
    [
        (400, ProviderRequestRejected, 1, PROVIDER_REQUEST_REJECTED),
        (401, ProviderRequestRejected, 1, PROVIDER_REQUEST_REJECTED),
        (402, ProviderRequestRejected, 1, PROVIDER_REQUEST_REJECTED),
        (403, ProviderRequestRejected, 1, PROVIDER_REQUEST_REJECTED),
        (404, ProviderRequestRejected, 1, PROVIDER_REQUEST_REJECTED),
        (409, ProviderTransportError, 3, PROVIDER_FAILURE),
        (429, ProviderTransportError, 3, PROVIDER_FAILURE),
        (500, ProviderTransportError, 3, PROVIDER_FAILURE),
        (503, ProviderTransportError, 3, PROVIDER_FAILURE),
        (504, ProviderTransportError, 3, PROVIDER_FAILURE),
    ],
)
def test_status_http_decide_retry_e_causa(
    monkeypatch: pytest.MonkeyPatch, status: int, kind: type, attempts: int, cause: str
) -> None:
    urlopen, calls = http_failure(status)
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with pytest.raises(kind, match=f"HTTP {status}") as raised:
        run(retrying_gemini().generate("s", "u", TechnicalSignal))
    assert calls["n"] == attempts
    assert cause_of(raised.value) == cause


RETRY_INFO_BODY = json.dumps(
    {
        "error": {
            "code": 429,
            "details": [
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "7s"}
            ],
        }
    }
)


@pytest.mark.parametrize(
    ("headers", "body", "expected"),
    [
        ({"Retry-After": "3"}, "", 3.0),
        ({}, RETRY_INFO_BODY, 7.0),
        ({}, "", 0.0),
    ],
    ids=["retry-after", "retry-info", "sem-atraso-usa-backoff"],
)
def test_429_respeita_o_atraso_pedido(
    monkeypatch: pytest.MonkeyPatch, headers: dict[str, str], body: str, expected: float
) -> None:
    urlopen, _ = http_failure(429, body, headers)
    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    delays: list[float] = []

    async def sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr("src.agents.llm_client.asyncio.sleep", sleep)
    with pytest.raises(ProviderTransportError):
        run(retrying_gemini().generate("s", "u", TechnicalSignal))
    # ``base_delay=0``: sem atraso pedido, o backoff é zero.
    assert delays == [expected, expected]


class Truncated:
    """Resposta HTTP cujo corpo termina antes do fim declarado."""

    def __enter__(self):
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def read(self) -> bytes:
        raise IncompleteRead(b'{"candidates": [')


@pytest.mark.parametrize(
    "failure",
    [
        error.URLError("Connection refused"),
        TimeoutError("timed out"),
        ConnectionResetError("reset by peer"),
        "truncated",
    ],
    ids=["url-error", "timeout", "connection-reset", "incomplete-read"],
)
def test_falha_de_transporte_e_repetida_e_vira_provider_failure(
    monkeypatch: pytest.MonkeyPatch, failure: Any
) -> None:
    calls = {"n": 0}

    def urlopen(req, timeout):
        calls["n"] += 1
        if failure == "truncated":
            return Truncated()
        raise failure

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    with pytest.raises(OSError) as raised:
        run(retrying_gemini().generate("s", "u", TechnicalSignal))
    assert calls["n"] == 3
    assert cause_of(raised.value) == PROVIDER_FAILURE


@pytest.mark.parametrize(
    "raw", [b"<html>proxy</html>", b"\xff\xfe", b"[]"], ids=["html", "bytes", "lista"]
)
def test_corpo_http_corrompido_e_transporte_nao_resposta_invalida(raw: bytes) -> None:
    attempts = {"n": 0}

    def transport(method, url, headers, body):
        attempts["n"] += 1
        return raw

    client = RetryingLLMClient(
        GeminiLLMClient(api_key="k", model=MODEL, transport=transport),
        max_attempts=3,
        base_delay=0,
    )
    with pytest.raises(ProviderTransportError) as raised:
        run(client.generate("s", "u", TechnicalSignal))
    assert attempts["n"] == 3
    assert cause_of(raised.value) == PROVIDER_FAILURE


def test_json_do_modelo_fora_do_schema_continua_invalid_response() -> None:
    stub = Stub(response(text='{"signal":"TALVEZ","justification":"x","confidence":0.5}'))
    client = RetryingLLMClient(
        GeminiLLMClient(api_key="k", model=MODEL, transport=stub), max_attempts=3, base_delay=0
    )
    with pytest.raises(ValueError) as raised:
        run(client.generate("s", "u", TechnicalSignal))
    assert len(stub.calls) == 1  # resposta inválida não é repetida
    assert cause_of(raised.value) == INVALID_RESPONSE


# ── Parsing defensivo ────────────────────────────────────────────


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {"candidates": [response()["candidates"][0], response()["candidates"][0]]},
            "esperado 1 candidato",
        ),
        ({"candidates": [{"content": {"parts": [{"text": ANSWER}]}}]}, "finishReason"),
        ({"candidates": [{"finishReason": "STOP"}]}, "content.parts"),
        ({"candidates": ["texto"]}, "não é um objeto"),
        ({"candidates": [], "promptFeedback": {"blockReason": "SAFETY"}}, "SAFETY"),
    ],
    ids=[
        "dois-candidatos",
        "sem-finish-reason",
        "sem-parts",
        "candidato-invalido",
        "bloqueado",
    ],
)
def test_ausencia_estrutural_nunca_e_aceita(payload: dict[str, Any], message: str) -> None:
    client, _ = gemini(payload)
    with pytest.raises(ValueError, match=message) as raised:
        run(client.generate("s", "u", TechnicalSignal))
    assert cause_of(raised.value) == INVALID_RESPONSE


def test_participante_constroi_o_cliente_nativo_sem_rede() -> None:
    participant = LLMParticipant(
        "SYN", provider="gemini", model=MODEL, temperature=1.0, thinking_level="medium"
    )
    stack = participant.client
    assert isinstance(stack, FailureRecordingClient)
    assert isinstance(stack.client, RetryingLLMClient)
    assert isinstance(stack.client.client, GeminiLLMClient)
    # Declarado pelo código, nunca qualificado sem LIVE_SMOKE.
    capabilities = participant.capabilities
    assert capabilities.declared == ("temperature", "thinking_level")
    assert capabilities.qualified == ()
    assert capabilities.status == CAPABILITY_DECLARED_UNQUALIFIED


# ── Replay preserva a evidência observada ────────────────────────


def test_replay_reemite_a_evidencia_observada_gravada() -> None:
    original = recorded(gemini()[0])
    replay = ReplayLLMClient(
        load_trace(json.dumps(original.to_json_dict())),
        provider="gemini",
        requested_model=MODEL,
    )
    rerecorded = recorded(cast(Any, replay))
    assert rerecorded.status == "ok"
    assert (
        rerecorded.provider_response_id,
        rerecorded.resolved_model,
        rerecorded.finish_reason,
    ) == ("resp-123", f"{MODEL}-001", "STOP")
