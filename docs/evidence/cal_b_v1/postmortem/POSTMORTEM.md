# CAL-B v1 — post-mortem do excesso de MANTER

**CAL-B1 CONSUMED — NOW DEVELOPMENT EVIDENCE**

Diagnóstico mecânico, só com artefatos selados (selos conferidos) e decisões/traces já publicados das fases anteriores. Zero chamadas ao provedor, zero preço/retorno posterior a `t`, zero Validation/Final, zero mudança de configuração, prompt ou código científico. Nada aqui seleciona parâmetro ou performance.

## 1. Tabela por âncora

| Anchor | 8 features (canônicas) | Votes C/V/M | Consensus | Mean conf. winner | Final technical | Final cause |
|---|---|---|---|---:|---|---|
| 2018-07-19 | sma50_gap=-0.022145, sma200_gap=-0.009971, bb_upper_gap=-0.050875, bb_lower_gap=0.214625, bb_width=0.245408, rsi=56.218315, macd_ratio=0.008158, macd_signal_ratio=-0.004667 | 1/0/4 | yes | 0.59 | MANTER | TECH_EXPLICIT_HOLD |
| 2019-03-07 | sma50_gap=0.059142, sma200_gap=0.23845, bb_upper_gap=-0.046012, bb_lower_gap=0.075712, bb_width=0.119943, rsi=56.449271, macd_ratio=0.016193, macd_signal_ratio=0.019067 | 0/0/5 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |
| 2019-10-15 | sma50_gap=0.052567, sma200_gap=0.046737, bb_upper_gap=-0.017174, bb_lower_gap=0.058335, bb_width=0.073987, rsi=59.752351, macd_ratio=0.005347, macd_signal_ratio=0.005344 | 0/0/5 | yes | 0.64 | MANTER | TECH_EXPLICIT_HOLD |
| 2020-06-01 | sma50_gap=0.212877, sma200_gap=-0.173738, bb_upper_gap=-0.019895, bb_lower_gap=0.224381, bb_width=0.221617, rsi=64.903843, macd_ratio=0.038201, macd_signal_ratio=0.029813 | 0/0/5 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |
| 2021-01-13 | sma50_gap=0.128419, sma200_gap=0.345001, bb_upper_gap=-0.073469, bb_lower_gap=0.113549, bb_width=0.183343, rsi=57.087248, macd_ratio=0.043306, macd_signal_ratio=0.044415 | 0/0/5 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |
| 2021-08-20 | sma50_gap=0.002653, sma200_gap=0.099031, bb_upper_gap=-0.049954, bb_lower_gap=0.074367, bb_width=0.122822, rsi=51.64421, macd_ratio=0.009052, macd_signal_ratio=0.007778 | 1/0/4 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |
| 2022-03-31 | sma50_gap=0.026464, sma200_gap=0.238282, bb_upper_gap=-0.02125, bb_lower_gap=0.113562, bb_width=0.128863, rsi=57.571627, macd_ratio=0.001056, macd_signal_ratio=-0.00379 | 2/0/3 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |
| 2022-11-04 | sma50_gap=-0.122889, sma200_gap=0.093176, bb_upper_gap=-0.247807, bb_lower_gap=-0.009856, bb_width=0.27314, rsi=33.557226, macd_ratio=-0.019806, macd_signal_ratio=0.006529 | 5/0/0 | yes | 0.65 | COMPRA | RISK_VETO_VOLATILITY |
| 2023-06-15 | sma50_gap=0.236734, sma200_gap=0.305407, bb_upper_gap=-0.020534, bb_lower_gap=0.322715, bb_width=0.298194, rsi=75.965752, macd_ratio=0.05463, macd_signal_ratio=0.042322 | 0/5/0 | yes | 0.792 | VENDA | ACTION_SELL |
| 2024-01-22 | sma50_gap=0.04573, sma200_gap=0.262542, bb_upper_gap=-0.037498, bb_lower_gap=0.031457, bb_width=0.069164, rsi=55.387471, macd_ratio=0.014173, macd_signal_ratio=0.018815 | 0/0/5 | yes | 0.65 | MANTER | TECH_EXPLICIT_HOLD |

## 2. Cinco votos por âncora (texto original preservado)

