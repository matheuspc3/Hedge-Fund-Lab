"""Compilação do fluxo multiagente linear da primeira versão."""

from collections.abc import Mapping
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from src.agents.llm_client import LLMClient
from src.agents.portfolio_manager import PortfolioConfig, create_portfolio_manager_node
from src.agents.risk_manager import RiskConfig, create_risk_manager_node
from src.agents.state import AgentState
from src.agents.technical_analyst import (
    AnalystEnsembleConfig,
    create_technical_analyst_ensemble_node,
)


def _route_after_risk(state: AgentState) -> Literal["portfolio_manager", "__end__"]:
    verdict = state.get("risk_verdict")
    return "portfolio_manager" if verdict and verdict.verdict == "APROVADO" else END


def build_graph(
    llm_client: LLMClient,
    risk_config: RiskConfig | None = None,
    portfolio_config: PortfolioConfig | None = None,
    ensemble_config: AnalystEnsembleConfig | None = None,
    *,
    generation_options: Mapping[str, Any] | None = None,
):
    """Grafo técnico -> risco -> portfólio.

    ``generation_options`` chega explicitamente aos três papéis. ``None`` é o
    comportamento legado: risco e portfólio chamam o provedor sem opção
    nenhuma e herdam o default dele.
    """
    builder = StateGraph(AgentState)
    builder.add_node(
        "technical_analyst",
        create_technical_analyst_ensemble_node(
            llm_client, ensemble_config, generation_options
        ),
    )
    builder.add_node(
        "risk_manager",
        create_risk_manager_node(llm_client, risk_config, generation_options),
    )
    builder.add_node(
        "portfolio_manager",
        create_portfolio_manager_node(llm_client, portfolio_config, generation_options),
    )
    builder.add_edge(START, "technical_analyst")
    builder.add_edge("technical_analyst", "risk_manager")
    builder.add_conditional_edges("risk_manager", _route_after_risk)
    builder.add_edge("portfolio_manager", END)
    return builder.compile()
