# Acessibilidade, responsividade e regressão visual

Consolida os entregáveis `ACCESSIBILITY_REPORT` e `VISUAL_REGRESSION`.
Escopo: o shell, o Início e os componentes novos, aplicados nas 7 páginas. A
página legada (`/legacy`) e o miolo das páginas não migradas foram verificados só
quanto a navegação, sobreposição horizontal e foco; não foram auditados por completo.

Evidência automática: `ui_checks.json`, **113/113 verificações aprovadas** no
Chrome headless (DevTools Protocol), servidor sem chave Gemini, apenas
requisições GET observadas.

## 1. WCAG 2.2 AA: o que foi verificado

| Critério | Como | Resultado |
|---|---|---|
| 1.4.3 Contraste de texto | `test_tokens_meet_contrast`: texto, texto secundário, texto discreto, link e as 7 cores de estado contra as 4 superfícies | todas ≥ 4,5:1 (menores: estado de erro 5,58:1 e texto discreto 5,65:1, na superfície mais clara) |
| 1.4.11 Contraste não textual | borda de controle `--border-control #6a8199` contra as 4 superfícies; borda computada conferida no navegador | ≥ 3:1 (menor 3,21:1); aprovado em radar, portfolio, paper |
| 1.4.1 Uso de cor | selos de estado têm ícone + texto + código original; ação paga tem "¤" + rótulo | aprovado por inspeção e pelo teste "states:home_shows_real_v1_v2" |
| 1.4.10 Reflow | sem rolagem horizontal da página em 1440, 1280, 768 e 390 px, nas 7 páginas | 28/28 aprovados |
| 2.1.1 Teclado | skip link é o primeiro foco; navegação principal alcançável; ajuda abre com Enter; menu móvel fecha com Esc | aprovado |
| 2.1.2 Sem armadilha de teclado | popover não modal; Esc fecha e devolve o foco ao "?" | aprovado |
| 2.4.1 Pular blocos | "Ir para o conteúdo" | aprovado |
| 2.4.2 Título da página | "Página · Área · Hedge-Fund-Lab", sem versão | aprovado (7 páginas) |
| 2.4.7 / 2.4.11 Foco visível e não encoberto | contorno sólido de 3 px em `--focus` | aprovado no shell; nas páginas legadas verificado por amostragem |
| 2.4.8 Localização | breadcrumb e `aria-current` (área e seção) | aprovado em 7 páginas + 6 rotas por hash |
| 2.5.8 Tamanho do alvo | `--target-min` 40 px no desktop, 44 px no celular; botão de fechar a ajuda 32 px com espaçamento | por CSS; não medido elemento a elemento |
| 3.2.3 Navegação consistente | um único menu nas 18 rotas (teste de servidor) | aprovado |
| 4.1.2 Nome, função, valor | botões de ajuda com `aria-label` "Ajuda: termo", `aria-expanded`, `aria-controls`; popover `role="dialog"` com título; regiões de tabela roláveis focáveis com rótulo | aprovado |
| 2.3.3 / preferência | `prefers-reduced-motion` desliga transições | por CSS |

## 2. O que não foi verificado (limitações honestas)

- Leitor de tela real (NVDA, VoiceOver): não testado. A semântica foi conferida pelo
  DOM, não pela fala.
- Zoom de 200 % e espaçamento de texto (1.4.4, 1.4.12): não testados.
- Gráficos (Chart.js) do legado e do H2: sem alternativa textual nova; continuam
  como antes.
- Tabelas largas do H2, do Paper e do legado rolam dentro do próprio contêiner no
  celular; a página não rola na horizontal, mas a leitura da tabela continua
  difícil em 390 px.
- Contraste das cores próprias das páginas não migradas (que não usam os tokens):
  não auditado elemento a elemento.
- Modo claro: não existe; o tema escuro continua o único.

## 3. Responsividade

| Largura | Comportamento |
|---|---|
| 1440 / 1280 | menu horizontal, barra de seções, breadcrumb, faixa de ambiente |
| ≤ 900 | botão "Menu" (`aria-expanded`), áreas em lista; aviso "sem ordens reais" continua visível |
| ≤ 640 | cartões em uma coluna, KPIs em duas, alvos de 44 px, popover ajustado à tela (teste "help:touch_opens_within_viewport": 12–378 px em 390 px) |

## 4. Capturas antes × depois

`screenshots/before/` (estado do commit anterior à V7.6.2) e `screenshots/after/`,
desktop 1440 px e celular 390 px, página inteira (até 6000 px).

| Página | Antes | Depois |
|---|---|---|
| Início | `home-*` | `home-*` |
| Radar | `radar-*` | `radar-*` |
| Carteira multiativos | `portfolio-*` | `portfolio-*` |
| Operação diária | `paper-*` | `paper-*` |
| Experimento H2 | `h2-*` | `h2-*` |
| Logs | `logs-*` | `logs-*` |
| Backtests legados | `legacy-*` | `legacy-*` |
| Ajuda aberta (desktop e celular) | — | `after-help-open-desktop`, `after-help-open-phone` |
| Central de ajuda com busca | — | `after-help-center-desktop` |
| Menu móvel aberto | — | `after-mobile-menu-phone` |
| Histórico V1 rejeitado consultável | — | `after-portfolio-v1-history-desktop` |

Observações sobre as capturas:

- Foram convertidas de PNG para JPEG (qualidade 82) pelo próprio Chrome, porque o
  projeto não tem Pillow; o pacote ficou com cerca de 8 MB.
- `logs-desktop.jpg` (antes e depois) foi **reduzido** para 1440 × 2000 px: a
  página de logs é muito longa e a tentativa de recortar acabou reescalando a
  imagem inteira; os originais não foram guardados. As demais estão em tamanho real.
- `home-desktop` e `home-phone` "antes" foram capturadas 1,8 s após o carregamento
  e mostram "Conferindo registros…"; as "depois" esperaram os dados.
- Os dados exibidos são os do repositório no momento da captura (Radar
  `radar-2026-10-09-recovery-01`, registros V1/V2 selados); nenhuma ação foi
  executada para gerá-las.