### 2018-07-19 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.58 | O RSI está em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal, sugerindo leve momentum de alta. No entanto, o preço rompeu acima da Banda de Bollinger superior (bb_upper_gap negativo) enquanto permanece ligeiramente abaixo das médias móveis de 50 e 200 períodos, indicando resistência estrutural e risco de exaustão a curto prazo. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | MANTER | 0.55 | O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo potencial sobrecompra, mas o RSI permanece em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal. Além disso, as médias móveis de 50 e 200 períodos estão ligeiramente acima do preço, indicando sinais mistos e consolidação. | MIXED_SIGNALS, NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | MANTER | 0.65 | O RSI está em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal, sugerindo recuperação. No entanto, o preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo) enquanto permanece abaixo das médias de 50 e 200 períodos, indicando resistência estrutural e risco de correção imediata. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | COMPRA | 0.65 | O preço rompeu a banda superior de Bollinger (bb_upper_gap negativo) com RSI em zona construtiva (56.22) e MACD superando a linha de sinal (macd_ratio positivo com spread favorável), indicando momentum de alta a despeito da proximidade com as médias móveis. | OTHER | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.58 | O RSI em 56.22 indica neutralidade, enquanto o preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), sugerindo potencial sobrecompra local. Contudo, o MACD mostra momentum positivo cruzando acima do sinal, contrastado por preços ainda abaixo das médias móveis de 50 e 200 períodos. Os sinais são mistos, recomendando manutenção de posição. | MIXED_SIGNALS, NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2019-03-07 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | O preço negocia acima das médias móveis (SMA50 e SMA200), indicando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), o RSI está neutro-alto em 56,45 e o MACD cruzou abaixo da linha de sinal, sugerindo perda temporária de força compradora e consolidação. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | MANTER | 0.65 | O ativo mantém tendência de alta estrutural com preços bem acima das médias de 50 e 200 períodos. No entanto, o preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), enquanto o MACD opera abaixo de sua linha de sinal e o RSI está neutro em 56, indicando desaceleração do ímpeto comprador e sugerindo consolidação a curto prazo. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | MANTER | 0.65 | O ativo mantém tendência de alta estrutural (preço acima da SMA 50 e SMA 200), porém o MACD está abaixo de sua linha de sinal indicando perda de momentum no curto prazo. O RSI em 56,45 e o preço próximo à banda superior sugerem consolidação sem gatilho claro de entrada ou saída imediata. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 4 | MANTER | 0.65 | O ativo opera acima das médias móveis (SMA50 e SMA200), indicando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), o MACD opera abaixo da sua linha de sinal apontando perda de momentum e o RSI em 56,45 é neutro, sugerindo consolidação antes de nova entrada. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.65 | O preço opera acima das médias móveis de 50 e 200 períodos, confirmando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), com MACD abaixo da linha de sinal e RSI neutro em 56, indicando perda de momentum e possível consolidação antes de nova entrada. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2019-10-15 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra no curto prazo, apesar do RSI neutro-altista (59.75) e médias móveis alinhadas positivamente. Como o MACD está estável e colado à sua linha de sinal sem aceleração clara, a recomendação prudente é MANTER. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | MANTER | 0.65 | O preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando potencial sobrecompra no curto prazo, apesar de RSI em 59.75 e médias móveis (SMA50 e SMA200) confirmarem tendência de alta moderada. O MACD está neutro em relação ao seu sinal, sugerindo cautela e manutenção de posição. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | MANTER | 0.65 | O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra a curto prazo, apesar das tendências de alta evidenciadas pelas médias móveis (sma50 e sma200 positivas) e MACD neutro/positivo. O RSI em 59,75 não confirma exaustão extrema, recomendando cautela e manutenção. | INSUFFICIENT_CONFIRMATION, NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | MANTER | 0.65 | O preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando potencial sobrecompra a curto prazo, apesar das tendências de médio e longo prazo positivas (sma50_gap e sma200_gap acima de 0). O RSI em 59.75 e o MACD praticamente neutro em relação ao sinal sugerem consolidação ou desaceleração do ímpeto comprador, recomendando cautela antes de nova entrada. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.6 | O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo condição de sobrecompra no curto prazo, apesar das médias móveis e MACD manterem viés altista moderado com RSI equilibrado em 59,75. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2020-06-01 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | O preço rompeu ligeiramente a banda superior de Bollinger com RSI em 64.9, indicando força, mas aproximando-se de sobrecompra. Apesar do MACD positivo e acima do sinal e forte gap sobre a SMA50, a cotação ainda opera significativamente abaixo da SMA200 (-17,37%), sugerindo cautela em uma tendência primária de baixa. | OVERBOUGHT_OVERSOLD_CONFLICT, GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | MANTER | 0.65 | O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), sinalizando sobrecompra em conjunto com RSI elevado em 64.9. Apesar do momentum positivo pelo MACD e SMA50, a tendência de longo prazo (SMA200) permanece negativa com gap de -17,37%, sugerindo risco de exaustão do movimento recente. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | MANTER | 0.65 | O preço rompeu a banda superior de Bollinger (bb_upper_gap negativo) com RSI moderadamente alto em 64.9, indicando esticamento no curto prazo, apesar do momentum positivo de MACD e SMA50. A distância negativa em relação à SMA200 sugere contra-tendência de longo prazo, recomendando cautela. | GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | MANTER | 0.65 | O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), sinalizando sobrecompra no curto prazo, embora o RSI permaneça em patamar razoável (64.90) e o MACD mantenha cruzamento altista. Além disso, há divergência entre as médias móveis, com gap positivo forte na SMA50 e negativo na SMA200, sugerindo consolidação ou pullback antes de continuação da tendência. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.65 | O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo) com RSI moderadamente alto em 64.9, indicando estiramento no curto prazo, apesar do momentum positivo de MACD e forte distância acima da SMA50; no entanto, o ativo ainda opera bem abaixo da SMA200 (-17.37%), recomendando cautela antes de novas entradas. | GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2021-01-13 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | Preço bem acima das médias de longo prazo indicando forte tendência de alta prévia, porém o MACD está ligeiramente abaixo de sua linha de sinal e o RSI em 57 pontos sugere perda de momentum imediato, sem configurar sobrevenda ou sobrecompra. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 2 | MANTER | 0.65 | O ativo opera em forte tendência de alta acima das médias (sma200_gap em 34,5% e sma50_gap em 12,8%), porém o MACD está ligeiramente abaixo de sua linha de sinal e o RSI em 57 indica perda de momentum sem sobrevenda ou sobrecompra claras, recomendando manutenção de posição. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 3 | MANTER | 0.65 | O preço se mantém em forte tendência de alta acima das médias de 50 e 200 períodos, porém negocia acima da banda superior de Bollinger com o MACD cruzando ligeiramente abaixo da linha de sinal, sugerindo exaustão de curto prazo sem reversão confirmada. | INSUFFICIENT_CONFIRMATION, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | MANTER | 0.65 | O ativo opera em forte tendência de alta acima das médias (sma200_gap em 34,5% e sma50_gap em 12,8%), porém negocia acima da banda superior de Bollinger (bb_upper_gap negativo) com leve divergência no MACD cruzando abaixo da linha de sinal, recomendando manutenção de posição sem nova entrada imediata. | TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.65 | O ativo mantém tendência de alta estrutural (preço acima das médias de 50 e 200 períodos), porém opera acima da banda superior de Bollinger com o RSI em 57 e o MACD cruzando ligeiramente abaixo da linha de sinal, indicando desaceleração do momentum e sugerindo cautela antes de novas entradas. | GENERIC_UNCERTAINTY, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2021-08-20 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | O RSI está neutro em 51.64 e o preço negocia dentro das Bandas de Bollinger sem extremos claros. Apesar da tendência de alta indicada pelo afastamento das médias (sma200_gap positivo) e MACD ligeiramente acima do sinal, a proximidade com a SMA 50 e a ausência de momentum forte sugerem consolidação no momento. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 2 | COMPRA | 0.68 | O ativo mantém tendência de alta estrutural com preço acima das médias móveis (SMA50 e SMA200 positivas), MACD operando acima de sua linha de sinal em território positivo e RSI em patamar neutro (51.64), demonstrando espaço para continuidade sem exaustão imediata. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT | — |
| 3 | MANTER | 0.65 | O RSI está em zona neutra (51.64) e o preço opera muito próximo à média móvel de 50 períodos (gap de 0.26%). Embora o MACD esteja ligeiramente acima do sinal e a tendência de longo prazo seja positiva (sma200_gap de 9.9%), a proximidade com a banda superior de Bollinger sugere consolidação momentânea sem gatilho claro de entrada ou saída. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 4 | MANTER | 0.65 | O RSI está em zona neutra (51.64) e o preço opera muito próximo à SMA 50 (gap de 0.26%). Embora o MACD apresente leve sinal altista acima da linha de sinal e a tendência de longo prazo seja positiva (SMA 200 gap de 9.9%), a posição do preço dentro das bandas de Bollinger e a falta de momentum forte sugerem consolidação no curto prazo. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 5 | MANTER | 0.65 | O RSI está neutro em 51.64 e o preço negocia muito próximo à SMA 50. Apesar do MACD apresentar ligeiro viés comprador e o ativo se manter acima da SMA 200, a proximidade da banda superior de Bollinger e a falta de momentum forte sugerem consolidação momentânea. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |

