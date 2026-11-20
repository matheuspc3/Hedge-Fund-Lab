# Problema e Objetivos

## Tema delimitado

Este trabalho investiga a comparacao entre estrategias quantitativas tradicionais, um modelo classico de otimizacao de carteiras baseado em Markowitz e um agente de Reinforcement Learning para alocacao de portfolio no mercado acionario brasileiro.

O foco nao e prever o preco futuro de uma acao isolada, nem construir um sistema generico de inteligencia artificial para investimentos. O foco e avaliar, em um ambiente de backtesting, se um agente de Reinforcement Learning consegue tomar decisoes de alocacao que sejam competitivas em relacao a estrategias tradicionais e benchmarks classicos, considerando retorno, risco, custos e robustez temporal.

## Problema de pesquisa

Estrategias baseadas em Reinforcement Learning tem sido aplicadas a problemas financeiros por sua capacidade de aprender decisoes sequenciais em ambientes dinamicos. No entanto, em problemas de alocacao de portfolio, modelos mais complexos nem sempre produzem desempenho superior a estrategias simples ou a modelos classicos, especialmente quando sao considerados custos de transacao, risco de overfitting, drawdowns e avaliacao fora da amostra.

No mercado acionario brasileiro, esse problema se torna ainda mais relevante porque a avaliacao de estrategias precisa lidar com caracteristicas praticas como volatilidade, mudancas de regime, liquidez, custos operacionais e sensibilidade dos resultados ao periodo historico escolhido. Assim, nao basta verificar se um agente de Reinforcement Learning gera maior retorno acumulado; e necessario avaliar se ele melhora a relacao risco-retorno de forma robusta quando comparado a benchmarks tradicionais.

## Pergunta de pesquisa

Agentes de Reinforcement Learning conseguem superar estrategias quantitativas tradicionais e modelos classicos de alocacao de portfolio, como Markowitz, em termos de retorno ajustado ao risco no mercado acionario brasileiro?

## Perguntas secundarias

1. O agente de Reinforcement Learning apresenta desempenho superior a benchmarks simples, como Buy and Hold e Equal Weight?

2. O agente de Reinforcement Learning apresenta desempenho superior a estrategias quantitativas baseadas em regras, como Momentum e Moving Average Crossover?

3. O agente de Reinforcement Learning apresenta desempenho superior a uma estrategia classica de otimizacao de carteiras, como Markowitz ou Minimum Variance?

4. O desempenho do agente permanece competitivo apos considerar custos de transacao e turnover?

5. Os resultados sao robustos em validacao temporal ou dependem excessivamente de um periodo especifico de mercado?

## Hipotese de trabalho

A hipotese inicial e que o agente de Reinforcement Learning pode apresentar desempenho competitivo em relacao a estrategias tradicionais, por aprender decisoes sequenciais de alocacao a partir do estado do mercado. Entretanto, espera-se que sua superioridade nao seja garantida em todos os cenarios, principalmente quando forem considerados custos de transacao, drawdown, turnover e validacao fora da amostra.

Essa hipotese e importante porque evita partir da premissa de que o metodo mais complexo sera automaticamente melhor. O trabalho deve testar se a complexidade adicional do Reinforcement Learning se justifica empiricamente.

## Objetivo geral

Avaliar se agentes de Reinforcement Learning conseguem superar estrategias quantitativas tradicionais e modelos classicos de alocacao de portfolio no mercado acionario brasileiro, considerando metricas de retorno ajustado ao risco, retorno acumulado, Maximum Drawdown, Sortino Ratio, Sharpe Ratio, turnover, custos de transacao e validacao temporal.

## Objetivos especificos

1. Selecionar um conjunto de ativos do mercado acionario brasileiro para compor o universo de investimento analisado.

2. Coletar e preparar dados historicos de precos dos ativos selecionados, garantindo padronizacao temporal e tratamento adequado dos retornos.

3. Implementar benchmarks simples de investimento, como Buy and Hold e Equal Weight.

4. Implementar estrategias quantitativas tradicionais baseadas em regras, como Momentum e Moving Average Crossover.

5. Implementar uma estrategia classica de otimizacao de portfolio baseada em Markowitz ou em carteira de minima variancia.

6. Construir um ambiente de backtesting que permita comparar todas as estrategias sob as mesmas condicoes de dados, periodo, rebalanceamento e custos.

7. Implementar um agente de Reinforcement Learning para tomada de decisao de alocacao de portfolio.

8. Avaliar o desempenho das estrategias por meio de retorno acumulado, Sharpe Ratio, Sortino Ratio, Maximum Drawdown, turnover e custos de transacao.

9. Realizar validacao temporal, como separacao treino-teste ou walk-forward, para analisar a robustez dos resultados.

