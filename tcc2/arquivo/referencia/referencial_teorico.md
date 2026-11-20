# 2 Referencial Teorico

Este capitulo apresenta os fundamentos teoricos que sustentam a comparacao entre estrategias quantitativas tradicionais, modelos classicos de alocacao de portfolio e agentes de Reinforcement Learning no contexto do mercado acionario brasileiro. A discussao esta organizada a partir das referencias reunidas nas pastas de estrategias quantitativas, Markowitz e benchmarks, metricas de desempenho, backtesting e robustez. O objetivo e estabelecer uma base conceitual para a implementacao e avaliacao empirica das estrategias consideradas no trabalho.

## 2.1 Estrategias quantitativas tradicionais

Estrategias quantitativas de investimento sao metodos sistematicos de tomada de decisao baseados em regras, indicadores, modelos estatisticos ou algoritmos. Diferentemente de uma abordagem discricionaria, na qual a decisao depende principalmente da interpretacao subjetiva do investidor, uma estrategia quantitativa define criterios objetivos para compra, venda, manutencao ou realocacao de ativos. Essa caracteristica torna tais estrategias adequadas para backtesting, pois permite simular historicamente como o metodo teria se comportado sob um conjunto fixo de regras.

No escopo deste trabalho, as estrategias quantitativas tradicionais cumprem o papel de benchmarks intermediarios entre estrategias simples, como Buy and Hold e Equal Weight, e modelos mais sofisticados, como Markowitz e Reinforcement Learning. Elas sao importantes porque representam formas classicas de explorar padroes observados em series financeiras, especialmente tendencias, reversoes e sinais derivados de precos historicos.

Brock, Lakonishok e LeBaron (1992) investigam regras tecnicas simples, incluindo regras baseadas em medias moveis, e mostram que tais procedimentos podem ser avaliados empiricamente por meio de simulacoes historicas. A contribuicao do estudo para este TCC esta em justificar o uso de regras de trading tecnicas como benchmarks quantitativos, ja que elas transformam informacoes passadas de preco em decisoes objetivas de investimento.

Lo, Mamaysky e Wang (2000) tambem contribuem para a fundamentacao da analise tecnica ao tratar padroes graficos e sinais de mercado sob uma perspectiva computacional e estatistica. Em vez de considerar a analise tecnica apenas como pratica informal, os autores mostram que seus padroes podem ser representados, identificados e avaliados de forma sistematica. Essa abordagem reforca a ideia de que estrategias baseadas em sinais tecnicos podem ser incorporadas a um experimento quantitativo reprodutivel.

Kakushadze e Serur (2018), em 151 Trading Strategies, reunem diferentes familias de estrategias sistematicas, incluindo abordagens baseadas em sinais de preco, reversao, tendencia, arbitragem estatistica e construcao de portfolios. Para este TCC, a obra funciona como referencia complementar para contextualizar a diversidade de estrategias quantitativas existentes e reforcar que o experimento deve delimitar um conjunto pequeno e comparavel de metodos, em vez de tentar cobrir todo o universo de estrategias possiveis.

## 2.2 Estrategias baseadas em regras

As estrategias baseadas em regras sao definidas por condicoes explicitas que determinam a composicao da carteira ou o momento de entrada e saida dos ativos. No trabalho, elas sao usadas como alternativas tradicionais ao agente de Reinforcement Learning, permitindo verificar se uma abordagem de aprendizado sequencial realmente agrega valor em relacao a metodos mais simples e interpretaveis.

### 2.2.1 Buy and Hold

Buy and Hold e uma estrategia passiva em que o investidor compra um ativo ou uma carteira de ativos e permanece posicionado durante todo o periodo de avaliacao. Sua importancia metodologica esta na simplicidade: ela representa um benchmark minimo contra o qual estrategias ativas devem ser comparadas. Se uma estrategia mais complexa nao supera Buy and Hold em termos de retorno ajustado ao risco, drawdown ou custos, sua utilidade pratica pode ser questionada.

