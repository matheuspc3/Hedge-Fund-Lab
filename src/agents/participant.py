"""Participante da arena que delega a decisão ao grafo multiagente.

Este módulo é um *adaptador*, não uma segunda stack de LLM. Ele reutiliza os
schemas, o cliente, os prompts, os nós e o grafo já existentes em
:mod:`src.agents` e reaproveita o cálculo de indicadores do pipeline. O que ele
acrescenta é o contrato causal da arena::

    MarketObservation(close(t))
            |
            v
    AgentState  -- grafo (quorum técnico -> risco -> portfólio)
            |
            v
    FinalDecision (COMPRA/VENDA/MANTER + position_size)
            |
            v
    carteira-alvo completa sobre o universo observado
            |
            v
    OrderIntent(target_weight)  -- ExecutionEngine na abertura de t+1

O participante termina em peso alvo. Quantidade, direção, preço de execução,
custo, caixa e ``Trade`` continuam sendo exclusividade do ``ExecutionEngine``:
nada aqui reimplementa o motor financeiro.

Limitação declarada: a stack de agentes atual é single-asset. ``AgentState``
descreve um ticker, um preço e uma posição escalar, e não existe etapa de
construção de carteira entre ativos. Por isso o participante recusa
explicitamente um universo com mais de um ativo em vez de fabricar um laço por
ticker — isso seria uma estratégia nova, sem sustentação no código atual. O
contrato de carteira-alvo completa (:func:`target_portfolio_to_intents`) já é o
caminho por onde a decisão passa, de modo que a evolução multi-ativo só precisa
substituir a origem dos pesos.
"""

import asyncio
import math
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, cast

import pandas as pd
from pydantic import BaseModel

from src.agents.graph import build_graph
from src.agents.llm_client import LLMClient, MockLLMClient
from src.agents.portfolio_manager import PortfolioConfig
from src.agents.risk_manager import RiskConfig
from src.agents.state import (
    AgentState,
    FinalDecision,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
)
from src.agents.technical_analyst import INDICATOR_KEYS, AnalystEnsembleConfig
from src.backtesting.arena import (
    WEIGHT_TOLERANCE,
    MarketObservation,
    OrderIntent,
    weights_to_intents,
)
from src.pipeline.transform import DataTransformer

#: Provedores que o participante sabe construir a partir de uma spec.
#: ``mock`` não faz rede e existe para teste e demonstração; ele aparece na
#: ``ParticipantSpec`` e, portanto, no manifest, de modo que um run mock nunca
#: se confunde com um run científico.
SUPPORTED_PROVIDERS = ("mock", "agent_router")

#: Fator de anualização da volatilidade, herdado do motor legado de agentes.
TRADING_DAYS_PER_YEAR = 252


class LLMDecisionError(ValueError):
    """A decisão do LLM não pode ser publicada como intenção de investimento.

    Cobre falha não recuperada no limite do provedor e saída que viola o
    contrato de carteira-alvo. Nunca vira ``MANTER``: infraestrutura quebrada e
    decisão de investimento são coisas diferentes.
    """


@dataclass(frozen=True)
class LLMDecisionRecord:
    """Trilha mínima de uma decisão, suficiente para reconstruí-la em teste.

    ponytail: integrar estes registros ao ``RunResult``/manifest exige mudança
    de schema e ficou como hardening seguinte; hoje eles vivem na instância do
    participante, que é nova a cada run.
    """

    session: pd.Timestamp
    technical_signal: TechnicalSignal | None
    consensus: TechnicalConsensus | None
    risk_verdict: RiskVerdict | None
    final_decision: FinalDecision | None
    target_weight: float | None
    errors: tuple[str, ...] = ()
    llm_failures: tuple[str, ...] = ()


