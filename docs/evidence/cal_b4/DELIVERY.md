# CAL-B4 / H2 v6 — execução one-shot e entrega

**CAL_B4_AWAITING_PRIMARY_AUTHOR_REVIEW**.
Os 12 gates automáticos passaram. São 10/10 decisões completas, 50 votos Technical
live únicos e 61 chamadas Gemini, sem retries ou falhas. O holdout foi consumido
uma única vez; nenhum rerun foi feito. A revisão humana obrigatória continua em
branco. SYSTEM_CALIBRATION_COMPLETE=False até a revisão integralmente PASS.

## V6 documentation erratum

`e3ae6a9`: descrições Hardening/B0 no delivery v6 corrigidas para PASS.
H2_V6_DELIVERY_ERRATUM=DOCUMENTATION_ONLY;
SCIENTIFIC_ARTIFACTS_CHANGED=False; SCIENTIFIC_RESULTS_CHANGED=False.
Manifests, traces, hashes e seleções development preservados.

## CAL-B4 protocol freeze

`2e79e88`: [protocolo](PROTOCOL_FREEZE_V1.md) e
[freeze JSON](protocol_freeze_v1.json). `09c9876`: guardas limitados, hash dos
guardas, pedido pendente e 60 checks offline PASS. Esses snapshots pre-live
permanecem intactos; seus campos PENDING/SEALED descrevem o momento do freeze.
A autorização posterior e os artefatos live abaixo registram a evolução.

## Final H2 v6 identity

Treatment 6; Technical prompt 5; response schema 2; evidence vocabulary 1;
evidence validator 1; Risk prompt 2; Portfolio e checkers byte-identical.
Gemini native em generativelanguage.googleapis.com; gemini-3.8-flash;
thinking LOW; temperature 1.0; max_output_tokens 8192; sem seed transmitida.
N=5, consensus_threshold=0.6, require_all_votes=true.

ParticipantSpec SHA256 integral:
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
O usuário confirmou esse hash explicitamente. Ele foi verificado antes da rede
e novamente no batch selado. O development summary não possui campo spec_hash;
nenhum campo foi acrescentado retroativamente. Os 12 ExperimentSpec hashes por
janela de Stress permanecem registrados no freeze como provenance original.

## Final development parameters

volatility_window=21; risk_max_volatility=0.50; risk_max_drawdown=0.25;
risk_max_concentration=1.0; long_target_weight=1.0.
CAL-A C2: EMPIRICAL_S1, empate C2/C3/C6, menor ID.
Sequential D01: EMPIRICAL_S2, empate D01/D03, menor ID.
Sem afirmação de superioridade robusta.

## CAL-B4 commitment audit

