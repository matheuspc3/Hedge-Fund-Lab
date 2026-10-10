# CAL-B — pacote comportamental (sem resultado financeiro)

Classifique cada âncora de forma independente em `review/AUTHOR_1.json` ou `review/AUTHOR_2.json`:
`material_hallucination` e `rationale_action_coherence` = PASS ou FAIL. Avalie só o texto visível de
cada estágio contra o prompt daquele estágio. Marcas do pré-filtro léxico são só ponteiros.

## 2018-07-19

Features: `{"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}`

Consenso: `{"vote_counts": {"COMPRA": 1, "MANTER": 4, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.58,
  "justification": "O RSI está em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal, sugerindo leve momentum de alta. No entanto, o preço rompeu acima da Banda de Bollinger superior (bb_upper_gap negativo) enquanto permanece ligeiramente abaixo das médias móveis de 50 e 200 períodos, indicando resistência estrutural e risco de exaustão a curto prazo.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.55,
  "justification": "O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo potencial sobrecompra, mas o RSI permanece em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal. Além disso, as médias móveis de 50 e 200 períodos estão ligeiramente acima do preço, indicando sinais mistos e consolidação.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O RSI está em zona neutra (56.22) e o MACD apresenta cruzamento positivo sobre o sinal, sugerindo recuperação. No entanto, o preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo) enquanto permanece abaixo das médias de 50 e 200 períodos, indicando resistência estrutural e risco de correção imediata.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu a banda superior de Bollinger (bb_upper_gap negativo) com RSI em zona construtiva (56.22) e MACD superando a linha de sinal (macd_ratio positivo com spread favorável), indicando momentum de alta a despeito da proximidade com as médias móveis.",
  "signal": "COMPRA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.214625, "bb_upper_gap": -0.050875, "bb_width": 0.245408, "macd_ratio": 0.008158, "macd_signal_ratio": -0.004667, "rsi": 56.218315, "sma200_gap": -0.009971, "sma50_gap": -0.022145}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.58,
  "justification": "O RSI em 56.22 indica neutralidade, enquanto o preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), sugerindo potencial sobrecompra local. Contudo, o MACD mostra momentum positivo cruzando acima do sinal, contrastado por preços ainda abaixo das médias móveis de 50 e 200 períodos. Os sinais são mistos, recomendando manutenção de posição.",
  "signal": "MANTER"
}
```

## 2019-03-07

Features: `{"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço negocia acima das médias móveis (SMA50 e SMA200), indicando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), o RSI está neutro-alto em 56,45 e o MACD cruzou abaixo da linha de sinal, sugerindo perda temporária de força compradora e consolidação.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo mantém tendência de alta estrutural com preços bem acima das médias de 50 e 200 períodos. No entanto, o preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), enquanto o MACD opera abaixo de sua linha de sinal e o RSI está neutro em 56, indicando desaceleração do ímpeto comprador e sugerindo consolidação a curto prazo.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo mantém tendência de alta estrutural (preço acima da SMA 50 e SMA 200), porém o MACD está abaixo de sua linha de sinal indicando perda de momentum no curto prazo. O RSI em 56,45 e o preço próximo à banda superior sugerem consolidação sem gatilho claro de entrada ou saída imediata.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera acima das médias móveis (SMA50 e SMA200), indicando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), o MACD opera abaixo da sua linha de sinal apontando perda de momentum e o RSI em 56,45 é neutro, sugerindo consolidação antes de nova entrada.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.075712, "bb_upper_gap": -0.046012, "bb_width": 0.119943, "macd_ratio": 0.016193, "macd_signal_ratio": 0.019067, "rsi": 56.449271, "sma200_gap": 0.23845, "sma50_gap": 0.059142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos, confirmando tendência de alta estrutural. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap negativo), com MACD abaixo da linha de sinal e RSI neutro em 56, indicando perda de momentum e possível consolidação antes de nova entrada.",
  "signal": "MANTER"
}
```

## 2019-10-15

