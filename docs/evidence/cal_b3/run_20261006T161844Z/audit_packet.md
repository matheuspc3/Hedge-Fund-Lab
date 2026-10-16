# CAL-B3 — pacote comportamental (sem resultado financeiro)

Autor principal: classifique cada âncora em `review/PRIMARY_AUTHOR.json`:
`material_unsupported_claim` e `rationale_action_coherence` = PASS ou FAIL (`optional_note` livre).
Material = fato/regra específica, não fornecida ao agente, que pesa na justificativa/decisão
(Technical: ticker, data, preço absoluto, notícia, macro, fundamentos; Risk: threshold, hard rule,
probabilidade ou limite inexistente). Coerência: Technical x sinal; Risk x veredito e payload;
Portfolio x ação e veredito do Risk. A segunda revisão é opcional (`SECOND_AUTHOR_OPTIONAL.json`).

## 2018-08-03

Features: `{"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}`

Consenso: `{"vote_counts": {"COMPRA": 1, "MANTER": 4, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço exibe forte tendência de alta, negociando bem acima das médias de 50 e 200 períodos com MACD positivo e acima do sinal. Contudo, o RSI acima de 70 indica condição de sobrecompra e o fechamento está colado na banda superior de Bollinger (bb_upper_gap próximo de zero), sugerindo cautela para novas entradas compradas.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo demonstra forte tendência de alta, com o preço bem acima das médias de 50 e 200 períodos (sma50_gap de 20,11% e sma200_gap de 12,17%) e MACD positivo acima da linha de sinal. No entanto, o RSI está em 70,34 (região de sobrecompra) e o fechamento está colado na banda superior de Bollinger (bb_upper_gap próximo de zero), sugerindo extensão de alta e desfavorável relação risco/retorno para novas compras imediatas.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), com forte momentum indicado pela linha MACD acima da linha de sinal e RSI em patamar de força compradora (70,34), mantendo-se dentro da banda de Bollinger superior.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta com preço significativamente acima das médias móveis de 50 e 200 períodos, e o MACD posicionado acima da linha de sinal e do zero. No entanto, o RSI encontra-se em patamar de sobrecompra (70,34) e o preço está muito próximo da banda superior de Bollinger (bb_upper_gap levemente negativo), indicando risco de estiramento e desaconselhando novas compras imediatas, sugerindo manutenção da posição.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.248925, "bb_upper_gap": -0.000685, "bb_width": 0.222049, "macd_ratio": 0.035448, "macd_signal_ratio": 0.026335, "rsi": 70.344275, "sma200_gap": 0.121671, "sma50_gap": 0.20111}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está bem acima das médias de 50 e 200 períodos e o MACD permanece acima da linha de sinal em território positivo, indicando tendência de alta expressiva. Contudo, o RSI está em zona de sobrecompra (70,34) e o preço encosta na banda superior de Bollinger (bb_upper_gap próximo de zero), sugerindo risco de exaustão no curto prazo.",
  "signal": "MANTER"
}
```

## 2019-03-19

Features: `{"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta, com preço bem acima das médias de 50 e 200 períodos e MACD positivo superando a linha de sinal. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI encontra-se em nível sobrecomprado (73,93), o que desaconselha novas compras devido ao risco de correção imediata.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta, com preço bem acima das médias móveis de 50 e 200 períodos (sma50_gap de 11,4% e sma200_gap de 34,2%) e MACD positivo acima da linha de sinal. No entanto, o RSI em 73,93 aponta sobrecompra e o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0), indicando estiramento no curto prazo e desfavorável relação risco-retorno para novas compras.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo apresenta forte tendência de alta com preço acima das médias móveis de 50 e 200 períodos e MACD positivo acima da linha de sinal. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge níveis de sobrecompra (73,93), sugerindo cautela para novas entradas compradas e indicando manutenção da posição existente.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos e o MACD permanece acima da linha de sinal, indicando forte tendência de alta. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge 73,93, sugerindo condição de sobrecompra e desaconselhando novas compras no momento atual.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.128352, "bb_upper_gap": 0.010466, "bb_width": 0.110235, "macd_ratio": 0.02492, "macd_signal_ratio": 0.019931, "rsi": 73.934548, "sma200_gap": 0.342253, "sma50_gap": 0.114248}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta com preço acima das médias de 50 e 200 períodos e MACD positivo acima da linha de sinal. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI em 73.93 indica condição de sobrecompra, desfavorecendo novas entradas a favor da tendência imediata e sugerindo cautela.",
  "signal": "MANTER"
}
```

