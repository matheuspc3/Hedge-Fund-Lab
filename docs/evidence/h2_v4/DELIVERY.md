# H2 v4 — delivery report

**H2_V4 TEMPORAL CONTRACT FIX FAILED**

## CAL-B3 FINAL GOVERNANCE

CAL_B3_FAIL — HOLDOUT CONSUMED. All 10 automatic gates PASS; primary-author human review FAIL at 2020-05-13 and 2022-03-11. H2_V3_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True. Reason: CAL_B3 HUMAN REVIEW FAILURE — UNSUPPORTED TEMPORAL CLAIMS. Second review: NOT_REVIEWED — NONBLOCKING. Raw evidence, commitment, human review and historical v1/v2/v3 evidence preserved. No future return used.

## H2 V4 CHANGESET

Only treatment change: Technical Prompt v2 -> v3. Risk Prompt v2, Portfolio, eight features/schema v2, runtime, self-consistency, execution, data/calendar and costs unchanged. Audit checker v3 is separate from decisions. Spec v3: 1d63ad4cc93f9ef49368ba6772a22403354b36f3cc7d9d57d3b0627b85b9becc. Spec v4 defect: a75b9e783cdc48b1098267c64bd22f47f45157b8e2cc4898711e418b01ebeb19.

## EXACT TECHNICAL PROMPT V3

SHA256: `ca283bd920bbd0655d9c9a23eacd98fb6da48e6609097cb27cd835e9dee50759`

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

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.

Snapshot-only language:
You receive only the current-session snapshot t. Therefore describe only relations observable in that snapshot.

Allowed examples:
- "the close is above the SMA50"
- "MACD is below its signal line"
- "RSI is neutral"
- "the current configuration is mixed"
- "the current indicators do not provide a clear directional preference"

Do not describe or imply how the state evolved over time unless previous-session values are explicitly provided.
Do not claim that price, trend, momentum or any indicator:
- recovered;
- weakened;
- strengthened;
- accelerated;
- decelerated;
- improved;
- deteriorated;
- increased or decreased;
- reversed;
- rebounded;
- pulled back;
- consolidated or is consolidating;
- recently changed;
- continues/remains in a state based on previous observations;
- gained/lost momentum.

