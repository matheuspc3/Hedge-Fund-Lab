"""Provas da evidência por chamada de LLM: gravação, concorrência e replay.

O que se prova aqui é proveniência, não estratégia. A correção econômica do
participante continua em ``tests/agents/test_llm_participant.py``; a integração
com o run científico, em ``tests/experiments/test_llm_runner.py``.
"""

import asyncio
import json
from typing import Any, cast

import pandas as pd
import pytest
from pydantic import BaseModel, ConfigDict, Field

from src.agents.llm_client import (
    AgentRouterLLMClient,
    LLMCallMetadata,
    LLMClient,
    MockLLMClient,
    RetryingLLMClient,
    current_call_telemetry,
)
from src.agents.llm_trace import (
    LLM_TRACE_SCHEMA_VERSION,
    STAGE_PORTFOLIO_MANAGER,
    STAGE_RISK_MANAGER,
    STAGE_TECHNICAL_ANALYST,
    LLMCallRecord,
    LLMCallRequest,
    RecordingLLMClient,
    ReplayLLMClient,
    ReplayMismatchError,
    dump_trace,
    load_trace,
    schema_digest,
    schema_name,
    sha256_text,
)
from src.agents.participant import LLMParticipant
from src.agents.state import FinalDecision, RiskVerdict, TechnicalSignal
from src.artifacts import canonical_json
from src.backtesting.arena import ExecutionEngine, MarketObservation
from src.backtesting.costs import CostModel

TICKER = "PETR4"
CAPITAL = 100_000.0
SESSION = pd.Timestamp("2023-03-15")

#: Quorum pequeno e limites abertos de propósito: estes testes exercitam
#: proveniência, não calibram o quorum — que continua não congelado.
PARAMS: dict[str, Any] = {
    "analyst_count": 3,
    "consensus_threshold": 1.0,
    "risk_max_volatility": 100.0,
    "risk_max_drawdown": 1.0,
    "risk_max_concentration": 1.0,
    "decision_frequency": 2,
}


def price_frame(sessions: int) -> pd.DataFrame:
    closes = [10.0 + (index % 4) * 0.5 + index * 0.05 for index in range(sessions)]
    return pd.DataFrame(
        {"abertura": [close * 0.99 for close in closes], "fechamento": closes},
        index=pd.bdate_range("2023-01-02", periods=sessions),
    )


#: Custos idênticos nos dois lados do experimento. Um replay que executasse com
#: outro modelo de custo teria outro caixa, outros prompts e divergiria — o que
#: o próprio ``ReplayLLMClient`` detecta, mas que não é o que estes testes
#: querem exercitar.
COSTS = CostModel(brokerage_fixed=1.0)


def run_live(data: pd.DataFrame) -> tuple[LLMParticipant, Any]:
    """Run gravado com provedor mock determinístico."""
    participant = LLMParticipant(TICKER, provider="mock", **PARAMS)
    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL, COSTS).run()
    return participant, result


def replay_participant(trace: bytes, **overrides: Any) -> tuple[LLMParticipant, Any]:
    params = {**PARAMS, **overrides}
    client = ReplayLLMClient.from_trace(trace, provider="mock", requested_model="")
    participant = LLMParticipant(TICKER, provider="mock", llm_client=client, **params)
    return participant, client


def run_replay(data: pd.DataFrame, trace: bytes) -> tuple[LLMParticipant, Any, Any]:
    """Reexecuta a mesma arena trocando apenas a origem das respostas."""
    participant, client = replay_participant(trace)
    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL, COSTS).run()
    return participant, client, result


def recorder(client: LLMClient, **overrides: Any) -> RecordingLLMClient:
    settings: dict[str, Any] = {"provider": "mock", "requested_model": "m/1"}
    settings.update(overrides)
    recording = RecordingLLMClient(client, **settings)
    recording.begin_session(SESSION)
    return recording


# ── Conteúdo de um registro de chamada ───────────────────────────


def test_registro_descreve_a_chamada_inteira() -> None:
    client = MockLLMClient(
        {TechnicalSignal: {"signal": "COMPRA", "justification": "j", "confidence": 0.5}}
    )
    recording = recorder(client)

    response = asyncio.run(
        recording.generate(
            "system text",
            "user text",
            TechnicalSignal,
            {"temperature": 0.4, "seed": 7, "analyst_id": 2},
            metadata=LLMCallMetadata(stage=STAGE_TECHNICAL_ANALYST, analyst_id=2),
        )
    )

    assert isinstance(response, TechnicalSignal)
    (record,) = recording.records
    assert record.sequence == 0
    assert record.call_id == "2023-03-15|technical_analyst|2|000000"
    assert record.request.stage == STAGE_TECHNICAL_ANALYST
    assert record.request.analyst_id == 2
    assert record.request.decision_session == "2023-03-15"
    assert record.request.provider == "mock"
    assert record.request.requested_model == "m/1"
    assert record.request.response_schema == "TechnicalSignal"
    # Prompt inteiro *e* hash: o hash prova o texto, o texto reconstrói a
    # chamada. Um não substitui o outro.
    assert record.request.system_prompt == "system text"
    assert record.request.user_prompt == "user text"
    assert record.request.system_prompt_sha256 == sha256_text("system text")
    assert record.request.user_prompt_sha256 == sha256_text("user text")
    assert dict(record.request.requested_options) == {
        "temperature": 0.4,
        "seed": 7,
        "analyst_id": 2,
    }
    assert record.status == "ok"
    assert record.attempt_count == 1 and record.retry_count == 0
    # Resposta validada em forma estável, nunca ``repr`` do objeto.
    assert record.validated_response == {
        "signal": "COMPRA",
        "justification": "j",
        "confidence": 0.5,
    }
    assert record.duration_ms >= 0.0
    assert record.started_at.endswith("Z")


