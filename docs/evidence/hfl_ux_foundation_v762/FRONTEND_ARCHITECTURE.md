# Arquitetura do frontend, design system e ajuda contextual

Consolida os entregáveis `FRONTEND_ARCHITECTURE`, `DESIGN_SYSTEM` e
`CONTEXTUAL_HELP`, que descrevem a mesma camada compartilhada.

## 1. Stack real (inspecionada, mantida)

| Camada | Tecnologia | Observação |
|---|---|---|
| Servidor | `dashboard/server.py` (`http.server` da biblioteca padrão) | serve páginas estáticas e APIs `/api/*`; só origem local |
| Páginas | 7 arquivos HTML (`platform`, `radar`, `portfolio`, `paper`, `h2`, `logs`, `index`) | sem templates; o servidor só substitui `<!-- platform-shell -->` |
| Script | JavaScript puro por página (`platform.js`, `radar.js`, `global-workflow.js`, `global-pm.js`, `portfolio.js`, `paper.js`, `h2.js`, `app.js`) | sem build, sem framework |
| Estilo | CSS por página (`radar.css`, `platform.css`, `portfolio.css`, `global-pm.css`, `paper.css`, `style.css`, inline em `h2`/`logs`) | sem pré-processador |
| Gráficos | Chart.js em `dashboard/vendor/` | já existente |
| Testes de UI | Node com DOM simulado (`test_global_pm_v2::test_20`, `test_platform_ui`) | ampliados com Chrome headless via DevTools, sem dependência nova |

Nenhum framework foi introduzido. A fundação nova são três arquivos estáticos
e o shell já existente.

## 2. Como as peças se encaixam

```text
GET /radar?run=…  →  server.py lê radar.html
                     substitui <!-- platform-shell --> por shell.html preenchido
                     com AREAS (6 áreas, seções, faixa de ambiente, breadcrumb)
página carregada  →  <head>: CSS da página, shell.css, scripts da página (defer)
                     <body>: link design-system.css (depois do CSS da página:
                     seus tokens prevalecem), glossary.js e ui.js (defer)
shell.js          →  marca área e seção pelo caminho + hash, ajusta breadcrumb e
                     faixa de ambiente, leva ?run= entre Radar e Carteira, menu móvel
ui.js             →  ativa [data-help], [data-ds-state] e .ds-copy, inclusive no
                     conteúdo que os scripts de página inserem depois (MutationObserver)
```

| Arquivo | Papel | Novo/alterado |
|---|---|---|
| `dashboard/design-system.css` | tokens + componentes `ds-*` + naturezas de ação + estados | novo |
| `dashboard/glossary.js` | catálogo único de termos (`window.HFL_GLOSSARY`) | novo |
| `dashboard/ui.js` | ajuda contextual, central de ajuda, selos de estado, copiar | novo |
| `dashboard/shell.html` | cabeçalho único, áreas, seções, breadcrumb, Ajuda | alterado |
| `dashboard/shell.css` | layout do shell sobre tokens; adaptação das páginas legadas | alterado |
| `dashboard/shell.js` | área ativa, breadcrumb, `?run=`, menu móvel | alterado |
| `dashboard/server.py` | `AREAS`/`PAGE_AREA` no lugar de `SHELL_LINKS`; três estáticos permitidos | alterado |

## 3. Design system (UX-M2)

### 3.1 Tokens (`:root` em `design-system.css`)

| Categoria | Tokens |
|---|---|
| Superfícies | `--bg`, `--surface`, `--surface-2`, `--surface-3`, `--shell-bg` |
| Texto | `--text`, `--text-2`, `--muted` |
| Linhas | `--line` (decorativa), `--border-control` (contorno de controles, ≥ 3:1) |
| Marca e interação | `--accent`, `--link`, `--focus`, `--focus-ring` |
| Estados | `--state-ok`, `--state-warn`, `--state-error`, `--state-info`, `--state-neutral`, `--state-synthetic`, `--state-paid` |
| Tipografia | `--font-sans`, `--font-mono`, `--fs-xs` … `--fs-2xl`, `--lh-body`, `--lh-tight` |
| Espaçamento | `--sp-1` … `--sp-8` (4, 8, 12, 16, 24, 32, 48, 64 px) |
| Forma e profundidade | `--radius-sm/md/lg`, `--shadow-1`, `--shadow-pop` |
| Layout | `--page-max` (1320 px), `--text-max` (72ch), `--target-min` (40 px) |
| Camadas | `--z-header`, `--z-popover`, `--z-dialog`, `--z-skip` |
| Breakpoints (documentados) | celular ≤ 640, tablet ≤ 1024, notebook ≤ 1366, desktop > 1366 |
| Aliases legados | `--page`, `--surface2`, `--surface3`, `--secondary`, `--border`, `--border2`, `--grid`, `--axis`, `--blue`, `--amber`, `--sans` apontam para os tokens; as páginas antigas herdam a paleta e o contorno de 3:1 sem reescrita |