Features: `{"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra no curto prazo, apesar do RSI neutro-altista (59.75) e médias móveis alinhadas positivamente. Como o MACD está estável e colado à sua linha de sinal sem aceleração clara, a recomendação prudente é MANTER.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando potencial sobrecompra no curto prazo, apesar de RSI em 59.75 e médias móveis (SMA50 e SMA200) confirmarem tendência de alta moderada. O MACD está neutro em relação ao seu sinal, sugerindo cautela e manutenção de posição.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra a curto prazo, apesar das tendências de alta evidenciadas pelas médias móveis (sma50 e sma200 positivas) e MACD neutro/positivo. O RSI em 59,75 não confirma exaustão extrema, recomendando cautela e manutenção.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera ligeiramente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando potencial sobrecompra a curto prazo, apesar das tendências de médio e longo prazo positivas (sma50_gap e sma200_gap acima de 0). O RSI em 59.75 e o MACD praticamente neutro em relação ao sinal sugerem consolidação ou desaceleração do ímpeto comprador, recomendando cautela antes de nova entrada.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.058335, "bb_upper_gap": -0.017174, "bb_width": 0.073987, "macd_ratio": 0.005347, "macd_signal_ratio": 0.005344, "rsi": 59.752351, "sma200_gap": 0.046737, "sma50_gap": 0.052567}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo condição de sobrecompra no curto prazo, apesar das médias móveis e MACD manterem viés altista moderado com RSI equilibrado em 59,75.",
  "signal": "MANTER"
}
```

## 2020-06-01

Features: `{"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu ligeiramente a banda superior de Bollinger com RSI em 64.9, indicando força, mas aproximando-se de sobrecompra. Apesar do MACD positivo e acima do sinal e forte gap sobre a SMA50, a cotação ainda opera significativamente abaixo da SMA200 (-17,37%), sugerindo cautela em uma tendência primária de baixa.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), sinalizando sobrecompra em conjunto com RSI elevado em 64.9. Apesar do momentum positivo pelo MACD e SMA50, a tendência de longo prazo (SMA200) permanece negativa com gap de -17,37%, sugerindo risco de exaustão do movimento recente.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu a banda superior de Bollinger (bb_upper_gap negativo) com RSI moderadamente alto em 64.9, indicando esticamento no curto prazo, apesar do momentum positivo de MACD e SMA50. A distância negativa em relação à SMA200 sugere contra-tendência de longo prazo, recomendando cautela.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo), sinalizando sobrecompra no curto prazo, embora o RSI permaneça em patamar razoável (64.90) e o MACD mantenha cruzamento altista. Além disso, há divergência entre as médias móveis, com gap positivo forte na SMA50 e negativo na SMA200, sugerindo consolidação ou pullback antes de continuação da tendência.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.224381, "bb_upper_gap": -0.019895, "bb_width": 0.221617, "macd_ratio": 0.038201, "macd_signal_ratio": 0.029813, "rsi": 64.903843, "sma200_gap": -0.173738, "sma50_gap": 0.212877}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço ultrapassou a banda superior de Bollinger (bb_upper_gap negativo) com RSI moderadamente alto em 64.9, indicando estiramento no curto prazo, apesar do momentum positivo de MACD e forte distância acima da SMA50; no entanto, o ativo ainda opera bem abaixo da SMA200 (-17.37%), recomendando cautela antes de novas entradas.",
  "signal": "MANTER"
}
```

## 2021-01-13

