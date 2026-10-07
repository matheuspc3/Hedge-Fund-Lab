# H2 v5 — delivery report

**H2_V5 LIVE NOT EXECUTED — AWAITING PROVIDER EGRESS APPROVAL**

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

NOT EXECUTED (no provider call)

Targets: 2020-05-13 and 2022-03-11. Decisions may remain MANTER; only current-state rationale fidelity is tested.

## TEMPORAL CLAIM RATE

| Evidence | Claims / outputs | Rate |
|---|---|---|
| v3 consumed CAL-B3 (R=1) | 16/50 | 32% |
| v4 defect (R=3) | 10/150 | 6.67% |
| v5 defect (R=3) | NOT EXECUTED | not measured |

Descriptive development evidence with different R; no future-performance claim.

## V5 GATE TABLE

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| V5-S1 | == 0 | not measured | NOT EXECUTED |
| V5-S2 | == 0 | not measured | NOT EXECUTED |
| V5-S3 | == 0 | not measured | NOT EXECUTED |
| V5-A | == 0 | not measured | NOT EXECUTED |
| V5-T | == 0 | not measured | NOT EXECUTED |
| V5-D | < 0.90 | not measured | NOT EXECUTED |

## HARDENING V5

NOT EXECUTED — requires prior gates/selection.

## B0 V5

NOT EXECUTED — requires prior gates/selection.

## CAL-A V5

NOT EXECUTED — requires prior gates/selection.

## SEQUENTIAL DEVELOPMENT V5

NOT EXECUTED — requires prior gates/selection.

## STRESS V5

NOT EXECUTED — requires prior gates/selection.

## FINAL V5 PARAMETERS

No final selection yet. Input baseline only: 21 / 0.50 / 0.25 / 1.0.

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
```

The commit containing this delivery is available in git log (a commit cannot contain its own hash).

## OFFLINE VERIFICATION

326 tests passed, 0 failed, 0 errors. Provider calls: 0.
Tests use mocks and synthetic data. Temporary-directory ACL limitations were resolved by running this offline check outside the sandbox.

## NEXT STEP

Provider egress approval, then run frozen defect hardening; later phases require PASS

Automatic approval review rejected the live command before process start: provider payload egress to the named Google Gemini endpoint requires explicit authorization. [Blocker record](execution_blocker.json).
