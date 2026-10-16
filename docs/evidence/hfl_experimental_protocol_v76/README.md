# HFL Premium V7.6 — Protocolo experimental de robustez (qualificado offline)

Preparação, qualificação offline e documentação de uma campanha experimental
futura. **Nenhuma inferência, nenhuma chamada ao Gemini, nenhuma credencial
testada, nenhuma operação financeira, nenhum resultado anterior alterado.**

**Estado do protocolo `HFL-V76-ROBUSTNESS-PROTOCOL` 1.0.0: `QUALIFIED_OFFLINE`.**
Não está `FROZEN_FOR_FUTURE_EVALUATION`, não está
`AUTHORIZED_FOR_PAID_EXECUTION` e não está `EXECUTED`.

## O que a V7.6 entrega

| Pergunta do avaliador | Onde |
|---|---|
| O que será testado, e por quê? | [EXPERIMENTAL_PROTOCOL.md](EXPERIMENTAL_PROTOCOL.md) §1–3, [PREREGISTRATION_DRAFT.md](PREREGISTRATION_DRAFT.md) |
| Como será medido? | [METRIC_CATALOG.json](METRIC_CATALOG.json) (32 métricas), protocolo §7–8 |
| Em que estados de carteira? | [SCENARIO_MATRIX.json](SCENARIO_MATRIX.json) (S0–S9, 34 casos qualificados) |
| Com quantas repetições e a que custo? | [REPETABILITY_DESIGN.md](REPETABILITY_DESIGN.md), [BUDGET_PLAN.json](BUDGET_PLAN.json) |
| Em que sessões? | [OUT_OF_SAMPLE_DESIGN.md](OUT_OF_SAMPLE_DESIGN.md) |
| Como seria a carteira simulada? | [PAPER_TRADING_PROTOCOL.md](PAPER_TRADING_PROTOCOL.md) |
| Contra o quê? | [BASELINES_AND_CONTROLS.md](BASELINES_AND_CONTROLS.md) |
| Que conclusões serão permitidas? | protocolo §9 |
| Está pronto para quê? | [READINESS_REPORT.json](READINESS_REPORT.json), [EXPERIMENT_MANIFEST.json](EXPERIMENT_MANIFEST.json) |
| O pacote anterior é confiável? | [V75_INDEPENDENT_AUDIT.md](V75_INDEPENDENT_AUDIT.md) |
| E os tokens do Radar? | [RADAR_TOKEN_ERRATUM.md](RADAR_TOKEN_ERRATUM.md) |
| E as 15 falhas da suíte? | [TEST_FAILURE_TRIAGE.md](TEST_FAILURE_TRIAGE.md) |
| Como reproduzir? | [REPRODUCIBILITY.md](REPRODUCIBILITY.md) |
| E depois? | [RESEARCH_ROADMAP.md](RESEARCH_ROADMAP.md) |

Código: `scripts/experiment_protocol_v76.py` (auditoria, errata, plano,
validador do protocolo, qualificador offline, readiness; `paid_gate` sempre
recusa) e `tests/test_experiment_protocol_v76.py` (32 testes, um por item pedido;
5/5 mutações das guardas detectadas, [mutation_checks.txt](mutation_checks.txt)). Reutiliza `verify_consolidation_v75.py`, o validador V2 selado,
o motor V5 e os runners somente para leitura. Nenhum arquivo selado foi
editado.

## Resultados principais

- **Auditoria V7.5:** íntegra e reprodutível (64 fontes, 32 métricas, 1706/15,
  tokens recomputados pelos envelopes brutos). Achado de conteúdo: as tabelas
  da V7.5 omitiram que compra só é admitida com recomendação COMPRA
  (WEGE3/VALE3/BBAS3 não podiam ser comprados). Nenhum resultado selado muda.