def _mock_client() -> MockLLMClient:
    """Cliente determinístico com respostas válidas para cada schema.

    Reutiliza ``MockLLMClient``: o default dele (``"MANTER"`` como texto) não
    valida contra nenhum schema, então as respostas são declaradas aqui.

    As respostas são ``dict``, não instâncias Pydantic: ``MockLLMClient``
    devolve uma instância pré-construída por referência, e ``portfolio_manager``
    escreve em ``position_size`` ao aplicar o teto. Um objeto compartilhado
    seria mutado de sessão em sessão; o ``dict`` faz cada chamada validar um
    objeto novo.
    """
    return MockLLMClient(
        {
            TechnicalSignal: {
                "signal": "COMPRA",
                "justification": "Resposta determinística de mock",
                "confidence": 0.9,
            },
            RiskVerdict: {
                "verdict": "APROVADO",
                "analysis": "Resposta determinística de mock",
                "risk_metrics": {},
            },
            FinalDecision: {
                "decision": "COMPRA",
                "position_size": 1.0,
                "reasoning": "Resposta determinística de mock",
            },
        }
    )


class FailureRecordingClient(LLMClient):
    """Observa o limite do provedor sem alterar a stack de agentes.

    Os nós do grafo capturam ``ValueError``/``TypeError`` e degradam para
    ``MANTER``/``VETADO``. Essa degradação é adequada para o caminho
    operacional legado, mas mistura falha de infraestrutura com decisão de
    investimento. Esta casca registra a falha *antes* de o nó engoli-la, para
    que o participante possa falhar explicitamente.

    Fica por fora de ``RetryingLLMClient``: uma tentativa que o retry recuperou
    não chega aqui e, portanto, não é registrada como falha.
    """

    def __init__(self, client: LLMClient) -> None:
        super().__init__()
        self.client = client
        self.failures: list[BaseException] = []

    def reset(self) -> None:
        self.failures.clear()

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
        options: dict[str, Any] | None = None,
    ) -> BaseModel | str:
        try:
            return await self.client.generate(
                system_prompt, user_prompt, response_schema, options
            )
        except BaseException as exc:  # registrado e repropagado, nunca absorvido
            self.failures.append(exc)
            raise


def target_portfolio_to_intents(
    observation: MarketObservation,
    target_weights: Mapping[str, float] | Iterable[tuple[str, float]],
) -> list[OrderIntent]:
    """Valida uma carteira-alvo **completa** e a converte em intents.

    Uma decisão de carteira declara um peso para cada ativo do universo
    observado. Ticker omitido é decisão inválida — não significa manter
    posição, não significa peso zero e não autoriza o executor a inferir nada.
    Peso zero é uma decisão explícita e precisa ser escrita.

    Nada é normalizado: soma acima de um, peso fora de ``[0, 1]``, valor não
    finito, ticker desconhecido e ticker duplicado falham. O caixa é implícito
    em ``1 - Σ pesos``.
    """
    pairs = (
        list(target_weights.items())
        if isinstance(target_weights, Mapping)
        else list(target_weights)
    )
    weights: dict[str, float] = {}
    for raw_ticker, raw_weight in pairs:
        ticker = str(raw_ticker).strip()
        if not ticker:
            raise LLMDecisionError("target portfolio contains an empty ticker")
        if ticker in weights:
            raise LLMDecisionError(f"duplicate ticker in target portfolio: {ticker}")
        weight = float(raw_weight)
        if not math.isfinite(weight):
            raise LLMDecisionError(f"target weight for {ticker} must be finite")
        if weight < 0 or weight > 1:
            raise LLMDecisionError(
                f"target weight for {ticker} must be between 0 and 1; "
                "shorting and leverage are not supported"
            )
        weights[ticker] = weight

    universe = set(observation.history)
    unknown = sorted(set(weights) - universe)
    if unknown:
        raise LLMDecisionError(
            f"target portfolio references unknown ticker(s): {', '.join(unknown)}"
        )
    missing = sorted(universe - set(weights))
    if missing:
        raise LLMDecisionError(
            f"target portfolio omits {', '.join(missing)}; a portfolio decision "
            "must declare a weight for every observed ticker, zero included"
        )
    if sum(weights.values()) > 1 + WEIGHT_TOLERANCE:
        raise LLMDecisionError(
            "target weights must sum to at most 1; leverage is not supported"
        )
    return weights_to_intents(observation, weights)


