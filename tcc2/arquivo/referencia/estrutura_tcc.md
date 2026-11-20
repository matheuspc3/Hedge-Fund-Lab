Com base no seu novo escopo, eu montaria a pasta **`references`** assim:

```txt
references/
│
├── 01_estrategias_quantitativas/
├── 02_markowitz_e_benchmarks/
├── 03_metricas_de_desempenho/
├── 04_backtesting_e_robustez/
└── 05_reinforcement_learning/
```

A ideia é: **cada referência citada no texto precisa ter um PDF dentro dessas pastas**, com os trechos usados no TCC grifados/anotados.

---

# 1. Referências para estratégias quantitativas tradicionais

| Seção do TCC                                     | Referência                         | Nome do PDF                                                 | O que grifar                                                                                |
| ------------------------------------------------ | ---------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 2.1 / 2.2 Estratégias quantitativas tradicionais | Brock, Lakonishok e LeBaron (1992) | `brock_lakonishok_lebaron_1992_technical_trading_rules.pdf` | Trechos sobre regras de médias móveis e trading rules simples como benchmarks quantitativos |
| 2.2 Moving Average Crossover                     | Lo, Mamaysky e Wang (2000)         | `lo_mamaysky_wang_2000_technical_analysis.pdf`              | Trechos sobre análise técnica como abordagem sistemática/computacional                      |
| 2.2 Momentum                                     | Moskowitz, Ooi e Pedersen (2012)   | `moskowitz_ooi_pedersen_2012_time_series_momentum.pdf`      | Trechos sobre persistência dos retornos e time-series momentum                              |
| 2.2 Mean Reversion                               | Poterba e Summers (1988)           | `poterba_summers_1988_mean_reversion.pdf`                   | Trechos sobre reversão à média e componentes transitórios nos preços                        |
| 2.2 RSI                                          | Wilder (1978)                      | `wilder_1978_new_concepts_technical_trading_systems.pdf`    | Fórmula e explicação do RSI                                                                 |
| 2.2 Bollinger Bands, caso você use               | Bollinger (2001)                   | `bollinger_2001_bollinger_bands.pdf`                        | Fórmula das bandas, média móvel e desvio-padrão                                             |

Brock, Lakonishok e LeBaron testam regras técnicas simples, como médias móveis, em uma longa série histórica do Dow Jones, então servem muito bem para justificar **Moving Average Crossover** como benchmark clássico. ([Wiley Online Library][1]) Lo, Mamaysky e Wang ajudam a dar uma base acadêmica para análise técnica tratada de forma computacional e empírica. ([Wiley Online Library][2]) Moskowitz, Ooi e Pedersen documentam time-series momentum em diferentes classes de ativos, sendo uma referência forte para a estratégia de momentum. ([ScienceDirect][3]) Poterba e Summers são úteis para fundamentar mean reversion. ([ScienceDirect][4]) Wilder é a referência clássica para RSI, e Bollinger é a referência direta para Bandas de Bollinger. ([Google Livros][5])

---

# 2. Referências para Markowitz e benchmarks de carteira

| Seção do TCC                     | Referência                        | Nome do PDF                                              | O que grifar                                                          |
| -------------------------------- | --------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- |
| 2.3 Teoria Moderna de Portfólio  | Markowitz (1952)                  | `markowitz_1952_portfolio_selection.pdf`                 | Trechos sobre risco, retorno, variância, covariância e diversificação |
| 2.3 Carteira de mínima variância | Markowitz (1952)                  | mesmo PDF                                                | Trechos que justificam otimização média-variância                     |
| 2.2 Equal Weight / benchmark 1/N | DeMiguel, Garlappi e Uppal (2009) | `demiguel_garlappi_uppal_2009_naive_diversification.pdf` | Trechos sobre o portfólio 1/N como benchmark forte e simples          |

Markowitz deve ficar como referência central porque seu TCC compara estratégias por **retorno ajustado ao risco**, e a teoria média-variância é a base clássica para discutir risco de carteira. ([Wiley Online Library][6]) DeMiguel, Garlappi e Uppal são importantes porque mostram que o portfólio ingênuo 1/N pode ser um benchmark competitivo contra métodos otimizados. ([OUP Academic][7])