### 2022-03-31 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | COMPRA | 0.68 | O ativo opera acima das médias móveis de 50 e 200 períodos com tendência de alta estabelecida. O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), acompanhado de MACD positivo cruzando acima de sua linha de sinal e RSI saudável em 57.57, indicando continuidade do momentum comprador sem sobrecompra extrema. | OVERBOUGHT_OVERSOLD_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | MANTER | 0.65 | O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo extensão de curto prazo, embora a tendência permaneça altista acima das médias de 50 e 200 períodos. Com o RSI neutro-altista em 57.57 e o MACD iniciando cruzamento positivo sobre o sinal mas ainda próximo de zero, a relação risco-retorno favorece a manutenção da posição até uma confirmação mais clara de rompimento. | INSUFFICIENT_CONFIRMATION, NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | COMPRA | 0.72 | O preço rompeu levemente acima da banda superior de Bollinger com bandas moderadamente alargadas, operando acima das SMAs de 50 e 200 períodos em forte tendência de alta. O MACD cruzou acima da linha de sinal em território positivo e o RSI em 57.57 indica momento favorável com espaço para valorização. | TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | MANTER | 0.65 | O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra a curto prazo, apesar da tendência de alta mais ampla confirmada pelas médias móveis (sma50_gap e sma200_gap positivos). O RSI em 57.57 e o MACD próximo ao sinal sem divergência extrema sugerem consolidação antes de nova definição direcional. | NEUTRAL_INDICATORS, OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | MANTER | 0.65 | O preço rompeu levemente acima da Banda de Bollinger superior (bb_upper_gap negativo), indicando potencial sobrecompra a curto prazo, apesar da tendência de alta mais ampla confirmada pelas médias móveis (sma50_gap e sma200_gap positivos). O RSI em 57.57 e o MACD próximo da linha de sinal sugerem continuidade moderada sem momentum explosivo ou exaustão imediata, recomendando manutenção de posição. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2022-11-04 — COMPRA (RISK_VETO_VOLATILITY)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | COMPRA | 0.65 | O ativo rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo esteja negativo (sma50_gap em -12.29%), a tendência de longo prazo ainda é de alta (sma200_gap em +9.32%), indicando oportunidade de repique/reversão à média. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 2 | COMPRA | 0.65 | O ativo rompeu ligeiramente abaixo da Banda de Bollinger inferior (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo esteja negativo (sma50_gap em -12.29%), o ativo ainda se sustenta acima da tendência de longo prazo (sma200_gap positivo de +9.32%), sugerindo oportunidade de repique/retorno à média. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 3 | COMPRA | 0.65 | O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Apesar da tendência de curto prazo em baixa (sma50_gap negativo), o ativo permanece acima da SMA 200 (+9.3%) e o MACD apresenta sinal de desaceleração/reversão altista iminente (macd_signal_ratio positivo), indicando oportunidade de repique. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 4 | COMPRA | 0.65 | O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo (sma50_gap e macd_ratio) seja de baixa, o ativo mantém suporte sobre a tendência estrutural de alta (sma200_gap positivo em 9.32%), sugerindo uma oportunidade de reversão à média com a recuperação do MACD em direção ao sinal. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |
| 5 | COMPRA | 0.65 | O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Apesar do momentum de curto prazo em baixa (sma50_gap negativo), a tendência de longo prazo permanece positiva (sma200_gap positivo de 9.3%), sugerindo uma oportunidade de reversão à média. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | — |

