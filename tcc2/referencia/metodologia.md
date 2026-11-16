# Metodologia

## Tipo de pesquisa

Este trabalho sera desenvolvido como uma pesquisa aplicada, quantitativa e experimental. A proposta e construir um ambiente computacional de backtesting para comparar o desempenho de estrategias de alocacao de portfolio no mercado acionario brasileiro.

A pesquisa e aplicada porque busca avaliar metodos de investimento em um problema pratico de tomada de decisao financeira. E quantitativa porque utiliza dados historicos de precos, retornos e metricas numericas de desempenho. E experimental porque as estrategias serao implementadas, simuladas e comparadas sob condicoes controladas.

## Visao geral do metodo

O trabalho sera conduzido em sete etapas principais:

1. selecao dos ativos;

2. coleta e preparacao dos dados historicos;

3. implementacao dos benchmarks tradicionais;

4. implementacao do modelo classico de alocacao baseado em Markowitz;

5. construcao do ambiente de backtesting;

6. implementacao e treinamento do agente de Reinforcement Learning;

7. comparacao dos resultados por metricas de desempenho, risco, custos e robustez temporal.

## Universo de dados

O universo de analise sera composto por ativos negociados no mercado acionario brasileiro. A selecao dos ativos devera considerar criterios como disponibilidade historica de dados, liquidez e representatividade no mercado. Uma alternativa viavel e selecionar acoes pertencentes ao Ibovespa ou um subconjunto de ativos com historico consistente no periodo analisado.

Os dados utilizados serao series historicas de precos ajustados, preferencialmente precos de fechamento ajustados por dividendos, desdobramentos e outros eventos corporativos. A partir desses precos, serao calculados retornos periodicos, indicadores tecnicos e variaveis de entrada para as estrategias.

## Periodo de analise

O periodo historico devera ser definido conforme a disponibilidade dos dados e a necessidade de separar janelas de treino, validacao e teste. Como o objetivo envolve estrategias quantitativas e Reinforcement Learning, o periodo precisa ser suficientemente longo para permitir treinamento, simulacao fora da amostra e comparacao entre diferentes regimes de mercado.

A divisao temporal deve respeitar a ordem cronologica dos dados. Portanto, os dados mais antigos serao usados para estimacao de parametros ou treinamento, enquanto os dados posteriores serao usados para teste. Essa decisao evita vazamento de informacao futura e torna a avaliacao mais proxima de uma aplicacao real.

## Preparacao dos dados

A preparacao dos dados envolvera:

1. coleta dos precos historicos dos ativos selecionados;

2. organizacao das series temporais em uma mesma frequencia;

3. tratamento de dados ausentes;

4. calculo dos retornos periodicos;

5. calculo de indicadores usados pelas estrategias, como medias moveis e retornos acumulados em janelas passadas;

6. normalizacao ou padronizacao de variaveis, se necessario para o agente de Reinforcement Learning;

7. separacao cronologica entre treino, validacao e teste.

Todas as estrategias deverao usar apenas informacoes disponiveis ate o momento da decisao. Por exemplo, uma decisao tomada no tempo `t` nao podera utilizar retorno, preco ou indicador calculado com dados posteriores a `t`.

## Estrategias comparadas

As estrategias serao divididas em tres grupos: benchmarks simples, estrategias quantitativas baseadas em regras e modelos de alocacao.

## Benchmarks simples

O primeiro benchmark sera o Buy and Hold. Nessa estrategia, a carteira e comprada no inicio do periodo de teste e mantida ate o final, sem rebalanceamentos frequentes. Ela representa uma base minima de comparacao para avaliar se estrategias ativas realmente agregam valor.

O segundo benchmark sera o Equal Weight. Nessa estrategia, o capital e distribuido igualmente entre os ativos selecionados, com rebalanceamentos periodicos. Ela representa uma forma simples de diversificacao e permite comparar metodos mais complexos com uma regra robusta e facilmente reproduzivel.

## Estrategias quantitativas baseadas em regras