class LLMParticipant:
    """Adapta o grafo multiagente ao contrato ``Participant`` da arena.

    Recebe apenas ``MarketObservation``: histórico truncado em ``close(t)``,
    posições, caixa e patrimônio. Não conhece o dataset, o snapshot, a próxima
    sessão nem o tamanho do recorte, então não consegue identificar o fim da
    amostra experimental.

    **Tradução de decisão para peso alvo.** O pipeline atual produz
    ``COMPRA``/``VENDA``/``MANTER`` com ``position_size`` que é fração *da
    operação* — caixa disponível na compra, posição corrente na venda — e não
    um peso de carteira. A tradução aplicada aqui é a identidade aritmética
    "em que estado de carteira esta ordem quer chegar", avaliada com o
    fechamento de ``t``::

        COMPRA(s) -> (posição * close + s * caixa) / patrimônio
        VENDA(s)  -> (posição * close * (1 - s))   / patrimônio
        MANTER    -> nenhuma intenção

    Ela preserva o dimensionamento que o ``portfolio_manager`` já calcula
    (fractional Kelly sobre ``confidence``, teto de posição e folga de
    concentração), sem copiar essa regra para cá e sem declará-la como o sizing
    científico final — Kelly sobre *confidence* textual continua sendo uma
    decisão metodológica em aberto. Duas diferenças são declaradas: o peso
    alcançado difere do peso alvo porque a execução acontece na abertura de
    ``t+1``, a outro preço, e a tradução não desconta custos, que pertencem ao
    executor.

    **Ausência de intenção não é decisão parcial.** ``MANTER``, veto de risco e
    ausência de decisão final devolvem lista vazia: nenhuma decisão nova, e o
    executor mantém a posição — a mesma semântica que os cinco participantes
    clássicos já usam e que o motor legado de agentes aplicava. Quando há
    decisão, ela passa por :func:`target_portfolio_to_intents` e cobre o
    universo inteiro.

    ``MANTER`` deliberadamente **não** vira ``target_weight`` igual ao peso
    observado no fechamento. Peso é alvo, não posição: reemitir o peso corrente
    faria o executor recalcular a quantidade alvo sobre o patrimônio da
    abertura seguinte e, depois de um gap, isso exigiria comprar ou vender.
    "Não fazer nada" precisa ser a ausência de ordem, como no motor legado, e
    não um rebalance disfarçado. Esta regra é do participante single-asset
    migrado; a decisão de carteira-alvo completa para o futuro LLM multi-ativo
    não muda por causa dela.

    **Frequência de decisão.** ``decision_frequency`` migra a mesma opção do
    ``AgentBacktestEngine``: só as sessões cujo índice é múltiplo dela chamam o
    grafo. O contador é interno, começa em zero a cada instância e é reiniciado
    quando a observação mostra a primeira sessão do recorte; ele nunca deriva
    do tamanho do dataset, da próxima sessão nem da distância até o fim. Uma
    diferença em relação ao motor legado é declarada: lá a última barra era
    sempre elegível (``is_last_day``), o que exige saber que o recorte acabou —
    informação que o contrato da arena não entrega e que o participante não
    pode ter.

    **Falha não vira HOLD.** Timeout, erro de provedor, JSON inválido, schema
    inválido e quorum incompletado por falhas são registrados no limite do
    provedor e levantam :class:`LLMDecisionError`; o run falha. Quorum sem
    supermaioria com todos os votos válidos continua sendo ``MANTER``, porque
    aí não houve falha nenhuma: é a regra de agregação da metodologia atual.
    """

    def __init__(
        self,
        ticker: str,
        *,
        provider: str = "mock",
        model: str = "",
        retry_attempts: int = 3,
        retry_base_delay: float = 0.5,
        analyst_count: int = 30,
        consensus_threshold: float = 5 / 6,
        require_all_votes: bool = True,
        temperature_min: float = 0.2,
        temperature_max: float = 0.8,
        seed_base: int = 10_000,
        risk_max_volatility: float = 0.50,
        risk_max_drawdown: float = 0.25,
        risk_max_concentration: float = 0.30,
        kelly_fraction: float = 0.50,
        max_position_size: float = 0.25,
        portfolio_max_concentration: float = 0.30,
        volatility_window: int = 21,
        payoff_ratio: float = 1.0,
        decision_frequency: int = 1,
        llm_client: LLMClient | None = None,
    ) -> None:
        if not ticker.strip():
            raise ValueError("ticker cannot be empty")
        if volatility_window < 2:
            raise ValueError("volatility_window must be >= 2")
        if decision_frequency < 1:
            raise ValueError("decision_frequency must be >= 1")
        if payoff_ratio <= 0 or not math.isfinite(payoff_ratio):
            raise ValueError("payoff_ratio must be finite and > 0")
        if retry_attempts < 1:
            raise ValueError("retry_attempts must be >= 1")
        if retry_base_delay < 0 or not math.isfinite(retry_base_delay):
            raise ValueError("retry_base_delay must be finite and >= 0")

        self.ticker = ticker.strip()
        self.provider = provider
        self.model = model
        self.retry_attempts = retry_attempts
        self.retry_base_delay = retry_base_delay
        self.volatility_window = volatility_window
        self.payoff_ratio = float(payoff_ratio)
        self.decision_frequency = decision_frequency

        self.ensemble_config = AnalystEnsembleConfig(
            analyst_count=analyst_count,
            consensus_threshold=consensus_threshold,
            require_all_votes=require_all_votes,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
            seed_base=seed_base,
        )
        self.risk_config = RiskConfig(
            max_volatility=risk_max_volatility,
            max_drawdown=risk_max_drawdown,
            max_concentration=risk_max_concentration,
        )
        self.portfolio_config = PortfolioConfig(
            kelly_fraction=kelly_fraction,
            max_position_size=max_position_size,
            max_concentration=portfolio_max_concentration,
        )

        # Cliente injetado é usado como está: o teste controla a stack inteira.
        base = llm_client if llm_client is not None else self._build_client()
        self.client = FailureRecordingClient(base)
        self.graph = build_graph(
            self.client,
            risk_config=self.risk_config,
            portfolio_config=self.portfolio_config,
            ensemble_config=self.ensemble_config,
        )
        self.transformer = DataTransformer()
        # Estado interno de uma execução, nunca compartilhado entre runs: a
        # factory do registry devolve instância nova a cada run.
        self.decisions: list[LLMDecisionRecord] = []
        self._peak_equity: float | None = None
        self._session_index = 0

    # ── Construção do cliente ────────────────────────────────────

    def _build_client(self) -> LLMClient:
        """Resolve o provedor declarado na spec; credencial vem do ambiente."""
        if self.provider == "mock":
            return _mock_client()
        if self.provider == "agent_router":
            if not self.model.strip():
                raise ValueError(
                    "provider 'agent_router' requires an explicit model; the "
                    "requested model is provenance and must appear in the spec"
                )
            # Import local: o cliente HTTP só é necessário no caminho real.
            from src.agents.llm_client import AgentRouterLLMClient, RetryingLLMClient

            client: LLMClient = AgentRouterLLMClient(model=self.model)
            if self.retry_attempts > 1:
                client = RetryingLLMClient(
                    client,
                    max_attempts=self.retry_attempts,
                    base_delay=self.retry_base_delay,
                )
            return client
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(
            f"unsupported llm provider: {self.provider!r}; supported: {supported}"
        )

    # ── Contrato da arena ────────────────────────────────────────

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        history = observation.history.get(self.ticker)
        if history is None:
            raise LLMDecisionError(f"observation missing ticker: {self.ticker}")
        if set(observation.history) != {self.ticker}:
            others = ", ".join(sorted(set(observation.history) - {self.ticker}))
            raise LLMDecisionError(
                f"{type(self).__name__} is single-asset and cannot reason across "
                f"assets; the observed universe also contains {others}. A "
                "per-ticker loop would be a different strategy, not this one"
            )

        equity = float(observation.equity)
        if not math.isfinite(equity) or equity <= 0:
            raise LLMDecisionError("observation equity must be finite and > 0")
        # Primeira sessão do recorte: reinicia pico e contador como o motor
        # legado, que partia do capital inicial — sem posição, patrimônio é o
        # capital — e do índice zero.
        if len(history) == 1:
            self._peak_equity = None
            self._session_index = 0
        # O pico acompanha *todas* as sessões, elegíveis ou não: o drawdown é
        # estado de portfólio, não subproduto da frequência de decisão.
        self._peak_equity = (
            equity if self._peak_equity is None else max(self._peak_equity, equity)
        )
        session_index = self._session_index
        self._session_index += 1
        if session_index % self.decision_frequency != 0:
            # Sessão não elegível: nenhuma chamada ao provedor e nenhuma
            # intenção nova. A posição corrente segue pela semântica normal da
            # arena, que mantém quem não recebe intent.
            return []

        close = float(cast(pd.Series, history["fechamento"]).iloc[-1])
        state = self._agent_state(observation, history, equity, close)
        self.client.reset()
        output = cast(dict, asyncio.run(self.graph.ainvoke(state)))
        failures = tuple(
            f"{type(error).__name__}: {error}" for error in self.client.failures
        )

        decision = output.get("final_decision")
        errors = tuple(str(error) for error in output.get("errors", []))
        weight = (
            self._target_weight(decision, observation, close)
            if decision is not None and decision.decision != "MANTER" and not failures
            else None
        )
        self.decisions.append(
            LLMDecisionRecord(
                session=observation.session,
                technical_signal=output.get("technical_signal"),
                consensus=output.get("technical_consensus"),
                risk_verdict=output.get("risk_verdict"),
                final_decision=decision,
                target_weight=weight,
                errors=errors,
                llm_failures=failures,
            )
        )

        if failures:
            raise LLMDecisionError(
                f"unrecovered LLM failure while deciding "
                f"{observation.session.date()}: {'; '.join(failures)}"
            )
        if weight is None:
            return []
        return target_portfolio_to_intents(observation, {self.ticker: weight})

    # ── Estado observável ────────────────────────────────────────

    def _agent_state(
        self,
        observation: MarketObservation,
        history: pd.DataFrame,
        equity: float,
        close_price: float,
    ) -> AgentState:
        """Monta o ``AgentState`` usando somente informação de ``close(t)``.

        Os indicadores são recalculados sobre o histórico truncado com a mesma
        função do pipeline. Como todos eles são varreduras para frente
        (``rolling`` e ``ewm(adjust=False)``), o valor em ``t`` é idêntico ao
        que a série inteira produziria — a diferença é que aqui não existe
        barra futura para observar.
        """
        close = cast(pd.Series, history["fechamento"])
        with_indicators = self.transformer.calculate_indicators(history)
        row = with_indicators.iloc[-1]
        indicators: dict[str, float | None] = {
            key: float(row[key])
            for key in INDICATOR_KEYS
            if key in with_indicators.columns and pd.notna(row[key])
        }

        returns = close.pct_change().dropna().tail(self.volatility_window)
        volatility = (
            float(returns.std(ddof=1) * math.sqrt(TRADING_DAYS_PER_YEAR))
            if len(returns) >= 2
            else None
        )
        peak = self._peak_equity or equity
        state: AgentState = {
            "ticker": self.ticker,
            "date": str(observation.session.date()),
            "indicators": indicators,
            "cash": float(observation.cash),
            "position": float(observation.positions[self.ticker]),
            "current_price": close_price,
            "equity": equity,
            "current_drawdown": (peak - equity) / peak,
            "payoff_ratio": self.payoff_ratio,
            "errors": [],
        }
        if volatility is not None:
            state["recent_volatility"] = volatility
        return state

    # ── Tradução para peso alvo ──────────────────────────────────

    def _target_weight(
        self,
        decision: FinalDecision,
        observation: MarketObservation,
        close: float,
    ) -> float:
        exposure = float(observation.positions[self.ticker]) * close
        size = float(decision.position_size)
        if decision.decision == "COMPRA":
            target_value = exposure + size * float(observation.cash)
        else:
            target_value = exposure * (1.0 - size)
        weight = target_value / float(observation.equity)
        if (
            not math.isfinite(weight)
            or weight < -WEIGHT_TOLERANCE
            or weight > 1 + WEIGHT_TOLERANCE
        ):
            raise LLMDecisionError(
                f"translated target weight {weight!r} is outside [0, 1]"
            )
        # Apenas resíduo de ponto flutuante é aparado; nenhum peso é
        # normalizado para caber em um limite econômico.
        return min(1.0, max(0.0, weight))
