# Comparação Global PM V1 × V2

Comparação das duas únicas inferências reais do Gestor Global (Global PM),
feita sobre as respostas seladas. Os valores vêm de
[METRICS.json](METRICS.json) (ids entre parênteses), recalculados por
`scripts/verify_consolidation_v75.py` a partir dos registros locais.

> **V1 e V2 não são duas execuções do mesmo tratamento.** Identidade, prompt,
> schema, contrato e política de validação são diferentes. As duas chamadas são
> observações únicas (n = 1 por tratamento), com temperatura 1,0. A tabela
> descreve o que foi observado; não estima efeito de tratamento.

## 1. Tabela principal

| Dimensão | Global PM V1 | Global PM V2 |
|---|---|---|
| Identidade do tratamento (`gpm_*.identity`) | `HFL-MULTIASSET-GLOBAL-PM-V1` | `HFL-MULTIASSET-GLOBAL-PM-V2` |
| Registro | `v7-5a78ea5d15214e37bcae18f167ffcee3` | `v74-76d07c0d32444cecaf07e875deacb519` |
| Contexto congelado (SHA-256) | `0f5f7554…047e67d6` | `c4879f28…50f210` |
| Contratos (SHA-256) | `faf633a1…4eda70` | `159fd196…6590e2` |
| Prompt | `GLOBAL_PM_PT_V1` | `GLOBAL_PM_PT_V2` |
| Política de validação | implícita no código (`multiasset_global_pm.validate`) | `GLOBAL_PM_VALIDATION_V2`, selada no contexto |
| Modelo LLM (pedido = resolvido) | `gemini-3.8-flash` | `gemini-3.8-flash` |
| Opções da chamada | temperatura 1,0; `thinking_level` low; até 8.192 tokens de saída | idem |
| Modo | `CONSULTATIVE_SANDBOX` | `CONSULTATIVE_SANDBOX` |
| Sessão de mercado | 09/10/2026 (marca de 19:00 BRT) | 09/10/2026 (marca de 19:00 BRT) |
| Origem dos pareceres | `radar-2026-10-09-recovery-01`, registrada em arquivo lateral da plataforma (`data/platform/v7/radar_origins/…`); o contexto V1 não sela a origem | `radar-2026-10-09-recovery-01`, selada no contexto (`radar_origin`, registry revisão 3) |
| Mesmos cinco pareceres? (`gpm.same_opinions_v1_v2`) | sim — hashes idênticos | sim |
| Pareceres apontam para os `result.json` do Radar (`gpm_*.integrity`) | sim (5/5) | sim (5/5) |
| Patrimônio hipotético | R$ 100.000,00 | R$ 100.000,00 |
| Caixa-alvo proposto | `1.0` (100%) | `1.00` (100%) |
| Pesos-alvo dos cinco ativos | todos `0` | todos `0.00` |
| Soma pesos + caixa | 1 | 1 |
| Operações propostas | 0 | 0 |
| Validação financeira V5 isolada | válida; Risk projetado `OK`; exposição 0 | válida; Risk projetado `OK`; exposição 0 |
| Validação global | **reprovada** | **aprovada** |
| Erros detectados | `explanation_selection_inconsistent` (estágio `GLOBAL_PM_VALIDATOR`) | nenhum |
| `not_selected` declarado | BBAS3, VALE3, WEGE3 | BBAS3, ITUB4, PETR4, VALE3, WEGE3 |
| Campo de adiamento | `deferred_opportunities = [ITUB4, PETR4]` (tickers) | `settlement_deferred_operations = []` (IDs de operação) |
| Uso da watchlist | não aplicável (campo inexistente no V1) | ITUB4 e PETR4, sinal `COMPRA` = recomendação do parecer |
| Métricas citadas verificadas | não aplicável (campo inexistente no V1) | 13 citadas, 13 conferem com `verifiable_metrics` |
| Veto BBAS3 respeitado | sim (peso 0, sem operação) | sim |
| Tokens de entrada | 18.794 | 20.623 |
| Tokens de saída | 2.519 | 2.880 |
| Tokens de pensamento | não informados (campo ausente) | não informados (campo ausente) |
| Tokens totais | 21.313 | 23.503 |
| Piso monetário observado (USD) | 0,02354175 | 0,02626725 |
| Reserva conservadora (USD) | 0,159744 | 0,159744 |
| Cobrança confirmada | não confirmada | não confirmada |
| Duração da chamada | 16,9 s | 19,5 s |
| Tentativas HTTP | 1 | 1 |
| Alteração de carteira | nenhuma (`portfolio_changed: false`) | nenhuma |
| Execução habilitada | não (`execution_enabled: false`) | não |
| Resultado final selado | `REJECTED_BY_VALIDATOR` | `VALID_PROPOSAL` |

Notas:

- O caixa-alvo aparece como `1.0` no V1 e `1.00` no V2 porque o modelo escreve
  o valor como texto decimal; o validador compara valores, não grafias.