A estrategia de Momentum sera implementada com base no desempenho passado dos ativos em uma janela temporal definida. Os ativos com melhor retorno acumulado recente receberao maior peso ou serao selecionados para compor a carteira. A janela de calculo e a frequencia de rebalanceamento deverao ser fixadas antes da avaliacao final.

A estrategia de Moving Average Crossover sera implementada a partir do cruzamento entre uma media movel curta e uma media movel longa. Quando a media curta estiver acima da media longa, o ativo podera receber sinal positivo de alocacao. Quando a media curta estiver abaixo da media longa, o ativo podera ter sua exposicao reduzida ou zerada.

Caso o escopo permita, indicadores como RSI ou regras de Mean Reversion poderao ser usados como estrategias complementares. No entanto, para manter o experimento controlado, o nucleo comparativo principal sera formado por Buy and Hold, Equal Weight, Momentum, Moving Average Crossover, Markowitz/Minimum Variance e Reinforcement Learning.

## Modelo classico de alocacao

O modelo classico de alocacao sera baseado na Teoria Moderna de Portfolio. A estrategia podera ser implementada como uma carteira de Markowitz ou como uma carteira de minima variancia.

Na abordagem de Markowitz, os pesos da carteira serao definidos a partir de estimativas de retorno esperado e matriz de covariancia dos ativos. Na abordagem de minima variancia, o objetivo sera encontrar os pesos que minimizam a variancia total da carteira, independentemente da previsao de retorno esperado. Essa segunda alternativa pode ser mais estavel quando as estimativas de retorno forem muito ruidosas.

As estimativas deverao ser calculadas com janelas historicas moveis ou expansivas, sempre usando apenas dados passados. A carteira sera rebalanceada em uma frequencia definida, como mensal ou trimestral, de acordo com o desenho experimental.

## Ambiente de backtesting

O ambiente de backtesting sera responsavel por simular a execucao das estrategias ao longo do tempo. Todas as estrategias deverao ser avaliadas no mesmo periodo, com a mesma base de ativos, mesma frequencia de rebalanceamento, mesmas regras de custos e mesmas metricas.

O backtest devera incluir:

1. capital inicial fixo;

2. regra de rebalanceamento;

3. calculo da evolucao da carteira;

4. registro das posicoes ao longo do tempo;

5. aplicacao de custos de transacao;

6. calculo de turnover;

7. armazenamento dos retornos periodicos de cada estrategia;

8. geracao de tabelas e graficos comparativos.

A comparacao so sera valida se as estrategias forem submetidas ao mesmo protocolo experimental. Assim, uma estrategia nao podera usar mais informacao, periodo diferente ou custo menor que as demais.

## Custos de transacao

Os custos de transacao serao incorporados ao backtest para aproximar os resultados de uma condicao mais realista. Esses custos poderao ser modelados como um percentual sobre o volume negociado em cada rebalanceamento.

O custo sera aplicado sempre que houver alteracao nos pesos da carteira. Dessa forma, estrategias com maior turnover serao penalizadas de maneira proporcional a sua intensidade de negociacao. Isso e importante porque estrategias ativas podem apresentar bom desempenho bruto, mas perder atratividade apos custos.

## Agente de Reinforcement Learning

O agente de Reinforcement Learning sera implementado para tomar decisoes sequenciais de alocacao de portfolio. O problema sera formulado a partir dos seguintes componentes:

1. ambiente: o mercado simulado pelo backtest;

2. estado: conjunto de informacoes disponiveis no tempo da decisao, como retornos passados, indicadores tecnicos, volatilidade e posicao atual da carteira;

3. acao: decisao de alocacao, compra, venda, manutencao ou ajuste dos pesos dos ativos;

4. recompensa: medida associada ao desempenho da carteira, como retorno liquido, retorno ajustado ao risco ou retorno penalizado por custos e turnover;

5. politica: regra aprendida pelo agente para escolher acoes a partir dos estados observados.

