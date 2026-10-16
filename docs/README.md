# Documentação do Hedge-Fund-Lab

Índice único de documentação, referências e evidências. Revisado em **15/10/2026**.
[Início do vault](../INICIO.md).

Registros diários: [14/10 — dados e diagnóstico](daily/2026-10-14.md) ·
[15/10 — correção autorizada dos custos Multiagentes](daily/2026-10-15.md).

## Ler primeiro

| Documento | Pergunta que responde |
|---|---|
| [Direção do projeto](DIRECAO_DO_PROJETO.md) | Onde queremos chegar e o que já decidimos? |
| [Roadmap](ROADMAP.md) | O que fazemos a seguir e quais são os critérios de saída? |
| [Estado atual](ESTADO_ATUAL.md) | O que existe, foi qualificado ou ainda falta? |
| [Ciclo de uso da plataforma](CICLO_USO_PLATAFORMA.md) | Como criar, alocar, comprar/vender e abrir análises; quais etapas ainda faltam para fechar o uso diário? |
| [Arquitetura](ARQUITETURA.md) | Onde cada responsabilidade está implementada? |
| [Contrato do piloto multiativos — DRAFT](PILOTO_MULTIATIVOS_SPEC.md) | Bases DP-09–DP-15 aprovadas; regras técnicas pendentes; DATA-01, PAPER-02, tela inicial e durabilidade PAPER-03 documentados; ativação oficial pendente |
| [README técnico](../README.md) | Como abrir o projeto e usar os comandos básicos? |

Esta página organiza a consulta. Não mantém cópias das decisões, tarefas ou
resultados; cada informação tem seu documento de referência.

## Multiativos: começar pela V7.6.5

[Registro diário de 14/10/2026](daily/2026-10-14.md): tentativa consultiva bloqueada
por dados incompletos, com diagnóstico persistido; nenhuma previsão ou ordem gerada.

| Referência | Uso |
|---|---|
| [Entrega do ledger](evidence/hfl_paper_ledger_v765/README.md) | Escopo e qualificação offline |
| [Limitações e próximos passos](evidence/hfl_paper_ledger_v765/LIMITATIONS.md) | Bloqueios para operação oficial |
| [Arquitetura](evidence/hfl_paper_ledger_v765/LEDGER_ARCHITECTURE.md) | Identidade, envelope e eventos |
| [Contabilidade](evidence/hfl_paper_ledger_v765/ACCOUNTING_INVARIANTS.md) | Caixa, posições, custos e reconciliação |
| [Persistência](evidence/hfl_paper_ledger_v765/PERSISTENCE_AND_RECOVERY.md) | SQLite, replay, idempotência e recuperação |
| [Calendário e preços](evidence/hfl_paper_ledger_v765/SETTLEMENT_AND_CALENDAR.md) | D+2, fontes e marcação |
| [Integração PM/autorização](evidence/hfl_paper_ledger_v765/GLOBAL_PM_INTEGRATION.md) | Fronteira consultiva e fluxo futuro |
| [API e dashboard](evidence/hfl_paper_ledger_v765/API_READ_MODELS.md) | GET, sessões, filtros e modo sintético |
| [Regressão](evidence/hfl_paper_ledger_v765/REGRESSION_REPORT.md) / [qualificação JSON](evidence/hfl_paper_ledger_v765/QUALIFICATION_RESULT.json) | Resultados registrados, sem nova execução implícita |
| [Preservação](evidence/hfl_paper_ledger_v765/PRESERVATION_REPORT.md) | Integridade verificada naquela entrega |

## Legacy H2/PETR4: contratos e avaliação

Etapa anterior preservada para consulta e documentação do TCC (DP-16).
Na plataforma, `/legacy` reúne piloto PETR4, Pesquisa H2 e backtests históricos.
PETR4 continua no universo multiativos; pesquisa e auditoria multiativos seguem ativas.

| Grupo | Referências originais |
|---|---|
| Método e tratamentos | [Freeze metodológico](H2_METHODOLOGICAL_FREEZE_V1.md), [Amendment 13/v5](H2_V5_AMENDMENT_13.md), [Amendment 14/v6](H2_V6_AMENDMENT_14.md) |
| Avaliação e aprovação | [Proposta](H2_V6_EVALUATION_AMENDMENT_PROPOSAL.md), [deliberação](H2_V6_EVALUATION_AMENDMENT_DELIBERATION.md), [objeto de aprovação acadêmica](H2_V6_ACADEMIC_APPROVAL_SUMMARY.md), [PDF](H2_V6_ACADEMIC_APPROVAL_SUMMARY.pdf) |
| Qualificação da avaliação | [Offline](H2_V6_EVALUATION_OFFLINE_QUALIFICATION.md), [revisão de prontidão](H2_V6_FREEZE_READINESS_REVIEW.md), [integração posterior E1–E5](H2_V6_EVALUATION_PRODUCTION_INTEGRATION.md) |
| Validation provisória OA-1 | [Contrato](H2_V6_OPERATIONAL_AMENDMENT_OA1.md), [síntese científica](H2_V6_OA1_VALIDATION_SCIENTIFIC_SUMMARY.md), [diagnóstico](H2_V6_OA1_VALIDATION_DIAGNOSTIC.md), [runbook](H2_V6_VALIDATION_PROVISIONAL_RUNBOOK.md) |
| Paper e supervisão | [Forward original](H2_V6_FORWARD_PAPER.md), [supervisionada](H2_V6_HUMAN_SUPERVISION_SPEC.md), [dashboard](H2_V6_FORWARD_DASHBOARD.md), [auditoria PENDENTE/EXPIRADA](evidence/hfl_paper_ledger_v765/H2_PENDING_STATE_AUDIT.md) |

