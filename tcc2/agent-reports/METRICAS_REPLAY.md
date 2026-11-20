# Métricas de risco do Replay Contínuo Abril–Novembro 2026 (v1, v2, v3)

Gerado por `tcc2/scripts/metricas_replay.py` a partir dos `daily.csv` selados em `tcc2/evidence/04-replay-abril-novembro/dados/series-v{1,2,3}/`. Vínculo: DP-37 / `REPLAY-01..03`, material do capítulo de resultados (`TCC-02/03`).

> **Ressalva.** 153 pregões (06/04/2026 a 12/11/2026), uma única trajetória de mercado, cinco ativos, reconstrução histórica feita depois do fechamento do período. As três versões da Multiagentes foram ajustadas a partir das auditorias desta mesma janela: os números são **dentro da amostra**, descritivos, e não têm significância estatística nem valor prospectivo (DP-09, DP-31, DP-37).

## 1. Retorno e risco

| Carteira | Patrimônio final (R$) | Retorno total | Retorno anualizado | Volatilidade anualizada | Sharpe | EP aprox. do Sharpe | Sortino | Máx. drawdown | Pico → vale | Duração máx. (pregões) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Multiagentes v1 | 82.178,71 | -17,82% | -27,62% | 23,17% | -1,28 | 1,29 | -1,60 | -22,90% | 14/04 → 12/08 | 146 |
| Multiagentes v2 | 85.743,57 | -14,26% | -22,38% | 19,33% | -1,21 | 1,29 | -1,58 | -19,37% | 14/04 → 06/11 | 146 |
| Multiagentes v3 | 100.067,36 | 0,07% | 0,11% | 16,01% | 0,09 | 1,28 | 0,13 | -12,80% | 14/04 → 10/06 | 97 |
| Buy & Hold | 88.791,11 | -11,21% | -17,78% | 22,08% | -0,78 | 1,28 | -1,01 | -18,53% | 05/10 → 05/11 | 119 |
| SMA 50/200 | 88.866,68 | -11,13% | -17,67% | 13,11% | -1,42 | 1,29 | -1,77 | -16,61% | 14/04 → 06/11 | 146 |
| Bollinger 20/2 | 104.887,05 | 4,89% | 8,18% | 11,77% | 0,73 | 1,28 | 1,16 | -8,52% | 30/04 → 05/06 | 85 |
| Equal Weight 63d | 89.869,29 | -10,13% | -16,13% | 21,61% | -0,71 | 1,28 | -0,94 | -18,10% | 05/10 → 05/11 | 119 |
| Mínima Variância 252/63 | 95.814,84 | -4,19% | -6,80% | 17,52% | -0,32 | 1,28 | -0,47 | -14,95% | 13/04 → 05/06 | 120 |

## 2. Operações, custos e caixa

| Carteira | Operações (C / V) | Custos (R$) | Volume negociado estimado (R$) | Giro no período | Caixa médio | Caixa no fechamento |
|---|---:|---:|---:|---:|---:|---:|
| Multiagentes v1 | 86 (50 / 36) | 184,40 | 614.667 | 6,78× | 12,98% | 1,64% |
| Multiagentes v2 | 38 (22 / 16) | 119,87 | 399.567 | 4,34× | 24,69% | 45,86% |
| Multiagentes v3 | 81 (29 / 52) | 120,07 | 400.233 | 4,03× | 14,94% | 0,75% |
| Buy & Hold | 0 (0 / 0) | 0,00 | 0 | 0,00× | 0,70% | 1,60% |
| SMA 50/200 | 6 (2 / 4) | 32,23 | 107.433 | 1,16× | 31,39% | 39,29% |
| Bollinger 20/2 | 24 (12 / 12) | 151,26 | 504.200 | 4,92× | 49,06% | 1,44% |
| Equal Weight 63d | 15 (9 / 6) | 5,11 | 17.033 | 0,18× | 0,70% | 1,58% |
| Mínima Variância 252/63 | 14 (8 / 6) | 27,94 | 93.133 | 0,97× | 0,78% | 1,65% |

## 3. Notas metodológicas