A arquitetura e o algoritmo especifico de Reinforcement Learning deverao ser escolhidos conforme a viabilidade tecnica do projeto. Uma alternativa e usar um algoritmo ja consolidado, como DQN, PPO ou outro metodo disponivel em bibliotecas de aprendizado por reforco. A escolha final devera considerar simplicidade de implementacao, compatibilidade com o ambiente de portfolio e capacidade de reproducao dos resultados.

O agente sera treinado apenas com dados do periodo de treino. Seu desempenho principal sera avaliado em periodo posterior, fora da amostra, para evitar que os resultados reflitam apenas memorizacao do historico.

## Divisao treino, validacao e teste

Os dados serao separados cronologicamente. Uma divisao possivel e:

1. periodo de treino: usado para treinamento do agente de Reinforcement Learning e estimacao inicial de parametros;

2. periodo de validacao: usado para ajuste de hiperparametros e escolha de configuracoes;

3. periodo de teste: usado para comparacao final entre as estrategias.

Se o volume de dados permitir, tambem podera ser utilizado um procedimento walk-forward. Nesse caso, as estrategias sao calibradas em uma janela historica e testadas em uma janela posterior; depois, a janela avanca no tempo e o processo se repete. Esse procedimento permite avaliar se os resultados sao consistentes em diferentes periodos.

## Metricas de avaliacao

As estrategias serao comparadas por um conjunto de metricas de desempenho, risco e operacionalidade:

1. retorno acumulado;

2. retorno medio;

3. volatilidade;

4. Sharpe Ratio;

5. Sortino Ratio;

6. Maximum Drawdown;

7. turnover;

8. custos de transacao;

9. retorno liquido apos custos.

O retorno acumulado indicara o crescimento total da carteira. O Sharpe Ratio avaliara o retorno excedente por unidade de risco total. O Sortino Ratio avaliara o retorno em relacao ao risco de queda. O Maximum Drawdown medira a maior perda acumulada entre pico e vale. O turnover indicara a intensidade de negociacao da estrategia. Os custos de transacao permitirao avaliar a diferenca entre desempenho teorico e desempenho liquido.

## Criterios de comparacao

O agente de Reinforcement Learning sera considerado superior a uma estrategia tradicional apenas se apresentar desempenho melhor de forma consistente em mais de uma dimensao. Nao sera suficiente obter maior retorno acumulado se isso vier acompanhado de drawdown excessivo, turnover muito alto ou desempenho instavel fora da amostra.

A analise final devera considerar:

1. se o agente supera os benchmarks simples;

2. se o agente supera as estrategias baseadas em regras;

3. se o agente supera Markowitz ou Minimum Variance;

4. se a superioridade permanece apos custos;

5. se os resultados sao consistentes em validacao temporal;

6. se a complexidade adicional do Reinforcement Learning se justifica em relacao aos ganhos observados.

## Ferramentas computacionais

A implementacao devera ser realizada em linguagem Python, por ser amplamente utilizada em ciencia de dados, financas quantitativas e aprendizado de maquina. Bibliotecas como pandas, NumPy, matplotlib, scikit-learn, PyTorch, Stable-Baselines3 ou bibliotecas equivalentes poderao ser utilizadas conforme a necessidade do projeto.

O codigo devera ser organizado de forma reproducivel, separando etapas de coleta de dados, preparacao, implementacao das estrategias, backtesting, treinamento do agente e avaliacao dos resultados.

## Resultado esperado da metodologia

Ao final da metodologia, espera-se obter um pipeline experimental capaz de:

1. carregar e preparar dados historicos dos ativos selecionados;

2. executar benchmarks tradicionais;

3. executar uma estrategia baseada em Markowitz ou minima variancia;

4. treinar e testar um agente de Reinforcement Learning;

5. simular todas as estrategias em ambiente de backtesting;

6. calcular metricas comparaveis de desempenho e risco;

7. gerar uma analise empirica que responda a pergunta de pesquisa.

Assim, a metodologia conecta diretamente a pergunta central do TCC ao resultado final esperado: verificar se Reinforcement Learning realmente entrega ganho de desempenho, risco e robustez em relacao a estrategias quantitativas tradicionais e a um benchmark classico de alocacao de portfolio.