O protocolo [EXPERIMENT_PROTOCOL](EXPERIMENT_PROTOCOL.md) mantém o desenho
geral e decisões históricas; freezes/amendments específicos têm precedência
conforme o próprio documento. Proposta, revisão e qualificação não são
aprovação acadêmica nem release do Final Test. Consultar o estado datado.

## Referências versionadas de plataforma e interface

Estes documentos explicam entregas anteriores. Seus comandos, telas, contagens
e próximos passos pertencem às respectivas versões; não são o planejamento ativo.

| Família | Referências |
|---|---|
| H2 UI inicial | [Premium v1](H2_V6_PREMIUM_UI.md), [v2](H2_V6_PREMIUM_V2.md), [revalidação v2](H2_V6_PREMIUM_V2_RECHECK.md), [v3](H2_V6_PREMIUM_V3.md) |
| Multiativos inicial | [Radar V4](HFL_PREMIUM_V4_RADAR.md), [carteira/motor V5](HFL_PREMIUM_V5_PORTFOLIO.md), [PM V6](HFL_PREMIUM_V6_GLOBAL_PM.md), [desenho multiativos](HFL_MULTIASSET_PORTFOLIO_DESIGN.md) |
| Plataforma | [Auditoria inicial V7](HFL_PLATFORM_AUDIT_V7.md), [arquitetura V7](HFL_PLATFORM_ARCHITECTURE.md), [runbook V7.3/V7.4](HFL_OPERATIONS_RUNBOOK.md) |
| UX | [Plano de migração e aceite](evidence/hfl_methodology_ux_review_v761/UX_MIGRATION_PLAN.md); progresso atual no roadmap |

## Evidências por versão

| Grupo | Pacotes preservados |
|---|---|
| Radar/carteira | [Radar inicial](evidence/hfl_multiasset_radar/README.md), [carteira offline](evidence/hfl_multiasset_portfolio/README.md), [Radar V7.3](evidence/hfl_radar_v73/README.md) |
| Global PM | [V1 rejeitada](evidence/hfl_global_pm/README.md), [V2 válida em caixa](evidence/hfl_global_pm_v2/README.md) |
| Plataforma | [V7](evidence/hfl_platform_v7/README.md), [V7.1](evidence/hfl_platform_v71/README.md), [V7.2](evidence/hfl_platform_v72/README.md), [incidente 12/10](evidence/hfl_incident_2026_10_12/README.md) |
| Ciência/robustez | [Consolidação V7.5](evidence/hfl_scientific_consolidation_v75/README.md), [protocolo V7.6](evidence/hfl_experimental_protocol_v76/README.md), [revisão V7.6.1](evidence/hfl_methodology_ux_review_v761/README.md) |
| UX/ledger | [Fundação V7.6.2](evidence/hfl_ux_foundation_v762/README.md), [Mercado/Radar V7.6.3](evidence/hfl_radar_ux_v763/README.md), [Carteiras V7.6.4](evidence/hfl_portfolio_ux_v764/README.md), [ledger V7.6.5](evidence/hfl_paper_ledger_v765/README.md) |
| DATA-01 | [Avaliação do fluxo de coleta e provedores — 14/10/2026](AVALIACAO_COLETA_DADOS_2026-10-14.md); interpretação separada do [catálogo verificável de documentos B3](evidence/pilot_market_data_2026/sources.json). A avaliação não autentica dados nem conclui DATA-01/PAPER-04. |

### Histórico experimental H2

| Família | Pacotes preservados |
|---|---|
| H2 e revisões | [inicial](evidence/h2/), [v2](evidence/h2_v2/), [v3](evidence/h2_v3/), [v4](evidence/h2_v4/), [v5](evidence/h2_v5/), [v6](evidence/h2_v6/) |
| CAL-A | [inicial](evidence/cal_a/), [v2](evidence/cal_a_v2/), [v3](evidence/cal_a_v3/), [v5](evidence/cal_a_v5/), [v6](evidence/cal_a_v6/) |
| Sequential Development | [inicial](evidence/sequential_dev/), [v2](evidence/sequential_dev_v2/), [v3](evidence/sequential_dev_v3/), [v5](evidence/sequential_dev_v5/), [v6](evidence/sequential_dev_v6/) |
| Stress | [inicial](evidence/stress/), [v2](evidence/stress_v2/), [v3](evidence/stress_v3/), [v6](evidence/stress_v6/) |
| CAL-B | [inicial](evidence/cal_b/), [v1/postmortem](evidence/cal_b_v1/), [B2](evidence/cal_b2/), [B3](evidence/cal_b3/), [B4](evidence/cal_b4/) |
| Avaliação | [Avaliação offline](evidence/h2_v6_evaluation/), [OA-1 provisória](evidence/h2_v6_provisional/) |
| Interface paper | [Forward](evidence/h2_forward_dashboard/), [UI v1](evidence/h2_premium_ui/), [UI v2](evidence/h2_premium_v2/), [UI v3](evidence/h2_premium_v3/) |
| Infraestrutura | [Calendário](evidence/calendar/), [runtime do provedor](evidence/provider_runtime/) |

