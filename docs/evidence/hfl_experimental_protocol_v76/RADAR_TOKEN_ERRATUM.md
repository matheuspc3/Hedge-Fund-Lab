# Errata não destrutiva — tokens de pensamento do Radar `radar-2026-10-09-recovery-01`

**Identificador:** `HFL-V76-RADAR-TOKEN-ERRATUM`.
**Natureza:** nota de auditoria. Nenhum `result.json`, journal, claim, reserva ou
registro de custo foi alterado. Os resultados científicos do Radar (votos,
sinais, Risk, recomendações) **não** são afetados: a errata trata apenas da
contabilidade de tokens e custo.
**Reprodução:** `.venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py erratum`
(somente leitura; decodifica os envelopes brutos e confere o SHA-256 de cada um).

## 1. Registros envolvidos

| Comitê | `result.json` (SHA-256, = `result.sha256` gravado) | `thoughts_tokens` gravado | `cost_usd` gravado | Classificação |
|---|---|---|---|---|
| PETR4 | `c63d7fdb025ba5e400a6432d32c3200cb2cd4afb02337c5b2e56cc1ff9fe5328` | 0 | 0,0080265 | zero gravado; pensamento ausente nas 6 chamadas |
| ITUB4 | `4f96331a5dae68d9a860577d6ce31ce7266e1846abf99c0a941c7bed651ee7d0` | 0 | 0,00757125 | zero gravado; ausente nas 6 chamadas |
| WEGE3 | `e085e3f8f0b58649656e2f3fa60b9d5da8d761d6369f9c091d2388524fbfd118` | 0 | 0,00872775 | zero gravado; ausente nas 6 chamadas |
| BBAS3 | `33c2b4f747bfefafd2266c1c2e4c482dd38b0371c60ca9016321cb618cb39df1` | 0 | 0,00840375 | zero gravado; ausente nas 5 chamadas |
| VALE3 | `cfdb44b972be1e4f91ab22f25564462ae69438c9781aa7467a716d1c640a64e8` | 374 | 0,01041 | **soma parcial**: 374 informados em 1 de 6 chamadas |

Os quatro registros apontados na V7.5 são PETR4, ITUB4, WEGE3 e BBAS3. A
auditoria encontrou um quinto caso relacionado: em VALE3, o valor 374 é real,
mas é a soma de uma única chamada informada (analista 2) com cinco chamadas em
que o campo está ausente.

## 2. Evidência bruta do provedor

Para cada uma das 29 chamadas, o `usageMetadata` foi lido do envelope bruto
(`raw_base64` no `provider_journal.jsonl`), depois de conferido contra o
`raw_sha256` gravado:

| Estado de `thoughtsTokenCount` no JSON bruto | Chamadas |
|---|---|
| **Campo ausente** (chave inexistente) | 28 |
| Campo presente com `null` | 0 |
| Campo presente com `0` explícito | 0 |
| Campo presente com valor positivo | 1 (VALE3, analista 2: 374) |

Nas 28 chamadas sem o campo, `promptTokenCount + candidatesTokenCount =
totalTokenCount`. Na chamada com o campo, o total inclui o pensamento
(1.119 + 118 + 374 = 1.611).

## 3. Cadeia de transformação

| Etapa | Onde | O que acontece com o campo ausente |
|---|---|---|
| Envelope do provedor | journal, `raw_base64` | chave ausente |
| Normalização | `src/agents/llm_client.py` (`usage.get("thoughtsTokenCount")`) | `thoughts_tokens: null` no registro da chamada (correto: "não informado") |
| Agregação do comitê | `scripts/multiasset_radar.py`, `sum((u.get(key) or 0) for u in usage)` | `null` vira **0** e entra na soma |
| Custo do comitê | mesmo arquivo: `(prompt × 0,75 + (completion + thoughts) × 3,75) / 10⁶`, em ponto flutuante | calculado com pensamento = 0 |
| Gravação | `result.json` (`tokens.thoughts_tokens`, `cost_usd`, `cost_basis = "provider tokens incl thinking; estimated billing, not invoice"`) | o zero e o custo aparecem como estimativa de cobrança |