Avoid temporal language such as "recently", "recent recovery", "continues", "remains", "has weakened", or equivalent expressions when they imply an unobserved earlier state.
You may describe current momentum as positive, negative, strong, weak, mixed or neutral when that characterization follows from the current features. Do not say that momentum became stronger/weaker.
If the snapshot is conflicting, describe it simply as a mixed current state. Do not invent a temporal narrative to explain the conflict.
```

## TEMPORAL CONTRACT

Allowed: MACD currently above signal; current momentum positive/weak/mixed/neutral. Unsupported: strengthened/weakened/recovered/lost momentum/consolidating/persisting based on earlier observations. A conflicting snapshot is a mixed current state. MANTER semantics unchanged; action changes are not required.

## CHECKER V3

Visible rationale only, PT/EN clause/context patterns. UNSUPPORTED_TEMPORAL_STATE_CLAIM is separate from feature contradictions and explicit transitions. Negation/conditionals/nonmarket contexts are tested. The bounded heuristic cannot prove completeness over every paraphrase; new calibration requires consumed development evidence and a new checker version. No v4-output-driven retuning occurred.

Source blobs/hashes were committed before live in [pre_live_freeze.json](pre_live_freeze.json).

## CHECKER REGRESSION REPORT

Acceptance PASS. 11400 unique consumed/development responses; 48 golden FAIL (including four human rationales); 31 golden PASS. Zero golden misses; zero Bollinger/SMA/MACD or explicit-transition regressions. No CAL-B4 used. Tests: 783 agents/experiments + 12 CAL-B4 safety passed.

[Regression report](technical_checker_v3/calibration_report.json) · [Golden corpus](technical_checker_v3/golden_corpus.json)

## CAL-B4 SELECTION

| Stratum | B1 | B2 | B3 | B4 |
|---:|---|---|---|---|
| 3 | 2018-07-19 | 2018-08-16 | 2018-08-03 | 2018-08-21 |
| 6 | 2019-03-07 | 2019-04-05 | 2019-03-19 | 2019-01-29 |
| 9 | 2019-10-15 | 2019-10-07 | 2019-10-18 | 2019-10-28 |
| 12 | 2020-06-01 | 2020-07-01 | 2020-05-13 | 2020-06-03 |
| 15 | 2021-01-13 | 2021-01-21 | 2021-01-06 | 2021-02-18 |
| 18 | 2021-08-20 | 2021-09-22 | 2021-08-17 | 2021-09-02 |
| 21 | 2022-03-31 | 2022-04-07 | 2022-03-11 | 2022-03-30 |
| 24 | 2022-11-04 | 2022-11-01 | 2022-11-29 | 2022-10-03 |
| 27 | 2023-06-15 | 2023-06-26 | 2023-05-12 | 2023-07-17 |
| 30 | 2024-01-22 | 2023-12-18 | 2024-01-11 | 2024-01-12 |

## CAL-B4 COMMITMENT

`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7` — SEALED.

Seed `aa821baf20c2f7f2d38cee8bf7c2f973050fccbb047d1c207be72df192d544b4`. Ranking hashes and complete exclusions: [selection.json](../cal_b4/selection.json). Minimum lexicographic SHA256 per stratum using only calendar and prior decision identity. Selection script commit e4fed89; commitment commit eed7576 preceded first provider call.

## DEFECT-DIRECTED HARDENING

10 consumed CAL-B3 anchors x R=3 x N=5. Technical v4 inferred live. No t+1.

| Gate | Value | PASS |
|---|---|---|
| V4-S1 | 0 | True |
| V4-S2 | 0 | True |
| V4-S3 | 10 | False |
| V4-A | 0 | True |
| V4-T | 0 | True |
| V4-D | 0.4 | True |

**2020-05-13**: v4 S1/S2/S3 = 0/0/6; technical actions ['MANTER', 'MANTER', 'MANTER']. All votes retained in raw traces.

**2022-03-11**: v4 S1/S2/S3 = 0/0/1; technical actions ['MANTER', 'MANTER', 'MANTER']. All votes retained in raw traces.

## TEMPORAL CLAIM RATE

| Evidence | Votes | Implicit temporal claim votes | Rate |
|---|---:|---:|---:|
| v3 consumed CAL-B3 | 50 | 16 | 32.00% |
| v4 defect development | 150 | 10 | 6.67% |

Descriptive comparison; different repetition counts and stochastic realizations. Zero observed findings would not prove that all unseen future rationales satisfy the contract.

## HARDENING V4

Not executed: defect-directed hardening did not pass; progression blocked.

## B0 V4

Not executed: defect-directed hardening did not pass; progression blocked.

## CAL-A V4

Not executed: defect-directed hardening did not pass; progression blocked.

## SEQUENTIAL DEVELOPMENT V4

Not executed: defect-directed hardening did not pass; progression blocked.

## STRESS V4

Not executed: defect-directed hardening did not pass; progression blocked.

## FINAL V4 PARAMETERS

Not selected: full development was not authorized after the defect gate result. The defect run used inherited v3 parameters 21 / 0.50 / drawdown 0.25; these are not a new final selection.

Runtime: gemini / gemini-3.8-flash / native API / thinking low / temperature 1.0 / max_output_tokens 8192 / no seed. N=5 / threshold 0.6 / require_all_votes=true. Technical prompt 3 / Risk prompt 2 / feature schema 2.

## CAL-B4 SAFETY

SEALED; executed=false; v4 decision intersections []. Runner and bank rejection tests passed before live; no CAL-B4 protocol/authorization added.

## VALIDATION / FINAL SAFETY

No scientific session >= 2024-09-02: []. Max v4 decision 2024-01-11; permitted development end remains 2024-08-30.

## COMMITS CREATED

```text
9407126 Finalize CAL-B3 primary review: FAIL, holdout consumed, v3 ineligible
b385500 Amendment 12: freeze minimal H2 v4 snapshot-only treatment and development protocol
369b8f4 Technical Prompt v3 and checker v3: freeze snapshot-only contract with offline regressions
e4fed89 CAL-B4: calendar-only deterministic selection script excluding all development decisions
eed7576 Seal CAL-B4 commitment before first H2 v4 live call; freeze checker blobs and safety checks
b733c97 H2 v4 defect hardening: temporal contract FAIL (10/150), preserve live evidence, stop progression
```

The delivery-summary commit follows this recorded evidence history.

## NEXT STEP

Stop v4 progression; preserve failure evidence. A new treatment/protocol decision is required; CAL-B4 stays sealed.
