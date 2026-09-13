"""Provas do contrato causal e de falha do participante multiagente."""

import math
from types import MappingProxyType
from typing import Any, cast

import pandas as pd
import pytest

from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.participant import (
    DEFAULT_LONG_TARGET_WEIGHT,
    FixedTargetSizing,
    LLMDecisionError,
    LLMParticipant,
    target_portfolio_to_intents,
)
from src.agents.state import PortfolioAction, RiskVerdict, TechnicalSignal
from src.backtesting.arena import ExecutionEngine, MarketObservation, OrderIntent

TICKER = "PETR4"
CAPITAL = 1_000.0

#: Alvo usado pelos cenários deste módulo. Metade do patrimônio dá números
#: inteiros nos preços do recorte e não é, nem pretende ser, valor científico.
TARGET = 0.5

APPROVED = {
    "verdict": "APROVADO",
    "analysis": "Aprovado no mock",
    "risk_metrics": {},
}


def signal(kind: str, confidence: float = 1.0) -> dict[str, Any]:
    return {"signal": kind, "justification": "mock", "confidence": confidence}


def action(kind: str) -> dict[str, Any]:
    """Resposta qualitativa do gestor de portfólio: direção, sem quantidade."""
    return {"decision": kind, "reasoning": "mock"}


def frame(opens: list[float], closes: list[float]) -> pd.DataFrame:
    """Barras mínimas do contrato da arena, indexadas por pregão."""
    sessions = pd.bdate_range("2023-01-02", periods=len(closes))
    return pd.DataFrame({"abertura": opens, "fechamento": closes}, index=sessions)


# Recorte de seis pregões: três de aquecimento (``MANTER``), duas decisões de
# compra e uma última sessão cuja decisão nunca chega a ser executada.
WARMUP_CLOSES = [9.0, 11.0, 10.0, 10.0, 10.0, 10.0]
WARMUP_OPENS = [9.0, 11.0, 10.0, 10.0, 10.0, 10.0]


def scripted_client(
    signals: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> MockLLMClient:
    """Mock determinístico: um analista por sessão e decisões roteirizadas.

    As respostas são ``dict`` de propósito — ``MockLLMClient`` devolveria uma
    instância Pydantic compartilhada por referência entre sessões.
    """
    return MockLLMClient(
        {
            TechnicalSignal: signals,
            RiskVerdict: APPROVED,
            PortfolioAction: decisions,
        }
    )


def scripted_participant(
    client: LLMClient,
    **overrides: Any,
) -> LLMParticipant:
    """Participante com um analista e limites de risco abertos.

    Os limites são afrouxados para que o teste exerça o contrato temporal e a
    tradução de peso, não os guard-rails determinísticos — que já têm provas
    próprias em ``tests/agents/test_agents.py``.
    """
    params: dict[str, Any] = {
        "analyst_count": 1,
        "consensus_threshold": 1.0,
        "risk_max_volatility": 100.0,
        "risk_max_drawdown": 1.0,
        "risk_max_concentration": 1.0,
        "long_target_weight": TARGET,
    }
    params.update(overrides)
    return LLMParticipant(TICKER, llm_client=client, **params)


def two_buys_participant() -> tuple[LLMParticipant, MockLLMClient]:
    """Roteiro comum sobre ``WARMUP_CLOSES``.

    Três sessões de aquecimento em ``MANTER``, duas compras — ambas no mesmo
    alvo determinístico, porque o alvo não depende da sessão — e, na última,
    uma saída para caixa, que existe como decisão mas não tem abertura seguinte
    onde executar.
    """
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")] * 2 + [signal("VENDA")],
        [action("COMPRA"), action("COMPRA"), action("VENDA")],
    )
    return scripted_participant(client), client


def observation(data: pd.DataFrame, **overrides: Any) -> MarketObservation:
    fields: dict[str, Any] = {
        "session": cast(pd.Timestamp, data.index[-1]),
        "history": MappingProxyType({TICKER: data.copy()}),
        "positions": MappingProxyType({TICKER: 0}),
        "cash": CAPITAL,
        "equity": CAPITAL,
    }
    fields.update(overrides)
    return MarketObservation(**fields)


# ── Causalidade ──────────────────────────────────────────────────


