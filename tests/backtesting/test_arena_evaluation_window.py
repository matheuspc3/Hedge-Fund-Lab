"""Provas da separação entre cobertura de dados e janela avaliada.

O invariante central desta suíte: sessões anteriores a ``decision_start``
existem como histórico causal e **nada mais** — não decidem, não negociam e não
entram na curva publicada. Mudar o tamanho do warm-up não pode mudar nenhum
número do experimento.
"""

import math
from typing import cast

import pandas as pd
import pytest

from src.backtesting.arena import (
    EvaluationWindowError,
    ExecutionEngine,
    MarketObservation,
    OrderIntent,
    common_sessions,
    resolve_evaluation_window,
)
from src.backtesting.costs import CostModel
from src.backtesting.metrics import performance_metrics, total_transaction_cost
from src.backtesting.portfolio import EqualWeightParticipant, MinVarianceParticipant
from src.strategies.bollinger_bands import BollingerParticipant
from src.strategies.buy_and_hold import BuyAndHoldParticipant
from src.strategies.sma_cross import SMACrossParticipant

TICKER = "PETR4"
CAPITAL = 10_000.0


#: Âncora fixa dos preços. O preço é função **da data**, nunca da posição
#: dentro do recorte: dois quadros que começam em datas diferentes precisam
#: concordar barra a barra nas datas que compartilham, senão um teste de
#: "warm-up maior não muda nada" compararia séries diferentes.
PRICE_EPOCH = pd.Timestamp("2022-12-01")


def frame(sessions: int, *, start: str = "2023-01-02") -> pd.DataFrame:
    """Série determinística e estritamente crescente, uma barra por sessão.

    Dias corridos, não pregões: esta suíte prova a semântica da janela sobre um
    calendário qualquer, e o calendário real é responsabilidade do snapshot.
    """
    index = pd.DatetimeIndex(pd.date_range(start=start, periods=sessions, freq="D"))
    closes = [100.0 + (stamp - PRICE_EPOCH).days for stamp in index]
    opens = [close - 2.0 for close in closes]
    return pd.DataFrame({"abertura": opens, "fechamento": closes}, index=index)


class Recorder:
    """Participante que registra cada observação e compra tudo quando pedido."""

    def __init__(self, *, buy: bool = True) -> None:
        self.sessions: list[pd.Timestamp] = []
        self.history_lengths: list[int] = []
        self.history_ends: list[pd.Timestamp] = []
        self.buy = buy

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        history = observation.history[TICKER]
        self.sessions.append(observation.session)
        self.history_lengths.append(len(history))
        self.history_ends.append(cast(pd.Timestamp, history.index[-1]))
        if not self.buy:
            return []
        return [
            OrderIntent(
                ticker=TICKER,
                target_weight=1.0,
                decision_time=observation.session,
            )
        ]


def engine(
    data: pd.DataFrame,
    *,
    decision_start: object = None,
    decision_end: object = None,
    minimum_history_sessions: int | None = None,
    participant: object = None,
) -> ExecutionEngine:
    return ExecutionEngine(
        cast("ExecutionEngine", participant or Recorder()),  # type: ignore[arg-type]
        {TICKER: data},
        CAPITAL,
        decision_start=decision_start,
        decision_end=decision_end,
        minimum_history_sessions=minimum_history_sessions,
    )


# ── Warm-up ──────────────────────────────────────────────────────


def test_warmup_nao_chama_o_participante() -> None:
    data = frame(10)
    recorder = Recorder()
    engine(
        data,
        decision_start="2023-01-08",
        decision_end="2023-01-09",
        participant=recorder,
    ).run()

    assert recorder.sessions == [
        pd.Timestamp("2023-01-08"),
        pd.Timestamp("2023-01-09"),
    ]


