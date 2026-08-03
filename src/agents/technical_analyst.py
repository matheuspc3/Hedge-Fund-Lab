"""Nós que convertem indicadores em parecer técnico individual ou coletivo."""

import asyncio
import json
from collections import Counter

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.agents.llm_client import LLMClient
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

SYSTEM_PROMPT = """Você é o analista técnico do Hedge-fund-lab.
Use exclusivamente o preço e os indicadores fornecidos. Ignore notícias,
conhecimento externo e dados futuros. Responda com COMPRA, VENDA ou MANTER,
uma justificativa curta baseada nos números e confiança entre 0 e 1."""


class AnalystEnsembleConfig(BaseModel):
    """Configuração do quorum de analistas independentes."""

    model_config = ConfigDict(extra="forbid")

    analyst_count: int = Field(default=30, ge=1, le=100)
    consensus_threshold: float = Field(default=5 / 6, gt=0.5, le=1.0)
    require_all_votes: bool = True
    temperature_min: float = Field(default=0.2, ge=0.0, le=2.0)
    temperature_max: float = Field(default=0.8, ge=0.0, le=2.0)
    seed_base: int = 10_000

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


def build_prompt(state: AgentState) -> str:
    indicators = parse_indicators_from_state(state)
    indicator_text = json.dumps(indicators, ensure_ascii=False, sort_keys=True)
    return (
        f"Ticker: {state.get('ticker', 'desconhecido')}\n"
        f"Data: {state.get('date', 'desconhecida')}\n"
        f"Preço atual: {state.get('current_price')}\n"
        f"Indicadores: {indicator_text if indicators else 'dados ausentes'}\n"
        "Emita COMPRA, VENDA ou MANTER sem usar informação externa."
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
        if not parse_indicators_from_state(state):
            message = "technical_analyst: indicadores ausentes"
            return {"technical_signal": _safe_signal(message), "errors": [message]}
        try:
            response = await llm.generate(
                SYSTEM_PROMPT, build_prompt(state), TechnicalSignal
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


def create_technical_analyst_ensemble_node(
    llm: LLMClient,
    config: AnalystEnsembleConfig | None = None,
):
    """Executa todos os analistas em paralelo e agrega por supermaioria."""

    config = config or AnalystEnsembleConfig()

    async def ask(state: AgentState, analyst_number: int):
        denominator = max(1, config.analyst_count - 1)
        temperature = config.temperature_min + (
            (config.temperature_max - config.temperature_min)
            * (analyst_number - 1)
            / denominator
        )
        seed = config.seed_base + analyst_number
        prompt = (
            f"Você é o analista {analyst_number} de {config.analyst_count}. "
            "Avalie de forma independente.\n" + build_prompt(state)
        )
        response = await llm.generate(
            SYSTEM_PROMPT,
            prompt,
            TechnicalSignal,
            {"temperature": temperature, "seed": seed, "analyst_id": analyst_number},
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
        if price is None or price <= 0 or not parse_indicators_from_state(state):
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