def test_agente_recebe_a_mesma_informacao_com_e_sem_futuro() -> None:
    """``t`` é indistinguível entre o recorte que termina nele e outro maior.

    ``A`` acaba em ``t``; ``B`` repete ``A`` e ainda tem futuro. Se qualquer
    campo entregue ao agente denunciasse o horizonte — número de sessões,
    próxima barra, fim da amostra — os prompts divergiriam no prefixo comum.
    """
    short = frame(WARMUP_OPENS[:5], WARMUP_CLOSES[:5])
    extended = frame([*WARMUP_OPENS, 10.0, 10.0], [*WARMUP_CLOSES, 12.0, 13.0])

    short_participant, short_client = two_buys_participant()
    ExecutionEngine(short_participant, {TICKER: short}, CAPITAL).run()
    long_participant, long_client = two_buys_participant()
    ExecutionEngine(long_participant, {TICKER: extended}, CAPITAL).run()

    assert len(short_client.calls) < len(long_client.calls)
    # Prova principal: o *input* do agente em cada sessão do prefixo é igual.
    assert short_client.calls == long_client.calls[: len(short_client.calls)]

    short_targets = [record.target_weight for record in short_participant.decisions]
    long_targets = [record.target_weight for record in long_participant.decisions]
    assert short_targets == long_targets[: len(short_targets)]
    assert short_targets[-1] is not None, "a última sessão de A ainda decide"


def test_participante_nao_recebe_dataset_nem_snapshot() -> None:
    """O participante só toca ``MarketObservation``; nada mais é passado."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    observed: list[set[str]] = []
    participant, _ = two_buys_participant()
    original = participant.decide

    def spy(obs: MarketObservation) -> list[OrderIntent]:
        observed.append(set(obs.history))
        # O histórico entregue termina exatamente na sessão observada.
        assert obs.history[TICKER].index[-1] == obs.session
        assert len(obs.history[TICKER]) == len(data.loc[: obs.session])
        return original(obs)

    participant.decide = spy  # type: ignore[method-assign]
    ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()

    assert observed == [{TICKER}] * len(data)


# ── Relógio: close(t) -> open(t+1) ───────────────────────────────


def test_decisao_no_fechamento_executa_na_abertura_seguinte() -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant, _ = two_buys_participant()

    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()

    decided = [
        record.session
        for record in participant.decisions
        if record.target_weight is not None
    ]
    assert decided == [data.index[3], data.index[4], data.index[5]]
    # A primeira decisão nasce no fechamento do 4º pregão e só vira trade na
    # abertura do 5º, ao preço de abertura daquela sessão.
    first = result.trades[0]
    assert first.date == data.index[4]
    assert first.price == data.loc[data.index[4], "abertura"]
    assert (first.type, first.quantity) == ("BUY", 50)  # 50% de 1000 a 10,00


def test_decisao_da_ultima_sessao_existe_e_so_executa_com_proxima_abertura() -> None:
    """A última decisão é real, mas morre sem abertura observada em ``t+1``.

    O mesmo roteiro corre em dois recortes que só diferem por uma sessão a
    mais no fim. A decisão de zerar a posição nasce nos dois; ela só vira
    ``SELL`` no recorte que tem a abertura seguinte.
    """
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    extended = frame([*WARMUP_OPENS, 10.0], [*WARMUP_CLOSES, 10.0])

    participant, _ = two_buys_participant()
    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()
    longer_participant, _ = two_buys_participant()
    longer = ExecutionEngine(longer_participant, {TICKER: extended}, CAPITAL).run()

    last = participant.decisions[-1]
    assert last.session == data.index[-1]
    assert last.target_weight == 0.0, "a última barra ainda produz decisão"

    assert len(longer.trades) == len(result.trades) + 1
    executed = longer.trades[-1]
    assert executed.date == extended.index[-1]
    assert executed.type == "SELL"


def test_gap_overnight_inverte_a_operacao_sem_mudar_a_decisao() -> None:
    """O participante declara estado desejado; a direção nasce na abertura.

    Os dois recortes são idênticos até ``close(t)`` e diferem apenas na
    abertura seguinte. O mesmo ``COMPRA`` produz o mesmo peso alvo nos dois — e
    é justamente por isso que a direção física diverge: com a abertura em baixa
    a exposição corrente fica abaixo de 50% e chegar ao alvo exige **comprar**;
    com o gap de alta ela ultrapassa 50% e o mesmo alvo exige **vender**.

    Esta é a consequência declarada da semântica de alvo: ``COMPRA`` significa
    "desejo estar exposto no peso configurado", não "emita uma ordem de compra".
    """
    calm = frame([*WARMUP_OPENS[:5], 8.0], WARMUP_CLOSES)
    gapped = frame([*WARMUP_OPENS[:5], 20.0], WARMUP_CLOSES)

    outcomes = []
    for data in (calm, gapped):
        participant, _ = two_buys_participant()
        result = ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()
        outcomes.append(
            (
                [record.target_weight for record in participant.decisions],
                result.trades,
            )
        )

    calm_targets, calm_trades = outcomes[0]
    gap_targets, gap_trades = outcomes[1]

    # Comparação até a decisão sob teste: a partir da sessão do gap as
    # carteiras divergem legitimamente, porque a execução foi diferente.
    assert calm_targets[:5] == gap_targets[:5]
    assert calm_targets[3] == pytest.approx(TARGET)
    assert calm_targets[4] == pytest.approx(TARGET)

    # Premissa: as duas primeiras decisões são o mesmo ``COMPRA``, e a primeira
    # execução é idêntica nos dois recortes (mesma abertura em t4).
    assert calm_trades[0].quantity == gap_trades[0].quantity == 50
    assert [(trade.type, trade.quantity) for trade in calm_trades[1:]] == [("BUY", 6)]
    assert [(trade.type, trade.quantity) for trade in gap_trades[1:]] == [("SELL", 13)]


def test_participante_nao_altera_caixa_posicao_nem_produz_trade() -> None:
    """``decide`` termina em peso alvo: nada de quantidade, custo ou caixa."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant, _ = two_buys_participant()
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))

    intents = participant.decide(observation(data.iloc[:4]))

    assert all(isinstance(intent, OrderIntent) for intent in intents)
    assert [(intent.ticker, intent.target_weight) for intent in intents] == [
        (TICKER, pytest.approx(TARGET))
    ]
    assert intents[0].decision_time == data.index[3]
    assert not hasattr(participant, "cash")
    assert not hasattr(participant, "positions")


