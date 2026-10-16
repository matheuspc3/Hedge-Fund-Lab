# Pré-registro — rascunho para revisão humana

| Campo | Valor |
|---|---|
| Protocolo | `HFL-V76-ROBUSTNESS-PROTOCOL` |
| Versão | 1.0.0 |
| Hash | `protocol_sha256` em [EXPERIMENT_MANIFEST.json](EXPERIMENT_MANIFEST.json) (SHA-256 sobre os hashes dos documentos do protocolo) |
| Estado | `QUALIFIED_OFFLINE`. **Não é um pré-registro vigente.** Passa a valer só depois de revisão humana registrada, escolhas marcadas como **[DECIDIR]** resolvidas e estado `FROZEN_FOR_FUTURE_EVALUATION` numa versão nova |
| Data de congelamento | não congelado |
| Contratos referenciados | Global PM V2 `159fd196…6590e2`; Radar V1 `77d75777…5bef`; Global PM V1 `faf633a1…4eda70` (fechado) |

## 1. Perguntas de pesquisa

- **Q1 (C1, dimensões A/C).** Com tratamento, inputs e cenário fixos, com que
  frequência o Global PM V2 produz propostas válidas, e quanto variam as decisões
  validadas?
- **Q2 (C2, dimensões B/D).** Como as propostas e as rejeições mudam com o estado
  da carteira (posições, caixa limitado, compra condicionada, veto)?
- **Q3 (C3, dimensão A/C).** A conformidade observada em Q1 se mantém em sessões
  fora da amostra de desenvolvimento?
- **Q4 (C4, dimensão E).** Como decisões congeladas antes dos preços se
  comportam numa carteira paper, contra controles com a mesma informação?

## 2. Hipóteses exploratórias

Registradas para evitar formulação depois dos dados. Nenhuma é confirmatória.

- **HE1.** Em C1, a decisão predominante será 100% em caixa sem operações (os
  pareceres de 09/10 são os mesmos das duas inferências anteriores).
- **HE2.** Rejeições, se houver, serão majoritariamente `CONTRACT_INVARIANT`, e
  não `RISK_OR_FINANCIAL`.
- **HE3.** Em C2, carteiras com posições reduzirão a frequência de "nenhuma
  operação" em relação a S0.
- **HE4.** Em C4, não há hipótese direcional sobre retorno; a análise é
  descritiva contra os controles.

## 3. Tratamentos

`HFL-MULTIASSET-GLOBAL-PM-V2`, sem alteração. Fonte de pareceres
`HFL-MULTIASSET-RADAR-V1`. V1 fechado. Qualquer mudança cria tratamento novo.

## 4. Controles

`ALWAYS_CASH`, `EQUAL_WEIGHT_ELIGIBLE`, `SIGNAL_RULE_DETERMINISTIC` (controle
primário de mesma informação), `BUY_AND_HOLD_EQUAL_WEIGHT`, `FIXED_WEIGHTS`
([BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md)). **[DECIDIR]** pesos de
`FIXED_WEIGHTS`.

## 5. Universo

PETR4, VALE3, ITUB4, WEGE3, BBAS3.

## 6. Seleção de sessões

- C1/C2: 09/10/2026 (inputs de desenvolvimento; não é avaliação fora da amostra).
- C3: 10 sessões de 01/09 a 08/10/2026 por permutação semeada (semente 7606),
  com ordem de substituição pré-registrada; nenhum preço consultado
  ([OUT_OF_SAMPLE_DESIGN.md](OUT_OF_SAMPLE_DESIGN.md)).
- C4: 20 sessões consecutivas após o congelamento.
- Janelas H2 proibidas.

## 7. Cenários de carteira

S0 em C1, C3 e C4 (início); S1, S4, S5 em C2
([SCENARIO_MATRIX.json](SCENARIO_MATRIX.json)). C2 só depois de existir um
caminho de preparo com posições, revisado.

## 8. Métricas

- **Primária de Q1:** `global_validation_rate` (Wilson 95%).
- **Secundárias de Q1:** `structural_validity_rate`, `rejection_code_frequency`,
  `no_operation_rate`, `target_weight_l1_dispersion`, `action_agreement`,
  `watchlist_stability`, `structured_justification_variation`;
  `raw_intent_agreement` à parte.
- **Q2:** as mesmas, por cenário, mais `veto_respected_rate` e
  `financial_validation_rate`.
- **Q4:** dimensão E; **[DECIDIR]** taxa livre de risco (CDI ou zero) e métrica
  primária (sugestão: diferença pareada por sessão contra
  `SIGNAL_RULE_DETERMINISTIC`).

Definições completas em [METRIC_CATALOG.json](METRIC_CATALOG.json).

## 9. Critérios de exclusão

Registro sem integridade (`status` do runner levanta exceção); sessão ausente
no COTAHIST; input Radar `BLOCKED`; comitês incompletos. Exclusões são
relatadas, nunca silenciosas. Falhas de provedor e de infraestrutura **não**
são excluídas: entram nas métricas de falha.

## 10. Número planejado de replicações

**[DECIDIR]** entre: C1 com n = 29 em dois estágios (10 + 19), o máximo sob o
teto selado da V2, que é a recomendação; ou apenas o piloto n = 10. C2: 5 por
cenário. C3: 1 por sessão. Justificativa de precisão em
[REPETABILITY_DESIGN.md](REPETABILITY_DESIGN.md).

## 11. Orçamento

Reservas: C1 até US$ 4,632576; C2 US$ 0,79872 por cenário; C3 US$ 34,77504; C4
US$ 69,55008 ([BUDGET_PLAN.json](BUDGET_PLAN.json)). Cada campanha precisa de
limite aprovado por humano. C3 e C4 exigem ainda autorização de orçamento
Radar (exposição agregada já acima do teto local). Reserva não é custo;
cobrança só pela fatura.

## 12. Regras de interrupção

Integridade falhou; `RECOVERY_REQUIRED`; mudança de `modelVersion` (fecha o
grupo de replicação); preflight recusado; contrato divergente do selado;
orçamento autorizado esgotado. Nunca por resultado observado.

## 13. Procedimento de análise

Seção 8 do [EXPERIMENTAL_PROTOCOL.md](EXPERIMENTAL_PROTOCOL.md): integridade →
descritivo por campanha, tratamento e cenário → taxas com IC → variabilidade só
de decisões validadas → intenção bruta à parte → dimensão E só com ledger paper
e controles. Desvios registrados em anexo.

## 14. Limitações conhecidas

Provedor sem determinismo nem versão fixa; sem semente; C1/C2 sobre inputs de
desenvolvimento; precisão limitada por 29 tentativas; C3 retrospectiva, não
prospectiva; calendário auditado só até 31/08/2026; políticas e carteira
didáticas; nenhuma execução real.

## Revisão humana (a preencher)

| Campo | Valor |
|---|---|
| Revisor(a) | |
| Data | |
| Decisões [DECIDIR] | |
| Aprovado para congelamento? | |