Contraste verificado por teste (`tests/test_ui_v762.py::test_tokens_meet_contrast`):

| Par | Mínimo exigido | Pior caso medido |
|---|---|---|
| `--border-control` sobre qualquer superfície | 3:1 | 3,21:1 (sobre `--surface-3`) |
| textos e cores de estado sobre qualquer superfície | 4,5:1 | 5,58:1 (`--state-error` sobre `--surface-3`) |

### 3.2 Componentes

| Componente | Classe/atributo | Uso nesta entrega |
|---|---|---|
| Títulos | `.ds-eyebrow`, `.ds-title`, `.ds-subtitle`, `.ds-section-title`, `.ds-lead` | Início, Carteira, H2 |
| Layout | `.ds-section`, `.ds-section-head`, `.ds-grid`, `.ds-grid--2/--3` | Início |
| Card | `.ds-card`, `.ds-card--link`, `.ds-card-icon`, `.ds-card-cta` | tarefas e comparações do Início |
| Botão por natureza | `button[data-action=read|prepare|verify|paid|simulate|history]` | Início, Radar, Operação diária, Carteira, Logs |
| Selo de estado | `<span data-ds-state="CODE">` → `.ds-state` | Início, Carteira, H2, aviso V1 |
| Alerta | `.ds-alert`, `--warn`, `--error`, `--closed` | Início, aviso V1 |
| Vazio / carregando | `.ds-empty`, `.ds-loading` | Início |
| Métricas | `.ds-kpis`, `.ds-kpi` | Estado do laboratório |
| Fluxo | `.ds-flow` (com `.is-gate`) | Como funciona |
| Tabela | `.ds-table-wrap`, `.ds-table` (cabeçalho fixo, números à direita) | disponível; páginas legadas migram no UX-M4+ |
| Hash/identificador | `.ds-hash` + `button.ds-copy[data-copy]` | disponível |
| Ajuda | `button.ds-help[data-help]`, `.ds-popover` | todas as áreas tocadas |
| Diálogo | `dialog.ds-dialog` | central de ajuda |
| Abas locais | `[role=tablist]`, `[role=tab]` | H2 (estilo unificado) |

### 3.3 Naturezas de ação

| `data-action` | Significado | Visual (além do texto) |
|---|---|---|
| `read` | consulta; não cria registro nem chama provedor | contorno, texto azul, ícone ◎ |
| `prepare` | grava registro/fotografia local; sem custo | fundo neutro, ícone ✎ |
| `verify` | verificação de requisitos (preflight) | contorno informativo, ícone ☑ |
| `paid` | pode consumir orçamento de IA; sempre confirma | **borda dupla âmbar**, fundo âmbar, ícone ¤ |
| `simulate` | contas hipotéticas, sem ordem | contorno tracejado violeta, ícone ≈ |
| `history` | recuperação ou registro histórico | texto secundário, ícone ⧗ |

O Radar troca a natureza do botão de execução conforme o modo (`paid`,
`simulate` para exemplo sintético, `read` para recuperação offline). Nenhuma
ação nova foi criada; só a apresentação mudou.

### 3.4 Estados semânticos

| Código (dados) | Texto | Ícone | Tom |
|---|---|---|---|
| `PREPARED` | Preparado | ◐ | info |
| `BLOCKED` | Bloqueado | ⊘ | aviso |
| `RUNNING` | Em execução | ⟳ | info |
| `COMPLETED` | Concluído | ● | neutro |
| `VALID_PROPOSAL` | Proposta validada | ✓ | ok |
| `REJECTED_BY_VALIDATOR` | Rejeitada pelo validador | ✕ | erro (borda dupla) |
| `EXPIRED` | Validade expirada | ⌛ | neutro |
| `READ_ONLY` | Somente leitura | ▣ | neutro |
| `SYNTHETIC` / `SYNTHETIC_DEMO` | Demonstração sintética | ≈ | sintético (tracejado) |
| `OFFICIAL` | Oficial | ◆ | info |
| `CONSULTATIVE_SANDBOX` | Consultivo · sem ordens | ⓘ | neutro |
| `CLOSED` | Tratamento encerrado | ⊝ | neutro |
| também | `INCIDENT_PRESERVED`, `RECOVERY_REQUIRED`, `FAILED`, `UNAVAILABLE` | | |

O selo mostra o código original em `<code>` (ex.: `VALID_PROPOSAL`) ao lado do
texto em português; nenhum dado é renomeado. `VALID_PROPOSAL` usa o tom "ok",
nunca um estilo de "ordem autorizada", e a ajuda associada diz que não é
garantia de lucro nem autorização para negociar.

## 4. Ajuda contextual

### 4.1 Uso