# ── Sizing determinístico: decisão qualitativa -> peso alvo ──────


def decided(participant: LLMParticipant) -> float | None:
    return participant.decisions[-1].target_weight


def warm_up(participant: LLMParticipant, data: pd.DataFrame) -> None:
    """Três sessões de aquecimento para o risco ter volatilidade e drawdown."""
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))


@pytest.mark.parametrize("confidence", [0.55, 0.95])
def test_confidence_nao_altera_o_tamanho_da_posicao(confidence: float) -> None:
    """Prova central desta metodologia: o alvo é invariante à confiança.

    Os dois cenários são idênticos exceto pela ``confidence`` reportada pelo
    analista, e a cadeia qualitativa produz ``COMPRA`` nos dois. Se a confiança
    entrasse em qualquer fórmula de dimensionamento — fractional Kelly ou um
    simples ``alvo * confidence`` — os pesos divergiriam aqui.

    ``confidence`` textual de um LLM não é ``P(win)``; ela continua sendo
    registrada e continua chegando aos agentes seguintes como contexto, mas não
    tem autoridade aritmética sobre exposição.
    """
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER", confidence=confidence)] * 3
        + [signal("COMPRA", confidence=confidence)],
        [action("COMPRA")],
    )
    participant = scripted_participant(client)
    warm_up(participant, data)

    intents = participant.decide(observation(data.iloc[:4]))

    recorded = participant.decisions[-1].technical_signal
    assert recorded is not None and recorded.confidence == pytest.approx(confidence)
    assert intents[0].target_weight == pytest.approx(TARGET)


def test_confianca_baixa_e_alta_produzem_exatamente_o_mesmo_alvo() -> None:
    """A mesma invariância comparada lado a lado, sem depender do parametrize."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    targets = []
    for confidence in (0.55, 0.95):
        client = scripted_client(
            [signal("MANTER", confidence=confidence)] * 3
            + [signal("COMPRA", confidence=confidence)],
            [action("COMPRA")],
        )
        participant = scripted_participant(client)
        warm_up(participant, data)
        participant.decide(observation(data.iloc[:4]))
        targets.append(decided(participant))

    assert targets[0] == targets[1] == pytest.approx(TARGET)


def test_compra_aprovada_vira_o_alvo_configurado_qualquer_que_seja_a_carteira() -> None:
    """O alvo é estado desejado, não função de caixa nem de posição corrente.

    Duas carteiras muito diferentes no mesmo pregão — sem posição e com 80% do
    patrimônio investido — recebem o mesmo alvo. A antiga tradução, que
    convertia "fração do caixa" em peso, devolveria números distintos.
    """
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    carteiras = [
        {"positions": MappingProxyType({TICKER: 0}), "cash": 1_000.0},
        {"positions": MappingProxyType({TICKER: 80}), "cash": 200.0},
    ]

    targets = []
    for carteira in carteiras:
        client = scripted_client(
            [signal("MANTER")] * 3 + [signal("COMPRA")], [action("COMPRA")]
        )
        participant = scripted_participant(client)
        warm_up(participant, data)
        intents = participant.decide(
            observation(data.iloc[:4], equity=1_000.0, **carteira)
        )
        targets.append(intents[0].target_weight)

    assert targets == [pytest.approx(TARGET), pytest.approx(TARGET)]


def test_venda_aprovada_vira_alvo_zero_e_nao_reducao_parcial() -> None:
    """``VENDA`` é sair da exposição, não reduzir uma fração dela."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("VENDA")], [action("VENDA")]
    )
    participant = scripted_participant(client)
    warm_up(participant, data)

    intents = participant.decide(
        observation(
            data.iloc[:4],
            positions=MappingProxyType({TICKER: 80}),
            cash=200.0,
            equity=1_000.0,
        )
    )

    assert intents[0].target_weight == 0.0