10. Comparar criticamente os resultados obtidos, identificando em quais condicoes o agente de Reinforcement Learning agrega valor ou perde atratividade em relacao aos benchmarks.

## Entrega final do trabalho

Ao final do TCC, sera entregue uma avaliacao empirica comparativa entre:

1. Buy and Hold;

2. Equal Weight;

3. Momentum;

4. Moving Average Crossover;

5. Markowitz ou Minimum Variance;

6. Agente de Reinforcement Learning.

Essa avaliacao devera incluir:

1. base de dados historica dos ativos selecionados;

2. ambiente de backtesting reproducivel;

3. implementacao das estrategias comparadas;

4. incorporacao de custos de transacao;

5. calculo das metricas de desempenho e risco;

6. validacao temporal dos resultados;

7. analise comparativa indicando se o agente de Reinforcement Learning supera ou nao os benchmarks tradicionais.

## Delimitacao do escopo

Este trabalho nao pretende desenvolver um sistema de recomendacao financeira para uso real, nem propor uma estrategia definitiva de investimento. Tambem nao pretende avaliar LLMs como consultores financeiros, modelos supervisionados de previsao de preco ou abordagens mais amplas de factor investing.

O escopo fica restrito a comparacao controlada entre estrategias quantitativas tradicionais, Markowitz e Reinforcement Learning em um ambiente historico de backtesting, com foco em metricas de risco-retorno e robustez temporal.

## Frase-guia do TCC

O trabalho busca responder se a complexidade de um agente de Reinforcement Learning se traduz em ganho real de desempenho, risco e robustez quando comparada a estrategias quantitativas tradicionais e a um benchmark classico de alocacao de portfolio no mercado acionario brasileiro.



---

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


---

Eu tomaria essa decisÃ£o assim:

**Sim: deixe Markowitz.**
**Sim: tire LLM.**

Como orientador, eu acharia essa mudanÃ§a melhor porque deixa o TCC mais **coerente, implementÃ¡vel e defensÃ¡vel**. O LLM parece atual, mas abriria muitos problemas metodolÃ³gicos. JÃ¡ Markowitz combina muito bem com sua pergunta porque Ã© um benchmark clÃ¡ssico de alocaÃ§Ã£o e risco-retorno.

---

# DecisÃ£o recomendada para o TCC

Seu TCC deve ficar assim:

> **ComparaÃ§Ã£o entre estratÃ©gias quantitativas tradicionais e agentes de Reinforcement Learning para alocaÃ§Ã£o de portfÃ³lio no mercado acionÃ¡rio brasileiro.**

Ou:

> **Benchmark clÃ¡ssico vs agente de IA: uma avaliaÃ§Ã£o entre estratÃ©gias tradicionais e Reinforcement Learning sob mÃ©tricas de risco-retorno.**

Essa versÃ£o Ã© melhor porque mantÃ©m o foco em **CiÃªncia de Dados**, mas sem virar um trabalho genÃ©rico sobre IA.

---

# O que fica no TCC

## 1. Benchmarks clÃ¡ssicos

VocÃª pode comparar o agente de IA contra:

```txt
Buy and Hold
Equal Weight
Moving Average Crossover
Momentum
Mean Reversion
RSI ou Bollinger Bands
Markowitz / Minimum Variance
```

Eu nÃ£o colocaria todas se o tempo estiver curto. O nÃºcleo mais forte seria:

```txt
Buy and Hold
Equal Weight
Momentum
Moving Average Crossover
Markowitz / Minimum Variance
Agente de Reinforcement Learning
```

Isso jÃ¡ dÃ¡ um TCC robusto.

---

# O que sai

Eu retiraria:

```txt
HipÃ³tese de EficiÃªncia de Mercado
Machine Learning supervisionado
LLM como consultor
Factor Investing, se nÃ£o for usar fatores
Black-Litterman, se quiser simplificar
Risk Parity, se o escopo estiver grande
```

O TCC fica mais limpo.

---

# Por que manter Markowitz?

Markowitz entra muito bem porque seu trabalho fala de **retorno ajustado ao risco**.

Ele permite comparar o agente de IA contra uma estratÃ©gia clÃ¡ssica de alocaÃ§Ã£o de portfÃ³lio. A lÃ³gica Ã©:

> â€œSerÃ¡ que um agente de IA que aprende decisÃµes sequenciais consegue superar uma estratÃ©gia clÃ¡ssica de otimizaÃ§Ã£o de carteira?â€

Essa pergunta Ã© muito mais forte do que comparar sÃ³ contra indicadores tÃ©cnicos.

