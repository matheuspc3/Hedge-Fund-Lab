"""Provas do contrato causal e de falha do participante multiagente."""

import math
from types import MappingProxyType
from typing import Any, cast

import pandas as pd
import pytest

from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.participant import (
    LLMDecisionError,
    LLMParticipant,
    target_portfolio_to_intents,
)
from src.agents.state import FinalDecision, RiskVerdict, TechnicalSignal
from src.backtesting.agent_engine import _buy_order, _sell_order
from src.backtesting.arena import ExecutionEngine, MarketObservation, OrderIntent
from src.backtesting.costs import CostModel

TICKER = "PETR4"
CAPITAL = 1_000.0

APPROVED = {
    "verdict": "APROVADO",
    "analysis": "Aprovado no mock",
    "risk_metrics": {},
}


def signal(kind: str, confidence: float = 1.0) -> dict[str, Any]:
    return {"signal": kind, "justification": "mock", "confidence": confidence}


def buy(size: float) -> dict[str, Any]:
    return {"decision": "COMPRA", "position_size": size, "reasoning": "mock"}


def sell(size: float) -> dict[str, Any]:
    return {"decision": "VENDA", "position_size": size, "reasoning": "mock"}


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
    instância Pydantic por referência e ``portfolio_manager`` escreve em
    ``position_size`` ao aplicar o teto.
    """
    return MockLLMClient(
        {
            TechnicalSignal: signals,
            RiskVerdict: APPROVED,
            FinalDecision: decisions,
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
        "kelly_fraction": 1.0,
        "max_position_size": 1.0,
        "portfolio_max_concentration": 1.0,
    }
    params.update(overrides)
    return LLMParticipant(TICKER, llm_client=client, **params)


def two_buys_participant() -> tuple[LLMParticipant, MockLLMClient]:
    """Roteiro comum sobre ``WARMUP_CLOSES``.

    Três sessões de aquecimento em ``MANTER``, alvos de 0,5 e 0,6 nas duas
    compras e, na última sessão, uma saída integral para caixa — que existe
    como decisão mas não tem abertura seguinte onde executar.
    """
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("COMPRA")] * 2 + [signal("VENDA")],
        [buy(0.5), buy(0.2), sell(1.0)],
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
    assert (first.type, first.quantity) == ("BUY", 50)


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
    abertura seguinte. O peso alvo emitido é o mesmo nos dois; com a abertura
    estável chegar a 0,6 exige comprar, e com o gap de alta exige vender.
    """
    calm = frame(WARMUP_OPENS, WARMUP_CLOSES)
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
    assert calm_targets[3] == pytest.approx(0.5)
    assert calm_targets[4] == pytest.approx(0.6)

    assert [(trade.type, trade.quantity) for trade in calm_trades[1:]] == [("BUY", 10)]
    assert [(trade.type, trade.quantity) for trade in gap_trades[1:]] == [("SELL", 5)]


