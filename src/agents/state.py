"""Contratos validados compartilhados pelos nós do grafo."""

import operator
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Modelo de resposta que rejeita campos inventados pelo LLM."""

    model_config = ConfigDict(extra="forbid")


class TechnicalSignal(StrictModel):
    signal: Literal["COMPRA", "VENDA", "MANTER"]
    justification: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class RiskVerdict(StrictModel):
    verdict: Literal["APROVADO", "VETADO"]
    analysis: str = Field(min_length=1)
    risk_metrics: dict[str, float] = Field(default_factory=dict)


class FinalDecision(StrictModel):
    """Decisão com quantidade financeira embutida — contrato **legado**.

    ``position_size`` é fração *da operação*: caixa disponível na compra,
    posição corrente na venda. Continua sendo o contrato dos caminhos
    operacionais legados (``AgentBacktestEngine``, ``DailyAgentRunner``). O
    caminho científico da arena **não** usa este schema: lá o gestor de
    portfólio responde :class:`PortfolioAction`, sem quantidade, e o tamanho
    da posição é decidido por política determinística fora do LLM.
    """

    decision: Literal["COMPRA", "VENDA", "MANTER"]
    position_size: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(min_length=1)


class PortfolioAction(StrictModel):
    """Decisão **qualitativa** do gestor de portfólio: direção, sem tamanho.

    Este é o contrato do caminho científico. Pedir ao LLM um ``position_size``
    para depois ignorá-lo seria fingir que a autoridade de dimensionamento não
    foi concedida; aqui o campo simplesmente não existe, então não há nada a
    ignorar. A exposição alvo é decidida depois, por política determinística.
    """

    decision: Literal["COMPRA", "VENDA", "MANTER"]
    reasoning: str = Field(min_length=1)


class TechnicalConsensus(StrictModel):
    total_analysts: int = Field(ge=1)
    valid_votes: int = Field(ge=0)
    threshold: float = Field(gt=0.5, le=1.0)
    counts: dict[Literal["COMPRA", "VENDA", "MANTER"], int]
    consensus_reached: bool
    winning_signal: Literal["COMPRA", "VENDA", "MANTER"] | None = None


class TechnicalVote(StrictModel):
    analyst_id: int = Field(ge=1)
    temperature: float = Field(ge=0.0, le=2.0)
    seed: int
    signal: TechnicalSignal


class AgentState(TypedDict, total=False):
    """Estado operacional de um ativo em uma única data.

    ``position`` é quantidade de ações. ``position_size`` nas decisões é a
    fração da operação: capital disponível em compras, posição atual em vendas.
    Drawdown e volatilidade usam magnitudes positivas (0.20 = 20%).

    O gestor de portfólio escreve **um** dos dois campos de saída, nunca os
    dois, conforme o ``sizing_mode`` configurado: ``final_decision`` no modo
    legado (com quantidade) e ``portfolio_action`` no modo científico (apenas
    direção). ``payoff_ratio`` só é material para a fórmula de Kelly do modo
    legado e é omitido pelo caminho científico.
    """

    ticker: str
    date: str
    #: Níveis brutos de indicadores — contrato **legado**. O caminho científico
    #: não os preenche, para que não exista nível a transmitir por acidente.
    indicators: dict[str, float | None]
    #: Razões adimensionais do contrato causal (:mod:`src.agents.features`).
    #: É o único conjunto quantitativo que o caminho científico publica ao
    #: provedor; ``ticker``, ``date`` e ``current_price`` permanecem no estado
    #: como informação interna e de auditoria, nunca como payload.
    features: dict[str, float]
    cash: float
    position: float
    current_price: float
    equity: float
    recent_volatility: float
    current_drawdown: float
    payoff_ratio: float
    technical_votes: list[TechnicalVote]
    technical_consensus: TechnicalConsensus
    technical_signal: TechnicalSignal | None
    risk_verdict: RiskVerdict | None
    final_decision: FinalDecision | None
    portfolio_action: PortfolioAction | None
    errors: Annotated[list[str], operator.add]