def test_manter_nao_emite_intencao() -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client([signal("MANTER")] * 4, [])
    participant = scripted_participant(client)

    assert participant.decide(observation(data.iloc[:4])) == []
    assert decided(participant) is None


def test_portfolio_manter_apos_sinal_de_compra_nao_emite_intencao() -> None:
    """O gestor pode recusar seguir o analista; recusar não é dimensionar."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")], [action("MANTER")]
    )
    participant = scripted_participant(client)
    warm_up(participant, data)

    assert participant.decide(observation(data.iloc[:4])) == []
    record = participant.decisions[-1]
    assert record.portfolio_action is not None
    assert record.portfolio_action.decision == "MANTER"
    assert record.target_weight is None


def test_veto_de_risco_nao_emite_intencao_e_nem_consulta_o_sizing() -> None:
    """Vetado é vetado: não existe alvo, nem alvo reduzido."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")], [action("COMPRA")]
    )
    # Concentração mínima possível: qualquer posição já viola o limite duro.
    participant = scripted_participant(
        client, risk_max_concentration=0.001, long_target_weight=0.001
    )
    warm_up(participant, data)

    intents = participant.decide(
        observation(
            data.iloc[:4],
            positions=MappingProxyType({TICKER: 80}),
            cash=200.0,
            equity=1_000.0,
        )
    )

    record = participant.decisions[-1]
    assert intents == []
    assert record.risk_verdict is not None and record.risk_verdict.verdict == "VETADO"
    # O grafo termina no risco: o gestor de portfólio nem chega a ser chamado.
    assert record.portfolio_action is None
    assert record.target_weight is None


def test_portfolio_nao_pode_inverter_o_sinal_tecnico_aprovado() -> None:
    """``COMPRA`` aprovada admite seguir ou manter; nunca virar ``VENDA``."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")], [action("VENDA")]
    )
    participant = scripted_participant(client)
    warm_up(participant, data)

    assert participant.decide(observation(data.iloc[:4])) == []
    record = participant.decisions[-1]
    assert record.portfolio_action is not None
    assert record.portfolio_action.decision == "MANTER"
    assert any("inverteu o sinal" in error for error in record.errors)


def test_schema_qualitativo_nao_tem_campo_de_tamanho() -> None:
    """A autoridade de sizing não é ignorada — ela não é concedida.

    Pedir ``position_size`` ao LLM para depois sobrescrevê-lo deixaria o campo
    no prompt, no schema enviado e no trace. Aqui ele não existe: o modelo não
    tem onde escrever um tamanho, e ``extra="forbid"`` recusa inventá-lo.
    """
    assert set(PortfolioAction.model_fields) == {"decision", "reasoning"}
    with pytest.raises(ValueError):
        PortfolioAction.model_validate(
            {"decision": "COMPRA", "reasoning": "x", "position_size": 0.99}
        )


def test_kelly_nao_e_chamado_no_caminho_cientifico(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kelly saiu do caminho científico de fato, não apenas de nome."""
    import src.agents.portfolio_manager as portfolio_manager

    def explode(*args: Any, **kwargs: Any) -> float:
        raise AssertionError("o caminho científico não pode chamar Kelly")

    monkeypatch.setattr(portfolio_manager, "calculate_kelly_size", explode)

    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")], [action("COMPRA")]
    )
    participant = scripted_participant(client)
    warm_up(participant, data)

    intents = participant.decide(observation(data.iloc[:4]))

    assert intents[0].target_weight == pytest.approx(TARGET)


# ── Política de sizing e sua configuração ────────────────────────