### 2023-06-15 — VENDA (ACTION_SELL)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | VENDA | 0.78 | O ativo apresenta forte sobrecompra indicada pelo RSI em 75.97 e pelo rompimento da banda superior de Bollinger (bb_upper_gap negativo). Além disso, os afastamentos das médias móveis (sma50_gap e sma200_gap superiores a 23% e 30%) sugerem estiramento excessivo e alta probabilidade de correção técnica a curto prazo. | OVERBOUGHT_OVERSOLD_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 2 | VENDA | 0.8 | O ativo apresenta forte sobrecompra com RSI próximo de 76, rompimento da banda superior de Bollinger (bb_upper_gap negativo) e expressivo afastamento das médias móveis de 50 e 200 períodos, indicando alta probabilidade de correção técnica iminente. | OVERBOUGHT_OVERSOLD_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 3 | VENDA | 0.78 | O ativo apresenta forte condição de sobrecompra com RSI próximo a 76 e o preço rompendo acima da Banda de Bollinger superior (bb_upper_gap negativo). Além disso, os afastamentos das médias de 50 e 200 períodos estão excessivamente esticados, indicando probabilidade elevada de exaustão do movimento de alta e correção técnica iminente. | OVERBOUGHT_OVERSOLD_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 4 | VENDA | 0.8 | O ativo apresenta condições extremas de sobrecompra, com RSI acima de 75 e preço rompendo a banda superior de Bollinger (bb_upper_gap negativo). Além disso, os afastamentos das médias móveis (SMA50 e SMA200) estão excessivamente esticados, indicando alta probabilidade de correção técnica iminente. | OVERBOUGHT_OVERSOLD_CONFLICT, TREND_MOMENTUM_CONFLICT | **FALSE** (bb_upper_gap < 0) |
| 5 | VENDA | 0.8 | O ativo apresenta forte sobrecompra com RSI próximo a 76, cotação rompendo acima da Banda de Bollinger superior (bb_upper_gap negativo) e expressivo afastamento das médias móveis de 50 e 200 períodos, indicando risco iminente de correção técnica. | OVERBOUGHT_OVERSOLD_CONFLICT | **FALSE** (bb_upper_gap < 0) |

### 2024-01-22 — MANTER (TECH_EXPLICIT_HOLD)