def test_participante_nao_altera_caixa_posicao_nem_produz_trade() -> None:
    """``decide`` termina em peso alvo: nada de quantidade, custo ou caixa."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant, _ = two_buys_participant()
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))

    intents = participant.decide(observation(data.iloc[:4]))

    assert all(isinstance(intent, OrderIntent) for intent in intents)
    assert [(intent.ticker, intent.target_weight) for intent in intents] == [
        (TICKER, pytest.approx(0.5))
    ]
    assert intents[0].decision_time == data.index[3]
    assert not hasattr(participant, "cash")
    assert not hasattr(participant, "positions")


# ── Tradução de decisão em peso alvo ─────────────────────────────


def test_compra_traduz_fracao_de_caixa_em_peso_de_carteira() -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    participant, _ = two_buys_participant()
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))

    # 40 ações a 10 valem 400 de um patrimônio de 1000; comprar metade dos 600
    # de caixa mira 700/1000.
    intents = participant.decide(
        observation(
            data.iloc[:4],
            positions=MappingProxyType({TICKER: 40}),
            cash=600.0,
            equity=1_000.0,
        )
    )

    assert intents[0].target_weight == pytest.approx(0.7)


def test_venda_traduz_fracao_de_posicao_em_peso_de_carteira() -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client(
        [signal("MANTER")] * 3 + [signal("VENDA")], [sell(0.25)]
    )
    participant = scripted_participant(client)
    for index in range(1, 4):
        participant.decide(observation(data.iloc[:index]))

    # Vender um quarto de 800 em ações deixa 600 investidos de 1000.
    intents = participant.decide(
        observation(
            data.iloc[:4],
            positions=MappingProxyType({TICKER: 80}),
            cash=200.0,
            equity=1_000.0,
        )
    )

    assert intents[0].target_weight == pytest.approx(0.6)


def test_manter_nao_emite_intencao() -> None:
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client([signal("MANTER")] * 4, [])
    participant = scripted_participant(client)

    assert participant.decide(observation(data.iloc[:4])) == []
    assert participant.decisions[-1].target_weight is None


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


def test_peso_traduzido_permanece_no_intervalo_fechado() -> None:
    """A tradução não pode produzir alavancagem nem peso negativo."""
    data = frame(WARMUP_OPENS, WARMUP_CLOSES)
    client = scripted_client([signal("MANTER")] * 3 + [signal("COMPRA")], [buy(1.0)])
    participant = scripted_participant(client)
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


# ── Paridade com o dimensionamento do motor legado ───────────────

ZERO_COST = CostModel()


class ParitySpy:
    """Observa caixa, posição e fechamento no instante da decisão."""

    def __init__(self, participant: LLMParticipant) -> None:
        self.participant = participant
        self.states: list[tuple[pd.Timestamp, float, int, float]] = []

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        self.states.append(
            (
                observation.session,
                observation.cash,
                observation.positions[TICKER],
                float(observation.history[TICKER]["fechamento"].iloc[-1]),
            )
        )
        return self.participant.decide(observation)


def run_parity(
    closes: list[float], signals: list[dict], decisions: list[dict]
) -> tuple[ParitySpy, LLMParticipant, list]:
    """Executa sem custos e sem gap: ``abertura == fechamento`` em toda sessão."""
    data = frame(list(closes), list(closes))
    participant = scripted_participant(scripted_client(signals, decisions))
    spy = ParitySpy(participant)
    result = ExecutionEngine(spy, {TICKER: data}, CAPITAL, ZERO_COST).run()
    return spy, participant, result.trades


def test_compra_tem_paridade_de_quantidade_com_o_motor_legado() -> None:
    """Mesmo cenário, mesma quantidade: a tradução não muda o dimensionamento.

    Sem gap (``open(t+1) == close(t)``) e sem custos, o peso alvo traduzido
    reproduz exatamente ``floor(caixa * size / preço)`` — a fórmula que
    ``_buy_order`` aplica no motor legado.

    São duas compras de propósito. Na primeira a posição é zero e caixa iguala
    patrimônio, o que tornaria a prova cega a confundir um com o outro. Na
    segunda já existe posição, então ``caixa != patrimônio`` e a fórmula fica
    de fato presa.
    """
    # 10,37 não divide o caixa em quantidade inteira: o ``floor`` é exercido.
    closes = [9.0, 11.0, 10.37, 10.37, 10.37, 10.37]
    spy, participant, trades = run_parity(
        closes, [signal("MANTER")] * 3 + [signal("COMPRA")] * 2, [buy(0.4), buy(0.4)]
    )

    executed_quantities = []
    for index, trade in zip((3, 4), trades, strict=True):
        _, cash, position, close = spy.states[index]
        decision = participant.decisions[index].final_decision
        assert decision is not None and decision.decision == "COMPRA"

        _, legacy_quantity, legacy_trade = _buy_order(
            cash, close, decision.position_size, ZERO_COST
        )
        assert legacy_trade is not None
        assert trade.price == close  # sem gap
        assert trade.type == "BUY"
        assert trade.quantity == legacy_quantity
        executed_quantities.append((cash, position, legacy_quantity))

    (first_cash, first_position, first_quantity) = executed_quantities[0]
    (second_cash, second_position, second_quantity) = executed_quantities[1]

    # Premissa da primeira compra: sem posição, caixa == patrimônio.
    assert first_position == 0
    assert first_cash == CAPITAL
    assert first_quantity == 38  # floor(1000 * 0.4 / 10.37) = floor(38.57)

    # Premissa da segunda: já há posição, então caixa != patrimônio e a compra
    # não pode ser explicada por uma fração do patrimônio.
    assert second_position == first_quantity
    assert second_cash < CAPITAL
    assert second_quantity == 23  # floor(605.94 * 0.4 / 10.37) = floor(23.37)


def test_venda_tem_paridade_de_quantidade_com_o_motor_legado() -> None:
    """Venda com ``posição * size`` inteiro reproduz ``floor(q * size)``.

    O participante nunca arredonda quantidade: quem trunca é o executor, e ele
    trunca a *posição alvo*, não a quantidade negociada. Quando ``q * size`` é
    inteiro as duas contas coincidem exatamente.
    """
    closes = [9.0, 11.0, 10.0, 10.0, 10.0, 10.0]
    spy, participant, trades = run_parity(
        closes,
        [signal("MANTER")] * 3 + [signal("COMPRA")] + [signal("VENDA")],
        [buy(1.0), sell(0.25)],
    )

    _, cash, position, close = spy.states[4]
    decision = participant.decisions[4].final_decision
    assert decision is not None and decision.decision == "VENDA"
    assert position * decision.position_size == int(position * decision.position_size)

    _, remaining, legacy_trade = _sell_order(
        cash, position, close, decision.position_size, ZERO_COST
    )
    assert legacy_trade is not None
    assert position - remaining == legacy_trade.quantity

    executed = trades[-1]
    assert executed.price == close  # sem gap
    assert executed.type == "SELL"
    assert executed.quantity == legacy_trade.quantity


def test_venda_com_fracao_nao_inteira_diverge_em_uma_acao_por_arredondamento() -> None:
    """Divergência conhecida e declarada, de arredondamento — não de sizing.

    O motor legado trunca a *quantidade vendida*; a arena trunca a *posição
    alvo* que sobra. Quando ``q * size`` não é inteiro, as duas políticas
    diferem em uma ação. Corrigir isso seria mudar a política de lote da arena,
    que continua ``TBD``, e não cabe ao participante.
    """
    closes = [9.0, 11.0, 10.0, 10.0, 10.0, 10.0]
    spy, participant, trades = run_parity(
        closes,
        [signal("MANTER")] * 3 + [signal("COMPRA")] + [signal("VENDA")],
        [buy(1.0), sell(0.333)],
    )

    _, cash, position, close = spy.states[4]
    decision = participant.decisions[4].final_decision
    assert decision is not None
    assert position * decision.position_size != int(position * decision.position_size)

    _, remaining, legacy_trade = _sell_order(
        cash, position, close, decision.position_size, ZERO_COST
    )
    assert legacy_trade is not None

    executed = trades[-1]
    assert executed.type == "SELL"
    assert executed.quantity == legacy_trade.quantity + 1


def test_manter_nao_vira_rebalance_para_o_peso_corrente() -> None:
    """``MANTER`` é ausência de ordem, não alvo igual ao peso do fechamento.

    A compra decidida em ``close(t3)`` executa em ``open(t4)`` e deixa metade
    do patrimônio no ativo. Em ``close(t4)`` o agente diz ``MANTER`` e a
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
        [buy(0.5)],
    )
    participant = scripted_participant(client)

    result = ExecutionEngine(participant, {TICKER: data}, CAPITAL).run()

    manter = participant.decisions[4]
    assert manter.target_weight is None
    assert manter.final_decision is not None
    assert manter.final_decision.decision == "MANTER"
    # Premissa: em close(t4) a posição valia exatamente metade do patrimônio,
    # e o gap de t5 desfaz essa proporção na abertura.
    assert [(trade.type, trade.date, trade.quantity) for trade in result.trades] == [
        ("BUY", data.index[4], 50)
    ]
