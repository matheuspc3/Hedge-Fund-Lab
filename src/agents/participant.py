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
    PortfolioAction (COMPRA/VENDA/MANTER, sem quantidade)
            |
            v
    política determinística de sizing  -> target_weight
            |
            v
    carteira-alvo completa sobre o universo observado
            |
            v
    OrderIntent(target_weight)  -- ExecutionEngine na abertura de t+1

O participante termina em peso alvo. Quantidade, direção, preço de execução,
custo, caixa e ``Trade`` continuam sendo exclusividade do ``ExecutionEngine``:
nada aqui reimplementa o motor financeiro.

**Qualidade da decisão e tamanho da posição são coisas separadas.** O LLM
decide a direção; quanto expor é política determinística e configurável
(:class:`FixedTargetSizing`), fora do alcance do modelo. Este participante usa
sempre o modo científico do gestor de portfólio
(``sizing_mode="qualitative"``), portanto nunca chama a fractional Kelly e
nunca consome a ``confidence`` textual como número.

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
from src.agents.llm_client import LLMCallMetadata, LLMClient, MockLLMClient
from src.agents.llm_trace import LLMCallRecord, RecordingLLMClient
from src.agents.portfolio_manager import SIZING_MODE_QUALITATIVE, PortfolioConfig
from src.agents.risk_manager import RiskConfig
from src.agents.state import (
    AgentState,
    PortfolioAction,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
)
from src.agents.technical_analyst import INDICATOR_KEYS, AnalystEnsembleConfig
from src.artifacts import RunArtifact
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

#: Default **técnico** de ``long_target_weight``, não valor científico.
#:
#: 0.25 é o antigo teto ``max_position_size`` do gestor de portfólio, adotado
#: aqui só para manter testes e API convenientes sem inventar um número novo.
#:
#: .. code-block:: text
#:
#:     technical default      = 0.25
#:     scientific frozen value = TBD  (EXPERIMENT PROTOCOL v1)
#:
#: Ele nunca foi aprovado metodologicamente e não pode ser citado como tal.
DEFAULT_LONG_TARGET_WEIGHT = 0.25


def _require_int(name: str, value: Any, *, minimum: int) -> int:
    """Exige um inteiro de verdade, com mínimo, antes de qualquer comparação.

    ``value < minimum`` sozinho não serve como validação: ``2.5 < 2`` é falso,
    então uma janela fracionária passaria; e ``bool`` é subclasse de ``int``,
    então ``True`` passaria valendo 1. Ambos são configuração inválida sendo
    aceita em silêncio, e configuração inválida vira ``spec_hash`` e manifest.

    ``analyst_count`` e ``seed_base`` também passam por aqui. Pydantic já
    rejeita ``2.5`` neles, mas **converte** ``True`` em ``1`` no modo padrão;
    esta função fecha exatamente essa borda, sem duplicar o resto.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f"{name} must be an integer, got {type(value).__name__}: {value!r}"
        )
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _validate_long_target_weight(value: Any, risk_max_concentration: float) -> float:
    """Exige um peso alvo long viável e coerente com o limite duro de risco.

    Duas validações, com motivos distintos:

    ``0 < weight <= 1``
        O projeto é long-only e sem alavancagem. Zero não é "manter": seria uma
        estratégia que nunca se expõe, e declará-la assim por engano de
        configuração é pior que recusar. Acima de 1 é alavancagem, que o
        contrato de carteira-alvo já proíbe.

    ``weight <= risk_max_concentration``
        Configuração em que o sizing determinístico manda construir exatamente
        a exposição que o gestor de risco existe para vetar é contraditória: o
        participante pediria todo pregão um alvo que a regra dura recusa, e o
        run silenciosamente viraria "quase nunca opera" em vez de falhar. O
        limite de risco é o teto; o alvo tem de caber embaixo dele.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(
            f"long_target_weight must be a number, got {type(value).__name__}"
        )
    weight = float(value)
    if not math.isfinite(weight):
        raise ValueError("long_target_weight must be finite")
    if weight <= 0 or weight > 1:
        raise ValueError(
            "long_target_weight must be > 0 and <= 1; this participant is "
            "long-only and unlevered"
        )
    if weight > float(risk_max_concentration):
        raise ValueError(
            f"long_target_weight {weight} exceeds risk_max_concentration "
            f"{risk_max_concentration}; the deterministic target would build an "
            "exposure the hard risk rule exists to veto"
        )
    return weight


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
    portfolio_action: PortfolioAction | None
    target_weight: float | None
    errors: tuple[str, ...] = ()
    llm_failures: tuple[str, ...] = ()


