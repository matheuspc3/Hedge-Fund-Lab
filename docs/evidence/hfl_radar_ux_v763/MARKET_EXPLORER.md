# Exploração do mercado

`/market`, `/market/` e `/market.html` são aliases da nova página. GET e HEAD
usam o shell único. A permissão de navegação externa foi ampliada somente para
esses pontos públicos de entrada; os controles de origem/CSRF das APIs não mudaram.

Fluxo: registro de execuções → universo da execução → resumo do ativo → detalhe
→ Radar com o mesmo `run` e `asset`. Selecionar um ativo e voltar pelo histórico
do navegador são consultas. Não há inclusão automática de ativos ou preparo.

Fontes: `GET /api/platform/radar-runs`, `radar-view?run=…` e
`radar-detail?run=…&ticker=…&session=…`. O universo e a sessão vêm de `run`,
não da lista de exemplos do frontend. Uma execução desconhecida gera erro,
sem substituir seus dados pelos da recovery-01. Falta de parecer gera estado
indisponível; um resultado parcial não recebe decisão final.

A cobertura oficial atual contém PETR4, VALE3, ITUB4, WEGE3 e BBAS3. Não há
nomes de empresas na fonte consumida: exibimos tickers, sem inventar nomes,
fundamentos ou cotações. A renderização percorre o universo retornado, permitindo
ampliação futura sem lista fixa nos componentes.

Fonte dos dados oficiais: OHLCV B3 COTAHIST e fatores de ajuste yfinance
congelados. A sessão de mercado, o horário de geração e a data da consulta são
conceitos separados. Todas as telas novas identificam a consulta como histórica.

A API não fornece uma série temporal de preços nesse contrato. O detalhe informa
a ausência de série, mostra a fotografia numérica e visualiza votos com `meter`
nativo. Os gráficos históricos Chart.js de `/legacy` são preservados no ambiente
de Pesquisa; não foram apresentados como cotações atuais.
