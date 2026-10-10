# CAL_B4_PROTOCOL_FREEZE_V1

Protocolo ex ante para uma única abertura da seleção CAL-B4 existente. O freeze
não autoriza egress: a autorização H2 v6 development não cobre CAL-B4.
CAL-B4 permanece `SEALED — NOT EXECUTED` até autorização específica e identidade
integralmente verificada. Não criar CAL-B5 nem executar Validation, Final Test ou
System Freeze.

## Identidade e provenance

H2 treatment 6; Technical prompt 5; Technical response schema 2; evidence vocabulary
1; evidence validator 1; Risk prompt 2. Technical, Risk, Portfolio, renderer,
validator e checkers permanecem byte-identical. A resposta Technical contém somente
`signal + confidence + evidence[{code, role}]`; o renderer determinístico nunca é
enviado a um LLM.

Configuração final: volatility_window 21, risk_max_volatility 0.50,
risk_max_drawdown 0.25, risk_max_concentration 1.0 e long_target_weight 1.0.
CAL-A selecionou C2 por EMPIRICAL_S1: empate C2/C3/C6, menor config_id.
Sequential selecionou D01 por EMPIRICAL_S2: empate D01/D03, menor config_id.
Esses empates não demonstram superioridade robusta.

Gemini native, host `generativelanguage.googleapis.com`, modelo
`gemini-3.8-flash`, thinking LOW, temperature 1.0, max_output_tokens 8192,
sem seed transmitida. N=5, consensus_threshold=0.6, require_all_votes=true.
Manter retry_attempts=6 e retry_base_delay=2.0, apenas para erros transitórios
de infraestrutura; nunca repetir uma resposta científica inválida.

O development summary contém `final_v6_params`, mas NÃO contém `spec_hash`.
Os ExperimentSpec hashes do Stress incluem janelas e são distintos. Nenhum deles
será substituído ou editado. O hash canônico do ParticipantSpec final, calculado
pelo helper histórico `run_cal_b.spec_sha256` sobre os parâmetros já presentes em
todos os manifests de Stress, é
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
A adoção desse identificador exige esclarecimento explícito do usuário antes do
live; não declarar que esse campo existia no summary. O arquivo de freeze JSON
registra os hashes originais por janela, os arquivos e a ausência do campo.

