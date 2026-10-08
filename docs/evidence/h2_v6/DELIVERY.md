# H2 v6 delivery

H2_V6 PREPARED OFFLINE — AWAITING SPECIFIC EXTERNAL AUTHORIZATION

## H2 V5 FINAL GOVERNANCE

H2_V5 TEMPORAL CONTRACT FIX FAILED; SEQUENTIAL DEVELOPMENT V5 — S3 4/1905. Ineligible for System Freeze.
All original artifacts and four flagged responses remain byte-identical; intermediate selections are preserved; Stress NOT EXECUTED.

## H2 V6 CHANGESET

Treatment 6 / Technical prompt 5 / response schema 2 / evidence validator 1 / vocabulary 1.
Eight features/schema 2, Risk prompt 2, Portfolio, confidence semantics V1, runtime, quorum, data/cost and execution are unchanged.

## WHY FREE TEXT WAS REMOVED

V5 snapshot instructions still allowed 4 unsupported temporal claims among 1905 Sequential outputs. A closed current-fact contract removes factual free narration without selecting the model's signal or qualitative roles.

## TECHNICAL RESPONSE SCHEMA V2

Exactly signal, confidence, evidence [{code, role}]. Strict extra-property rejection, confidence 0..1; no justification, reasoning, comment or free string.
Exact JSON Schema: [technical_response_schema_v2.json](technical_response_schema_v2.json).

## EVIDENCE VOCABULARY

CLOSE_ABOVE_SMA50, CLOSE_AT_SMA50, CLOSE_BELOW_SMA50, CLOSE_ABOVE_SMA200, CLOSE_AT_SMA200, CLOSE_BELOW_SMA200, CLOSE_ABOVE_BB_UPPER, CLOSE_AT_BB_UPPER, CLOSE_INSIDE_BOLLINGER, CLOSE_AT_BB_LOWER, CLOSE_BELOW_BB_LOWER, MACD_POSITIVE, MACD_ZERO, MACD_NEGATIVE, MACD_ABOVE_SIGNAL, MACD_AT_SIGNAL, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT.

## ALLOWED-EVIDENCE GENERATION

Exactly eight canonical features; sign/zero comparison selects one SMA50, SMA200, band, MACD-zero and MACD/signal fact, plus current RSI and width. No epsilon thresholds. Inconsistent band order and coincident zero boundaries fail before provider calls. JSON user prompt contains only features and allowed_evidence_codes.

## EVIDENCE VALIDATOR

Schema + request-specific membership + nonempty unique subset of at most seven facts. Roles are free qualitative classifications, never hardcoded to code or signal. Invalid response is fail closed, without repair; v6 validation errors are replayable ValueError records.

## EXACT TECHNICAL PROMPT V5