Features: `{"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "Preço bem acima das médias de longo prazo indicando forte tendência de alta prévia, porém o MACD está ligeiramente abaixo de sua linha de sinal e o RSI em 57 pontos sugere perda de momentum imediato, sem configurar sobrevenda ou sobrecompra.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera em forte tendência de alta acima das médias (sma200_gap em 34,5% e sma50_gap em 12,8%), porém o MACD está ligeiramente abaixo de sua linha de sinal e o RSI em 57 indica perda de momentum sem sobrevenda ou sobrecompra claras, recomendando manutenção de posição.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço se mantém em forte tendência de alta acima das médias de 50 e 200 períodos, porém negocia acima da banda superior de Bollinger com o MACD cruzando ligeiramente abaixo da linha de sinal, sugerindo exaustão de curto prazo sem reversão confirmada.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera em forte tendência de alta acima das médias (sma200_gap em 34,5% e sma50_gap em 12,8%), porém negocia acima da banda superior de Bollinger (bb_upper_gap negativo) com leve divergência no MACD cruzando abaixo da linha de sinal, recomendando manutenção de posição sem nova entrada imediata.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113549, "bb_upper_gap": -0.073469, "bb_width": 0.183343, "macd_ratio": 0.043306, "macd_signal_ratio": 0.044415, "rsi": 57.087248, "sma200_gap": 0.345001, "sma50_gap": 0.128419}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo mantém tendência de alta estrutural (preço acima das médias de 50 e 200 períodos), porém opera acima da banda superior de Bollinger com o RSI em 57 e o MACD cruzando ligeiramente abaixo da linha de sinal, indicando desaceleração do momentum e sugerindo cautela antes de novas entradas.",
  "signal": "MANTER"
}
```

## 2021-08-20

Features: `{"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}`

Consenso: `{"vote_counts": {"COMPRA": 1, "MANTER": 4, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O RSI está neutro em 51.64 e o preço negocia dentro das Bandas de Bollinger sem extremos claros. Apesar da tendência de alta indicada pelo afastamento das médias (sma200_gap positivo) e MACD ligeiramente acima do sinal, a proximidade com a SMA 50 e a ausência de momentum forte sugerem consolidação no momento.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.68,
  "justification": "O ativo mantém tendência de alta estrutural com preço acima das médias móveis (SMA50 e SMA200 positivas), MACD operando acima de sua linha de sinal em território positivo e RSI em patamar neutro (51.64), demonstrando espaço para continuidade sem exaustão imediata.",
  "signal": "COMPRA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O RSI está em zona neutra (51.64) e o preço opera muito próximo à média móvel de 50 períodos (gap de 0.26%). Embora o MACD esteja ligeiramente acima do sinal e a tendência de longo prazo seja positiva (sma200_gap de 9.9%), a proximidade com a banda superior de Bollinger sugere consolidação momentânea sem gatilho claro de entrada ou saída.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O RSI está em zona neutra (51.64) e o preço opera muito próximo à SMA 50 (gap de 0.26%). Embora o MACD apresente leve sinal altista acima da linha de sinal e a tendência de longo prazo seja positiva (SMA 200 gap de 9.9%), a posição do preço dentro das bandas de Bollinger e a falta de momentum forte sugerem consolidação no curto prazo.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.074367, "bb_upper_gap": -0.049954, "bb_width": 0.122822, "macd_ratio": 0.009052, "macd_signal_ratio": 0.007778, "rsi": 51.64421, "sma200_gap": 0.099031, "sma50_gap": 0.002653}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O RSI está neutro em 51.64 e o preço negocia muito próximo à SMA 50. Apesar do MACD apresentar ligeiro viés comprador e o ativo se manter acima da SMA 200, a proximidade da banda superior de Bollinger e a falta de momentum forte sugerem consolidação momentânea.",
  "signal": "MANTER"
}
```

## 2022-03-31

Features: `{"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}`

