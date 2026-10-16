# HFL Premium V7.4 — Global PM: endurecimento de contrato, validação semântica e preservação científica

Qualificação offline de 12/10/2026. **Nenhuma chamada ao Gemini, nenhum claim
pago, nenhuma reserva liberada, nenhuma evidência anterior alterada.** A primeira
inferência real do Global PM permanece exatamente como ocorreu:

**`GEMINI_GLOBAL_PM → REJECTED_BY_VALIDATOR`** (`explanation_selection_inconsistent`).

A correção é uma evolução separada, `HFL-MULTIASSET-GLOBAL-PM-V2`, que não
reinterpreta nem aprova aquela inferência.

| Arquivo | Conteúdo |
|---|---|
| [incident_reproduction.json](incident_reproduction.json) | Reprodução somente leitura da rejeição V1, contrafactual em memória, diagnóstico de tokens, hashes dos 6 arquivos do registro |
| [contracts_v2.json](contracts_v2.json) | Contratos V2 e V1 atuais, prompt, schema, configuração, política de validação, estimativa sobre os inputs oficiais |
| [qualification.json](qualification.json) | Índice selado da qualificação V2 (casos A, B, C, D, F; respostas sintéticas) |
| [platform_views.json](platform_views.json) | Visões da API da plataforma: registro V1 (agora e após a validade, relógio simulado) e registros V2 |
| [preservation_before.json](preservation_before.json), [preservation_since.json](preservation_since.json) | Snapshot antes da qualificação e comparação depois (`changes: []`, `violations: []`) |
| [mutation_checks.txt](mutation_checks.txt) | 13 mutações das guardas novas; todas derrubam testes |
| [regression_before_v74.txt](regression_before_v74.txt), [regression.txt](regression.txt), [ruff.txt](ruff.txt) | Regressão completa antes/depois e lint |

## 1. Causa exata da rejeição original

Registro `v7-5a78ea5d15214e37bcae18f167ffcee3`, contexto
`0f5f7554…e67d6`, origem Radar `radar-2026-10-09-recovery-01`, sessão 09/10,
`CONSULTATIVE_SANDBOX`, `gemini-3.8-flash`, R$ 100.000 hipotéticos.

O validador V1 (`scripts/multiasset_global_pm.py`, `validate`) deriva as duas
listas dos dados estruturados e compara com as declaradas:

| Lista | Definição V1 (código) | Derivada | Declarada pelo Gemini |
|---|---|---|---|
| `not_selected` | tickers com `asset_reasoning[t].action == "NOT_SELECTED"` | BBAS3, ITUB4, PETR4, VALE3, WEGE3 | BBAS3, VALE3, WEGE3 |
| `deferred_opportunities` | tickers das operações que a validação financeira V5 classificou como `deferred_operations` (compras que esperam liquidação de venda) | ∅ (não há operações) | ITUB4, PETR4 |

O Gemini leu `deferred_opportunities` como "oportunidades de investimento adiadas
por condições de mercado" (RSI elevado). O contrato V1 define o campo em função
de operações financeiramente dependentes de liquidação. As cinco ações eram
`NOT_SELECTED`, mas ITUB4 e PETR4 foram retiradas de `not_selected` e postas no
outro campo. As duas igualdades falham → `explanation_selection_inconsistent`.
A rejeição foi correta e permanece.

**Onde nasce a ambiguidade (V1):**

- *Prompt:* "Explique seleção, exclusão, **adiamento**, caixa e risco" — nenhuma
  definição dos campos; "adiamento" é lido naturalmente como adiamento de
  investimento.
- *Schema:* `not_selected: list[str]`, `deferred_opportunities: list[str]`, sem
  descrição. O nome "opportunities" sugere oportunidade de mercado.
- *Validador:* a definição só existe no código; um único código cobre as duas
  listas.

**Ambiguidades adicionais encontradas:**

1. **Justificativa × intenção × operação:** o V1 não tinha onde registrar uma
   observação de mercado sem operação; o único lugar "plausível" era o campo de
   liquidação.