def test_hash_de_prompt_nao_normaliza_espaco_em_branco() -> None:
    """Espaço em branco efetivamente enviado faz parte do prompt."""
    assert sha256_text("a b") != sha256_text("a  b")
    assert sha256_text("a\n") != sha256_text("a")


def test_hash_combinado_distingue_texto_movido_entre_os_prompts() -> None:
    def request(system: str, user: str) -> LLMCallRequest:
        return LLMCallRequest(
            stage=STAGE_RISK_MANAGER,
            analyst_id=None,
            decision_session="2023-03-15",
            provider="mock",
            requested_model="m/1",
            system_prompt=system,
            user_prompt=user,
            response_schema=None,
            response_schema_sha256=None,
            requested_options={},
        )

    assert (
        request("ab", "c").combined_prompt_sha256
        != request("a", "bc").combined_prompt_sha256
    )


def test_sessao_de_decisao_precisa_ser_declarada() -> None:
    """Sem contexto aberto a gravação recusa; nada é deduzido da ordem."""
    recording = RecordingLLMClient(MockLLMClient(), provider="mock", requested_model="")

    with pytest.raises(Exception, match="no decision session is open"):
        asyncio.run(recording.generate("s", "u"))


def test_falha_definitiva_vira_registro_de_erro() -> None:
    class Broken(LLMClient):
        async def generate(self, *args: Any, **kwargs: Any) -> Any:
            raise TimeoutError("provider timeout")

    recording = recorder(RetryingLLMClient(Broken(), max_attempts=3, base_delay=0))

    with pytest.raises(TimeoutError):
        asyncio.run(
            recording.generate(
                "s", "u", metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER)
            )
        )

    (record,) = recording.records
    assert record.status == "error"
    assert record.error_type == "TimeoutError"
    assert record.error_message == "provider timeout"
    # Uma chamada lógica, três tentativas HTTP: o trace distingue as duas.
    assert record.attempt_count == 3 and record.retry_count == 2
    assert record.validated_response is None
    # Mensagem apenas; nenhum stack trace entra no artefato.
    assert "Traceback" not in json.dumps(record.to_json_dict())


def test_tentativa_recuperada_pelo_retry_nao_e_falha() -> None:
    class Flaky(LLMClient):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        async def generate(self, *args: Any, **kwargs: Any) -> Any:
            self.calls += 1
            if self.calls < 3:
                raise ConnectionError("transitório")
            return "ok"

    recording = recorder(RetryingLLMClient(Flaky(), max_attempts=3, base_delay=0))
    assert asyncio.run(recording.generate("s", "u")) == "ok"

    (record,) = recording.records
    assert record.status == "ok"
    assert record.attempt_count == 3 and record.retry_count == 2


# ── Concorrência: provenance por chamada, sem estado global ──────


