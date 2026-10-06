"""Nós que convertem indicadores em parecer técnico individual ou coletivo."""

import asyncio
import json
from collections import Counter
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2
from src.agents.features import FEATURE_KEYS, canonical_prompt_json
from src.agents.llm_client import LLMCallMetadata, LLMClient
from src.agents.llm_trace import STAGE_TECHNICAL_ANALYST
from src.agents.state import (
    AgentState,
    TechnicalConsensus,
    TechnicalSignal,
    TechnicalVote,
)

INDICATOR_KEYS = (
    "sma_50",
    "sma_200",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "rsi",
    "macd",
    "macd_sinal",
)

#: Prompt dos caminhos **legados** (``AgentBacktestEngine``,
#: ``DailyAgentRunner``), que continuam alimentando o estado com níveis brutos.
SYSTEM_PROMPT = """You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the provided bar close value and technical indicators. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1."""

#: Prompt do caminho **científico**. Ele não menciona preço, ativo nem data
#: porque nenhum dos três é transmitido: o payload é adimensional e anônimo por
#: contrato (:mod:`src.agents.features`).
CAUSAL_SYSTEM_PROMPT = """You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1."""


class AnalystEnsembleConfig(BaseModel):
    """Configuração do quorum de analistas independentes."""

    model_config = ConfigDict(extra="forbid")

    analyst_count: int = Field(default=30, ge=1, le=100)
    consensus_threshold: float = Field(default=5 / 6, gt=0.5, le=1.0)
    require_all_votes: bool = True
    temperature_min: float = Field(default=0.2, ge=0.0, le=2.0)
    temperature_max: float = Field(default=0.8, ge=0.0, le=2.0)
    seed_base: int = 10_000
    #: Versão do system prompt técnico científico (Amendment 8): 1 = v1 sem
    #: glossário; 2 = glossário semântico das features + estado-não-transição.
    prompt_version: int = Field(default=1, ge=1, le=2)

    @model_validator(mode="after")
    def validate_temperature_range(self):
        if self.temperature_min > self.temperature_max:
            raise ValueError("temperature_min must be <= temperature_max")
        return self


def parse_indicators_from_state(state: AgentState) -> dict[str, float]:
    indicators = state.get("indicators", {})
    return {
        key: float(indicators[key])
        for key in INDICATOR_KEYS
        if indicators.get(key) is not None
    }


def parse_features_from_state(state: AgentState) -> dict[str, float]:
    """Features causais do estado, restritas ao contrato declarado.

    Filtrar por :data:`~src.agents.features.FEATURE_KEYS` não é redundância
    defensiva: é o ponto em que um campo novo — e possivelmente portador de
    nível — deixa de atravessar para o provedor por acidente.
    """
    features = state.get("features", {})
    return {
        key: float(features[key])
        for key in FEATURE_KEYS
        if features.get(key) is not None
    }


def has_quantitative_context(state: AgentState) -> bool:
    """Há contexto quantitativo suficiente para consultar o analista?"""
    return bool(parse_features_from_state(state)) or bool(
        parse_indicators_from_state(state)
    )


def system_prompt_for(state: AgentState, prompt_version: int = 1) -> str:
    """Escolhe o system prompt pelo contrato que o estado satisfaz e pela versão."""
    if not parse_features_from_state(state):
        return SYSTEM_PROMPT
    return TECHNICAL_SYSTEM_PROMPT_V2 if prompt_version == 2 else CAUSAL_SYSTEM_PROMPT


def build_prompt(state: AgentState) -> str:
    """Prompt do usuário — causal quando há features, legado quando não há.

    O caminho científico **não** transmite ticker, data nem preço: identidade e
    calendário abrem um canal de memorização do modelo, e o nível absoluto é
    contaminado por proventos posteriores a ``t``. Os três continuam íntegros
    nos artefatos de auditoria.
    """
    features = parse_features_from_state(state)
    if features:
        return (
            f"Features: {canonical_prompt_json(features)}\n"
            "Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics."
        )
    indicators = parse_indicators_from_state(state)
    indicator_text = json.dumps(indicators, ensure_ascii=False, sort_keys=True)
    return (
        f"Ticker: {state.get('ticker', 'unknown')}\n"
        f"Date: {state.get('date', 'unknown')}\n"
        f"Close: {state.get('current_price')}\n"
        f"Indicators: {indicator_text if indicators else 'none'}\n"
        "Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics."
    )


def _safe_signal(reason: str) -> TechnicalSignal:
    return TechnicalSignal(signal="MANTER", justification=reason, confidence=0.0)


def create_technical_analyst_node(llm: LLMClient):
    async def node(state: AgentState) -> dict:
        errors: list[str] = []
        price = state.get("current_price")
        if price is None or price <= 0:
            message = "technical_analyst: preço atual ausente ou inválido"
            return {"technical_signal": _safe_signal(message), "errors": [message]}
        if not has_quantitative_context(state):
            message = "technical_analyst: indicadores ausentes"
            return {"technical_signal": _safe_signal(message), "errors": [message]}
        try:
            response = await llm.generate(
                system_prompt_for(state),
                build_prompt(state),
                TechnicalSignal,
                metadata=LLMCallMetadata(stage=STAGE_TECHNICAL_ANALYST),
            )
            if not isinstance(response, TechnicalSignal):
                raise TypeError("resposta não segue TechnicalSignal")
            return {"technical_signal": response, "errors": errors}
        except (TypeError, ValueError) as exc:
            message = f"technical_analyst: resposta inválida: {exc}"
            return {"technical_signal": _safe_signal(message), "errors": [message]}

    return node