- Duração e tokens são observações únicas; a diferença V2 − V1 (+1.829 de
  entrada, +361 de saída, +2.190 no total; `gpm.token_delta_v2_minus_v1`) não
  pode ser atribuída ao prompt ou ao schema. Ver
  [COST_ACCOUNTING.md](COST_ACCOUNTING.md).
- A validade temporal (24 h, até 13/10 15:18 BRT no V1 e 13/10 17:29 BRT no V2)
  é separada do status selado: após a expiração o V1 continua
  `REJECTED_BY_VALIDATOR` e o V2 continua `VALID_PROPOSAL`.

## 2. Quatro dimensões que não devem ser confundidas

| Dimensão | Pergunta | V1 | V2 |
|---|---|---|---|
| **Intenção econômica do modelo** | O que o LLM quis propor? | manter 100% em caixa | manter 100% em caixa |
| **Conformidade contratual** | A resposta satisfaz as invariantes do tratamento? | não: as listas declaradas divergem das derivadas | sim, para todas as invariantes I1–I20 |
| **Validação financeira** | A proposta simulada satisfaz regras contábeis e de risco? | sim (V5 isolada) | sim (V5 dentro da validação V2) |
| **Resultado financeiro observado** | A decisão gerou ganho, perda ou redução de risco? | **não disponível** | **não disponível** |

A intenção econômica foi a mesma nos dois casos. O que mudou foi a
conformidade da resposta estruturada ao contrato de cada tratamento. Nenhuma
operação foi proposta, simulada como executada ou executada, e não houve
avaliação prospectiva: não existe resultado financeiro a comparar. Passar no
validador não torna uma proposta financeiramente superior.

## 3. Decisão por ativo

| Ativo | Recomendação do Radar | Risk | V1: ação · lista declarada | V2: ação · lista declarada | Restrição determinística aplicável |
|---|---|---|---|---|---|
| PETR4 | COMPRA | APROVADO | `NOT_SELECTED` · `deferred_opportunities` | `NOT_SELECTED` · `not_selected` + watchlist | nenhuma; compra permitida, não obrigatória |
| VALE3 | VENDA | APROVADO | `NOT_SELECTED` · `not_selected` | `NOT_SELECTED` · `not_selected` | sem custódia: venda impossível (I16 `insufficient_available_units`) |
| ITUB4 | COMPRA | APROVADO | `NOT_SELECTED` · `deferred_opportunities` | `NOT_SELECTED` · `not_selected` + watchlist | nenhuma; compra permitida, não obrigatória |
| WEGE3 | MANTER | APROVADO | `NOT_SELECTED` · `not_selected` | `NOT_SELECTED` · `not_selected` | nenhuma |
| BBAS3 | MANTER (COMPRA 5/5 vetada) | VETADO | `NOT_SELECTED` · `not_selected` | `NOT_SELECTED` · `not_selected` | veto: nenhuma operação e nenhum aumento de peso (V1: só em operações; V2: também em pesos, I13) |

A divergência do V1 está inteira em PETR4 e ITUB4: a ação declarada
(`NOT_SELECTED`) era coerente com peso zero e sem operação, mas os tickers
foram retirados de `not_selected` e postos num campo que o contrato V1 reserva
a compras dependentes de liquidação.

## 4. Diferenças de contrato relevantes para a comparação

| Aspecto | V1 | V2 |
|---|---|---|
| Listas de explicação | `not_selected`, `deferred_opportunities` (tickers, sem definição no prompt nem no schema) | `not_selected` (derivável da ação), `settlement_deferred_operations` (IDs), `watchlist_candidates` (consultiva, sem quantidade, preço, peso ou dependência) |
| Códigos de erro de lista | um código para as duas listas | `not_selected_inconsistent`, `settlement_deferred_inconsistent`, `invalid_watchlist`, `watchlist_signal_mismatch`, `watchlist_conflicts_with_operation` |
| Números no texto | não verificados | `cited_metrics` contra `verifiable_metrics` congeladas; texto livre continua não verificado |
| Veto | só em operações | em operações e em pesos-alvo |
| Status após a validade | a visão V1 trocava o status por `PROPOSAL_EXPIRED` (corrigido na apresentação V7.4) | status selado preservado; `expired` separado |
| Custo | `cost_usd` (`null` quando incompleto) | `cost` com tokens, pensamento, consistência, piso, reserva e cobrança |
| Inalterados | política de alocação, Risk V5, execução desabilitada, modelo, preços hipotéticos, teto de entrada | idem (importados do V1) |

Fonte das diferenças de contrato:
[../hfl_global_pm_v2/README.md](../hfl_global_pm_v2/README.md) (seções 4–6) e
[../hfl_global_pm_v2/contracts_v2.json](../hfl_global_pm_v2/contracts_v2.json).