Consenso: `{"vote_counts": {"COMPRA": 2, "MANTER": 3, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.68,
  "justification": "O ativo opera acima das médias móveis de 50 e 200 períodos com tendência de alta estabelecida. O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), acompanhado de MACD positivo cruzando acima de sua linha de sinal e RSI saudável em 57.57, indicando continuidade do momentum comprador sem sobrecompra extrema.",
  "signal": "COMPRA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço ultrapassou ligeiramente a banda superior de Bollinger (bb_upper_gap negativo), sugerindo extensão de curto prazo, embora a tendência permaneça altista acima das médias de 50 e 200 períodos. Com o RSI neutro-altista em 57.57 e o MACD iniciando cruzamento positivo sobre o sinal mas ainda próximo de zero, a relação risco-retorno favorece a manutenção da posição até uma confirmação mais clara de rompimento.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço rompeu levemente acima da banda superior de Bollinger com bandas moderadamente alargadas, operando acima das SMAs de 50 e 200 períodos em forte tendência de alta. O MACD cruzou acima da linha de sinal em território positivo e o RSI em 57.57 indica momento favorável com espaço para valorização.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu levemente acima da banda superior de Bollinger (bb_upper_gap negativo), indicando possível sobrecompra a curto prazo, apesar da tendência de alta mais ampla confirmada pelas médias móveis (sma50_gap e sma200_gap positivos). O RSI em 57.57 e o MACD próximo ao sinal sem divergência extrema sugerem consolidação antes de nova definição direcional.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.113562, "bb_upper_gap": -0.02125, "bb_width": 0.128863, "macd_ratio": 0.001056, "macd_signal_ratio": -0.00379, "rsi": 57.571627, "sma200_gap": 0.238282, "sma50_gap": 0.026464}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu levemente acima da Banda de Bollinger superior (bb_upper_gap negativo), indicando potencial sobrecompra a curto prazo, apesar da tendência de alta mais ampla confirmada pelas médias móveis (sma50_gap e sma200_gap positivos). O RSI em 57.57 e o MACD próximo da linha de sinal sugerem continuidade moderada sem momentum explosivo ou exaustão imediata, recomendando manutenção de posição.",
  "signal": "MANTER"
}
```

## 2022-11-04

Features: `{"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "VETADO", "risk_source": "HARD_RULE", "risk_rule": "VOLATILITY", "portfolio_called": false, "portfolio_source": null, "portfolio_rule": null, "portfolio_decision": null, "target_weight": null, "final_cause": "RISK_VETO_VOLATILITY"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo esteja negativo (sma50_gap em -12.29%), a tendência de longo prazo ainda é de alta (sma200_gap em +9.32%), indicando oportunidade de repique/reversão à média.",
  "signal": "COMPRA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo rompeu ligeiramente abaixo da Banda de Bollinger inferior (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo esteja negativo (sma50_gap em -12.29%), o ativo ainda se sustenta acima da tendência de longo prazo (sma200_gap positivo de +9.32%), sugerindo oportunidade de repique/retorno à média.",
  "signal": "COMPRA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Apesar da tendência de curto prazo em baixa (sma50_gap negativo), o ativo permanece acima da SMA 200 (+9.3%) e o MACD apresenta sinal de desaceleração/reversão altista iminente (macd_signal_ratio positivo), indicando oportunidade de repique.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Embora o momentum de curto prazo (sma50_gap e macd_ratio) seja de baixa, o ativo mantém suporte sobre a tendência estrutural de alta (sma200_gap positivo em 9.32%), sugerindo uma oportunidade de reversão à média com a recuperação do MACD em direção ao sinal.",
  "signal": "COMPRA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": -0.009856, "bb_upper_gap": -0.247807, "bb_width": 0.27314, "macd_ratio": -0.019806, "macd_signal_ratio": 0.006529, "rsi": 33.557226, "sma200_gap": 0.093176, "sma50_gap": -0.122889}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço rompeu abaixo da banda inferior de Bollinger (bb_lower_gap negativo) com RSI próximo à sobrevenda (33.56). Apesar do momentum de curto prazo em baixa (sma50_gap negativo), a tendência de longo prazo permanece positiva (sma200_gap positivo de 9.3%), sugerindo uma oportunidade de reversão à média.",
  "signal": "COMPRA"
}
```

## 2023-06-15