- **Curva de patrimônio.** Para cada carteira, 154 pontos: R$ 100.000,00 no fechamento de referência da cesta inicial (02/04/2026) seguidos dos 153 patrimônios de fechamento do `daily.csv` (posições a mercado + caixa + recebíveis). Daí resultam 153 retornos diários simples; dias sem operação (retorno da carteira parada ou em caixa) permanecem na série.
- **Sharpe.** Definição congelada `H2_SCIENTIFIC_SHARPE_DEFINITION_V1` de `src/backtesting/metrics.py` (função `scientific_sharpe`): `mean(r − rf/252) / std(r, ddof=1) · √252`, com **rf = 0** (taxa livre de risco nula, parâmetro do protocolo). A definição foi congelada para o protocolo H2; aqui é aplicada ao replay apenas para manter a mesma fórmula, sem que o replay seja um teste de H2. Como o caixa do replay não é remunerado, rf = 0 é coerente com a contabilidade da simulação, mas ignora o custo de oportunidade de uma taxa de juros positiva, que reduziria todos os índices.
- **Erro-padrão aproximado do Sharpe.** `√((1 + SR_d²/2)/n) · √252`, com SR_d diário e n = 153, supondo retornos iid (Lo, 2002). Fica em torno de 1,3 para todas as carteiras: diferenças de Sharpe dessa ordem não se distinguem de ruído amostral nesta janela. <!-- TODO(redator): incluir Lo (2002) em references.bib se a nota for para o texto. -->
- **Sortino.** `sortino_ratio` de `src/backtesting/metrics.py`, rf = 0 e MAR = 0; são defaults técnicos do módulo, não política científica congelada.
- **Retorno anualizado e volatilidade.** `annualized_return` (composto, 252/153) e `annualized_volatility` (desvio amostral × √252). A anualização de 153 pregões é extrapolação aritmética; serve só para comparar escalas.
- **Máximo drawdown.** `max_drawdown` e `max_drawdown_duration` de `src/backtesting/metrics.py`; as datas de pico e vale (não existentes no módulo) são o fechamento de maior patrimônio anterior ao vale e o fechamento de menor drawdown. A duração conta pregões consecutivos abaixo do pico anterior (qualquer episódio, não necessariamente o do máximo drawdown).
- **Operações.** Contadas como mudanças de quantidade de um ativo entre estados diários consecutivos, partindo da cesta inicial (855 BBAS3, 461 ITUB4, 415 PETR4, 239 VALE3, 397 WEGE3); a montagem da cesta não entra. Os totais conferem com o documento mestre para as oito carteiras.
- **Custos e giro.** Custo = último valor acumulado da coluna `costs`. O volume negociado é estimado por custo / 0,03% (taxa única do replay); o arredondamento do custo ao centavo admite erro de até ~R$ 16,67 por operação. Giro = volume estimado / patrimônio médio dos 153 fechamentos. Não é o `turnover` legado de `metrics.py`, que mede variação de pesos e exigiria preços diários.
- **Caixa.** `cash / equity` em cada fechamento (recebíveis fora do caixa).

## 4. Verificações executadas (asserts do script)

- 918 estados diários por versão (153 pregões × 6 carteiras), mesmas 153 sessões nas três versões; status apenas `COMPLETED` ou `NO_ANALYSIS`.
- Cinco referências idênticas nas três versões em sessão, caixa, custos, patrimônio, posições e recebíveis. A única diferença textual entre os arquivos é o campo `status`: os pregões `NO_ANALYSIS` da Multiagentes (v1: nenhum; v2: 26/06; v3: 01/07, 01/09, 01/10, 02/10) são registrados com esse status nas seis carteiras da campanha, sem afetar os valores das referências.
- Patrimônio final, compras, vendas e custos das oito carteiras iguais aos do documento mestre (§5.1); caixa médio e de fechamento e patrimônio mínimo e máximo das três Multiagentes iguais aos do documento mestre.

## 5. Figuras e tabelas geradas

- `tcc2/overleaf/chapters/tabelas/metricas-replay.tex`: duas tabelas booktabs (`tab:replay-risco`, `tab:replay-operacoes`).
- `tcc2/overleaf/figures/replay-patrimonio.tex`, `replay-drawdown.tex`, `replay-caixa.tex` (pgfplots, dados em `tcc2/overleaf/figures/replay-series.csv`; rótulos `fig:replay-patrimonio`, `fig:replay-drawdown`, `fig:replay-caixa`). Exigem `\usepackage{pgfplots}` no preâmbulo de `main.tex`. matplotlib não está instalado no ambiente; por isso as figuras são compiladas pelo LaTeX.