@dataclass(frozen=True)
class FixedTargetSizing:
    """Política de sizing determinística: alvo fixo para exposição long.

    Traduz **decisão qualitativa** em **estado desejado de carteira**::

        COMPRA -> long_target_weight
        VENDA  -> 0.0
        MANTER -> None  (nenhuma intenção nova)

    Deliberadamente simples, porque o participante é single-asset e long-only.
    Nada aqui olha ``confidence``, preço, caixa, posição corrente ou próxima
    abertura: o alvo é o mesmo estado desejado, e traduzi-lo em compra ou venda
    concreta é trabalho do ``ExecutionEngine`` em ``open(t+1)``.

    Ela é a primeira de uma família prevista (``fixed_target``,
    ``volatility_target``, ``calibrated_kelly``); as outras **não** existem e
    não são simuladas. O que este tipo garante é o ponto de troca: o
    participante consulta uma política, não uma fórmula embutida.
    """

    long_target_weight: float

    def target_weight(self, decision: str) -> float | None:
        if decision == "COMPRA":
            return self.long_target_weight
        if decision == "VENDA":
            return 0.0
        return None


def _mock_client() -> MockLLMClient:
    """Cliente determinístico com respostas válidas para cada schema.

    Reutiliza ``MockLLMClient``: o default dele (``"MANTER"`` como texto) não
    valida contra nenhum schema, então as respostas são declaradas aqui.

    As respostas são ``dict``, não instâncias Pydantic: ``MockLLMClient``
    devolveria uma instância pré-construída por referência, compartilhada entre
    sessões. O ``dict`` faz cada chamada validar um objeto novo.
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
            PortfolioAction: {
                "decision": "COMPRA",
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
        *,
        metadata: LLMCallMetadata | None = None,
    ) -> BaseModel | str:
        try:
            return await self.client.generate(
                system_prompt, user_prompt, response_schema, options, metadata=metadata
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

    **Decisão qualitativa, sizing determinístico.** O grafo termina em
    :class:`~src.agents.state.PortfolioAction` — direção e justificativa, sem
    quantidade. O peso alvo sai de :class:`FixedTargetSizing`::

        COMPRA aprovada -> target_weight = long_target_weight
        VENDA  aprovada -> target_weight = 0.0
        MANTER          -> nenhuma intenção
        veto de risco   -> nenhuma intenção

    Nada nessa tradução depende de ``confidence``, de Kelly ou de qualquer
    número escolhido pelo LLM: duas execuções que só diferem na confiança
    reportada produzem exatamente o mesmo peso alvo. ``confidence`` continua
    existindo como saída do analista, como contexto qualitativo dos agentes
    seguintes e como variável de análise no trace — ela apenas não entra em
    fórmula de dimensionamento.

    **``COMPRA`` é estado desejado, não ordem de compra.** Emitir
    ``target_weight = long_target_weight`` significa *querer estar exposto
    naquele peso*, e não que o trade físico em ``open(t+1)`` será ``BUY``. Com
    exposição corrente abaixo do alvo o executor compra; depois de um gap de
    alta que empurre a exposição acima do alvo, o mesmo alvo exige vender. A
    direção financeira concreta nasce na abertura e pertence à arena; o
    participante não declara ``side``. Duas diferenças seguem declaradas: o peso
    alcançado difere do alvo porque a execução acontece a outro preço, e o alvo
    não desconta custos, que são do executor.

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
        long_target_weight: float = DEFAULT_LONG_TARGET_WEIGHT,
        volatility_window: int = 21,
        decision_frequency: int = 1,
        llm_client: LLMClient | None = None,
    ) -> None:
        if not ticker.strip():
            raise ValueError("ticker cannot be empty")
        volatility_window = _require_int(
            "volatility_window", volatility_window, minimum=2
        )
        decision_frequency = _require_int(
            "decision_frequency", decision_frequency, minimum=1
        )
        retry_attempts = _require_int("retry_attempts", retry_attempts, minimum=1)
        analyst_count = _require_int("analyst_count", analyst_count, minimum=1)
        seed_base = _require_int("seed_base", seed_base, minimum=0)
        if retry_base_delay < 0 or not math.isfinite(retry_base_delay):
            raise ValueError("retry_base_delay must be finite and >= 0")
        long_target_weight = _validate_long_target_weight(
            long_target_weight, risk_max_concentration
        )

        self.ticker = ticker.strip()
        self.provider = provider
        self.model = model
        self.retry_attempts = retry_attempts
        self.retry_base_delay = retry_base_delay
        self.volatility_window = volatility_window
        self.decision_frequency = decision_frequency
        self.long_target_weight = long_target_weight
        self.sizing = FixedTargetSizing(long_target_weight)

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
        # Modo científico, sempre: o participante da arena nunca executa o
        # caminho de Kelly sobre ``confidence``, nem por configuração.
        self.portfolio_config = PortfolioConfig(sizing_mode=SIZING_MODE_QUALITATIVE)

        # Cliente injetado é usado como está: o teste controla a stack inteira.
        base = llm_client if llm_client is not None else self._build_client()
        self.client = FailureRecordingClient(base)
        # Camada de gravação por fora de tudo. A ordem é declarada em
        # ``RecordingLLMClient``: acima do retry para registrar chamadas
        # lógicas em vez de tentativas, e acima do observador de falha para que
        # a falha final entre no trace antes de subir para cá.
        self.trace = RecordingLLMClient(
            self.client, provider=self.provider, requested_model=self.model
        )
        self.graph = build_graph(
            self.trace,
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
        # A sessão de decisão é declarada pelo participante, que é quem a
        # conhece; nenhuma camada abaixo a deduz da ordem das chamadas.
        self.trace.begin_session(observation.session)
        self.client.reset()
        output = cast(dict, asyncio.run(self.graph.ainvoke(state)))
        failures = tuple(
            f"{type(error).__name__}: {error}" for error in self.client.failures
        )

        action = output.get("portfolio_action")
        errors = tuple(str(error) for error in output.get("errors", []))
        # Sizing só é consultado quando existe decisão qualitativa e nenhuma
        # falha: veto de risco e ``MANTER`` sequer chegam até aqui com ação
        # acionável, e falha de infraestrutura não vira decisão.
        weight = (
            self.sizing.target_weight(action.decision)
            if action is not None and not failures
            else None
        )
        self.decisions.append(
            LLMDecisionRecord(
                session=observation.session,
                technical_signal=output.get("technical_signal"),
                consensus=output.get("technical_consensus"),
                risk_verdict=output.get("risk_verdict"),
                portfolio_action=action,
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

    # ── Evidência do run ─────────────────────────────────────────

    @property
    def llm_calls(self) -> tuple[LLMCallRecord, ...]:
        """Trace desta execução, em ordem de emissão."""
        return self.trace.records

    def run_artifacts(self) -> tuple[RunArtifact, ...]:
        """Congela o trace para publicação junto do run.

        Satisfaz ``RunArtifactProvider`` estruturalmente: a camada
        experimental publica esta evidência sem conhecer este tipo. Os bytes
        saem daqui prontos — publicar o run não reconsulta provedor, cliente
        nem estado externo, pela mesma razão que ``SnapshotEvidence`` existe.
        """
        return (self.trace.artifact(),)

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
            # ``payoff_ratio`` é insumo exclusivo da fórmula de Kelly do modo
            # legado. O caminho científico não o produz para que não haja
            # parâmetro morto fingindo ser material.
            "errors": [],
        }
        if volatility is not None:
            state["recent_volatility"] = volatility
        return state