---

# 3. Referências para métricas de desempenho

| Seção do TCC                       | Referência                  | Nome do PDF                               | O que grifar                                                        |
| ---------------------------------- | --------------------------- | ----------------------------------------- | ------------------------------------------------------------------- |
| 2.5 Sharpe Ratio                   | Sharpe (1994)               | `sharpe_1994_sharpe_ratio.pdf`            | Fórmula e interpretação do Sharpe Ratio                             |
| 2.5 Sharpe Ratio / limitações      | Lo (2002)                   | `lo_2002_statistics_of_sharpe_ratios.pdf` | Trechos sobre interpretação estatística do Sharpe                   |
| 2.5 Sortino Ratio                  | Kidd (2012)                 | `kidd_2012_sortino_ratio_downside_risk.pdf` | Trechos sobre downside risk, MAR e diferença em relação ao Sharpe    |
| 2.5 Maximum Drawdown               | Magdon-Ismail et al. (2004) | `magdon_ismail_2004_maximum_drawdown.pdf` | Definição de maximum drawdown como queda do pico ao vale            |
| 2.5 Turnover e custos de transação | Harris (2003)               | `harris_2003_trading_and_exchanges.pdf`   | Trechos sobre custos de transação, execução e impacto de negociação |

Sharpe (1994) é a referência direta para o Sharpe Ratio. ([PM Research][8]) Lo (2002) é bom para mostrar cuidado estatístico na interpretação do Sharpe, especialmente em séries financeiras. ([ResearchGate][9]) Kidd (2012) fundamenta o uso do Sortino Ratio como métrica que penaliza mais diretamente o risco de queda, em vez de tratar volatilidade positiva e negativa da mesma forma. Magdon-Ismail et al. ajudam a formalizar o maximum drawdown. ([Cambridge University Press & Assessment][11]) Harris é útil para justificar a inclusão de custos de transação e turnover no backtest. ([Acsu Buffalo][12])

---

# 4. Referências para backtesting, validação e robustez

| Seção do TCC                         | Referência                | Nome do PDF                                              | O que grifar                                                          |
| ------------------------------------ | ------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------- |
| 2.4 Backtesting                      | White (2000)              | `white_2000_reality_check_data_snooping.pdf`             | Trechos sobre data snooping e risco de achar estratégia boa por acaso |
| 2.7 Teste estatístico de performance | Hansen (2005)             | `hansen_2005_superior_predictive_ability.pdf`            | Trechos sobre teste de superior predictive ability                    |
| 2.7 Robustez / overfitting           | Bailey et al. (2016/2017) | `bailey_et_al_2016_probability_backtest_overfitting.pdf` | Trechos sobre probabilidade de overfitting em backtests               |
| 2.7 Validação temporal / robustez    | Bailey et al. (2016/2017) | mesmo PDF                                                | Trechos sobre validação em simulações de investimento                 |

White é uma referência importante porque seu TCC vai testar várias estratégias; isso aumenta o risco de **data snooping**, ou seja, encontrar uma estratégia aparentemente boa apenas por testar muitas alternativas. ([Wiley Online Library][13]) Hansen complementa isso com um teste de superioridade preditiva, útil se você quiser comparar estatisticamente o desempenho das estratégias. ([Tandf Online][14]) Bailey et al. são muito bons para justificar a preocupação com overfitting em backtests financeiros. ([SSRN][15])

---

# 5. Referências para Reinforcement Learning

| Seção do TCC                     | Referência                     | Nome do PDF                                    | O que grifar                                                                                                |
| -------------------------------- | ------------------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 2.6 Conceitos básicos de RL      | Sutton e Barto (2018)          | `sutton_barto_2018_reinforcement_learning.pdf` | Definições de agente, ambiente, estado, ação, recompensa e política                                         |
| 2.6 RL aplicado a trading        | Moody e Saffell (2001)         | `moody_saffell_2001_learning_to_trade.pdf`     | Trechos sobre uso de reinforcement learning para otimizar retorno ajustado ao risco com custos de transação |
| 2.6 Deep RL / DQN, caso use      | Mnih et al. (2015)             | `mnih_et_al_2015_dqn.pdf`                      | Trechos sobre deep Q-network e aprendizado de políticas por interação                                       |
| 2.6 PPO, caso use                | Schulman et al. (2017)         | `schulman_et_al_2017_ppo.pdf`                  | Trechos sobre PPO, função objetivo e método policy gradient                                                 |
| 2.6 RL em finanças quantitativas | Liu et al. (2021/2022) — FinRL | `liu_et_al_2021_finrl.pdf`                     | Trechos sobre framework de DRL para trading, ambiente, agentes, custos e reproducibilidade                  |