2. **Validade mascara a rejeição na visão V1:** `run_global_pm.detail` troca o
   status para `PROPOSAL_EXPIRED` após `expires_at` (13/10 18:18 UTC). A partir daí
   a interface mostraria "Proposta expirada" e não `REJECTED_BY_VALIDATOR`.
   (Corrigido na apresentação; o runner V1 não muda — seção 6.)
3. **Veto só é checado em operações:** peso-alvo positivo em BBAS3 (vetado) sem
   operação era rejeitado só indiretamente (`target_quantity_inconsistent`).
4. **Números em texto livre não são verificados:** evidências citadas eram só
   códigos; valores numéricos não tinham forma estruturada (seção 9).
5. **Custo `null`:** correto, mas a interface mostrava apenas "Indisponível"
   (seção 10).

## 2. Reprodução offline da primeira inferência

`scripts/run_global_pm_v2.py incident` (somente leitura) confere os bytes dos
seis arquivos do registro antes e depois, relê o contexto pelo verificador V1
completo (`run_global_pm.detail`: selos, contratos, journal privado em SQLite
`mode=ro`, export, tokens, revalidação) e reexecuta o validador V1 no instante
`validation_at` gravado:

| Verificação | Resultado |
|---|---|
| SHA-256 dos 6 arquivos (contexto, resultado, claim, autorização, journal, SQLite) | idênticos aos fixados em `INCIDENT_SHA256` antes e depois |
| Contexto / resultado | `0f5f7554…e67d6` / `6fc83a20…62856` |
| Status no instante da validação | `REJECTED_BY_VALIDATOR` |
| Validação reexecutada == validação selada | `true` (byte a byte, inclusive `sha256` `f2a027a0…500f1`) |
| Código | `explanation_selection_inconsistent` (estágio `GLOBAL_PM_VALIDATOR`) |
| Validação financeira V5 isolada | `valid: true`, `risk_projected: OK`, 0 operações, custo `0`, caixa `100000.00`, exposição `0` |
| Efeitos | nenhum: árvore `data/global_pm/hfl_global_pm_v1` idêntica antes/depois; `--since` sem mudanças |

## 3. Contrafactual em memória

Cópia profunda da resposta, somente em memória, com
`not_selected = [BBAS3, ITUB4, PETR4, VALE3, WEGE3]` e
`deferred_opportunities = []`; demais campos inalterados; validador V1 completo:

**`VALID_PROPOSAL`, sem erros.** Não há inconsistência adicional que o V1
detecte: pesos somam 1, universo completo, hashes e evidências citadas
conferem, ações coerentes com pesos e operações, V5 válida.

Classificação gravada: `DIAGNOSTIC_IN_MEMORY_ONLY_NOT_A_CORRECTION_NOT_SEALED`.
Nada foi gravado sobre o registro; nenhum resultado com a identidade da
inferência foi criado. O contrafactual **não** valida o texto (ver seção 9 — o
V1 não verifica números em texto livre).

## 4. Matriz de invariantes semânticas (V2)

Todas derivadas dos dados estruturados; a primeira violação rejeita com um
código preciso; nenhum campo é reescrito (`normalization: NONE`).