Falha, supersessão ou texto parecido não tornam esses registros descartáveis.
Até marcadores `SUPERSEDED.md` idênticos pertencem a runs distintos. Não fundir
evidências, reexecutar one-shot consumida ou abrir holdout por seguir este índice.

## Pesquisa e material acadêmico

- [Decisões pendentes do pré-registro](evidence/hfl_methodology_ux_review_v761/PREREGISTRATION_DECISIONS.md)
  e [erratas formais](evidence/hfl_methodology_ux_review_v761/FORMAL_ERRATA.md).
- [Materiais da faculdade](faculdade/) e [fonte da monografia](faculdade/monografia/main.tex).
- [Arquivo histórico](archive/README.md): planos, resumos e documentação técnica superados.

Ao citar um resultado, registrar tratamento/run, arquivo, sessão, versão/hash e
natureza: primário, derivado, diagnóstico, interpretativo ou sintético. Reservas
e pisos de custo não são fatura confirmada; conformidade não é rentabilidade.

## Organização no Obsidian e manutenção

O vault é a raiz `Hedge-Fund-Lab`, com `.obsidian` criado pelo usuário. Favoritar
[INICIO](../INICIO.md); notas, contratos, evidências e monografia já estão no vault.
Usar links Markdown relativos e explícitos; não duplicar arquivos para outro vault.
As configurações pessoais existentes permanecem intactas.

| Classe | Como manter |
|---|---|
| Direção/roadmap/estado/arquitetura | Atualizar quando a decisão ou implementação mudar; indicar fonte, data e limites |
| Contratos científicos | Preservar identidade e aprovações; mudanças por documento/versionamento próprios |
| Evidências e entregas versionadas | Preservar bytes e caminhos vinculados a hashes; novas interpretações apontam a fonte e errata |
| Planos/resumos superados | Arquivar documentos mutáveis com aviso e links para o sucessor |
| Cache/layout pessoal/temporários | Limpar somente após comprovar origem, uso e recuperabilidade; nunca confundir com ledger/journal |

O documento de direção guarda o objetivo e as decisões aceitas; o roadmap guarda
prioridades. Cada entrega atualiza estado/roadmap e vincula evidência, sem copiar
logs inteiros para novas notas. Não preencher aprovação de outra pessoa.

Se a busca do Obsidian ficar ruidosa, excluir `.venv`, `data`, `.git` e caches
da navegação nas preferências do aplicativo. Isso não apaga arquivos nem os
remove dos verificadores. Não publicar/sincronizar automaticamente o vault inteiro:
`.env`, journals privados e estados operacionais não integram o pacote público do TCC.

Verificar navegação: `.venv/Scripts/python.exe -B scripts/check_docs.py`.
O check de leitura cobre links locais dos índices ativos e cobertura deste catálogo;
não executa comandos dos documentos, acessa rede ou interpreta dados do holdout.

## Revisão documental de 13/10/2026

- Os índices separados de evidências e organização foram unificados nesta página;
  os dois arquivos redundantes foram removidos após atualização dos consumidores.
- Arquitetura geral e README técnico extensos foram preservados em `archive`;
  as páginas canônicas agora apresentam o mapa atual e comandos essenciais.
- Direção, roadmap e estado continuam separados por responsabilidade.
- Documentos H2/HFL, evidências e monografia mantiveram seus bytes e caminhos.
- `out.json` e configurações pessoais do Obsidian permanecem do operador.

Verificação final desta revisão: 8 páginas ativas, 207 links locais válidos,
33 documentos Markdown na raiz de `docs` e 49 pacotes catalogados. Comparação
antes/depois: 11.400 arquivos de código, testes, contratos, evidências e material
acadêmico mantiveram seus hashes; o verificador existente retornou `violations: []`.
O check documental passou no lint/formatação. Suítes da aplicação não reexecutadas.

Esta revisão organiza a leitura; não cria aprovação científica, campanha,
inferência, posição financeira ou execução paper.

PAPER-01 em 13/10/2026 acrescentou o contrato ativo acima, em DRAFT, com matriz
de reuso, recomendações/decisões pendentes e incrementos DATA-01/PAPER-02/03.
Não altera os pacotes de evidência nem ativa a carteira oficial. Verificações
desta entrega estão no [estado atual](ESTADO_ATUAL.md).