## 2019-10-18

Features: `{"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "COMPRA", "target_weight": 1.0, "final_cause": "ACTION_BUY"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[{"verdict": "APROVADO", "gates": {"V3-R1": false, "V3-R2": false, "V3-R3": false}, "codes": []}]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando tendência de alta. O MACD está positivo e acima de sua linha de sinal, acompanhado por um RSI em zona altista moderada (57,94) e cotação dentro das bandas de Bollinger, sugerindo continuidade do momentum comprador.",
  "signal": "COMPRA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos, com MACD positivo e acima da linha de sinal. O RSI em 57,94 reflete momentum favorável sem sobrecompra, e o fechamento permanece dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos, o MACD opera acima de zero e de sua linha de sinal, e o RSI em 57,9 reflete momentum positivo sem estar sobrecomprado.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), com o MACD acima de zero e superior à linha de sinal. O RSI em 57,94 indica força compradora sem sobrecompra, dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.059437, "bb_upper_gap": -0.023957, "bb_width": 0.08194, "macd_ratio": 0.008972, "macd_signal_ratio": 0.00687, "rsi": 57.937445, "sma200_gap": 0.043646, "sma50_gap": 0.048115}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), com o MACD acima de zero e superando sua linha de sinal. O RSI em 57,94 indica força compradora sem sobrecompra, dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.

Avalie somente o sinal técnico e as métricas de risco explicitamente fornecidas no payload. Não use notícias, conhecimento externo, identidade do ativo, datas ou informação futura.

As regras duras numéricas do sistema são aplicadas deterministicamente antes desta etapa. Se esta chamada foi alcançada, essas regras anteriores não vetaram a operação.

Não invente, suponha nem aplique novos thresholds numéricos que não estejam explicitamente fornecidos no seu payload ou no seu contrato.

O campo confidence do sinal técnico é metadado qualitativo. Não existe um limiar numérico de confidence configurado para aprovação ou veto. Nunca diga ou implique que uma confidence está acima ou abaixo de um threshold inexistente, e nunca aprove ou vete uma operação somente porque a confidence é baixa ou alta.

Você pode considerar confidence qualitativamente em conjunto com as métricas efetivamente fornecidas, mas sem criar cortes numéricos ou regras ocultas.

Você ainda pode retornar VETADO quando a combinação do sinal e das métricas fornecidas indicar risco inadequado. Nesse caso, a justificativa deve se apoiar somente nos valores e relações presentes no payload, sem inventar regras quantitativas externas.

Preserve capital, não invente dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.192782}, "technical_signal": {"confidence": 0.738, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "A proposta de COMPRA apresenta consenso pleno dos votos técnicos (5/5) com confiança qualitativa positiva. No lado do risco, a volatilidade recente é moderada (0.192782), a concentração atual é nula (0.0) e o drawdown atual é zero (0.0), indicando disponibilidade de alocação sem sobreposição de perdas acumuladas ou concentração prévia. O perfil risco-retorno é favorável à execução.",
  "risk_metrics": {
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.192782
  },
  "verdict": "APROVADO"
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
{"risk_verdict": {"analysis": "A proposta de COMPRA apresenta consenso pleno dos votos técnicos (5/5) com confiança qualitativa positiva. No lado do risco, a volatilidade recente é moderada (0.192782), a concentração atual é nula (0.0) e o drawdown atual é zero (0.0), indicando disponibilidade de alocação sem sobreposição de perdas acumuladas ou concentração prévia. O perfil risco-retorno é favorável à execução.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.192782}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.738, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "decision": "COMPRA",
  "reasoning": "Sinal técnico de COMPRA aprovado por consenso total (5/5) e validado pelo controle de risco, sem impedimentos de concentração ou drawdown."
}
```