def test_warmup_nao_gera_intent_nem_trade() -> None:
    """Nenhum trade pode ter data anterior à primeira decisão avaliada."""
    data = frame(10)
    result = engine(data, decision_start="2023-01-08", decision_end="2023-01-09").run()

    assert result.trades, "a janela precisa produzir algum trade para o teste valer"
    assert all(
        pd.Timestamp(trade.date) >= pd.Timestamp("2023-01-08")
        for trade in result.trades
    )


def test_warmup_nao_entra_na_curva_publicada() -> None:
    data = frame(10)
    result = engine(data, decision_start="2023-01-08", decision_end="2023-01-09").run()

    # decision_start, decision_end e settlement — nada antes.
    assert list(result.equity_curve.index) == [
        pd.Timestamp("2023-01-08"),
        pd.Timestamp("2023-01-09"),
        pd.Timestamp("2023-01-10"),
    ]


def test_carteira_comeca_zerada_em_decision_start() -> None:
    """Warm-up não pode virar posição financeira em silêncio."""
    data = frame(10)
    result = engine(data, decision_start="2023-01-08", decision_end="2023-01-09").run()

    assert result.equity_curve.iloc[0] == pytest.approx(CAPITAL)


def test_warmup_maior_nao_altera_a_curva_avaliada() -> None:
    """Mesma janela + mesma informação usada = mesmos números.

    Os dois runs enxergam histórico diferente antes de ``decision_start``, mas
    o participante aqui não lê o histórico. O que se prova é que acrescentar
    dias anteriores não acrescenta pontos neutros à curva nem estica o período.
    """
    short = engine(
        frame(6, start="2023-01-05"),
        decision_start="2023-01-08",
        decision_end="2023-01-09",
    ).run()
    long = engine(
        frame(30, start="2022-12-20"),
        decision_start="2023-01-08",
        decision_end="2023-01-09",
    ).run()

    assert list(short.equity_curve.index) == list(long.equity_curve.index)
    pd.testing.assert_series_equal(short.equity_curve, long.equity_curve)
    assert short.final_equity == long.final_equity


# ── Histórico entregue na primeira decisão ───────────────────────


def test_primeira_decisao_enxerga_o_warmup_inteiro() -> None:
    """Expanding: a decisão em ``t`` vê todo o histórico causal até ``t``."""
    data = frame(10)
    recorder = Recorder(buy=False)
    engine(
        data,
        decision_start="2023-01-08",
        decision_end="2023-01-09",
        participant=recorder,
    ).run()

    # 2023-01-02 .. 2023-01-08 = 7 barras, terminando na própria decisão.
    assert recorder.history_lengths[0] == 7
    assert recorder.history_ends[0] == pd.Timestamp("2023-01-08")
    assert recorder.history_lengths[1] == 8
    assert recorder.history_ends[1] == pd.Timestamp("2023-01-09")


def test_historico_nunca_ultrapassa_a_sessao_decidida() -> None:
    data = frame(10)
    recorder = Recorder(buy=False)
    engine(
        data,
        decision_start="2023-01-04",
        decision_end="2023-01-09",
        participant=recorder,
    ).run()

    assert all(
        end == session
        for end, session in zip(recorder.history_ends, recorder.sessions, strict=True)
    )


# ── Calibration Anchor ───────────────────────────────────────────


def test_ancora_unica_decide_uma_vez_e_executa_em_t_mais_um() -> None:
    data = frame(10)
    recorder = Recorder()
    result = engine(
        data,
        decision_start="2023-01-08",
        decision_end="2023-01-08",
        participant=recorder,
    ).run()

    assert recorder.sessions == [pd.Timestamp("2023-01-08")]
    assert [pd.Timestamp(trade.date) for trade in result.trades] == [
        pd.Timestamp("2023-01-09")
    ]
    assert list(result.equity_curve.index) == [
        pd.Timestamp("2023-01-08"),
        pd.Timestamp("2023-01-09"),
    ]


