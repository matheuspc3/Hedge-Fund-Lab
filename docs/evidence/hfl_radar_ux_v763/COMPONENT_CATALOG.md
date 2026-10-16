# Componentes reutilizados e criados

| Componente | Local | Uso real |
|---|---|---|
| `HFLMarket.summary(row, run, page)` | `market-ui.js` | Cards no Mercado e Radar |
| `HFLMarket.decisions(row)` | `market-ui.js` | Quatro etapas distintas em resumo/detalhe |
| `HFLMarket.detail(row, run, compact)` | `market-ui.js` | Detalhe das duas páginas e comparação de duas empresas |
| `HFLMarket.copy(label, value)` | `market-ui.js` | Markup para o botão de cópia existente |
| `HFL.confirmCost(preflightData)` | `ui.js` | Revisão do botão pago já existente no Radar |
| `ds-table` / `ds-table-wrap` | `design-system.css` | Tabela comparativa do Radar |
| `ds-card`, `ds-kpi`, `ds-flow`, `ds-alert` | design system existente | Ambas as páginas |
| `ds-help`, `ds-copy`, central de ajuda | `ui.js` / `glossary.js` existentes | Indicadores, Risk, consenso, evidências |

Não há dependência, framework ou paleta nova. `market.css` define apenas layout
e composição com os tokens V7.6.2. A tabela usa caption, cabeçalhos de coluna/linha
e região rolável focável. Dados ausentes ficam indisponíveis; apenas pareceres
`COMPLETED` mostram decisões finais.

`HFLMarket` escapa valores recebidos da API antes de compor HTML. Números são
formatados com `toLocaleString`; valores não finitos/ausentes não viram zero.
O código de leitura nunca grava evidências. Controles operacionais nas demais
páginas ainda precisam adotar os componentes compartilhados (UX-M2/M5–M7).
