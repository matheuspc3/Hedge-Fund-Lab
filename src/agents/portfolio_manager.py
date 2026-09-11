"""Nó final de decisão e dimensionamento conservador da operação."""

import json

from pydantic import BaseModel, ConfigDict, Field

from src.agents.llm_client import LLMClient
from src.agents.state import AgentState, FinalDecision

SYSTEM_PROMPT = """Você é o gestor de portfólio do Hedge-fund-lab.
Consolide o sinal aprovado sem inverter sua direção. O tamanho solicitado deve
respeitar o máximo informado. Retorne COMPRA, VENDA ou MANTER."""


class PortfolioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kelly_fraction: float = Field(default=0.50, gt=0.0, le=1.0)
    max_position_size: float = Field(default=0.25, gt=0.0, le=1.0)
    max_concentration: float = Field(default=0.30, gt=0.0, le=1.0)


def calculate_kelly_size(
    win_probability: float,
    payoff_ratio: float = 1.0,
    fraction: float = 0.5,
) -> float:
    """Fractional Kelly limitada ao intervalo [0, 1]."""
    if not 0.0 <= win_probability <= 1.0:
        raise ValueError("win_probability must be between 0 and 1")
    if payoff_ratio <= 0:
        raise ValueError("payoff_ratio must be > 0")
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction must be between 0 and 1")
    full_kelly = (payoff_ratio * win_probability - (1 - win_probability)) / payoff_ratio
    return min(1.0, max(0.0, full_kelly * fraction))


def _hold(reason: str) -> FinalDecision:
    return FinalDecision(decision="MANTER", position_size=0.0, reasoning=reason)


def create_portfolio_manager_node(
    llm: LLMClient,
    config: PortfolioConfig | None = None,
):
    config = config or PortfolioConfig()

    async def node(state: AgentState) -> dict:
        signal = state.get("technical_signal")
        verdict = state.get("risk_verdict")
        if signal is None or verdict is None:
            message = "portfolio_manager: parecer anterior ausente"
            return {"final_decision": _hold(message), "errors": [message]}
        if verdict.verdict == "VETADO":
            return {
                "final_decision": _hold("Operação vetada pelo gestor de risco"),
                "errors": [],
            }
        if signal.signal == "MANTER":
            return {"final_decision": _hold("Analista recomendou manter"), "errors": []}
        if state.get("current_price", 0.0) <= 0:
            message = "portfolio_manager: preço atual ausente ou inválido"
            return {"final_decision": _hold(message), "errors": [message]}

        max_size = 1.0
        if signal.signal == "COMPRA":
            if state.get("cash", 0.0) <= 0:
                return {"final_decision": _hold("Caixa insuficiente"), "errors": []}
            kelly = calculate_kelly_size(
                signal.confidence,
                state.get("payoff_ratio", 1.0),
                config.kelly_fraction,
            )
            equity = state.get("equity", 0.0)
            current_exposure = 0.0
            if equity > 0:
                current_exposure = (
                    state.get("position", 0.0) * state["current_price"] / equity
                )
            concentration_room = max(0.0, config.max_concentration - current_exposure)
            max_size = min(kelly, config.max_position_size, concentration_room)
            if max_size <= 0:
                return {
                    "final_decision": _hold(
                        "Kelly ou limite de concentração não permite compra"
                    ),
                    "errors": [],
                }

        prompt = json.dumps(
            {
                "technical_signal": signal.model_dump(),
                "risk_verdict": verdict.model_dump(),
                "max_position_size": max_size,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        try:
            response = await llm.generate(SYSTEM_PROMPT, prompt, FinalDecision)
            if not isinstance(response, FinalDecision):
                raise TypeError("resposta não segue FinalDecision")
            if response.decision not in {signal.signal, "MANTER"}:
                message = "portfolio_manager: decisão inverteu o sinal técnico"
                return {"final_decision": _hold(message), "errors": [message]}
            if response.decision == "MANTER":
                response.position_size = 0.0
            else:
                response.position_size = min(response.position_size, max_size)
            return {"final_decision": response, "errors": []}
        except (TypeError, ValueError) as exc:
            message = f"portfolio_manager: resposta inválida: {exc}"
            return {"final_decision": _hold(message), "errors": [message]}

    return node