def test_analistas_concorrentes_nao_misturam_tentativas_nem_respostas() -> None:
    """Cada analista publica *suas* tentativas, seu id e sua resposta.

    O ensemble roda ``asyncio.gather``. Enquanto o contador de tentativas era
    atributo do cliente concreto, um analista lento podia publicar o número de
    tentativas de outro. Aqui cada analista falha um número diferente de vezes
    de propósito, e cada registro precisa ficar com o seu.
    """

    class PerAnalystFlaky(LLMClient):
        """Analista ``n`` falha ``n - 1`` vezes antes de responder."""

        def __init__(self) -> None:
            super().__init__()
            self.seen: dict[int, int] = {}

        async def generate(
            self,
            system_prompt: str,
            user_prompt: str,
            response_schema: type[BaseModel] | None = None,
            options: dict[str, Any] | None = None,
            *,
            metadata: LLMCallMetadata | None = None,
        ) -> Any:
            analyst = cast(LLMCallMetadata, metadata).analyst_id or 0
            self.seen[analyst] = self.seen.get(analyst, 0) + 1
            # Cede o controle um número *diferente* de vezes por analista, de
            # propósito. Cedendo igual, as tarefas avançam em lockstep e um
            # contador global acertaria por coincidência: todo mundo estaria na
            # mesma rodada. Fora de lockstep, um analista termina enquanto os
            # outros já escreveram outra contagem.
            for _ in range(6 - analyst):
                await asyncio.sleep(0)
            if self.seen[analyst] < analyst:
                raise ConnectionError(f"analista {analyst} instável")
            return TechnicalSignal(
                signal="COMPRA", justification=f"analista {analyst}", confidence=0.5
            )

    recording = recorder(
        RetryingLLMClient(PerAnalystFlaky(), max_attempts=5, base_delay=0)
    )

    async def ensemble() -> None:
        await asyncio.gather(
            *(
                recording.generate(
                    "s",
                    f"prompt do analista {analyst}",
                    TechnicalSignal,
                    {"analyst_id": analyst},
                    metadata=LLMCallMetadata(
                        stage=STAGE_TECHNICAL_ANALYST, analyst_id=analyst
                    ),
                )
                for analyst in range(1, 6)
            )
        )

    asyncio.run(ensemble())

    assert all(record.request.analyst_id is not None for record in recording.records)
    by_analyst = {
        cast(int, record.request.analyst_id): record for record in recording.records
    }
    assert sorted(by_analyst) == [1, 2, 3, 4, 5]
    for analyst, record in by_analyst.items():
        assert record.attempt_count == analyst, f"analista {analyst} herdou tentativas"
        assert record.request.user_prompt == f"prompt do analista {analyst}"
        assert cast(dict, record.validated_response)["justification"] == (
            f"analista {analyst}"
        )
    # Sequência densa e sem repetição: um registro por chamada lógica.
    assert [record.sequence for record in recording.records] == [0, 1, 2, 3, 4]


def test_rascunho_de_telemetria_nao_vaza_entre_tasks() -> None:
    """Duas gravações concorrentes enxergam rascunhos distintos."""
    observed: list[int] = []

    class Probe(LLMClient):
        async def generate(self, *args: Any, **kwargs: Any) -> Any:
            slot = current_call_telemetry()
            assert slot is not None
            slot.attempts = 40 + len(observed)
            observed.append(id(slot))
            await asyncio.sleep(0)
            assert slot is current_call_telemetry()
            return "ok"

    recording = recorder(Probe())

    async def concurrent() -> None:
        await asyncio.gather(
            *(recording.generate("s", f"u{number}") for number in range(3))
        )

    asyncio.run(concurrent())

    assert len(set(observed)) == 3
    assert [record.attempt_count for record in recording.records] == [40, 41, 42]


# ── Serialização do trace ────────────────────────────────────────


def test_trace_e_jsonl_determinístico_com_schema_version() -> None:
    participant, _ = run_live(price_frame(8))
    blob = participant.run_artifacts()[0].content

    assert blob.endswith(b"\n")
    assert b"\r\n" not in blob
    lines = blob.decode("utf-8").splitlines()
    payloads = [json.loads(line) for line in lines]
    assert payloads, "um run com sessões elegíveis precisa gravar chamadas"
    assert {payload["schema_version"] for payload in payloads} == {
        LLM_TRACE_SCHEMA_VERSION
    }
    # Serialização estável: reserializar os mesmos registros dá os mesmos bytes.
    assert dump_trace(load_trace(blob)) == blob
    assert [payload["sequence"] for payload in payloads] == list(range(len(payloads)))
    assert len({payload["call_id"] for payload in payloads}) == len(payloads)


def test_trace_registra_os_tres_papeis_e_o_id_do_analista() -> None:
    participant, _ = run_live(price_frame(8))
    records = participant.llm_calls

    stages = {record.request.stage for record in records}
    assert stages == {
        STAGE_TECHNICAL_ANALYST,
        STAGE_RISK_MANAGER,
        STAGE_PORTFOLIO_MANAGER,
    }
    analysts = {
        record.request.analyst_id
        for record in records
        if record.request.stage == STAGE_TECHNICAL_ANALYST
    }
    assert analysts == {1, 2, 3}
    # Papéis que não são do ensemble não inventam analista.
    assert all(
        record.request.analyst_id is None
        for record in records
        if record.request.stage != STAGE_TECHNICAL_ANALYST
    )
    # Toda chamada está ligada à sessão em que a decisão foi tomada.
    sessions = {record.request.decision_session for record in records}
    assert sessions == {
        str(pd.Timestamp(record.session).date()) for record in participant.decisions
    }


def test_trace_separa_opcao_solicitada_de_opcao_transmitida() -> None:
    """``seed`` é solicitado pelo ensemble e **não** é transmitido."""
    from src.agents.llm_client import AgentRouterLLMClient

    client = AgentRouterLLMClient(
        api_key="k", base_url="https://exemplo.invalido/v1", model="vendor/modelo"
    )
    options = {"temperature": 0.4, "seed": 99, "analyst_id": 2, "top_p": 0.9}

    assert client.transport_options(options) == {"temperature": 0.4, "top_p": 0.9}
    assert "seed" not in client.transport_options(options)
    assert client.provider_endpoint() == ("https://exemplo.invalido/v1/chat/completions")


