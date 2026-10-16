# V7.6.2 · Fundação de UX: navegação única, design system e primeiro uso

Implementação real dos marcos **UX-M2** (design system e componentes comuns) e
**UX-M3** (navegação única e nova página inicial) do item de roadmap
`HFL-UX-001`, a partir do blueprint da V7.6.1
([`../hfl_methodology_ux_review_v761/`](../hfl_methodology_ux_review_v761/README.md)).
Inclui a desativação, **apenas na interface**, da ação paga obsoleta do Global PM V1.

Esta entrega **não** é a refatoração completa do frontend. As páginas Radar,
Carteira, Operação diária, H2, Logs e Backtests legados ganharam o shell, os tokens,
os nomes e as naturezas de ação, mas o miolo delas ainda usa componentes antigos
(ver [FRONTEND_ARCHITECTURE.md §5](FRONTEND_ARCHITECTURE.md#5-componentes-legados-ainda-em-uso)).

## Resumo

| Tema | Resultado |
|---|---|
| Navegação | um único menu em todas as 18 rotas; 6 áreas por objetivo (Início, Mercado, Carteira multiativos, Operação diária PETR4, Pesquisa, Auditoria) + Ajuda; breadcrumb; `aria-current`; 5 menus de página removidos |
| Página inicial | apresentação, três garantias, seis tarefas, estado do laboratório lido da API, "como funciona" com a etapa de validação; painéis operacionais mantidos |
| Design system | `design-system.css` com tokens (superfícies, texto, estados, tipografia, espaçamento, foco, camadas) e aliases legados; componentes `ds-*` |
| Ajuda contextual | botão "?" acessível (popover não modal), central de ajuda com busca, glossário único com 36 termos |
| Naturezas de ação | `data-action` = `read`, `prepare`, `verify`, `paid`, `simulate`, `history`; ação paga com ícone ¤ e borda dupla, nunca só por cor |
| Estados | selos com ícone + texto + código original (`VALID_PROPOSAL` → "Proposta validada", `REJECTED_BY_VALIDATOR` → "Rejeitada pelo validador"…) |
| Global PM V1 | preparar, verificar e solicitar ficam ocultos e desabilitados; aviso de encerramento; histórico e recuperação sem nova chamada preservados; **backend ainda aceita a rota (risco residual)** |
| V2 | nenhum atalho pago criado; continua só pelo CLI |
| Testes | `tests/test_ui_v762.py` (9 testes) + 113 verificações de navegador, todas aprovadas |
| Ciência | nenhum validador, runner, política, baseline, registro, claim ou journal alterado; nenhuma inferência executada |

## Índice

| Documento | Conteúdo | Entregáveis pedidos que consolida |
|---|---|---|
| [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) | stack, ligação entre as peças, tokens, componentes, naturezas de ação, estados, ajuda, glossário, componentes legados restantes, receita de migração | FRONTEND_ARCHITECTURE, DESIGN_SYSTEM, CONTEXTUAL_HELP |
| [NAVIGATION_MAPPING.md](NAVIGATION_MAPPING.md) | antes × depois, mapa link a link, rotas e deep links preservados, divergências do blueprint, nova página inicial | NAVIGATION_MAPPING, HOMEPAGE_IMPLEMENTATION |
| [V1_PAID_ACTION_AUDIT.md](V1_PAID_ACTION_AUDIT.md) | gatilhos, correção, o que foi preservado, risco no backend, verificação | V1_PAID_ACTION_AUDIT |
| [ACCESSIBILITY_AND_VISUAL_REPORT.md](ACCESSIBILITY_AND_VISUAL_REPORT.md) | critérios WCAG verificados e não verificados, responsividade, capturas antes × depois | ACCESSIBILITY_REPORT, VISUAL_REGRESSION |
| [REGRESSION_REPORT.md](REGRESSION_REPORT.md) | suíte completa, falhas conhecidas, testes atualizados e por quê, preservação | REGRESSION_REPORT, PRESERVATION_REPORT |
| este README | resumo, como iniciar e testar, limitações, próximos marcos | README, NEXT_UX_MILESTONES |

Dados brutos: `ui_checks.json` (113 verificações), `preservation_before.json`,
`preservation_since.json`, `regression.txt`, `screenshots/before/`, `screenshots/after/`.

## Como iniciar o painel

```bash
# painel normal (lê .env, como antes)
.venv/Scripts/python.exe -B dashboard/server.py 8090
# painel sem chave Gemini (usado nas verificações de interface)
.venv/Scripts/python.exe -B scripts/serve_dashboard_keyless.py 8097
```

Abrir `http://127.0.0.1:8090/`. O servidor só escuta em `127.0.0.1`.

## Como testar

```bash
# servidor, rotas, glossário, contraste, V1 encerrado (+ navegador, se houver Node e Chrome)
.venv/Scripts/python.exe -m pytest tests/test_ui_v762.py -q
# só as verificações estáticas e de servidor
HFL_SKIP_BROWSER=1 .venv/Scripts/python.exe -m pytest tests/test_ui_v762.py -q
# verificações de navegador contra um servidor já aberto (sem chave)
node scripts/ui_check_v762.mjs checks http://127.0.0.1:8097 out.json
# verificações + capturas
node scripts/ui_check_v762.mjs checks http://127.0.0.1:8097 out.json pasta-de-capturas
```

As verificações de navegador usam o Chrome instalado em modo headless pelo
DevTools Protocol (Node 24, sem dependências), enviam apenas GET e falham se
houver qualquer requisição a provedor de IA ou erro de console.

## Limitações

- Refatoração parcial: o miolo das páginas continua legado (lista por página em
  FRONTEND_ARCHITECTURE §5).
- O componente padrão de **confirmação de custo** do blueprint não foi
  implementado; os diálogos pagos atuais (Radar e agentes H2) seguem como estavam.
- A desativação do V1 é **somente da interface**. O backend ainda aceita
  `POST /api/platform/global-prepare` e `global-run`; bloqueá-lo exige aprovação
  específica (V1_PAID_ACTION_AUDIT §5).
- "Mercado" tem só o Radar; a página de ativos e indicadores é do UX-M4.
  "Auditoria" aponta para uma seção do Início até o UX-M7.
- Acessibilidade verificada por automação e inspeção do DOM; sem leitor de tela
  real, sem zoom de 200 %.
- As capturas estão em JPEG; `logs-desktop` foi reduzida (ACCESSIBILITY_AND_VISUAL_REPORT §4).
- Aplicação da ajuda "?" ainda é inicial: Início, shell e trechos de cada área.

## Próximos marcos de UX

| Marco | O que falta | Depende de |
|---|---|---|
| UX-M2 (restante) | componente de confirmação de custo; tabela padrão adotada nas páginas | migração dos fluxos pagos |
| UX-M4 | Radar com componentes `ds-*`; página de ativos e indicadores; ajuda em RSI, MACD, Bollinger, consenso, confiança técnica | — |
| UX-M5 | Carteira e Gestor Global com componentes novos; decidir bloqueio V1 no backend | **decisão humana** sobre o backend |
| UX-M6 | Operação diária, H2, legado; páginas de evidências e metodologia em Pesquisa | — |
| UX-M7 | página própria de Auditoria; Logs no padrão; ajuda em hash, claim, journal, replay | — |
| UX-M8 | leitor de tela, zoom 200 %, alvos medidos, regressão visual comparativa | M4–M7 |
