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
    decision: Literal["COMPRA", "VENDA", "MANTER"]
    position_size: float = Field(ge=0.0, le=1.0)
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
    """

    ticker: str
    date: str
    indicators: dict[str, float | None]
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
    errors: Annotated[list[str], operator.add]