def test_endpoint_registrado_nao_carrega_credencial() -> None:
    from src.agents.llm_client import AgentRouterLLMClient

    client = AgentRouterLLMClient(
        api_key="k",
        base_url="https://usuario:senha-secreta@provedor.invalido/v1",
        model="m",
    )
    endpoint = client.provider_endpoint() or ""

    assert "senha-secreta" not in endpoint and "usuario" not in endpoint
    assert endpoint == "https://provedor.invalido/v1/chat/completions"


def test_trace_nao_contem_credencial(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "sk-segredo-que-nao-pode-vazar")
    participant, _ = run_live(price_frame(8))
    blob = participant.run_artifacts()[0].content.decode("utf-8")

    for forbidden in (
        "sk-segredo-que-nao-pode-vazar",
        "LLM_API_KEY",
        "Authorization",
        "Bearer",
    ):
        assert forbidden not in blob


# ── Replay ───────────────────────────────────────────────────────


def test_replay_reproduz_decisoes_trades_equity_e_metricas() -> None:
    from src.backtesting.metrics import performance_metrics

    data = price_frame(24)
    live, live_result = run_live(data)
    trace = live.run_artifacts()[0].content

    replayed, client, replay_result = run_replay(data, trace)
    client.assert_complete()

    assert [record.target_weight for record in live.decisions] == [
        record.target_weight for record in replayed.decisions
    ]
    assert live_result.equity_curve.equals(replay_result.equity_curve)
    assert [
        (str(trade.date), trade.type, trade.quantity, trade.price, trade.cost)
        for trade in live_result.trades
    ] == [
        (str(trade.date), trade.type, trade.quantity, trade.price, trade.cost)
        for trade in replay_result.trades
    ]
    assert performance_metrics(live_result.equity_curve) == performance_metrics(
        replay_result.equity_curve
    )
    assert live_result.trades, "o cenário precisa produzir operações"


def test_replay_nao_toca_a_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    data = price_frame(16)
    live, _ = run_live(data)
    trace = live.run_artifacts()[0].content

    def explode(*args: Any, **kwargs: Any):
        raise AssertionError("replay não pode fazer chamada externa")

    # Superfícies de saída, não o socket em si: o próprio event loop do
    # Windows abre um ``socketpair`` local para se acordar, e derrubá-lo
    # testaria o asyncio, não a ausência de rede.
    monkeypatch.setattr("urllib.request.urlopen", explode)
    monkeypatch.setattr("urllib.request.Request", explode)
    monkeypatch.setattr("socket.create_connection", explode)
    monkeypatch.setattr("http.client.HTTPConnection.connect", explode)
    monkeypatch.setattr("http.client.HTTPSConnection.connect", explode)

    _, client, _ = run_replay(data, trace)
    client.assert_complete()

    assert client.consumed == len(live.llm_calls)


def test_replay_ignora_relogio_e_duracao() -> None:
    """Timestamp e latência não fazem parte da identidade da chamada."""
    data = price_frame(10)
    live, _ = run_live(data)
    payloads = parse_trace(live.run_artifacts()[0].content)
    for payload in payloads:
        payload["started_at"] = "1999-01-01T00:00:00.000000Z"
        payload["duration_ms"] = 999_999.0

    replayed, client, _ = run_replay(data, serialize_trace(payloads))
    client.assert_complete()

    assert [record.target_weight for record in replayed.decisions] == [
        record.target_weight for record in live.decisions
    ]


def parse_trace(trace: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in trace.decode("utf-8").splitlines()]


def serialize_trace(payloads: list[dict[str, Any]]) -> bytes:
    lines = [json.dumps(payload, sort_keys=True) for payload in payloads]
    return ("\n".join(lines) + "\n").encode("utf-8")


def mutate_trace(trace: bytes, index: int, **changes: Any) -> bytes:
    payloads = parse_trace(trace)
    payloads[index].update(changes)
    return serialize_trace(payloads)


def drop_from_trace(trace: bytes, index: int) -> bytes:
    payloads = parse_trace(trace)
    del payloads[index]
    return serialize_trace(payloads)


SCHEMAS: dict[str, type[BaseModel]] = {
    "TechnicalSignal": TechnicalSignal,
    "RiskVerdict": RiskVerdict,
    "FinalDecision": FinalDecision,
}


