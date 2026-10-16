# Auditoria integral de UX/UI

## 1. Método e limites

- **Inventário automatizado** (`python -B scripts/review_v761.py ux` →
  [ux_inventory.json](ux_inventory.json)). Lê as rotas e o menu (`SHELL_LINKS`)
  direto de `dashboard/server.py`, sem importá-lo. Para cada página extrai
  títulos, seções, botões (com classificação de intenção), contadores de
  acessibilidade e ajuda, endpoints usados pelo JS e frequência de termos.
- **Leitura manual** do texto visível de todas as páginas e do código de
  navegação (`shell.html`, `shell.js`, scripts de página).
- **Limites:** nenhuma captura de tela nova nesta entrega e nenhum teste com
  usuários. Conteúdo gerado dinamicamente pelo JS foi inventariado só em parte
  (botões e endpoints em strings). Os contrastes foram calculados sobre os
  tokens de cor, não sobre renderização.

## 2. Inventário

7 páginas físicas, 18 rotas, 4 grupos de menu e 17 links secundários.

| Página | Rotas | Título da aba / h1 | Marca de versão exposta | Seções | Botões (leitura · escrita · **paga**) | Navegação própria além do shell | Ajuda contextual |
|---|---|---|---|---|---|---|---|
| `platform.html` | `/` | "Visão Geral" / "Seu laboratório, em uma só visão." | "PREMIUM V7" | `#readiness`, `#wallets`, `#audit` (+ cards de 4 ambientes) | 1 · 0 · 0 | não | 0 |
| `paper.html` | `/paper` | "H2 v6 · Operação Paper Trading" / 5 h1 (uma por vista) | "H2 v6" | `#visao`, `#sala`, `#mercado`, `#carteiras`, `#agentes` (vistas por hash; `#supervisao` é alias de `#sala`) | 5 · 4 · **2** | **sim** (Visão Geral, Sala de Decisão, Mercado, Carteiras, Agentes, Radar de Ativos, Gestor de Carteira) | 0 |
| `radar.html` | `/radar` | "Radar de Ativos · Premium V4" / "Um universo. Cinco perspectivas por ativo." | "PREMIUM V4" | `#run-card`, `#room` ("Sala de Decisão") | 4 · 2 · **1** | **sim** (← Operação PETR4, Operação Paper, Radar de Ativos, Gestor Global, Histórico H2 v6) | 0 |
| `portfolio.html` | `/portfolio` | "Gestor Global · Premium V6" / **3 h1** | "PREMIUM V6", "NOVO EXPERIMENTO V6" | `#global-workflow` (V7), `#ai-proposal` (V6 / tratamento V1), carteira V5 sintética | 8 · 1 · **2** | **sim** (Operação Paper, Radar de Ativos, **Gestor de Carteira**, Histórico H2 v6) | 0 |
| `h2.html` | `/h2` | "H2 v6 · Hedge-Fund Lab" / sem h1 | "H2 v6" | 6 abas + 3 modos (Provisória OA-1, Oficial, Demonstração) | 9 · 0 · 0 | link "Operação Paper Trading →" | 0 |
| `logs.html` | `/logs` | "Hedge-fund-lab · Logs" / "📋 Hedge-fund-lab Logs" | — | — | 1 · 0 · 0 | **sim** ("Dashboard | Logs") | 0 |
| `index.html` | `/legacy` | "Hedge-fund-lab · Dashboard" / "Backtests legados" | — | 2 abas | 2 · 0 · 0 | não | 0 |

Ações pagas (inferência Gemini) encontradas: **5 botões em 3 fluxos**.

- `/paper`: "3. Confirmar e executar agentes", mais o diálogo "Autorizar e
  executar Gemini" (agentes H2).
- `/radar`: "3. Confirmar e executar este lote" (comitês), com uma caixa de
  seleção inline.
- `/portfolio`: "4. Solicitar proposta · confirmar custo", mais o diálogo
  "Confirmar somente esta inferência" (Global PM).

## 3. Diagnóstico

