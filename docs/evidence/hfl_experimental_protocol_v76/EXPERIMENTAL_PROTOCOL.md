# Protocolo experimental de robustez — `HFL-V76-ROBUSTNESS-PROTOCOL` 1.0.0

**Estado:** `QUALIFIED_OFFLINE`, registrado em [EXPERIMENT_MANIFEST.json](EXPERIMENT_MANIFEST.json)
com o SHA-256 dos documentos do protocolo. **Não** congelado para avaliação,
**não** autorizado para execução paga, **não** executado.

Este documento é o protocolo integral. Os detalhes de cada parte estão em:
[REPETABILITY_DESIGN.md](REPETABILITY_DESIGN.md) (replicações),
[OUT_OF_SAMPLE_DESIGN.md](OUT_OF_SAMPLE_DESIGN.md) (sessões),
[PAPER_TRADING_PROTOCOL.md](PAPER_TRADING_PROTOCOL.md) (carteira simulada),
[BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md) (controles),
[SCENARIO_MATRIX.json](SCENARIO_MATRIX.json), [METRIC_CATALOG.json](METRIC_CATALOG.json),
[BUDGET_PLAN.json](BUDGET_PLAN.json). O pré-registro para revisão humana está em
[PREREGISTRATION_DRAFT.md](PREREGISTRATION_DRAFT.md).

## 1. Pergunta

Como avaliar sistematicamente se a arquitetura multiagentes (comitês técnicos →
Risk individual → Global PM → validador determinístico) gera decisões
consistentes, respeita os controles determinísticos e se comporta de forma
robusta em diferentes sessões e estados financeiros?

## 2. Cinco dimensões, nunca misturadas

| Dimensão | Pergunta | Evidência que responde | O que **não** se conclui dela |
|---|---|---|---|
| **A. Conformidade contratual** | A resposta atende schema, referências, pesos e invariantes? | status e códigos do validador V2 em respostas reais | qualidade econômica da decisão |
| **B. Segurança financeira e operacional** | As operações respeitam custódia, caixa, custos, concentração, risco e liquidação? | validação V5 nas respostas reais; matriz S0–S9 qualifica as regras | que o sistema reduz risco futuro |
| **C. Robustez e repetibilidade** | Com condições fixas, com que frequência há propostas válidas e como variam? | replicações independentes do mesmo cenário (C1) | generalização para outras sessões |
| **D. Sensibilidade ao estado da carteira** | Como a proposta muda com posições, caixa limitado, recebíveis, vetos? | campanhas C2 com estados S1–S9 | efeito causal de um componente da arquitetura |
| **E. Desempenho financeiro posterior** | Como decisões congeladas se comportariam diante de preços posteriores? | paper trading prospectivo (C4) e, com ressalvas, retrospectivo fora da amostra (C3), contra controles | superioridade sem desenho e amostra adequados |

Regras de leitura: conformidade (A) não implica boa decisão (E); uma proposta
conservadora não demonstra redução de risco futuro; um resultado rentável
isolado não demonstra superioridade estatística.

## 3. Tratamentos, fonte e controles

| Papel | Identidade | Hash | Observação |
|---|---|---|---|
| Tratamento avaliado | `HFL-MULTIASSET-GLOBAL-PM-V2` | contratos `159fd196…6590e2` | selado; o validador do protocolo exige `contracts()` atual = selado no registro `v74-76d0…` |
| Fonte de pareceres | `HFL-MULTIASSET-RADAR-V1` | manifesto `77d75777…5bef` | execução `radar-2026-10-09-recovery-01` (C1, C2) ou novas execuções registradas (C3, C4) |
| Histórico, fechado | `HFL-MULTIASSET-GLOBAL-PM-V1` | contratos `faf633a1…4eda70` | nunca replicado, nunca agrupado com V2 (o validador recusa) |
| Controles | determinísticos | — | [BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md) |

Qualquer mudança de prompt, schema, contrato, configuração (inclusive o teto de
orçamento selado em `CONFIG`) ou política de validação cria **outro
tratamento**, com identidade própria. O H2 v6 está fora do escopo: nenhuma
campanha pode referenciá-lo, e nenhuma sessão pode cair nas janelas H2
(VALIDATION 02/09/2024–29/08/2025, FINAL_TEST 01/09/2025–31/08/2026).