def replay_recorded_call(client: ReplayLLMClient, record: LLMCallRecord) -> Any:
    """Refaz, contra o replay, exatamente a chamada que foi gravada."""
    request = record.request
    client.begin_session(pd.Timestamp(request.decision_session))
    schema = SCHEMAS.get(request.response_schema or "")
    return asyncio.run(
        client.generate(
            request.system_prompt,
            request.user_prompt,
            schema,
            dict(request.requested_options),
            metadata=LLMCallMetadata(stage=request.stage, analyst_id=request.analyst_id),
        )
    )


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"user_prompt": "outro prompt"}, "user_prompt_sha256"),
        ({"system_prompt": "outro system"}, "system_prompt_sha256"),
        ({"requested_model": "outro/modelo"}, "requested_model"),
        ({"provider": "outro_provider"}, "provider"),
        ({"requested_options": {"temperature": 0.99}}, "requested_options"),
        ({"response_schema": "RiskVerdict"}, "response_schema"),
        ({"stage": "risk_manager"}, "stage"),
        ({"analyst_id": 99}, "analyst_id"),
        ({"decision_session": "1999-12-31"}, "decision_session"),
    ],
    ids=[
        "user_prompt",
        "system_prompt",
        "model",
        "provider",
        "temperature",
        "response_schema",
        "stage",
        "analyst_id",
        "decision_session",
    ],
)
def test_replay_detecta_divergencia_da_chamada(
    changes: dict[str, Any], expected: str
) -> None:
    """Divergência é erro explícito, nunca "responde a próxima assim mesmo"."""
    live, _ = run_live(price_frame(10))
    original = live.llm_calls[0]
    tampered = mutate_trace(live.run_artifacts()[0].content, 0, **changes)
    client = ReplayLLMClient.from_trace(tampered, provider="mock", requested_model="")

    with pytest.raises(ReplayMismatchError, match=expected):
        replay_recorded_call(client, original)
    # Nada foi consumido: a chamada divergente não avança o cursor.
    assert client.consumed == 0


def test_replay_detecta_ordem_de_chamadas_trocada() -> None:
    live, _ = run_live(price_frame(10))
    payloads = parse_trace(live.run_artifacts()[0].content)
    payloads[0], payloads[1] = payloads[1], payloads[0]
    swapped = serialize_trace(payloads)
    client = ReplayLLMClient.from_trace(swapped, provider="mock", requested_model="")

    with pytest.raises(ReplayMismatchError, match="does not match recorded call"):
        replay_recorded_call(client, live.llm_calls[0])


def test_divergencia_no_replay_derruba_o_run_em_vez_de_produzir_numeros() -> None:
    """No caminho completo, a divergência vira falha do run, nunca decisão."""
    data = price_frame(10)
    live, _ = run_live(data)
    tampered = mutate_trace(live.run_artifacts()[0].content, 0, user_prompt="outro")

    with pytest.raises(Exception) as failure:
        run_replay(data, tampered)

    assert "ReplayMismatchError" in str(failure.value) or isinstance(
        failure.value, ReplayMismatchError
    )
    assert "user_prompt_sha256" in str(failure.value)


def test_replay_detecta_registro_faltando() -> None:
    """Trace mais curto que a execução: o replay pede uma chamada a mais."""
    data = price_frame(10)
    live, _ = run_live(data)
    shortened = drop_from_trace(live.run_artifacts()[0].content, -1)

    with pytest.raises(Exception, match="exhausted"):
        run_replay(data, shortened)


def test_replay_detecta_registro_sobrando_ao_final() -> None:
    """Completeness: sobra de registro é código que deixou de chamar."""
    data = price_frame(10)
    live, _ = run_live(data)
    trace = live.run_artifacts()[0].content
    payloads = parse_trace(trace)
    extra = dict(payloads[-1])
    extra["sequence"] = extra["sequence"] + 1
    extra["call_id"] = extra["call_id"] + "-extra"
    inflated = serialize_trace([*payloads, extra])

    _, client, _ = run_replay(data, inflated)

    assert client.pending, "o registro extra precisa sobrar"
    with pytest.raises(ReplayMismatchError, match="consumed .* of .* recorded"):
        client.assert_complete()


def test_replay_recusa_schema_version_desconhecido() -> None:
    live, _ = run_live(price_frame(8))
    tampered = mutate_trace(live.run_artifacts()[0].content, 0, schema_version=99)

    with pytest.raises(ReplayMismatchError, match="schema_version"):
        load_trace(tampered)


def test_replay_reproduz_falha_registrada_com_o_tipo_original() -> None:
    record = LLMCallRecord(
        call_id="2023-03-15|risk_manager|-|000000",
        sequence=0,
        request=LLMCallRequest(
            stage=STAGE_RISK_MANAGER,
            analyst_id=None,
            decision_session="2023-03-15",
            provider="mock",
            requested_model="m/1",
            system_prompt="s",
            user_prompt="u",
            response_schema=None,
            response_schema_sha256=None,
            requested_options={},
        ),
        started_at="2023-03-15T00:00:00.000000Z",
        duration_ms=1.0,
        attempt_count=3,
        status="error",
        error_type="TimeoutError",
        error_message="provider timeout",
    )
    client = ReplayLLMClient([record], provider="mock", requested_model="m/1")
    client.begin_session(SESSION)

    with pytest.raises(TimeoutError, match="provider timeout"):
        asyncio.run(
            client.generate("s", "u", metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER))
        )
    client.assert_complete()


