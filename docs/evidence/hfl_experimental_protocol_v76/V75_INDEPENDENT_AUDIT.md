# Auditoria da consolidação V7.5

**Objeto:** `docs/evidence/hfl_scientific_consolidation_v75/` (commits
`adecfb6`, `12c94ed`, `b171c80`), `scripts/verify_consolidation_v75.py`,
`tests/test_consolidation_v75.py`.
**Método:** verificadores somente leitura e uma recomputação por caminho
diferente do usado pela V7.5. A V7.5 somou o `token_usage` normalizado; aqui os
números saem dos envelopes brutos do provedor. Além disso, as tabelas
publicadas foram confrontadas com o código das regras determinísticas.
**Reprodução:** `.venv/Scripts/python.exe -B scripts/experiment_protocol_v76.py audit`
(saída também em `READINESS_REPORT.json → v75_audit`).

> **Limite da independência.** A V7.5 e esta auditoria foram produzidas pelo
> mesmo agente. A independência é de **método** (outro caminho de cálculo e
> outras fontes de verdade), não de **pessoa**. Uma revisão humana separada
> continua necessária (ver [README.md](README.md), pendências).

## 1. Verificações

| # | Verificação | Resultado |
|---|---|---|
| 1 | Hashes das 64 fontes do `EVIDENCE_MANIFEST.json` | conferem; `violations: []`, nenhuma mudança OPERATIONAL |
| 2 | Existência das fontes primárias | todas presentes (`missing: []`) |
| 3 | Separação real × sintético | nenhuma métrica de resultado cita fonte SYNTHETIC; os dois IDs reais têm `planner = GEMINI_GLOBAL_PM`; 18 registros sintéticos fora dos resultados |
| 4 | Reprodutibilidade das métricas | as 32 métricas, recalculadas, são idênticas a `METRICS.json` |
| 4b | Recomputação independente (envelopes brutos) | Radar: 29 chamadas, 29.179 / 5.294 / 34.847 tokens, 374 de pensamento; V1: 18.794 / 2.519 / 21.313; V2: 20.623 / 2.880 / 23.503. Todos iguais à V7.5 |
| 5 | Resultados selados × tabelas | `REJECTED_BY_VALIDATOR` (V1) e `VALID_PROPOSAL` (V2) na tabela principal; valores de volatilidade e RSI do Radar (relatório §6) presentes e iguais às métricas; números de tokens e custo de `COMPARISON_V1_V2.md` e `COST_ACCOUNTING.md` conferidos pelo verificador da V7.5 |
| 6 | Conclusões financeiras não demonstradas | nenhuma afirmação afirmativa de superioridade, retorno, alfa, Sharpe ou redução de risco em `SCIENTIFIC_REPORT.md`, `TCC_RESULTS_DRAFT.md`, `COMPARISON_V1_V2.md`, `README.md` (varredura lexical com tratamento de negação; o teste confirma que uma frase indevida é detectada) |
| 7 | Preservação de V1 e V2 | status selados inalterados; `contracts()` V1 = selado no contexto V1; `contracts()["sha256"]` V2 = selado no contexto V2 |
| 8 | Contagens declaradas | 64 fontes, 32 métricas, regressão "15 failed, 1706 passed" em `regression.txt`: confirmadas |
| 9 | Teste da V7.5 | `tests/test_consolidation_v75.py`: 2 aprovados |

## 2. Achados

### A1 — Restrição determinística omitida nas tabelas da V7.5 (correção de conteúdo)

O motor V5 (`scripts/multiasset_manager.py:399`) só admite **compra** de ativo
cuja recomendação final do parecer é COMPRA (`buy_incompatible_with_opinion`).
A V7.5 não registrou essa regra:

| Documento V7.5 | Linha | Publicado | Correto |
|---|---|---|---|
| `COMPARISON_V1_V2.md` §3 e `SCIENTIFIC_REPORT.md` §6.1 | WEGE3 | restrição determinística: "nenhuma" | compra não admitida (recomendação MANTER) |
| idem | VALE3 | "sem custódia: venda impossível" | também compra não admitida (recomendação VENDA) |
| idem | BBAS3 | veto | veto e recomendação final MANTER (compra também barrada por esta regra) |
| idem | PETR4, ITUB4 | "nenhuma; compra permitida, não obrigatória" | correto |

Consequência: na sessão estudada, **só PETR4 e ITUB4 podiam receber compras**.
A frase "COMPRA não obriga compra" continua correta; o que falta é que **sem
COMPRA, compra é proibida**. Nenhum resultado selado muda. As conclusões da
V7.5 continuam válidas, e a decisão "100% em caixa" permanece admissível. O
achado foi revelado pelo caso `S2-buy-without-compra-opinion` da qualificação
V7.6. Os documentos da V7.5 não foram editados; esta seção é a errata deles.

### A2 — Soma parcial de pensamento em VALE3

A V7.5 apontou quatro comitês com `thoughts_tokens: 0` gravado sobre campos
ausentes. O registro de VALE3 (374) também é uma soma parcial: 1 chamada
informada e 5 ausentes. Tratado em [RADAR_TOKEN_ERRATUM.md](RADAR_TOKEN_ERRATUM.md).

### A3 — Horário da qualificação sintética V2

O relatório V7.5 (§5.1, etapa 12) dá "≈ 16:12", a partir do horário de
modificação dos diretórios. Os campos selados dos cinco registros `v74-qual-*`
confirmam 19:12:02–19:12:04 UTC (16:12 BRT), antes do commit `020d1cc` (16:18).
O valor está correto; a fonte adequada são os campos selados, não o mtime.

### A4 — Códigos do validador V2 sem descrição

O validador V2 pode emitir dois códigos que não constam da tabela de descrições
`ERRORS` de `multiasset_global_pm_v2.py`: `concentration_or_exposure_limit`
(vindo do motor V5) e `record_hash_mismatch` (selo de contexto adulterado). A
afirmação da V7.4 de que `ERRORS` descreve "todos os códigos" não é exata. A UI
mostraria o código sem descrição. O arquivo é selado no contrato V2 e não foi
alterado; os dois códigos estão declarados em `SCENARIO_MATRIX.json →
undescribed_codes`, e o validador do protocolo acusa se algum deles passar a
ter descrição (indicando mudança de contrato).

### A5 — Cobertura da conferência automática de tabelas

O verificador da V7.5 confere automaticamente só os números de tokens e custo
de duas tabelas. A tabela §6 do relatório foi conferida nesta auditoria. Os
demais números do relatório e do rascunho do TCC continuam conferidos só por
leitura. Não se encontrou divergência.

### A6 — Dependência de registros locais

Os testes e verificadores da V7.5 pulam ou acusam `missing` numa cópia sem
`data/`. Isso já estava documentado; continua sendo o principal limite de
auditoria externa (ver [RESEARCH_ROADMAP.md](RESEARCH_ROADMAP.md)).

## 3. Conclusão da auditoria

O pacote V7.5 é íntegro e reprodutível: hashes, fontes, métricas e status
selados conferem, e não há conclusão financeira indevida. Há uma omissão de
conteúdo (A1) na camada interpretativa e uma imprecisão de contabilidade
já coberta pela errata (A2). Nenhum achado altera resultados selados ou as
conclusões sustentadas da V7.5.