Em um estudo com ativos brasileiros, Buy and Hold pode ser aplicado a um indice de mercado, a um ativo individual ou a uma carteira inicial fixa. Essa estrategia permite avaliar se os ganhos de modelos ativos decorrem de decisoes efetivamente melhores ou apenas da exposicao geral ao mercado.

### 2.2.2 Equal Weight

Equal Weight, ou carteira igualmente ponderada, consiste em distribuir o capital igualmente entre os ativos selecionados. Embora simples, esse benchmark e relevante porque incorpora diversificacao sem depender de estimativas instaveis de retorno esperado, variancia ou covariancia. Assim, ele funciona como uma base comparativa forte para modelos de otimizacao que exigem maior complexidade estatistica.

No contexto deste TCC, Equal Weight permite verificar se estrategias como Markowitz ou Reinforcement Learning conseguem melhorar o desempenho em relacao a uma regra simples de diversificacao. Essa comparacao e importante porque modelos mais sofisticados podem sofrer com erro de estimacao, excesso de ajuste aos dados historicos e maior turnover.

### 2.2.3 Moving Average Crossover

Moving Average Crossover e uma estrategia tecnica baseada no cruzamento entre medias moveis de diferentes horizontes. Em geral, quando uma media curta cruza acima de uma media longa, interpreta-se que ha um sinal de tendencia positiva; quando cruza abaixo, interpreta-se que ha sinal de enfraquecimento ou reversao da tendencia. A regra traduz a ideia de acompanhamento de tendencia em um criterio operacional claro.

Brock, Lakonishok e LeBaron (1992) sao uma referencia central para esse tipo de abordagem, pois analisam regras de medias moveis e de rompimento em series historicas extensas. A relevancia para o presente trabalho esta no uso dessas regras como benchmark quantitativo classico: elas sao simples, reproduziveis e baseadas apenas em informacoes historicas disponiveis ate o momento da decisao.

Lo, Mamaysky e Wang (2000) complementam essa fundamentacao ao mostrar que padroes de analise tecnica podem ser estudados por metodos quantitativos. Desse modo, o cruzamento de medias moveis pode ser tratado nao apenas como uma heuristica de mercado, mas como uma regra formal sujeita a validacao empirica.

### 2.2.4 Momentum

Momentum e uma estrategia baseada na persistencia de retornos. A ideia central e que ativos com desempenho positivo em uma janela recente tendem a continuar apresentando desempenho superior no curto ou medio prazo, enquanto ativos com desempenho negativo tendem a permanecer relativamente fracos. No TCC, a estrategia de momentum pode ser implementada selecionando ou aumentando o peso dos ativos com maior retorno passado em determinada janela temporal.

Moskowitz, Ooi e Pedersen (2012) documentam a existencia de time-series momentum em diferentes classes de ativos, indicando que o retorno passado de um ativo pode conter informacao relevante sobre seu retorno futuro. Essa referencia sustenta o uso de momentum como benchmark quantitativo tradicional, pois mostra que a estrategia nao e apenas uma regra arbitraria, mas uma anomalia amplamente investigada na literatura financeira.

Para fins metodologicos, a estrategia de momentum deve ser definida de forma objetiva, especificando janela de calculo, frequencia de rebalanceamento, criterio de selecao dos ativos e tratamento de custos de transacao. Esses elementos sao essenciais para garantir reprodutibilidade e evitar escolhas ex-post que favorecam artificialmente o resultado do backtest.

### 2.2.5 Mean Reversion

Mean Reversion, ou reversao a media, parte da ideia de que desvios expressivos em relacao a um nivel considerado normal tendem a ser parcialmente revertidos ao longo do tempo. Em estrategias de investimento, essa logica pode ser aplicada comprando ativos que tiveram queda recente ou reduzindo exposicao a ativos que subiram de forma acentuada, desde que se assuma que parte desse movimento foi transitorio.

Poterba e Summers (1988) investigam componentes transitorios nos precos das acoes e contribuem para a discussao sobre previsibilidade e reversao em series financeiras. Para este trabalho, a referencia serve como base teorica para incluir estrategias contrarias ou de reversao como contraponto as estrategias de momentum. Enquanto momentum pressupoe persistencia, mean reversion pressupoe correcao parcial de desvios.

