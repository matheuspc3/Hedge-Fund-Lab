"""Contratos mínimos e execução comum da arena incremental.

O caminho comum executa participantes long-only, sem margem ou alavancagem,
sobre um ou mais ativos. As escolhas científicas definitivas de lote, slippage,
liquidez, suspensão e calendário continuam fora deste contrato técnico
preliminar.

**Cobertura de dados e janela avaliada são coisas diferentes.** O calendário
comum descreve o que existe; a :class:`EvaluationWindow` descreve o que conta
para o experimento::

    data_start ...... decision_start ... decision_end .. settlement_session
    |___ warm-up ____|___ decisões avaliadas ________|__ executa a última __|

Sessões de warm-up existem apenas como histórico causal da primeira decisão:
não marcam patrimônio, não chamam o participante e não produzem trade.

Fronteira da curva publicada, quando a janela é declarada::

    primeiro ponto = decision_start       (capital inicial, posição zero)
    último ponto   = settlement_session   (a última decisão já liquidada)
    len(curva)     = evaluated_sessions + 1

O ``+ 1`` é a ``settlement_session``, e é por isso que o tamanho da curva
**não** é o número de decisões nem o número de sessões avaliadas. No modo
técnico legado não existe settlement e a curva cobre a cobertura inteira.
"""

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol, cast

import pandas as pd

from src.backtesting.costs import CostModel
from src.backtesting.engine import BacktestResult, Trade

# Tolerância numérica única do caminho comum: resíduo de ponto flutuante em
# somas de pesos e comparações de peso alvo, nunca folga econômica.
WEIGHT_TOLERANCE = 1e-9


class EvaluationWindowError(ValueError):
    """A janela pedida não pode ser avaliada sobre o calendário disponível.

    Fail-closed por desenho: alinhar a data silenciosamente para o pregão
    seguinte, ou aceitar uma janela sem settlement, publicaria um run que
    responde a uma pergunta diferente da que foi pedida.
    """


def common_sessions(data: Mapping[str, pd.DataFrame]) -> pd.DatetimeIndex:
    """Calendário comum por interseção, em ordem crescente.

    Fonte única da regra: o motor executa sobre este calendário e o gate
    pré-run do runner resolve a janela sobre exatamente o mesmo índice, de modo
    que os dois não podem divergir sobre qual sessão existe.
    """
    common: pd.DatetimeIndex | None = None
    for ticker in sorted(data):
        index = cast(pd.DatetimeIndex, data[ticker].index)
        common = (
            index
            if common is None
            else cast(pd.DatetimeIndex, common.intersection(index))
        )
    if common is None:
        raise ValueError("data cannot be empty")
    return cast(pd.DatetimeIndex, common.sort_values())