def test_settlement_session_nao_decide() -> None:
    """A sessão de liquidação executa o pendente e não consulta ninguém."""
    data = frame(10)
    recorder = Recorder()
    engine(
        data,
        decision_start="2023-01-05",
        decision_end="2023-01-07",
        participant=recorder,
    ).run()

    assert recorder.sessions == [
        pd.Timestamp("2023-01-05"),
        pd.Timestamp("2023-01-06"),
        pd.Timestamp("2023-01-07"),
    ]
    assert pd.Timestamp("2023-01-08") not in recorder.sessions


def test_nenhuma_decisao_depois_de_decision_end() -> None:
    data = frame(20)
    recorder = Recorder()
    engine(
        data,
        decision_start="2023-01-04",
        decision_end="2023-01-09",
        participant=recorder,
    ).run()

    assert max(recorder.sessions) == pd.Timestamp("2023-01-09")


def test_sessoes_posteriores_ao_settlement_nao_entram_no_run() -> None:
    data = frame(20)
    result = engine(data, decision_start="2023-01-04", decision_end="2023-01-09").run()

    assert result.equity_curve.index[-1] == pd.Timestamp("2023-01-10")


# ── Gates ────────────────────────────────────────────────────────


def test_sem_settlement_falha_explicitamente() -> None:
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="no settlement session"):
        engine(data, decision_start="2023-01-10", decision_end="2023-01-11")


def test_decision_end_na_ultima_sessao_falha() -> None:
    """A última barra da cobertura não pode ser a última decisão avaliada."""
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="no settlement session"):
        engine(data, decision_start="2023-01-05", decision_end="2023-01-11")


def test_historico_insuficiente_falha_antes_de_executar() -> None:
    data = frame(10)
    recorder = Recorder()
    with pytest.raises(EvaluationWindowError, match="minimum_history_sessions"):
        engine(
            data,
            decision_start="2023-01-04",
            decision_end="2023-01-05",
            minimum_history_sessions=5,
            participant=recorder,
        )
    assert recorder.sessions == [], "o gate precisa falhar antes de qualquer decisão"


def test_historico_suficiente_passa_no_limite() -> None:
    """O gate conta o warm-up mais a própria barra de ``decision_start``."""
    data = frame(10)
    built = engine(
        data,
        decision_start="2023-01-04",
        decision_end="2023-01-05",
        minimum_history_sessions=3,
    )
    assert built.window.available_history_sessions == 3


def test_data_fora_do_calendario_nao_e_alinhada() -> None:
    data = frame(10).drop(pd.Timestamp("2023-01-05"))
    with pytest.raises(EvaluationWindowError, match="is not a session shared"):
        engine(data, decision_start="2023-01-05", decision_end="2023-01-08")


def test_start_depois_de_end_falha() -> None:
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="is after decision_end"):
        engine(data, decision_start="2023-01-08", decision_end="2023-01-05")


def test_janela_pela_metade_falha() -> None:
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="declared together"):
        engine(data, decision_start="2023-01-05")


def test_gate_de_warmup_exige_janela_declarada() -> None:
    """Exigir histórico mínimo sem janela seria um gate sem significado."""
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="requires an explicit"):
        engine(data, minimum_history_sessions=3)


# ── Modo técnico legado ──────────────────────────────────────────


def test_sem_janela_decide_toda_a_cobertura() -> None:
    """Sem janela declarada o motor se comporta exatamente como antes."""
    data = frame(5)
    recorder = Recorder()
    result = engine(data, participant=recorder).run()

    assert recorder.sessions == list(data.index)
    assert list(result.equity_curve.index) == list(data.index)
    assert not result.trades or max(
        pd.Timestamp(trade.date) for trade in result.trades
    ) <= cast(pd.Timestamp, data.index[-1])


def test_modo_legado_nao_reserva_settlement() -> None:
    window = resolve_evaluation_window(common_sessions({TICKER: frame(5)}))

    assert window.settlement_session is None
    assert window.explicit is False
    assert window.warmup_sessions == 0
    assert window.evaluated_sessions == 5