def test_replay_revalida_a_resposta_contra_o_schema() -> None:
    """Payload gravado que não satisfaz mais o contrato não passa calado."""
    live, _ = run_live(price_frame(8))
    trace = live.run_artifacts()[0].content
    tampered = mutate_trace(trace, 0, validated_response={"signal": "TALVEZ"})

    with pytest.raises(Exception) as failure:
        run_replay(price_frame(8), tampered)
    assert not isinstance(failure.value, ReplayMismatchError)


# ── A gravação não muda a estratégia ─────────────────────────────


def test_gravacao_nao_altera_a_decisao_do_participante() -> None:
    """O recorder devolve exatamente a resposta do cliente embrulhado."""
    data = price_frame(20)
    with_trace, result = run_live(data)

    direct = LLMParticipant(TICKER, provider="mock", **PARAMS)
    baseline = ExecutionEngine(direct, {TICKER: data}, CAPITAL, COSTS).run()

    assert result.equity_curve.equals(baseline.equity_curve)
    assert [record.target_weight for record in with_trace.decisions] == [
        record.target_weight for record in direct.decisions
    ]


def test_participante_grava_uma_chamada_por_no_e_por_analista() -> None:
    data = price_frame(6)
    participant = LLMParticipant(
        TICKER,
        provider="mock",
        **{**PARAMS, "decision_frequency": 6},
    )
    observation = MarketObservation(
        session=cast(pd.Timestamp, data.index[-1]),
        history={TICKER: data},
        positions={TICKER: 0},
        cash=CAPITAL,
        equity=CAPITAL,
    )
    participant.decide(observation)

    stages = [record.request.stage for record in participant.llm_calls]
    # Três analistas, depois risco, depois portfólio: uma chamada lógica cada.
    assert stages == [STAGE_TECHNICAL_ANALYST] * 3 + [
        STAGE_RISK_MANAGER,
        STAGE_PORTFOLIO_MANAGER,
    ]


# ── Prompt lógico versus prompt de transporte ────────────────────
#
# O ``AgentRouterLLMClient`` não envia o prompt lógico: ele acrescenta o
# ``model_json_schema()`` serializado ao system prompt antes de montar o corpo
# HTTP. O trace publica o prompt lógico, e por isso a identidade da chamada
# precisa incluir o digest do schema — é a outra metade do que foi enviado.

SCHEMA_INSTRUCTION = "\n\nResponda estritamente em JSON válido seguindo a estrutura:\n"


def schema_pair() -> tuple[type[BaseModel], type[BaseModel]]:
    """Dois schemas com o **mesmo** ``__qualname__`` e estruturas diferentes.

    É o caso realista de alguém afrouxar um limite de ``Field`` sem renomear a
    classe: o nome lógico não muda, o JSON Schema muda, e o prompt que chega ao
    provedor muda junto.
    """

    def make(upper: float) -> type[BaseModel]:
        class Payload(BaseModel):
            model_config = ConfigDict(extra="forbid")
            confidence: float = Field(ge=0.0, le=upper)

        return Payload

    tight, loose = make(1.0), make(100.0)
    assert tight.__qualname__ == loose.__qualname__
    assert tight.model_json_schema() != loose.model_json_schema()
    return tight, loose


def test_digest_do_schema_e_o_hash_do_json_schema_canonico() -> None:
    assert schema_digest(None) is None
    assert schema_digest(TechnicalSignal) == sha256_text(
        canonical_json(TechnicalSignal.model_json_schema())
    )
    # Nome igual não implica contrato igual.
    tight, loose = schema_pair()
    assert schema_name(tight) == schema_name(loose)
    assert schema_digest(tight) != schema_digest(loose)


def test_prompt_logico_nao_e_o_texto_enviado_ao_provedor() -> None:
    """Prova a transformação que o adaptador aplica antes do transporte."""
    sent: dict[str, Any] = {}

    def transport(method: str, url: str, headers: dict[str, str], body: dict[str, Any]):
        sent["body"] = body
        payload = {"choices": [{"message": {"content": '{"confidence": 0.5}'}}]}
        return json.dumps(payload).encode("utf-8")

    tight, _ = schema_pair()
    client = AgentRouterLLMClient(
        api_key="k",
        base_url="https://exemplo.invalido/v1",
        model="m/1",
        transport=transport,
    )
    recording = recorder(client, provider="agent_router")
    asyncio.run(
        recording.generate(
            "prompt lógico",
            "u",
            tight,
            metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER),
        )
    )

    transported = sent["body"]["messages"][0]["content"]
    (record,) = recording.records
    # O que foi enviado NÃO é o prompt lógico publicado no trace.
    assert transported != record.request.system_prompt
    assert transported.startswith("prompt lógico")
    assert SCHEMA_INSTRUCTION in transported
    # Mas é determinado por ele mais o schema, e ambos estão na identidade.
    assert transported == (
        "prompt lógico"
        + SCHEMA_INSTRUCTION
        + json.dumps(tight.model_json_schema(), ensure_ascii=False)
    )
    assert record.request.response_schema_sha256 == schema_digest(tight)
    # E o hash do texto final é publicado como evidência direta.
    assert record.transport_system_prompt_sha256 == sha256_text(transported)
    assert record.transport_system_prompt_sha256 != record.request.system_prompt_sha256