@dataclass(frozen=True)
class EvaluationWindow:
    """Janela avaliada já resolvida contra um calendário comum concreto.

    Descreve *evidência realizada*, não configuração pedida: cada campo é uma
    sessão que existe no calendário do run. A configuração pedida vive na
    ``ExperimentSpec``; esta resolução é o que aconteceu com ela.

    ``settlement_session`` é a consequência direta de ``close(t) -> open(t+1)``:
    sem ela, a decisão tomada em ``decision_end`` nunca vira trade.

    **Toda contagem desta classe é contagem de sessão comum**, o calendário por
    interseção que o motor percorre. É a única unidade em que o gate, a
    execução e a evidência publicada podem concordar: um ticker pode ter barra
    numa data em que outro não tem, e essa barra não é uma sessão em que a
    arena decide ou executa.

    ``evaluated_sessions`` conta as sessões comuns de ``[decision_start,
    decision_end]`` — aquelas em que a arena **consulta** o participante.
    Não é o número de intents emitidos: um participante com
    ``decision_frequency > 1``, ou que decida ``MANTER``, é consultado na
    sessão e não emite intent algum. Também não é o tamanho da curva
    publicada, que inclui a ``settlement_session``.
    """

    data_start: pd.Timestamp
    data_end: pd.Timestamp
    decision_start: pd.Timestamp
    decision_end: pd.Timestamp
    settlement_session: pd.Timestamp | None
    warmup_sessions: int
    evaluated_sessions: int

    @property
    def available_history_sessions(self) -> int:
        """Sessões comuns causalmente disponíveis **até e incluindo** ``decision_start``.

        Definição canônica única, e a medida que o gate de warm-up compara::

            warmup_sessions            = sessões comuns estritamente anteriores
                                         a decision_start
            available_history_sessions = warmup_sessions + 1

        O ``+ 1`` é a própria barra de ``decision_start``, que já está
        observável no fechamento em que a primeira decisão é tomada.

        **Não é** ``len(observation.history[ticker])``. O histórico entregue ao
        participante é o quadro daquele ticker recortado em ``t``, e um ticker
        que negocie em datas fora do calendário comum chega com *mais* barras.
        O gate conta o calendário comum de propósito: é o único número igual
        para todos os tickers do run, e é um limite inferior do histórico que
        qualquer um deles recebe. Em run single-asset os dois coincidem.
        """
        return self.warmup_sessions + 1

    @property
    def warmup_calendar_days(self) -> int:
        """Dias corridos entre a primeira barra disponível e a primeira decisão."""
        return int((self.decision_start - self.data_start).days)

    @property
    def run_end(self) -> pd.Timestamp:
        """Última sessão que o motor precisa processar."""
        settlement = self.settlement_session
        return self.decision_end if settlement is None else settlement

    @property
    def explicit(self) -> bool:
        """``True`` quando a janela foi declarada, não derivada da cobertura."""
        return self.settlement_session is not None

    def to_dict(self) -> dict[str, object]:
        """Evidência canônica publicada no manifest do run.

        ``first_decision_session`` e ``last_decision_session`` são os limites
        da janela: a primeira e a última sessão em que o participante foi
        **consultado**. Quando ele emitiu um intent em cada uma delas é
        pergunta do participante, não do calendário, e a resposta vive na
        evidência dele (o trace de LLM, os trades publicados) — a arena não
        conhece ``decision_frequency`` e não inventaria aqui um número que não
        observa.
        """
        settlement = self.settlement_session
        return {
            "data_start": _date_text(self.data_start),
            "data_end": _date_text(self.data_end),
            "first_decision_session": _date_text(self.decision_start),
            "last_decision_session": _date_text(self.decision_end),
            "settlement_session": (
                None if settlement is None else _date_text(settlement)
            ),
            "warmup_sessions": self.warmup_sessions,
            "warmup_calendar_days": self.warmup_calendar_days,
            "available_history_sessions": self.available_history_sessions,
            "evaluated_sessions": self.evaluated_sessions,
        }


def _date_text(moment: pd.Timestamp) -> str:
    return pd.Timestamp(moment).date().isoformat()