| # | Invariante | Código |
|---|---|---|
| I1 | Identidade e `schema_version` da resposta = V2 (antes do schema) | `treatment_identity_mismatch` |
| I2 | Schema estrito, `extra=forbid`, tipos string para valores | `response_schema_invalid` |
| I3 | Registro, sessão, tempos, hashes de snapshot/contexto copiados | `proposal_identity_or_session`, `proposal_hash_mismatch` |
| I4 | `created_at ≤ validação < expires_at` | `proposal_expired_or_future` |
| I5 | Universo completo em pesos e justificativas; pesos atuais inalterados | `complete_universe_and_current_weights_required` |
| I6 | `opinion_refs` = hashes recebidos | `opinion_reference_mismatch` |
| I7 | Σ pesos + caixa = 1; caixa ≥ 0 | `weights_must_sum_to_one` |
| I8 | 0 ≤ peso ≤ 40%; exposição ≤ 85% | `negative_or_excessive_target_weight`, `exposure_target_limit` |
| I9 | Listas sem repetição e dentro do universo | `invalid_explanation_selection`, `invalid_watchlist` |
| I10 | `watchlist[t].radar_signal` = recomendação final do parecer | `watchlist_signal_mismatch` |
| I11 | Justificativa cita só o parecer e códigos de evidência recebidos | `unsupported_explanation_reference` |
| I12 | `cited_metrics` só com chaves de `verifiable_metrics[t]`; valor = fonte arredondada *half-even* na precisão citada (≤ 6 casas) | `unsupported_metric_reference`, `cited_metric_mismatch` |
| I13 | Ativo `VETADO`: nenhuma operação e peso-alvo ≤ atual | `vetoed_asset_allocation` |
| I14 | Operação no universo; quantidade inteira positiva; fonte de financiamento coerente com dependências | `operation_outside_universe`, `whole_positive_units_required`, `invalid_funding_source` |
| I15 | Nenhuma observação futura em ativo com operação | `watchlist_conflicts_with_operation` |
| I16 | V5: caixa liquidado, custódia, teto de custo, dependência = venda anterior desta proposta, giro/custo, Risk projetado | `insufficient_settled_cash`, `insufficient_available_units`, `cost_ceiling`, `dependency_cycle_unknown_or_not_sale`, `turnover_or_cost_limit`, `global_risk_blocked` |
| I17 | Quantidades coerentes com pesos-alvo (uma ação + custos) | `target_quantity_inconsistent` |
| I18 | `action` = única ação permitida por peso e operações (`expected_action`) | `explanation_action_inconsistent` |
| I19 | `not_selected` = {t : action = NOT_SELECTED} (⇔ peso 0 e sem operação) | `not_selected_inconsistent` |
| I20 | `settlement_deferred_operations` = IDs das operações que esperam liquidação | `settlement_deferred_inconsistent` |

Descrições legíveis de todos os códigos (V1 e V2) em `ERRORS`
(`scripts/multiasset_global_pm_v2.py`), servidas pela API à interface.

## 5. Contrato corrigido (V2)

- **`not_selected`** — ativos sem operação, peso-alvo zero e ação
  `NOT_SELECTED`. Derivável: I18 + I19.
- **`settlement_deferred_operations`** (substitui `deferred_opportunities`) —
  `operation_id` (não tickers) das compras formalmente condicionadas à
  liquidação de uma venda desta proposta (`funding_source = SETTLEMENT`,
  `dependencies` = IDs de vendas). Exemplo: venda de PETR4 gera recebível D+2;
  a compra de WEGE3 depende dele e só aparece na projeção condicional. Derivável
  pelo V5 (I16 + I20).
- **`watchlist_candidates`** — observações de mercado puramente consultivas:
  `{ticker, radar_signal, observation, reassessment_condition}`. O schema não
  admite quantidade, preço, peso, dependência ou autorização (`extra=forbid`);
  o ativo não pode ter operação; o sinal deve ser o do parecer. **Uma observação
  de mercado não é uma operação condicionada à liquidação.**
- **`cited_metrics`** por ativo — fatos numéricos verificáveis (seção 9).
- **Texto livre** (`reasoning`, `global_reasoning`, `risks`, `summary`) —
  interpretação do modelo, não verificada; rotulada assim na interface.

O prompt V2 define cada campo, a regra de custódia, o veto e os limites dos
dados (sem setores, índice, notícias, fundamentos, retornos futuros). Texto
integral e schema em [contracts_v2.json](contracts_v2.json).

## 6. Diferenças entre V1 e V2