def test_hash_de_transporte_e_nulo_quando_nao_ha_transformacao() -> None:
    """O mock não transforma nada; inventar um hash seria fato fabricado."""
    recording = recorder(MockLLMClient())
    asyncio.run(recording.generate("s", "u"))

    (record,) = recording.records
    assert record.transport_system_prompt_sha256 is None


def test_hash_de_transporte_nao_carrega_credencial() -> None:
    """Cabeçalhos não entram no trace; o hash cobre só o corpo da mensagem."""

    def transport(method: str, url: str, headers: dict[str, str], body: dict[str, Any]):
        assert headers["Authorization"] == "Bearer sk-segredo"
        payload = {"choices": [{"message": {"content": "ok"}}]}
        return json.dumps(payload).encode("utf-8")

    client = AgentRouterLLMClient(
        api_key="sk-segredo",
        base_url="https://exemplo.invalido/v1",
        model="m/1",
        transport=transport,
    )
    recording = recorder(client, provider="agent_router")
    asyncio.run(recording.generate("s", "u"))

    published = dump_trace(recording.records).decode("utf-8")
    for forbidden in ("sk-segredo", "Authorization", "Bearer"):
        assert forbidden not in published


def test_replay_detecta_schema_de_mesmo_nome_e_estrutura_diferente() -> None:
    """A prova central: nome lógico igual, contrato diferente, replay recusa.

    Sem ``response_schema_sha256`` na identidade este caso passava em silêncio —
    e não é inofensivo: o schema é serializado dentro do system prompt, então as
    duas execuções perguntaram coisas diferentes ao provedor.
    """
    tight, loose = schema_pair()
    recording = recorder(MockLLMClient({tight: {"confidence": 0.9}}))
    asyncio.run(
        recording.generate(
            "s", "u", tight, metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER)
        )
    )
    trace = dump_trace(recording.records)

    replay = ReplayLLMClient.from_trace(trace, provider="mock", requested_model="m/1")
    replay.begin_session(SESSION)

    with pytest.raises(ReplayMismatchError, match="response_schema_sha256"):
        asyncio.run(
            replay.generate(
                "s", "u", loose, metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER)
            )
        )
    # O payload gravado ainda satisfaria o schema novo: sem o digest, nada
    # denunciaria a troca.
    assert loose.model_validate({"confidence": 0.9})
    assert replay.consumed == 0


def test_replay_aceita_o_mesmo_schema_estruturalmente_identico() -> None:
    """O digest não é do objeto: dois `type` distintos e iguais casam."""
    first, _ = schema_pair()
    second, _ = schema_pair()
    assert first is not second

    recording = recorder(MockLLMClient({first: {"confidence": 0.4}}))
    asyncio.run(
        recording.generate(
            "s", "u", first, metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER)
        )
    )
    replay = ReplayLLMClient.from_trace(
        dump_trace(recording.records), provider="mock", requested_model="m/1"
    )
    replay.begin_session(SESSION)

    response = asyncio.run(
        replay.generate(
            "s", "u", second, metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER)
        )
    )

    assert isinstance(response, second)
    replay.assert_complete()


# ── Conclusão fora de ordem entre analistas paralelos ────────────

#: Analista 1 é o mais lento, 2 o mais rápido, 3 intermediário. A ordem de
#: conclusão fica deliberadamente diferente da ordem de emissão.
OUT_OF_ORDER_DELAYS = {1: 0.05, 2: 0.0, 3: 0.02}


class OutOfOrderProvider(LLMClient):
    """Provedor falso cujas respostas chegam fora da ordem em que foram pedidas."""

    def __init__(self) -> None:
        super().__init__()
        self.completion_order: list[int] = []

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> Any:
        analyst = cast(LLMCallMetadata, metadata).analyst_id or 0
        await asyncio.sleep(OUT_OF_ORDER_DELAYS[analyst])
        self.completion_order.append(analyst)
        return TechnicalSignal(
            signal="COMPRA",
            justification=f"analista {analyst}",
            confidence=round(0.1 * analyst, 1),
        )


def record_out_of_order() -> tuple[RecordingLLMClient, OutOfOrderProvider]:
    provider = OutOfOrderProvider()
    recording = recorder(provider)

    async def ensemble() -> None:
        await asyncio.gather(
            *(
                recording.generate(
                    "sys",
                    f"prompt do analista {analyst}",
                    TechnicalSignal,
                    {"analyst_id": analyst, "temperature": 0.1 * analyst},
                    metadata=LLMCallMetadata(
                        stage=STAGE_TECHNICAL_ANALYST, analyst_id=analyst
                    ),
                )
                for analyst in (1, 2, 3)
            )
        )

    asyncio.run(ensemble())
    return recording, provider