# ── Evidência realizada ──────────────────────────────────────────


def test_evidencia_da_janela_descreve_o_calendario_executado() -> None:
    window = resolve_evaluation_window(
        common_sessions({TICKER: frame(10)}),
        decision_start="2023-01-08",
        decision_end="2023-01-09",
    )

    assert window.to_dict() == {
        "data_start": "2023-01-02",
        "data_end": "2023-01-11",
        "first_decision_session": "2023-01-08",
        "last_decision_session": "2023-01-09",
        "settlement_session": "2023-01-10",
        "warmup_sessions": 6,
        "warmup_calendar_days": 6,
        "available_history_sessions": 7,
        "evaluated_sessions": 2,
    }


# ── Semântica canônica do warm-up, sem off-by-one ────────────────


def test_warmup_e_historico_disponivel_diferem_por_uma_sessao() -> None:
    """``available = warmup + 1``: a barra de ``decision_start`` também conta."""
    window = resolve_evaluation_window(
        common_sessions({TICKER: frame(10)}),
        decision_start="2023-01-06",
        decision_end="2023-01-08",
    )

    # 2023-01-02..2023-01-05 antes; 2023-01-02..2023-01-06 até a decisão.
    assert window.warmup_sessions == 4
    assert window.available_history_sessions == window.warmup_sessions + 1 == 5


def test_gate_passa_exatamente_no_minimo() -> None:
    """``available == minimum`` é suficiente — o limite é inclusivo."""
    data = frame(10)
    recorder = Recorder(buy=False)
    engine(
        data,
        decision_start="2023-01-06",
        decision_end="2023-01-08",
        minimum_history_sessions=5,
        participant=recorder,
    ).run()

    assert recorder.history_lengths[0] == 5


def test_gate_falha_por_uma_unica_sessao() -> None:
    """``available == minimum - 1`` falha: um a mais não é arredondado."""
    data = frame(10)
    with pytest.raises(EvaluationWindowError, match="only 5 session"):
        engine(
            data,
            decision_start="2023-01-06",
            decision_end="2023-01-08",
            minimum_history_sessions=6,
        )


def test_historico_minimo_de_uma_sessao_permite_decidir_na_primeira_barra() -> None:
    """Piso da spec: ``minimum=1`` aceita ``decision_start == data_start``."""
    built = engine(
        frame(10),
        decision_start="2023-01-02",
        decision_end="2023-01-03",
        minimum_history_sessions=1,
    )

    assert built.window.warmup_sessions == 0
    assert built.window.available_history_sessions == 1


def test_historico_disponivel_conta_sessao_comum_nao_barra_de_um_ticker() -> None:
    """A contagem do gate é do calendário comum, e é limite inferior por ticker.

    Um ticker que negocia numa data em que o outro não negocia entrega *mais*
    barras ao participante do que ``available_history_sessions``. A contagem
    comum é deliberada: é o único número igual para todos os tickers do run, e
    é sobre ele que a arena decide e executa.
    """
    completo = frame(10)
    # Mesmo quadro, sem duas sessões: a interseção encolhe, o outro ticker não.
    esburacado = completo.drop(
        [pd.Timestamp("2023-01-03"), pd.Timestamp("2023-01-05")]
    )

    observed: list[dict[str, int]] = []

    class Pair:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            observed.append(
                {
                    ticker: len(frame_)
                    for ticker, frame_ in observation.history.items()
                }
            )
            return []

    built = ExecutionEngine(
        cast("ExecutionEngine", Pair()),  # type: ignore[arg-type]
        {"CHEIO": completo, "VAZADO": esburacado},
        CAPITAL,
        decision_start="2023-01-08",
        decision_end="2023-01-09",
    )
    built.run()

    first = observed[0]
    assert built.window.available_history_sessions == 5
    assert first == {"CHEIO": 7, "VAZADO": 5}
    assert min(first.values()) == built.window.available_history_sessions