| Analyst | Signal | Confidence | Justification | Labels | Upper-band breach claim |
|---:|---|---:|---|---|---|
| 1 | MANTER | 0.65 | O ativo mantém tendência de alta estrutural indicada pelos gaps positivos contra a SMA50 (4,57%) e SMA200 (26,25%), porém o MACD está abaixo da linha de sinal e o RSI em 55,39 mostra neutralidade de momentum dentro das bandas de Bollinger, sugerindo consolidação temporária. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 2 | MANTER | 0.65 | O ativo opera em tendência de alta estrutural (afastado das médias de 50 e 200 períodos), porém o MACD está abaixo de sua linha de sinal indicando perda de momentum e o RSI em 55,38 aponta neutralidade dentro das bandas de Bollinger. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 3 | MANTER | 0.65 | O ativo opera acima das médias móveis (SMA 50 e SMA 200) e dentro das Bandas de Bollinger, com RSI neutro em 55.39. Contudo, o MACD está abaixo da sua linha de sinal, indicando perda de momento no curto prazo, justificando uma postura de manutenção. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 4 | MANTER | 0.65 | O ativo mantém tendência de alta de longo e médio prazo com sma200_gap positivo (+26,25%) e sma50_gap (+4,57%). O RSI está neutro em 55,39 e os preços operam no centro das bandas de Bollinger. No entanto, o MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), sugerindo desaceleração do momentum e ausência de gatilho claro de entrada ou saída imediata. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |
| 5 | MANTER | 0.65 | O ativo opera acima das médias móveis (SMA 50 e SMA 200 positivas), confirmando tendência de alta no longo prazo. Contudo, o MACD está abaixo da linha de sinal indicando perda de momentum recente, enquanto o RSI em 55,39 e o preço dentro das bandas de Bollinger sugerem neutralidade no curto prazo. | NEUTRAL_INDICATORS, TREND_MOMENTUM_CONFLICT | — |

## 3. Força do HOLD

| Classe | Âncoras |
|---|---:|
| 5/5 HOLD | 5 |
| 4/5 HOLD | 2 |
| 3/5 HOLD | 1 |

## 4. Minoria não-HOLD nas âncoras MANTER

| Anchor | HOLD | BUY | SELL |
|---|---:|---:|---:|
| 2018-07-19 | 4 | 1 | 0 |
| 2019-03-07 | 5 | 0 | 0 |
| 2019-10-15 | 5 | 0 | 0 |
| 2020-06-01 | 5 | 0 | 0 |
| 2021-01-13 | 5 | 0 | 0 |
| 2021-08-20 | 4 | 1 | 0 |
| 2022-03-31 | 3 | 2 | 0 |
| 2024-01-22 | 5 | 0 | 0 |

## 5. Controle clássico (indicator-family-matched) nas mesmas datas

Só barras até close(t); não é avaliação de performance. As famílias são **eventos de cruzamento t-1→t**: 0 significa "nenhum cruzamento hoje", não "estado neutro".

| Anchor | SMA | BB | RSI | MACD | Score | Classical action | LLM technical |
|---|---:|---:|---:|---:|---:|---|---|
| 2018-07-19 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |
| 2019-03-07 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |
| 2019-10-15 | 0 | 0 | 0 | 1 | 1 | COMPRA | MANTER |
| 2020-06-01 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |
| 2021-01-13 | 0 | 0 | 0 | -1 | -1 | VENDA | MANTER |
| 2021-08-20 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |
| 2022-03-31 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |
| 2022-11-04 | 0 | 1 | 0 | 0 | 1 | COMPRA | COMPRA |
| 2023-06-15 | 0 | 0 | 0 | 0 | 0 | MANTER | VENDA |
| 2024-01-22 | 0 | 0 | 0 | 0 | 0 | MANTER | MANTER |

## 6. Sinais das features (descritivo; sem pesos, sem score)

| Anchor | sma50_gap | sma200_gap | Bollinger | %B | RSI | macd_ratio | macd_signal_ratio | macd−signal |
|---|---|---|---|---:|---|---|---|---|
| 2018-07-19 | - | - | INSIDE | 0.7673 | 56.22 NEUTRAL_UPPER(50-70) | + | - | + |
| 2019-03-07 | + | + | INSIDE | 0.5934 | 56.45 NEUTRAL_UPPER(50-70) | + | + | - |
| 2019-10-15 | + | + | INSIDE | 0.7593 | 59.75 NEUTRAL_UPPER(50-70) | + | + | + |
| 2020-06-01 | + | - | INSIDE | 0.9003 | 64.90 NEUTRAL_UPPER(50-70) | + | + | + |
| 2021-01-13 | + | + | INSIDE | 0.5625 | 57.09 NEUTRAL_UPPER(50-70) | + | + | - |
| 2021-08-20 | + | + | INSIDE | 0.5683 | 51.64 NEUTRAL_UPPER(50-70) | + | + | + |
| 2022-03-31 | + | + | INSIDE | 0.8245 | 57.57 NEUTRAL_UPPER(50-70) | + | - | + |
| 2022-11-04 | - | + | BELOW_LOWER | -0.0312 | 33.56 NEUTRAL_LOWER(30-50) | - | + | - |
| 2023-06-15 | + | + | INSIDE | 0.9209 | 75.97 OVERBOUGHT(>70) | + | + | + |
| 2024-01-22 | + | + | INSIDE | 0.4391 | 55.39 NEUTRAL_UPPER(50-70) | + | + | - |

