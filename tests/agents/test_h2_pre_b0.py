"""Contrato pré-B0 do participante LLM para o H2 (Self-Consistency).

Prova o que o hardening implementou sem rodar experimento nenhum: prompt
lógico idêntico entre amostras, maioria estrita 3/5, causas finais
estruturadas, ``BUY_AT_TARGET_NOOP``, fail-closed de entrada, política de
inversão do PM, opções de geração nos três papéis, ``decisions.jsonl`` e o
preflight de capacidades. Tudo com mock: nenhuma rede, nenhum resultado.
"""

import json
from types import MappingProxyType
from typing import Any, cast

import pandas as pd
import pytest

import src.agents.participant as participant_module
from src.agents.llm_client import (
    LLMClient,
    MockLLMClient,
    ProviderRequestRejected,
    ProviderTransportError,
)
from src.agents.participant import (
    ACTION_BUY,
    ACTION_SELL,
    BUY_AT_TARGET_NOOP,
    CAPABILITY_DECLARED_UNQUALIFIED,
    CAPABILITY_NOT_APPLICABLE,
    CAPABILITY_QUALIFIED,
    INVALID_INPUT,
    INVALID_RESPONSE,
    LLM_DECISION_ARTIFACT_SCHEMA_VERSION,
    NOT_ELIGIBLE,
    PORTFOLIO_HOLD,
    PROVIDER_FAILURE,
    PROVIDER_REQUEST_REJECTED,
    RISK_VETO_DRAWDOWN,
    RISK_VETO_LLM,
    RISK_VETO_VOLATILITY,
    SCIENTIFIC_REQUIRED_PARAMS,
    TECH_EXPLICIT_HOLD,
    TECH_NO_MAJORITY,
    LLMDecisionError,
    LLMParticipant,
    classify_decision,
)
from src.agents.state import (
    PortfolioAction,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
)
from src.backtesting.arena import MarketObservation
from src.experiments.hardening import (
    H2_SC_PROVISIONAL_PARAMS,
    H_SYN_ARCHETYPES,
    HardeningState,
    frozen_observation,
    synthetic_frame,
    synthetic_states,
)

CAPITAL = 100_000.0
APPROVED = {"verdict": "APROVADO", "analysis": "mock", "risk_metrics": {}}
UPTREND = synthetic_states()[0]
TICKER = UPTREND.ticker


def vote(kind: str) -> dict[str, Any]:
    return {"signal": kind, "justification": "mock", "confidence": 0.7}


def action(kind: str) -> dict[str, Any]:
    return {"decision": kind, "reasoning": "mock"}


def client(
    votes: list[str],
    decision: str = "COMPRA",
    risk: dict[str, Any] = APPROVED,
) -> MockLLMClient:
    return MockLLMClient(
        {
            TechnicalSignal: [vote(kind) for kind in votes],
            RiskVerdict: risk,
            PortfolioAction: action(decision),
        }
    )


def sc(llm: LLMClient, **overrides: Any) -> LLMParticipant:
    return LLMParticipant(
        TICKER, llm_client=llm, **{**H2_SC_PROVISIONAL_PARAMS, **overrides}
    )


def decide(participant: LLMParticipant, observation: MarketObservation | None = None):
    intents = participant.decide(observation or frozen_observation(UPTREND, CAPITAL))
    return intents, participant.decisions[-1]


def invested(history: pd.DataFrame) -> MarketObservation:
    """Carteira integralmente investida: caixa zero, peso exatamente 1."""
    close = float(history["fechamento"].iloc[-1])
    return MarketObservation(
        session=cast(pd.Timestamp, history.index[-1]),
        history=MappingProxyType({TICKER: history.copy()}),
        positions=MappingProxyType({TICKER: CAPITAL / close}),
        cash=0.0,
        equity=CAPITAL,
    )


# ── Self-Consistency ─────────────────────────────────────────────