# ── Primeira decisão ─────────────────────────────────────────────


def test_primeira_decisao_recebe_carteira_intacta() -> None:
    """Em ``decision_start``: caixa igual ao capital, posição zero, sem trade."""
    data = frame(10)
    seen: list[MarketObservation] = []

    class Watcher:
        def decide(self, observation: MarketObservation) -> list[OrderIntent]:
            seen.append(observation)
            return []

    ExecutionEngine(
        cast("ExecutionEngine", Watcher()),  # type: ignore[arg-type]
        {TICKER: data},
        CAPITAL,
        decision_start="2023-01-08",
        decision_end="2023-01-09",
    ).run()

    first = seen[0]
    assert first.session == pd.Timestamp("2023-01-08")
    assert first.cash == pytest.approx(CAPITAL)
    assert first.equity == pytest.approx(CAPITAL)
    assert dict(first.positions) == {TICKER: 0}
    assert max(first.history[TICKER].index) == first.session
    assert len(first.history[TICKER]) == 7


def test_participante_e_consultado_uma_vez_por_sessao_avaliada() -> None:
    data = frame(10)
    recorder = Recorder(buy=False)
    engine(
        data,
        decision_start="2023-01-05",
        decision_end="2023-01-08",
        participant=recorder,
    ).run()

    assert recorder.sessions == sorted(set(recorder.sessions))
    assert len(recorder.sessions) == 4


# ── Settlement: com e sem intent pendente ────────────────────────


def test_settlement_executa_e_cobra_a_ultima_decisao() -> None:
    """O custo e o resultado da última decisão entram no que é publicado.

    A armadilha que este teste fecha é a decisão de ``decision_end`` ser
    executada e o seu custo ficar fora do resultado — trade sem contrapartida
    no patrimônio final.
    """
    data = frame(10)
    costs = CostModel(brokerage_fixed=7.0)
    result = ExecutionEngine(
        Recorder(),  # type: ignore[arg-type]
        {TICKER: data},
        CAPITAL,
        costs,
        decision_start="2023-01-08",
        decision_end="2023-01-08",
    ).run()

    settlement = pd.Timestamp("2023-01-09")
    assert [pd.Timestamp(trade.date) for trade in result.trades] == [settlement]
    trade = result.trades[0]
    assert trade.cost == pytest.approx(7.0)
    assert total_transaction_cost(result.trades) == pytest.approx(7.0)

    # Patrimônio final reconstruído a partir do trade: caixa residual mais a
    # posição marcada no fechamento do settlement.
    open_price = float(data.loc[settlement, "abertura"])
    close_price = float(data.loc[settlement, "fechamento"])
    cash = CAPITAL - trade.quantity * open_price - trade.cost
    assert result.final_equity == pytest.approx(cash + trade.quantity * close_price)
    assert result.equity_curve.iloc[-1] == pytest.approx(result.final_equity)


def test_settlement_sem_intent_pendente_continua_valido() -> None:
    """Há próxima sessão, mas nada a liquidar: o run é válido, sem trade."""
    data = frame(10)
    recorder = Recorder(buy=False)
    result = engine(
        data,
        decision_start="2023-01-08",
        decision_end="2023-01-08",
        participant=recorder,
    ).run()

    assert recorder.sessions == [pd.Timestamp("2023-01-08")]
    assert result.trades == []
    assert list(result.equity_curve.index) == [
        pd.Timestamp("2023-01-08"),
        pd.Timestamp("2023-01-09"),
    ]
    assert result.final_equity == pytest.approx(CAPITAL)


def test_ausencia_de_intent_e_ausencia_de_settlement_sao_coisas_diferentes() -> None:
    """Uma é run válido; a outra é configuração recusada antes de executar."""
    data = frame(10)

    sem_intent = engine(
        data,
        decision_start="2023-01-08",
        decision_end="2023-01-08",
        participant=Recorder(buy=False),
    ).run()
    assert sem_intent.trades == []

    with pytest.raises(EvaluationWindowError, match="no settlement session"):
        engine(data, decision_start="2023-01-11", decision_end="2023-01-11")