@pytest.mark.parametrize(
    ("decision", "expected"),
    [("COMPRA", 0.25), ("VENDA", 0.0), ("MANTER", None)],
)
def test_politica_de_alvo_fixo_traduz_direcao_em_estado_desejado(
    decision: str, expected: float | None
) -> None:
    assert FixedTargetSizing(0.25).target_weight(decision) == expected


def test_default_tecnico_do_alvo_e_declarado_como_tecnico() -> None:
    """0,25 existe para manter a API conveniente, não por aprovação científica.

    O valor científico definitivo continua ``TBD`` no protocolo experimental; o
    que este teste prende é apenas que o default não mudou sem querer.
    """
    assert DEFAULT_LONG_TARGET_WEIGHT == 0.25
    assert LLMParticipant(TICKER, llm_client=MockLLMClient()).long_target_weight == 0.25


@pytest.mark.parametrize(
    ("weight", "message"),
    [
        (0.0, "must be > 0"),
        (-0.1, "must be > 0"),
        (1.5, "must be > 0"),
        (float("nan"), "must be finite"),
        (float("inf"), "must be finite"),
        (True, "must be a number"),
        ("0.2", "must be a number"),
    ],
    ids=["zero", "negativo", "acima_de_um", "nan", "inf", "booleano", "texto"],
)
def test_alvo_invalido_e_rejeitado_na_construcao(weight: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        LLMParticipant(TICKER, long_target_weight=weight, llm_client=MockLLMClient())


def test_alvo_acima_do_limite_duro_de_concentracao_e_rejeitado() -> None:
    """Sizing que manda construir o que o risco existe para vetar é contradição."""
    with pytest.raises(ValueError, match="exceeds risk_max_concentration"):
        LLMParticipant(
            TICKER,
            long_target_weight=0.40,
            risk_max_concentration=0.30,
            llm_client=MockLLMClient(),
        )


def test_alvo_igual_ao_limite_duro_de_concentracao_e_aceito() -> None:
    participant = LLMParticipant(
        TICKER,
        long_target_weight=0.30,
        risk_max_concentration=0.30,
        llm_client=MockLLMClient(),
    )

    assert participant.long_target_weight == pytest.approx(0.30)


@pytest.mark.parametrize("name", ["kelly_fraction", "max_position_size", "payoff_ratio"])
def test_parametros_mortos_de_kelly_nao_existem_mais_na_api_cientifica(
    name: str,
) -> None:
    """Parâmetro que não afeta comportamento não pode entrar no ``spec_hash``."""
    overrides: dict[str, Any] = {name: 0.5}
    with pytest.raises(TypeError):
        LLMParticipant(TICKER, llm_client=MockLLMClient(), **overrides)


# ── Falha do LLM não vira HOLD ───────────────────────────────────


class BrokenClient(LLMClient):
    """Cliente que sempre falha do jeito pedido, sem rede."""

    def __init__(self, error: BaseException) -> None:
        super().__init__()
        self.error = error

    async def generate(self, *args: Any, **kwargs: Any) -> Any:
        raise self.error


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("provider timeout"),
        ConnectionError("HTTP 503: provider unavailable"),
        ValueError("resposta não é JSON válido: 'talvez compre'"),
        TypeError("resposta não segue TechnicalSignal"),
    ],
    ids=["timeout", "provider_error", "json_invalido", "schema_invalido"],
)
def test_falha_do_provedor_nao_vira_hold(error: BaseException) -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant = scripted_participant(BrokenClient(error), retry_attempts=1)

    with pytest.raises(LLMDecisionError, match="unrecovered LLM failure"):
        participant.decide(observation(data.iloc[:4]))

    # A falha fica na trilha, e nenhuma decisão de investimento foi fabricada.
    assert participant.decisions[-1].llm_failures
    assert participant.decisions[-1].target_weight is None


def test_resposta_fora_do_schema_falha_em_vez_de_manter() -> None:
    """Confidence acima de 1 é rejeitada pelo schema e derruba o run."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = MockLLMClient({TechnicalSignal: signal("COMPRA", confidence=4.2)})
    participant = scripted_participant(client)

    with pytest.raises(LLMDecisionError, match="unrecovered LLM failure"):
        participant.decide(observation(data.iloc[:4]))


def test_quorum_incompleto_por_falha_derruba_o_run() -> None:
    """Votos perdidos por falha são infraestrutura, não consenso de mercado."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant = scripted_participant(
        BrokenClient(ConnectionError("boom")),
        analyst_count=4,
        consensus_threshold=0.75,
        retry_attempts=1,
    )

    with pytest.raises(LLMDecisionError, match="unrecovered LLM failure"):
        participant.decide(observation(data.iloc[:4]))