def test_prompt_logico_e_identico_entre_os_cinco_analistas() -> None:
    participant = sc(client(["COMPRA"] * 5))
    decide(participant)

    technical = [
        r for r in participant.llm_calls if r.request.stage == "technical_analyst"
    ]
    assert len(technical) == 5
    assert len({r.request.system_prompt for r in technical}) == 1
    assert len({r.request.user_prompt for r in technical}) == 1
    assert "analista" not in technical[0].request.user_prompt
    # Quem é o analista é metadado e identidade, nunca texto do prompt.
    assert sorted(cast(int, r.request.analyst_id) for r in technical) == [1, 2, 3, 4, 5]
    assert len({r.request.identity_digest for r in technical}) == 5
    assert {r.request.requested_options["temperature"] for r in technical} == {1.0}


@pytest.mark.parametrize(
    ("votes", "cause"),
    [
        (["COMPRA", "COMPRA", "COMPRA", "VENDA", "MANTER"], ACTION_BUY),
        (["COMPRA", "COMPRA", "VENDA", "VENDA", "MANTER"], TECH_NO_MAJORITY),
        (["MANTER", "MANTER", "MANTER", "COMPRA", "VENDA"], TECH_EXPLICIT_HOLD),
    ],
    ids=["3/5 alcanca consenso", "2-2-1 nao alcanca", "maioria MANTER"],
)
def test_maioria_estrita_tres_de_cinco(votes: list[str], cause: str) -> None:
    intents, record = decide(sc(client(votes)))
    assert record.final_cause == cause
    if cause == ACTION_BUY:
        assert record.consensus is not None and record.consensus.consensus_reached
        assert intents
    else:
        assert intents == []


def test_maioria_manter_e_distinguivel_de_ausencia_de_maioria() -> None:
    _, held = decide(sc(client(["MANTER"] * 3 + ["COMPRA", "VENDA"])))
    _, split = decide(sc(client(["COMPRA", "COMPRA", "VENDA", "VENDA", "MANTER"])))
    assert (held.technical_outcome, held.final_cause) == ("MANTER", TECH_EXPLICIT_HOLD)
    assert (split.technical_outcome, split.final_cause) == (
        "NO_MAJORITY",
        TECH_NO_MAJORITY,
    )


def test_limiar_legado_de_cinco_sextos_exige_unanimidade_com_cinco() -> None:
    _, record = decide(sc(client(["COMPRA"] * 4 + ["VENDA"]), consensus_threshold=5 / 6))
    assert record.final_cause == TECH_NO_MAJORITY


# ── BUY_AT_TARGET_NOOP ───────────────────────────────────────────


def test_compra_ja_no_alvo_e_noop_e_nao_veto_de_risco() -> None:
    participant = sc(client(["COMPRA"] * 5))
    intents, record = decide(participant, invested(UPTREND.history))

    # A regra de concentração continua vetando (comportamento econômico
    # intocado: nenhuma intenção) — só a classificação deixou de ser veto.
    assert record.risk_verdict is not None and record.risk_verdict.verdict == "VETADO"
    assert record.risk_rule == "CONCENTRATION"
    assert record.observed_weight == pytest.approx(1.0)
    assert record.final_cause == BUY_AT_TARGET_NOOP
    assert intents == []


def test_compra_com_carteira_zerada_continua_acao() -> None:
    _, record = decide(sc(client(["COMPRA"] * 5)))
    assert record.observed_weight == 0.0
    assert record.final_cause == ACTION_BUY


# ── Fail-closed de entrada ───────────────────────────────────────


def test_entrada_incompleta_falha_antes_de_chamar_o_provedor() -> None:
    llm = client(["COMPRA"] * 5)
    participant = sc(llm)
    short = UPTREND.history.iloc[:120]

    with pytest.raises(LLMDecisionError) as raised:
        decide(
            participant, frozen_observation(HardeningState("s", TICKER, short), CAPITAL)
        )

    assert raised.value.reason == INVALID_INPUT
    assert llm.calls == []
    record = participant.decisions[-1]
    assert record.final_cause == INVALID_INPUT
    assert "missing_feature:sma200_gap" in record.input_violations