# ── decision_frequency governa a elegibilidade, não a janela ─────


class Periodic:
    """Participante com grade própria, como a ``decision_frequency`` do LLM.

    A grade nasce na **primeira chamada** a ``decide()``, nunca na primeira
    barra do quadro: é exatamente o contrato que o ``LLMParticipant`` usa.
    """

    def __init__(self, frequency: int) -> None:
        self.frequency = frequency
        self.consulted: list[pd.Timestamp] = []
        self.emitted: list[pd.Timestamp] = []
        self._index = 0

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        index = self._index
        self._index += 1
        self.consulted.append(observation.session)
        if index % self.frequency:
            return []
        self.emitted.append(observation.session)
        return [
            OrderIntent(
                ticker=TICKER,
                target_weight=1.0 if (index // self.frequency) % 2 == 0 else 0.0,
                decision_time=observation.session,
            )
        ]


def test_grade_de_frequencia_comeca_em_decision_start() -> None:
    """``decision_start`` é o índice zero; ``+1..+4`` não são elegíveis."""
    data = frame(20)
    agent = Periodic(5)
    engine(
        data,
        decision_start="2023-01-06",
        decision_end="2023-01-16",
        participant=agent,
    ).run()

    sessions = list(data.loc["2023-01-06":"2023-01-16"].index)
    assert agent.consulted == sessions
    assert agent.emitted == [sessions[0], sessions[5], sessions[10]]


def test_warmup_nao_desloca_a_grade_de_frequencia() -> None:
    """Mesma janela, mesmos preços por data, coberturas anteriores diferentes."""
    grades: list[list[pd.Timestamp]] = []
    for start in ("2023-01-10", "2022-12-01"):
        sessions = int((pd.Timestamp("2023-01-28") - pd.Timestamp(start)).days)
        agent = Periodic(5)
        engine(
            frame(sessions, start=start),
            decision_start="2023-01-16",
            decision_end="2023-01-26",
            participant=agent,
        ).run()
        grades.append(agent.emitted)

    assert grades[0] == grades[1]
    assert grades[0][0] == pd.Timestamp("2023-01-16")


def test_decision_end_nao_elegivel_nao_forca_decisao_nem_invalida_o_run() -> None:
    """``decision_end`` é limite da janela, não obrigação de decidir.

    Com ``decision_frequency=5`` e ``decision_end`` fora da grade, a última
    decisão *emitida* precede ``decision_end``, o settlement não tem pendente
    e o run continua válido — nenhuma chamada extraordinária é inventada.
    """
    data = frame(20)
    agent = Periodic(5)
    result = engine(
        data,
        decision_start="2023-01-06",
        decision_end="2023-01-13",
        participant=agent,
    ).run()

    assert agent.consulted[-1] == pd.Timestamp("2023-01-13")
    assert agent.emitted[-1] == pd.Timestamp("2023-01-11")
    # Cada decisão emitida virou trade em t+1 dela, e nada mais: a sessão de
    # settlement — seguinte a decision_end — não tinha pendente e não negocia.
    assert [pd.Timestamp(trade.date) for trade in result.trades] == [
        pd.Timestamp("2023-01-07"),
        pd.Timestamp("2023-01-12"),
    ]
    assert result.equity_curve.index[-1] == pd.Timestamp("2023-01-14")


# ── Fronteira da curva publicada ─────────────────────────────────


def test_curva_vai_de_decision_start_a_settlement() -> None:
    data = frame(20)
    built = engine(data, decision_start="2023-01-06", decision_end="2023-01-13")
    result = built.run()

    assert result.equity_curve.index[0] == built.window.decision_start
    assert result.equity_curve.index[-1] == built.window.settlement_session


def test_tamanho_da_curva_nao_e_numero_de_decisoes() -> None:
    """``len(curva) == evaluated_sessions + 1``; a grade decide menos que isso."""
    data = frame(20)
    agent = Periodic(5)
    built = engine(
        data,
        decision_start="2023-01-06",
        decision_end="2023-01-16",
        participant=agent,
    )
    result = built.run()

    window = built.window
    assert window.evaluated_sessions == 11
    assert len(result.equity_curve) == window.evaluated_sessions + 1
    # Consultas: uma por sessão avaliada. Intents: só os da grade.
    assert len(agent.consulted) == window.evaluated_sessions
    assert len(agent.emitted) == 3


def test_modo_legado_nao_acrescenta_ponto_de_settlement() -> None:
    data = frame(6)
    built = engine(data)
    result = built.run()

    assert len(result.equity_curve) == built.window.evaluated_sessions == 6


def test_invariantes_de_ordenacao_da_janela() -> None:
    window = resolve_evaluation_window(
        common_sessions({TICKER: frame(20)}),
        decision_start="2023-01-06",
        decision_end="2023-01-13",
    )
    settlement = window.settlement_session
    assert settlement is not None

    assert window.data_start <= window.decision_start
    assert window.decision_start <= window.decision_end
    assert window.decision_end < settlement
    assert settlement <= window.data_end
    assert window.warmup_sessions >= 0
    assert window.evaluated_sessions >= 1


# ── Métricas dependem da janela, não da cobertura ────────────────


def test_cobertura_anterior_maior_nao_altera_metrica_alguma() -> None:
    """Warm-up é informação de mercado; não pode virar duração nem retorno.

    O participante é Buy & Hold justamente porque a sua decisão não depende do
    histórico: assim o que sobra para comparar é só a semântica da curva. Um
    participante com indicador recursivo mudaria de comportamento por razão
    legítima e não isolaria nada.
    """
    window = {"decision_start": "2023-01-16", "decision_end": "2023-01-26"}
    curves: list[pd.Series] = []
    metrics: list[dict] = []
    for start in ("2023-01-12", "2022-11-01"):
        sessions = int((pd.Timestamp("2023-01-28") - pd.Timestamp(start)).days)
        result = ExecutionEngine(
            BuyAndHoldParticipant(TICKER),
            {TICKER: frame(sessions, start=start)},
            CAPITAL,
            **window,  # type: ignore[arg-type]
        ).run()
        curves.append(result.equity_curve)
        metrics.append(dict(performance_metrics(result.equity_curve)))

    assert len(curves[0]) == len(curves[1])
    pd.testing.assert_series_equal(curves[0], curves[1])
    for key in ("annualized_return", "sharpe_ratio", "sortino_ratio", "max_drawdown"):
        assert key in metrics[0]
        assert metrics[0][key] == pytest.approx(metrics[1][key])
    assert metrics[0] == metrics[1]


# ── Ciclo de vida dos participantes do registry ──────────────────


def _participant_cases() -> list:
    """Um caso por participante do registry, com o universo que ele aceita."""
    return [
        pytest.param(lambda: BuyAndHoldParticipant(TICKER), 1, id="buy_and_hold"),
        pytest.param(lambda: SMACrossParticipant(TICKER, 3, 8), 1, id="sma_cross"),
        pytest.param(lambda: BollingerParticipant(TICKER, 5, 1.5), 1, id="bollinger"),
        pytest.param(lambda: EqualWeightParticipant(rebalance_freq=4), 2, id="equal_weight"),
        pytest.param(
            lambda: MinVarianceParticipant(window=10, rebalance_freq=4),
            2,
            id="min_variance",
        ),
    ]


def wave_frame(sessions: int, *, start: str) -> pd.DataFrame:
    """Série oscilante, também ancorada na data, não na posição do recorte.

    A rampa monótona de :func:`frame` nunca cruza médias nem rompe bandas: sobre
    ela, SMA e Bollinger não emitem intent algum e a prova passaria vazia. Aqui
    o preço oscila o bastante para os dois negociarem de verdade, e continua
    sendo função de ``(data - PRICE_EPOCH)`` — dois recortes que começam em
    datas diferentes concordam barra a barra onde se sobrepõem.
    """
    index = pd.DatetimeIndex(pd.date_range(start=start, periods=sessions, freq="D"))
    offsets = [float((stamp - PRICE_EPOCH).days) for stamp in index]
    closes = [50.0 + 12.0 * math.sin(offset / 6.0) + offset * 0.05 for offset in offsets]
    opens = [close - 0.5 for close in closes]
    return pd.DataFrame({"abertura": opens, "fechamento": closes}, index=index)


def _universe(tickers: int, sessions: int, start: str) -> dict[str, pd.DataFrame]:
    base = wave_frame(sessions, start=start)
    names = [TICKER, "VALE3"][:tickers]
    return {name: base * (1.0 + 0.01 * index) for index, name in enumerate(names)}


@pytest.mark.parametrize(("build", "tickers"), _participant_cases())
def test_participante_nao_infere_primeira_decisao_do_tamanho_do_historico(
    build, tickers: int
) -> None:
    """Nenhum participante pode confundir ``data_start`` com ``decision_start``.

    As duas coberturas começam em datas diferentes, mas ambas cobrem com folga o
    lookback do indicador de cada caso — então qualquer diferença na sequência
    de intents seria consequência do *tamanho do recorte*, não da informação
    disponível. É exatamente essa dependência que o warm-up trouxe de volta:
    ``len(history) > 1`` já na primeira decisão faria o Buy & Hold nunca entrar
    e deslocaria a grade de rebalance conforme o snapshot crescesse para trás.
    """
    window = {"decision_start": "2023-01-16", "decision_end": "2023-02-10"}
    emitted: list[list[tuple]] = []
    for start in ("2022-12-05", "2022-10-01"):
        sessions = int((pd.Timestamp("2023-02-13") - pd.Timestamp(start)).days)
        participant = build()
        original = participant.decide
        record: list[tuple] = []

        def spy(observation, original=original, record=record):
            intents = original(observation)
            record.append(
                (
                    observation.session,
                    tuple(
                        sorted(
                            (intent.ticker, intent.target_weight) for intent in intents
                        )
                    ),
                )
            )
            return intents

        participant.decide = spy  # type: ignore[method-assign]
        ExecutionEngine(
            participant,
            _universe(tickers, sessions, start),
            CAPITAL,
            **window,  # type: ignore[arg-type]
        ).run()
        emitted.append(record)

    assert emitted[0][0][0] == pd.Timestamp("2023-01-16")
    assert emitted[0] == emitted[1]
    assert any(
        intents for _, intents in emitted[0]
    ), "o caso precisa emitir algum intent para provar alguma coisa"


@pytest.mark.parametrize(("build", "tickers"), _participant_cases())
def test_instancia_nova_por_run_nao_carrega_estado(build, tickers: int) -> None:
    """Instância nova por run já basta: dois runs idênticos coincidem em tudo.

    Nenhum framework de ciclo de vida é necessário enquanto
    ``build_participant`` devolver instância nova — este é o teste que tornaria
    visível a falta dela.
    """
    window = {"decision_start": "2023-01-16", "decision_end": "2023-02-10"}
    data = _universe(tickers, 140, "2022-10-01")
    results = [
        ExecutionEngine(build(), data, CAPITAL, **window).run()  # type: ignore[arg-type]
        for _ in range(2)
    ]

    pd.testing.assert_series_equal(results[0].equity_curve, results[1].equity_curve)
    assert results[0].trades, "o caso precisa negociar para provar alguma coisa"
    assert [
        (trade.date, trade.ticker, trade.type, trade.quantity)
        for trade in results[0].trades
    ] == [
        (trade.date, trade.ticker, trade.type, trade.quantity)
        for trade in results[1].trades
    ]
