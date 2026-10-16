# Regressão visual

Capturas PNG reais, geradas pelo Chrome headless, sem composição, geração de
imagem ou substituição de dados. Originais V7.6.1/V7.6.2 não foram sobrescritos.

| Visão | Captura |
|---|---|
| Radar antes, desktop/mobile | `screenshots/before/radar-desktop.png`, `radar-phone.png` |
| Mercado | `screenshots/completed/market-desktop.png` |
| Radar reorganizado | `screenshots/completed/radar-desktop.png` |
| PETR4 com indicadores | `screenshots/completed/petr4-detail.png` |
| BBAS3 com veto | `screenshots/completed/bbas3-detail.png` |
| Comitê expandido | `screenshots/completed/committee-expanded.png` |
| Ajuda aberta | `screenshots/completed/contextual-help.png` |
| Filtro sem resultados | `screenshots/completed/empty-state.png` |
| Mobile | `screenshots/completed/radar-mobile.png` |

Desktop: 1440×900, celular: 390×844; página inteira até 6000 CSS px. Comitê e
ajuda usam viewport, preservando o contexto da interação. As demais capturas
retornam ao topo antes de capturar a página inteira, evitando artefatos de
posicionamento fixo do skip link fora do viewport. Não há imagem “Mercado antes”:
a página não existia; a entrada antiga abria `/legacy`.

Inspeção: uma navegação, quatro conceitos de decisão distintos, cartões coerentes,
detalhes recolhidos, indicadores com unidade, BBAS3 explicitamente vetado, tabela
rolando somente em sua região e ações operacionais separadas. Não há comparação
automática pixel a pixel ou validação por usuários nesta entrega. Capturas
intermediárias das tentativas foram descartadas como redundantes; relatórios
brutos dessas tentativas permanecem preservados.