```html
<button class="ds-help" data-help="confianca-tecnica"></button>
```

`ui.js` preenche o texto "?", o nome acessível "Ajuda: <termo>" e
`aria-expanded`. Um id inexistente desabilita o botão e é acusado pelo teste.

### 4.2 Comportamento

| Requisito | Implementação |
|---|---|
| Abrir | clique, toque, Enter ou Espaço (botão nativo) |
| Fechar | Esc, botão × ou clique fora; Esc e × devolvem o foco ao "?" |
| Foco | ao abrir, o foco vai para o painel (`role="dialog"`, `aria-modal="false"`, `tabindex=-1`) |
| Não some sozinho | sem hover; o painel fica aberto até ser fechado (teste "stays_open_while_reading") |
| Telas pequenas | posicionado e limitado ao viewport (12 px de margem); abre acima se faltar espaço; largura `min(380px, 100vw − 24px)`; rolagem interna |
| Conteúdo | termo, definição simples, "Saiba mais" (explicação técnica e exemplo), "Cuidado" (ressalva), referência ao código do laboratório, link para o glossário completo |
| `title` | não usado |

### 4.3 Central de ajuda e glossário

- Botão "Ajuda" no shell abre `dialog.ds-dialog` com todos os termos em ordem
  alfabética e busca.
- `dashboard/glossary.js` é a **única** fonte: 36 termos com ids estáveis
  (`rsi`, `macd`, `bollinger`, `volatilidade`, `drawdown`, `sharpe`, `correlacao`,
  `consenso`, `confianca-tecnica`, `risk`, `veto`, `caixa-disponivel`,
  `caixa-reservado`, `recebivel`, `d-mais-2`, `peso-alvo`, `exposicao`,
  `preflight`, `snapshot`, `hash`, `claim`, `journal`, `replay`,
  `inferencia-paga`, `proposta-validada`, `proposta-rejeitada`,
  `paper-trading`, `backtesting`, mais `sem-ordens-reais`,
  `demonstracao-sintetica`, `consultivo`, `oficial`, `tratamento`,
  `tratamento-encerrado`, `radar`, `gestor-global`).
- Conteúdo derivado de `docs/evidence/hfl_methodology_ux_review_v761/CONTEXTUAL_HELP_GLOSSARY.md`,
  com a referência ao código real em cada termo específico do laboratório.
- Testes: ids únicos; os 28 termos exigidos existem; todo `data-help` usado
  em HTML/JS existe; nenhuma definição é copiada para as páginas.

### 4.4 Onde já aparece (adoção inicial)

Shell (sem ordens reais); Início (11 no HTML: garantias, fluxo, operação paper,
claim, journal; mais 4 nas métricas de estado); Radar (Radar); Carteira (Gestor Global, tratamento encerrado,
fotografia, recuperação, demonstração sintética); Operação diária (paper
trading); Backtests legados (backtesting); Estado do laboratório (por métrica).
A aplicação nas demais telas está registrada no roadmap (UX-M4 a UX-M7).

## 5. Componentes legados ainda em uso

| Página | O que ainda é legado | Marco |
|---|---|---|
| `/radar` | cartões, tabelas e métricas de `radar.css` (já com tokens unificados) | UX-M4 |
| `/portfolio` | seções V6 (`global-pm.css`) e V5 (`portfolio.css`); diálogo de confirmação antigo (fluxo desativado) | UX-M5 |
| `/paper` | componentes de `paper.css` (cartões, tabelas, diálogos de confirmação paga e de supervisão) | UX-M6 |
| `/h2` | estilos inline da página (cartões, gráficos, tabelas) | UX-M6 |
| `/legacy` | `style.css` próprio (largura, tipografia monoespaçada, abas) | UX-M6 |
| `/logs` | estilos inline próprios (paleta estilo GitHub) | UX-M7 |
| `/` | painéis operacionais "atenção necessária", carteiras e auditoria (`platform.css`) | UX-M7 |

O padrão de confirmação de custo descrito no blueprint V7.6.1 **não** foi
implementado como componente nesta entrega: os fluxos pagos (Radar e agentes H2)
mantêm seus diálogos atuais, já com preflight e consentimento. Ele entra quando
esses fluxos forem migrados (UX-M4, UX-M6).

## 6. Como migrar uma página (próximos marcos)

1. Remover estilos locais que dupliquem tokens; usar `var(--…)`.
2. Trocar cartões e tabelas por `.ds-card` e `.ds-table-wrap`/`.ds-table`.
3. Marcar cada botão com `data-action` conforme a natureza real.
4. Exibir estados com `data-ds-state` (código original preservado).
5. Inserir `data-help` no primeiro uso visível de cada termo do glossário.
6. Rodar `node scripts/ui_check_v762.mjs checks …` e `pytest tests/test_ui_v762.py`.