## 2020-05-13

Features: `{"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço está contido dentro das Bandas de Bollinger, com RSI neutro em 51,87 e MACD positivo acima da linha de sinal. Embora o preço esteja acima da SMA50 (sma50_gap positivo de 5,7%), permanece substancialmente abaixo da SMA200 (sma200_gap de -29,69%), indicando conflito entre a tendência de médio e longo prazo.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.55,
  "justification": "O ativo opera dentro das bandas de Bollinger com RSI em 51.87, indicando neutralidade no curto prazo. Embora o preço esteja acima da SMA50 e o MACD esteja positivo e acima de sua linha de sinal, há forte divergência com a tendência de longo prazo, dado o distanciamento expressivo abaixo da SMA200 (sma200_gap de -29.69%). Sinais conflitantes recomendam cautela.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das bandas de Bollinger com RSI neutro (51.87). Embora o MACD esteja positivo e acima da linha de sinal e o preço esteja acima da SMA50 (sma50_gap = 0.057), a forte distância negativa em relação à SMA200 (sma200_gap = -0.297) aponta para uma tendência primária de baixa contrastando com a recuperação de curto prazo, sugerindo cautela e manutenção.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preco esta dentro das bandas de Bollinger e acima da SMA50, com MACD positivo e acima do sinal. Contudo, o RSI permanece neutro (51.87) e a tendencia de longo prazo e fortemente baixista (sma200_gap de -29.69%), configurando sinais mistos que recomendam cautela.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.140387, "bb_upper_gap": -0.067655, "bb_width": 0.200742, "macd_ratio": 0.017201, "macd_signal_ratio": 0.008314, "rsi": 51.867798, "sma200_gap": -0.296947, "sma50_gap": 0.057002}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço está contido dentro das bandas de Bollinger com RSI neutro em 51,87. Embora o momentum de curto prazo seja positivo com o MACD acima da linha de sinal e o preço acima da SMA50 (gap de 5,7%), o ativo permanece significativamente abaixo da SMA200 (gap de -29,69%), indicando forte tendência de baixa no longo prazo que contrasta com a recuperação recente.",
  "signal": "MANTER"
}
```

## 2021-01-06

Features: `{"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 2, "VENDA": 3}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "VENDA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "VENDA", "target_weight": 0.0, "final_cause": "ACTION_SELL"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo demonstra forte tendência de alta, operando bem acima das médias de 50 e 200 períodos e com o MACD positivo acima da linha de sinal. Contudo, o preço encontra-se acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge 75.17, indicando condições esticadas de sobrecompra, desfavorecendo novas compras no momento e justificando a manutenção da posição.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço está acima da banda superior de Bollinger (bb_upper_gap > 0) e muito estendido em relação às médias móveis de 50 e 200 períodos (sma50_gap de 21,3% e sma200_gap de 41,8%). Além disso, o RSI encontra-se em nível elevado de sobrecompra (75,17), sugerindo forte exaustão compradora e assimetria desfavorável para novas entradas compradas.",
  "signal": "VENDA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço encontra-se acima da banda superior de Bollinger (bb_upper_gap > 0) e bem esticado em relação às médias móveis (sma50_gap de 21% e sma200_gap de quase 42%). Além disso, o RSI está em patamar sobrecomprado (75,17), indicando risco elevado de exaustão e correção técnica no curto prazo.",
  "signal": "VENDA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo demonstra forte tendência de alta, com preço bem acima das médias de 50 e 200 períodos e MACD positivo acima da linha de sinal. Contudo, o RSI em 75,17 e o fechamento acima da banda superior de Bollinger (bb_upper_gap > 0) indicam condição de sobrecompra estendida, desaconselhando novas compras imediatas.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.149158, "bb_upper_gap": 0.009365, "bb_width": 0.129526, "macd_ratio": 0.040373, "macd_signal_ratio": 0.038885, "rsi": 75.173598, "sma200_gap": 0.417708, "sma50_gap": 0.2134}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço está acima da banda superior de Bollinger (bb_upper_gap > 0) e muito esticado em relação às médias móveis (sma50_gap em 21,34% e sma200_gap em 41,77%). O RSI está em zona de forte sobrecompra em 75,17, indicando esgotamento do movimento de alta e risco elevado de correção, apesar do MACD positivo.",
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
{"risk_verdict": {"analysis": "Operação não aumenta a exposição", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.297476}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.418, "justification": "Consenso coletivo: 3/5 votos em VENDA", "signal": "VENDA"}}
```