- **Errata:** PETR4, ITUB4, WEGE3 e BBAS3 gravam `thoughts_tokens: 0` sobre
  campos **ausentes** (28 de 29 chamadas; nenhum zero explícito). A agregação
  selada faz `None → 0`. VALE3 grava uma soma parcial (374 em 1/6). O
  `cost_usd` gravado é o piso observado; custo estimado e cobrado: `UNKNOWN`.
- **Falhas:** as 15 foram reproduzidas e classificadas. As 7 de PostgreSQL passam
  com SQLite temporário, sem serviço (causa comprovada: ambiente). Nenhuma
  envolve código da V7.6.
- **Qualificação offline:** 34/34 casos S0–S9 no validador V2 selado, sobre os
  pareceres oficiais congelados e com respostas roteirizadas; árvores seladas
  inalteradas; hash da qualificação reproduzível. A replicação foi demonstrada
  com contextos de hash distinto e mesma impressão econômica.
- **Orçamento:** o teto selado da V2 permite no máximo **29** novas chamadas.
  Campanhas maiores ou com novos comitês Radar ficam **bloqueadas** até decisão
  humana ou tratamento novo.

## Limitações

Ver protocolo §12 e [PREREGISTRATION_DRAFT.md](PREREGISTRATION_DRAFT.md) §14:
provedor sem determinismo nem versão fixa; sem semente; C1/C2 sobre os inputs
de desenvolvimento; precisão modesta com 29 tentativas; C3 retrospectiva;
calendário auditado só até 31/08/2026; carteira e políticas didáticas; a
auditoria da V7.5 foi feita pelo mesmo agente que a produziu.

## Pendências de revisão humana

1. Revisar e congelar o pré-registro (decisões **[DECIDIR]**: n de C1, taxa
   livre de risco, métrica primária de Q4, pesos de `FIXED_WEIGHTS`).
2. Decidir sobre a errata formal dos documentos V7.5 (achado A1) e de tokens.
3. Decidir sobre as 8 falhas de teste que exigem aprovação metodológica.
4. Autorizar (ou não) a primeira campanha paga.

## Verificação final

Executada depois dos commits `718203e` e `8f5a4dd`, com a árvore limpa.

| Verificação | Resultado |
|---|---|
| `check_preservation.py --since preservation_before.json` ([preservation_since.json](preservation_since.json)) | `changes: []`, `violations: []` |
| Baselines históricos | `violations: []`; só as duas mudanças OPERATIONAL legadas (`job.json`, `last_prepare.json` do Radar original) |
| `verify_consolidation_v75.py` | `ok: true`: as 64 fontes da V7.5, inclusive os registros V1/V2 e os 5 pareceres, mantêm o SHA-256 |
| `experiment_protocol_v76.py validate` | `errors: []`; contratos V2 e Radar iguais aos selados |
| Registros criados em `data/` | nenhum (nenhum `v76-*`) |
| Testes novos | 32 aprovados; 5/5 mutações detectadas |
| Lint | `ruff check` e `ruff format` limpos nos dois arquivos novos |

**Regressão** (`pytest -q`, [regression.txt](regression.txt)): **1738 aprovados,
15 falhas**. A suíte **não** está verde. 1738 = 1706 da V7.5 + 32 testes da
V7.6. As 15 falhas são as mesmas da V7.5 (comparação nome a nome) e estão
classificadas em [TEST_FAILURE_TRIAGE.md](TEST_FAILURE_TRIAGE.md). Nenhuma
envolve código da V7.6, e nenhum teste antigo foi alterado.

## Restrições respeitadas

Sem chamadas ao Gemini nem HTTP ao provedor; nenhuma credencial testada; sem
inferência, Radar pago ou Final Test H2; nenhuma alteração em H2 v6, Radar
original, recovery-01, Global PM V1/V2, contextos, claims, journals,
autorizações, reservas, baselines ou evidências V7.5; nenhuma ordem; nenhum
serviço iniciado; sem push.
