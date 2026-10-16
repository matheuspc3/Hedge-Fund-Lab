# HFL Premium V7.6.1 — Revisão metodológica e blueprint de UX

Duas frentes, sem inferência, sem chamada ao Gemini, sem operação financeira,
sem alteração de resultados, tratamentos selados ou interface:

- **A. Governança científica:** erratas formais, análise da política de veto,
  decisões do pré-registro organizadas para aprovação, revisão do piloto,
  calendário B3 e holdout H2, triagem das falhas. O protocolo
  `HFL-V76-ROBUSTNESS-PROTOCOL` 1.0.0 **continua `QUALIFIED_OFFLINE`**, pronto
  para revisão humana.
- **B. UX/UI:** auditoria integral da interface, arquitetura de informação
  proposta, jornadas, nomenclatura, glossário com ajuda "?", design system,
  wireframes e plano de migração. A iniciativa está registrada no roadmap
  canônico ([`docs/ROADMAP.md` §10.1](../../ROADMAP.md)) como **`HFL-UX-001`,
  prioridade ALTA, DISCOVERY / DESIGN — IMPLEMENTATION PENDING APPROVAL**.

## Índice

| Frente | Documento | Conteúdo |
|---|---|---|
| A | [V76_READINESS_REVIEW.md](V76_READINESS_REVIEW.md) | números da V7.6 conferidos; bloqueios e resolução; independência |
| A | [FORMAL_ERRATA.md](FORMAL_ERRATA.md) | `ERRATUM-HFL-2026-001` (tokens do Radar) e `-002` (restrição de compra) |
| A | [RISK_VETO_POLICY_DECISION.md](RISK_VETO_POLICY_DECISION.md) | veto absoluto × só redução × redução condicionada; recomendação B num tratamento novo |
| A | [PREREGISTRATION_DECISIONS.md](PREREGISTRATION_DECISIONS.md) | decisões D1–D12 com opções, consequências e recomendação |
| A | [REPETABILITY_PILOT_REVIEW.md](REPETABILITY_PILOT_REVIEW.md) | piloto de 10: intervalos, métricas, regras de ampliação, variabilidade |
| A | [B3_CALENDAR_AND_HOLDOUT_REVIEW.md](B3_CALENDAR_AND_HOLDOUT_REVIEW.md) | sessões C3 conferidas no COTAHIST oficial (10/10); proteção do holdout |
| A | [REGRESSION_REPORT.md](REGRESSION_REPORT.md) | o que é corrigível com segurança × o que exige revisão; resultado da suíte |
| B | [UX_AUDIT.md](UX_AUDIT.md) | inventário das 7 páginas e 18 rotas; 15 achados; causas |
| B | [INFORMATION_ARCHITECTURE.md](INFORMATION_ARCHITECTURE.md) | sitemap atual, sitemap proposto, responsabilidade de cada página |
| B | [USER_JOURNEYS.md](USER_JOURNEYS.md) | jornadas A–F, atual × proposta |
| B | [NAMING_AND_TERMINOLOGY.md](NAMING_AND_TERMINOLOGY.md) | convenções e dicionário nome atual → proposto |
| B | [CONTEXTUAL_HELP_GLOSSARY.md](CONTEXTUAL_HELP_GLOSSARY.md) | padrão do "?" e glossário amarrado ao código |
| B | [DESIGN_SYSTEM_PROPOSAL.md](DESIGN_SYSTEM_PROPOSAL.md) | tokens, componentes, estados, naturezas de ação, confirmação de custo, mensagens |
| B | [WIREFRAMES.md](WIREFRAMES.md) | wireframes das jornadas principais |
| B | [UX_MIGRATION_PLAN.md](UX_MIGRATION_PLAN.md) | marcos UX-M1…M8, decisão U10, critérios de aceite |
| dados | [ux_inventory.json](ux_inventory.json), [calendar_check.json](calendar_check.json) | saídas de `scripts/review_v761.py` |

**Consolidações** (o enunciado as permite): `CURRENT_SITEMAP` e
`PROPOSED_SITEMAP` → `INFORMATION_ARCHITECTURE.md`; `UX_ACCEPTANCE_CRITERIA` →
`UX_MIGRATION_PLAN.md` §4; `REGRESSION_TRIAGE` → `REGRESSION_REPORT.md`;
`PRESERVATION_REPORT` e `NEXT_STEPS` → este README. Cada par descrevia o mesmo
objeto em dois arquivos.