Saída visível:

```json
{
  "decision": "VENDA",
  "reasoning": "O sinal técnico aponta VENDA com consenso coletivo e a análise de risco aprovou a operação sem aumento de exposição, permitindo a execução da direção indicada."
}
```

## 2021-08-17

Features: `{"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "COMPRA", "target_weight": 1.0, "final_cause": "ACTION_BUY"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[{"verdict": "APROVADO", "gates": {"V3-R1": false, "V3-R2": false, "V3-R3": false}, "codes": []}]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando tendência de alta no médio e longo prazo. O MACD está acima de zero e superior à linha de sinal, reforçando o momentum comprador, enquanto o RSI em 56,15 indica força positiva sem condições de sobrecompra. O ativo permanece dentro das bandas de Bollinger com espaço até a banda superior.",
  "signal": "COMPRA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando tendência de alta consistente. O MACD opera acima de zero e acima de sua linha de sinal, reforçado por um RSI em zona altista moderada (56,15) e preço contido dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço encontra-se acima das médias móveis de 50 e 200 períodos (sma50_gap > 0 e sma200_gap > 0), indicando tendência de alta no médio e longo prazo. O MACD opera acima de zero e acima de sua linha de sinal (macd_ratio > macd_signal_ratio), acompanhado por um RSI equilibrado em 56,15 e preço oscilando dentro das bandas de Bollinger sem sobrecompra extrema.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando tendência de alta. O MACD está acima de zero e de sua linha de sinal (macd_ratio > macd_signal_ratio), enquanto o RSI em 56,15 reflete força compradora sem indicar sobrecompra.",
  "signal": "COMPRA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.106411, "bb_upper_gap": -0.032258, "bb_width": 0.133712, "macd_ratio": 0.011847, "macd_signal_ratio": 0.005554, "rsi": 56.146259, "sma200_gap": 0.122908, "sma50_gap": 0.017989}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.72,
  "justification": "O preço situa-se acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando tendência de alta. O MACD opera acima de zero e da sua linha de sinal, acompanhado por um RSI moderadamente altista de 56,15 e preço contido dentro das bandas de Bollinger, sugerindo continuidade do movimento positivo.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.

Avalie somente o sinal técnico e as métricas de risco explicitamente fornecidas no payload. Não use notícias, conhecimento externo, identidade do ativo, datas ou informação futura.

As regras duras numéricas do sistema são aplicadas deterministicamente antes desta etapa. Se esta chamada foi alcançada, essas regras anteriores não vetaram a operação.

Não invente, suponha nem aplique novos thresholds numéricos que não estejam explicitamente fornecidos no seu payload ou no seu contrato.

O campo confidence do sinal técnico é metadado qualitativo. Não existe um limiar numérico de confidence configurado para aprovação ou veto. Nunca diga ou implique que uma confidence está acima ou abaixo de um threshold inexistente, e nunca aprove ou vete uma operação somente porque a confidence é baixa ou alta.

Você pode considerar confidence qualitativamente em conjunto com as métricas efetivamente fornecidas, mas sem criar cortes numéricos ou regras ocultas.

Você ainda pode retornar VETADO quando a combinação do sinal e das métricas fornecidas indicar risco inadequado. Nesse caso, a justificativa deve se apoiar somente nos valores e relações presentes no payload, sem inventar regras quantitativas externas.

Preserve capital, não invente dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.368561}, "technical_signal": {"confidence": 0.738, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "A proposta de COMPRA apresenta consenso pleno no sinal técnico (5/5 votos) e métricas de risco favoráveis dentro do portfólio, com concentração e drawdown zerados (0.0). A volatilidade recente de 0.368561 é compatível com a alocação diante da ausência de exposição prévia, não havendo fatores adversos nas métricas fornecidas que justifiquem veto.",
  "risk_metrics": {
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.368561
  },
  "verdict": "APROVADO"
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
{"risk_verdict": {"analysis": "A proposta de COMPRA apresenta consenso pleno no sinal técnico (5/5 votos) e métricas de risco favoráveis dentro do portfólio, com concentração e drawdown zerados (0.0). A volatilidade recente de 0.368561 é compatível com a alocação diante da ausência de exposição prévia, não havendo fatores adversos nas métricas fornecidas que justifiquem veto.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.368561}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.738, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "decision": "COMPRA",
  "reasoning": "Sinal técnico com consenso unânime (5/5) e confiança de 73,8%, devidamente aprovado pelo controle de risco com métricas zeradas de concentração e drawdown."
}
```

