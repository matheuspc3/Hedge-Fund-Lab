"""Nó final de decisão do portfólio, em dois modos explicitamente separados.

Dois caminhos coexistem neste projeto e **não** compartilham política de
dimensionamento:

``legacy_confidence_kelly``
    O comportamento histórico, preservado para não quebrar em silêncio o
    ``AgentBacktestEngine`` e o ``DailyAgentRunner``: ``confidence`` do parecer
    técnico entra como ``win_probability`` na fractional Kelly, o resultado é
    limitado por ``max_position_size`` e pela folga de concentração, e o LLM
    responde :class:`FinalDecision` com um ``position_size`` abaixo desse teto.

``qualitative``
    O caminho científico da arena. O LLM responde :class:`PortfolioAction` —
    apenas direção e justificativa — e **nenhuma quantidade financeira sai
    daqui**. O tamanho da posição é decidido depois, por política determinística
    do participante.

A separação existe por uma razão metodológica, não estética: a ``confidence``
textual de um LLM não é uma probabilidade empírica de vitória e não pode ser
consumida aritmeticamente como ``P(win)`` sem calibração prévia. Kelly continua
implementado aqui porque continua servindo ao caminho legado, a ablations e a
uma versão calibrada futura — não porque seja o sizing científico v1.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.agents.features import canonical_prompt_json
from src.agents.llm_client import LLMCallMetadata, LLMClient
from src.agents.llm_trace import STAGE_PORTFOLIO_MANAGER
from src.agents.state import AgentState, FinalDecision, PortfolioAction

#: Modo legado: ``confidence`` -> Kelly -> teto de posição -> ``position_size``.
SIZING_MODE_LEGACY = "legacy_confidence_kelly"
#: Modo científico: decisão qualitativa; o sizing é determinístico e externo.
SIZING_MODE_QUALITATIVE = "qualitative"

SIZING_MODES = (SIZING_MODE_LEGACY, SIZING_MODE_QUALITATIVE)

SYSTEM_PROMPT = """Você é o gestor de portfólio do Hedge-fund-lab.
Consolide o sinal aprovado sem inverter sua direção. O tamanho solicitado deve
respeitar o máximo informado. Retorne COMPRA, VENDA ou MANTER."""

QUALITATIVE_SYSTEM_PROMPT = """Você é o gestor de portfólio do Hedge-fund-lab.
Decida apenas a direção: seguir o sinal técnico aprovado ou manter a posição
atual. Você não define tamanho de posição, percentual de carteira nem
quantidade financeira — isso é decidido fora desta etapa por política
determinística. Não inverta a direção do sinal aprovado. Retorne COMPRA, VENDA
ou MANTER com uma justificativa objetiva."""


class PortfolioConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    #: Qual política governa o nó. O default é o legado de propósito: quem já
    #: constrói o grafo sem declarar nada continua recebendo o comportamento
    #: que tinha, em vez de mudar de estratégia sem pedir.
    sizing_mode: Literal["legacy_confidence_kelly", "qualitative"] = SIZING_MODE_LEGACY
    #: Materiais apenas em ``legacy_confidence_kelly``; ignorados no modo
    #: qualitativo, onde nenhuma quantidade é calculada aqui.
    kelly_fraction: float = Field(default=0.50, gt=0.0, le=1.0)
    max_position_size: float = Field(default=0.25, gt=0.0, le=1.0)
    max_concentration: float = Field(default=0.30, gt=0.0, le=1.0)


def calculate_kelly_size(
    win_probability: float,
    payoff_ratio: float = 1.0,
    fraction: float = 0.5,
) -> float:
    """Fractional Kelly limitada ao intervalo [0, 1].

    **Alternativa legada/experimental, não o sizing científico v1.** Ela só é
    chamada no modo ``legacy_confidence_kelly``. Alimentá-la com a
    ``confidence`` textual do LLM equivale a afirmar que aquele número é uma
    probabilidade empírica de vitória, o que o projeto não sustenta hoje.
    """
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


def _hold_action(reason: str) -> PortfolioAction:
    return PortfolioAction(decision="MANTER", reasoning=reason)


def create_portfolio_manager_node(
    llm: LLMClient,
    config: PortfolioConfig | None = None,
):
    """Nó do gestor de portfólio no modo declarado por ``config``."""
    config = config or PortfolioConfig()
    if config.sizing_mode == SIZING_MODE_QUALITATIVE:
        return _qualitative_node(llm)
    return _legacy_kelly_node(llm, config)


def _qualitative_node(llm: LLMClient):
    """Decisão de direção, sem autoridade de dimensionamento.

    O que este nó **não** faz é a parte metodologicamente relevante: não chama
    :func:`calculate_kelly_size`, não lê ``confidence`` como número, não calcula
    teto de posição e não pede quantidade ao LLM. ``confidence`` continua
    visível no ``technical_signal`` enviado como contexto qualitativo — ela
    apenas não entra em fórmula alguma.

    Também não existe guarda de "caixa insuficiente" aqui, como no modo legado:
    lá a compra era uma fração do caixa e caixa zero tornava a ordem vazia;
    aqui a decisão declara um **estado desejado de carteira**, que pode já estar
    satisfeito. Se sobra caixa para chegar ao alvo é pergunta do executor.
    """

    async def node(state: AgentState) -> dict:
        signal = state.get("technical_signal")
        verdict = state.get("risk_verdict")
        if signal is None or verdict is None:
            message = "portfolio_manager: parecer anterior ausente"
            return {"portfolio_action": _hold_action(message), "errors": [message]}
        if verdict.verdict == "VETADO":
            return {
                "portfolio_action": _hold_action(
                    "Operação vetada pelo gestor de risco"
                ),
                "errors": [],
            }
        if signal.signal == "MANTER":
            return {
                "portfolio_action": _hold_action("Analista recomendou manter"),
                "errors": [],
            }
        if state.get("current_price", 0.0) <= 0:
            message = "portfolio_manager: preço atual ausente ou inválido"
            return {"portfolio_action": _hold_action(message), "errors": [message]}

        # Canonicalização também aqui: o parecer de risco carrega as métricas
        # escalares e o sinal técnico carrega ``confidence``. Um único estágio
        # sem quantização bastaria para quebrar a identidade do prompt entre
        # dois vintages da mesma série.
        prompt = canonical_prompt_json(
            {
                "technical_signal": signal.model_dump(),
                "risk_verdict": verdict.model_dump(),
            }
        )
        try:
            response = await llm.generate(
                QUALITATIVE_SYSTEM_PROMPT,
                prompt,
                PortfolioAction,
                metadata=LLMCallMetadata(stage=STAGE_PORTFOLIO_MANAGER),
            )
            if not isinstance(response, PortfolioAction):
                raise TypeError("resposta não segue PortfolioAction")
            if response.decision not in {signal.signal, "MANTER"}:
                message = "portfolio_manager: decisão inverteu o sinal técnico"
                return {"portfolio_action": _hold_action(message), "errors": [message]}
            return {"portfolio_action": response, "errors": []}
        except (TypeError, ValueError) as exc:
            message = f"portfolio_manager: resposta inválida: {exc}"
            return {"portfolio_action": _hold_action(message), "errors": [message]}

    return node


def _legacy_kelly_node(llm: LLMClient, config: PortfolioConfig):
    """Comportamento histórico preservado para os runners operacionais."""

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
            response = await llm.generate(
                SYSTEM_PROMPT,
                prompt,
                FinalDecision,
                metadata=LLMCallMetadata(stage=STAGE_PORTFOLIO_MANAGER),
            )
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