`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Selection permaneceu byte-identical. Seed, candidatos, rankings e winners foram
reproduzidos com calendário somente; dez anchors e ordem exatas. Antes do live,
nenhuma anchor aparecia em scientific development identities e nenhum payload
CAL-B4 foi produzido. CAL_B4_HOLDOUT_INTEGRITY=PRESERVED antes da abertura.
Depois do one-shot: dez anchors CONSUMED. Nenhuma CAL-B5 criada.

## CAL-B4 authorization audit

`0760f72`: [autorização específica](execution_authorization.json), dada por Lucas
Pereira da Silva após o freeze, aceitando cobrança normal, hash final exato e
somente os requests científicos congelados. Development authorization não foi
usada como autorização CAL-B4. Guard limitado conferiu commitment, phase, anchors,
R, versões, hash e host. Global CAL_B_AUTHORIZED permaneceu False.
Credencial local usada somente no header de autenticação nativo, sem inclusão
nos payloads/traces; nenhum arquivo .env ou secret enviado como conteúdo.

## One-shot audit / holdout consumption

Batch: [run_20261008T221200Z](run_20261008T221200Z/batch.json).
2026-10-08T22:12:00Z até 22:13:18Z; R=1, N=5 por anchor. Participante novo por
anchor, sem memória/call bank/resposta anterior. Recovery_used=False nas dez.
Nenhum rerun ou inferência de substituição. Raw provider envelope e tentativas
HTTP persistidos com fsync, seguidos dos selos de cada anchor e do batch.

`c5aa362`: 92 arquivos raw selados commitados ANTES de abrir/calcular os gates.
O audit registra audit_git_commit=c5aa362..., comprovando essa ordem. Batch seal,
90 hashes de arquivos por anchor e os dez hashes de seal foram conferidos.
Os 6.752 arquivos baseline e todos os guardas congelados continuam byte-identical.
Veja [verificação pós-live](post_live_verification.json).

## Automatic gate table

| Gate | Result | PASS/FAIL |
|---|---|---|
| CB4-A | 10/10 decisões; 0 falhas finais | PASS |
| CB4-E | 0 invalid structured Technical responses em 50 votos | PASS |
| CB4-S | 0 quorum/truncation/fallback/version/input/inversion issues | PASS |
| CB4-C | 0 causality issues; 8 features + allowed set iguais ao recálculo até t | PASS |
| CB4-HR | 0 hard risk violations | PASS |
| CB4-S1 | 0 semantic contradictions no renderer | PASS |
| CB4-S2 | 0 unsupported transitions | PASS |
| CB4-S3 | 0 unsupported implicit temporal state claims | PASS |
| CB4-R1 | 0 unsupported confidence thresholds/numeric rules | PASS |
| CB4-R2 | 0 confidence-only decisions | PASS |
| CB4-R3 | 0 genuine verdict-text contradictions | PASS |
| CB4-D | 4/10 HOLD-equivalent = 0.40 < 0.90 | PASS |

Fonte: [automatic_gates.json](run_20261008T221200Z/automatic_gates.json).
PASS automático é sanity check, não aprovação humana nem resultado financeiro.

## Action distribution

| Medida | Count |
|---|---|
| Technical votos COMPRA / VENDA / MANTER | 25 / 5 / 20 |
| Technical consenso COMPRA / VENDA / MANTER | 5 / 1 / 4 |
| ACTION_BUY / ACTION_SELL | 5 / 1 |
| TECH_EXPLICIT_HOLD / TECH_NO_MAJORITY | 4 / 0 |
| Risk veto | 0 |
| PORTFOLIO_HOLD / BUY_AT_TARGET_NOOP | 0 / 0 |

As dez anchors tiveram consenso unânime 5/5. Distribuição apenas descritiva:
nenhum mínimo BUY, SELL ou veto foi aplicado além do CB4-D congelado.

| Anchor | Technical consenso | Final cause |
|---|---|---|
| 2018-08-21 | VENDA | ACTION_SELL |
| 2019-01-29 | COMPRA | ACTION_BUY |
| 2019-10-28 | COMPRA | ACTION_BUY |
| 2020-06-03 | MANTER | TECH_EXPLICIT_HOLD |
| 2021-02-18 | COMPRA | ACTION_BUY |
| 2021-09-02 | MANTER | TECH_EXPLICIT_HOLD |
| 2022-03-30 | COMPRA | ACTION_BUY |
| 2022-10-03 | MANTER | TECH_EXPLICIT_HOLD |
| 2023-07-17 | MANTER | TECH_EXPLICIT_HOLD |
| 2024-01-12 | COMPRA | ACTION_BUY |

## Structured Technical audit

50/50 respostas estritas signal/confidence/evidence[{code,role}]. Zero schema
extra field, evidence fora do vocabulary/allowed set, duplicata, role inválido,
evidence vazio ou confidence inválida. Features e allowed set recalculados
causalmente e comparados exatamente. Renderer determinístico auditado pelo
checker v3 congelado, sem enviá-lo a qualquer LLM. Factual evidence, roles,
signal, confidence e provenance de todos os votos estão no packet/guia.
Role/signal coherence humana ainda não foi classificada.

## Risk audit / discretionary activity

5 chamadas LLM, 5 APROVADO, 0 VETADO: approval_rate=1.0, veto_rate=0.0.
RISK_LLM_DISCRETIONARY_VETO=NOT_OBSERVED — DESCRIPTIVE ONLY.
R1/R2/R3=0; checker Risk v2 e prompt byte-identical. VENDA/MANTER passaram pelo
auto-approve congelado. Hard risk: zero violações. Volatilidade, drawdown e
concentração não produziram hard veto nesta CAL-B4; coverage NOT_EXERCISED,
diagnóstico sem reprovação. Drawdown e posição iniciais zero por anchor.
Textos visíveis Risk permanecem para revisão humana de unsupported claims e
coerência analysis/verdict.

## Portfolio audit

6 chamadas: 5 COMPRA, 1 VENDA; zero inversão, response inválida ou Portfolio HOLD.
Quatro Technical MANTER encerraram o fluxo antes do Portfolio. Apenas decisões
e intents foram persistidos; nenhuma ordem foi executada. Prompt/contratos
Portfolio permanecem byte-identical. Reasoning/action/verdict aguardam revisão.

## Primary human review packet / second review status

Leia [REVIEW_GUIDE.md](run_20261008T221200Z/review/REVIEW_GUIDE.md), apresentação
determinística e compacta dos mesmos campos do packet, com features, allowed
evidence, todos os 50 votos, Risk/Portfolio payloads e textos visíveis.
O [packet completo](run_20261008T221200Z/AUDIT_PACKET.md) e o
[JSON](run_20261008T221200Z/audit_packet.json) preservam os traces/provenance.
Packet/gates originais protegidos por AUDIT_SEAL.json; guia tem SHA256 separado.

Preencha somente [PRIMARY_AUTHOR.json](run_20261008T221200Z/review/PRIMARY_AUTHOR.json):
reviewer, reviewed_utc e PASS/FAIL nos quatro campos de cada uma das dez anchors:
technical_evidence_factual_validity; technical_role_signal_coherence;
material_unsupported_claim; rationale_action_coherence. Os 40 campos continuam
null, sem classificação pelo assistente. Não exigir regra determinística entre
roles e signal nem reprovar por discordar da recomendação. FAIL apenas por
incoerência material clara/fato ou regra não fornecidos/coerência rationale/ação.
Qualquer FAIL reprova; todos os campos PASS são obrigatórios para PASS humano.
Segunda revisão: **NOT_REVIEWED — NONBLOCKING**.

## Financial outcome / operational economics

FINANCIAL_OUTCOME=NOT COMPUTED. Não calcular P&L, retornos, Sharpe, Sortino, MDD,
hit rate ou benchmark. Nenhum preço open(t+1) foi consultado para execução ou
avaliação. Snapshot/CostSpec/calendário/quantity mode/capital foram preservados;
o loader usa somente prefixo causal e cada decisão usa histórico até close(t).

| Métrica | Valor |
|---|---|
| Logical provider calls | 61 = 50 Technical + 5 Risk + 6 Portfolio |
| HTTP attempts | 61 |
| Retries / transient errors / final errors | 0 / 0 / 0 |
| Latency p50 / p90 | 2886.38 / 3508.25 ms |
| Input / output / thinking tokens | 59336 / 10328 / 360 |
| Monetário | NOT COMPUTED — NO FROZEN PRICING |

## Validation / Final safety / CAL-B4 status / next step

Validation e Final Test intocados; nenhuma feature/inferência/execução desses
domínios. System Freeze não executado. Nenhum tratamento/gate/threshold alterado.
Estado: **CAL_B4_AWAITING_PRIMARY_AUTHOR_REVIEW**. A execução live terminou e
parou obrigatoriamente para Lucas preencher a ficha.
SYSTEM_CALIBRATION_COMPLETE=False; CAL_B4_PASS ainda não foi declarado.
Somente após revisão integralmente PASS: CAL_B4_PASS — SANITY CHECK ONLY,
SYSTEM_CALIBRATION_COMPLETE=True e READY FOR SYSTEM FREEZE DESIGN.
Mesmo nesse caso, não executar System Freeze nesta task.

## Commits created

e3ae6a9 — errata documental v6;
2e79e88 — protocolo CAL-B4;
09c9876 — guardas limitados e checks offline;
0760f72 — autorização externa específica/hash confirmado;
c5aa362 — raw one-shot selado antes da auditoria.
O commit seguinte registra automatic gates, packet e ficha em branco;
o status intermediário é registrado separadamente. Ainda não há commit de
primary review preenchida nem de PASS humano/final.