`scripts/multiasset_radar.py` é código selado do tratamento
`HFL-MULTIASSET-RADAR-V1` (SHA-256 `8ff6fef5…ee7c32`, o mesmo registrado nas
fontes dos contextos Global PM). Ele não foi editado: corrigir a agregação
mudaria o manifesto do tratamento.

## 4. Registro original × interpretação corrigida

| Camada | Conteúdo |
|---|---|
| **Registro imutável original** | `result.json` com `thoughts_tokens: 0` (4 comitês) ou `374` (VALE3) e `cost_usd` em ponto flutuante; hashes da seção 1, iguais aos `result.sha256` gravados |
| **Interpretação originalmente registrada** | `cost_basis`: "provider tokens incl thinking; estimated billing, not invoice" (custo estimado incluindo pensamento) |
| **Evidência bruta do provedor** | campo ausente em 28/29 chamadas; nenhum zero explícito |
| **Inconsistência identificada** | a agregação transforma ausência em zero; o custo gravado não inclui pensamento não informado e não é uma estimativa completa |
| **Interpretação corrigida (auditoria)** | pensamento `NOT_REPORTED` (PETR4, ITUB4, WEGE3, BBAS3) ou `PARTIALLY_REPORTED: 374 em 1/6` (VALE3); `cost_usd` gravado = **piso observado** pelos tokens informados (confere exatamente nos 5 comitês); custo estimado `UNKNOWN`; cobrança `UNKNOWN` |

## 5. Valores por comitê

| Comitê | Chamadas | Entrada | Saída | Pensamento informado | Total informado | Piso observado (USD) | Estimado | Cobrado |
|---|---|---|---|---|---|---|---|---|
| PETR4 | 6 | 5.897 | 961 | não informado | 6.858 | 0,0080265 | UNKNOWN | UNKNOWN |
| VALE3 | 6 | 5.900 | 1.222 | 374 (1/6 chamadas) | 7.496 | 0,01041 | UNKNOWN | UNKNOWN |
| ITUB4 | 6 | 5.890 | 841 | não informado | 6.731 | 0,00757125 | UNKNOWN | UNKNOWN |
| WEGE3 | 6 | 5.897 | 1.148 | não informado | 7.045 | 0,00872775 | UNKNOWN | UNKNOWN |
| BBAS3 | 5 | 5.595 | 1.122 | não informado | 6.717 | 0,00840375 | UNKNOWN | UNKNOWN |
| **Total** | **29** | **29.179** | **5.294** | **374 (1/29)** | **34.847** | **0,04313925** | **UNKNOWN** | **UNKNOWN** |

Esses totais e o piso coincidem com a V7.5 (`radar.tokens`,
`radar.usd_observed_lower_bound`), recalculados por um caminho independente
(envelopes brutos, não o `token_usage` normalizado).

## 6. O que a errata não afirma

- Não afirma que houve pensamento nas 28 chamadas. A ausência do campo e a
  igualdade entrada + saída = total são **compatíveis** com pensamento zero se o
  provedor omitir campos de valor zero, mas essa convenção não está documentada
  nas evidências locais. A classificação permanece `NOT_REPORTED`.
- Não afirma cobrança. Sem fatura do provedor, o valor pago é `UNKNOWN`.
- Não reclassifica nenhum resultado científico do Radar nem do Global PM.

## 7. Efeito sobre documentos anteriores

- **V7.5:** o `COST_ACCOUNTING.md` já tratava o `cost_usd` como piso e o
  pensamento como não informado. A errata acrescenta o caso parcial de VALE3,
  que a V7.5 tratou só como "informado em 1 das 29 chamadas".
- **Campanhas futuras:** o protocolo V7.6 usa o piso pelos tokens brutos e
  nunca o `cost_usd` agregado do Radar como estimativa
  (`METRIC_CATALOG.json`, `usd_observed_lower_bound`).
- **Correção de código:** só em um tratamento Radar novo, versionado (ver
  [RESEARCH_ROADMAP.md](RESEARCH_ROADMAP.md)).