## 2022-03-11

Features: `{"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), mantendo a tendência estrutural de alta. No entanto, o MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), o RSI está neutro em 47.99 e o fechamento está contido dentro das bandas de Bollinger, sugerindo consolidação ou perda de momentum no curto prazo sem gatilho claro de compra ou venda.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger e acima das médias de 50 e 200 períodos, mantendo tendência estrutural de alta. No entanto, o MACD está abaixo de sua linha de sinal e o RSI próximo a 48 indica momentum neutro, justificando a manutenção da posição.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece dentro das Bandas de Bollinger e acima das médias móveis de 50 e 200 períodos, indicando uma tendência estrutural positiva. Contudo, o MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI encontra-se em patamar neutro (47,99), sugerindo perda de momento e falta de sinal claro de entrada no momento.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos, indicando uma tendência estrutural positiva no longo prazo. No entanto, no curto prazo o momentum enfraqueceu, com o MACD posicionado abaixo de sua linha de sinal e o RSI em zona neutra (47,99). O preço também opera confortavelmente dentro das bandas de Bollinger, sugerindo ausência de gatilhos imediatos de compra ou venda.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.024909, "bb_upper_gap": -0.068405, "bb_width": 0.095389, "macd_ratio": 0.008259, "macd_signal_ratio": 0.014978, "rsi": 47.993308, "sma200_gap": 0.230443, "sma50_gap": 0.018157}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos (sma50_gap de +1,8% e sma200_gap de +23,0%), indicando tendência estrutural de alta. No entanto, o preço está contido dentro das Bandas de Bollinger, o RSI em 48 reflete neutralidade de momentum, e a linha MACD situa-se abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio), sugerindo fraqueza no curto prazo que recomenda cautela sem configurar venda compulsória.",
  "signal": "MANTER"
}
```

## 2022-11-29