def _no_consensus(
    config: AnalystEnsembleConfig,
    votes: list[TechnicalVote],
    counts: Counter,
    reason: str,
) -> dict:
    summary = TechnicalConsensus(
        total_analysts=config.analyst_count,
        valid_votes=len(votes),
        threshold=config.consensus_threshold,
        counts={signal: counts[signal] for signal in ("COMPRA", "VENDA", "MANTER")},
        consensus_reached=False,
        winning_signal=None,
    )
    return {
        "technical_votes": votes,
        "technical_consensus": summary,
        "technical_signal": _safe_signal(reason),
    }


def ensemble_user_prompt(state: AgentState, analyst_number: int, analyst_count: int) -> str:
    """Prompt de usuário de um analista do quorum.

    No caminho científico (features causais) o prompt é **idêntico** para todos
    os analistas: Self-Consistency pede amostras independentes da mesma
    pergunta, e um rótulo "analista n de N" seria uma perturbação de prompt por
    amostra. Quem é o analista continua declarado em ``analyst_id``, como
    metadado e na identidade do trace — nunca no texto.

    O caminho legado (níveis brutos) mantém o rótulo, para não trocar em
    silêncio o prompt, o cache e os replays dos runners operacionais.
    """
    if parse_features_from_state(state):
        return build_prompt(state)
    return (
        f"Você é o analista {analyst_number} de {analyst_count}. "
        "Avalie de forma independente.\n" + build_prompt(state)
    )


def create_technical_analyst_ensemble_node(
    llm: LLMClient,
    config: AnalystEnsembleConfig | None = None,
    options: Mapping[str, Any] | None = None,
):
    """Executa todos os analistas em paralelo e agrega por supermaioria.

    ``options`` são as opções de geração declaradas (``thinking_level``,
    ``max_output_tokens``…), repassadas a cada analista. A temperatura de cada
    analista continua vindo do ``config``: ela é parte do desenho do quorum.
    """

    config = config or AnalystEnsembleConfig()
    generation = dict(options or {})

    async def ask(state: AgentState, analyst_number: int):
        denominator = max(1, config.analyst_count - 1)
        temperature = config.temperature_min + (
            (config.temperature_max - config.temperature_min)
            * (analyst_number - 1)
            / denominator
        )
        seed = config.seed_base + analyst_number
        response = await llm.generate(
            system_prompt_for(state, config.prompt_version),
            ensemble_user_prompt(state, analyst_number, config.analyst_count),
            TechnicalSignal,
            {
                **generation,
                "temperature": temperature,
                "seed": seed,
                "analyst_id": analyst_number,
            },
            # Quem é o analista é metadado técnico declarado pela chamada, não
            # algo a ser deduzido depois lendo o texto do prompt.
            metadata=LLMCallMetadata(
                stage=STAGE_TECHNICAL_ANALYST, analyst_id=analyst_number
            ),
        )
        if not isinstance(response, TechnicalSignal):
            raise TypeError("resposta não segue TechnicalSignal")
        return TechnicalVote(
            analyst_id=analyst_number,
            temperature=temperature,
            seed=seed,
            signal=response,
        )

    async def node(state: AgentState) -> dict:
        price = state.get("current_price")
        if price is None or price <= 0 or not has_quantitative_context(state):
            message = "technical_ensemble: preço ou indicadores ausentes"
            result = _no_consensus(config, [], Counter(), message)
            result["errors"] = [message]
            return result

        responses = await asyncio.gather(
            *(ask(state, number) for number in range(1, config.analyst_count + 1)),
            return_exceptions=True,
        )
        votes = [
            response for response in responses if isinstance(response, TechnicalVote)
        ]
        failures = len(responses) - len(votes)
        counts = Counter(vote.signal.signal for vote in votes)
        errors = (
            [f"technical_ensemble: {failures} resposta(s) inválida(s)"]
            if failures
            else []
        )

        if config.require_all_votes and failures:
            result = _no_consensus(
                config, votes, counts, "Quorum incompleto; manter por segurança"
            )
            result["errors"] = errors
            return result

        winner, winner_count = max(
            ((signal, counts[signal]) for signal in ("MANTER", "COMPRA", "VENDA")),
            key=lambda item: item[1],
        )
        denominator = config.analyst_count if config.require_all_votes else len(votes)
        share = winner_count / denominator if denominator else 0.0
        reached = share >= config.consensus_threshold
        if not reached:
            result = _no_consensus(
                config,
                votes,
                counts,
                f"Sem consenso: {winner_count}/{denominator} votos no sinal mais votado",
            )
            result["errors"] = errors
            return result

        winning_votes = [vote for vote in votes if vote.signal.signal == winner]
        mean_confidence = sum(vote.signal.confidence for vote in winning_votes) / len(
            winning_votes
        )
        collective = TechnicalSignal(
            signal=winner,
            justification=f"Consenso coletivo: {winner_count}/{denominator} votos em {winner}",
            confidence=mean_confidence * share,
        )
        summary = TechnicalConsensus(
            total_analysts=config.analyst_count,
            valid_votes=len(votes),
            threshold=config.consensus_threshold,
            counts={signal: counts[signal] for signal in ("COMPRA", "VENDA", "MANTER")},
            consensus_reached=True,
            winning_signal=winner,
        )
        return {
            "technical_votes": votes,
            "technical_consensus": summary,
            "technical_signal": collective,
            "errors": errors,
        }

    return node