Markowitz serve como benchmark acadÃªmico.
Buy and Hold e Equal Weight servem como benchmarks simples.
Momentum e mÃ©dias mÃ³veis servem como benchmarks rule-based.
RL serve como agente de IA.

---

# Por que tirar LLM?

Eu tiraria LLM por 5 motivos principais:

1. **Reprodutibilidade fraca**
   O LLM pode responder diferente dependendo do prompt, temperatura, modelo e versÃ£o.

2. **Risco de vazamento de informaÃ§Ã£o**
   Se o LLM tiver conhecimento treinado com dados futuros, fica difÃ­cil garantir que ele sÃ³ usou informaÃ§Ã£o disponÃ­vel no momento da decisÃ£o.

3. **Dificuldade de avaliaÃ§Ã£o justa**
   EstratÃ©gias quantitativas sÃ£o determinÃ­sticas ou treinÃ¡veis. LLM como consultor Ã© mais subjetivo.

4. **Escopo muito grande**
   VocÃª jÃ¡ terÃ¡ backtest, Markowitz, estratÃ©gias clÃ¡ssicas, mÃ©tricas e RL. LLM adicionaria outro TCC dentro do TCC.

5. **Banca pode questionar muito**
   A banca pode perguntar: â€œComo vocÃª garante que o LLM nÃ£o usou informaÃ§Ã£o futura?â€, â€œComo controla o prompt?â€, â€œComo reproduz os resultados?â€, â€œQual foi a funÃ§Ã£o objetiva do LLM?â€

EntÃ£o eu deixaria LLM como **trabalho futuro**, nÃ£o como experimento principal.

---

# Pergunta de pesquisa final

Eu escreveria assim:

> **Agentes de Reinforcement Learning conseguem superar estratÃ©gias quantitativas tradicionais e modelos clÃ¡ssicos de alocaÃ§Ã£o de portfÃ³lio, como Markowitz, em termos de retorno ajustado ao risco no mercado acionÃ¡rio brasileiro?**

Essa pergunta estÃ¡ muito boa porque compara:

```txt
IA moderna: Reinforcement Learning
vs
Benchmarks clÃ¡ssicos: Buy and Hold, Equal Weight, Momentum, MÃ©dias MÃ³veis e Markowitz
```

---

# Objetivo geral

> **Avaliar se agentes de Reinforcement Learning conseguem superar estratÃ©gias quantitativas tradicionais e modelos clÃ¡ssicos de alocaÃ§Ã£o de portfÃ³lio no mercado acionÃ¡rio brasileiro, considerando mÃ©tricas de retorno ajustado ao risco, drawdown, retorno acumulado, turnover e custos de transaÃ§Ã£o.**

---

# Objetivos especÃ­ficos

```txt
- Implementar estratÃ©gias tradicionais de investimento, como Buy and Hold, Equal Weight, Momentum e Moving Average Crossover.

- Implementar uma estratÃ©gia baseada na Teoria Moderna de PortfÃ³lio, utilizando o modelo de Markowitz ou Minimum Variance.

- Construir um ambiente de backtesting com dados histÃ³ricos de ativos brasileiros.

- Implementar um agente de Reinforcement Learning para tomada de decisÃ£o de alocaÃ§Ã£o ou compra/venda.

- Comparar as estratÃ©gias utilizando Sharpe Ratio, Sortino Ratio, mÃ¡ximo drawdown, retorno acumulado, turnover e custos de transaÃ§Ã£o.

- Avaliar a robustez dos resultados por meio de validaÃ§Ã£o temporal ou walk-forward.
```

---

# Estrutura nova da FundamentaÃ§Ã£o TeÃ³rica

Eu deixaria assim:

```txt
2 FundamentaÃ§Ã£o TeÃ³rica

2.1 EstratÃ©gias quantitativas tradicionais

2.2 EstratÃ©gias baseadas em regras
    2.2.1 Buy and Hold
    2.2.2 Equal Weight
    2.2.3 Moving Average Crossover
    2.2.4 Momentum
    2.2.5 Mean Reversion

2.3 Teoria Moderna de PortfÃ³lio
    2.3.1 Markowitz
    2.3.2 Carteira de mÃ­nima variÃ¢ncia
    2.3.3 RelaÃ§Ã£o risco-retorno

2.4 Backtesting em sÃ©ries financeiras

2.5 MÃ©tricas de desempenho e risco
    2.5.1 Retorno acumulado
    2.5.2 Sharpe Ratio
    2.5.3 Sortino Ratio
    2.5.4 Maximum Drawdown
    2.5.5 Turnover
    2.5.6 Custos de transaÃ§Ã£o

2.6 Reinforcement Learning
    2.6.1 Agente, ambiente, estado, aÃ§Ã£o e recompensa
    2.6.2 Reinforcement Learning aplicado a trading e alocaÃ§Ã£o de portfÃ³lio

2.7 ValidaÃ§Ã£o temporal e anÃ¡lise de robustez
```