SHA256: b041c5f03e20296f06f254629227b6a55978eb2aefccd1ba5eade33aac520a5d

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Do not write a textual market narrative.

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
Return exactly signal, confidence, and evidence [{code, role}]. No textual justification or additional fields.
```

## DETERMINISTIC RENDERER

Fixed Portuguese current-fact templates with each role explicitly attributed to the analyst. Canonical RSI/width values are rendered directly. No evolution, persistence or inference. Display never enters Risk, Portfolio or any other LLM request.

## TRACE / PROVENANCE CHANGES

Original raw provider output, validated structured response, allowed codes and display remain separate. Optional technical_evidence observation records treatment/prompt/schema/vocabulary/validator versions and prompt/schema/allowed/raw/validated/display SHA256 values plus UI serialization. Existing request identity already covers changed prompt and schema. Historical v1-v5 response schemas and requests stay reproducible.

## CHECKER V3 IMMUTABILITY AUDIT

feature_semantics.py and scripts/h2_v4.py remain byte-identical to their freeze. The original checker audits rendered text without recalibration. Offline regression reproduces v3 16/50, v4 10/150 and v5 Sequential 4/1905. The 1620-case renderer matrix has zero S1/S2/S3 flags.

## CAL-B4 CARRY-FORWARD AUDIT

CAL_B4_CARRIED_FORWARD_TO_H2_V6=True; PRESERVED. Same commitment/ranking reproduced using calendar/identity only; runner/bank guards passed with no inference. 1972 original v5 artifacts hashed and preserved.

## DEFECT-DIRECTED HARDENING V6

NOT EXECUTED. Ten consumed CAL-B3 anchors x R=3 x N=5; 150 live Technical outputs; no t+1. Gates E/S1/S2/S3/A/T ==0 and HOLD <.90. Any failure stops, with no edits/reruns. Targets 2020-05-13 and 2022-03-11 may remain MANTER.

## STRUCTURED EVIDENCE FAILURES

V6 live E results are pending for phases not executed; offline incompatible facts, duplicate codes, invalid roles and textual extras were rejected. No live PASS is inferred from tests.

## TEMPORAL CLAIM RATE

Rates below describe different phase corpora; they are not a paired estimate of treatment effects.

| Corpus | S3 / N | Rate |
|---|---:|---:|
| v3 consumed | 16/50 | 32% |
| v4 directed | 10/150 | 6.67% |
| v5 directed | 0/150 | 0% |
| v5 Hardening | 0/300 | 0% |
| v5 B0 | 0/60 | 0% |
| v5 CAL-A | 0/300 | 0% |
| v5 Sequential | 4/1905 | 0.21% |
| v6 defect | NOT EXECUTED/None | pending |
| v6 hardening | NOT EXECUTED/None | pending |
| v6 b0 | NOT EXECUTED/None | pending |
| v6 cal_a | NOT EXECUTED/None | pending |
| v6 sequential | NOT EXECUTED/None | pending |
| v6 stress | NOT EXECUTED/None | pending |

## HARDENING V6

NOT EXECUTED. Same 12 H states, R=5, original gates plus E/S1/S2/S3.

## B0 V6

NOT EXECUTED. Same H states, R=1, same ex ante baseline and gates.

## CAL-A V6

NOT EXECUTED. Same 20 anchors, six 21/63 x .40/.50/.60 candidates, R=3, original S1 and tie-break; new live Technical with within-phase pairing.

## SEQUENTIAL DEVELOPMENT V6

NOT EXECUTED. Same 2024-03-01 -> 2024-08-30 window, D01 .25/D02 .15/D03 .35, R=3, original Sharpe/S2/tie-break. The protocol requires auditing all 1905 unique Technical outputs. Four prior failure sessions are naturally re-evaluated here only.

Natural four-session results:

{"2024-04-01": "NOT EXECUTED", "2024-05-16": "NOT EXECUTED", "2024-06-12": "NOT EXECUTED", "2024-08-06": "NOT EXECUTED"}

## STRESS V6

NOT EXECUTED. Only after complete Sequential PASS: same four windows, R=3, original integrity gates plus E/S1/S2/S3; no tuning authority.

## FINAL V6 PARAMETERS

null — no final selection before all required phases pass.
Entry only: 21/.40/.15/1.0; V6_ENTRY_BASELINE_ONLY — NOT FINAL SELECTION. CAL-A and Sequential reselect independently.

## UI SERIALIZATION CONTRACT

signal, confidence, evidence [{code, role, display}], display_explanation; portable JSON, no frontend dependency.

## CAL-B4 SAFETY

SEALED / NOT EXECUTED. Commitment: 35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7

## VALIDATION / FINAL SAFETY

NOT EXECUTED; no v6 decision beyond 2024-08-30. Development engines retain their existing data boundaries.

## COMMITS CREATED

Commits through report generation (the delivery commit itself is recorded by git log):

- 61d16aa Record canonical v5 failure governance for v6
- ab7e84f Freeze H2 v6 structured Technical amendment
- beccc3b Add strict Technical response schema v2
- dd3eb17 Derive current facts and validate request-specific evidence
- 3a7844a Freeze Technical prompt v5 with structured current evidence
- 2977fc2 Render factual evidence and analyst roles for audit and UI
- a71b5d7 Audit CAL-B4 carry-forward to H2 v6 without inference
- 9c3a462 Integrate v6 evidence validation, provenance and guarded phase runners
- 18a0aa1 Freeze offline v6 checks, schema, prompt and provenance hashes

## NEXT STEP

Specific H2 v6 external authorization is required before first live call (user request item 40). V5 authorization does not carry to v6.
After authorization, execute directed hardening then conditional phases in frozen order. CAL-B4 remains sealed throughout.

Offline verification: 860 tests passed; zero external provider calls.
