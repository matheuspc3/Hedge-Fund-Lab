# CAL-B4 — entrega offline

Status: `CAL_B4_PROTOCOL_FROZEN — AWAITING_SPECIFIC_EXTERNAL_AUTHORIZATION_AND_SPEC_IDENTITY_CLARIFICATION`.
CAL-B4: `SEALED — NOT EXECUTED`. Nenhuma feature, payload, inferência, rationale ou
resultado financeiro CAL-B4 foi produzido. Validation e Final Test permanecem
intocados. System Freeze não executado. Chamadas externas desta preparação: zero.

## V6 documentation erratum

Commit `e3ae6a9`: somente as descrições Hardening/B0 no DELIVERY v6 foram corrigidas
para PASS e acrescidas dos marcadores DOCUMENTATION_ONLY, SCIENTIFIC_ARTIFACTS_CHANGED=False,
SCIENTIFIC_RESULTS_CHANGED=False. Nenhum manifest, trace, seleção ou resultado foi alterado.

## CAL-B4 protocol freeze

Commit `2e79e88`: `PROTOCOL_FREEZE_V1.md` + `protocol_freeze_v1.json`.
6752 arquivos existentes de código/evidência preservados por SHA256; as 12
ExperimentSpec identities originais de Stress também registradas. A implementação
limitada e os seus checks ficam em commit separado com `guards_freeze.json`.

## Final identity and parameters

Treatment 6; Technical prompt 5; response schema 2; vocabulary 1; validator 1;
Risk prompt 2. Gemini native `gemini-3.8-flash`, LOW, temperature 1.0, max tokens
8192, sem seed transmitida. N=5, quorum 0.6, todos os votos obrigatórios.
Parâmetros: 21 / 0.50 / 0.25 / 1.0, concentração 1.0.
C2 EMPIRICAL_S1 empatou com C3/C6 e venceu pelo menor ID; D01 EMPIRICAL_S2
empatou com D03 e venceu pelo menor ID. Sem afirmação de superioridade robusta.

O development summary não contém spec_hash. O ParticipantSpec final canônico,
verificado contra todos os manifests de Stress, resulta em
`7858beb47ea9b2be9ac870f4abb72f9422782e7ff30c975eba8f3255babe4938`.
Não foi inserido em nenhum artefato development nem confundido com ExperimentSpec
hash por janela. Adotar esse identificador depende de esclarecimento explícito.

## Commitment / authorization / one-shot audit

Commitment:
`35d3d468a3253538392314c158c8605867c283c864fbd99c9499c8fd276f6ae7`.
Selection byte-identical, seed/ranking/winners reproduzidos apenas com calendário;
dez anchors em ordem; nenhuma delas em decision identities de development.
`CAL_B4_HOLDOUT_INTEGRITY = PRESERVED`.

Autorização externa específica: PENDING. A autorização development não cobre
CAL-B4. `authorization_request.json` é somente um pedido em branco com
authorized=False, sem poder de execução. O guard exige autorização específica
commitada e identidade exata; global CAL_B_AUTHORIZED continua False.

Executor: `scripts/run_cal_b4.py`, reutilizando o executor histórico decision-only.
Participante novo por anchor; sem call bank ou memória. Raw provider envelope e
HTTP attempts persistidos com fsync. Anchor com journal existente admite somente
replay exato; missing identity bloqueia a rede. HTTP success sem envelope persistido
é falha fechada por fronteira de crash incerta. Raw seal e commit obrigatórios
antes do audit. Audit/review não podem sobrescrever pacote já produzido.
O loader limita as barras ao prefixo do calendário até a última anchor autorizada;
cada decisão usa history_until(t). Hash de integridade do snapshot não analisa
outcomes. Nenhuma execução em open(t+1).

## Automatic gate table

| Gate | Result | PASS/FAIL |
|---|---|---|
| CB4-A | NOT EXECUTED | PENDING |
| CB4-E | NOT EXECUTED | PENDING |
| CB4-S | NOT EXECUTED | PENDING |
| CB4-C | NOT EXECUTED | PENDING |
| CB4-HR | NOT EXECUTED | PENDING |
| CB4-S1 | NOT EXECUTED | PENDING |
| CB4-S2 | NOT EXECUTED | PENDING |
| CB4-S3 | NOT EXECUTED | PENDING |
| CB4-R1 | NOT EXECUTED | PENDING |
| CB4-R2 | NOT EXECUTED | PENDING |
| CB4-R3 | NOT EXECUTED | PENDING |
| CB4-D | NOT EXECUTED | PENDING |

Action distribution, structured Technical audit, Risk/Portfolio audits,
discretionary activity e operational economics live: NOT EXECUTED.
Não inferir PASS dos checks offline.

## Primary human review packet

Só será gerado após o raw batch commitado e os gates automáticos. Quatro campos
por anchor: technical_evidence_factual_validity, technical_role_signal_coherence,
material_unsupported_claim, rationale_action_coherence. Review permanece em branco
até o usuário preencher. Nenhuma regra determinística roles/signal; discordância
do sinal não constitui FAIL. Um FAIL material em qualquer campo já reprova.
Segunda revisão: `NOT_REVIEWED — NONBLOCKING`.

## Offline checks

60 passed: guardas de autorização/identidade/paths, threshold 0.90 literal,
revisão obrigatória, raw invalid-schema preservation, exact replay, missing-response
network refusal, transient retry, leitura limitada ao prefixo causal, calendar-only carry-forward, strict evidence
contract e ponte de auditoria sobre dados de Stress development já publicados.
O primeiro teste encontrou erro de permissão do sandbox em diretório temporário;
a execução no workspace autorizado passou integralmente. Nenhuma chamada externa.
Comando reproduzível em `offline_verification.json`.

## Financial outcome / safety / next step

`FINANCIAL_OUTCOME = NOT COMPUTED`.
Validation/Final: nenhuma feature/inferência/execução. System Freeze: não realizado.
Após autorização e esclarecimento de identidade: run one-shot, commit raw selado,
audit, commit pacote e parar para a revisão humana. Qualquer gate falho interrompe
o protocolo, sem correção/rerun. Somente revisão humana integralmente PASS permite
`CAL_B4_PASS — SANITY CHECK ONLY` e `READY FOR SYSTEM FREEZE DESIGN`.