| | V1 (selado, inferência real) | V2 |
|---|---|---|
| Identidade | `HFL-MULTIASSET-GLOBAL-PM-V1` | `HFL-MULTIASSET-GLOBAL-PM-V2` |
| `schema_version` | 1 | 2 |
| Prompt | `GLOBAL_PM_PT_V1` | `GLOBAL_PM_PT_V2` (semântica dos campos, custódia, veto, limites dos dados) |
| Listas | `not_selected`, `deferred_opportunities` (tickers) | `not_selected`, `settlement_deferred_operations` (IDs), `watchlist_candidates` |
| Métricas citadas | — | `cited_metrics` contra `verifiable_metrics` congeladas no contexto |
| Códigos de lista | um (`explanation_selection_inconsistent`) | `not_selected_inconsistent`, `settlement_deferred_inconsistent`, `invalid_watchlist`, `watchlist_*` |
| Veto | só em operações (V5) | também em pesos-alvo (I13) |
| Política de validação | implícita no código | `GLOBAL_PM_VALIDATION_V2`, selada no contexto e nos contratos |
| Status após a validade | substituído por `PROPOSAL_EXPIRED` | status selado mantido; `expired` separado |
| Custo | `cost_usd` ou `null` | `cost` com tokens informados, pensamento, consistência, estimativa ou `UNKNOWN`, piso observado, reserva, cobrança |
| Origem Radar | arquivo lateral da plataforma | selada no contexto; preflight pago exige `VERIFIED` |
| Diretório | `data/global_pm/hfl_global_pm_v1/` | `data/global_pm/hfl_global_pm_v2/` (reservas próprias) |
| Execução pela UI | prepare/preflight/run | somente leitura; prepare/preflight/run pelo CLI |
| Inalterados | política de alocação, Risk V5, execução desabilitada, modelo, preços, teto de entrada | idem (reutilizados por import) |

**Por que arquivos novos:** o hash de `multiasset_global_pm.py` e
`run_global_pm.py` está selado em todo contexto V1
(`contracts.sources_sha256`), e os baselines de preservação fixam esses
arquivos, `global_pm_api.py` e o motor V5. Qualquer edição invalidaria a
verificação do registro real. A V2 importa o V1 (somente leitura) e reutiliza
`freeze`/`calculation_context` sobre uma cópia rotulada do snapshot.

Orçamento: o preflight V2 soma as reservas V1 **e** V2 contra o mesmo teto local
de US$ 5,00 (conservador; nenhuma reserva é liberada).

## 7. Novo schema e prompt

Ver [contracts_v2.json](contracts_v2.json) (`prompt_v2`, `response_schema_v2`,
`validation_policy_v2`, `config_v2`). Sobre os inputs oficiais congelados (em
memória), a entrada estimada é **55.051 bytes** (teto 65.536) e a reserva
**US$ 0,159744** (igual à V1).

## 8. Identidade científica e hashes

| Item | V2 | V1 (atual = selado no registro real) |
|---|---|---|
| Contratos | `159fd196879c37362ab67270b4c7ddccb2ca529e06d74d1633c3936dd36590e2` | `faf633a1dad788f3ed72e8b88b8f4c04b9bbccac4fd75277693c50f19a4eda70` |
| Prompt | `4aaa6d5247979d1f157e07b897211345ed4cb2eefdd48545fa0748c2561b6f70` | `6ff81df33cd7cb7a6f36df5b85346c596e5bce127ffa78024ec2e7e38540203a` |
| Schema de resposta | `974be1e2e40965f363b5a4d6bf9cf78d1328bdafcdc0097d8fcb69b673e26ef4` | `14ea2eb6544d8d031b3ca7dcc4a42106e444af52ea4f481b847edab57646f842` |
| Política de validação | `2206a3ba4b4b391bce96598d042a5ce86c235c19e9c775c339b507c53e1a26c6` | — (V1 chama de `validation_policy_sha256` o hash da política de alocação, `1a542d6a…`, que a V2 registra como `allocation_policy_sha256`) |
| Configuração | `3a3b0ca0578f65f43bb6148e4d4a4f4dad73d8e7432d9df95c6ec85123296226` | `b3876cf2fc113eef81498ffd3bd6896ad4549e391c2f6f39233dd6fb22906f22` |
| Índice da qualificação | `669114353f55983b6ebe7214215b1982fb24340b8218ea89beaa467a7a253115` | — |

`v1_unchanged_vs_sealed_incident_context: true`: o `contracts()` V1 calculado
hoje é idêntico ao selado no contexto da inferência real.

## 9. Evidências não suportadas na primeira resposta

Auditoria manual de cada afirmação factual contra o contexto congelado:

