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
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence, cast

import pandas as pd
from pydantic import BaseModel, ValidationError

from src.agents.features import FEATURE_KEYS, canonical_number, dimensionless_features
from src.agents.graph import build_graph
from src.agents.llm_client import (
    METADATA_ONLY_OPTIONS,
    AgentRouterLLMClient,
    GeminiLLMClient,
    LLMCallMetadata,
    LLMClient,
    MockLLMClient,
    ProviderRequestRejected,
    RetryingLLMClient,
)
from src.agents.llm_trace import LLMCallRecord, RecordingLLMClient, session_key
from src.agents.portfolio_manager import (
    PORTFOLIO_RULE_DIRECTION_INVERSION,
    PORTFOLIO_RULE_INVALID_RESPONSE,
    PORTFOLIO_RULE_MISSING_INPUT,
    PORTFOLIO_SOURCE_LLM,
    SIZING_MODE_QUALITATIVE,
    PortfolioConfig,
)
from src.agents.risk_manager import (
    RISK_RULE_CONCENTRATION,
    RISK_RULE_DRAWDOWN,
    RISK_RULE_INVALID_RESPONSE,
    RISK_RULE_MISSING_METRICS,
    RISK_RULE_MISSING_SIGNAL,
    RISK_RULE_VOLATILITY,
    RISK_SOURCE_LLM,
    RiskConfig,
)
from src.agents.state import (
    AgentState,
    PortfolioAction,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
)
from src.agents.technical_analyst import INDICATOR_KEYS, AnalystEnsembleConfig
from src.artifacts import RunArtifact, canonical_json
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
#: se confunde com um run científico. ``gemini`` é a Gemini API nativa, runtime
#: científico recomendado (escolha de provedor/modelo:
#: ``PENDING_ADVISOR_RATIFICATION``).
SUPPORTED_PROVIDERS = ("mock", "agent_router", "gemini")

#: Cliente concreto de cada provedor real, consultado pelo preflight de
#: capacidades **sem** instanciar nada nem fazer rede. ``mock`` não está aqui:
#: dublê de teste não faz afirmação semântica sobre opção alguma.
PROVIDER_CLIENTS: Mapping[str, type[LLMClient]] = {
    "agent_router": AgentRouterLLMClient,
    "gemini": GeminiLLMClient,
}

#: Vocabulário de ``thinking_level`` aceito na spec. Quais níveis um provedor
#: honra é capacidade do cliente concreto, conferida no preflight.
THINKING_LEVEL_VOCABULARY = ("minimal", "low", "medium", "high")

#: O que fazer quando o gestor de portfólio devolve a direção oposta ao sinal
#: aprovado. Nos dois casos a sessão é classificada ``INVALID_RESPONSE``, nunca
#: ``PORTFOLIO_HOLD``. ``flag`` mantém o comportamento herdado (nenhuma
#: intenção, run segue); ``fail`` derruba o run. Qual vale no H2 é
#: ``PENDING_ADVISOR_RATIFICATION``.
PORTFOLIO_INVERSION_POLICIES = ("flag", "fail")

#: Parâmetros que uma spec científica de ``llm_agent`` precisa escrever,
#: qualquer que seja o provedor. Os dependentes do provedor (``model``,
#: ``max_output_tokens``, ``thinking_level``) são acrescentados no preflight.
#: Omitido não significa "default": significa spec recusada.
SCIENTIFIC_REQUIRED_PARAMS = (
    "provider",
    "temperature",
    "analyst_count",
    "consensus_threshold",
    "require_all_votes",
    "decision_frequency",
    "strict_inputs",
    "portfolio_inversion_policy",
)

# ── Causa final de uma sessão consultada ─────────────────────────
#
# Código estruturado, derivado dos campos que cada etapa devolve — nunca de
# texto livre. Falha técnica (``INVALID_*``, ``PROVIDER_*``) não é decisão
# de investimento e nunca é contada como prudência.

LLM_DECISION_ARTIFACT_SCHEMA_VERSION = 1
LLM_DECISION_ARTIFACT = "llm_decisions"
LLM_DECISION_FILENAME = "decisions.jsonl"

ACTION_BUY = "ACTION_BUY"
ACTION_SELL = "ACTION_SELL"
NOT_ELIGIBLE = "NOT_ELIGIBLE"
TECH_EXPLICIT_HOLD = "TECH_EXPLICIT_HOLD"
TECH_NO_MAJORITY = "TECH_NO_MAJORITY"
#: COMPRA com a carteira já no alvo: não há exposição a construir. Precede o
#: veto de risco porque, com ``long_target_weight = risk_max_concentration``,
#: a regra de concentração veta exatamente este caso — e vetar um no-op não é
#: prudência.
BUY_AT_TARGET_NOOP = "BUY_AT_TARGET_NOOP"
RISK_VETO_VOLATILITY = "RISK_VETO_VOLATILITY"
RISK_VETO_DRAWDOWN = "RISK_VETO_DRAWDOWN"
RISK_VETO_CONCENTRATION = "RISK_VETO_CONCENTRATION"
RISK_VETO_LLM = "RISK_VETO_LLM"
PORTFOLIO_HOLD = "PORTFOLIO_HOLD"
INVALID_INPUT = "INVALID_INPUT"
INVALID_RESPONSE = "INVALID_RESPONSE"
#: Falha transitória do provedor (rede, timeout, 429/5xx) que sobreviveu ao
#: retry. Não é a mesma coisa que a recusa abaixo.
PROVIDER_FAILURE = "PROVIDER_FAILURE"
#: Recusa determinística da requisição (HTTP 400/401/402/403/404, chave
#: ausente, opção não suportada): erro de contrato ou de configuração, não
#: queda do provedor, e nunca repetida.
PROVIDER_REQUEST_REJECTED = "PROVIDER_REQUEST_REJECTED"