A comparacao entre momentum e mean reversion e relevante porque essas estrategias representam hipoteses opostas sobre a dinamica dos retornos. Em mercados sujeitos a mudancas de regime, uma abordagem pode funcionar melhor em certos periodos e pior em outros, reforcando a necessidade de avaliacao temporal e analise de robustez.

### 2.2.6 RSI

O Relative Strength Index (RSI), proposto por Wilder (1978), e um indicador tecnico que busca medir a intensidade dos movimentos recentes de alta e baixa de um ativo. Tradicionalmente, valores elevados de RSI sao associados a condicoes de sobrecompra, enquanto valores baixos sao associados a condicoes de sobrevenda. Assim, o indicador pode ser usado tanto em estrategias de reversao quanto como filtro auxiliar de entrada e saida.

No escopo deste TCC, o RSI pode ser incluido como estrategia complementar ou indicador comparativo, caso o experimento utilize sinais tecnicos alem de medias moveis e momentum. Sua utilidade esta em representar uma regra classica de analise tecnica, amplamente conhecida e facilmente operacionalizavel em backtests.

## 2.3 Teoria Moderna de Portfolio

A Teoria Moderna de Portfolio, proposta por Markowitz (1952), estabelece uma das bases mais importantes da teoria financeira moderna. Seu ponto central e que a decisao de investimento nao deve considerar apenas o retorno esperado de cada ativo isoladamente, mas tambem o risco da carteira como um todo e as relacoes de covariancia entre os ativos. Dessa forma, a diversificacao permite combinar ativos de modo a reduzir o risco total da carteira sem necessariamente reduzir o retorno esperado na mesma proporcao.

Markowitz (1952) formaliza a relacao entre risco e retorno por meio da analise media-variancia. Nesse modelo, o retorno esperado da carteira e uma media ponderada dos retornos esperados dos ativos, enquanto o risco e representado pela variancia ou desvio-padrao dos retornos da carteira. A composicao otima depende nao apenas da volatilidade individual dos ativos, mas tambem de como eles se movem conjuntamente.

Essa abordagem e relevante para o presente trabalho porque oferece um benchmark classico de alocacao de portfolio. Enquanto estrategias como momentum e medias moveis definem regras de exposicao com base em sinais de preco, Markowitz define pesos de carteira a partir de uma otimizacao risco-retorno. Assim, a comparacao com Reinforcement Learning se torna mais forte: o agente de IA nao sera avaliado apenas contra regras tecnicas simples, mas tambem contra uma teoria consolidada de otimizacao de carteiras.

### 2.3.1 Carteira de minima variancia

A carteira de minima variancia e uma aplicacao direta da estrutura de Markowitz. Seu objetivo e encontrar os pesos dos ativos que minimizam a variancia total da carteira, dadas as estimativas de covariancia entre os retornos. Diferentemente de uma carteira que tenta maximizar retorno esperado, a minima variancia concentra-se na reducao de risco, o que pode ser especialmente util quando estimativas de retorno sao instaveis ou pouco confiaveis.

No contexto do mercado acionario brasileiro, a carteira de minima variancia pode funcionar como benchmark conservador. Ela permite avaliar se estrategias ativas conseguem gerar melhor relacao risco-retorno sem elevar excessivamente drawdowns, turnover e custos de transacao. Por depender fortemente da matriz de covariancia, sua implementacao tambem exige cuidado com a janela de estimacao e com o rebalanceamento ao longo do tempo.

### 2.3.2 Relacao risco-retorno

A relacao risco-retorno e um eixo central deste TCC. Uma estrategia nao deve ser avaliada apenas pelo retorno acumulado, pois retornos maiores podem vir acompanhados de volatilidade elevada, grandes perdas temporarias ou custos operacionais excessivos. A contribuicao de Markowitz (1952) e justamente mostrar que a escolha de carteira envolve trade-offs entre retorno esperado e risco.