sma50_gap, sma200_gap, macd_ratio e macd−signal com o mesmo sinal: 4/10 (2019-10-15, 2021-08-20, 2022-03-31, 2023-06-15).

## 7. Leitura da banda superior (achado não previsto na taxonomia)

`bb_upper_gap = close/upper − 1` (`src/agents/features.py`): negativo = preço **abaixo** da banda superior. O prompt técnico transmite só os nomes e valores das 8 razões, sem definição nem convenção de sinal. Regra textual de afirmação de rompimento/posição acima da banda superior: `(acima|ultrapass|romp)[^.;,]{0,45}superior` (todas as ocorrências da CAL-B conferidas manualmente).

- CAL-B v1: `bb_upper_gap < 0` nas 10 âncoras; afirmações falsas de rompimento em 32/50 votos, 27/40 nas âncoras HOLD e 24/36 votos MANTER.

| Fase | votos técnicos | preço abaixo da banda | afirmações falsas | taxa | preço acima da banda | afirmações verdadeiras | MANTER c/ afirmação falsa | MANTER sem afirmação |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Hardening (H, R=5) | 300 | 275 | 90 | 0.3273 | 25 | 0 | 0.7667 | 0.6378 |
| B0 (H, R=1) | 60 | 55 | 18 | 0.3273 | 5 | 0 | 0.7222 | 0.6757 |
| CAL-A | 300 | 270 | 116 | 0.4296 | 30 | 8 | 0.3793 | 0.6948 |
| Sequential Dev | 1905 | 1815 | 669 | 0.3686 | 90 | 12 | 0.3513 | 0.8316 |
| Stress | 2985 | 2700 | 988 | 0.3659 | 285 | 28 | 0.4818 | 0.6297 |
| CAL-B v1 | 50 | 50 | 32 | 0.64 | 0 | 0 | 0.75 | 0.6667 |

## 8. Taxonomia das justificativas (votos das 8 âncoras HOLD, múltiplos rótulos)

| Label | Votos |
|---|---:|
| TREND_MOMENTUM_CONFLICT | 37 |
| NEUTRAL_INDICATORS | 26 |
| OVERBOUGHT_OVERSOLD_CONFLICT | 18 |
| GENERIC_UNCERTAINTY | 8 |
| INSUFFICIENT_CONFIRMATION | 3 |
| MIXED_SIGNALS | 2 |
| OTHER | 1 |

Regras: `MIXED_SIGNALS` = `mist|divergen|conflit|contradit|amb[ií]gu|sinais opostos|n[ãa]o h[áa] (?:um )?consenso`; `INSUFFICIENT_CONFIRMATION` = `confirma[çc][ãa]o|n[ãa]o confirma|sem [^.]{0,25}confirmad|aguard`; `NEUTRAL_INDICATORS` = `neutr|lateral|indefini|sem dire[çc][ãa]o|sem tend[êe]ncia|consolida`; `OVERBOUGHT_OVERSOLD_CONFLICT` = `sobrecompr|sobrevend|exaust`; `GENERIC_UNCERTAINTY` = `incert|cautel|prud[êe]n|indecis|d[úu]vid`; `TREND_MOMENTUM_CONFLICT` = `(tend[êe]ncia|m[ée]dia|sma) & (macd|momentum|rsi|for[çc]a) & (embora|por[ée]m|entretanto|contudo|no entanto|apesar|mas\b|enquanto|todavia)`

## 9. MANTER como default de segurança

- linguagem de segurança/incerteza (`cautel|prud[êe]n|aguard|esperar|confirma[çc][ãa]o|incert|evitar|seguran[çc]a`): 9/36 votos MANTER vs 0/14 votos direcionais;
- visão neutra declarada (`neutr|consolida|lateral|sem gatilho|aus[êe]ncia de gatilho`): 25/36 votos MANTER; nenhuma das duas: 7/36;
- confidence de MANTER exatamente 0.65 em 32/36 votos.

Trechos literais:

- 2019-10-15 #1: “…al sem aceleração clara, a recomendação prudente é MANTER.…”
- 2019-10-15 #2: “…utro em relação ao seu sinal, sugerindo cautela e manutenção de posição.…”
- 2019-10-15 #3: “…confirma exaustão extrema, recomendando cautela e manutenção.…”
- 2019-10-15 #4: “…ração do ímpeto comprador, recomendando cautela antes de nova entrada.…”
- 2020-06-01 #1: “…e abaixo da SMA200 (-17,37%), sugerindo cautela em uma tendência primária de baixa.…”
- 2020-06-01 #3: “…-tendência de longo prazo, recomendando cautela.…”
- 2020-06-01 #5: “…baixo da SMA200 (-17.37%), recomendando cautela antes de novas entradas.…”
- 2021-01-13 #5: “…o desaceleração do momentum e sugerindo cautela antes de novas entradas.…”
- 2022-03-31 #2: “…avorece a manutenção da posição até uma confirmação mais clara de rompimento.…”