| Afirmação do Gemini | Contexto | Situação |
|---|---|---|
| BBAS3 consenso COMPRA 5/5; vol. 21p 54,48% > 50% | contagem 5/0/0; `asset_volatility_21 = 0.544844`; Risk "acima de 50%" | suportada |
| ITUB4 RSI 76,56; vol. 42,92% | `rsi = 76.557381`; `0.429197` | suportada |
| PETR4 RSI 74,92; vol. 39,23%; "colada à banda superior" | `74.915165`; `0.392326`; `bb_upper_gap = -0.001608` | suportada (interpretação razoável) |
| WEGE3 4/5 MANTER, confiança 0,476, RSI 55,62, MACD abaixo do sinal | idem | suportada |
| VALE3 abaixo das médias, MACD negativo, sem posição | idem | suportada |
| ITUB4 "rompimento de banda superior de Bollinger" | `bb_upper_gap = -0.009664` e evidência `CLOSE_INSIDE_BOLLINGER` | **contradita pelos números** — copiada do texto do Risk individual do Radar (`individual_risk.analysis`), outro LLM |
| "correlação histórica de ITUB4 e PETR4 com o **setor financeiro** e mercado é relevante" | só correlações par a par de 60 retornos (ITUB4–PETR4 = 0,331); `sector_status = NOT_EVALUATED_NO_RELIABLE_METADATA`; nenhum índice | **não suportada**; PETR4 não é do setor financeiro |
| "Volatilidade **setorial** expressiva (BBAS3 54,48%, ITUB4 42,92%)" | volatilidades individuais, setor não avaliado | **rótulo não suportado** |
| "evitar risco de correção imediata", "adiando compras até que ocorram retrações" | nenhuma previsão no contexto | previsão/intenção apresentada como fundamento |

**Regra V2 (determinística, limitada a campos verificáveis):** cada contexto
congela `verifiable_metrics[t]` = indicadores do parecer, métricas de risco
individual, confiança técnica e `correlation_<OUTRO>` para os pares calculados.
Um número só conta como fato quando citado em `cited_metrics` com uma dessas
chaves e o valor confere. Não há chave de setor, índice ou previsão; citar uma
é rejeitado. Texto livre — inclusive textos recebidos de outros LLMs, como o
parecer do Risk individual — permanece interpretação e não é validado por
comparação textual. O prompt V2 proíbe setores, correlações setoriais, retornos
futuros e previsões apresentadas como observação; a confiança técnica segue
qualitativa, nunca probabilidade.

## 10. Tokens e custo

`usageMetadata` bruto da resposta (do journal privado):
`promptTokenCount 18794`, `candidatesTokenCount 2519`, `totalTokenCount 21313`,
**sem o campo `thoughtsTokenCount`** (ausente, não nulo). O normalizador
compartilhado grava `thoughts_tokens: null`. O V1 (`billing`) devolve `null` →
interface "Indisponível". Correto: `null` não é zero.

`usage_accounting` (V2, aplicado em leitura também ao registro V1, sem regravá-lo):

| Campo | Valor no registro real |
|---|---|
| Tokens informados pelo provedor | entrada 18.794 · saída 2.519 · total 21.313 |
| Pensamento | `NOT_REPORTED` |
| Consistência dos totais | `CONSISTENT_WITHOUT_THOUGHTS_FIELD` (18.794 + 2.519 = 21.313) |
| Custo estimado | **`UNKNOWN`** (`usd_estimated: null`) |
| Piso observado (entrada + saída informadas, preços 2026) | US$ 0,02354175 |
| Reserva conservadora | US$ 0,159744 (não liberada) |
| Cobrança confirmada | `null` — `NOT_CONFIRMED_NO_PROVIDER_INVOICE` |

Estimativa só existe quando entrada, saída e pensamento são informados como
inteiros não negativos **e** somam o total; `0` explícito conta como informado;
total divergente → `INCONSISTENT`/`UNKNOWN`; valores booleanos, negativos,
fracionários ou texto contam como ausentes. A soma coincidir com o total não é
tratada como prova de pensamento zero, nem a soma de tokens como preço faturado.
O `cost_usd: null` gravado no registro V1 não foi alterado.

## 11. Interface do Gestor Global

`/portfolio` (`global-pm.js`, `global-workflow.js`; API `platform_api.py`):

