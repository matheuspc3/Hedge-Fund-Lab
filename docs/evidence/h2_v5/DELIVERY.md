# H2 v5 — delivery report

**H2_V5 TEMPORAL CONTRACT FIX FAILED**

## H2 V4 FINAL GOVERNANCE

H2_V4 TEMPORAL CONTRACT FIX FAILED; H2_V4_NOT_ELIGIBLE_FOR_SYSTEM_FREEZE = True.
Reason: DEFECT-DIRECTED HARDENING FAILED V4-S3. Existing v4 evidence preserved.

## H2 V5 CHANGESET

[Amendment 13](../../H2_V5_AMENDMENT_13.md). Only Technical v3 -> v4 snapshot/temporal language.
Treatment 5; Technical 4; Risk 2; feature schema 2. All other treatment settings unchanged.
Participant spec SHA-256:

- v4: `a75b9e783cdc48b1098267c64bd22f47f45157b8e2cc4898711e418b01ebeb19`
- v5: `44f218c21ade5b95d98f119b17b169570a31fe6a5812d982d9e08770de909e9e`

## EXACT TECHNICAL PROMPT V4

[Exact UTF-8 prompt](technical_prompt_v4.txt); SHA-256 `f20bc8140cf10ad35fde876a291298b7a1a124e08081a5b1186b4eb600862077`.

## SNAPSHOT-ONLY STRICT CONTRACT

Only current snapshot statements. Persistence/evolution forbidden. Current trend, current momentum and mathematical RSI lookback allowed. Five explicit PASS/FAIL pairs tested; MANTER unchanged.

## CHECKER IMMUTABILITY AUDIT

Checker v3 byte-identical; no recalibration. [Pre-live audit](pre_live_audit.json), [offline regression](checker_regression.json).

| Source | SHA-256 | Git blob |
|---|---|---|
| src/agents/feature_semantics.py | `fb2cfa36feba26b5e8f622828e03aa8fcfd25b1f7a0567d387f82baf9f056169` | `57c0b1b0548455b897fdf0149c177a9bcd7b2557` |
| scripts/h2_v4.py | `630e7d8f862d4b5ffe5d8052911928e23f51634eaafcc88292ae0ef74a539f8e` | `672f6931ce19254acb147a2bc93705f542018ea1` |

## V4 BASELINE VIOLATIONS

Original 10/150 S3 flags reproduced exactly; S1=S2=0. No v4 results corrected.

## CAL-B4 CARRY-FORWARD AUDIT

CAL_B4_CARRIED_FORWARD_TO_H2_V5 = True; CAL_B4_HOLDOUT_INTEGRITY = PRESERVED.
Calendar/date/commitment reproduced; runner and call-bank guards block all ten dates before network. No CAL-B4 development decision identity found.

## CAL-B4 COMMITMENT

Existing `35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`. Selection file byte-identical; no new commitment/CAL-B5.

## DEFECT-DIRECTED HARDENING V5

H2_V5 MINIMAL DEFECT FIX PASSED; 150/150 Technical outputs.

Targets: 2020-05-13 and 2022-03-11. Decisions may remain MANTER; only current-state rationale fidelity is tested.