## 10. Confidence por sinal (descritivo; não entra em sizing nem seleção)

| Signal | n | média | mediana | min | max |
|---|---:|---:|---:|---:|---:|
| COMPRA | 9 | 0.6644 | 0.65 | 0.65 | 0.72 |
| VENDA | 5 | 0.792 | 0.8 | 0.78 | 0.8 |
| MANTER | 36 | 0.6419 | 0.65 | 0.55 | 0.65 |

## 11. Consenso e N contrafactual (só os 5 votos existentes)

- `TECH_NO_MAJORITY` = 0; menor número de votos do vencedor = 3/5; reduzir o limiar de 3/5 mudaria alguma decisão: não.

| Anchor | Votes C/V/M | primeiros 3 | primeiros 4 | todos 5 |
|---|---|---|---|---|
| 2018-07-19 | 1/0/4 | MANTER | MANTER | MANTER |
| 2019-03-07 | 0/0/5 | MANTER | MANTER | MANTER |
| 2019-10-15 | 0/0/5 | MANTER | MANTER | MANTER |
| 2020-06-01 | 0/0/5 | MANTER | MANTER | MANTER |
| 2021-01-13 | 0/0/5 | MANTER | MANTER | MANTER |
| 2021-08-20 | 1/0/4 | MANTER | MANTER | MANTER |
| 2022-03-31 | 2/0/3 | COMPRA | NO_MAJORITY | MANTER |
| 2022-11-04 | 5/0/0 | COMPRA | COMPRA | COMPRA |
| 2023-06-15 | 0/5/0 | VENDA | VENDA | VENDA |
| 2024-01-22 | 0/0/5 | MANTER | MANTER | MANTER |

## 12. Contribuição de Risk/Portfolio

- TECHNICAL INACTIVITY: 8 âncoras (2018-07-19, 2019-03-07, 2019-10-15, 2020-06-01, 2021-01-13, 2021-08-20, 2022-03-31, 2024-01-22): consenso MANTER, Risk AUTO_APPROVE, Portfolio não chamado.
- RISK SUPPRESSION: 1 (2022-11-04): COMPRA 5/5 vetada pela regra dura de volatilidade antes do LLM de risco.
- HOLDs com chamada de Risk/Portfolio LLM: 0.

## 13. Taxa de HOLD por fase (sem performance)

| Fase | decisões | TECH_EXPLICIT_HOLD | NO_MAJORITY | votos MANTER | votos COMPRA | votos VENDA | HOLD 5/5, 4/5, 3/5 |
|---|---:|---:|---:|---:|---:|---:|---|
| Hardening H_syn (R=5) | 40 | 0.55 | 0.0 | 0.545 | 0.25 | 0.205 | [18, 2, 2] |
| Hardening H_real (R=5) | 20 | 0.75 | 0.0 | 0.78 | 0.22 | 0.0 | [15, 0, 0] |
| B0 (H, R=1) | 12 | 0.6667 | 0.0 | 0.6333 | 0.25 | 0.1167 | [7, 0, 1] |
| CAL-A (20 anchors x R=3, config 1) | 60 | 0.4667 | 0.0 | 0.5033 | 0.2033 | 0.2933 | [22, 2, 4] |
| Sequential Dev (127 sessions x R=3, D01) | 381 | 0.6273 | 0.0026 | 0.6409 | 0.2525 | 0.1066 | [206, 14, 19] |
| Stress (4 windows x R=3) | 597 | 0.5226 | 0.0017 | 0.533 | 0.2633 | 0.2037 | [250, 30, 32] |
| CAL-B v1 (10 anchors x R=1) | 10 | 0.8 | 0.0 | 0.72 | 0.18 | 0.1 | [5, 2, 1] |

## 14. Diagnóstico

**PRIMARY_DIAGNOSIS = E — MIXED**, com um mecanismo dominante identificado:
um defeito de **semântica de feature** no contrato do prompt técnico, que se
soma a neutralidade real de parte dos estados e a linguagem de cautela. C e D
estão descartados.

Componentes, em ordem de peso da evidência:

