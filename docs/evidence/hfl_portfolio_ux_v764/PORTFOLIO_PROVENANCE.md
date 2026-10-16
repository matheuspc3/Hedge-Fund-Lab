# Proveniência e isolamento

`OFFICIAL_HYPOTHETICAL_SNAPSHOT` significa contexto consultivo real, persistido e verificável, com fotografia financeira hipotética. Não significa execução paper multiativos. `H2_PAPER_LEDGER` identifica uma das cinco carteiras H2 existentes. `SYNTHETIC_DEMO` e o livro V5 ficam somente no Simulador.

Nenhuma posição vem de `target_weights`. Posições vêm da fonte financeira selecionada: snapshot hipotético ou carteira H2 persistida. Operações H2 vêm de sessões reconciliadas e mantêm sessão da decisão quando disponível; B&H não recebe a decisão da IA como origem. A inexistência de preço médio ou liquidação H2 não é substituída por números do V5.

Marcas V2 conservam `mode: synthetic`, `basis: RAW`, `source: SYNTHETIC_OFFLINE_NOT_MARKET_DATA`. Seus valores coincidem com referências preparadas, mas a classificação primária permanece visível. Não são cotação em tempo real. Pareceres oficiais do Radar mantêm sua própria origem B3 e fatores ajustados, consultáveis no JSON verificado.

H2: fechamento ajustado do ledger para marcação, preço de execução publicado por operação. A data da marca não é a da consulta. Não usar fechamento anterior como abertura futura. Curvas mostram somente sessões reconciliadas; observações distantes são pontos, sem linha que finja continuidade. Dados ausentes são `null`/Indisponível; zero financeiro explícito permanece zero.

`official_decisions.json` e `h2_observation.json` são relatórios datados desta entrega; a interface lê sempre as APIs, nunca esses relatórios. Evidências primárias continuam em suas raízes originais, com hashes verificados pelos leitores existentes.