Por isso, a avaliacao empirica deve considerar metricas ajustadas ao risco, como Sharpe Ratio, Sortino Ratio e Maximum Drawdown, alem de retorno acumulado. Essa perspectiva permite comparar estrategias com perfis diferentes de forma mais equilibrada, especialmente quando se confrontam metodos passivos, regras tecnicas, otimizacao classica e Reinforcement Learning.

## 2.4 Backtesting em series financeiras

Backtesting e o processo de simular uma estrategia de investimento sobre dados historicos, aplicando as regras de decisao como se elas estivessem sendo executadas no passado. Essa pratica e fundamental para avaliar estrategias quantitativas, mas tambem apresenta riscos metodologicos importantes. Resultados historicos positivos podem decorrer de padroes reais, mas tambem de acaso, escolhas excessivamente ajustadas aos dados ou vazamento de informacao futura.

White (2000) discute o problema de data snooping, que ocorre quando muitas estrategias, parametros ou variacoes sao testadas sobre o mesmo conjunto de dados e apenas os melhores resultados sao reportados. Nesse caso, uma estrategia pode parecer lucrativa simplesmente porque foi selecionada entre muitas alternativas, e nao porque possui capacidade preditiva real. Essa preocupacao e diretamente relevante para este TCC, pois a comparacao entre diferentes benchmarks e um agente de RL envolve multiplas especificacoes.

Hansen (2005) complementa essa discussao ao propor um teste de superior predictive ability, voltado a avaliar se um modelo apresenta desempenho superior de forma estatisticamente defensavel em relacao a um conjunto de alternativas. Embora o TCC nao precise necessariamente implementar esse teste, a referencia reforca a necessidade de tratar a superioridade de uma estrategia com cautela, especialmente quando varias estrategias sao comparadas.

Bailey et al. (2016) abordam o problema do overfitting em backtests financeiros. A ideia central e que estrategias podem ser ajustadas aos dados historicos de tal forma que apresentam excelente desempenho in-sample, mas falham quando aplicadas fora da amostra. Essa contribuicao justifica o uso de validacao temporal, separacao entre treino e teste e, se possivel, procedimentos walk-forward.

Para que o backtest seja metodologicamente adequado, as decisoes de cada periodo devem usar apenas informacoes disponiveis ate aquele momento. Alem disso, custos de transacao, rebalanceamento, liquidez e turnover devem ser considerados, pois podem alterar significativamente a viabilidade pratica de estrategias ativas.

## 2.5 Metricas de desempenho e risco

A comparacao entre estrategias de investimento exige metricas capazes de capturar diferentes dimensoes de desempenho. Retorno acumulado, por si so, nao e suficiente para avaliar uma estrategia, pois ignora a volatilidade, a magnitude das perdas, a regularidade dos resultados e os custos associados a negociacao. Por esse motivo, este TCC considera metricas de retorno ajustado ao risco, drawdown, turnover e custos de transacao.

### 2.5.1 Retorno acumulado

O retorno acumulado mede a variacao total do capital ao longo do periodo analisado. Ele e uma metrica intuitiva e importante, pois mostra o crescimento final da carteira. Entretanto, deve ser interpretado em conjunto com medidas de risco. Duas estrategias podem apresentar retorno acumulado semelhante, mas uma delas pode ter enfrentado quedas muito maiores ou volatilidade excessiva ao longo do caminho.

### 2.5.2 Sharpe Ratio

O Sharpe Ratio, discutido por Sharpe (1994), mede o retorno excedente de uma estrategia por unidade de risco total, normalmente representado pelo desvio-padrao dos retornos. A metrica e amplamente utilizada porque resume em um unico indicador a relacao entre retorno e volatilidade. Em termos gerais, quanto maior o Sharpe Ratio, melhor o retorno ajustado ao risco.