def test_quorum_sem_supermaioria_continua_sendo_decisao() -> None:
    """Discordância entre votos válidos é regra de agregação, não falha."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = MockLLMClient(
        {
            TechnicalSignal: [
                signal("COMPRA"),
                signal("VENDA"),
                signal("COMPRA"),
                signal("VENDA"),
            ]
        }
    )
    participant = scripted_participant(
        client, analyst_count=4, consensus_threshold=0.75
    )

    assert participant.decide(observation(data.iloc[:4])) == []
    record = participant.decisions[-1]
    assert record.llm_failures == ()
    assert record.consensus is not None and not record.consensus.consensus_reached


# ── Carteira-alvo completa ───────────────────────────────────────


def portfolio_observation(*tickers: str) -> MarketObservation:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    return MarketObservation(
        session=cast(pd.Timestamp, data.index[-1]),
        history=MappingProxyType({ticker: data.copy() for ticker in tickers}),
        positions=MappingProxyType(dict.fromkeys(tickers, 0)),
        cash=CAPITAL,
        equity=CAPITAL,
    )


def test_carteira_completa_vira_intents_em_ordem_canonica() -> None:
    observed = portfolio_observation("PETR4", "VALE3", "WEGE3")

    intents = target_portfolio_to_intents(
        observed, {"WEGE3": 0.0, "PETR4": 0.4, "VALE3": 0.3}
    )

    assert [(intent.ticker, intent.target_weight) for intent in intents] == [
        ("PETR4", 0.4),
        ("VALE3", 0.3),
        ("WEGE3", 0.0),
    ]
    assert all(intent.decision_time == observed.session for intent in intents)


def test_ticker_omitido_e_decisao_invalida() -> None:
    """Omitir um ativo não significa manter, nem zerar, nem deixar inferir."""
    observed = portfolio_observation("PETR4", "VALE3", "WEGE3")

    with pytest.raises(LLMDecisionError, match="omits WEGE3"):
        target_portfolio_to_intents(observed, {"PETR4": 0.4, "VALE3": 0.3})


@pytest.mark.parametrize(
    ("weights", "message"),
    [
        ({"PETR4": 0.4, "VALE3": 0.3, "ITUB4": 0.1}, "unknown ticker"),
        ({"PETR4": float("nan"), "VALE3": 0.3}, "must be finite"),
        ({"PETR4": float("inf"), "VALE3": 0.3}, "must be finite"),
        ({"PETR4": -0.1, "VALE3": 0.3}, "between 0 and 1"),
        ({"PETR4": 1.4, "VALE3": 0.3}, "between 0 and 1"),
        ({"PETR4": 0.8, "VALE3": 0.8}, "sum to at most 1"),
    ],
    ids=["desconhecido", "nan", "inf", "negativo", "acima_de_um", "soma_maior_que_um"],
)
def test_carteira_invalida_falha_sem_normalizar(
    weights: dict[str, float], message: str
) -> None:
    observed = portfolio_observation("PETR4", "VALE3")

    with pytest.raises(LLMDecisionError, match=message):
        target_portfolio_to_intents(observed, weights)


def test_ticker_duplicado_e_decisao_invalida() -> None:
    observed = portfolio_observation("PETR4", "VALE3")

    with pytest.raises(LLMDecisionError, match="duplicate ticker"):
        target_portfolio_to_intents(
            observed, [("PETR4", 0.4), ("VALE3", 0.3), ("PETR4", 0.2)]
        )


def test_participante_single_asset_recusa_universo_multi_ativo() -> None:
    """Nada de laço por ticker: seria outra estratégia, não esta."""
    client, _ = two_buys_participant()

    with pytest.raises(LLMDecisionError, match="single-asset"):
        client.decide(portfolio_observation(TICKER, "VALE3"))


def test_alvo_maximo_de_carteira_inteira_continua_sendo_decisao_valida() -> None:
    """Alvo 100% é long sem alavancagem, e o contrato de carteira o aceita.

    O sizing determinístico não pode produzir peso fora de ``[0, 1]`` por
    construção — o alvo é validado na criação do participante —, então o que
    resta provar é a borda superior atravessando ``target_portfolio_to_intents``
    sem ser normalizada nem recusada.
    """
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")], [action("COMPRA")]
    )
    participant = scripted_participant(client, long_target_weight=1.0)
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))

    intents = participant.decide(observation(data.iloc[:4]))

    weight = intents[0].target_weight
    assert 0.0 <= weight <= 1.0 and math.isclose(weight, 1.0)


# ── Frequência de decisão ────────────────────────────────────────


def long_frame(sessions: int) -> pd.DataFrame:
    """Preços oscilantes, suficientes para sair do aquecimento do risco."""
    closes = [10.0 + (index % 4) * 0.5 for index in range(sessions)]
    return frame(list(closes), list(closes))


def test_frequencia_de_decisao_chama_o_provedor_so_nos_indices_multiplos() -> None:
    """``decision_frequency`` migra a opção do motor legado, sessão a sessão."""
    data = long_frame(10)
    client = MockLLMClient({TechnicalSignal: signal("MANTER")})
    participant = scripted_participant(client, decision_frequency=3)

    sessions: list[pd.Timestamp] = []

    class Recorder:
        # O nome do parâmetro segue o Protocol ``Participant``: a arena o
        # aceita estruturalmente, não por herança.
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            before = len(client.calls)
            intents = participant.decide(observation)
            if len(client.calls) > before:
                sessions.append(observation.session)
            return intents

    ExecutionEngine(Recorder(), {TICKER: data}, CAPITAL).run()

    eligible = [data.index[index] for index in (0, 3, 6, 9)]
    assert sessions == eligible
    # Um analista por sessão elegível: nenhuma chamada nas demais.
    assert len(client.calls) == 4
    assert [record.session for record in participant.decisions] == eligible


def test_sessao_nao_elegivel_nao_emite_intencao_nem_toca_o_provedor() -> None:
    data = long_frame(10)
    client = MockLLMClient({TechnicalSignal: signal("MANTER")})
    participant = scripted_participant(client, decision_frequency=3)

    emitted = [
        (index, bool(participant.decide(observation(data.iloc[: index + 1]))))
        for index in range(len(data))
    ]

    assert [index for index, _ in emitted if index % 3 != 0]
    assert not any(has_intent for index, has_intent in emitted if index % 3 != 0)
    assert len(client.calls) == 4


def test_contador_de_frequencia_reinicia_em_cada_execucao() -> None:
    """Dois runs recomeçam do índice zero; nada atravessa execuções."""
    data = long_frame(7)
    runs: list[list[pd.Timestamp]] = []
    for _ in range(2):
        client = MockLLMClient({TechnicalSignal: signal("MANTER")})
        participant = scripted_participant(client, decision_frequency=3)
        ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()
        runs.append([record.session for record in participant.decisions])

    expected = [data.index[index] for index in (0, 3, 6)]
    assert runs == [expected, expected]


def test_frequencia_nao_depende_do_tamanho_do_recorte() -> None:
    """O índice elegível é o mesmo com ou sem futuro adicional no dataset.

    No motor legado a última barra era sempre elegível (``is_last_day``), o que
    exige saber que o recorte acabou. A arena não entrega essa informação e o
    participante não a reconstrói: a elegibilidade depende só do índice já
    percorrido.
    """
    short = long_frame(7)
    extended = long_frame(11)

    runs: list[list[pd.Timestamp]] = []
    for data in (short, extended):
        client = MockLLMClient({TechnicalSignal: signal("MANTER")})
        participant = scripted_participant(client, decision_frequency=3)
        ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()
        runs.append([record.session for record in participant.decisions])

    assert runs[0] == [short.index[index] for index in (0, 3, 6)]
    assert runs[1] == [extended.index[index] for index in (0, 3, 6, 9)]
    # A sessão 6 encerra o recorte curto e é intermediária no longo: mesma
    # elegibilidade nos dois, sem exceção para a última barra.
    assert runs[0] == runs[1][: len(runs[0])]


def test_frequencia_invalida_e_rejeitada_na_construcao() -> None:
    with pytest.raises(ValueError, match="decision_frequency must be >= 1"):
        LLMParticipant(TICKER, decision_frequency=0, llm_client=MockLLMClient())


# ── Parâmetros inteiros ──────────────────────────────────────────

#: Parâmetros conceitualmente inteiros, com o mínimo que cada um aceita.
INTEGER_PARAMS = [
    ("decision_frequency", 1),
    ("volatility_window", 2),
    ("retry_attempts", 1),
    ("analyst_count", 1),
    ("seed_base", 0),
]


def participant_with(name: str, value: Any) -> LLMParticipant:
    """Constrói passando ``value`` no parâmetro ``name``, qualquer que seja o tipo.

    O ``dict[str, Any]`` é deliberado: o alvo do teste é justamente entregar um
    valor de tipo errado e exigir que a validação de runtime o recuse. Anotar
    mais estreito só esconderia o caso do próprio teste.
    """
    overrides: dict[str, Any] = {name: value}
    return LLMParticipant(TICKER, llm_client=MockLLMClient(), **overrides)


@pytest.mark.parametrize(("name", "minimum"), INTEGER_PARAMS)
def test_parametro_inteiro_aceita_inteiro_valido(name: str, minimum: int) -> None:
    assert participant_with(name, minimum + 2) is not None


@pytest.mark.parametrize(("name", "minimum"), INTEGER_PARAMS)
@pytest.mark.parametrize("offset", [-1, -2], ids=["abaixo_do_minimo", "bem_abaixo"])
def test_parametro_inteiro_rejeita_valor_abaixo_do_minimo(
    name: str, minimum: int, offset: int
) -> None:
    with pytest.raises(ValueError, match=f"{name} must be >= {minimum}"):
        participant_with(name, minimum + offset)


@pytest.mark.parametrize(("name", "minimum"), INTEGER_PARAMS)
def test_parametro_inteiro_rejeita_float_fracionario(name: str, minimum: int) -> None:
    """``2.5 < 2`` é falso: comparar com o mínimo não valida o tipo."""
    with pytest.raises(ValueError, match=f"{name} must be an integer"):
        participant_with(name, minimum + 0.5)


@pytest.mark.parametrize(("name", "minimum"), INTEGER_PARAMS)
def test_parametro_inteiro_rejeita_booleano(name: str, minimum: int) -> None:
    """``bool`` é subclasse de ``int`` e passaria valendo 1.

    Pydantic sozinho não fecha esta borda: no modo padrão ele **converte**
    ``True`` em ``1`` para um campo ``int``, de modo que ``analyst_count=True``
    viraria um quorum de um analista e entraria assim no ``spec_hash`` e no
    manifest.
    """
    del minimum
    with pytest.raises(ValueError, match=f"{name} must be an integer"):
        participant_with(name, True)


# ── O que deixou de valer, e por quê ─────────────────────────────

# Existiam aqui três provas de paridade de quantidade com o
# ``AgentBacktestEngine``: sem gap e sem custos, a tradução
# ``position_size -> target_weight`` reproduzia ``floor(caixa * size / preço)``
# do motor legado.
#
# Elas foram removidas porque o comportamento que elas prendiam foi
# **deliberadamente abandonado** no caminho científico. O participante não
# traduz mais fração de operação em peso: ele declara um alvo determinístico.
# Manter aquelas provas exigiria manter ``position_size`` vivo só para
# satisfazê-las, que é exatamente a compatibilidade falsa que esta mudança
# elimina. O motor legado segue com seu próprio dimensionamento e seus próprios
# testes (``tests/backtesting/test_agent_engine.py``,
# ``tests/agents/test_agents.py::test_portfolio_legado_*``).


def test_manter_nao_vira_rebalance_para_o_peso_corrente() -> None:
    """``MANTER`` é ausência de ordem, não alvo igual ao peso do fechamento.

    A compra decidida em ``close(t3)`` executa em ``open(t4)`` e deixa metade
    do patrimônio no ativo, que é o alvo determinístico deste cenário. Em ``close(t4)`` o agente diz ``MANTER`` e a
    abertura de ``t5`` traz um gap de alta. Se ``MANTER`` reemitisse o peso
    observado (0,5), o executor recalcularia a quantidade alvo sobre o
    patrimônio inflado da abertura e precisaria **vender** para voltar a 0,5 —
    um rebalance disfarçado de "não fazer nada". A ausência de segundo trade é
    a prova de que isso não acontece.
    """
    data = frame(
        [9.0, 11.0, 10.0, 10.0, 10.0, 25.0],
        [9.0, 11.0, 10.0, 10.0, 10.0, 10.0],
    )
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")] + [signal("MANTER")] * 2,
        [action("COMPRA")],
    )
    participant = scripted_participant(client)

    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()

    manter = participant.decisions[4]
    assert manter.target_weight is None
    assert manter.portfolio_action is not None
    assert manter.portfolio_action.decision == "MANTER"
    # Premissa: em close(t4) a posição valia exatamente metade do patrimônio,
    # e o gap de t5 desfaz essa proporção na abertura.
    assert [(trade.type, trade.date, trade.quantity) for trade in result.trades] == [
        ("BUY", data.index[4], 50)
    ]
