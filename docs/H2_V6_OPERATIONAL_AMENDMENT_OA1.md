# H2 v6 — Amendment operacional OA-1: Validation provisória autorizada somente pelo autor

**Identidade:** `H2-V6-OA1`. **Estado:** PROPOSTO — sem efeito até aceite manual do autor.
Branch `#1-Update`. Redigido em 09/10/2026, America/Sao_Paulo, antes de qualquer
execução da Validation. O SHA256 deste arquivo é vinculado pelo registro de aceite;
qualquer alteração posterior invalida o aceite.

## 1. Motivo e alcance

O autor deseja avançar operacionalmente sem aguardar, neste momento, as manifestações
do coautor e do orientador (bloqueios A1–A3 do
[relatório de integração](H2_V6_EVALUATION_PRODUCTION_INTEGRATION.md)).

O guard existente (`require_authorization`, modo não sintético) exige manifesto
`APPROVED / FROZEN`, três manifestações humanas e registro de System Freeze. Ele
**impede** uma execução autorizada somente pelo autor. OA-1 **não altera esse guard**
nem qualquer byte inventariado no candidato. Cria uma rota separada, com identidade própria:

| Item | Rota oficial (inalterada) | Rota OA-1 |
|---|---|---|
| Entrypoint | `scripts/run_h2_v6_evaluation.py` | `scripts/run_h2_v6_provisional.py` |
| Manifesto | definitivo `APPROVED / FROZEN` | candidato `dc118ce9…` verificado integralmente, estado inalterado |
| Autorização | 3 manifestações + freeze + consentimento da fase | aceite do autor `H2_V6_AUTHOR_PROVISIONAL_OPERATIONAL_AUTHORIZATION` |
| Fases | Validation, depois Final | **somente Validation** |
| Saída | `data/runs/h2_v6_evaluation/VALIDATION` | `data/runs/h2_v6_provisional/VALIDATION` |
| Identidade dos runs | `H2-V6-VALIDATION-…` | `H2-V6-OA1-VALIDATION-…`, plano com `mode` próprio |
| Rótulo | resultado científico | `AUTHOR_PROVISIONAL_OPERATIONAL — NOT ACADEMICALLY RATIFIED` |

## 2. O que é preservado integralmente

Tratamento H2 v6 (ParticipantSpec `7858beb4…`), CAL-B4 e seus selos, SF-B1..SF-B6,
Bootstrap A, benchmarks (B&H, SMA Regime, Bollinger Estado), parâmetros, custos
(5 bps + 0,032%; grade 0/5/10/20), snapshot reservado, janela da Validation
(decisões 2024-09-02..2025-08-28, settlement 2025-08-29), R=3, journal FULL,
reserva antes do transporte, recuperação replay-only e fail-closed.

A rota OA-1 reutiliza `EvaluationBatch` por subclasse. Substitui apenas: o guard de
autoridade (reconferido antes de **cada** transporte), a raiz de saída e o rótulo de
identidade. O candidato é verificado por `verify_manifest` (hashes de fontes,
documentos, bindings CAL-B4, ambiente, preservação, diff permitido e árvore limpa)
antes de abrir o snapshot e novamente nos limites de slot.

## 3. O que OA-1 não é

- Não é aprovação acadêmica, manifestação do coautor ou do orientador, nem System Freeze.
  Os campos `approvals`, `freeze_record` e `phase_authorizations` do candidato continuam `null`.
- Não autoriza Final Test. Nenhum caminho de OA-1 alcança `FINAL_TEST`; o checkpoint
  provisório é vinculado ao SHA do candidato e não satisfaz o gate oficial de Final.
- Não autoriza tuning, seleção ou reclassificação com base nos resultados. Uma
  identidade de plano divergente aborta o batch.
- Não autoriza substituir runs, votos ou chamadas. Falha irrecuperável permanece registrada.

## 4. Consequências que o autor aceita

1. **Observação antecipada do holdout de Validation.** Os resultados da janela de
   Validation ficam conhecidos antes da ratificação acadêmica. Se coautor ou orientador
   exigirem mudança de tratamento, protocolo ou análise, essa janela estará contaminada
   para o protocolo modificado.
2. **Status dos resultados.** Devem ser reportados como provisórios e não ratificados.
   Se e como a execução OA-1 poderá ser adotada como Validation oficial é decisão futura
   do coautor e do orientador, fora do escopo deste amendment.
3. **Custos e egress.** Chamadas reais à Gemini API (`generativelanguage.googleapis.com`),
   com cobrança normal, contendo apenas payloads científicos do protocolo.
4. **Falha irrecuperável.** Interrupção no meio de um slot (queda de processo, rede,
   energia, Ctrl+C), recusa do provedor ou retries esgotados tornam o slot
   irrecuperável: a recuperação é replay-only e nenhuma chamada substituta é feita.
   Uma Validation provisória incompleta exigiria novo amendment.

## 5. Ativação, revogação e registro

- **Ativação:** somente pelo próprio autor, executando
  `scripts/run_h2_v6_provisional.py authorize` com seu nome e a frase de confirmação
  que contém o prefixo do SHA deste documento, e commitando o registro gerado em
  `docs/evidence/h2_v6_provisional/AUTHOR_AUTHORIZATION_OA1.json`. O registro vincula
  este documento, o runner, o manifesto, o tratamento, R, runs, janela, snapshot, host,
  saída e o commit em que foi criado. Agentes e terceiros não criam este registro.
- **Execução:** exige árvore limpa, registro commitado e `--confirm` igual ao prefixo
  do SHA do registro.
- **Revogação:** antes da execução, remover o registro por commit. Depois de iniciada,
  a execução não é desfeita; os artifacts permanecem como evidência.
- **Selagem:** ao final, `audit` grava
  `docs/evidence/h2_v6_provisional/VALIDATION_PROVISIONAL_CHECKPOINT.json`
  (hashes de summary, custos, release, journal e todos os artifacts), a ser commitado.
  A ordem prospectiva (amendment → aceite → execução → checkpoint) fica no histórico Git.
