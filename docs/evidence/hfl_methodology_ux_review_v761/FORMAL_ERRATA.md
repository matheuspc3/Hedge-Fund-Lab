# Erratas formais (não destrutivas)

| Campo | Valor |
|---|---|
| Emissão | 12/10/2026, V7.6.1 |
| Natureza | notas de auditoria vinculadas a hashes; **nenhum** arquivo selado, journal, claim, reserva, registro de custo ou documento V7.5/V7.6 foi editado |
| Estado | **formalizadas; ratificação humana pendente** |
| Efeito sobre inferências seladas | nenhum: os status `REJECTED_BY_VALIDATOR` (V1) e `VALID_PROPOSAL` (V2) e os pareceres do Radar permanecem |

---

## ERRATUM-HFL-2026-001 — Tokens de pensamento no agregado do Radar

**Origem:** auditoria V7.5 (`COST_ACCOUNTING.md` §3), detalhada na V7.6
([RADAR_TOKEN_ERRATUM.md](../hfl_experimental_protocol_v76/RADAR_TOKEN_ERRATUM.md)).
**Reprodução:** `.venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py erratum`.

### Evidência original (imutável)

| Comitê | `result.json` SHA-256 (= `result.sha256` gravado) | `provider_journal.jsonl` SHA-256 (prefixo) | `thoughts_tokens` gravado | `cost_usd` gravado |
|---|---|---|---|---|
| PETR4 | `c63d7fdb025ba5e400a6432d32c3200cb2cd4afb02337c5b2e56cc1ff9fe5328` | `4c9f8bb0480c9c17…` | 0 | 0,0080265 |
| ITUB4 | `4f96331a5dae68d9a860577d6ce31ce7266e1846abf99c0a941c7bed651ee7d0` | `1f00e51b30d355e4…` | 0 | 0,00757125 |
| WEGE3 | `e085e3f8f0b58649656e2f3fa60b9d5da8d761d6369f9c091d2388524fbfd118` | `dba1aa60ad133584…` | 0 | 0,00872775 |
| BBAS3 | `33c2b4f747bfefafd2266c1c2e4c482dd38b0371c60ca9016321cb618cb39df1` | `602fb978a0cdc56a…` | 0 | 0,00840375 |
| VALE3 | `cfdb44b972be1e4f91ab22f25564462ae69438c9781aa7467a716d1c640a64e8` | `cb1135c4bad7206c…` | 374 | 0,01041 |

Código da agregação: `scripts/multiasset_radar.py` (SHA-256
`8ff6fef588bff4c13f0e302f4cbdd700d075e72d7e51006d3728a185ccee7c32`, selado no
tratamento `HFL-MULTIASSET-RADAR-V1`), `sum((u.get(key) or 0) for u in usage)`.

### Vocabulário de estados

| Estado | Definição | Ocorrência nas 29 chamadas |
|---|---|---|
| **Valor bruto informado** | `thoughtsTokenCount` presente com inteiro > 0 no envelope do provedor | 1 (VALE3, analista 2: 374) |
| **Campo ausente** | a chave não existe no `usageMetadata` bruto | 28 |
| **Zero explícito** | a chave existe com valor 0 | 0 |
| **Total parcial** | soma de um comitê em que só parte das chamadas informou o campo | VALE3 (374 = 1 informada + 5 ausentes) |
| **Valor desconhecido** | quantidade real de pensamento das chamadas com campo ausente | 28 chamadas; não determinável localmente |
| **Piso de custo observado** | (entrada × 0,75 + (saída + pensamento informado) × 3,75) / 10⁶ USD | US$ 0,04313925 no lote (igual à soma dos `cost_usd` gravados) |
| **Reserva conservadora** | teto local bloqueado antes do lote, nunca liberado | US$ 3,31776 |
| **Cobrança efetiva** | valor faturado pelo provedor | **não confirmada** (`UNKNOWN`) |

### Interpretação anterior × corrigida

| | Publicado | Corrigido |
|---|---|---|
| `thoughts_tokens` de PETR4, ITUB4, WEGE3, BBAS3 | 0 | `NOT_REPORTED` (ausente, não zero) |
| `thoughts_tokens` de VALE3 | 374 | `PARTIALLY_REPORTED: 374 em 1/6 chamadas` |
| `cost_usd` dos cinco comitês | "estimated billing" | piso pelos tokens informados; custo estimado `UNKNOWN` |
| Cobrança do lote | — | `UNKNOWN` |

**Impacto científico:** nenhum sobre votos, sinais, Risk e recomendações.
Afeta só a leitura de custo: comparações de custo entre o Radar e outros
componentes só podem usar pisos. **Correção de código:** só em um tratamento
Radar novo e versionado.

---

## ERRATUM-HFL-2026-002 — Restrição de compra omitida nas tabelas da V7.5

**Origem:** qualificação V7.6 (caso `S2-buy-without-compra-opinion`) e
auditoria V7.6, achado A1
([V75_INDEPENDENT_AUDIT.md](../hfl_experimental_protocol_v76/V75_INDEPENDENT_AUDIT.md)).

### Evidência original

| Documento V7.5 | SHA-256 (cópia LF commitada em `12c94ed`) | Local |
|---|---|---|
| `COMPARISON_V1_V2.md` | `a55dc8843547adf4a70edcab9d15d5748399ffa63d70b2d82d76b3dd434fa727` | §3, coluna "Restrição determinística aplicável" |
| `SCIENTIFIC_REPORT.md` | `7760c13802e2eeda20667445bd639befc07325ada1d67ff0a85953292633978b` | §6.1, mesma coluna |

### Regra efetiva

`scripts/multiasset_manager.py` (SHA-256 `4caf6bf84f983778c647f07430390c9d02e0eaa23800cd793c8e97e2f3ed8fa4`, igual ao selado em
`contracts.sources_sha256` dos contextos V1 e V2), linhas 397–400:

```python
if opinion["risk_verdict"] == "VETADO":
    raise ValueError("individual_veto")
if op["side"] == "BUY" and opinion["recommendation"] != "COMPRA":
    raise ValueError("buy_incompatible_with_opinion")
```

### Interpretação anterior × corrigida

| Ativo | Recomendação final | Publicado na V7.5 | Corrigido |
|---|---|---|---|
| PETR4 | COMPRA | nenhuma restrição; compra permitida, não obrigatória | **correto** |
| ITUB4 | COMPRA | idem | **correto** |
| WEGE3 | MANTER | "nenhuma" | **compra proibida** (`buy_incompatible_with_opinion`) |
| VALE3 | VENDA | "sem custódia: venda impossível" | venda impossível sem custódia **e compra proibida** |
| BBAS3 | MANTER (veto) | veto | veto (nenhuma operação) **e** compra também barrada pela recomendação |

**Impacto científico:** na sessão de 09/10/2026, só PETR4 e ITUB4 podiam
receber compras. As conclusões da V7.5 continuam válidas ("COMPRA não obriga
compra"; "100% em caixa é admissível"). A frase deve ser completada: **sem
COMPRA, compra é proibida pelo motor financeiro**. Nenhuma inferência selada
foi afetada: as duas propostas reais não tinham operações. O rascunho do TCC
(V7.5) não cita a regra e não precisa de correção, mas deve incorporá-la
quando descrever as restrições.

---

## Procedimento de ratificação

1. Revisão humana desta página.
2. Se ratificadas, citar os IDs `ERRATUM-HFL-2026-001/002` no texto do TCC e
   em qualquer documento derivado futuro.
3. Nunca editar os arquivos originais; a errata é a correção.