## 4. Unidade experimental

- **Identidade de tentativa** (`attempt_id` = `record_id` do runner V2):
  `v76-<campanha>-<sessão>-r<k>`, determinística e única. Cada tentativa tem
  contexto, autorização, claim, journal, reserva e resultado próprios; não há
  retry pago automático. O `prepare` recusa raiz já usada, e o preflight recusa
  registro já reivindicado.
- **Identidade de contexto** (`context_sha256`): muda a cada tentativa (registro,
  horários, selos).
- **Identidade do input econômico** (`economic_fingerprint`): hash dos
  pareceres, históricos, contexto de cálculo, pesos, métricas verificáveis,
  políticas, contratos e carteira, sem identificadores nem horários. Deve ser
  igual entre replicações do mesmo cenário. A qualificação offline demonstra
  isso (`READINESS_REPORT.json → qualification.replication_identity`). Nunca se
  afirma que duas inferências receberam bytes idênticos: o prompt inclui
  `record_id`, horários e hashes, que diferem.

## 5. Campanhas planejadas

Valores de [BUDGET_PLAN.json](BUDGET_PLAN.json). A reserva é o teto conservador
dos runners selados (US$ 0,159744 por chamada Global PM; US$ 0,663552 por
comitê Radar de até 6 chamadas). O "piso de referência" usa a média dos pisos
observados na V7.5 e serve só para ordem de grandeza.

| Campanha | Tipo | Cenário | Tentativas | Chamadas | Reserva (US$) | Piso de ref. (US$) | Estado | Bloqueios |
|---|---|---|---|---|---|---|---|---|
| `c1-pilot` | repetibilidade nos inputs de desenvolvimento | S0 | 10 | 10 GPM | 1,59744 | 0,249 | planejada, não autorizada | — |
| `c1-intermediate` | idem (alternativa) | S0 | 29 | 29 GPM | 4,632576 | 0,722 | planejada, não autorizada | — |
| `c1-extended` | idem (alternativa) | S0 | 100 | 100 GPM | 15,9744 | 2,490 | **bloqueada** | excede o teto selado da V2 |
| `c2-s1`, `c2-s4`, `c2-s5` | sensibilidade ao estado | S1, S4, S5 | 5 cada | 5 GPM cada | 0,79872 cada | 0,125 cada | **bloqueada** | não existe caminho de preparo com posições |
| `c3-oos` | retrospectiva fora da amostra | S0 | 10 sessões | 50 comitês + 10 GPM (≤ 310 chamadas) | 34,77504 | 0,680 | **bloqueada** | protocolo não congelado; sessões não conferidas no COTAHIST; teto agregado Radar |
| `c4-prospective` | prospectiva | S0 + carteira paper | 20 decisões | 100 comitês + 20 GPM (≤ 620) | 69,55008 | 1,361 | **bloqueada** | protocolo não congelado; ledger paper inexistente; teto agregado Radar |

Limites atuais lidos dos registros (somente leitura):

- **Global PM.** O teto local de US$ 5,00 faz parte do `CONFIG` selado da V2 e é
  compartilhado com o V1. Já há US$ 0,319488 reservados, restando US$ 4,680512:
  **no máximo 29 novas chamadas V2**. Ultrapassar exige um tratamento novo ou
  uma decisão metodológica explícita, nunca a edição do teto selado.
- **Radar.** O teto agregado local é de US$ 5,0, e as reservas registradas já
  somam US$ 6,63552 (lote original incerto + recuperação). Qualquer novo lote
  exige autorização humana de orçamento (`radar_runs.py authorize-budget`).

As alternativas `c1-*` não são cumulativas: o pré-registro escolhe uma.

## 6. Matriz de cenários (categoria A, qualificação sintética)

S0–S9 em [SCENARIO_MATRIX.json](SCENARIO_MATRIX.json): 34 casos com estados de
carteira explícitos, sobre os **pareceres oficiais congelados** (somente
leitura), com respostas **roteirizadas** (`SCRIPTED_FAKE_NOT_GEMINI`) e o
**validador V2 selado**. Contextos congelados só em memória, num instante fixo:
os hashes são reproduzíveis e nada é gravado em `data/`. Resultado: **34/34**
desfechos esperados; árvores seladas inalteradas.