def resolve_evaluation_window(
    sessions: pd.DatetimeIndex,
    *,
    decision_start: object = None,
    decision_end: object = None,
    minimum_history_sessions: int | None = None,
) -> EvaluationWindow:
    """Resolve a janela avaliada contra o calendário comum, ou falha.

    Com ``decision_start``/``decision_end`` ausentes devolve o **modo técnico
    legado**: toda a cobertura é decidida, não existe warm-up e não existe
    settlement reservado — exatamente o comportamento anterior à janela
    explícita. O caminho científico declara a janela e nunca cai aqui.

    Nenhuma data é alinhada para o pregão seguinte: uma âncora que não é sessão
    comum é erro de configuração, não detalhe a ser corrigido em silêncio.
    """
    if sessions.empty:
        raise EvaluationWindowError("data has no session shared by every ticker")

    data_start = cast(pd.Timestamp, sessions[0])
    data_end = cast(pd.Timestamp, sessions[-1])

    if decision_start is None and decision_end is None:
        if minimum_history_sessions is not None:
            raise EvaluationWindowError(
                "minimum_history_sessions requires an explicit decision window; "
                "a warm-up gate is meaningless when every session is decided"
            )
        return EvaluationWindow(
            data_start=data_start,
            data_end=data_end,
            decision_start=data_start,
            decision_end=data_end,
            settlement_session=None,
            warmup_sessions=0,
            evaluated_sessions=len(sessions),
        )
    if decision_start is None or decision_end is None:
        raise EvaluationWindowError(
            "decision_start and decision_end must be declared together"
        )

    start = _require_session(sessions, decision_start, "decision_start")
    end = _require_session(sessions, decision_end, "decision_end")
    if start > end:
        raise EvaluationWindowError(
            f"decision_start {_date_text(start)} is after decision_end "
            f"{_date_text(end)}"
        )

    start_position = _position_of(sessions, start)
    end_position = _position_of(sessions, end)

    if end_position + 1 >= len(sessions):
        raise EvaluationWindowError(
            f"decision_end {_date_text(end)} has no settlement session: the "
            "decision taken at its close is executed at the next common open, "
            "which this data does not contain. Extend the coverage past "
            "decision_end or move decision_end back"
        )
    settlement = cast(pd.Timestamp, sessions[end_position + 1])

    window = EvaluationWindow(
        data_start=data_start,
        data_end=data_end,
        decision_start=start,
        decision_end=end,
        settlement_session=settlement,
        warmup_sessions=start_position,
        evaluated_sessions=end_position - start_position + 1,
    )

    if minimum_history_sessions is not None:
        available = window.available_history_sessions
        if available < minimum_history_sessions:
            raise EvaluationWindowError(
                f"decision_start {_date_text(start)} has only {available} "
                f"session(s) of history available, below the required "
                f"minimum_history_sessions={minimum_history_sessions}; the "
                "first evaluated decision would be taken with less context "
                "than the protocol declares"
            )
    return window


def _position_of(sessions: pd.DatetimeIndex, session: pd.Timestamp) -> int:
    """Posição inteira de uma sessão já validada como presente e única.

    ``get_loc`` é tipado para índices que admitem duplicata ou fatia; aqui o
    calendário comum é único e ordenado, então a posição é sempre um inteiro.
    """
    position = sessions.get_loc(session)
    if not isinstance(position, int):
        raise EvaluationWindowError(
            f"session {_date_text(session)} is not uniquely located in the "
            "common calendar"
        )
    return position


def _require_session(
    sessions: pd.DatetimeIndex, moment: object, label: str
) -> pd.Timestamp:
    """Exige uma data que seja sessão comum, sem alinhamento implícito."""
    try:
        stamp = cast(pd.Timestamp, pd.Timestamp(moment))  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise EvaluationWindowError(f"{label} is not a valid date: {moment!r}") from exc
    if pd.isna(stamp):
        raise EvaluationWindowError(f"{label} cannot be NaT")
    stamp = cast(pd.Timestamp, stamp.normalize())
    if stamp not in sessions:
        raise EvaluationWindowError(
            f"{label} {_date_text(stamp)} is not a session shared by every "
            "ticker in this run; it is not aligned to the next session "
            "automatically, because that would evaluate a different date than "
            "the one declared"
        )
    return stamp


@dataclass(frozen=True)
class OrderIntent:
    """Posição alvo desejada, anterior a preço, custos e arredondamento.

    O intent descreve apenas *onde* o participante quer estar, decidido em
    ``close(t)``. Direção da negociação não é decisão do participante: comprar
    ou vender depende da posição e do preço observados na abertura seguinte,
    que o participante não conhece. A elegibilidade de execução também pertence
    ao executor, que associa a intenção à próxima abertura observada — se ela
    existir.
    """

    ticker: str
    target_weight: float
    decision_time: pd.Timestamp

    def __post_init__(self) -> None:
        ticker = self.ticker.strip()
        decision_time = pd.Timestamp(self.decision_time)
        if not ticker:
            raise ValueError("ticker cannot be empty")
        if not math.isfinite(self.target_weight) or not 0 <= self.target_weight <= 1:
            raise ValueError(
                "target_weight must be finite and between 0 and 1; "
                "shorting and leverage are not supported"
            )
        if pd.isna(decision_time):
            raise ValueError("decision_time cannot be NaT")
        object.__setattr__(self, "ticker", ticker)
        object.__setattr__(self, "decision_time", decision_time)