Commitment integral:
`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Usar exatamente as dez anchors e a ordem de `selection.json`; seleção permanece
byte-identical. Antes de abrir: reproduzir seed, candidatos, ranking e winners
somente com calendário e identities; confirmar ausência das anchors em todos os
decision identities de development. Não calcular features CAL-B4 nesse preflight.
Registrar CAL_B4_HOLDOUT_INTEGRITY=PRESERVED somente com todas essas verificações.

## Autorização e one-shot

Autorização limitada deve conferir phase CAL-B4, commitment integral, anchors
exatas em ordem, R=1, treatment=6, Technical prompt=5, schema=2, vocabulary=1,
validator=1, Risk prompt=2, hash final aprovado e host nativo. Qualquer diferença
falha fechado. `CAL_B_AUTHORIZED` global permanece False. Exigir autorização
externa específica, commitada, que aceite cobrança e payloads científicos
necessários; secrets/.env, dados arbitrários, Validation e Final são excluídos.

Cada anchor recebe participante novo, cinco votos Technical live independentes,
Risk/Portfolio no fluxo congelado, posição inicial zero e capital 100000.
Sem call bank, memória entre anchors, resposta development ou rerun comportamental.
Snapshot B3 COTAHIST OHLCV + Yahoo adjustment + calendário B3, CostSpec e execução
fractional_notional são os existentes no Stress. Information set somente até
close(t). Não acessar preço t+1 nem executar ordem. FINANCIAL_OUTCOME=NOT COMPUTED.

Executar lote fechado sem mostrar decisões intermediárias. Persistir respostas
raw com fsync antes de seguir; selar artefatos e hashes; commitar raw batch;
somente depois abrir/calcular audit packet. Resposta científica utilizável consome
a anchor. Crash após persistência admite apenas replay da mesma identity e raw
response. Anchor consumida não admite nova inferência para completar/substituir
respostas. Recovery impossível: CAL_B4_INVALID — PARTIAL HOLDOUT CONSUMED.
Gate obrigatório falhou: parar, sem editar tratamento/gates e sem rerun.

## Gates automáticos literais

| Gate | Condição PASS |
|---|---|
| CB4-A | 10/10 complete decisions; zero falha final provider/infrastructure |
| CB4-E | Zero Technical structured response inválida: schema estrito, extras, vocabulary/request-specific membership, uniqueness, roles, evidence não vazia, confidence 0..1 |
| CB4-S | Zero quorum incompleto, truncation, fallback, versão divergente, input científico ausente ou inversão |
| CB4-C | Zero post-t/future leakage, ticker/data/preço absoluto no Technical, Validation/Final access; oito features e allowed set exatamente iguais ao recálculo causal |
| CB4-HR | Zero violação das hard rules congeladas |
| CB4-S1 | Zero contradição semântica do checker congelado sobre renderer determinístico |
| CB4-S2 | Zero unsupported transition no mesmo checker |
| CB4-S3 | Zero unsupported implicit temporal state claim no mesmo checker |
| CB4-R1 | Zero threshold de confidence ou regra numérica não fornecida no Risk checker congelado |
| CB4-R2 | Zero confidence-only decision no mesmo Risk checker |
| CB4-R3 | Zero genuine verdict-text contradiction no mesmo Risk checker |
| CB4-D | total_hold_rate < 0.90 usando causas HOLD-equivalent congeladas; 9/10 e 10/10 falham |

Drawdown/concentration zero no estado inicial; coverage não exercida é diagnóstico,
não falha. Nenhum mínimo de BUY, SELL ou Risk veto. Zero veto discricionário é
RISK_LLM_DISCRETIONARY_VETO=NOT_OBSERVED. Reportar calls/approved/vetoed/rate,
Technical COMPRA/VENDA/MANTER, ACTION_BUY/ACTION_SELL/TECH_EXPLICIT_HOLD/
TECH_NO_MAJORITY, Risk veto e Portfolio hold/noop. Nenhum outcome financeiro.

Economics: logical calls, HTTP attempts, retries, transient/final errors, p50/p90
latency e input/output/thinking tokens. Sem custo monetário sem pricing congelado.

## Revisão e status

Depois do commit raw e gates automáticos, criar `review/PRIMARY_AUTHOR.json` em
branco, com PASS/FAIL obrigatório por anchor nos quatro campos:
technical_evidence_factual_validity, technical_role_signal_coherence,
material_unsupported_claim, rationale_action_coherence. Nunca preencher pelo autor.
Evidence factual validity compara snapshot/allowed set. Role/signal coherence
falha somente por incoerência material evidente: nenhuma regra determinística
entre roles e signal, e discordar da recomendação não é FAIL. Unsupported claims
incidem principalmente em Risk/Portfolio e texto não determinístico. Coerência
compara Risk rationale/verdict e Portfolio rationale/action/verdict.

Qualquer automatic gate FAIL: CAL_B4_FAIL — HOLDOUT CONSUMED.
Todos automatic gates PASS: CAL_B4_AWAITING_PRIMARY_AUTHOR_REVIEW.
Qualquer campo humano FAIL: CAL_B4_FAIL — HOLDOUT CONSUMED, mesmo com ficha parcial.
Todos os quatro campos de todas as dez anchors PASS:
CAL_B4_PASS — SANITY CHECK ONLY; SYSTEM_CALIBRATION_COMPLETE=True,
H2_FINAL_TREATMENT_VERSION=6, H2_FINAL_PARAMETERS=21/0.50/0.25/1.0,
READY FOR SYSTEM FREEZE DESIGN. Não realizar System Freeze.
Segunda revisão: NOT_REVIEWED — NONBLOCKING.

Commits separados: errata; protocolo; autorização limitada/guards; raw sealed
batch; automatic gates/packet; primary review preenchida pelo usuário; status final.
Freeze científico imutável após este commit. Guardas operacionais serão hashados e
commitados antes de qualquer chamada. Nenhum resultado CAL-B4 existe neste freeze.