| Cenário | Casos | Regras exercitadas |
|---|---|---|
| S0 caixa | 2 | caixa 100% com watchlist válido; VENDA sem custódia rejeitada |
| S1 posições | 6 | manter, reduzir, zerar, aumentar; `NOT_SELECTED` com posição rejeitado |
| S2 caixa limitado | 3 | compra dentro do caixa; além do caixa (`insufficient_settled_cash`); compra sem parecer COMPRA (`buy_incompatible_with_opinion`) |
| S3 D+2 | 2 | venda gera recebível e não aumenta caixa disponível; recebível usado como caixa rejeitado |
| S4 compra condicionada | 4 | dependência correta (`WAIT_SETTLEMENT`); sem dependência; lista omitida; dependência inexistente |
| S5 veto | 5 | compra, peso, aumento e **redução** de ativo vetado rejeitados; manter posição vetada válido |
| S6 concentração | 2 | 39,6% válido; 41,3% rejeitado (`concentration_or_exposure_limit`) |
| S7 risco global | 2 | exposure > 85% rejeitada; 11 operações rejeitadas no schema (máx. 10) |
| S8 dados inconsistentes | 6 | hash de parecer, hash de contexto, ativo ausente, contexto expirado, parecer adulterado, resposta V1 |
| S9 não operar | 2 | manter posições apesar de VENDA; caixa sem operação |

Fatos de contrato revelados pela qualificação, que entram no protocolo:

1. Compra só é admitida em ativo com recomendação COMPRA (motor V5); MANTER e
   VENDA impedem compra. Isso corrige as tabelas da V7.5
   ([V75_INDEPENDENT_AUDIT.md](V75_INDEPENDENT_AUDIT.md), A1).
2. O veto impede **qualquer** operação, inclusive reduzir a posição vetada.
3. Giro acima de 100% não é atingível numa única proposta sem operações
   anteriores na sessão (compras dependentes liquidam em D+2). O limite de
   giro só é exercitável com histórico intradiário, que não existe nestas
   campanhas.
4. Dois códigos emitidos não têm descrição em `ERRORS` (auditoria, A4).

A categoria A **não** permite inferir desempenho de investimento.

## 7. Métricas e taxonomia de falhas

O [METRIC_CATALOG.json](METRIC_CATALOG.json) define 32 métricas, cada uma com
nome, dimensão, objetivo, fórmula, unidade, numerador, denominador,
aplicabilidade, fonte, limitações, tratamento de ausentes e `min_n`. O
validador do protocolo recusa métrica incompleta ou referência a métrica
inexistente.

Taxonomia (fixada antes de qualquer campanha):

| Classe | Códigos / estados |
|---|---|
| `MODEL_SCHEMA` | `response_schema_invalid`, `treatment_identity_mismatch` |
| `CONTRACT_INVARIANT` | `proposal_identity_or_session`, `proposal_hash_mismatch`, `complete_universe_and_current_weights_required`, `opinion_reference_mismatch`, `weights_must_sum_to_one`, `invalid_explanation_selection`, `invalid_watchlist`, `watchlist_signal_mismatch`, `watchlist_conflicts_with_operation`, `unsupported_explanation_reference`, `unsupported_metric_reference`, `cited_metric_mismatch`, `operation_outside_universe`, `whole_positive_units_required`, `invalid_funding_source`, `target_quantity_inconsistent`, `explanation_action_inconsistent`, `not_selected_inconsistent`, `settlement_deferred_inconsistent` |
| `RISK_OR_FINANCIAL` | `vetoed_asset_allocation`, `negative_or_excessive_target_weight`, `exposure_target_limit`, `concentration_or_exposure_limit`, `buy_incompatible_with_opinion`, `insufficient_settled_cash`, `insufficient_available_units`, `cost_ceiling`, `dependency_cycle_unknown_or_not_sale`, `turnover_or_cost_limit`, `global_risk_blocked` |
| `PROCEDURE_OR_INTEGRITY` | `proposal_expired_or_future`, `record_hash_mismatch`, contexto/preflight recusado |
| `PROVIDER` | `failure.json` com `PROVIDER_FAILED` |
| `INFRASTRUCTURE` | `RECOVERY_REQUIRED`, falha local antes de envelope |
| `UNCLASSIFIED` | qualquer caso sem diagnóstico; nunca atribuído ao modelo por padrão |

