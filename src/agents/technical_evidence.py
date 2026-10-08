"""H2 v6 current-state contract, separate from the frozen linguistic checker."""

from typing import Literal, get_args
from collections.abc import Mapping

from pydantic import ConfigDict, Field

from src.agents.state import StrictModel
from src.agents.features import FEATURE_KEYS, canonical_number, canonical_prompt_json

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


def canonical_features(features: Mapping[str, float]) -> dict[str, float]:
    if set(features) != set(FEATURE_KEYS):
        raise ValueError("structured Technical requires exactly the eight features")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in features.values()):
        raise ValueError("features must be finite numbers")
    values = {key: canonical_number(features[key]) for key in FEATURE_KEYS}
    if not 0 <= values["rsi"] <= 100 or values["bb_width"] < 0:
        raise ValueError("invalid current RSI or band width")
    # Positive price/reference ratios preserve the gap ordering; no epsilon.
    if any(values[k] <= -1 for k in ("sma50_gap", "sma200_gap", "bb_upper_gap", "bb_lower_gap")):
        raise ValueError("price/reference ratios must be positive")
    if values["bb_upper_gap"] > values["bb_lower_gap"]:
        raise ValueError("inconsistent Bollinger band order")
    if values["bb_upper_gap"] == values["bb_lower_gap"] == 0:
        raise ValueError("coincident band boundaries have no unique vocabulary code")
    return values


def _relation(value: float, above: str, at: str, below: str) -> str:
    return above if value > 0 else below if value < 0 else at


def allowed_evidence_codes(features: Mapping[str, float]) -> list[str]:
    f = canonical_features(features)
    upper, lower = f["bb_upper_gap"], f["bb_lower_gap"]
    band = ("CLOSE_ABOVE_BB_UPPER" if upper > 0 else "CLOSE_AT_BB_UPPER" if upper == 0
            else "CLOSE_BELOW_BB_LOWER" if lower < 0 else "CLOSE_AT_BB_LOWER" if lower == 0
            else "CLOSE_INSIDE_BOLLINGER")
    return [
        _relation(f["sma50_gap"], "CLOSE_ABOVE_SMA50", "CLOSE_AT_SMA50", "CLOSE_BELOW_SMA50"),
        _relation(f["sma200_gap"], "CLOSE_ABOVE_SMA200", "CLOSE_AT_SMA200", "CLOSE_BELOW_SMA200"),
        band,
        _relation(f["macd_ratio"], "MACD_POSITIVE", "MACD_ZERO", "MACD_NEGATIVE"),
        _relation(f["macd_ratio"] - f["macd_signal_ratio"], "MACD_ABOVE_SIGNAL", "MACD_AT_SIGNAL", "MACD_BELOW_SIGNAL"),
        "RSI_CURRENT", "BB_WIDTH_CURRENT",
    ]


def evidence_user_prompt(features: Mapping[str, float]) -> str:
    f = canonical_features(features)
    return canonical_prompt_json({"features": f, "allowed_evidence_codes": allowed_evidence_codes(f)})


def validate_technical_evidence(response, features, allowed_codes) -> TechnicalEvidenceResponse:
    value = TechnicalEvidenceResponse.model_validate(
        response.model_dump(mode="json") if isinstance(response, TechnicalEvidenceResponse) else response)
    expected = allowed_evidence_codes(features)
    if list(allowed_codes) != expected:
        raise ValueError("allowed evidence set differs from the canonical feature facts")
    codes = [item.code for item in value.evidence]
    if len(codes) != len(set(codes)) or len(codes) > len(expected) or not set(codes) <= set(expected):
        raise ValueError("INVALID_RESPONSE: evidence must be unique and allowed for this request")
    return value


EVIDENCE_DISPLAY = {
    "CLOSE_ABOVE_SMA50": "fechamento acima da SMA50",
    "CLOSE_AT_SMA50": "fechamento na SMA50",
    "CLOSE_BELOW_SMA50": "fechamento abaixo da SMA50",
    "CLOSE_ABOVE_SMA200": "fechamento acima da SMA200",
    "CLOSE_AT_SMA200": "fechamento na SMA200",
    "CLOSE_BELOW_SMA200": "fechamento abaixo da SMA200",
    "CLOSE_ABOVE_BB_UPPER": "fechamento acima da banda superior de Bollinger",
    "CLOSE_AT_BB_UPPER": "fechamento na banda superior de Bollinger",
    "CLOSE_INSIDE_BOLLINGER": "fechamento dentro das bandas de Bollinger",
    "CLOSE_AT_BB_LOWER": "fechamento na banda inferior de Bollinger",
    "CLOSE_BELOW_BB_LOWER": "fechamento abaixo da banda inferior de Bollinger",
    "MACD_POSITIVE": "MACD acima de zero",
    "MACD_ZERO": "MACD em zero",
    "MACD_NEGATIVE": "MACD abaixo de zero",
    "MACD_ABOVE_SIGNAL": "MACD acima da linha de sinal",
    "MACD_AT_SIGNAL": "MACD na linha de sinal",
    "MACD_BELOW_SIGNAL": "MACD abaixo da linha de sinal",
}
ROLE_DISPLAY = {"SUPPORTS_COMPRA": "suporte à COMPRA", "SUPPORTS_VENDA": "suporte à VENDA",
                "CAUTION": "cautela", "NEUTRAL": "neutro"}


def technical_evidence_ui(response, features, allowed_codes) -> dict:
    value = validate_technical_evidence(response, features, allowed_codes)
    f = canonical_features(features)
    displays = {**EVIDENCE_DISPLAY, "RSI_CURRENT": f"RSI atual = {f['rsi']}",
                "BB_WIDTH_CURRENT": f"largura relativa atual das bandas = {f['bb_width']}"}
    items = [{**item.model_dump(), "display": displays[item.code]} for item in value.evidence]
    explanation = "; ".join(f"{item['display']} — classificado pelo analista como {ROLE_DISPLAY[item['role']]}"
                            for item in items)
    return {"signal": value.signal, "confidence": value.confidence, "evidence": items,
            "display_explanation": explanation}


def render_technical_evidence(response, original_feature_payload, allowed_facts) -> str:
    return technical_evidence_ui(response, original_feature_payload, allowed_facts)["display_explanation"]