Essa estrutura Ã© bem mais defendÃ­vel.

---

# Metodologia recomendada

O fluxo do TCC pode ser:

```txt
1. Selecionar os ativos
2. Coletar preÃ§os histÃ³ricos
3. Calcular retornos e indicadores
4. Definir janelas temporais de treino e teste
5. Implementar benchmarks tradicionais
6. Implementar Markowitz / Minimum Variance
7. Implementar agente de Reinforcement Learning
8. Simular as carteiras no mesmo perÃ­odo
9. Aplicar custos de transaÃ§Ã£o
10. Calcular mÃ©tricas
11. Comparar os resultados
12. Fazer anÃ¡lise de robustez
```

---

# ComparaÃ§Ã£o final dos mÃ©todos

Eu usaria esta tabela mental:

| Grupo                 | EstratÃ©gia                   | FunÃ§Ã£o no TCC                        |
| --------------------- | ---------------------------- | ------------------------------------ |
| Benchmark simples     | Buy and Hold                 | Base mÃ­nima de comparaÃ§Ã£o            |
| Benchmark simples     | Equal Weight                 | Carteira simples e forte             |
| EstratÃ©gia rule-based | Momentum                     | EstratÃ©gia quantitativa clÃ¡ssica     |
| EstratÃ©gia rule-based | MÃ©dia mÃ³vel                  | EstratÃ©gia tÃ©cnica clÃ¡ssica          |
| OtimizaÃ§Ã£o clÃ¡ssica   | Markowitz / Minimum Variance | Benchmark acadÃªmico de risco-retorno |
| Agente de IA          | Reinforcement Learning       | Modelo moderno a ser avaliado        |

---

# Como explicar ao orientador

VocÃª pode falar assim:

> Professor, pensei em retirar o LLM para deixar o escopo mais controlado e metodologicamente defensÃ¡vel. O LLM traria problemas de reprodutibilidade, controle de informaÃ§Ã£o e padronizaÃ§Ã£o do experimento. Em vez disso, pretendo manter o foco na comparaÃ§Ã£o entre estratÃ©gias quantitativas tradicionais, Markowitz como benchmark clÃ¡ssico de alocaÃ§Ã£o e um agente de Reinforcement Learning como abordagem de IA. Assim, o trabalho fica mais centrado em CiÃªncia de Dados, backtesting, validaÃ§Ã£o temporal e mÃ©tricas de risco-retorno.

---

# Se a banca perguntar â€œpor que tirou LLM?â€

Resposta boa:

> O LLM foi retirado por delimitaÃ§Ã£o de escopo. Embora seja uma abordagem atual, sua inclusÃ£o exigiria discutir controle de prompt, reprodutibilidade, estabilidade das respostas e possÃ­vel vazamento de informaÃ§Ã£o. Como o objetivo do trabalho Ã© uma comparaÃ§Ã£o controlada entre estratÃ©gias, optou-se por focar em Reinforcement Learning, que permite definir formalmente estados, aÃ§Ãµes, recompensas e regras de decisÃ£o dentro de um ambiente de backtesting.

---

# Se a banca perguntar â€œpor que Markowitz?â€

Resposta boa:

> Markowitz foi mantido por ser um benchmark clÃ¡ssico de alocaÃ§Ã£o de portfÃ³lio baseado na relaÃ§Ã£o entre risco e retorno. Como o trabalho avalia estratÃ©gias por mÃ©tricas ajustadas ao risco, faz sentido comparar o agente de Reinforcement Learning nÃ£o apenas contra estratÃ©gias simples, mas tambÃ©m contra uma abordagem tradicional de otimizaÃ§Ã£o de carteiras.

---

# Minha decisÃ£o final como orientador

Eu aprovaria este escopo:

```txt
EstratÃ©gias tradicionais:
- Buy and Hold
- Equal Weight
- Momentum
- Moving Average Crossover

OtimizaÃ§Ã£o clÃ¡ssica:
- Markowitz / Minimum Variance

Agente de IA:
- Reinforcement Learning

AvaliaÃ§Ã£o:
- Sharpe
- Sortino
- Max Drawdown
- Retorno acumulado
- Turnover
- Custos de transaÃ§Ã£o
- Walk-forward
```

E deixaria fora:

```txt
- LLM
- Machine Learning supervisionado
- HipÃ³tese de EficiÃªncia de Mercado
- Factor Investing
- Black-Litterman
```

Essa Ã© a versÃ£o mais equilibrada: atual, viÃ¡vel, cientÃ­fica e menos vulnerÃ¡vel a crÃ­ticas.


