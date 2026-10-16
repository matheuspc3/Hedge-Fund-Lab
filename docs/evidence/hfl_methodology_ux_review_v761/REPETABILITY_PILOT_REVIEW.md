# Revisão do piloto de repetibilidade (C1)

Revisão do desenho V7.6 ([REPETABILITY_DESIGN.md](../hfl_experimental_protocol_v76/REPETABILITY_DESIGN.md)).
Nada foi executado: nenhum orçamento consumido, nenhum claim criado.

## 1. Confirmação das premissas

| Premissa | Valor | Fonte |
|---|---|---|
| Reserva por inferência V2 | US$ 0,159744 | `estimate()` do runner V2: 65.536 × 1,50 + 8.192 × 7,50 por milhão |
| Reservado V1 + V2 | US$ 0,319488 | reservas `paid: true` em `data/global_pm/*/reservations` (lidas pelo plano V7.6) |
| Teto | US$ 5,00 | `CONFIG["root_budget_usd"]` selado no contrato V2 (`config_sha256 3a3b0ca0…`) |
| Capacidade restante | 29 inferências **no total** (todas as campanhas V2) | `BUDGET_PLAN.json → caps.global_pm_max_new_calls` |
| Condições adicionais | preflight do runner por tentativa (validade, origem `VERIFIED`, tamanho, orçamento) | `run_global_pm_v2.preflight` |

## 2. Precisão de um piloto de 10

Intervalos de 95% para a taxa de `VALID_PROPOSAL`, por número observado de
respostas válidas (Wilson e exato de Clopper-Pearson):

| Válidas em 10 | Wilson 95% | Clopper-Pearson 95% |
|---|---|---|
| 10 | [0,72; 1,00] | [0,69; 1,00] |
| 9 | [0,60; 0,98] | [0,56; 1,00] |
| 8 | [0,49; 0,94] | [0,44; 0,98] |
| 7 | [0,40; 0,89] | [0,35; 0,93] |
| 5 | [0,24; 0,76] | [0,19; 0,81] |

Com 10 tentativas, mesmo sem nenhuma rejeição, uma taxa de rejeição de até
~26–31% é compatível com os dados. O piloto mede **viabilidade operacional e
ordem de grandeza**, não uma taxa precisa. Para comparação, em 19: 19/19 →
Wilson [0,83; 1,00]; em 29: 29/29 → [0,88; 1,00].

Recomendação de relato: **Clopper-Pearson** como principal (conservador e
exato em amostras pequenas), Wilson como complementar. Abaixo de `min_n` = 10
nada é chamado de "taxa".

## 3. Métricas

- **Primária:** `global_validation_rate` (k/n com IC).
- **Secundárias:** `structural_validity_rate`, `rejection_code_frequency`,
  `no_operation_rate`, `target_weight_l1_dispersion`, `action_agreement`,
  `watchlist_stability`, `structured_justification_variation`,
  `provider_failure_rate`, `infrastructure_failure_rate`,
  `usd_observed_lower_bound` por tentativa.
- **À parte:** `raw_intent_agreement` (inclui respostas rejeitadas, rotulado
  `RAW_LLM_INTENT`).

## 4. Interrupção e ampliação de 10 para 29 (ou 19)

A ampliação é decidida **antes** do piloto e depende só de segurança
([PREREGISTRATION_DECISIONS.md](PREREGISTRATION_DECISIONS.md), D3):

| Verificação entre estágios | Continua se |
|---|---|
| Integridade de cada registro (`run_global_pm_v2.py status`) | nenhuma exceção |
| Estados | nenhum `RECOVERY_REQUIRED`; falhas classificadas |
| `modelVersion` dos envelopes | idêntico em todas as tentativas |
| Preflight | aprovado para a próxima tentativa |
| Orçamento | dentro do limite humano |
| Contrato | `contracts()` atual = selado |

**Proibido:** olhar a taxa de validação do piloto para decidir se amplia. Se
isso acontecer, o resultado combinado deixa de ser estimativa limpa e o desvio
precisa ser registrado.

## 5. Registro da variabilidade

Por tentativa (já gravado pelo runner, salvo a última linha):
`record_id`, `context_sha256`, `economic_fingerprint`, `system_prompt_sha256`,
`user_prompt_sha256`, `requested_model`, `resolved_model`, `modelVersion` e
`responseId` do envelope, `started_at`, `duration_ms`, tokens informados (com o
estado do campo de pensamento: ausente, zero explícito ou valor), status,
códigos de erro, vetor de decisão (pesos + caixa), ações, watchlist, métricas
citadas. Falta só registrar a **versão do Python e do SO** num índice da
campanha, porque o runner não grava esses dois dados.

## 6. Inputs equivalentes × bytes idênticos

- **Bytes idênticos:** não acontecem e não são afirmados. O prompt de usuário
  inclui `record_id`, `created_at`, `expires_at` e hashes, todos diferentes por
  tentativa.
- **Input economicamente equivalente:** demonstrado pela `economic_fingerprint`
  (pareceres, históricos, contexto de cálculo, pesos, métricas, políticas,
  contratos e carteira, sem identificadores nem horários). A V7.6 qualificou
  offline que dois contextos com registros e horários diferentes têm a mesma
  impressão.
- **Efeito possível dos bytes diferentes:** um LLM pode reagir a diferenças
  irrelevantes no texto (o `record_id`). Essa sensibilidade fica misturada à
  variabilidade amostral e não é separável sem um tratamento novo com identificadores
  neutros. Essa limitação deve ser declarada.

## 7. Sem semente controlável

- A variabilidade observada inclui amostragem (temperatura 1,0), possível
  não determinismo do provedor e mudanças silenciosas do modelo.
- Não é possível reproduzir uma resposta específica: a reprodutibilidade é da
  **validação** (replay offline do journal), não da **geração**.
- O desenho mede "o que o tratamento produz na prática", não um processo
  determinístico. Isso é adequado para conformidade operacional e inadequado
  para atribuir causa a mudanças finas de prompt.