FAILURE_CAUSES = frozenset(
    {INVALID_INPUT, INVALID_RESPONSE, PROVIDER_FAILURE, PROVIDER_REQUEST_REJECTED}
)
RISK_VETO_CAUSES = frozenset(
    {RISK_VETO_VOLATILITY, RISK_VETO_DRAWDOWN, RISK_VETO_CONCENTRATION, RISK_VETO_LLM}
)
_HARD_RULE_VETOES = {
    RISK_RULE_VOLATILITY: RISK_VETO_VOLATILITY,
    RISK_RULE_DRAWDOWN: RISK_VETO_DRAWDOWN,
    RISK_RULE_CONCENTRATION: RISK_VETO_CONCENTRATION,
}

#: Resultado técnico quando o quorum não ficou completo — só acontece junto
#: de falha, e falha derruba o run.
TECH_OUTCOME_INCOMPLETE = "INCOMPLETE"
TECH_OUTCOME_NO_MAJORITY = "NO_MAJORITY"

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

    Cobre falha não recuperada no limite do provedor, resposta que viola o
    contrato, entrada científica incompleta e saída que viola o contrato de
    carteira-alvo. Nunca vira ``MANTER``: infraestrutura quebrada e decisão de
    investimento são coisas diferentes. ``reason`` carrega a causa estruturada
    (``INVALID_INPUT``, ``INVALID_RESPONSE``, ``PROVIDER_FAILURE``,
    ``PROVIDER_REQUEST_REJECTED``) quando há.
    """

    def __init__(self, message: str, reason: str | None = None) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class LLMDecisionRecord:
    """Trilha de uma decisão consultada, publicada em ``decisions.jsonl``.

    Os campos estruturados (``final_cause``, fontes e regras de risco e de
    portfólio, ``observed_weight``) bastam para dizer *por que* a sessão
    terminou como terminou sem ler texto livre; ``errors`` e ``llm_failures``
    ficam como evidência, nunca como insumo de classificação.
    """

    session: pd.Timestamp
    technical_signal: TechnicalSignal | None
    consensus: TechnicalConsensus | None
    risk_verdict: RiskVerdict | None
    portfolio_action: PortfolioAction | None
    target_weight: float | None
    errors: tuple[str, ...] = ()
    llm_failures: tuple[str, ...] = ()
    final_cause: str | None = None
    risk_source: str | None = None
    risk_rule: str | None = None
    portfolio_source: str | None = None
    portfolio_rule: str | None = None
    #: Peso do ativo no fechamento de ``t``, antes da decisão.
    observed_weight: float | None = None
    input_violations: tuple[str, ...] = ()

    @property
    def technical_outcome(self) -> str | None:
        """``COMPRA``/``VENDA``/``MANTER`` com maioria, ou o motivo de não ter."""
        consensus = self.consensus
        if consensus is None:
            return None
        if consensus.valid_votes < consensus.total_analysts:
            return TECH_OUTCOME_INCOMPLETE
        if not consensus.consensus_reached:
            return TECH_OUTCOME_NO_MAJORITY
        return consensus.winning_signal

    @property
    def portfolio_called(self) -> bool:
        return self.portfolio_source == PORTFOLIO_SOURCE_LLM

    def to_json_dict(self, ticker: str) -> dict[str, Any]:
        consensus = self.consensus
        return {
            "schema_version": LLM_DECISION_ARTIFACT_SCHEMA_VERSION,
            "decision_session": session_key(self.session),
            "ticker": ticker,
            "eligible": True,
            "vote_counts": None if consensus is None else dict(consensus.counts),
            "valid_votes": None if consensus is None else consensus.valid_votes,
            "analyst_count": None if consensus is None else consensus.total_analysts,
            "consensus_threshold": None if consensus is None else consensus.threshold,
            "consensus_reached": None
            if consensus is None
            else consensus.consensus_reached,
            "technical_outcome": self.technical_outcome,
            "risk_verdict": None
            if self.risk_verdict is None
            else self.risk_verdict.verdict,
            "risk_source": self.risk_source,
            "risk_rule": self.risk_rule,
            "portfolio_called": self.portfolio_called,
            "portfolio_source": self.portfolio_source,
            "portfolio_rule": self.portfolio_rule,
            "portfolio_decision": (
                None if self.portfolio_action is None else self.portfolio_action.decision
            ),
            "observed_weight": self.observed_weight,
            "target_weight": self.target_weight,
            "final_cause": self.final_cause,
            "input_violations": list(self.input_violations),
            "errors": list(self.errors),
            "failures": list(self.llm_failures),
        }


def classify_decision(
    *,
    consensus: TechnicalConsensus | None,
    risk_verdict: RiskVerdict | None,
    risk_source: str | None,
    risk_rule: str | None,
    portfolio_action: PortfolioAction | None,
    portfolio_rule: str | None,
    observed_weight: float | None,
    long_target_weight: float,
    input_violations: Sequence[str] = (),
    failures: Sequence[BaseException] = (),
) -> str:
    """Causa final de uma sessão consultada, só a partir de campos estruturados.

    A ordem é a precedência: falha técnica antes de qualquer decisão, e
    ``BUY_AT_TARGET_NOOP`` antes do veto de risco. Falha é classificada pelo
    **tipo**: :class:`ProviderRequestRejected` (recusa determinística, nunca
    repetida) é ``PROVIDER_REQUEST_REJECTED``; ``OSError`` — que cobre
    ``ProviderTransportError``, ``ConnectionError`` e ``TimeoutError``, já
    esgotado o retry — é ``PROVIDER_FAILURE``; qualquer outra falha registrada
    é resposta inválida.

    ``BUY_AT_TARGET_NOOP`` exige duas coisas: o peso observado igual ao alvo
    **na mesma representação canônica que a regra de concentração usa** e
    nenhuma intenção executável. Uma COMPRA aprovada no alvo ainda vira
    ``OrderIntent``; com caixa na carteira o peso deriva até a abertura e o
    executor rebalanceia — isso é ``ACTION_BUY``, não no-op.
    """
    if (
        input_violations
        or risk_rule in (RISK_RULE_MISSING_SIGNAL, RISK_RULE_MISSING_METRICS)
        or portfolio_rule == PORTFOLIO_RULE_MISSING_INPUT
    ):
        return INVALID_INPUT
    if any(isinstance(failure, ProviderRequestRejected) for failure in failures):
        return PROVIDER_REQUEST_REJECTED
    if any(isinstance(failure, OSError) for failure in failures):
        return PROVIDER_FAILURE
    if (
        failures
        or consensus is None
        or consensus.valid_votes < consensus.total_analysts
        or risk_rule == RISK_RULE_INVALID_RESPONSE
        or portfolio_rule
        in (PORTFOLIO_RULE_INVALID_RESPONSE, PORTFOLIO_RULE_DIRECTION_INVERSION)
    ):
        return INVALID_RESPONSE
    if not consensus.consensus_reached:
        return TECH_NO_MAJORITY
    if consensus.winning_signal == "MANTER":
        return TECH_EXPLICIT_HOLD
    at_target = observed_weight is not None and canonical_number(
        observed_weight
    ) == canonical_number(long_target_weight)
    emits_buy = portfolio_action is not None and portfolio_action.decision == "COMPRA"
    if consensus.winning_signal == "COMPRA" and at_target and not emits_buy:
        return BUY_AT_TARGET_NOOP
    if risk_verdict is not None and risk_verdict.verdict == "VETADO":
        if risk_source == RISK_SOURCE_LLM:
            return RISK_VETO_LLM
        return _HARD_RULE_VETOES.get(cast(str, risk_rule), INVALID_RESPONSE)
    if portfolio_action is None:
        return INVALID_RESPONSE
    if portfolio_action.decision == "MANTER":
        return PORTFOLIO_HOLD
    return ACTION_BUY if portfolio_action.decision == "COMPRA" else ACTION_SELL


#: Status de capacidade de um par (provedor, modelo).
CAPABILITY_NOT_APPLICABLE = "NOT_APPLICABLE"
CAPABILITY_DECLARED_UNQUALIFIED = "DECLARED_UNQUALIFIED"
CAPABILITY_QUALIFIED = "QUALIFIED"

#: Qualificação **empírica** por ``(provider, model)``: as opções que um
#: LIVE_SMOKE registrado (evidência versionada, data, modelo resolvido)
#: mostrou serem aceitas por aquele modelo. Uma entrada nova é decisão
#: registrada com evidência, nunca inferência de ``DECLARED_OPTIONS``.
#:
#: ``thinking_level`` é qualificado **por nível** (``thinking_level:<nível>``):
#: aceitar ``low`` não prova ``medium`` nem ``high``. Qualificação técnica de
#: transporte não é escolha científica de nível.
EMPIRICALLY_QUALIFIED: Mapping[tuple[str, str], frozenset[str]] = MappingProxyType(
    {
        # DEV_SMOKE 2026-10-04, API nativa v1beta generateContent: técnico,
        # risco e portfólio com HTTP 200, finishReason STOP e schema validado;
        # thinkingLevel validado pelo controle negativo. Arquivos em
        # EMPIRICAL_QUALIFICATION_EVIDENCE.
        ("gemini", "gemini-3.8-flash"): frozenset(
            {"temperature", "max_output_tokens", "thinking_level:low"}
        ),
    }
)

#: Evidência sanitizada que sustenta cada entrada de
#: :data:`EMPIRICALLY_QUALIFIED`, relativa à raiz do repositório.
EMPIRICAL_QUALIFICATION_EVIDENCE: Mapping[tuple[str, str], tuple[str, ...]] = MappingProxyType(
    {
        ("gemini", "gemini-3.8-flash"): (
            "docs/evidence/provider_runtime/gemini-3.8-flash_dev_smoke_20261004T191655Z.json",
            "docs/evidence/provider_runtime/gemini-3.8-flash_dev_smoke_20261004T191834Z.json",
            "docs/evidence/provider_runtime/gemini-3.8-flash_negative_control_20261004T191935Z.json",
        ),
    }
)


def _qualification_key(option: str, generation: Mapping[str, Any]) -> str:
    """Chave de qualificação de uma opção pedida; thinking é por nível."""
    if option == "thinking_level":
        return f"thinking_level:{generation['thinking_level']}"
    return option


@dataclass(frozen=True)
class CapabilityReport:
    """O que a spec pede ao provedor, em conjuntos que não se implicam.

    ``requested``      tudo o que o pipeline coloca em ``options``
    ``transported``    o que o cliente concreto sabe colocar no corpo HTTP
    ``declared``       o que o código do cliente afirma que o provedor honra
    ``qualified``      o que um LIVE_SMOKE mostrou ser honrado por ``model``
    ``metadata_only``  pedido, registrado no trace e nunca transmitido

    ``transported`` não implica ``declared``, e ``declared`` não implica
    ``qualified``. ``status`` é ``NOT_APPLICABLE`` para o ``mock`` (dublê que
    não faz afirmação semântica), ``QUALIFIED`` quando todo o pedido está
    qualificado para o modelo e ``DECLARED_UNQUALIFIED`` no resto.
    """

    provider: str
    model: str
    requested: tuple[str, ...]
    transported: tuple[str, ...]
    declared: tuple[str, ...]
    qualified: tuple[str, ...]
    metadata_only: tuple[str, ...]
    status: str


def generation_options(
    temperature: Any = None,
    thinking_level: Any = None,
    max_output_tokens: Any = None,
) -> dict[str, Any]:
    """Opções de geração declaradas, sem as ausentes."""
    declared = {
        "temperature": temperature,
        "thinking_level": thinking_level,
        "max_output_tokens": max_output_tokens,
    }
    return {key: value for key, value in declared.items() if value is not None}


def capability_report(
    provider: str, generation: Mapping[str, Any], model: str = ""
) -> CapabilityReport:
    """Confere localmente, sem rede, se o cliente declara o que a spec pede.

    Levanta ``ValueError`` em incompatibilidade: opção de geração pedida e não
    declarada (ou não transportada), opção de metadado que o cliente
    transmitiria, ou ``thinking_level`` fora dos níveis declarados. A
    qualificação empírica por modelo é só reportada aqui; quem a exige é o
    preflight científico.
    """
    # O quorum sempre pede temperatura, seed e analyst_id; risco e portfólio
    # pedem as opções de geração declaradas.
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(
            f"unsupported llm provider: {provider!r}; supported: {supported}"
        )
    requested = tuple(sorted({"temperature", *METADATA_ONLY_OPTIONS, *generation}))
    metadata_only = tuple(sorted(METADATA_ONLY_OPTIONS))
    client = PROVIDER_CLIENTS.get(provider)
    if client is None:
        return CapabilityReport(
            provider, model, requested, (), (), (), metadata_only,
            CAPABILITY_NOT_APPLICABLE,
        )

    transmitted = set(getattr(client, "TRANSMITTED_OPTION_KEYS", ()))
    declared = set(client.DECLARED_OPTIONS)
    leaked = sorted(METADATA_ONLY_OPTIONS & transmitted)
    if leaked:
        raise ValueError(
            f"provider {provider!r} would transmit metadata-only option(s) "
            f"{', '.join(leaked)}; seed and analyst_id never reach the provider"
        )
    wanted = set(requested) - METADATA_ONLY_OPTIONS
    missing = sorted(wanted - (declared & transmitted))
    if missing:
        raise ValueError(
            f"provider {provider!r} does not declare option(s) "
            f"{', '.join(missing)}; requested options would be dropped or "
            "misread instead of honored. Use a provider that declares them or "
            "remove the option from the spec"
        )
    levels = getattr(client, "THINKING_LEVELS", None)
    level = generation.get("thinking_level")
    if level is not None and levels is not None and level not in levels:
        raise ValueError(
            f"thinking_level {level!r} is not declared for provider "
            f"{provider!r}; declared levels: {', '.join(levels)}"
        )
    entries = EMPIRICALLY_QUALIFIED.get((provider, model), frozenset())
    qualified = {name for name in wanted if _qualification_key(name, generation) in entries}
    return CapabilityReport(
        provider,
        model,
        requested,
        tuple(sorted(wanted & transmitted)),
        tuple(sorted(wanted & declared)),
        tuple(sorted(qualified)),
        metadata_only,
        CAPABILITY_QUALIFIED if qualified == wanted else CAPABILITY_DECLARED_UNQUALIFIED,
    )


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
        from src.agents.technical_evidence import TechnicalEvidenceResponse, validate_technical_evidence
        try:
            response = await self.client.generate(
                system_prompt, user_prompt, response_schema, options, metadata=metadata
            )
            if response_schema is TechnicalEvidenceResponse:
                payload = json.loads(user_prompt)
                response = validate_technical_evidence(response, payload["features"], payload["allowed_evidence_codes"])
            return response
        except BaseException as exc:  # registrado e repropagado, nunca absorvido
            if response_schema is TechnicalEvidenceResponse and isinstance(exc, ValidationError):
                # The existing trace can reconstruct ValueError exactly, not Pydantic internals.
                failure = ValueError(str(exc))
                self.failures.append(failure)
                raise failure from exc
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
    sessão, o tamanho do recorte, a janela avaliada nem a fase do protocolo,
    então não consegue identificar o fim da amostra experimental.

    **Estado ancorado na janela avaliada, não no snapshot.** ``_peak_equity`` e
    o contador de ``decision_frequency`` nascem na primeira chamada a
    ``decide()``, que a arena emite em ``decision_start``. O warm-up anterior
    chega como histórico dentro de ``observation.history`` e não move nenhum
    dos dois: aumentar o warm-up não desloca a grade de decisão nem o
    drawdown observado.

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
    grafo. O contador é interno, começa em zero na primeira chamada a
    ``decide()`` — que a arena emite em ``decision_start`` — e nunca deriva do
    tamanho do dataset, da próxima sessão nem da distância até o fim. Logo
    ``decision_start`` é sempre elegível e a grade é
    ``decision_start + k * decision_frequency``, imune ao tamanho do warm-up.

    Uma diferença em relação ao motor legado é declarada: lá a última barra era
    sempre elegível (``is_last_day``), o que exige saber que o recorte acabou —
    informação que o contrato da arena não entrega e que o participante não
    pode ter. **Consequência assumida:** quando ``decision_end`` não cai na
    grade, ele é consultado e não emite intent, e a ``settlement_session``
    liquida o pendente da última decisão *efetivamente emitida* — ou nada, se
    não houver pendente. ``decision_end`` delimita a janela; não força decisão
    extraordinária, porque forçá-la exigiria exatamente o ``is_last_day`` que
    a causalidade da arena retirou.

    **Falha não vira HOLD.** Timeout, erro de provedor, JSON inválido, schema
    inválido e quorum incompletado por falhas são registrados no limite do
    provedor e levantam :class:`LLMDecisionError`; o run falha. Quorum sem
    supermaioria com todos os votos válidos continua sendo ``MANTER``, porque
    aí não houve falha nenhuma: é a regra de agregação da metodologia atual.

    **Entrada científica é fail-closed com ``strict_inputs=True``.** As oito
    features do contrato e a volatilidade sobre a janela inteira são
    obrigatórias; faltando qualquer uma, a sessão é ``INVALID_INPUT`` e o run
    falha antes de qualquer chamada ao provedor. O default ``False`` preserva
    os caminhos de teste e desenvolvimento com histórico curto — e o runner
    recusa fase científica sem ``strict_inputs=True``, pelo mesmo padrão com
    que recusa ``integer_shares``. Mesmo sem ``strict_inputs`` a sessão é
    classificada ``INVALID_INPUT``, nunca como prudência.

    **Opções de geração explícitas.** ``temperature``, ``thinking_level`` e
    ``max_output_tokens`` declarados chegam aos três papéis; ``temperature``
    fixa a temperatura de todos os analistas e exclui ``temperature_min`` /
    ``temperature_max``. Sem nenhuma delas, risco e portfólio continuam
    chamando sem opção, como antes. Nenhuma é calibrável no CAL-A, e ``seed``
    continua só metadado.
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
        temperature_min: float | None = None,
        temperature_max: float | None = None,
        seed_base: int = 10_000,
        risk_max_volatility: float = 0.50,
        risk_max_drawdown: float = 0.25,
        risk_max_concentration: float = 0.30,
        long_target_weight: float = DEFAULT_LONG_TARGET_WEIGHT,
        volatility_window: int = 21,
        decision_frequency: int = 1,
        temperature: float | None = None,
        thinking_level: str | None = None,
        max_output_tokens: int | None = None,
        strict_inputs: bool = False,
        portfolio_inversion_policy: str = "flag",
        technical_prompt_version: int = 1,
        risk_prompt_version: int = 1,
        technical_response_schema_version: int = 1,
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
        technical_prompt_version = _require_int(
            "technical_prompt_version", technical_prompt_version, minimum=1
        )
        risk_prompt_version = _require_int("risk_prompt_version", risk_prompt_version, minimum=1)
        if (technical_prompt_version == 5 and technical_response_schema_version != 2
                or technical_prompt_version != 5 and technical_response_schema_version != 1):
            raise ValueError("Technical prompt and response schema versions are incompatible")
        if retry_base_delay < 0 or not math.isfinite(retry_base_delay):
            raise ValueError("retry_base_delay must be finite and >= 0")
        long_target_weight = _validate_long_target_weight(
            long_target_weight, risk_max_concentration
        )
        if temperature is not None:
            if temperature_min is not None or temperature_max is not None:
                raise ValueError(
                    "declare either temperature or temperature_min/temperature_max; "
                    "two declarations of the same setting cannot both be material"
                )
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
                raise ValueError("temperature must be a number")
            temperature = float(temperature)
            if not math.isfinite(temperature) or not 0.0 <= temperature <= 2.0:
                raise ValueError("temperature must be finite and between 0 and 2")
            temperature_min = temperature_max = temperature
        if thinking_level is not None and thinking_level not in THINKING_LEVEL_VOCABULARY:
            raise ValueError(
                f"thinking_level must be one of {', '.join(THINKING_LEVEL_VOCABULARY)}"
            )
        if max_output_tokens is not None:
            max_output_tokens = _require_int(
                "max_output_tokens", max_output_tokens, minimum=1
            )
        if not isinstance(strict_inputs, bool):
            raise ValueError("strict_inputs must be a boolean")
        if portfolio_inversion_policy not in PORTFOLIO_INVERSION_POLICIES:
            raise ValueError(
                "portfolio_inversion_policy must be one of "
                f"{', '.join(PORTFOLIO_INVERSION_POLICIES)}"
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
        self.strict_inputs = strict_inputs
        self.portfolio_inversion_policy = portfolio_inversion_policy
        self.generation_options = generation_options(
            temperature, thinking_level, max_output_tokens
        )
        # Antes de construir cliente, grafo ou qualquer coisa que fale com a
        # rede: incompatibilidade detectável localmente não custa chamada.
        self.capabilities = capability_report(
            provider, self.generation_options, model.strip()
        )

        self.ensemble_config = AnalystEnsembleConfig(
            analyst_count=analyst_count,
            consensus_threshold=consensus_threshold,
            require_all_votes=require_all_votes,
            temperature_min=0.2 if temperature_min is None else temperature_min,
            temperature_max=0.8 if temperature_max is None else temperature_max,
            seed_base=seed_base,
            prompt_version=technical_prompt_version,
        )
        self.risk_config = RiskConfig(
            max_volatility=risk_max_volatility,
            max_drawdown=risk_max_drawdown,
            max_concentration=risk_max_concentration,
            prompt_version=risk_prompt_version,
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
            generation_options=self.generation_options or None,
        )
        self.transformer = DataTransformer()
        # Estado interno de uma execução, nunca compartilhado entre runs: a
        # factory do registry devolve instância nova a cada run.
        self.decisions: list[LLMDecisionRecord] = []
        #: Sessões consultadas fora da grade de ``decision_frequency``: não
        #: chamam o grafo, mas aparecem em ``decisions.jsonl`` como
        #: ``NOT_ELIGIBLE``.
        self.skipped_sessions: list[pd.Timestamp] = []
        self._peak_equity: float | None = None
        self._session_index = 0
        # Relógio da execução: ``None`` até a primeira decisão, que a arena
        # emite em ``decision_start``. Nunca retrocede.
        self._last_session: pd.Timestamp | None = None

    # ── Construção do cliente ────────────────────────────────────

    def _build_client(self) -> LLMClient:
        """Resolve o provedor declarado na spec; credencial vem do ambiente."""
        if self.provider == "mock":
            return _mock_client()
        if self.provider in PROVIDER_CLIENTS:
            if not self.model.strip():
                raise ValueError(
                    f"provider {self.provider!r} requires an explicit model; the "
                    "requested model is provenance and must appear in the spec"
                )
            client: LLMClient = cast(Any, PROVIDER_CLIENTS[self.provider])(
                model=self.model
            )
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

    def _require_forward_session(self, session: pd.Timestamp) -> None:
        """Avança o relógio interno da execução, e recusa andar para trás.

        Reaproveitar a instância entre runs traria pico e contador da execução
        anterior; sem o antigo ``len(history) == 1`` nada perceberia isso. Como
        a arena só avança no tempo, uma sessão que não é estritamente posterior
        à última significa instância reutilizada ou observação fora de ordem —
        as duas contaminariam o run em silêncio.
        """
        last = self._last_session
        if last is not None and session <= last:
            raise LLMDecisionError(
                f"session {session.date()} does not advance past the previously "
                f"observed {last.date()}; a participant instance belongs to a "
                "single run and its state cannot be reused across runs"
            )
        self._last_session = session

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
        # Ciclo de vida explícito: o estado de execução nasce na **primeira
        # chamada a** ``decide()`` desta instância, que é sempre
        # ``decision_start`` — a arena não chama o participante durante o
        # warm-up. Instância nova por run é garantida por ``build_participant``.
        #
        # O tamanho do histórico deixou de ser o detector: com janela avaliada
        # existe warm-up antes da primeira decisão, e ``len(history) == 1``
        # nunca mais seria verdade em ``decision_start``. Usá-lo manteria o
        # pico e o contador ancorados no início do snapshot, não da janela.
        self._require_forward_session(observation.session)
        # O pico acompanha *todas* as sessões avaliadas, elegíveis ou não: o
        # drawdown é estado de portfólio, não subproduto da frequência de
        # decisão. Ele começa em ``decision_start``, com o patrimônio inicial.
        self._peak_equity = (
            equity if self._peak_equity is None else max(self._peak_equity, equity)
        )
        session_index = self._session_index
        self._session_index += 1
        if session_index % self.decision_frequency != 0:
            # Sessão não elegível: nenhuma chamada ao provedor e nenhuma
            # intenção nova. A posição corrente segue pela semântica normal da
            # arena, que mantém quem não recebe intent.
            self.skipped_sessions.append(observation.session)
            return []

        close = float(cast(pd.Series, history["fechamento"]).iloc[-1])
        position = float(observation.positions[self.ticker])
        observed_weight = position * close / equity
        state = self._agent_state(observation, history, equity, close)
        violations = self._input_violations(state, history)
        if violations and self.strict_inputs:
            # Fail-closed antes de qualquer chamada: entrada científica
            # incompleta não é pergunta que se faça ao provedor.
            self.decisions.append(
                LLMDecisionRecord(
                    session=observation.session,
                    technical_signal=None,
                    consensus=None,
                    risk_verdict=None,
                    portfolio_action=None,
                    target_weight=None,
                    final_cause=INVALID_INPUT,
                    observed_weight=observed_weight,
                    input_violations=violations,
                )
            )
            raise LLMDecisionError(
                f"invalid scientific input at {observation.session.date()}: "
                f"{', '.join(violations)}",
                reason=INVALID_INPUT,
            )

        # A sessão de decisão é declarada pelo participante, que é quem a
        # conhece; nenhuma camada abaixo a deduz da ordem das chamadas.
        self.trace.begin_session(observation.session)
        self.client.reset()
        output = asyncio.run(self._run_graph(state))
        failures = tuple(self.client.failures)

        action = output.get("portfolio_action")
        portfolio_rule = output.get("portfolio_rule")
        final_cause = classify_decision(
            consensus=output.get("technical_consensus"),
            risk_verdict=output.get("risk_verdict"),
            risk_source=output.get("risk_source"),
            risk_rule=output.get("risk_rule"),
            portfolio_action=action,
            portfolio_rule=portfolio_rule,
            observed_weight=observed_weight,
            long_target_weight=self.long_target_weight,
            input_violations=violations,
            failures=failures,
        )
        # Sizing só é consultado quando existe decisão qualitativa e nenhuma
        # resposta inválida ou falha de provedor: veto de risco e ``MANTER``
        # sequer chegam até aqui com ação acionável, e falha não vira decisão.
        weight = (
            self.sizing.target_weight(action.decision)
            if action is not None
            and final_cause
            not in (INVALID_RESPONSE, PROVIDER_FAILURE, PROVIDER_REQUEST_REJECTED)
            else None
        )
        failure_text = tuple(f"{type(error).__name__}: {error}" for error in failures)
        self.decisions.append(
            LLMDecisionRecord(
                session=observation.session,
                technical_signal=output.get("technical_signal"),
                consensus=output.get("technical_consensus"),
                risk_verdict=output.get("risk_verdict"),
                portfolio_action=action,
                target_weight=weight,
                errors=tuple(str(error) for error in output.get("errors", [])),
                llm_failures=failure_text,
                final_cause=final_cause,
                risk_source=output.get("risk_source"),
                risk_rule=output.get("risk_rule"),
                portfolio_source=output.get("portfolio_source"),
                portfolio_rule=portfolio_rule,
                observed_weight=observed_weight,
                input_violations=violations,
            )
        )

        tolerated_inversion = (
            portfolio_rule == PORTFOLIO_RULE_DIRECTION_INVERSION
            and self.portfolio_inversion_policy == "flag"
        )
        if failure_text or (final_cause == INVALID_RESPONSE and not tolerated_inversion):
            detail = "; ".join(failure_text) or "response violates the stage contract"
            raise LLMDecisionError(
                f"unrecovered LLM failure while deciding "
                f"{observation.session.date()}: {detail}",
                reason=final_cause,
            )
        if final_cause == INVALID_INPUT and self.strict_inputs:
            raise LLMDecisionError(
                f"invalid scientific input at {observation.session.date()}",
                reason=INVALID_INPUT,
            )
        if weight is None:
            return []
        return target_portfolio_to_intents(observation, {self.ticker: weight})

    async def _run_graph(self, state: AgentState) -> dict[str, Any]:
        """Executa o grafo e devolve o último estado, mesmo se o provedor cair.

        Risco e portfólio só capturam ``TypeError``/``ValueError``: uma falha
        de transporte esgotada no retry (ou uma recusa da requisição) atravessa
        o nó e aborta o grafo. Essa exceção já foi registrada pelo
        ``FailureRecordingClient`` e gravada no trace; aqui ela deixa de ser
        exceção crua e vira o estado parcial — votos e parecer já obtidos —, que
        ``decide`` classifica e transforma em ``LLMDecisionError``. Qualquer
        exceção que **não** veio do limite do provedor é bug e sobe intacta.
        """
        last: dict[str, Any] = dict(state)
        try:
            async for snapshot in self.graph.astream(state, stream_mode="values"):
                last = snapshot
        except Exception as exc:
            if not any(exc is failure for failure in self.client.failures):
                raise
        return last

    # ── Evidência do run ─────────────────────────────────────────

    @property
    def llm_calls(self) -> tuple[LLMCallRecord, ...]:
        """Trace desta execução, em ordem de emissão."""
        return self.trace.records

    def decision_lines(self) -> list[dict[str, Any]]:
        """Uma linha por sessão consultada, em ordem de sessão."""
        lines = [
            (record.session, record.to_json_dict(self.ticker))
            for record in self.decisions
        ]
        lines += [
            (
                session,
                {
                    "schema_version": LLM_DECISION_ARTIFACT_SCHEMA_VERSION,
                    "decision_session": session_key(session),
                    "ticker": self.ticker,
                    "eligible": False,
                    "final_cause": NOT_ELIGIBLE,
                },
            )
            for session in self.skipped_sessions
        ]
        return [line for _, line in sorted(lines, key=lambda item: item[0])]

    def decisions_artifact(self) -> RunArtifact:
        """``decisions.jsonl``: a causa estruturada de cada sessão consultada."""
        lines = [canonical_json(line) for line in self.decision_lines()]
        return RunArtifact(
            name=LLM_DECISION_ARTIFACT,
            filename=LLM_DECISION_FILENAME,
            schema_version=LLM_DECISION_ARTIFACT_SCHEMA_VERSION,
            content=("\n".join(lines) + "\n" if lines else "").encode("utf-8"),
            summary={
                "decision_count": len(self.decisions),
                "not_eligible_count": len(self.skipped_sessions),
            },
        )

    def run_artifacts(self) -> tuple[RunArtifact, ...]:
        """Congela trace e decisões para publicação junto do run.

        Satisfaz ``RunArtifactProvider`` estruturalmente: a camada
        experimental publica esta evidência sem conhecer este tipo. Os bytes
        saem daqui prontos — publicar o run não reconsulta provedor, cliente
        nem estado externo, pela mesma razão que ``SnapshotEvidence`` existe.
        O trace continua sendo o primeiro artefato.
        """
        return (self.trace.artifact(), self.decisions_artifact())

    # ── Gate local, antes de construir ───────────────────────────

    @classmethod
    def preflight(
        cls, params: Mapping[str, Any], *, scientific: bool
    ) -> CapabilityReport:
        """Confere a spec sem construir o participante e sem tocar a rede.

        Em qualquer fase, o provedor precisa **declarar** as opções de geração
        pedidas — ``transport_options`` sozinho não prova suporte semântico.

        Em fase científica, nada material pode vir de default invisível:

        - todo parâmetro de :data:`SCIENTIFIC_REQUIRED_PARAMS` precisa estar
          escrito na spec — sem ``temperature`` o quorum voltaria à faixa
          0.2-0.8 e risco/portfólio herdariam o default do provedor; sem
          ``portfolio_inversion_policy`` a inversão viraria ``flag`` implícito;
        - provedor real também precisa de ``model``, ``max_output_tokens`` e,
          se o cliente tem níveis de thinking, ``thinking_level`` — senão
          valeriam os defaults do modelo, que o run não registra;
        - ``strict_inputs`` precisa ser ``True``;
        - provedor real precisa estar **empiricamente qualificado** para
          ``(provider, model)`` (:data:`EMPIRICALLY_QUALIFIED`): declaração de
          código não substitui LIVE_SMOKE.
        """
        provider = str(params.get("provider", "mock"))
        if scientific:
            required = list(SCIENTIFIC_REQUIRED_PARAMS)
            client = PROVIDER_CLIENTS.get(provider)
            if client is not None:
                required += ["model", "max_output_tokens"]
                if getattr(client, "THINKING_LEVELS", None) is not None:
                    required.append("thinking_level")
            missing = sorted(key for key in required if params.get(key) is None)
            if missing:
                raise ValueError(
                    "a scientific llm_agent spec must declare every material "
                    f"setting explicitly; missing: {', '.join(missing)}"
                )
            if params.get("strict_inputs") is not True:
                raise ValueError(
                    "a scientific phase requires strict_inputs=True for llm_agent; "
                    "missing features or risk metrics must fail the run instead "
                    "of becoming a silent MANTER"
                )
        report = capability_report(
            provider,
            generation_options(
                params.get("temperature"),
                params.get("thinking_level"),
                params.get("max_output_tokens"),
            ),
            str(params.get("model", "")).strip(),
        )
        if scientific and report.status == CAPABILITY_DECLARED_UNQUALIFIED:
            unqualified = sorted(set(report.declared) - set(report.qualified))
            raise ValueError(
                f"provider {provider!r} model {report.model!r} is "
                f"{CAPABILITY_DECLARED_UNQUALIFIED} for {', '.join(unqualified)}; "
                "a scientific phase requires a recorded LIVE_SMOKE qualification "
                "for this model (EMPIRICALLY_QUALIFIED)"
            )
        return report

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

        Os níveis brutos morrem nesta função: o que entra no estado é o
        conjunto adimensional de :mod:`src.agents.features`. ``ticker``,
        ``date`` e ``current_price`` continuam no estado porque as regras
        internas e a auditoria precisam deles — o prompt é que não os recebe.
        """
        close = cast(pd.Series, history["fechamento"])
        with_indicators = self.transformer.calculate_indicators(history)
        row = with_indicators.iloc[-1]
        levels: dict[str, float] = {
            key: float(row[key])
            for key in INDICATOR_KEYS
            if key in with_indicators.columns and pd.notna(row[key])
        }
        features = dimensionless_features(close_price, levels)

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
            "features": features,
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

    def _input_violations(
        self, state: AgentState, history: pd.DataFrame
    ) -> tuple[str, ...]:
        """Violações do contrato científico de entrada, como códigos.

        As oito features do contrato e a volatilidade sobre a janela
        **inteira** são obrigatórias. Com ``strict_inputs`` qualquer violação
        derruba a sessão antes de chamar o provedor; sem ele, a sessão segue
        como antes e é classificada ``INVALID_INPUT``.
        """
        features = state.get("features", {})
        violations = [
            f"missing_feature:{key}" for key in FEATURE_KEYS if key not in features
        ]
        # ``pct_change`` perde só a primeira barra: o OHLCV validado não tem NaN.
        if len(history) - 1 < self.volatility_window:
            violations.append("volatility_window_incomplete")
        volatility = state.get("recent_volatility")
        if volatility is None or not math.isfinite(volatility):
            violations.append("volatility_unavailable")
        return tuple(violations)
