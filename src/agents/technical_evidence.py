"""H2 v6 current-state contract, separate from the frozen linguistic checker."""

from typing import Literal, get_args

from pydantic import ConfigDict, Field

from src.agents.state import StrictModel

TECHNICAL_RESPONSE_SCHEMA_VERSION = 2
TECHNICAL_EVIDENCE_VOCABULARY_VERSION = 1
TECHNICAL_EVIDENCE_VALIDATOR_VERSION = 1

EvidenceCode = Literal[
    "CLOSE_ABOVE_SMA50", "CLOSE_AT_SMA50", "CLOSE_BELOW_SMA50",
    "CLOSE_ABOVE_SMA200", "CLOSE_AT_SMA200", "CLOSE_BELOW_SMA200",
    "CLOSE_ABOVE_BB_UPPER", "CLOSE_AT_BB_UPPER", "CLOSE_INSIDE_BOLLINGER",
    "CLOSE_AT_BB_LOWER", "CLOSE_BELOW_BB_LOWER",
    "MACD_POSITIVE", "MACD_ZERO", "MACD_NEGATIVE",
    "MACD_ABOVE_SIGNAL", "MACD_AT_SIGNAL", "MACD_BELOW_SIGNAL",
    "RSI_CURRENT", "BB_WIDTH_CURRENT",
]
EvidenceRole = Literal["SUPPORTS_COMPRA", "SUPPORTS_VENDA", "CAUTION", "NEUTRAL"]
EVIDENCE_CODES = get_args(EvidenceCode)


class TechnicalEvidence(StrictModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    code: EvidenceCode
    role: EvidenceRole


class TechnicalEvidenceResponse(StrictModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    signal: Literal["COMPRA", "VENDA", "MANTER"]
    confidence: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    evidence: list[TechnicalEvidence] = Field(min_length=1, max_length=7)