Sutton e Barto são a base teórica para explicar RL de forma formal. ([Ideias Incompletas][16]) Moody e Saffell conectam diretamente RL com trading e retorno ajustado ao risco, então essa referência é muito alinhada ao seu TCC. ([ACM Digital Library][17]) Se você usar DQN, cite Mnih et al.; se usar PPO, cite Schulman et al. ([Nature][18]) FinRL é uma referência útil para mostrar que existe uma literatura recente tratando RL como pipeline de trading quantitativo com ambiente, agentes, custos e reprodutibilidade. ([ACM Digital Library][19])

---

# Lista final enxuta que eu usaria no seu TCC

Se eu fosse seu orientador, eu recomendaria começar com estas **15 referências principais**:

```txt
1. Markowitz (1952) — Portfolio Selection
2. DeMiguel, Garlappi e Uppal (2009) — 1/N Portfolio Strategy
3. Brock, Lakonishok e LeBaron (1992) — Technical Trading Rules
4. Lo, Mamaysky e Wang (2000) — Foundations of Technical Analysis
5. Moskowitz, Ooi e Pedersen (2012) — Time Series Momentum
6. Poterba e Summers (1988) — Mean Reversion
7. Wilder (1978) — RSI
8. Bollinger (2001) — Bollinger Bands
9. Sharpe (1994) — Sharpe Ratio
10. Kidd (2012) — Sortino Ratio e Downside Risk
11. Magdon-Ismail et al. (2004) — Maximum Drawdown
12. White (2000) — Data Snooping
13. Hansen (2005) — Superior Predictive Ability
14. Sutton e Barto (2018) — Reinforcement Learning
15. Moody e Saffell (2001) — RL aplicado a trading
```

E eu deixaria como **opcionais**, dependendo da implementação:

```txt
16. Mnih et al. (2015) — se usar DQN
17. Schulman et al. (2017) — se usar PPO
18. Liu et al. (2021/2022) — se usar FinRL ou quiser citar framework de DRL em trading
19. Harris (2003) — se você discutir custos de transação com mais profundidade
20. Bailey et al. (2016/2017) — se quiser fortalecer a parte de overfitting em backtest
```

---

# Como ficaria a pasta do jeito que o orientador quer

```txt
references/
│
├── 01_estrategias_quantitativas/
│   ├── brock_lakonishok_lebaron_1992_technical_trading_rules.pdf
│   ├── lo_mamaysky_wang_2000_technical_analysis.pdf
│   ├── moskowitz_ooi_pedersen_2012_time_series_momentum.pdf
│   ├── poterba_summers_1988_mean_reversion.pdf
│   ├── wilder_1978_new_concepts_technical_trading_systems.pdf
│   └── bollinger_2001_bollinger_bands.pdf
│
├── 02_markowitz_e_benchmarks/
│   ├── markowitz_1952_portfolio_selection.pdf
│   └── demiguel_garlappi_uppal_2009_naive_diversification.pdf
│
├── 03_metricas_de_desempenho/
│   ├── sharpe_1994_sharpe_ratio.pdf
│   ├── lo_2002_statistics_of_sharpe_ratios.pdf
│   ├── kidd_2012_sortino_ratio_downside_risk.pdf
│   ├── magdon_ismail_2004_maximum_drawdown.pdf
│   └── harris_2003_trading_and_exchanges.pdf
│
├── 04_backtesting_e_robustez/
│   ├── white_2000_reality_check_data_snooping.pdf
│   ├── hansen_2005_superior_predictive_ability.pdf
│   └── bailey_et_al_2016_probability_backtest_overfitting.pdf
│
└── 05_reinforcement_learning/
    ├── sutton_barto_2018_reinforcement_learning.pdf
    ├── moody_saffell_2001_learning_to_trade.pdf
    ├── mnih_et_al_2015_dqn.pdf
    ├── schulman_et_al_2017_ppo.pdf
    └── liu_et_al_2021_finrl.pdf
```