## 8. Procedimento de análise

1. **Integridade primeiro:** `run_global_pm_v2.py status` em cada registro;
   `check_preservation.py --since`; um registro sem integridade sai da análise e
   é relatado.
2. **Descritivo por campanha, por tratamento e por cenário,** sem agrupar
   tratamentos ou cenários.
3. **Taxas** (A, B, C) com numerador, denominador e intervalo de Wilson 95%; abaixo
   de `min_n`, apenas a contagem.
4. **Decisões validadas** entram nas métricas de variabilidade (C) e financeiras
   (E). Respostas rejeitadas só entram em `rejection_code_frequency` e, à
   parte, em `raw_intent_agreement` (rótulo `RAW_LLM_INTENT`).
5. **Pesos zero:** carteira 100% caixa é o vetor (0, …, 0, caixa = 1), um ponto
   válido; distâncias e concordâncias o tratam como qualquer decisão.
6. **Financeiro (E):** só com ledger paper e controles do mesmo desenho;
   nenhuma estatística inferencial sem teste pré-registrado; Sharpe indefinido
   com volatilidade zero.
7. **Desvios do protocolo:** registrados num anexo de desvios; nunca
   reclassificam resultados selados.

## 9. Conclusões permitidas e proibidas

| Permitido (com a evidência correspondente) | Proibido |
|---|---|
| "Em n tentativas do tratamento V2 sobre o contexto X, k foram válidas (IC 95% [a, b])." | taxa sem denominador, ou com n abaixo de `min_n` apresentada como estimativa |
| "As decisões validadas variaram L1 = d entre replicações." | variância calculada com respostas rejeitadas |
| "O validador rejeitou todas as propostas que violavam o veto." | "o sistema reduz risco" |
| "Na campanha paper prospectiva, o retorno foi r contra r_c do controle c." | "o Global PM é superior" sem teste pré-registrado e amostra adequada |
| "Retrospectivo fora da amostra de desenvolvimento" | chamar de "prospectivo" qualquer sessão cujos preços já eram conhecidos ao congelar o protocolo |

## 10. Ciclo de vida

`DRAFT` → `QUALIFIED_OFFLINE` (V7.6) → `FROZEN_FOR_FUTURE_EVALUATION` (exige
revisão humana registrada e data de congelamento) →
`AUTHORIZED_FOR_PAID_EXECUTION` (exige autorização humana com hash do
protocolo, signatário e limite) → `EXECUTED` (exige registros de execução
existentes). O validador recusa qualquer estado sem o requisito
correspondente. Depois do congelamento, uma mudança de hipótese, amostra,
métrica, cenário ou tratamento exige **versão nova**; uma versão congelada não
é sobrescrita (`frozen_protocol_modified`).

## 11. Segurança

- Nenhuma chamada paga na V7.6; `paid_gate` recusa sempre, e não existe
  orquestrador pago neste protocolo.
- Cada campanha paga futura exige: aprovação humana explícita, limite, preflight
  do runner, contexto válido, IDs únicos, registro de autorização e ausência de
  retry automático (já garantidos pelos runners selados).
- Reservas nunca são liberadas por estimativa; cobrança desconhecida não é zero.

## 12. Limitações conhecidas

- O provedor não garante determinismo nem fixação da versão do modelo; o nome
  `gemini-3.8-flash` pode mudar de comportamento. Mitigação: registrar
  `modelVersion` e `responseId` (já gravados) e tratar mudança de versão
  observada como quebra do grupo de replicação.
- O runner V2 não aceita semente; a variabilidade é inerente (temperatura 1,0).
- C1 e C2 usam inputs da sessão de desenvolvimento: medem repetibilidade e
  sensibilidade, não generalização.
- O teto selado limita C1 a 29 tentativas: precisão modesta
  ([REPETABILITY_DESIGN.md](REPETABILITY_DESIGN.md)).
- O calendário B3 do projeto só está auditado contra o COTAHIST até
  31/08/2026; as sessões de C3 precisam ser conferidas no COTAHIST antes do uso.