def test_sem_strict_inputs_a_sessao_segue_mas_nunca_vira_prudencia() -> None:
    participant = sc(client(["MANTER"] * 5), strict_inputs=False)
    short = UPTREND.history.iloc[:10]
    _, record = decide(
        participant, frozen_observation(HardeningState("s", TICKER, short), CAPITAL)
    )
    assert record.final_cause == INVALID_INPUT
    assert "volatility_window_incomplete" in record.input_violations


# ── Falhas técnicas ──────────────────────────────────────────────


class Unreachable(LLMClient):
    async def generate(self, *args: Any, **kwargs: Any):
        raise ConnectionError("provider down")


def test_falha_de_provedor_e_provider_failure() -> None:
    participant = sc(Unreachable())
    with pytest.raises(LLMDecisionError) as raised:
        decide(participant)
    assert raised.value.reason == PROVIDER_FAILURE
    assert participant.decisions[-1].final_cause == PROVIDER_FAILURE


def test_resposta_fora_do_schema_e_invalid_response() -> None:
    llm = MockLLMClient({TechnicalSignal: "not-json"})
    participant = sc(llm)
    with pytest.raises(LLMDecisionError) as raised:
        decide(participant)
    assert raised.value.reason == INVALID_RESPONSE


def test_inversao_do_pm_com_flag_e_invalid_response_sem_intencao() -> None:
    intents, record = decide(
        sc(client(["COMPRA"] * 5, decision="VENDA"), portfolio_inversion_policy="flag")
    )
    assert record.portfolio_rule == "DIRECTION_INVERSION"
    assert record.final_cause == INVALID_RESPONSE
    assert intents == []


def test_inversao_do_pm_com_fail_derruba_a_decisao() -> None:
    # ``fail`` é o valor provisório do H2 (PENDING_ADVISOR_RATIFICATION).
    assert H2_SC_PROVISIONAL_PARAMS["portfolio_inversion_policy"] == "fail"
    participant = sc(client(["COMPRA"] * 5, decision="VENDA"))
    with pytest.raises(LLMDecisionError) as raised:
        decide(participant)
    assert raised.value.reason == INVALID_RESPONSE


class FailAt(LLMClient):
    """Votos, risco e portfólio válidos, exceto no estágio ``schema``."""

    def __init__(self, schema: type, error: BaseException) -> None:
        super().__init__()
        self.schema = schema
        self.error = error
        self.inner = client(["COMPRA"] * 5)

    async def generate(self, system_prompt, user_prompt, response_schema=None, options=None, *, metadata=None):
        if response_schema is self.schema:
            raise self.error
        return await self.inner.generate(
            system_prompt, user_prompt, response_schema, options, metadata=metadata
        )


STAGES = {
    TechnicalSignal: "technical_analyst",
    RiskVerdict: "risk_manager",
    PortfolioAction: "portfolio_manager",
}


@pytest.mark.parametrize("schema", list(STAGES), ids=list(STAGES.values()))
@pytest.mark.parametrize(
    "error",
    [ConnectionError("provider down"), TimeoutError("provider slow")],
    ids=["connection", "timeout"],
)
def test_falha_de_provedor_em_qualquer_papel_e_provider_failure(
    schema: type, error: BaseException
) -> None:
    participant = sc(FailAt(schema, error))
    with pytest.raises(LLMDecisionError) as raised:
        participant.decide(frozen_observation(UPTREND, CAPITAL))

    assert raised.value.reason == PROVIDER_FAILURE
    (record,) = participant.decisions
    assert record.final_cause == PROVIDER_FAILURE
    # Nunca MANTER financeiro: nenhum peso alvo, nenhum intent.
    assert record.target_weight is None
    assert record.llm_failures and type(error).__name__ in record.llm_failures[0]
    # O trace guarda a chamada que falhou, no papel certo.
    failed = [r for r in participant.llm_calls if r.status == "error"]
    assert failed and {r.request.stage for r in failed} == {STAGES[schema]}
    # O estado parcial é evidência: o quorum que já tinha decidido continua lá.
    if schema is not TechnicalSignal:
        assert record.consensus is not None and record.consensus.winning_signal == "COMPRA"