No contexto deste trabalho, o Sharpe Ratio permite comparar estrategias com diferentes niveis de exposicao ao risco. Uma estrategia de Reinforcement Learning, por exemplo, pode gerar maior retorno acumulado, mas isso so sera desejavel se o ganho compensar a volatilidade adicional. Assim, o Sharpe Ratio ajuda a evitar conclusoes baseadas apenas no retorno bruto.

Lo (2002) chama atencao para a interpretacao estatistica do Sharpe Ratio, especialmente quando os retornos apresentam autocorrelacao, dependencia temporal ou distribuicoes que se afastam da normalidade. Essa observacao e relevante para series financeiras, nas quais os retornos podem apresentar caudas pesadas e regimes de volatilidade. Portanto, o Sharpe deve ser usado com cautela e complementado por outras metricas.

### 2.5.3 Sortino Ratio

O Sortino Ratio e uma variacao do Sharpe Ratio que considera apenas o risco de queda, isto e, a volatilidade associada a retornos abaixo de um alvo ou retorno minimo aceitavel. Essa distincao e importante porque a volatilidade positiva nao representa necessariamente um problema para o investidor. Ao penalizar mais diretamente os desvios negativos, o Sortino Ratio pode oferecer uma avaliacao mais alinhada a preocupacao com perdas.

Kidd (2012) apresenta o Sortino Ratio como uma metrica de desempenho ajustada ao risco que substitui o desvio-padrao total, usado no Sharpe Ratio, pela downside deviation. A autora destaca que o indicador busca medir o retorno excedente em relacao ao risco de nao atingir uma meta minima de retorno, conhecida como Minimum Accepted Return (MAR). Assim, o Sortino Ratio e particularmente util quando o interesse do investidor esta mais associado a perdas ou retornos abaixo de um objetivo do que a oscilacoes positivas da carteira.

Apesar dessa vantagem, Kidd (2012) tambem observa que o Sortino Ratio nao deve ser interpretado como uma medida completa de risco. A forma de calcular a downside deviation pode alterar significativamente o resultado, especialmente quando se utilizam apenas observacoes historicas abaixo da meta definida. Por isso, neste TCC, o Sortino Ratio deve ser tratado como metrica complementar ao Sharpe Ratio e ao Maximum Drawdown, contribuindo para avaliar o risco de queda sem substituir outras medidas de desempenho e robustez.

### 2.5.4 Maximum Drawdown

Maximum Drawdown mede a maior queda percentual de uma carteira entre um pico e um vale ao longo do periodo analisado. Essa metrica captura a severidade da pior perda acumulada enfrentada pelo investidor antes de uma recuperacao. Diferentemente da volatilidade, que mede dispersao geral dos retornos, o drawdown esta diretamente associado a perdas observadas na trajetoria do capital.

Magdon-Ismail et al. (2004) formalizam o conceito de maximum drawdown e sua relevancia na avaliacao de risco. Para este TCC, a metrica e fundamental porque estrategias com retornos elevados podem ser pouco atrativas se estiverem associadas a perdas temporarias muito profundas. Em uma comparacao entre benchmarks tradicionais e RL, o drawdown ajuda a avaliar a estabilidade e a tolerancia ao risco de cada abordagem.

### 2.5.5 Turnover

Turnover mede a intensidade de negociacao de uma estrategia, isto e, quanto a composicao da carteira muda ao longo do tempo. Estrategias com alto turnover tendem a gerar mais custos de transacao e podem ser menos viaveis na pratica. Essa metrica e especialmente importante para estrategias ativas, como momentum, medias moveis e Reinforcement Learning, que podem alterar posicoes com frequencia.

No trabalho, o turnover deve ser usado para avaliar nao apenas o desempenho financeiro, mas tambem a eficiencia operacional das estrategias. Uma estrategia que supera as demais antes dos custos pode perder atratividade depois de considerar corretagem, spread, impostos ou impacto de mercado.

### 2.5.6 Custos de transacao

Harris (2003) discute aspectos de microestrutura de mercado, negociacao e custos associados a execucao de ordens. Esses custos sao relevantes porque o retorno teorico de uma estrategia pode diferir substancialmente do retorno realizavel. Custos de transacao incluem corretagem, spread bid-ask, emolumentos, impostos e possivel impacto de mercado em ativos menos liquidos.