Features: `{"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.55,
  "justification": "O ativo opera dentro das bandas de Bollinger, com RSI em patamar neutro (44.64). O preço está abaixo da SMA 50 (-10.48%), porém ainda acima da SMA 200 (+3.33%), indicando fraqueza no médio prazo mas sustentação no longo prazo. O MACD permanece negativo, embora ligeiramente acima da linha de sinal, sem clareza direcional forte.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço encontra-se dentro das bandas de Bollinger, acima da SMA200 mas significativamente abaixo da SMA50, indicando fraqueza no médio prazo. O MACD está negativo, embora ligeiramente acima da linha de sinal, e o RSI em 44.64 mostra momentum neutro/fraco sem condições claras de sobrecompra ou sobrevenda.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das bandas de Bollinger e acima da SMA200 (sma200_gap positivo de 3,3%), indicando suporte estrutural de longo prazo. No entanto, opera significativamente abaixo da SMA50 (-10,5%) com RSI em 44,64, refletindo fraqueza no médio prazo. Embora o MACD esteja acima de sua linha de sinal, ambos permanecem em território negativo. Os sinais mistos sugerem neutralidade.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger e acima da SMA200, porém permanece significativamente abaixo da SMA50 (-10,48%). O MACD está em território negativo, embora ligeiramente acima de sua linha de sinal, e o RSI em 44,64 indica neutralidade sem extremos definidos.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.120243, "bb_upper_gap": -0.095674, "bb_width": 0.213297, "macd_ratio": -0.052192, "macd_signal_ratio": -0.055634, "rsi": 44.63767, "sma200_gap": 0.033255, "sma50_gap": -0.104789}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger e acima da SMA 200, porém abaixo da SMA 50 (-10.48%). O MACD permanece em território negativo, embora ligeiramente acima de sua linha de sinal, e o RSI em 44.64 reflete neutralidade sem sobrevenda extrema, configurando um cenário misto e sem tendência clara definida.",
  "signal": "MANTER"
}
```

## 2023-05-12

Features: `{"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta, com preço bem acima das médias móveis de 50 e 200 períodos e MACD acima da linha de sinal. No entanto, o preço se encontra acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge 72,29, caracterizando sobrecompra e desaconselhando novas entradas sem uma consolidação prévia.",
  "signal": "MANTER"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta com preço acima das médias móveis de 50 e 200 períodos e MACD positivo acima do sinal. No entanto, o preço está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge 72,29, apontando para condições de sobrecompra que sugerem cautela contra novas compras imediatas.",
  "signal": "MANTER"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta, com preço bem acima das médias de 50 e 200 períodos e MACD positivo e acima do sinal. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI está em 72.29, indicando condição de sobrecompra e desfavorável para novas entradas imediatas.",
  "signal": "MANTER"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta, com preço bem acima das médias de 50 e 200 períodos e MACD positivo acima da linha de sinal. No entanto, o fechamento está acima da banda superior de Bollinger (bb_upper_gap > 0) e o RSI atinge 72,29, indicando estado de sobrecompra e desfavorável para novas entradas imediatas, recomendando-se manter a posição.",
  "signal": "MANTER"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.185146, "bb_upper_gap": 0.022359, "bb_width": 0.147485, "macd_ratio": 0.028947, "macd_signal_ratio": 0.021039, "rsi": 72.291726, "sma200_gap": 0.110169, "sma50_gap": 0.168142}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está em forte tendência de alta, operando acima das médias móveis de 50 e 200 períodos e com MACD positivo acima da linha de sinal. Contudo, o fechamento acima da banda superior de Bollinger (bb_upper_gap > 0) somado ao RSI em 72.29 indica condição de sobrecompra no momento atual, desaconselhando novas compras imediatas e justificando a manutenção da posição.",
  "signal": "MANTER"
}
```

## 2024-01-11

Features: `{"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "COMPRA", "target_weight": 1.0, "final_cause": "ACTION_BUY"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

Checker do Risk v2: `[{"verdict": "APROVADO", "gates": {"V3-R1": false, "V3-R2": false, "V3-R3": false}, "codes": []}]`

### technical_analyst #1

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O ativo opera com forte tendência de alta, com o preço significativamente acima das médias de 50 e 200 períodos (sma50_gap de 7,30% e sma200_gap de 30,54%). O MACD permanece positivo e acima de sua linha de sinal, enquanto o RSI em 62,94 indica força compradora sem atingir zona de sobrecompra extrema. O preço encontra-se dentro das bandas de Bollinger, com espaço até a banda superior.",
  "signal": "COMPRA"
}
```

