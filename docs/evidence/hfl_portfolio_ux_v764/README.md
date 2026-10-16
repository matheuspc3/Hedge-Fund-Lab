# HFL Premium V7.6.4 — Portfolio UX & Paper Monitoring Foundation

Implementação funcional de UX-M5 e da consulta HFL-PAPER-001, em 13/10/2026.
A carteira multiativos oficial ainda é um **snapshot hipotético consultivo**, não um ledger prospectivo. O acompanhamento H2 lê cinco carteiras persistidas independentes. Nenhuma operação ou inferência foi executada por esta entrega.

## Uso

```powershell
.venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8116
```

- `/portfolio#visao-geral`: patrimônio e caixa da fonte selecionada.
- `/portfolio#posicoes`: posições e sessões reconciliadas.
- `/portfolio#global-workflow`: inferências oficiais V1/V2, motivos, projeção, evidências.
- `/portfolio#simulador`: fixtures V5/V6 isoladas.
- `/portfolio#evidencias`: operações e linha do tempo da carteira selecionada.
- `/paper?wallet=h2%3Aai#acompanhamento`: acompanhamento H2 somente leitura.
- `?analysis=<registro>` abre a decisão; `?wallet=<id>` seleciona a carteira. `?run=` do Radar permanece na URL.

V1: **REJECTED_BY_VALIDATOR**. V2: **VALID_PROPOSAL**, caixa-alvo 100%, zero operações. H2 supervisionada: **EXPIRADA** após 10h BRT de 13/10, sem aprovação ou execução registrada. H2 original: intenção pendente, última marcação 09/10. Não houve compra retroativa.

## Documentação

| Documento | Conteúdo |
|---|---|
| [PORTFOLIO_ARCHITECTURE.md](PORTFOLIO_ARCHITECTURE.md) | arquitetura anterior/nova e contrato GET |
| [GLOBAL_PM_HISTORY.md](GLOBAL_PM_HISTORY.md) | registros primários V1/V2 e datas |
| [PORTFOLIO_INFORMATION_HIERARCHY.md](PORTFOLIO_INFORMATION_HIERARCHY.md) | navegação e divulgação progressiva |
| [PAPER_MONITORING.md](PAPER_MONITORING.md) | consulta implementada e bloqueios operacionais |
| [PAPER_DATA_SOURCE_AUDIT.md](PAPER_DATA_SOURCE_AUDIT.md) | inventário por recurso, persistência e efeitos |
| [PORTFOLIO_PROVENANCE.md](PORTFOLIO_PROVENANCE.md) | isolamento, preços e datas |
| [DEMONSTRATION_SEPARATION.md](DEMONSTRATION_SEPARATION.md) | cenários didáticos independentes |
| [COMPONENT_CATALOG.md](COMPONENT_CATALOG.md) | componentes compartilhados |
| [INTERACTION_TESTS.md](INTERACTION_TESTS.md) | testes funcionais e Chrome |
| [ACCESSIBILITY_REPORT.md](ACCESSIBILITY_REPORT.md) | verificações e limites WCAG |
| [VISUAL_REGRESSION.md](VISUAL_REGRESSION.md) | capturas reais e correções |
| [REGRESSION_REPORT.md](REGRESSION_REPORT.md) | suíte, baseline e diferença 15/14 |
| [PRESERVATION_REPORT.md](PRESERVATION_REPORT.md) | snapshots e preservação |
| [NEXT_STEPS.md](NEXT_STEPS.md) | contrato operacional futuro e pendências |

Validação direcionada: **55 passed, 23 subtests passed**. Adaptador final: **12 passed**. Chrome V7.6.4: **36/36**. **Regressão completa final: 1765 passed, 14 falhas preexistentes, 61 subtests passed.** Comparação por nome: nenhuma falha nova. Preservação final: `violations: []`; 227 arquivos Global PM/V5 idênticos e snapshot Radar/H2 sem alterações. V7.5 íntegra e V7.6 sem erros.

Implementado: consulta persistente, seletor, atualização GET, posições, histórico, decisões, proveniência e estados vazios/erro. Pendente: execução prospectiva multiativos, atualização automática e campos financeiros que o ledger H2 não publica. Não se declara monitoramento automático completo.

Base inicial: `888c8d7`. `out.json` já existia não rastreado e permanece do operador. Commits locais: `e7fa1f1` adaptador; `07cecc3` interface; `41d8cb1` testes; `50094aa` documentação; `09f06b2` preservação da API selada e mock de interface. A validação completa corresponde a `09f06b2`; o commit final acrescenta somente relatórios. Sem push.

## Relatório ao operador

| # | Item | Resultado |
|---|---|---|
| 1 | Resumo executivo | UX-M5 e fundação de consulta paper implementados; execução multiativos automática pendente |
| 2 | Arquitetura | página empilhada → cinco áreas; leitor de evidências, adaptador GET e componentes de apresentação |
| 3 | Páginas | portfolio.html e paper.html; navegação compartilhada e aliases mantidos |
| 4 | Componentes | monitoring.js/css e monitoring_api.py; design system/glossário/Chart.js existentes |
| 5 | V1/V2 | rejeitada/validada; ambas consultáveis, sem inferência nova |
| 6 | Demonstrações | V5/V6 preservadas exclusivamente no Simulador, com dados sintéticos identificados |
| 7 | Carteiras paper | cinco carteiras H2 independentes, sem soma de patrimônio |
| 8 | Fontes persistentes | estados H2, sessões/trades, aprovações, marcas, contextos/resultados e ledger V5 sintético |
| 9 | Monitoramento implementado | seletor, consulta/refresh, posições, caixa, decisões, operações, curva, eventos, fonte/sessão, links, erros |
| 10 | Bloqueios | nenhum ledger oficial multiativos prospectivo nem atualização diária automática |
| 11 | Posições/caixa/operações | derivados dos registros financeiros escolhidos; alvo não vira posição; ausente não vira zero |
| 12 | Preços | locais, já congelados; H2 ajustado; marcas legadas V2 declaradas sintéticas; sem cotação externa nova |
| 13 | Patrimônio | última marca/sessões reconciliadas existentes; GET não avança pregão |
| 14 | Decisões futuras | novos registros selados entram no catálogo; execução exige mecanismo/autorização financeira específicos |
| 15 | H2 de 13/10 | supervisionada EXPIRADA sem aprovação; original pendente; nenhuma operação reconciliada disponível |
| 16 | Testes funcionais | 55 passed + 23 subtests direcionados; adaptador final 12 passed; correções/jornada 15 passed |
| 17 | Navegador | 36/36 novos checks; jornadas V7.6.2/V7.6.3 também passaram na suíte final |
| 18 | Capturas | nove PNGs reais em screenshots/, incluindo V1, V2, Simulador, H2 e mobile |
| 19 | Acessibilidade | teclado/foco/ajuda/tabelas/reflow testados; zoom nativo e leitor de tela pendentes UX-M8 |
| 20 | Regressão geral | 1765 passed, 14 falhas conhecidas, 61 subtests; nenhuma regressão nova por nome |
| 21 | Preservação | violations: []; dados e baselines preservados; API selada byte a byte |
| 22 | Roadmap | UX-M5 e HFL-PAPER-001 registrados com pendências UX-M6/M7/M8 explícitas |
| 23 | Commits | locais e pequenos por frente, listados acima; sem push |
| 24 | Limitações | snapshot V2 não é ledger; histórico atual de uma sessão; campos H2 ausentes; acessibilidade integral pendente |
| 25 | Próxima etapa | revisão do contrato operacional multiativos/ingestão e autorizações, sem execução automática nesta entrega |