@dataclass(frozen=True)
class MarketObservation:
    """Informação observável no fechamento de uma sessão.

    Contém somente o que existe em ``t``. O participante não sabe se ainda há
    barra futura no recorte, portanto não consegue identificar o fim da amostra
    experimental por este contrato.
    """

    session: pd.Timestamp
    history: Mapping[str, pd.DataFrame]
    positions: Mapping[str, int]
    cash: float
    equity: float


class Participant(Protocol):
    """Participante que somente decide; não executa nem altera portfólio."""

    def decide(self, observation: MarketObservation) -> list[OrderIntent]: ...


def weights_to_intents(
    observation: MarketObservation,
    target_weights: Mapping[str, float],
) -> list[OrderIntent]:
    """Converte um mapa de pesos alvo em intents, em ordem canônica.

    Nenhuma direção é decidida aqui: o intent declara apenas o peso desejado e
    o executor descobre, na abertura seguinte, se chegar nele exige comprar,
    vender ou nada.
    """
    return [
        OrderIntent(
            ticker=ticker,
            target_weight=float(target_weights[ticker]),
            decision_time=observation.session,
        )
        for ticker in sorted(target_weights)
    ]


class ExecutionEngine:
    """Executa intents long-only na abertura seguinte e marca equity no close."""

    def __init__(
        self,
        participant: Participant,
        data: Mapping[str, pd.DataFrame],
        initial_capital: float,
        cost_model: CostModel | None = None,
        *,
        decision_start: object = None,
        decision_end: object = None,
        minimum_history_sessions: int | None = None,
    ) -> None:
        if not data:
            raise ValueError("data cannot be empty")
        if initial_capital <= 0 or not math.isfinite(initial_capital):
            raise ValueError("initial_capital must be finite and > 0")

        frames: dict[str, pd.DataFrame] = {}
        for raw_ticker, frame in data.items():
            ticker = raw_ticker.strip()
            if not ticker:
                raise ValueError("ticker cannot be empty")
            if ticker in frames:
                raise ValueError(f"duplicate ticker in data: {ticker}")
            frames[ticker] = self._validate(ticker, frame)

        self.participant = participant
        self.tickers = sorted(frames)
        self.data = {ticker: frames[ticker] for ticker in self.tickers}
        # Calendário comum explícito por interseção, como no motor multi-ativo
        # legado: nenhuma barra é fabricada nem propagada por forward-fill.
        self.sessions = self._common_sessions()
        if self.sessions.empty:
            raise ValueError("data has no session shared by every ticker")
        # A janela é resolvida na construção, antes de qualquer execução: uma
        # configuração impossível falha aqui e não depois de o participante já
        # ter decidido — e possivelmente pago — algumas sessões.
        self.window = resolve_evaluation_window(
            self.sessions,
            decision_start=decision_start,
            decision_end=decision_end,
            minimum_history_sessions=minimum_history_sessions,
        )
        self.initial_capital = float(initial_capital)
        self.cost_model = cost_model or CostModel()

    @staticmethod
    def _validate(ticker: str, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            raise ValueError(f"data for {ticker} cannot be empty")
        missing = {"abertura", "fechamento"} - set(frame.columns)
        if missing:
            raise ValueError(
                f"data for {ticker} missing columns: {', '.join(sorted(missing))}"
            )
        if not isinstance(frame.index, pd.DatetimeIndex):
            raise ValueError("data index must be a DatetimeIndex")
        if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
            raise ValueError("data index must be sorted and unique")
        prices = frame[["abertura", "fechamento"]].to_numpy(dtype=float)
        if not all(math.isfinite(value) and value > 0 for value in prices.flat):
            raise ValueError("open and close prices must be finite and > 0")
        return frame.copy(deep=True)

    def _common_sessions(self) -> pd.DatetimeIndex:
        return common_sessions(self.data)

    # ── Execução ─────────────────────────────────────────────────

    def _buy_total(
        self, quantities: Mapping[str, int], prices: Mapping[str, float]
    ) -> float:
        """Custo financeiro total de um conjunto de compras, via ``CostModel``."""
        total = 0.0
        for ticker in sorted(quantities):
            quantity = quantities[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            total += notional + self.cost_model.apply_buy(notional)
        return total

    def _scale_buys(
        self,
        wanted: Mapping[str, int],
        prices: Mapping[str, float],
        budget: float,
    ) -> dict[str, int]:
        """Dimensiona as compras em conjunto, sem privilegiar nenhum ticker.

        Quando o caixa não cobre todos os déficits, os alvos são escalonados
        pelo mesmo fator e truncados para baixo. O fator vem de uma busca
        binária sobre o custo real reportado pelo ``CostModel``, portanto o
        resultado não depende da ordem dos tickers nem assume a fórmula de custo.

        ponytail: o resíduo de caixa não é redistribuído; a política científica
        de lote e arredondamento continua TBD e deve substituir este truncamento.
        """
        if not wanted:
            return {}
        if self._buy_total(wanted, prices) <= budget:
            return dict(wanted)

        low, high = 0.0, 1.0
        best = dict.fromkeys(wanted, 0)
        for _ in range(64):
            middle = (low + high) / 2
            candidate = {
                ticker: math.floor(middle * quantity)
                for ticker, quantity in wanted.items()
            }
            if self._buy_total(candidate, prices) <= budget:
                low, best = middle, candidate
            else:
                high = middle
        return best

    def _settle(
        self,
        intents: list[OrderIntent],
        session: pd.Timestamp,
        prices: Mapping[str, float],
        cash: float,
        positions: dict[str, int],
    ) -> tuple[float, list[Trade]]:
        """Aplica os intents pendentes na abertura de ``session``.

        A direção nasce aqui: o peso alvo vira quantidade alvo sobre o
        patrimônio observado na abertura e é comparada com a posição corrente.
        Excesso vira ``SELL``, déficit vira ``BUY`` e uma posição já no alvo não
        gera trade — mesmo que, no fechamento anterior, o alvo apontasse para o
        lado oposto.
        """
        equity_at_open = cash + sum(
            positions[ticker] * prices[ticker] for ticker in self.tickers
        )
        targets = {intent.ticker: intent.target_weight for intent in intents}
        desired = {
            ticker: (
                math.floor(equity_at_open * targets[ticker] / prices[ticker])
                if ticker in targets
                else positions[ticker]
            )
            for ticker in self.tickers
        }

        trades: list[Trade] = []
        # Vendas primeiro: o caixa liberado financia as compras do rebalance.
        for ticker in self.tickers:
            quantity = positions[ticker] - desired[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            cost = self.cost_model.apply_sell(notional)
            if cash + notional - cost < 0:
                raise ValueError("sell costs would make cash negative")
            cash += notional - cost
            positions[ticker] -= quantity
            trades.append(
                Trade(
                    date=session,
                    type="SELL",
                    price=prices[ticker],
                    quantity=quantity,
                    cost=cost,
                    ticker=ticker,
                )
            )

        wanted = {
            ticker: desired[ticker] - positions[ticker]
            for ticker in self.tickers
            if desired[ticker] > positions[ticker]
        }
        quantities = self._scale_buys(wanted, prices, cash)
        spent = self._buy_total(quantities, prices)
        if spent > cash:
            raise RuntimeError("buy execution would make cash negative")
        for ticker in sorted(quantities):
            quantity = quantities[ticker]
            if quantity <= 0:
                continue
            notional = quantity * prices[ticker]
            positions[ticker] += quantity
            trades.append(
                Trade(
                    date=session,
                    type="BUY",
                    price=prices[ticker],
                    quantity=quantity,
                    cost=self.cost_model.apply_buy(notional),
                    ticker=ticker,
                )
            )
        return cash - spent, trades

    def _validate_intents(
        self, intents: list[OrderIntent], observation: MarketObservation
    ) -> None:
        if not all(isinstance(intent, OrderIntent) for intent in intents):
            raise TypeError("participant must return OrderIntent instances")
        if len({intent.ticker for intent in intents}) != len(intents):
            raise ValueError("participant returned duplicate intents for a ticker")
        total_weight = 0.0
        for intent in intents:
            if intent.ticker not in self.data:
                raise ValueError(f"intent references unknown ticker: {intent.ticker}")
            if intent.decision_time != observation.session:
                raise ValueError("intent decision_time must match observation session")
            total_weight += intent.target_weight
        if total_weight > 1 + WEIGHT_TOLERANCE:
            raise ValueError(
                "target weights must sum to at most 1; leverage is not supported"
            )

    def run(self) -> BacktestResult:
        """Executa ``close(t) -> intent -> open(t+1) -> trade -> close equity``.

        Percorre somente ``[decision_start, run_end]``. As sessões de warm-up
        anteriores **não** são percorridas: elas continuam existindo em
        ``self.data`` e portanto em ``observation.history``, que é exatamente o
        papel que lhes cabe — informação causal, nunca performance. Por isso a
        carteira em ``decision_start`` é sempre ``cash = initial_capital`` e
        posição zero: warm-up não pode virar posição financeira por acidente.

        Na ``settlement_session`` o motor liquida o pendente de
        ``decision_end`` e marca o resultado, mas **não** chama o participante:
        decidir ali seria decidir fora da janela avaliada.

        Liquidar *o que houver*: se a consulta em ``decision_end`` não produziu
        intent — ``MANTER``, veto de risco, sessão não elegível pela
        ``decision_frequency`` do participante —, o settlement simplesmente
        marca o patrimônio e o run continua válido. Ausência legítima de trade
        não é falha de settlement, e ``decision_end`` nunca força uma chamada
        extraordinária: ele é limite da janela, não obrigação de decidir.

        No modo técnico legado (sem janela declarada) ``decision_end`` é a
        última sessão da cobertura e não há settlement, de modo que o intent
        da última sessão continua morrendo sem execução, como antes.
        """
        window = self.window
        first_position = _position_of(self.sessions, window.decision_start)
        last_position = _position_of(self.sessions, window.run_end)
        run_sessions = cast(
            pd.DatetimeIndex, self.sessions[first_position : last_position + 1]
        )

        cash = self.initial_capital
        positions = dict.fromkeys(self.tickers, 0)
        pending: list[OrderIntent] = []
        trades: list[Trade] = []
        equity_values: list[float] = []

        for raw_session in run_sessions:
            session = cast(pd.Timestamp, raw_session)
            opens = {
                ticker: float(self.data[ticker].loc[session, "abertura"])
                for ticker in self.tickers
            }
            if pending:
                cash, settled = self._settle(pending, session, opens, cash, positions)
                trades.extend(settled)
            pending = []

            closes = {
                ticker: float(self.data[ticker].loc[session, "fechamento"])
                for ticker in self.tickers
            }
            equity = cash + sum(
                positions[ticker] * closes[ticker] for ticker in self.tickers
            )
            equity_values.append(equity)
            if session > window.decision_end:
                # Settlement: o pendente já foi liquidado e o patrimônio já foi
                # marcado. Nada mais desta sessão pertence ao experimento.
                continue
            observation = MarketObservation(
                session=session,
                # O histórico vem do quadro inteiro, não do recorte executado:
                # a decisão em ``decision_start`` enxerga todo o warm-up.
                history=MappingProxyType(
                    {
                        ticker: self.data[ticker].loc[:session].copy(deep=True)
                        for ticker in self.tickers
                    }
                ),
                positions=MappingProxyType(dict(positions)),
                cash=cash,
                equity=equity,
            )
            intents = list(self.participant.decide(observation))
            self._validate_intents(intents, observation)
            pending = intents

        equity_curve = pd.Series(equity_values, index=run_sessions, dtype=float)
        return BacktestResult(
            equity_curve=equity_curve,
            trades=trades,
            initial_capital=self.initial_capital,
            final_equity=float(equity_curve.iloc[-1]),
        )