### technical_analyst #2

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está confortavelmente acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando forte tendência de alta. O MACD opera acima de zero e acima de sua linha de sinal, acompanhado por um RSI saudável de 62,94, mostrando força compradora sem estar em sobrecompra extrema, além de estar contido dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### technical_analyst #3

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), o MACD opera acima de zero e de sua linha de sinal, e o RSI em 62,94 indica força compradora sem estar em sobrecompra extrema, mantendo-se dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### technical_analyst #4

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando forte tendência de alta. O MACD opera acima de zero e de sua linha de sinal, e o RSI em 62.94 reforça o momento comprador sem indicar sobrecompra extrema.",
  "signal": "COMPRA"
}
```

### technical_analyst #5

System prompt:

```text
You are the technical analyst for Hedge-fund-lab.
Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price level, no asset identity and no calendar date are available, and none is required for this decision. Ignore news, external knowledge, and future prices.

Feature definitions (close = closing price of the current session t; SMA50/SMA200 = simple moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; MACD 12/26/9):
- bb_lower_gap = close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; > 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, an upper breakout or overbought.
- bb_upper_gap = close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; < 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, a break above the upper band, overbought, or a price above the band.
- bb_width = (BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish direction by itself.
- macd_ratio = MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.
- macd_signal_ratio = MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below.
- rsi = Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent losses; lower values mean recent losses predominate.
- sma200_gap = close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.
- sma50_gap = close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.
Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the upper band; bb_lower_gap < 0 means the close is below the lower band.

State, not transition: the features describe only the current session t; no earlier values are provided. You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal line, the close is beyond the upper band). Do not state transitions that would require comparing with an earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot show them.

Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence between 0 and 1.
```

User prompt:

```text
Features: {"bb_lower_gap": 0.114976, "bb_upper_gap": -0.043221, "bb_width": 0.152718, "macd_ratio": 0.023258, "macd_signal_ratio": 0.022531, "rsi": 62.940519, "sma200_gap": 0.305376, "sma50_gap": 0.073036}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está confortavelmente acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando forte tendência de alta. O MACD opera acima de zero e acima de sua linha de sinal, enquanto o RSI em 62,94 confirma momentum comprador saudável sem apresentar sobrecompra excessiva, mantendo-se dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.

Avalie somente o sinal técnico e as métricas de risco explicitamente fornecidas no payload. Não use notícias, conhecimento externo, identidade do ativo, datas ou informação futura.

As regras duras numéricas do sistema são aplicadas deterministicamente antes desta etapa. Se esta chamada foi alcançada, essas regras anteriores não vetaram a operação.

Não invente, suponha nem aplique novos thresholds numéricos que não estejam explicitamente fornecidos no seu payload ou no seu contrato.

O campo confidence do sinal técnico é metadado qualitativo. Não existe um limiar numérico de confidence configurado para aprovação ou veto. Nunca diga ou implique que uma confidence está acima ou abaixo de um threshold inexistente, e nunca aprove ou vete uma operação somente porque a confidence é baixa ou alta.

Você pode considerar confidence qualitativamente em conjunto com as métricas efetivamente fornecidas, mas sem criar cortes numéricos ou regras ocultas.

Você ainda pode retornar VETADO quando a combinação do sinal e das métricas fornecidas indicar risco inadequado. Nesse caso, a justificativa deve se apoiar somente nos valores e relações presentes no payload, sem inventar regras quantitativas externas.

Preserve capital, não invente dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.177251}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "O sinal de COMPRA apresenta consenso pleno (5/5) e suporte qualitativo favorável. Do ponto de vista de risco, as métricas informadas estão controladas, com concentração e drawdown zerados e volatilidade recente compatível com a tomada de posição.",
  "risk_metrics": {
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.177251
  },
  "verdict": "APROVADO"
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
{"risk_verdict": {"analysis": "O sinal de COMPRA apresenta consenso pleno (5/5) e suporte qualitativo favorável. Do ponto de vista de risco, as métricas informadas estão controladas, com concentração e drawdown zerados e volatilidade recente compatível com a tomada de posição.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.177251}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "decision": "COMPRA",
  "reasoning": "Sinal técnico com forte consenso de 5/5 votos e alta confiança (0.75), plenamente aprovado pela análise de risco sob métricas controladas e sem restrições de drawdown ou concentração."
}
```