Features: `{"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 0, "VENDA": 5}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "VENDA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "VENDA", "target_weight": 0.0, "final_cause": "ACTION_SELL"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O ativo apresenta forte sobrecompra indicada pelo RSI em 75.97 e pelo rompimento da banda superior de Bollinger (bb_upper_gap negativo). Além disso, os afastamentos das médias móveis (sma50_gap e sma200_gap superiores a 23% e 30%) sugerem estiramento excessivo e alta probabilidade de correção técnica a curto prazo.",
  "signal": "VENDA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.8,
  "justification": "O ativo apresenta forte sobrecompra com RSI próximo de 76, rompimento da banda superior de Bollinger (bb_upper_gap negativo) e expressivo afastamento das médias móveis de 50 e 200 períodos, indicando alta probabilidade de correção técnica iminente.",
  "signal": "VENDA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O ativo apresenta forte condição de sobrecompra com RSI próximo a 76 e o preço rompendo acima da Banda de Bollinger superior (bb_upper_gap negativo). Além disso, os afastamentos das médias de 50 e 200 períodos estão excessivamente esticados, indicando probabilidade elevada de exaustão do movimento de alta e correção técnica iminente.",
  "signal": "VENDA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.8,
  "justification": "O ativo apresenta condições extremas de sobrecompra, com RSI acima de 75 e preço rompendo a banda superior de Bollinger (bb_upper_gap negativo). Além disso, os afastamentos das médias móveis (SMA50 e SMA200) estão excessivamente esticados, indicando alta probabilidade de correção técnica iminente.",
  "signal": "VENDA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.322715, "bb_upper_gap": -0.020534, "bb_width": 0.298194, "macd_ratio": 0.05463, "macd_signal_ratio": 0.042322, "rsi": 75.965752, "sma200_gap": 0.305407, "sma50_gap": 0.236734}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.8,
  "justification": "O ativo apresenta forte sobrecompra com RSI próximo a 76, cotação rompendo acima da Banda de Bollinger superior (bb_upper_gap negativo) e expressivo afastamento das médias móveis de 50 e 200 períodos, indicando risco iminente de correção técnica.",
  "signal": "VENDA"
}
```

### portfolio_manager

System prompt:

```text
Você é o gestor de portfólio do Hedge-fund-lab.
Decida apenas a direção: seguir o sinal técnico aprovado ou manter a posição
atual. Você não define tamanho de posição, percentual de carteira nem
quantidade financeira — isso é decidido fora desta etapa por política
determinística. Não inverta a direção do sinal aprovado. Retorne COMPRA, VENDA
ou MANTER com uma justificativa objetiva.
```

User prompt:

```text
{"risk_verdict": {"analysis": "Operação não aumenta a exposição", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.320983}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.792, "justification": "Consenso coletivo: 5/5 votos em VENDA", "signal": "VENDA"}}
```

Saída visível:

```json
{
  "decision": "VENDA",
  "reasoning": "O sinal técnico de VENDA possui alta confiança (79,2%) com consenso unânime de 5/5 votos, e a análise de risco aprovou a operação sem aumento indevido de exposição."
}
```

## 2024-01-22

Features: `{"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo mantém tendência de alta estrutural indicada pelos gaps positivos contra a SMA50 (4,57%) e SMA200 (26,25%), porém o MACD está abaixo da linha de sinal e o RSI em 55,39 mostra neutralidade de momentum dentro das bandas de Bollinger, sugerindo consolidação temporária.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera em tendência de alta estrutural (afastado das médias de 50 e 200 períodos), porém o MACD está abaixo de sua linha de sinal indicando perda de momentum e o RSI em 55,38 aponta neutralidade dentro das bandas de Bollinger.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera acima das médias móveis (SMA 50 e SMA 200) e dentro das Bandas de Bollinger, com RSI neutro em 55.39. Contudo, o MACD está abaixo da sua linha de sinal, indicando perda de momento no curto prazo, justificando uma postura de manutenção.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo mantém tendência de alta de longo e médio prazo com sma200_gap positivo (+26,25%) e sma50_gap (+4,57%). O RSI está neutro em 55,39 e os preços operam no centro das bandas de Bollinger. No entanto, o MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), sugerindo desaceleração do momentum e ausência de gatilho claro de entrada ou saída imediata.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.
Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.031457, "bb_upper_gap": -0.037498, "bb_width": 0.069164, "macd_ratio": 0.014173, "macd_signal_ratio": 0.018815, "rsi": 55.387471, "sma200_gap": 0.262542, "sma50_gap": 0.04573}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera acima das médias móveis (SMA 50 e SMA 200 positivas), confirmando tendência de alta no longo prazo. Contudo, o MACD está abaixo da linha de sinal indicando perda de momentum recente, enquanto o RSI em 55,39 e o preço dentro das bandas de Bollinger sugerem neutralidade no curto prazo.",
  "signal": "MANTER"
}
```

