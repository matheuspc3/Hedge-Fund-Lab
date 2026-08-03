"""Nó de risco com regras duras anteriores a qualquer chamada de LLM."""

import json

from pydantic import BaseModel, ConfigDict, Field

from src.agents.llm_client import LLMClient
from src.agents.state import AgentState, RiskVerdict

SYSTEM_PROMPT = """Você é o gestor de risco do Hedge-fund-lab.
Avalie apenas o sinal e as métricas fornecidas. Preserve capital, não invente
dados e retorne APROVADO ou VETADO com análise objetiva."""


class RiskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_volatility: float = Field(default=0.50, ge=0.0)
    max_drawdown: float = Field(default=0.25, ge=0.0, le=1.0)
    max_concentration: float = Field(default=0.30, gt=0.0, le=1.0)


class RiskManager:
    def __init__(self, llm: LLMClient, config: RiskConfig | None = None):
        self.llm = llm
        self.config = config or RiskConfig()

    @staticmethod
    def _metrics(state: AgentState) -> dict[str, float]:
        metrics = {}
        for key in ("recent_volatility", "current_drawdown"):
            value = state.get(key)
            if value is not None:
                metrics[key] = float(value)
        equity = state.get("equity")
        price = state.get("current_price")
        position = state.get("position", 0.0)
        if equity and equity > 0 and price is not None:
            metrics["current_concentration"] = max(0.0, position * price / equity)
        return metrics

    @staticmethod
    def _verdict(verdict: str, analysis: str, metrics: dict[str, float]) -> RiskVerdict:
        return RiskVerdict(verdict=verdict, analysis=analysis, risk_metrics=metrics)

    async def evaluate(self, state: AgentState) -> dict:
        signal = state.get("technical_signal")
        metrics = self._metrics(state)
        if signal is None:
            message = "risk_manager: sinal técnico ausente"
            return {
                "risk_verdict": self._verdict("VETADO", message, metrics),
                "errors": [message],
            }

        # ponytail: vender ou não operar não aumenta exposição; não bloqueamos uma
        # saída por falta de métricas. Reavaliar se shorts entrarem no experimento.
        if signal.signal in {"VENDA", "MANTER"}:
            return {
                "risk_verdict": self._verdict(
                    "APROVADO", "Operação não aumenta a exposição", metrics
                ),
                "errors": [],
            }

        required = {"recent_volatility", "current_drawdown", "current_concentration"}
        missing = sorted(required - metrics.keys())
        if missing:
            message = f"risk_manager: métricas ausentes: {', '.join(missing)}"
            return {
                "risk_verdict": self._verdict("VETADO", message, metrics),
                "errors": [message],
            }
        if metrics["recent_volatility"] > self.config.max_volatility:
            return {
                "risk_verdict": self._verdict(
                    "VETADO", "Volatilidade acima do limite", metrics
                ),
                "errors": [],
            }
        if metrics["current_drawdown"] > self.config.max_drawdown:
            return {
                "risk_verdict": self._verdict(
                    "VETADO", "Drawdown acima do limite", metrics
                ),
                "errors": [],
            }
        if metrics["current_concentration"] >= self.config.max_concentration:
            return {
                "risk_verdict": self._verdict(
                    "VETADO", "Concentração no limite", metrics
                ),
                "errors": [],
            }

        prompt = json.dumps(
            {"technical_signal": signal.model_dump(), "risk_metrics": metrics},
            ensure_ascii=False,
            sort_keys=True,
        )
        try:
            response = await self.llm.generate(SYSTEM_PROMPT, prompt, RiskVerdict)
            if not isinstance(response, RiskVerdict):
                raise TypeError("resposta não segue RiskVerdict")
            response.risk_metrics.update(metrics)
            return {"risk_verdict": response, "errors": []}
        except (TypeError, ValueError) as exc:
            message = f"risk_manager: resposta inválida: {exc}"
            return {
                "risk_verdict": self._verdict("VETADO", message, metrics),
                "errors": [message],
            }


def create_risk_manager_node(llm: LLMClient, config: RiskConfig | None = None):
    return RiskManager(llm, config).evaluate