1. **Leitura errada de `bb_upper_gap` (contrato do prompt sub-especificado).**
   Nas 10 âncoras o preço está abaixo da banda superior, mas 27 dos 40 votos
   das âncoras HOLD (24/36 votos MANTER) afirmam que o preço "rompeu/ultrapassou
   a banda superior" e usam essa sobrecompra inexistente como contra-argumento
   à tendência de alta. O erro não é da CAL-B: ocorre em 33–43% dos votos com o
   preço abaixo da banda em todas as fases anteriores, e quase nunca há
   afirmação correta quando o preço está de fato acima da banda. O prompt
   transmite os nomes das 8 razões sem definição nem convenção de sinal. Das
   3 âncoras HOLD em que SMA50, SMA200, MACD e MACD − sinal têm o mesmo sinal
   (2019-10-15, 2021-08-20, 2022-03-31), em duas (2019-10-15 e 2022-03-31)
   todos os 5 votos citam o rompimento falso; a terceira (2021-08-20,
   sma50_gap 0.0027, RSI 51.6) justifica MANTER por neutralidade.
2. **Neutralidade/conflito real em parte dos estados (B parcial).** RSI entre
   51.6 e 64.9 nas 8 âncoras HOLD; em 5 das 8, o sinal da tendência (SMA) e o
   do momentum (MACD − sinal) discordam (2018-07-19, 2019-03-07, 2020-06-01,
   2021-01-13, 2024-01-22). 2021-08-20 e 2024-01-22 não citam o rompimento
   falso e justificam MANTER por neutralidade/consolidação. O controle clássico
   não ajuda a separar: é de eventos de cruzamento e dá 0 em 6 das 8 âncoras
   HOLD.
3. **MANTER como default de cautela (A parcial).** 9/36 votos MANTER usam
   linguagem de cautela/confirmação (0/14 votos direcionais); 32/36 têm
   confidence exatamente 0.65. A maioria (25/36) declara visão neutra, então a
   evidência de fallback de segurança existe, mas não é o mecanismo principal.

Descartados: **C — ensemble**: 5 das 8 âncoras HOLD são 5/5 e 2 são 4/5; 72%
dos votos individuais são MANTER; nenhum NO_MAJORITY; baixar o limiar não muda
nada; só 2022-03-31 mudaria com os 3 primeiros votos (COMPRA). **D —
Risk/Portfolio**: nenhum dos 8 HOLDs passou por Risk ou Portfolio LLM; a única
supressão de risco (2022-11-04) é o veto duro de volatilidade de uma COMPRA 5/5.

**Salto ou continuação?** Continuação. A taxa de TECH_EXPLICIT_HOLD da CAL-B
(0.80) fica no alto da faixa das fases anteriores (0.47–0.75; H_real 0.75,
Sequential Dev 0.63), e a parcela de votos MANTER (0.72) é próxima da do H_real
(0.78). Ilustração (supõe independência): com a taxa do Sequential Dev, 8+
holds em 10 âncoras teriam probabilidade ≈ 0.22. O gate do Hardening passou
com total_hold_rate 0.633 calculado sobre H, que mistura H_syn (explicit hold
0.55) e H_real (0.75).

## 15. O que esta evidência sustenta

- O excesso de MANTER é **do Technical**, não de Risk/Portfolio nem da
  agregação.
- O Technical v1 lê sistematicamente errado a convenção de sinal de
  `bb_upper_gap`, desde o Hardening, e usa a leitura errada como argumento
  contra entrar.
- Parte dos estados da CAL-B tem conflito real entre tendência e momentum, com
  RSI neutro.
- A CAL-B não foi um salto; a propensão a MANTER já existia em development, e
  o gate do Hardening (sobre H com estados sintéticos) não a capturou.

## 16. O que esta evidência NÃO sustenta

- Que o sistema "deveria" ter negociado nessas datas, ou que mais negociação
  seria melhor: nenhum retorno foi olhado.
- Que corrigir a semântica das features reduziria os HOLDs abaixo de 0.90, ou
  quanto: não houve nova inferência.
- Causalidade entre a leitura errada e o MANTER: a associação é descritiva e
  muda de sentido entre fases (em Hardening, B0 e CAL-B os votos com a
  afirmação falsa são mais vezes MANTER; em CAL-A, Sequential Dev e Stress,
  menos).
- Qualquer escolha de prompt, temperature, thinking, N ou limiar.
- As taxonomias por regra textual são aproximações; o texto original está
  preservado acima para conferência.

## 17. Classe mínima de defeito recomendada

**TECHNICAL PROMPT CONTRACT — FEATURE SEMANTICS UNDER-SPECIFIED.** O prompt
técnico entrega 8 razões adimensionais sem definição nem convenção de sinal, e
o modelo interpreta pelo menos uma delas (`bb_upper_gap`) ao contrário de forma
sistemática. É defeito objetivo, detectável sem resultado financeiro (a
afirmação contradiz o dado fornecido), e a classe de correção mínima é
documentar no contrato o significado e o sinal de cada feature. O objetivo
dessa correção é leitura correta do dado, não aumentar a taxa de negociação.
"Conservadorismo do prompt" fica como fator secundário a reavaliar depois da
correção, não como alvo de tuning. O texto exato não é proposto aqui.
