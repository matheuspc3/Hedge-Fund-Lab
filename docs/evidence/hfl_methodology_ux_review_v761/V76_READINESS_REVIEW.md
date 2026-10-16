# Revisão de prontidão do protocolo V7.6

## 1. Números conferidos nos artefatos

| Afirmação do relatório V7.6 | Verificado em | Resultado |
|---|---|---|
| Protocolo `HFL-V76-ROBUSTNESS-PROTOCOL` 1.0.0, `QUALIFIED_OFFLINE` | `EXPERIMENT_MANIFEST.json`, `READINESS_REPORT.json` | confirmado; `protocol_sha256 0da31e25…3bb22` |
| 10 cenários S0–S9 | `SCENARIO_MATRIX.json → scenarios` | 10 |
| 34 casos de qualificação, todos aprovados | `SCENARIO_MATRIX.json → cases`; `READINESS_REPORT.json → qualification` | 34; 34/34 |
| 32 métricas | `METRIC_CATALOG.json → metrics` | 32 |
| 8 campanhas | `EXPERIMENT_MANIFEST.json → campaigns` | 8 |
| 1738 aprovados, 15 falhas | `regression.txt` | confirmado |
| Sem violações de preservação | `preservation_since.json` | `changes: []`, `violations: []` |
| Validação do protocolo | `experiment_protocol_v76.py validate` (V7.6.1) | `errors: []` |
| Testes do protocolo | `pytest tests/test_experiment_protocol_v76.py` (V7.6.1) | 32 aprovados |
| Nenhuma chamada paga | `gpm.records_by_planner` (V7.5) e ausência de registros `v76-*` | confirmado |

## 2. Bloqueios e como cada um se resolve

| Bloqueio (`READINESS_REPORT.json`) | Natureza | Resolução |
|---|---|---|
| `HUMAN_REVIEW_OF_PREREGISTRATION` | governança | revisão e decisões D1–D12 ([PREREGISTRATION_DECISIONS.md](PREREGISTRATION_DECISIONS.md)) |
| `PROTOCOL_FROZEN` | governança | versão 1.1.0 congelada após a revisão |
| `PAID_EXECUTION_AUTHORIZATION` | governança | autorização humana por campanha |
| `COTAHIST_SESSION_VERIFICATION` | dados | **diagnóstico feito**: 10/10 sessões no COTAHIST oficial ([B3_CALENDAR_AND_HOLDOUT_REVIEW.md](B3_CALENDAR_AND_HOLDOUT_REVIEW.md)); remover na 1.1.0 com reconferência na preparação |
| `BUDGET_EXCEEDS_SEALED_V2_CAP_REQUIRES_NEW_TREATMENT_OR_DECISION` | contrato | só na campanha estendida (100); decisão D1/D7 |
| `RADAR_AGGREGATE_EXCEEDS_CAP_REQUIRES_HUMAN_BUDGET_AUTHORIZATION` | orçamento | `radar_runs.py authorize-budget` (humano) |
| `HOLDINGS_PREPARATION_PATH_NOT_IMPLEMENTED` | implementação | caminho de preparo novo, fora dos arquivos selados (C2) |
| `PAPER_LEDGER_NOT_IMPLEMENTED` | implementação | ledger paper multiativo (C4) |

## 3. Pendências metodológicas novas (V7.6.1)

1. **Vagas V2 compartilhadas:** as 29 chamadas valem para todas as campanhas
   V2. C1 = 29 inviabiliza C3 com o mesmo tratamento (D1/D7).
2. **Veto absoluto** trava posições vetadas; isso afeta C2/C4, não C1/C3
   ([RISK_VETO_POLICY_DECISION.md](RISK_VETO_POLICY_DECISION.md)).
3. **Sobreposição de histórico** dos indicadores C3 com a janela H2 (entrada,
   não avaliação): declarar e decidir.
4. **Erratas** 001 e 002 formalizadas, aguardando ratificação
   ([FORMAL_ERRATA.md](FORMAL_ERRATA.md)).

## 4. Independência da revisão

A V7.5, a V7.6 e esta revisão foram produzidas pelo mesmo agente. Os
verificadores usam caminhos de cálculo independentes (envelopes brutos,
código das regras, COTAHIST), mas isso não substitui revisão humana. **Requisito
para congelar:** um(a) revisor(a) humano(a) registra no manifesto 1.1.0
(`human_review`) que conferiu, no mínimo: (a) as erratas; (b) as decisões
D1–D12; (c) uma amostra das conclusões contra as fontes primárias; (d) a lista
de conclusões permitidas e proibidas.

## 5. Estado

**Continua `QUALIFIED_OFFLINE`**, pronto para revisão humana. Nada foi
congelado, autorizado ou executado.