2020-05-13: S1=0, S2=0, S3=0/15; actions [{'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}, {'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}, {'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}].

2022-03-11: S1=0, S2=0, S3=0/15; actions [{'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}, {'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}, {'technical_outcome': 'MANTER', 'portfolio_decision': 'MANTER', 'final_cause': 'TECH_EXPLICIT_HOLD'}].

## TEMPORAL CLAIM RATE

| Evidence | Claims / outputs | Rate |
|---|---|---|
| v3 consumed CAL-B3 (R=1) | 16/50 | 32% |
| v4 defect (R=3) | 10/150 | 6.67% |
| v5 defect (R=3) | 0/150 | 0.00% |

Descriptive development evidence with different R; no future-performance claim.

| V5 phase | Claims / unique Technical responses | Rate |
|---|---|---|
| Defect-directed hardening v5 | 0/150 | 0.0000% |
| Hardening v5 | 0/300 | 0.0000% |
| B0 v5 | 0/60 | 0.0000% |
| CAL-A v5 | 0/300 | 0.0000% |
| Sequential Development v5 | 4/1905 | 0.2100% |

## V5 GATE TABLE

The following are the original defect-directed gates. Their PASS is preserved. Full development later failed the same zero-S3 language contract (Sequential: 4/1905); progression stopped before Stress.

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| V5-S1 | == 0 | 0 | PASS |
| V5-S2 | == 0 | 0 | PASS |
| V5-S3 | == 0 | 0 | PASS |
| V5-A | == 0 | 0 | PASS |
| V5-T | == 0 | 0 | PASS |
| V5-D | < 0.90 | 0.43333333333333335 | PASS |

## HARDENING V5

Evidence: [docs/evidence/h2_v5/hardening_low_20261007T232735Z/manifest.json](hardening_low_20261007T232735Z/manifest.json).

```json
{
  "G-A": {
    "value": 0,
    "threshold": "== 0",
    "pass": true
  },
  "G-T": {
    "value": 0,
    "threshold": "== 0",
    "pass": true
  },
  "G-I": {
    "value": 0.48333333333333334,
    "threshold": "< 0.90",
    "pass": true
  },
  "G-F": {
    "value": 0.0,
    "threshold": "<= 0.10",
    "pass": true
  }
}
```

## B0 V5

Evidence: [docs/evidence/h2_v5/b0_low_20261007T233307Z/manifest.json](b0_low_20261007T233307Z/manifest.json).

```json
{
  "G-A": {
    "value": 0,
    "threshold": "== 0",
    "pass": true
  },
  "G-T": {
    "value": 0,
    "threshold": "== 0",
    "pass": true
  },
  "G-I": {
    "value": 0.5,
    "threshold": "< 0.90",
    "pass": true
  },
  "G-F": {
    "value": null,
    "threshold": "<= 0.10",
    "pass": true
  }
}
```

## CAL-A V5

Evidence: [docs/evidence/cal_a_v5/run_20261007T233451Z/summary.json](../cal_a_v5/run_20261007T233451Z/summary.json).

360/360 evaluations; 60/60 paired Technical realizations; audit S1/S2/S3=0/300.
CAL_A_V5_DISCRIMINATION = NONE; CAL_A_V5_SELECTION_BASIS = PROTOCOL_TIE_FALLBACK.
All six S1 scores identical; C1 (21 / 0.40) selected by lowest config_id. No superiority claim.
```json
{
  "S1": {
    "1": -0.00017041605303383015,
    "2": -0.00017041605303383015,
    "3": -0.00017041605303383015,
    "4": -0.00017041605303383015,
    "5": -0.00017041605303383015,
    "6": -0.00017041605303383015
  },
  "ranking": [
    1,
    2,
    3,
    4,
    5,
    6
  ],
  "selected_config_id": 1,
  "paired_technical_audit": {
    "anchor_replicates": 60,
    "same_five_technical_responses_in_all_configs": true
  }
}
```
Two recovered transient failures: one timeout and one transport error; no final failure.

## SEQUENTIAL DEVELOPMENT V5

Evidence: [docs/evidence/sequential_dev_v5/run_20261007T234620Z/summary.json](../sequential_dev_v5/run_20261007T234620Z/summary.json).

9/9 runs; 381/381 session-replicates paired; last decision 2024-08-29, last data/settlement 2024-08-30.
SEQUENTIAL_DEV_V5_DISCRIMINATION = YES; SEQUENTIAL_DEV_V5_SELECTION_BASIS = EMPIRICAL_S2.
D02 (drawdown 0.15) selected by highest mean Scientific Sharpe; no top tie. R=3 development evidence only.
```json
{
  "S2": {
    "1": 0.07966809364534329,
    "2": 0.09194897902961162,
    "3": 0.07966809364534329
  },
  "ranking": [
    2,
    1,
    3
  ],
  "selected_config_id": 2,
  "sharpe_by_replicate": {
    "1": [
      0.3696834442274871,
      0.3696834442274871,
      -0.5003626075189443
    ],
    "2": [
      0.3696834442274871,
      0.3696834442274871,
      -0.4635199513661394
    ],
    "3": [
      0.3696834442274871,
      0.3696834442274871,
      -0.5003626075189443
    ]
  },
  "paired_technical_audit": {
    "session_replicates": 381,
    "decision_sessions": 127,
    "same_five_technical_responses_in_all_configs": true,
    "mismatched": []
  },
  "validation_audit": {
    "last_decision_session": "2024-08-29",
    "max_settlement_session": "2024-08-30",
    "max_data_end": "2024-08-30",
    "phase_end": "2024-08-30"
  }
}
```
Three recovered transient failures: one connection reset and two transport errors; no final failure.

**Temporal contract FAIL: 4/1905 (0.2100%), S1=S2=0.**

All four rationales asserted `enfraquecimento` rather than a current weak state; all four votes were MANTER.

- 2024-04-01, analyst 4: Os sinais são mistos entre a tendência mais longa e o enfraquecimento de médio prazo, justificando manutenção

- 2024-06-12, analyst 1: Diante do conflito entre a tendência de longo prazo e o enfraquecimento do momentum intermediário, a recomendação atual é MANTER

- 2024-08-06, analyst 3: Diante de sinais divergentes entre tendência de longo prazo e enfraquecimento no médio prazo, a recomendação é manter

- 2024-05-16, analyst 2: Essa divergência entre tendência de longo prazo e enfraquecimento dos indicadores de curto prazo justifica uma postura de cautela

## STRESS V5

NOT EXECUTED — STOP after Sequential Development S3 failure.

## FINAL V5 PARAMETERS

No parameters eligible for final freeze: v5 stopped before Stress. Recorded phase selections: window 21, max volatility 0.40, max drawdown 0.15, max concentration 1.0. Original input baseline: 21 / 0.50 / 0.25 / 1.0.

## CAL-B4 SAFETY

NOT EXECUTED — SEALED. No features, payloads, rationales, returns or Risk/checker evaluation for CAL-B4.

## VALIDATION / FINAL SAFETY

NOT EXECUTED. No v5 decision >=2024-09-02; scientific data capped at 2024-08-30.

## COMMITS CREATED

```text
10f9ff0 H2 v4 final governance: S3 failed, ineligible for System Freeze
3a419b2 Amendment 13: freeze H2 v5 language-only treatment and carry forward CAL-B4
272cae1 Technical Prompt v4: strict snapshot language with contract checks; checker v3 unchanged
8ff9dd8 CAL-B4 carry-forward: freeze v5 integrity audit, identical checker v3 and 10/150 regression
a253de3 H2 v5 phase runners: preserve frozen grids and gate full development on defect PASS
faaa228 H2 v5 delivery: 326 offline checks pass; preserve sealed holdouts and record live approval blocker
f9c050b H2 v5: record explicit Gemini egress authorization with sealed holdout limits
117bc25 H2 v5 defect hardening: all six gates PASS, S3 0/150, preserve live evidence
231156e H2 v5 Hardening and B0: frozen gates PASS, live Technical and sealed holdouts
33bc9f5 CAL-A v5: 360 paired evaluations complete, no discrimination, C1 by frozen tie-break
6d216ca Sequential Development v5: 9 paired runs complete, select D02 by frozen S2
f085335 H2 v5 final governance: stop on Sequential S3 4/1905; preserve directed PASS and block Stress
```

The commit containing this delivery is available in git log (a commit cannot contain its own hash).

## OFFLINE VERIFICATION

326 tests passed, 0 failed, 0 errors. Provider calls: 0.
Tests use mocks and synthetic data. Temporary-directory ACL limitations were resolved by running this offline check outside the sandbox.

Post-live: 134 targeted tests passed, 0 failed, 0 errors; provider calls: 0.
The shared phase guard refuses further development after S3 failure. Frozen prompt, checker, Risk, Portfolio, features and CAL-B4 commitment unchanged.

## NEXT STEP

STOP v5 after development S3 failure; no prompt/checker edits or rerun. A new user-authorized treatment/protocol decision is required; CAL-B4 stays sealed.