def test_recusa_da_requisicao_e_provider_request_rejected() -> None:
    participant = sc(FailAt(RiskVerdict, ProviderRequestRejected("HTTP 400", status=400)))
    with pytest.raises(LLMDecisionError) as raised:
        participant.decide(frozen_observation(UPTREND, CAPITAL))
    assert raised.value.reason == PROVIDER_REQUEST_REJECTED
    assert participant.decisions[-1].final_cause == PROVIDER_REQUEST_REJECTED


def test_bug_fora_do_limite_do_provedor_continua_subindo_cru(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Só exceção registrada pelo limite do provedor vira estado parcial."""
    participant = sc(client(["COMPRA"] * 5))
    monkeypatch.setattr(
        participant.graph, "astream", lambda *a, **k: _raise_async(KeyError("bug"))
    )
    with pytest.raises(KeyError):
        participant.decide(frozen_observation(UPTREND, CAPITAL))


async def _raise_async(error: BaseException):
    raise error
    yield  # pragma: no cover - torna a função um gerador assíncrono


# ── BUY_AT_TARGET_NOOP: nunca com intent executável ──────────────


def at_weight(history: pd.DataFrame, weight: float) -> MarketObservation:
    close = float(history["fechamento"].iloc[-1])
    return MarketObservation(
        session=cast(pd.Timestamp, history.index[-1]),
        history=MappingProxyType({TICKER: history.copy()}),
        positions=MappingProxyType({TICKER: weight * CAPITAL / close}),
        cash=(1 - weight) * CAPITAL,
        equity=CAPITAL,
    )


VETO_LLM = {"verdict": "VETADO", "analysis": "mock", "risk_metrics": {}}


@pytest.mark.parametrize(
    ("weight", "target", "ceiling", "risk", "cause", "intent"),
    [
        # H2: alvo = teto = 1.0; a regra de concentração veta, nada é emitido.
        (1.0, 1.0, 1.0, APPROVED, BUY_AT_TARGET_NOOP, None),
        # Faixa que a regra (6 casas) já trata como 1.0: mesma representação.
        (1 - 4e-7, 1.0, 1.0, APPROVED, BUY_AT_TARGET_NOOP, None),
        # Abaixo do alvo canônico: não é no-op, compra o que falta.
        (0.999999, 1.0, 1.0, APPROVED, ACTION_BUY, 1.0),
        (0.9, 1.0, 1.0, APPROVED, ACTION_BUY, 1.0),
        # Fora do H2: alvo 0.25 < teto 0.30. COMPRA aprovada no alvo ainda é
        # intent — com caixa o peso deriva e o executor rebalanceia.
        (0.25, 0.25, 0.30, APPROVED, ACTION_BUY, 0.25),
        (0.25 - 4e-7, 0.25, 0.30, APPROVED, ACTION_BUY, 0.25),
        # Mesmo alvo, mas vetado: nenhum intent, aí sim no-op.
        (0.25, 0.25, 0.30, VETO_LLM, BUY_AT_TARGET_NOOP, None),
    ],
    ids=[
        "h2-exato",
        "h2-faixa-arredondada",
        "h2-abaixo",
        "h2-bem-abaixo",
        "alvo-025-aprovado",
        "alvo-025-ligeiramente-abaixo",
        "alvo-025-vetado",
    ],
)
def test_noop_so_quando_nenhuma_intencao_e_emitida(
    weight: float,
    target: float,
    ceiling: float,
    risk: dict[str, Any],
    cause: str,
    intent: float | None,
) -> None:
    participant = sc(
        client(["COMPRA"] * 5, risk=risk),
        long_target_weight=target,
        risk_max_concentration=ceiling,
    )
    intents, record = decide(participant, at_weight(UPTREND.history, weight))
    assert record.final_cause == cause
    assert [i.target_weight for i in intents] == ([] if intent is None else [intent])
    # O invariante que o artefato precisa respeitar.
    if record.final_cause == BUY_AT_TARGET_NOOP:
        assert intents == [] and record.target_weight is None


# ── Opções de geração ────────────────────────────────────────────


def test_opcoes_de_geracao_chegam_aos_tres_papeis() -> None:
    participant = sc(client(["COMPRA"] * 5), thinking_level="low", max_output_tokens=2048)
    decide(participant)

    by_stage = {
        r.request.stage: dict(r.request.requested_options) for r in participant.llm_calls
    }
    declared = {"temperature": 1.0, "thinking_level": "low", "max_output_tokens": 2048}
    assert by_stage["risk_manager"] == declared
    assert by_stage["portfolio_manager"] == declared
    technical = by_stage["technical_analyst"]
    assert {key: technical[key] for key in declared} == declared
    # seed continua só metadado do quorum, nunca opção de risco/portfólio.
    assert "seed" in technical and "seed" not in by_stage["risk_manager"]


def test_sem_opcoes_declaradas_risco_e_portfolio_seguem_como_antes() -> None:
    params = {
        key: value
        for key, value in H2_SC_PROVISIONAL_PARAMS.items()
        if key != "temperature"
    }
    participant = LLMParticipant(TICKER, llm_client=client(["COMPRA"] * 5), **params)
    decide(participant)
    risk = [r for r in participant.llm_calls if r.request.stage == "risk_manager"]
    assert dict(risk[0].request.requested_options) == {}


def test_temperature_e_faixa_nao_podem_ser_declaradas_juntas() -> None:
    with pytest.raises(ValueError, match="either temperature"):
        sc(client(["COMPRA"] * 5), temperature_min=0.2)


# ── decisions.jsonl ──────────────────────────────────────────────


def test_decisions_jsonl_tem_uma_linha_por_sessao_consultada() -> None:
    history = synthetic_frame(H_SYN_ARCHETYPES[0])
    participant = sc(client(["COMPRA"] * 5), decision_frequency=2)
    for end in (590, 591):
        participant.decide(
            frozen_observation(HardeningState("s", TICKER, history.iloc[:end]), CAPITAL)
        )

    trace, decisions = participant.run_artifacts()
    assert trace.name == "llm_calls"
    assert (decisions.name, decisions.filename) == ("llm_decisions", "decisions.jsonl")
    assert decisions.schema_version == LLM_DECISION_ARTIFACT_SCHEMA_VERSION
    assert dict(decisions.summary) == {"decision_count": 1, "not_eligible_count": 1}

    first, second = (json.loads(line) for line in decisions.content.decode().splitlines())
    assert first["final_cause"] == ACTION_BUY and first["eligible"] is True
    assert first["vote_counts"] == {"COMPRA": 5, "VENDA": 0, "MANTER": 0}
    assert first["valid_votes"] == first["analyst_count"] == 5
    assert first["consensus_threshold"] == 0.6 and first["consensus_reached"] is True
    assert first["technical_outcome"] == "COMPRA"
    assert (first["risk_verdict"], first["risk_source"], first["risk_rule"]) == (
        "APROVADO",
        "LLM",
        None,
    )
    assert (first["portfolio_called"], first["portfolio_decision"]) == (True, "COMPRA")
    assert (first["observed_weight"], first["target_weight"]) == (0.0, 1.0)
    assert second == {
        "schema_version": LLM_DECISION_ARTIFACT_SCHEMA_VERSION,
        "decision_session": str(cast(pd.Timestamp, history.index[590]).date()),
        "ticker": TICKER,
        "eligible": False,
        "final_cause": NOT_ELIGIBLE,
    }


# ── Classificação ────────────────────────────────────────────────


def consensus(
    winner: str | None, reached: bool = True, valid: int = 5
) -> TechnicalConsensus:
    return TechnicalConsensus(
        total_analysts=5,
        valid_votes=valid,
        threshold=0.6,
        counts={"COMPRA": 0, "VENDA": 0, "MANTER": 0},
        consensus_reached=reached,
        winning_signal=winner,
    )


def classify(**overrides: Any) -> str:
    fields: dict[str, Any] = {
        "consensus": consensus("COMPRA"),
        "risk_verdict": RiskVerdict(verdict="APROVADO", analysis="x"),
        "risk_source": "LLM",
        "risk_rule": None,
        "portfolio_action": PortfolioAction(decision="COMPRA", reasoning="x"),
        "portfolio_rule": None,
        "observed_weight": 0.0,
        "long_target_weight": 1.0,
    }
    fields.update(overrides)
    return classify_decision(**fields)


VETO = RiskVerdict(verdict="VETADO", analysis="x")


@pytest.mark.parametrize(
    ("overrides", "cause"),
    [
        ({}, ACTION_BUY),
        (
            {
                "consensus": consensus("VENDA"),
                "portfolio_action": PortfolioAction(decision="VENDA", reasoning="x"),
            },
            ACTION_SELL,
        ),
        (
            {"portfolio_action": PortfolioAction(decision="MANTER", reasoning="x")},
            PORTFOLIO_HOLD,
        ),
        (
            {
                "risk_verdict": VETO,
                "risk_source": "HARD_RULE",
                "risk_rule": "VOLATILITY",
                "portfolio_action": None,
            },
            RISK_VETO_VOLATILITY,
        ),
        (
            {
                "risk_verdict": VETO,
                "risk_source": "HARD_RULE",
                "risk_rule": "DRAWDOWN",
                "portfolio_action": None,
            },
            RISK_VETO_DRAWDOWN,
        ),
        (
            {"risk_verdict": VETO, "risk_source": "LLM", "portfolio_action": None},
            RISK_VETO_LLM,
        ),
        (
            {
                "risk_verdict": VETO,
                "risk_source": "HARD_RULE",
                "risk_rule": "CONCENTRATION",
                "observed_weight": 1.0,
                "portfolio_action": None,
            },
            BUY_AT_TARGET_NOOP,
        ),
        ({"consensus": consensus(None, reached=False)}, TECH_NO_MAJORITY),
        ({"consensus": consensus("MANTER")}, TECH_EXPLICIT_HOLD),
        ({"consensus": consensus(None, reached=False, valid=4)}, INVALID_RESPONSE),
        ({"risk_rule": "MISSING_METRICS"}, INVALID_INPUT),
        ({"input_violations": ("missing_feature:rsi",)}, INVALID_INPUT),
        ({"failures": (TimeoutError("t"),)}, PROVIDER_FAILURE),
        ({"failures": (ValueError("schema"),)}, INVALID_RESPONSE),
        ({"failures": (ProviderTransportError("HTTP 503"),)}, PROVIDER_FAILURE),
        ({"failures": (ProviderRequestRejected("HTTP 400"),)}, PROVIDER_REQUEST_REJECTED),
        (
            {"failures": (ProviderTransportError("t"), ProviderRequestRejected("r"))},
            PROVIDER_REQUEST_REJECTED,
        ),
        ({"portfolio_rule": "DIRECTION_INVERSION"}, INVALID_RESPONSE),
    ],
)
def test_classificacao_vem_so_de_campos_estruturados(
    overrides: dict[str, Any], cause: str
) -> None:
    assert classify(**overrides) == cause


# ── Preflight de capacidades ─────────────────────────────────────


GEMINI_MODEL = "gemini-model-under-test"


def gemini_params(**overrides: Any) -> dict[str, Any]:
    """Spec científica completa de ``llm_agent`` com Gemini."""
    return {
        "provider": "gemini",
        "model": GEMINI_MODEL,
        **H2_SC_PROVISIONAL_PARAMS,
        "thinking_level": "low",
        "max_output_tokens": 4096,
        **overrides,
    }


def mock_params(**overrides: Any) -> dict[str, Any]:
    return {"provider": "mock", **H2_SC_PROVISIONAL_PARAMS, **overrides}


def without(params: dict[str, Any], key: str) -> dict[str, Any]:
    return {name: value for name, value in params.items() if name != key}


GEMINI_REQUIRED = (*SCIENTIFIC_REQUIRED_PARAMS, "model", "max_output_tokens", "thinking_level")


@pytest.mark.parametrize("key", GEMINI_REQUIRED)
def test_preflight_cientifico_recusa_cada_parametro_material_ausente(key: str) -> None:
    with pytest.raises(ValueError, match=f"missing: .*{key}"):
        LLMParticipant.preflight(without(gemini_params(), key), scientific=True)


@pytest.mark.parametrize("key", SCIENTIFIC_REQUIRED_PARAMS)
def test_preflight_cientifico_com_mock_tambem_exige_o_nucleo(key: str) -> None:
    with pytest.raises(ValueError, match=f"missing: .*{key}"):
        LLMParticipant.preflight(without(mock_params(), key), scientific=True)


def test_mock_cientifico_completo_passa_sem_afirmacao_semantica() -> None:
    report = LLMParticipant.preflight(mock_params(), scientific=True)
    assert report.status == CAPABILITY_NOT_APPLICABLE
    assert report.declared == report.qualified == report.transported == ()


def test_preflight_separa_pedido_transportado_declarado_qualificado_e_metadado() -> None:
    report = LLMParticipant.preflight(gemini_params(), scientific=False)
    assert report.requested == (
        "analyst_id",
        "max_output_tokens",
        "seed",
        "temperature",
        "thinking_level",
    )
    expected = ("max_output_tokens", "temperature", "thinking_level")
    assert report.transported == report.declared == expected
    assert report.qualified == ()
    assert report.metadata_only == ("analyst_id", "seed")
    assert report.status == CAPABILITY_DECLARED_UNQUALIFIED


def test_fase_cientifica_exige_qualificacao_empirica_do_modelo() -> None:
    with pytest.raises(ValueError, match="DECLARED_UNQUALIFIED.*LIVE_SMOKE"):
        LLMParticipant.preflight(gemini_params(), scientific=True)


def test_qualificacao_e_por_modelo_nao_por_provedor(monkeypatch: pytest.MonkeyPatch) -> None:
    every = frozenset({"temperature", "thinking_level", "max_output_tokens"})
    monkeypatch.setattr(
        participant_module,
        "EMPIRICALLY_QUALIFIED",
        MappingProxyType({("gemini", GEMINI_MODEL): every}),
    )
    report = LLMParticipant.preflight(gemini_params(), scientific=True)
    assert report.status == CAPABILITY_QUALIFIED
    assert report.qualified == tuple(sorted(every))
    with pytest.raises(ValueError, match="DECLARED_UNQUALIFIED"):
        LLMParticipant.preflight(gemini_params(model="outro-modelo"), scientific=True)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (gemini_params(strict_inputs=False), "strict_inputs=True"),
        (gemini_params(provider="agent_router"), "does not declare option"),
        (gemini_params(thinking_level="minimal"), "thinking_level 'minimal' is not declared"),
        (gemini_params(provider="outro"), "unsupported llm provider"),
    ],
    ids=[
        "sem strict em fase cientifica",
        "openai-compat sem thinking nem max tokens",
        "nivel nao declarado",
        "provedor desconhecido",
    ],
)
def test_preflight_recusa_localmente(params: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        LLMParticipant.preflight(params, scientific=True)


def test_caminho_nao_cientifico_continua_aceitando_defaults() -> None:
    """Fora de fase científica nada novo é exigido: os caminhos legados seguem."""
    report = LLMParticipant.preflight({"provider": "mock"}, scientific=False)
    assert report.status == CAPABILITY_NOT_APPLICABLE
    LLMParticipant.preflight({"provider": "agent_router", "model": "m"}, scientific=False)


def test_construcao_recusa_provedor_que_nao_declara_a_opcao() -> None:
    with pytest.raises(ValueError, match="does not declare"):
        LLMParticipant(TICKER, provider="agent_router", model="m", thinking_level="low")