| # | Achado | Evidência | Gravidade |
|---|---|---|---|
| U1 | **Navegação dupla em quase todas as páginas:** o shell da plataforma e o cabeçalho antigo de cada página, com rótulos diferentes para o mesmo destino | `paper`, `radar`, `portfolio`, `logs`, `h2` têm navegação própria; "Radar de Ativos" × "Radar Multiativos"; "Gestor de Carteira" × "Gestor Global" | alta |
| U2 | **Versões como estrutura do produto:** títulos e cabeçalhos expõem "Premium V4", "V6", "V7", "Novo experimento V6", "H2 v6" | `<title>` e faixas de cabeçalho | alta |
| U3 | **Uma página, três gerações:** `/portfolio` empilha o fluxo V7 (Global PM), a "Proposta da IA" V6 (demonstrações A–F do tratamento V1) e a carteira contábil V5 sintética, com três h1 | `portfolio.html` | alta |
| U4 | **Mesmo nome para coisas diferentes:** "Sala de Decisão" (deliberação H2 em `/paper` × detalhe do comitê em `/radar`); "Visão Geral" (página inicial × vista do `/paper` × aba do `/h2`); "Carteiras" (carteiras prospectivas H2 × carteira hipotética multiativos); "Operação" (operação paper H2 × "Operação com confirmação humana") | inventário, `repeated_headings_across_pages` | alta |
| U5 | **Mesmo destino com nomes diferentes:** `/#audit` = "Auditoria Operacional" e "Processos e Auditoria"; `/radar` = "Radar Multiativos", "Continuar no Radar" e "Radar de Ativos" | `same_target_different_labels` | média |
| U6 | **Dois itens de menu para a mesma vista:** "Sala de Decisão" e "Supervisão Humana" abrem `#sala` | `paper.js`: `LEGACY = {…, supervisao: "sala"}` | média |
| U7 | **Grupos que misturam contextos:** "Laboratório" junta o catálogo de agentes do H2 (`/paper#agentes`) com Radar e Gestor Global; "Pesquisa e Auditoria" junta resultados H2, auditoria operacional, logs técnicos e backtests legados; "Operação" contém só a operação paper PETR4 | `SHELL_LINKS` | alta |
| U8 | **Nenhuma ajuda contextual:** 0 atributos `title`, 0 ícones de ajuda, 0 `abbr`. Termos técnicos sem explicação: "preflight" (30 ocorrências), "contexto" (22), "snapshot" (12), "replay" (12), "claim", "journal", "Risk", "OA-1", "fixture" | `ux_inventory.json → terms`, `counts` | **crítica** para iniciantes |
| U9 | **Fluxos pagos com padrões diferentes:** etapas 1-2-3 em `/paper` e `/radar`, 1-2-3-4 em `/portfolio`; "2. Preflight", "2. Verificar preflight", "3. Preflight global"; confirmação por diálogo em dois fluxos e por caixa de seleção inline no Radar; rótulos com negação ("sem Gemini", "sem executar") ao lado de ações pagas | inventário de botões | alta |
| U10 | **Caminho pago da interface aponta para um tratamento fechado:** "4. Solicitar proposta" em `/portfolio` usa `run_global_pm` (Global PM **V1**), que o protocolo V7.6 declara fechado; a V2, tratamento vigente, só aparece em leitura na UI e roda pelo CLI | `dashboard/platform_api.py` (`cli = global_api.cli`); `global_pm_api.py` importa `run_global_pm` | **crítica** (governança) |
| U11 | **Inconsistência visual:** 7 arquivos CSS, 3 paletas de tokens concorrentes (`shell.css`, `paper.css`, `radar.css`), 64 cores hexadecimais distintas, estilos inline em 3 páginas, só tema escuro; `logs` e `legacy` com identidade visual própria (emoji no h1, `style.css` antigo) | CSS | média |
| U12 | **Rótulos datados na navegação principal:** "Prontidão para 13/10" | `SHELL_LINKS["overview"]` | média |
| U13 | **Linguagem de desenvolvedor para o usuário final:** "Execute o pipeline ETL para ver os logs aqui. `python -m src.pipeline.flows`"; "V5 contábil e V6 A–F"; "Validation OA-1 provisória"; "fixture" | `logs.html`, `platform.html`, `portfolio.html` | média |
| U14 | **Contraste de componentes:** bordas `--line` (1,67:1) e `--border2` (2,34:1) abaixo de 3:1 sobre o fundo; falham o WCAG 1.4.11 quando são o único contorno de um campo | cálculo sobre `shell.css` | média |
| U15 | **Hierarquia de títulos:** `/paper` tem 5 h1 (vistas), `/portfolio` 3, `/h2` nenhum | inventário | baixa |

### Pontos fortes a preservar

- Separação explícita "LOCAL · SEM ORDENS REAIS" no shell e avisos de que
  "parecer ou proposta não executa operação".
- Fluxos pagos com etapas e confirmação separada; preflight e consulta
  declarados como sem custo.
- Distinção já implementada na V7.4 entre resposta rejeitada e validada
  (`global-pm.js`).
- Acessibilidade de base: link "Pular para o conteúdo", `lang="pt-BR"`,
  regiões `aria-live` (19), menu responsivo com Escape, tabelas roláveis com
  foco e rótulo.
- Página inicial já classifica os quatro ambientes (Histórico científico,
  Prospectivo real — paper, Consultivo com Gemini, Demonstração sintética).

## 4. Causas principais da confusão

1. **Crescimento por versões:** cada entrega (V4 Radar, V5 carteira, V6 Gestor,
   V7 plataforma) adicionou uma página ou seção com o próprio cabeçalho, e o
   shell V7 foi sobreposto sem remover as navegações antigas (U1, U2, U3).
2. **Organização por origem técnica, e não por tarefa:** o menu reflete de onde
   veio cada funcionalidade (H2, multiativos, legado), não o que o usuário
   quer fazer (analisar, montar carteira, operar, pesquisar, auditar) (U7).
3. **Ausência de um vocabulário controlado:** o mesmo conceito tem vários nomes,
   e o mesmo nome serve a vários conceitos (U4, U5, U9).
4. **Conhecimento implícito:** a interface pressupõe que o usuário conhece
   preflight, snapshot, claim, journal, OA-1 e a diferença entre V1 e V2 (U8, U13).
5. **Segurança comunicada por texto, não por estrutura:** a diferença entre
   consultar, preparar, pagar e simular está em parágrafos, não em componentes
   visualmente distintos (U9, U10).
