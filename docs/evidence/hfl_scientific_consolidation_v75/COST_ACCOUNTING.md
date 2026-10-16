# Contabilidade de tokens e custo computacional

Escopo: custo de **inferência** (chamadas ao Gemini). Não há custo de transação
financeira: nenhuma ordem foi proposta como executável nem executada, e as
validações financeiras projetaram custo de corretagem `0` para as duas
propostas sem operações.

Valores recalculados por `scripts/verify_consolidation_v75.py` a partir de
`usageMetadata` gravado nos journals do provedor ([METRICS.json](METRICS.json)).
Tabela de preços usada pelo laboratório: US$ 0,75 por milhão de tokens de
entrada e US$ 3,75 por milhão de tokens de saída (inclusive pensamento),
conferida em 11/10/2026 em `https://ai.google.dev/gemini-api/docs/pricing`
(registrada em `cost.rates_usd_million` do resultado V2 e nas autorizações).

## 1. Conceitos

| Termo | Significado | O que **não** é |
|---|---|---|
| Tokens informados | Contagens devolvidas pelo provedor em `usageMetadata` | contagem independente |
| Pensamento não informado | `thoughtsTokenCount` **ausente** da resposta | zero comprovado |
| Piso monetário observado | (entrada × preço de entrada + saída informada × preço de saída) / 10⁶ | custo estimado completo, valor pago |
| Estimativa de planejamento | Hipótese do preflight (4 bytes/token, 2.500 tokens de saída) | uso observado |
| Reserva conservadora | Teto local bloqueado antes da chamada, nunca liberado | custo, fatura |
| Cobrança confirmada | Valor da fatura do provedor | — não há fatura consultada: **desconhecida** |

## 2. Global PM V1 × V2

| Item | Global PM V1 | Global PM V2 |
|---|---|---|
| Chamadas ao provedor | 1 (1 tentativa, sem retry) | 1 (1 tentativa, sem retry) |
| Tokens de entrada | 18.794 | 20.623 |
| Tokens de saída | 2.519 | 2.880 |
| Tokens de pensamento | não informados | não informados |
| Tokens totais | 21.313 | 23.503 |
| Entrada + saída = total? | sim (`CONSISTENT_WITHOUT_THOUGHTS_FIELD`) | sim |
| Custo estimado | `UNKNOWN` (calculado pela regra V2, em leitura) | `UNKNOWN` (selado) |
| `cost_usd` gravado | `null` | `null` |
| Piso monetário observado (USD) | 0,02354175 | 0,02626725 |
| Estimativa de planejamento (USD) | 0,0187303125 | 0,0197034375 |
| Bytes de entrada estimados | 49.895 | 55.085 |
| Reserva conservadora (USD) | 0,159744 | 0,159744 |
| Cobrança confirmada | não confirmada (`NOT_CONFIRMED_NO_PROVIDER_INVOICE`) | não confirmada |

Leituras permitidas:

- O total informado é igual à soma de entrada e saída nas duas chamadas. Isso
  **não** prova que o pensamento foi zero: o campo simplesmente não veio. O
  normalizador grava `thoughts_tokens: null`, e o custo estimado fica
  `UNKNOWN`.
- O piso observado ficou acima da estimativa de planejamento nas duas
  chamadas. A razão bytes/token observada na entrada foi de cerca de 2,65
  (49.895 / 18.794) e 2,67 (55.085 / 20.623), menor que os 4 bytes/token
  assumidos no planejamento. A reserva parte de um teto de entrada mais
  conservador e não foi ultrapassada pelo piso; sem os tokens de pensamento,
  não é possível afirmar quanto foi efetivamente cobrado.
- A diferença V2 − V1 (+1.829 de entrada, +361 de saída, +2.190 no total) não
  mede a eficiência dos tratamentos. São duas chamadas únicas, com prompts,
  schemas e contextos diferentes e amostragem estocástica (temperatura 1,0).

## 3. Radar `radar-2026-10-09-recovery-01`

Conciliação feita chamada a chamada nos cinco `provider_journal.jsonl`:

| Item | Valor |
|---|---|
| Chamadas | 29 (25 analistas técnicos + 4 Risk LLM; BBAS3 vetado por regra determinística, sem chamada de Risk) |
| Tentativas por chamada | 1; nenhum erro; nenhum retry |
| Tokens de entrada | 29.179 |
| Tokens de saída | 5.294 |
| Tokens de pensamento informados | 374, em 1 das 29 chamadas (VALE3); nas outras 28 o campo está ausente |
| Tokens totais | 34.847 (= entrada + saída + pensamento informado) |
| Piso monetário observado (USD) | 0,04313925 |
| Soma de `cost_usd` dos cinco `result.json` (USD) | 0,04313925 |
| Estimativa de planejamento do lote (USD) | 0,14625 |
| Reserva conservadora do lote (USD) | 3,31776 |
| Cobrança confirmada | desconhecida |

**Classificação: parcialmente observada.** A conciliação de tokens fecha
exatamente. O valor monetário, porém, é só um piso: 28 chamadas não informaram
pensamento.

**Nota de auditoria (sem alteração da fonte).** Os `result.json` selados do
Radar agregam `thoughts_tokens: 0` em PETR4, ITUB4, WEGE3 e BBAS3, e o campo
`cost_basis` diz "provider tokens incl thinking; estimated billing". Nos
journals, as chamadas desses comitês têm `thoughts_tokens: null`. O agregado,
portanto, trata ausência como zero, e o `cost_usd` gravado coincide com o piso
observado. Esse valor deve ser lido como piso pelos tokens informados, não como
estimativa de cobrança. A rotina de agregação pertence ao código selado do
Radar V4, que não foi editado.

## 4. Lote Radar original (incidente)

`radar-2026-10-09-original`, 12/10 02:59 BRT: 25 chamadas reservadas, 25 falhas
locais de transporte (guard offline), nenhum envelope do provedor, nenhum
parecer. Reserva de US$ 3,31776 mantida como **incerta** e nunca liberada; o
uso no provedor "a confirmar no console" (registry). Não entra em nenhuma
contagem de comitês nem de tokens. Fonte:
[../hfl_incident_2026_10_12/forensics.json](../hfl_incident_2026_10_12/forensics.json).

## 5. Agregados

| Agregado | USD | Natureza |
|---|---|---|
| Soma dos pisos observados (Radar recovery + V1 + V2) | 0,09294825 | piso; não é fatura |
| Reservas das inferências reais (recovery 3,31776 + original 3,31776 + V1 0,159744 + V2 0,159744) | 6,955008 | reservas locais; não são custo |

A conta de cobrança real exige o console de faturamento do provedor, que não
faz parte das evidências locais (ver [RESEARCH_GAPS.md](RESEARCH_GAPS.md)).
