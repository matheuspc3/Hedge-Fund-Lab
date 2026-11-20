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