---

# Checklist que você deve fazer em cada PDF

Para cada arquivo da pasta `references`, faça isso:

```txt
1. Conferir se o título do PDF é igual ao título citado no TCC.
2. Conferir autores.
3. Conferir ano.
4. Conferir DOI, se for artigo.
5. Conferir periódico ou conferência.
6. Grifar o trecho usado para justificar a citação.
7. Fazer uma anotação curta no PDF, por exemplo:
   “Usado na seção 2.2 para justificar estratégia de momentum”.
8. Garantir que toda referência citada no texto aparece na lista de referências.
9. Garantir que toda referência da lista tem PDF marcado na pasta references.
```

Para livros como **Wilder**, **Bollinger**, **Sutton e Barto** e **Harris**, nem sempre haverá DOI. Nesses casos, confira **título, autores, editora, ano e ISBN**. Use PDF legal da biblioteca, capítulo disponibilizado pelo autor/editora, ou apenas as páginas permitidas/necessárias para fins acadêmicos.

[1]: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb04681.x?utm_source=chatgpt.com "Simple Technical Trading Rules and the Stochastic ..."
[2]: https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00265?utm_source=chatgpt.com "Foundations of Technical Analysis: Computational ..."
[3]: https://www.sciencedirect.com/science/article/pii/S0304405X11002613?utm_source=chatgpt.com "Time series momentum"
[4]: https://www.sciencedirect.com/science/article/pii/0304405X88900219?utm_source=chatgpt.com "Mean reversion in stock prices: Evidence and Implications"
[5]: https://books.google.com/books/about/New_Concepts_in_Technical_Trading_System.html?hl=pt-BR&id=WesJAQAAMAAJ&utm_source=chatgpt.com "New Concepts in Technical Trading Systems"
[6]: https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1952.tb01525.x?utm_source=chatgpt.com "PORTFOLIO SELECTION* - Markowitz - 1952"
[7]: https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901?utm_source=chatgpt.com "Optimal Versus Naive Diversification: How Inefficient is the 1/N ..."
[8]: https://www.pm-research.com/content/iijpormgmt/21/1/49?utm_source=chatgpt.com "The Sharpe Ratio"
[9]: https://www.researchgate.net/publication/228139699_The_Statistics_of_Sharpe_Ratios?utm_source=chatgpt.com "(PDF) The Statistics of Sharpe Ratios"
[10]: https://www.cfainstitute.org/insights/professional-learning/refresher-readings/the-sortino-ratio "The Sortino Ratio: Is Downside Risk the Only Risk that Matters?"
[11]: https://www.cambridge.org/core/journals/journal-of-applied-probability/article/on-the-maximum-drawdown-of-a-brownian-motion/F9E3B8A454B020DDEBF0AC3390EF7807?utm_source=chatgpt.com "On the maximum drawdown of a Brownian motion"
[12]: https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/Trading-Exchanges-Market-Microstructure-Practitioners%20Draft%20Copy.pdf?utm_source=chatgpt.com "Trading-Exchanges-Market-Microstructure-Practitioners ..."
[13]: https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152?utm_source=chatgpt.com "A Reality Check for Data Snooping - White - 2000"
[14]: https://www.tandfonline.com/doi/abs/10.1198/073500105000000063?utm_source=chatgpt.com "A Test for Superior Predictive Ability"
[15]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253&utm_source=chatgpt.com "The Probability of Backtest Overfitting"
[16]: https://incompleteideas.net/book/the-book-2nd.html?utm_source=chatgpt.com "Reinforcement Learning: An Introduction"
[17]: https://dl.acm.org/doi/10.1109/72.935097?utm_source=chatgpt.com "Learning to trade via direct reinforcement"
[18]: https://www.nature.com/articles/nature14236?utm_source=chatgpt.com "Human-level control through deep reinforcement learning"
[19]: https://dl.acm.org/doi/10.1145/3490354.3494366?utm_source=chatgpt.com "FinRL: deep reinforcement learning framework to automate ..."
