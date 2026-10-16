"""Structured Technical prompt; historical prompts and checker are immutable."""

import hashlib

from src.agents.feature_semantics import TECHNICAL_SYSTEM_PROMPT_V2, _SCHEMA

STRUCTURED_TECHNICAL_CONTRACT = """Do not write a textual market narrative.

Do not explain how the state changed over time.

Select evidence only from the current-state evidence codes provided with this request.

The evidence codes are factual current-state observations derived deterministically from the feature payload.

Your role labels are your qualitative interpretation of those facts.

Return only the structured JSON required by the schema.

Select a relevant nonempty subset of the supplied allowed_evidence_codes, without duplicates.
For each selected code assign SUPPORTS_COMPRA, SUPPORTS_VENDA, CAUTION, or NEUTRAL.
Any role may be assigned to any allowed fact; it is your qualitative interpretation.
Choose signal COMPRA, VENDA, or MANTER from the current quantitative configuration.
Choose confidence between 0 and 1 as qualitative, uncalibrated self-reported metadata.
Confidence is not a probability, decision threshold, or position-sizing input.
Return exactly signal, confidence, and evidence [{code, role}]. No textual justification or additional fields."""

assert TECHNICAL_SYSTEM_PROMPT_V2.endswith(_SCHEMA)
TECHNICAL_SYSTEM_PROMPT_V5 = TECHNICAL_SYSTEM_PROMPT_V2.removesuffix(_SCHEMA) + STRUCTURED_TECHNICAL_CONTRACT
TECHNICAL_SYSTEM_PROMPT_V5_SHA256 = hashlib.sha256(TECHNICAL_SYSTEM_PROMPT_V5.encode("utf-8")).hexdigest()
