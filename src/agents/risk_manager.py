"""Nó de risco com regras duras anteriores a qualquer chamada de LLM."""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.agents.features import canonical_metrics, canonical_prompt_json
from src.agents.llm_client import LLMCallMetadata, LLMClient
from src.agents.llm_trace import STAGE_RISK_MANAGER
from src.agents.state import AgentState, RiskVerdict

SYSTEM_PROMPT = """Você é o gestor de risco do Hedge-fund-lab.
Avalie apenas o sinal e as métricas fornecidas. Preserve capital, não invente
dados e retorne APROVADO ou VETADO com análise objetiva."""

#: Quem decidiu o veredito (``risk_source``) e por qual regra (``risk_rule``).
#: São códigos estruturados para que a causa de um veto nunca precise ser
#: reconstruída lendo o texto livre de ``RiskVerdict.analysis``.
RISK_SOURCE_AUTO_APPROVE = "AUTO_APPROVE"
RISK_SOURCE_HARD_RULE = "HARD_RULE"
RISK_SOURCE_LLM = "LLM"

RISK_RULE_VOLATILITY = "VOLATILITY"
RISK_RULE_DRAWDOWN = "DRAWDOWN"
RISK_RULE_CONCENTRATION = "CONCENTRATION"
#: Insumo ausente: falha de entrada, não prudência financeira.
RISK_RULE_MISSING_SIGNAL = "MISSING_SIGNAL"
RISK_RULE_MISSING_METRICS = "MISSING_METRICS"
#: Resposta do LLM que não satisfaz ``RiskVerdict``.
RISK_RULE_INVALID_RESPONSE = "INVALID_RESPONSE"


class RiskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_volatility: float = Field(default=0.50, ge=0.0)
    max_drawdown: float = Field(default=0.25, ge=0.0, le=1.0)
    max_concentration: float = Field(default=0.30, gt=0.0, le=1.0)


class RiskManager:
    def __init__(
        self,
        llm: LLMClient,
        config: RiskConfig | None = None,
        options: Mapping[str, Any] | None = None,
    ):
        self.llm = llm
        self.config = config or RiskConfig()
        #: Opções de geração declaradas; ``None`` preserva a chamada legada,
        #: que não envia opção nenhuma e herda o default do provedor.
        self.options = dict(options) if options else None

    @staticmethod
    def _metrics(state: AgentState) -> dict[str, float]:
        """Métricas de risco na representação canônica única.

        A quantização acontece **aqui**, antes das regras duras, e não apenas
        na serialização do prompt. Dois vintages da mesma série ajustada
        produzem níveis que diferem por um fator comum; sem a canonicalização,
        ``0.25000000000001`` e ``0.24999999999999`` atravessariam o mesmo
        limiar em lados opostos e o veredito de risco dependeria de proventos
        posteriores à decisão. O valor canônico é o valor científico.
        """
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
        return canonical_metrics(metrics)

    @staticmethod
    def _verdict(verdict: str, analysis: str, metrics: dict[str, float]) -> RiskVerdict:
        return RiskVerdict(verdict=verdict, analysis=analysis, risk_metrics=metrics)

    @classmethod
    def _result(
        cls,
        verdict: str,
        analysis: str,
        metrics: dict[str, float],
        source: str,
        rule: str | None,
        errors: list[str] | None = None,
    ) -> dict:
        return {
            "risk_verdict": cls._verdict(verdict, analysis, metrics),
            "risk_source": source,
            "risk_rule": rule,
            "errors": errors or [],
        }

    async def evaluate(self, state: AgentState) -> dict:
        signal = state.get("technical_signal")
        metrics = self._metrics(state)
        if signal is None:
            message = "risk_manager: sinal técnico ausente"
            return self._result(
                "VETADO",
                message,
                metrics,
                RISK_SOURCE_HARD_RULE,
                RISK_RULE_MISSING_SIGNAL,
                [message],
            )

        # ponytail: vender ou não operar não aumenta exposição; não bloqueamos uma
        # saída por falta de métricas. Reavaliar se shorts entrarem no experimento.
        if signal.signal in {"VENDA", "MANTER"}:
            return self._result(
                "APROVADO",
                "Operação não aumenta a exposição",
                metrics,
                RISK_SOURCE_AUTO_APPROVE,
                None,
            )

        required = {"recent_volatility", "current_drawdown", "current_concentration"}
        missing = sorted(required - metrics.keys())
        if missing:
            message = f"risk_manager: métricas ausentes: {', '.join(missing)}"
            return self._result(
                "VETADO",
                message,
                metrics,
                RISK_SOURCE_HARD_RULE,
                RISK_RULE_MISSING_METRICS,
                [message],
            )
        if metrics["recent_volatility"] > self.config.max_volatility:
            return self._result(
                "VETADO",
                "Volatilidade acima do limite",
                metrics,
                RISK_SOURCE_HARD_RULE,
                RISK_RULE_VOLATILITY,
            )
        if metrics["current_drawdown"] > self.config.max_drawdown:
            return self._result(
                "VETADO",
                "Drawdown acima do limite",
                metrics,
                RISK_SOURCE_HARD_RULE,
                RISK_RULE_DRAWDOWN,
            )
        if metrics["current_concentration"] >= self.config.max_concentration:
            return self._result(
                "VETADO",
                "Concentração no limite",
                metrics,
                RISK_SOURCE_HARD_RULE,
                RISK_RULE_CONCENTRATION,
            )

        prompt = canonical_prompt_json(
            {"technical_signal": signal.model_dump(), "risk_metrics": metrics}
        )
        try:
            response = await self.llm.generate(
                SYSTEM_PROMPT,
                prompt,
                RiskVerdict,
                self.options,
                metadata=LLMCallMetadata(stage=STAGE_RISK_MANAGER),
            )
            if not isinstance(response, RiskVerdict):
                raise TypeError("resposta não segue RiskVerdict")
            response.risk_metrics.update(metrics)
            return {
                "risk_verdict": response,
                "risk_source": RISK_SOURCE_LLM,
                "risk_rule": None,
                "errors": [],
            }
        except (TypeError, ValueError) as exc:
            message = f"risk_manager: resposta inválida: {exc}"
            return self._result(
                "VETADO",
                message,
                metrics,
                RISK_SOURCE_LLM,
                RISK_RULE_INVALID_RESPONSE,
                [message],
            )


def create_risk_manager_node(
    llm: LLMClient,
    config: RiskConfig | None = None,
    options: Mapping[str, Any] | None = None,
):
    return RiskManager(llm, config, options).evaluate
