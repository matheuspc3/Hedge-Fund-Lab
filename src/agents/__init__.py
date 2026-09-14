"""Sistema multiagente para decisões de investimento auditáveis."""

from src.agents.graph import build_graph
from src.agents.llm_client import (
    AgentRouterLLMClient,
    CachedLLMClient,
    LLMCallMetadata,
    LLMClient,
    MockLLMClient,
    RetryingLLMClient,
)
from src.agents.llm_trace import (
    LLM_TRACE_FILENAME,
    LLM_TRACE_SCHEMA_VERSION,
    LLMCallRecord,
    LLMCallRequest,
    RecordingLLMClient,
    ReplayLLMClient,
    ReplayMismatchError,
)
from src.agents.participant import (
    DEFAULT_LONG_TARGET_WEIGHT,
    SUPPORTED_PROVIDERS,
    FixedTargetSizing,
    LLMDecisionError,
    LLMDecisionRecord,
    LLMParticipant,
    target_portfolio_to_intents,
)
from src.agents.portfolio_manager import (
    SIZING_MODE_LEGACY,
    SIZING_MODE_QUALITATIVE,
    PortfolioConfig,
    calculate_kelly_size,
)
from src.agents.state import (
    AgentState,
    FinalDecision,
    PortfolioAction,
    RiskVerdict,
    TechnicalConsensus,
    TechnicalSignal,
    TechnicalVote,
)
from src.agents.technical_analyst import AnalystEnsembleConfig

__all__ = [
    "DEFAULT_LONG_TARGET_WEIGHT",
    "LLM_TRACE_FILENAME",
    "LLM_TRACE_SCHEMA_VERSION",
    "SIZING_MODE_LEGACY",
    "SIZING_MODE_QUALITATIVE",
    "SUPPORTED_PROVIDERS",
    "AgentRouterLLMClient",
    "AgentState",
    "AnalystEnsembleConfig",
    "CachedLLMClient",
    "FinalDecision",
    "FixedTargetSizing",
    "LLMCallMetadata",
    "LLMCallRecord",
    "LLMCallRequest",
    "LLMClient",
    "LLMDecisionError",
    "LLMDecisionRecord",
    "LLMParticipant",
    "MockLLMClient",
    "PortfolioAction",
    "PortfolioConfig",
    "RecordingLLMClient",
    "ReplayLLMClient",
    "ReplayMismatchError",
    "RetryingLLMClient",
    "RiskVerdict",
    "TechnicalConsensus",
    "TechnicalSignal",
    "TechnicalVote",
    "build_graph",
    "calculate_kelly_size",
    "target_portfolio_to_intents",
]
