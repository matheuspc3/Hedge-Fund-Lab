# Amendment 14 — H2 treatment version 6

H2 v5 remains failed and ineligible: SEQUENTIAL DEVELOPMENT V5 — S3 4/1905.
All historical artifacts, four responses, checker v3, prompt v4, intermediate
selections and Stress NOT EXECUTED are preserved. Free-text Technical rationale
is removed because snapshot instructions still permitted residual temporal claims.

H2_TREATMENT_VERSION=6; technical_prompt_version=5;
TECHNICAL_RESPONSE_SCHEMA_VERSION=2; TECHNICAL_EVIDENCE_VALIDATOR_VERSION=1;
TECHNICAL_EVIDENCE_VOCABULARY_VERSION=1. Feature schema 2, all eight formulas,
Risk prompt v2 and Portfolio remain unchanged. The only Technical response is
signal, confidence and evidence [{code, role}]; no extra fields or free strings.
Confidence semantics V1 are unchanged. Consensus votes only signal; roles never
determine signal, confidence thresholds or sizing.

Closed vocabulary: CLOSE_{ABOVE,AT,BELOW}_SMA50 and SMA200;
CLOSE_ABOVE_BB_UPPER, CLOSE_AT_BB_UPPER, CLOSE_INSIDE_BOLLINGER,
CLOSE_AT_BB_LOWER, CLOSE_BELOW_BB_LOWER; MACD_{POSITIVE,ZERO,NEGATIVE};
MACD_{ABOVE,AT,BELOW}_SIGNAL; RSI_CURRENT; BB_WIDTH_CURRENT.
From the same canonical eight features derive exactly one fact per relation,
plus current RSI and width. Exact canonical zero is the boundary; no epsilon.
Reject inconsistent band order and ambiguous coincident boundaries rather than
inventing a fact. Allowed codes accompany the eight features in JSON.
Evidence is nonempty, unique, bounded by allowed count, and restricted to the
request's allowed set. Roles SUPPORTS_COMPRA, SUPPORTS_VENDA, CAUTION, NEUTRAL
are unrestricted qualitative interpretations. Invalid responses fail closed via
the existing INVALID_RESPONSE policy, with no correction or sanitization.

The renderer only translates current facts using fixed Portuguese templates,
with roles explicitly attributed to the analyst. It is display evidence only,
never returned to any LLM. Individual structured votes, raw provider output,
validated response, allowed codes and display are separately preserved, with
prompt/schema/allowed/raw/validated/display hashes and version provenance.
Risk receives the existing collective signal/confidence/consensus summary and
metrics, never individual evidence or display. Historical v1-v5 replay survives.
Checker v3 sources stay byte-identical and audit rendered text. E and linguistic
S1/S2/S3 are separate gates; expected zero for each.

Gemini gemini-3.8-flash native API; thinking LOW; temperature 1.0; 8192 tokens;
no transmitted seed; N=5; quorum .6; all votes required. Existing retry,
data/cost, strict inputs, inversion=fail, decision_frequency=1 and long target
1.0 remain frozen. Entry 21/.40/.15/1.0 is explicitly
V6_ENTRY_BASELINE_ONLY — NOT FINAL SELECTION. Hardening/B0 keep their original
ex ante baseline; CAL-A and Sequential must select afresh.

Directed hardening: exactly ten consumed CAL-B3 anchors, R=3, N=5, 150 live
Technical responses, no settlement/t+1/financial metrics. Targets 2020-05-13
and 2022-03-11 may remain MANTER. E/S1/S2/S3/A/T ==0; total HOLD <.90.
Any failed gate: H2_V6 STRUCTURED TECHNICAL FIX FAILED, STOP without edits or
reruns in this task. All pass: H2_V6 STRUCTURED TECHNICAL FIX PASSED.

Then Diagnostic Hardening (same H datasets R=5 and gates), B0 (R=1), CAL-A
(same 20 anchors, R=3, six 21/63 x .40/.50/.60 candidates, S1/tie-break),
Sequential (2024-03-01 through 2024-08-30, R=3, D01 .25, D02 .15, D03 .35,
same Sharpe/S2/tie-break), Stress (same four windows R=3, no tuning authority).
All v6 Technical outputs live; only within-phase exact-identity pairing.
E/S1/S2/S3 apply in every phase and stop progression on failure. Sequential
audits all 1905 unique Technical responses and naturally highlights 2024-04-01,
2024-05-16, 2024-06-12, 2024-08-06. No ad hoc live calls on those dates.
Stress requires complete Sequential PASS and all original integrity gates plus
E/S1/S2/S3. No result-dependent changes to prompts/checkers/gates/configuration.

CAL_B4_CARRIED_FORWARD_TO_H2_V6=True; integrity PRESERVED, same commitment
35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7.
No CAL-B5. Calendar/identity-only carry-forward audit and runner/bank guards
before first live. CAL-B4 SEALED / NOT EXECUTED throughout. Validation/Final
untouched; no decision after 2024-08-30 and engine data bounded accordingly.

V5 external authorization does not authorize v6. Complete implementation,
offline checks and committed freeze first, then obtain explicit v6 permission
before any live call. Conditional live phase commits record only executed work.
Only after all phases pass: H2_V6 DEVELOPMENT COMPLETE — READY FOR CAL-B4
PROTOCOL. CAL-B4 is never automatically executed.