Para este TCC, incorporar custos de transacao aumenta o realismo do backtest. Isso e particularmente importante ao comparar estrategias passivas com estrategias ativas, pois metodos que rebalanceiam com maior frequencia podem parecer superiores em um ambiente sem custos, mas perder desempenho quando os custos sao incluidos.

## 2.6 Reinforcement Learning aplicado a alocacao de portfolio

Reinforcement Learning e uma abordagem de aprendizado de maquina em que um agente aprende a tomar decisoes por interacao com um ambiente. Em um problema de investimento, o ambiente pode ser representado pelo mercado financeiro, o estado pode incluir informacoes historicas de precos, retornos, indicadores ou posicoes da carteira, as acoes podem corresponder a comprar, vender, manter ou definir pesos de alocacao, e a recompensa pode ser associada ao retorno da carteira ajustado por risco e custos.

No escopo proposto para o TCC, o agente de Reinforcement Learning representa a abordagem de inteligencia artificial a ser comparada com benchmarks tradicionais. A pergunta central e se um agente capaz de aprender decisoes sequenciais consegue superar estrategias baseadas em regras e modelos classicos de otimizacao em metricas como retorno acumulado, Sharpe Ratio, Sortino Ratio, Maximum Drawdown e turnover.

Esta secao ainda precisa ser fortalecida com PDFs especificos de Reinforcement Learning, pois a pasta atual nao contem as referencias previstas em `estrutura_tcc.md`, como Sutton e Barto, Moody e Saffell, Mnih et al., Schulman et al. ou FinRL. Para a versao final do referencial teorico, recomenda-se adicionar pelo menos uma referencia conceitual de RL e uma referencia aplicada a trading ou alocacao de portfolio.

## 2.7 Validacao temporal e analise de robustez

A validacao temporal e essencial em estudos com series financeiras porque os dados possuem ordem cronologica e podem apresentar mudancas de regime. Diferentemente de problemas tradicionais de aprendizado supervisionado, nao se deve embaralhar aleatoriamente observacoes financeiras quando isso cria risco de vazamento de informacao futura. A avaliacao deve respeitar a sequencia temporal, usando dados passados para estimar parametros ou treinar modelos e dados posteriores para teste.

O procedimento walk-forward e uma alternativa adequada para esse contexto. Nele, a estrategia e treinada ou calibrada em uma janela historica e testada em um periodo posterior; em seguida, a janela avanca no tempo e o processo se repete. Esse metodo permite avaliar a estabilidade do desempenho em diferentes periodos de mercado e reduz a dependencia de uma unica divisao treino-teste.

White (2000), Hansen (2005) e Bailey et al. (2016) sustentam a preocupacao com robustez, data snooping e overfitting em backtests. Em conjunto, essas referencias mostram que um resultado historico positivo nao deve ser interpretado automaticamente como evidencia de superioridade. E necessario verificar se a estrategia permanece competitiva fora da amostra, se nao depende de parametros excessivamente ajustados e se seu desempenho resiste a custos de transacao e mudancas de periodo.

No presente TCC, a analise de robustez deve cumprir tres funcoes principais. Primeiro, garantir que todas as estrategias sejam comparadas sob as mesmas condicoes de dados, custos e periodo. Segundo, avaliar se os resultados sao consistentes ao longo do tempo, e nao concentrados em um intervalo especifico. Terceiro, reduzir o risco de conclusoes artificiais causadas por excesso de testes ou selecao retrospectiva de parametros.

## 2.8 Sintese do referencial teorico

As referencias analisadas sustentam a construcao de um experimento comparativo entre metodos tradicionais e uma abordagem baseada em Reinforcement Learning. As estrategias tecnicas, como medias moveis, momentum, mean reversion e RSI, fornecem benchmarks quantitativos simples e interpretaveis. A Teoria Moderna de Portfolio de Markowitz oferece um benchmark classico de otimizacao risco-retorno. As metricas de desempenho, como Sharpe Ratio, Maximum Drawdown, turnover e custos de transacao, permitem avaliar as estrategias de forma mais completa do que apenas pelo retorno acumulado.