def replay_out_of_order(trace: bytes) -> tuple[ReplayLLMClient, dict[int, Any]]:
    """Reexecuta o mesmo ensemble **sem** latência alguma."""
    replay = ReplayLLMClient.from_trace(trace, provider="mock", requested_model="m/1")
    replay.begin_session(SESSION)
    answers: dict[int, Any] = {}

    async def ensemble() -> None:
        async def one(analyst: int) -> None:
            answers[analyst] = await replay.generate(
                "sys",
                f"prompt do analista {analyst}",
                TechnicalSignal,
                {"analyst_id": analyst, "temperature": 0.1 * analyst},
                metadata=LLMCallMetadata(
                    stage=STAGE_TECHNICAL_ANALYST, analyst_id=analyst
                ),
            )

        await asyncio.gather(*(one(analyst) for analyst in (1, 2, 3)))

    asyncio.run(ensemble())
    return replay, answers


def test_trace_e_canonico_por_ordem_de_emissao_nao_de_conclusao() -> None:
    """O artefato não depende de quem terminou primeiro.

    ``sequence`` é atribuído de forma síncrona, quando a chamada é *emitida*, e
    ``records`` publica ordenado por ele. A ordem de conclusão das tarefas do
    ensemble depende do escalonador e não atravessa para o arquivo.
    """
    recording, provider = record_out_of_order()

    assert provider.completion_order != [1, 2, 3], "o cenário precisa sair de ordem"
    assert sorted(provider.completion_order) == [1, 2, 3]
    assert [record.request.analyst_id for record in recording.records] == [1, 2, 3]
    assert [record.sequence for record in recording.records] == [0, 1, 2]
    # Cada registro ficou com a resposta do seu próprio analista.
    for record in recording.records:
        analyst = record.request.analyst_id
        assert record.request.user_prompt == f"prompt do analista {analyst}"
        assert cast(dict, record.validated_response)["justification"] == (
            f"analista {analyst}"
        )


def test_trace_de_analistas_concorrentes_e_estavel_entre_execucoes() -> None:
    """Repetir o mesmo ensemble produz o mesmo arquivo, byte a byte.

    Comparando só os campos materiais: relógio e duração mudam por definição.
    """
    materials: set[str] = set()
    completions: set[tuple[int, ...]] = set()
    for _ in range(5):
        recording, provider = record_out_of_order()
        completions.add(tuple(provider.completion_order))
        materials.add(
            canonical_json([record.request.identity() for record in recording.records])
        )

    assert len(materials) == 1, "a identidade publicada variou entre execuções"
    assert completions, "o cenário precisa ter rodado"


def test_replay_sem_latencia_reproduz_o_ensemble_fora_de_ordem() -> None:
    """Sem as latências, cada analista recebe de volta a sua própria resposta."""
    recording, provider = record_out_of_order()
    assert provider.completion_order != [1, 2, 3]
    trace = dump_trace(recording.records)

    replay, answers = replay_out_of_order(trace)

    replay.assert_complete()
    assert replay.consumed == 3
    for analyst in (1, 2, 3):
        assert answers[analyst].justification == f"analista {analyst}"
        assert answers[analyst].confidence == pytest.approx(0.1 * analyst)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"analyst_id": 99}, "analyst_id"),
        ({"user_prompt": "outro prompt"}, "user_prompt_sha256"),
        (
            {"requested_options": {"analyst_id": 1, "temperature": 0.9}},
            "requested_options",
        ),
        ({"stage": "risk_manager"}, "stage"),
    ],
    ids=["analyst_id", "prompt", "option", "stage"],
)
def test_replay_do_bloco_paralelo_ainda_recusa_divergencia(
    changes: dict[str, Any], expected: str
) -> None:
    """Ignorar a ordem de conclusão não afrouxa nada mais."""
    recording, _ = record_out_of_order()
    tampered = mutate_trace(dump_trace(recording.records), 0, **changes)

    with pytest.raises(ReplayMismatchError, match=expected):
        replay_out_of_order(tampered)


def test_replay_do_bloco_paralelo_detecta_registro_faltando() -> None:
    recording, _ = record_out_of_order()
    shortened = drop_from_trace(dump_trace(recording.records), -1)

    with pytest.raises(ReplayMismatchError, match="exhausted"):
        replay_out_of_order(shortened)


def test_replay_do_bloco_paralelo_detecta_registro_excedente() -> None:
    recording, _ = record_out_of_order()
    payloads = parse_trace(dump_trace(recording.records))
    extra = dict(payloads[-1])
    extra["sequence"] = extra["sequence"] + 1
    extra["call_id"] = extra["call_id"] + "-extra"

    replay, _ = replay_out_of_order(serialize_trace([*payloads, extra]))

    assert replay.pending
    with pytest.raises(ReplayMismatchError, match="consumed .* of .* recorded"):
        replay.assert_complete()