- **Status selado separado da validade:** a pílula mostra
  `validation_status` (do resultado selado) e acrescenta "validade expirada";
  após 13/10 18:18 UTC o registro real continua `REJECTED_BY_VALIDATOR`
  (verificado com relógio simulado em [platform_views.json](platform_views.json)).
- **Resposta rejeitada:** título "Resposta rejeitada pelo validador ·
  `REJECTED_BY_VALIDATOR`"; o resumo do modelo aparece como "Intenção
  registrada do LLM (auditoria, não é recomendação validada)"; sem gráfico de
  alocação-alvo (o painel diz "Intenção registrada do LLM rejeitada: caixa-alvo
  100%"); simulação desabilitada; tabela marcada "somente para auditoria".
- **Código e descrição:** `explanation_selection_inconsistent`: "As listas de
  ativos não selecionados ou de operações adiadas não correspondem às operações
  e justificativas da proposta."
- **Validações separadas:** "Validação global" × "Validação financeira V5
  isolada" ("Válida · Risk OK" — "Não aprova a proposta rejeitada").
- **Listas distintas:** não selecionadas; operações condicionadas à liquidação
  (V2); observações futuras consultivas (V2); no V1, o campo aparece com o nome
  original e sua definição; "Operações executáveis: indisponíveis".
- **Texto livre** rotulado como interpretação do modelo; métricas citadas
  mostradas como "conferidas com o contexto".
- **Custo:** desconhecido (`UNKNOWN`) com tokens informados, pensamento "não
  informado", piso observado, reserva e "cobrança não confirmada".
- **Registros V2** aparecem na lista com "· V2" e o status selado; preflight,
  execução e replay ficam desabilitados ("somente pelo CLI, com autorização
  humana separada"); o backend recusa IDs V2 nas rotas de escrita
  (`invalid_analysis_id`).

Verificação: o teste 20 executa o `global-pm.js` real em Node com DOM simulado
(resposta rejeitada × validada). Não foram feitas capturas de tela no
navegador nesta entrega.

## 12. Testes novos

`tests/test_global_pm_v2.py` — 31 testes, offline (`no_network`, transporte
Gemini substituído por falha), registros só em `data/global_pm/test-only-v2-*`
(apagado ao final). Os testes sobre inputs oficiais pulam numa cópia limpa sem
o registro local.

| Item pedido | Teste |
|---|---|
| 1 Reprodução exata | `test_01_incident_reproduced_read_only` |
| 2 Contrafactual | `test_02_counterfactual_only_in_memory` |
| 3 Carteira em caixa | `test_03_…`, `test_all_cash_decision_on_official_inputs` |
| 4 Lista completa de não selecionados | `test_04_…` |
| 5 Oportunidade futura sem operação | `test_05_watchlist_is_advisory_only`, `test_03_…` |
| 6 Operação dependente de liquidação | `test_06_…` |
| 7 Dependência inexistente | `test_07_…` (também uso antecipado do recebível) |
| 8 VENDA sem custódia | `test_08_sale_signal_without_custody` (VALE3 oficial) |
| 9 Ativo vetado | `test_09_vetoed_asset` (BBAS3 oficial; texto não remove veto; manter posição vetada é válido) |
| 10 Caixa insuficiente | `test_10_…` |
| 11 Soma ≠ 100% | `test_11_…` |
| 12 Quantidade não inteira | `test_12_…` |
| 13 Custo acima do permitido | `test_13_…` |
| 14 Referência incorreta | `test_14_…` (evidência inexistente, setor, índice, RSI errado, "rompimento" `bb_upper_gap`, correlação errada, precisão > 6) |
| 15 Hash de parecer divergente | `test_15_…` |
| 16 Confusão V1/V2 | `test_16_v1_and_v2_never_mix`, `test_16_v1_response_against_v2_contract` |
| 17 Contexto expirado | `test_17_…` |
| 18 Rejeição original preservada | `test_18_original_rejection_survives_expiry_in_the_view` |
| 19 Tokens incompletos | `test_19_…` |
| 20 UI rejeitada × validada | `test_20_…` (Node) |
| 21 Recuperação sem inferência | `test_21_…` (queda após o journal; replay sem nova chamada) |
| 22 Chamadas pagas bloqueadas | `test_22_…` (sem origem; sem `--authorize-paid`; sem chave; nada gravado) |
| 23 Reserva e journal | `test_23_…` (reservas V1 intactas, claim/journal imutáveis) |
| 24 Histórico H2 intacto | `test_24_no_preservation_violation` |
| 25 Sem efeitos financeiros | `test_25_…` |
| Adversariais | `test_adversarial_contradictions`, `test_05_…`, `test_09_…`, `test_14_…` |
| Qualificação A–F | `test_qualification_cases`; persistida em [qualification.json](qualification.json) |
| Plataforma | `test_platform_lists_v2_read_only` |

Mutações ([mutation_checks.txt](mutation_checks.txt)): remover cada guarda
nova (veto, as duas listas, observação × operação, sinal, métricas, identidade,
consistência de tokens, origem Radar no preflight, rótulos da UI, status selado
na API) derruba os testes correspondentes: **13/13**.

Qualificação persistida (`run_global_pm_v2.py qualify`, demo-v4 sintético,
`FAKE_GLOBAL_PM_NOT_GEMINI`, US$ 0):

| Caso | Situação | Resultado |
|---|---|---|
| A | 100% caixa, 5 não selecionados, ITUB4/PETR4 em observação | `VALID_PROPOSAL` |
| B | compra de PETR4 com caixa liquidado | `VALID_PROPOSAL` |
| C | venda de VALE3 sem custódia | `REJECTED_BY_VALIDATOR` · `insufficient_available_units` |
| D | venda de PETR4 + compra de WEGE3 dependente do recebível D+2 | `VALID_PROPOSAL` |
| F | forma do incidente: observações de mercado no campo de liquidação | `REJECTED_BY_VALIDATOR` · `settlement_deferred_inconsistent` |

O caso E (veto) exige um parecer vetado, que o demo-v4 não tem; está coberto
pelos testes sobre os inputs oficiais congelados (BBAS3).

## 13. Regressão

1703 aprovados, 15 falhas, nenhuma ligada à V7.4; as duas legadas de preservação
continuam vermelhas. Classificação completa na seção "Regressão final".

## 14. Preservação

- Registro real V1: 6 arquivos com SHA-256 fixados antes e depois de cada
  operação; árvore `data/global_pm/hfl_global_pm_v1/` (incluindo as 14 reservas)
  idêntica antes/depois da qualificação.
- `check_preservation.py --since preservation_before.json`: `changes: []`,
  `violations: []` (Radar, ledgers H2/forward, registry e execuções).
- Baselines históricos: `violations: []`; só as duas mudanças OPERATIONAL
  legadas (seção "Regressão final").
- Nenhum arquivo selado editado: `multiasset_global_pm.py`, `run_global_pm.py`,
  `global_pm_api.py`, motor V5, Radar, H2 v6 e `docs/HFL_PREMIUM_V6_GLOBAL_PM.md`
  inalterados.

## 15. Arquivos

Novos: `scripts/multiasset_global_pm_v2.py`, `scripts/run_global_pm_v2.py`,
`tests/test_global_pm_v2.py`, esta pasta. Alterados (não fixados por baseline):
`dashboard/platform_api.py`, `dashboard/global-pm.js`,
`dashboard/global-workflow.js`, `dashboard/portfolio.html` (versão dos scripts),
`docs/HFL_PLATFORM_ARCHITECTURE.md`, `docs/HFL_OPERATIONS_RUNBOOK.md`.
Dados locais (fora do Git): `data/global_pm/hfl_global_pm_v2/` (qualificação e
reservas de US$ 0).

## 16. Comandos de qualificação e do preflight futuro

```powershell
# CONSULTA — reprodução da rejeição V1 e contrafactual (somente leitura)
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py incident
# CONSULTA — testes offline
.venv/Scripts/python.exe -m pytest -q tests/test_global_pm_v2.py
# GRAVA (sintético, US$ 0) — qualificação A–F; um prefixo novo por rodada
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py qualify
```

Inferência oficial V2 futura (**não executada**; exige decisão humana nova):

```powershell
.venv/Scripts/python.exe -B scripts/check_preservation.py --snapshot data/platform/antes-gpm-v2.json
# GRAVA: contexto V2 (validade 24 h) a partir de uma execução Radar registrada
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py prepare --radar-run radar-2026-10-09-recovery-01 --confirm-hypothetical --ack-fixture-policy
# CONSULTA: preflight (origem VERIFIED, orçamento V1+V2, validade, tamanho); devolve o token
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py preflight --id v74-<id>
# PAGA: uma chamada, sem retry; $env:GEMINI_API_KEY somente neste terminal
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py run --id v74-<id> --confirm <token> --authorize-paid
# CONSULTA: resultado, ou replay offline do journal
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py status --id v74-<id>
.venv/Scripts/python.exe -B scripts/run_global_pm_v2.py replay --id v74-<id>
.venv/Scripts/python.exe -B scripts/check_preservation.py --since data/platform/antes-gpm-v2.json
```

Uma V2 qualificada não autoriza piloto, política de investimento nem execução
de ordens; o resultado continua consultivo (`execution_enabled: false`).

## Regressão final

Suíte completa (`poetry run pytest -q`, árvore limpa após os commits):
**1703 aprovados, 15 falhas** ([regression.txt](regression.txt)). Antes da V7.4
(mesma suíte sem os 31 testes novos, árvore suja pelos arquivos novos ainda não
versionados): 1672 aprovados, 15 falhas ([regression_before_v74.txt](regression_before_v74.txt)).
A suíte **não** está totalmente aprovada. Nenhuma falha envolve código da V7.4:

| Falhas | Causa | Relação com a V7.4 |
|---|---|---|
| `test_global_pm.py::test_31_original_ledgers_preserved`, `test_multiasset_portfolio.py::test_original_scientific_radar_and_ledger_preservation` | **As duas falhas legadas:** `data/radar/hfl_multiasset_v1/job.json` e `last_prepare.json` (OPERATIONAL) mudaram por ações do operador em 12/10, antes da V7.3; os testes comparam o hash exato de todos os arquivos dos baselines V6/V5. `violations: []`. Baselines não foram alterados. | nenhuma; idênticas antes e depois |
| `test_radar_runs.py::test_real_recovery_has_five_official_inputs_equivalent_to_original`, `::test_real_itub4_bonus_normalized_and_bbas3_restricted` | Afirmam o estado de `radar-2026-10-09-recovery-01` **antes** do lote oficial (0 claims, plano 30/29). O lote oficial foi executado em 12/10 (5 claims), então esses testes do V7.3 ficaram desatualizados em relação aos dados locais. | nenhuma; idênticas antes e depois |
| `tests/pipeline/test_flows.py` (7) | PostgreSQL em `127.0.0.1:5435` indisponível (`connection refused`). | ambiente |
| `test_cal_b4_safety`, `test_spec` (estratégias `*_h2_proposed` extras no registro), `test_v6_phase_routing` | Divergências antigas de código/teste H2 não tocado aqui. | nenhuma; idênticas antes e depois |
| `test_h2_v6_provisional::test_oa1_validation_seal_and_dashboard` × `tests/pipeline/test_snapshot.py::test_manifest_adulterado_e_rejeitado[code]` | Par complementar: o primeiro exige árvore limpa ("evaluation requires a clean repository"); o segundo muta `git_dirty=False` e só detecta a mutação com árvore suja. Um dos dois sempre falha. Antes: falhou o primeiro (árvore suja); agora, o segundo. Confirmado com um arquivo não versionado temporário: com ele, `test_snapshot` passa. | nenhuma |

Testes mais acoplados à entrega (V2, V1 Global PM, plataforma V7, UI):
87 aprovados, 1 falha (a legada `test_31`).

## Restrições respeitadas

Sem chamadas pagas, sem consulta ao Gemini, sem reexecutar a inferência
original, sem sobrescrever resultados, journals, claims ou reservas, sem
reclassificar a rejeição, sem alterar a H2 v6, o tratamento V1 ou os baselines,
sem operações reais, sem push.