A literatura sobre backtesting e robustez mostra que a avaliacao empirica deve ser conduzida com cuidado, evitando data snooping, overfitting e vazamento de informacao. Dessa forma, o referencial teorico aponta para uma metodologia baseada em comparacao justa entre estrategias, validacao temporal, inclusao de custos e avaliacao por multiplas metricas de risco-retorno. Esse conjunto de fundamentos torna o problema de pesquisa mais defensavel: investigar se um agente de Reinforcement Learning consegue superar estrategias quantitativas tradicionais e modelos classicos de alocacao de portfolio no mercado acionario brasileiro.

## Referencias utilizadas nos PDFs locais

BAILEY, David H. et al. The probability of backtest overfitting. 2016.

BROCK, William; LAKONISHOK, Josef; LEBARON, Blake. Simple technical trading rules and the stochastic properties of stock returns. The Journal of Finance, 1992.

HANSEN, Peter R. A test for superior predictive ability. Journal of Business & Economic Statistics, 2005.

HARRIS, Larry. Trading and exchanges: market microstructure for practitioners. Oxford University Press, 2003.

KAKUSHADZE, Zura; SERUR, Juan A. 151 trading strategies. Palgrave Macmillan, 2018.

LO, Andrew W. The statistics of Sharpe ratios. Financial Analysts Journal, 2002.

LO, Andrew W.; MAMAYSKY, Harry; WANG, Jiang. Foundations of technical analysis: computational algorithms, statistical inference, and empirical implementation. The Journal of Finance, 2000.

MAGDON-ISMAIL, Malik et al. On the maximum drawdown of a Brownian motion. Journal of Applied Probability, 2004.

MARKOWITZ, Harry. Portfolio selection. The Journal of Finance, 1952.

MOSKOWITZ, Tobias J.; OOI, Yao Hua; PEDERSEN, Lasse Heje. Time series momentum. Journal of Financial Economics, 2012.

POTERBA, James M.; SUMMERS, Lawrence H. Mean reversion in stock prices: evidence and implications. Journal of Financial Economics, 1988.

SHARPE, William F. The Sharpe ratio. The Journal of Portfolio Management, 1994.

WHITE, Halbert. A reality check for data snooping. Econometrica, 2000.

WILDER, J. Welles. New concepts in technical trading systems. Trend Research, 1978.

KIDD, Deborah. The Sortino Ratio: is downside risk the only risk that matters? CFA Institute, 2012.

## Referencias pendentes para completar o escopo

SUTTON, Richard S.; BARTO, Andrew G. Reinforcement learning: an introduction. 2. ed. MIT Press, 2018.

MOODY, John; SAFFELL, Matthew. Learning to trade via direct reinforcement. IEEE Transactions on Neural Networks, 2001.

## Paginas usadas na extracao do texto

| Artigo/livro | Pagina(s) |
| --- | --- |
| (Kakushadze e Serur, 2018) | 1 |
| (Brock, Lakonishok e LeBaron, 1992) | PDF sem texto extraivel; OCR/conferencia manual pendente |
| (Lo, Mamaysky e Wang, 2000) | 1, 2 |
| (Moskowitz, Ooi e Pedersen, 2012) | 1, 2 |
| (Poterba e Summers, 1988) | 1, 2 |
| (Wilder, 1978) | PDF sem texto extraivel; OCR/conferencia manual pendente |
| (Markowitz, 1952) | 1, 2 |
| (White, 2000) | 1, 2 |
| (Hansen, 2005) | 1, 2 |
| (Bailey et al., 2016) | 2, 5 |
| (Sharpe, 1994) | 1, 2 |
| (Lo, 2002) | 1, 2 |
| (Kidd, 2012) | 1, 2, 3 |
| (Magdon-Ismail et al., 2004) | 1, 4 |
| (Harris, 2003) | 11, 12 |