**Código novo (ferramenta de auditoria, não científica):**
`scripts/review_v761.py` (inventário de UX lido de `server.py` e do HTML/JS;
conferência de calendário só por data) e `tests/test_review_v761.py`. Nenhum
arquivo do `dashboard/`, dos runners ou dos validadores foi alterado.

## Achados que exigem atenção

1. **Caminho pago para um tratamento fechado (U10):** "Solicitar proposta" em
   `/portfolio` usa o runner do Global PM **V1**, declarado fechado pelo
   protocolo V7.6; a V2 só roda pelo CLI. Recomendação: desabilitar o caminho
   pago V1 na UI, o que exige decisão humana porque muda comportamento.
2. **Veto absoluto** impede reduzir ou zerar posição vetada (verificado em
   memória). Irrelevante para C1/C3 (caixa), decisivo para C2/C4.
3. **Vagas V2 compartilhadas:** o teto selado comporta 29 chamadas **no total**.
   C1 = 29 inviabiliza C3 com o mesmo tratamento. Recomendação: C1 = 19
   (10 + 9) e C3 = 10.
4. **Calendário:** as 27 sessões da janela C3 e as 10 selecionadas existem no
   COTAHIST oficial (SHA igual ao registrado pelos inputs do Radar), lidas só
   por data.
5. **Holdout H2:** o histórico dos indicadores de setembro/2026 contém barras
   da janela FINAL_TEST (entrada, não avaliação). Declarar e decidir.
6. **Sharpe com volatilidade zero:** o código H2 retorna 0,0 por convenção; o
   catálogo V7.6 define "indefinido". A interface e o TCC devem usar
   "indefinido".

## Pendências de aprovação humana

| # | Decisão | Documento |
|---|---|---|
| 1 | Ratificar `ERRATUM-HFL-2026-001` e `-002` | FORMAL_ERRATA |
| 2 | Política de veto (A, B ou C) e, se B/C, novo tratamento | RISK_VETO_POLICY_DECISION |
| 3 | Decisões D1–D12 do pré-registro | PREREGISTRATION_DECISIONS |
| 4 | Aceitar a sobreposição de histórico com a janela H2 em C3 | B3_CALENDAR_AND_HOLDOUT_REVIEW |
| 5 | Correções de teste seguras × metodológicas | REGRESSION_REPORT |
| 6 | Aprovar UX-M1 (sitemap, nomes, design system) antes de qualquer implementação | UX_MIGRATION_PLAN |
| 7 | Caminho pago V1 na UI (U10) | UX_MIGRATION_PLAN §3 |
| 8 | Revisão humana independente da V7.5/V7.6/V7.6.1 | V76_READINESS_REVIEW §4 |

## Próximos passos recomendados (não iniciados)

1. Revisão humana das pendências 1–3 e 8 → protocolo 1.1.0 com decisões,
   congelamento → campanha C1 (estágio 1 de 10 tentativas).
2. Em paralelo, aprovação do UX-M1 → UX-M2 (componentes) e UX-M3 (navegação),
   incluindo a decisão U10.

## Verificação final

Executada depois dos commits `a381c23` e `c3986a9`, com a árvore limpa.

| Verificação | Resultado |
|---|---|
| `check_preservation.py --since preservation_before.json` ([preservation_since.json](preservation_since.json)) | `changes: []`, `violations: []` |
| Baselines históricos | `violations: []`; só as duas mudanças OPERATIONAL legadas |
| Pacote V7.5 (`verify_consolidation_v75.py`) | `ok: true` |
| Protocolo V7.6 (`experiment_protocol_v76.py validate`) | `errors: []`; estado `QUALIFIED_OFFLINE` |
| Global PM V1 / V2 (`run_global_pm_v2.py incident` / `status`) | `REJECTED_BY_VALIDATOR` (revalidação idêntica) / `VALID_PROPOSAL` |
| `dashboard/`, runners, validadores, `src/` desde `983a9d8` | sem alteração (`git diff` vazio): nenhuma rota mudou de comportamento |
| Registros financeiros ou de inferência criados | nenhum |
| Testes novos | `tests/test_review_v761.py`: 3 aprovados; ruff limpo |

**Regressão** (`pytest -q`, [regression.txt](regression.txt)): **1741 aprovados,
15 falhas**. A suíte **não** está verde. 1741 = 1738 da V7.6 + 3 testes novos.
As 15 falhas são as mesmas da V7.6, nome a nome; nenhum teste antigo foi alterado.
