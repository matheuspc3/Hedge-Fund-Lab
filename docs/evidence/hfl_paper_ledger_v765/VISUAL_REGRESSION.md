# Capturas e revisão visual

Capturas PNG reais pelo Chrome headless/CDP, sem imagens geradas:

| Arquivo em screenshots/ | Estado |
|---|---|
| official-all-cash.png | V2 consultivo, sem posições/rosca; quatro indicadores compactos |
| synthetic-overview.png | opt-in sintético, patrimônio/caixa/origem e reconciliação |
| synthetic-positions-history.png | duas posições e cinco pontos por sessão |
| synthetic-operations-timeline.png | operações e segunda página de eventos |
| synthetic-session-receivable.png | posição reduzida e recebível na sessão 22/04 |
| h2-separate-line.png | H2 em /paper com seletor próprio |
| synthetic-mobile.png | 390 px, tabelas roláveis, seletores/identidade/gráfico |
| synthetic-reflow-200.png | reflow CSS equivalente a 200% |
| ledger-read-error.png | falha de leitura injetada no transporte; saldo anterior oculto |
| ledger-empty.png | catálogo sintético vazio injetado, sem promoção de fixture |

A revisão visual abriu capturas desktop e mobile e verificou hierarquia, ausência de rosca em caixa puro, ausência de overflow de página, legibilidade da origem sintética, tabelas com rolagem e gráfico com tabela equivalente. As dez capturas são estados reais do frontend; dois cenários de erro/vazio são identificados como mocks de transporte do teste. Não são dados oficiais.

Melhorias após revisão: exposição ganhou lugar nos quatro indicadores principais; texto da curva distingue campos históricos publicados do ledger sintético e campos ausentes H2; aviso do snapshot V2 esclarece a qualificação isolada do novo ledger. Última coleta final substitui somente capturas desta entrega. Capturas anteriores V7.6.2–V7.6.4 permanecem intactas.

Não há comparação pixel a pixel automatizada nem declaração de conformidade WCAG integral. Verificações responsivas/teclado/foco/ajuda são incrementais; contraste/tokens herdam design system existente.
