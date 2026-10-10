# CAL-B2 — pacote comportamental (sem resultado financeiro)

Classifique cada âncora de forma independente em `review/AUTHOR_1.json` ou `review/AUTHOR_2.json`:
`material_hallucination` e `rationale_action_coherence` = PASS ou FAIL. Avalie só o texto visível de
cada estágio contra o prompt daquele estágio. Marcas do pré-filtro léxico são só ponteiros.

## 2018-08-16

Features: `{"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das bandas de Bollinger, muito próximo da banda inferior (bb_lower_gap de 1,37%). Embora esteja acima da SMA 50 e ligeiramente acima da SMA 200, o MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI em 45,98 reflete neutralidade com viés corretivo, justificando cautela e manutenção.",
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
Features: {"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das bandas de Bollinger e próximo à média móvel de 200 períodos (sma200_gap próximo a zero), embora permaneça acima da SMA 50. O RSI está em patamar neutro (45,98) e a linha MACD está abaixo de sua linha de sinal, indicando perda de ímpeto de alta sem confirmar forte tendência definida para compra ou venda imediata.",
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
Features: {"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço está acima das médias móveis SMA50 e SMA200 e dentro das bandas de Bollinger, mas o MACD está abaixo de sua linha de sinal e o RSI em 45.98 indica neutralidade sem força direcional clara.",
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
Features: {"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço permanece dentro das bandas de Bollinger, ligeiramente acima da banda inferior. O MACD está positivo, porém abaixo da sua linha de sinal, indicando desaceleração de curto prazo. O RSI em 45.98 mostra neutralidade, e o preço está praticamente alinhado à SMA200 com leve distanciamento da SMA50, sugerindo equilíbrio momentâneo sem viés direcional claro.",
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
Features: {"bb_lower_gap": 0.013732, "bb_upper_gap": -0.099967, "bb_width": 0.118822, "macd_ratio": 0.016631, "macd_signal_ratio": 0.027822, "rsi": 45.981833, "sma200_gap": 0.000134, "sma50_gap": 0.058852}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das bandas de Bollinger e muito próximo da SMA200 (gap de 0,01%). Embora esteja acima da SMA50 e o MACD esteja em território positivo, a linha MACD situa-se abaixo de sua linha de sinal e o RSI em 45,98 indica neutralidade de momento, justificando uma postura de cautela sem viés direcional claro.",
  "signal": "MANTER"
}
```

## 2019-04-05

Features: `{"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece confortavelmente acima das médias móveis de 50 e 200 períodos, confirmando tendência estrutural de alta. No entanto, o fechamento está dentro das bandas de Bollinger, o RSI indica nível neutro a levemente altista (58,05) e a linha do MACD está abaixo da sua linha de sinal, recomendando manutenção de posição sem novas entradas agressivas.",
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
Features: {"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera em clara tendência de alta de longo e médio prazo, estando bem acima das médias de 50 e 200 períodos (sma50_gap = 6,66% e sma200_gap = 27,88%). O preço permanece dentro das bandas de Bollinger com RSI moderadamente altista em 58,05. Contudo, a linha MACD situa-se ligeiramente abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), indicando perda momentânea de momentum no curto prazo, recomendando a manutenção da posição sem novas compras.",
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
Features: {"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos, indicando tendência primária de alta. No entanto, o preço situa-se dentro das bandas de Bollinger e a linha MACD está ligeiramente abaixo da sua linha de sinal, com RSI neutro em 58,05, recomendando cautela e manutenção da posição atual.",
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
Features: {"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera em clara tendência de alta de médio e longo prazo, situando-se significativamente acima das médias SMA50 (gap de +6,66%) e SMA200 (gap de +27,88%). No entanto, o preço está contido dentro das bandas de Bollinger e a linha de MACD está ligeiramente abaixo da sua linha de sinal (0,0128 vs 0,0139), sugerindo desaceleração do ímpeto no curto prazo. Com o RSI em nível intermediário saudável (58,05), a recomendação prudente é MANTER a posição.",
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
Features: {"bb_lower_gap": 0.067799, "bb_upper_gap": -0.018564, "bb_width": 0.084288, "macd_ratio": 0.012782, "macd_signal_ratio": 0.01394, "rsi": 58.051354, "sma200_gap": 0.278769, "sma50_gap": 0.066637}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece em tendência de alta no longo e médio prazo (acima das SMAs de 50 e 200 períodos), e dentro das Bandas de Bollinger com RSI moderadamente altista em 58,05. Contudo, o MACD está ligeiramente abaixo de sua linha de sinal, sugerindo desaceleração momentânea do ímpeto.",
  "signal": "MANTER"
}
```

## 2019-10-07

Features: `{"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 0, "VENDA": 5}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "VENDA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "VENDA", "target_weight": 0.0, "final_cause": "ACTION_SELL"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.68,
  "justification": "O preço de fechamento está abaixo da banda inferior de Bollinger (bb_lower_gap < 0) e ligeiramente abaixo da SMA200 (sma200_gap < 0). Além disso, a linha MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI em 42.28 sinaliza predominância de pressões vendedoras.",
  "signal": "VENDA"
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
Features: {"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.68,
  "justification": "O fechamento está abaixo da banda inferior de Bollinger (bb_lower_gap negativo) e ligeiramente abaixo da SMA200. O MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI em 42.28 indica predominância de perdas recentes, sugerindo fraqueza no momento técnico.",
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
Features: {"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O fechamento está abaixo da banda inferior de Bollinger (bb_lower_gap negativo) e abaixo da SMA200. O MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI indica predomínio de pressão vendedora em 42,28, configurando um cenário de fraqueza técnica.",
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
Features: {"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço fechou abaixo da banda inferior de Bollinger (bb_lower_gap negativo) e ligeiramente abaixo da SMA 200. Além disso, o MACD está abaixo de sua linha de sinal com RSI fraco em 42,28 indicando predominância de pressão vendedora.",
  "signal": "VENDA"
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
Features: {"bb_lower_gap": -0.003805, "bb_upper_gap": -0.069082, "bb_width": 0.067746, "macd_ratio": 0.005232, "macd_signal_ratio": 0.012418, "rsi": 42.280894, "sma200_gap": -0.000895, "sma50_gap": 0.003232}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está abaixo da banda inferior de Bollinger (bb_lower_gap negativo) e ligeiramente abaixo da SMA200. O MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI em 42.28 indica predomínio de momentum vendedor.",
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
{"risk_verdict": {"analysis": "Operação não aumenta a exposição", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.240385}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.662, "justification": "Consenso coletivo: 5/5 votos em VENDA", "signal": "VENDA"}}
```

Saída visível:

```json
{
  "decision": "VENDA",
  "reasoning": "Sinal técnico de venda aprovado pelo controle de risco com consenso unânime de 5/5 votos e métricas dentro dos parâmetros aceitáveis."
}
```

## 2020-07-01

Features: `{"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preco esta operando entre as bandas de Bollinger e acima da SMA50 (+11,17%), mas permanece abaixo da SMA200 (-10,54%), indicando tendencia de longo prazo de baixa. O MACD esta positivo porem abaixo de sua linha de sinal, e o RSI em 57,83 esta em regiao neutra, sugerindo sinais mistos sem direcao clara definida.",
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
Features: {"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preco esta operando acima da SMA50 (+11.17%), porem significativamente abaixo da SMA200 (-10.54%), configurando um cenario de tendencia de longo prazo de baixa com recuperacao no medio prazo. O MACD permanece positivo mas abaixo de sua linha de sinal, enquanto o RSI em 57.83 e as Bandas de Bollinger (preco contido dentro das bandas) indicam forca compradora moderada sem consolidacao clara de continuidade direcional.",
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
Features: {"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger e acima da SMA50 (+11,17%), porém permanece abaixo da SMA200 (-10,54%), indicando conflito entre tendências de médio e longo prazo. O RSI em 57,83 está em zona neutra, enquanto o MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), sugerindo fraqueza no momento recente.",
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
Features: {"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger e acima da SMA50 (sma50_gap positivo de 11,17%), porém permanece significativamente abaixo da SMA200 (sma200_gap de -10,54%), indicando tendência primária de baixa. Adicionalmente, o MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio), enquanto o RSI em 57,83 sinaliza momento neutro a moderadamente positivo, gerando sinais técnicos conflitantes que recomendam cautela.",
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
Features: {"bb_lower_gap": 0.057998, "bb_upper_gap": -0.028467, "bb_width": 0.085206, "macd_ratio": 0.023349, "macd_signal_ratio": 0.028067, "rsi": 57.834426, "sma200_gap": -0.105383, "sma50_gap": 0.111668}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço opera dentro das bandas de Bollinger, acima da SMA50 (+11,17%), mas significativamente abaixo da SMA200 (-10,54%), indicando conflito entre as tendências de médio e longo prazo. O RSI em 57,83 é neutro e o MACD está abaixo de sua linha de sinal, recomendando cautela.",
  "signal": "MANTER"
}
```

## 2021-01-21

Features: `{"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preco permanece acima das medias moveis de longo e medio prazo (sma200_gap de +24,63% e sma50_gap de +2,46%), indicando tendencia estrutural de alta. No entanto, no curto prazo, o MACD esta abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI esta em 44,74, apontando perda de forca compradora e posicionamento no terco inferior das Bandas de Bollinger sem configurar sobrevenda extrema. Os sinais conflitantes entre a tendencia longa e a fraqueza de curto prazo recomendam manutencao.",
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
Features: {"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos (sma50_gap > 0 e sma200_gap > 0), indicando tendência de alta no longo prazo. No entanto, o MACD está abaixo de sua linha de sinal (macd_ratio < macd_signal_ratio), o RSI em 44.74 denota momento neutro/fraco e o preço está dentro das bandas de Bollinger, sugerindo consolidação ou correção temporária sem sinal claro de entrada ou saída imediata.",
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
Features: {"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo opera acima das médias móveis de 50 e 200 períodos (sma50_gap positivo e sma200_gap expressivo), sustentando a tendência estrutural de alta. No entanto, o MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI encontra-se em patamar neutro a fraco (44.74), indicando perda de momentum e ausência de confirmação para novas entradas no momento.",
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
Features: {"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos (sma50_gap positivo e sma200_gap expressivo), indicando tendência estrutural de alta. No entanto, o MACD está abaixo da sua linha de sinal e o RSI em 44.74 indica perda de momentum recente, com o preço oscilando dentro das bandas de Bollinger sem sinal claro de reversão ou compra imediata.",
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
Features: {"bb_lower_gap": 0.044078, "bb_upper_gap": -0.12551, "bb_width": 0.176787, "macd_ratio": 0.015047, "macd_signal_ratio": 0.030333, "rsi": 44.742948, "sma200_gap": 0.24633, "sma50_gap": 0.02456}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço permanece acima das médias móveis de 50 e 200 períodos (sma50_gap > 0 e sma200_gap > 0), indicando tendência estrutural de alta. No entanto, o MACD está abaixo da sua linha de sinal (macd_ratio < macd_signal_ratio) e o RSI em 44.74 sinaliza perda de força compradora no curto prazo, sugerindo consolidação dentro das Bandas de Bollinger sem gatilho claro de compra ou venda.",
  "signal": "MANTER"
}
```

## 2021-09-22

Features: `{"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço encontra-se dentro das Bandas de Bollinger, com RSI neutro em 47.90. Embora o fechamento esteja acima da SMA 200 (+4.14%), está ligeiramente abaixo da SMA 50 (-1.45%) e o MACD permanece negativo e abaixo de sua linha de sinal, indicando ausência de tendência direcional clara e recomendando manutenção da posição.",
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
Features: {"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço encontra-se dentro das bandas de Bollinger com RSI neutro em 47.90. Embora permaneça acima da SMA200 indicando suporte de longo prazo, está abaixo da SMA50 e o MACD opera abaixo de zero e abaixo da sua linha de sinal, gerando sinais mistos que recomendam cautela.",
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
Features: {"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das Bandas de Bollinger e ligeiramente acima da SMA200, porém abaixo da SMA50. O MACD opera abaixo de zero e abaixo da sua linha de sinal, indicando momentum negativo no curto prazo. Contudo, o RSI em 47,90 permanece neutro, sem sinal claro de sobrevenda ou sobrecompra, justificando cautela e manutenção de posição.",
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
Features: {"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço encontra-se dentro das Bandas de Bollinger e acima da SMA200, indicando tendência estrutural positiva no longo prazo. No entanto, opera abaixo da SMA50 e apresenta MACD negativo e abaixo da linha de sinal, com RSI neutro em 47,90, refletindo perda de momentum no curto prazo e ausência de viés direcional claro.",
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
Features: {"bb_lower_gap": 0.071759, "bb_upper_gap": -0.094342, "bb_width": 0.167998, "macd_ratio": -0.014073, "macd_signal_ratio": -0.009938, "rsi": 47.904148, "sma200_gap": 0.04144, "sma50_gap": -0.014545}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está contido dentro das Bandas de Bollinger e opera acima da SMA 200, mas abaixo da SMA 50. O MACD permanece negativo e abaixo da linha de sinal, enquanto o RSI está em patamar neutro (47,9), sem convicção direcional clara.",
  "signal": "MANTER"
}
```

## 2022-04-07

Features: `{"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "COMPRA", "target_weight": 1.0, "final_cause": "ACTION_BUY"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima de ambas as médias móveis (SMA50 e SMA200), indicando tendência de alta sustentada. O MACD opera acima de zero e de sua linha de sinal, e o RSI em 60 aponta força compradora sem indicar sobrecompra extrema. Além disso, o fechamento ligeiramente acima da banda superior de Bollinger reforça o momento altista.",
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
Features: {"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), ligeiramente acima da banda superior de Bollinger. O MACD opera acima de zero e de sua linha de sinal, e o RSI em 60.14 indica força compradora sem sobrecompra extrema.",
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
Features: {"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando forte tendência de alta. O fechamento está ligeiramente acima da banda superior de Bollinger (bb_upper_gap > 0). O MACD opera acima da linha de sinal e acima de zero, enquanto o RSI em 60.14 aponta predomínio de força compradora sem indicar sobrecompra extrema.",
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
Features: {"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), com forte alinhamento de alta. A linha MACD está positiva e acima da linha de sinal. O fechamento situa-se ligeiramente acima da banda superior de Bollinger (bb_upper_gap > 0) com RSI em 60,14, indicando forte momentum altista sem sobrecompra extrema.",
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
Features: {"bb_lower_gap": 0.12889, "bb_upper_gap": 0.000103, "bb_width": 0.120984, "macd_ratio": 0.005715, "macd_signal_ratio": 0.001109, "rsi": 60.136134, "sma200_gap": 0.249932, "sma50_gap": 0.041641}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), indicando forte tendência de alta. O fechamento está ligeiramente acima da banda superior de Bollinger (bb_upper_gap > 0), com momentum positivo confirmado pelo MACD acima de zero e acima de sua linha de sinal, e RSI em 60,14 denotando força compradora sem sobrecompra extrema.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.
Avalie apenas o sinal e as métricas fornecidas. Preserve capital, não invente
dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.371407}, "technical_signal": {"confidence": 0.762, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "Sinal técnico com forte consenso (5/5 votos) e alta confiança (76.2%). Métricas de risco sob controle: drawdown zerado, concentração nula e volatilidade recente compatível com o perfil operacional. Entrada permitida respeitando limites normais de dimensionamento de posição.",
  "risk_metrics": {
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.371407
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
{"risk_verdict": {"analysis": "Sinal técnico com forte consenso (5/5 votos) e alta confiança (76.2%). Métricas de risco sob controle: drawdown zerado, concentração nula e volatilidade recente compatível com o perfil operacional. Entrada permitida respeitando limites normais de dimensionamento de posição.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.371407}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.762, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "decision": "COMPRA",
  "reasoning": "Sinal técnico aprovado com forte consenso (5/5 votos), confiança elevada (76.2%) e validação positiva de risco sem impedimentos operacionais."
}
```

## 2022-11-01

Features: `{"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}`

Consenso: `{"vote_counts": {"COMPRA": 0, "MANTER": 5, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "MANTER"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "AUTO_APPROVE", "risk_rule": null, "portfolio_called": false, "portfolio_source": "RULE", "portfolio_rule": "TECH_HOLD", "portfolio_decision": "MANTER", "target_weight": null, "final_cause": "TECH_EXPLICIT_HOLD"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.6,
  "justification": "O preço está próximo da banda inferior de Bollinger e abaixo da SMA50, indicando fraqueza no médio prazo, embora permaneça bem acima da SMA200 (tendência primária de alta). O MACD opera abaixo de zero e abaixo da sua linha de sinal, e o RSI em 38,17 indica predominância de perdas recentes sem caracterizar sobrevenda extrema. Os sinais são mistos entre a correção de curto/médio prazo e a tendência altista de longo prazo.",
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
Features: {"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está bem próximo da banda inferior de Bollinger (bb_lower_gap em 0,66%) e abaixo da SMA50 (-7,89%), com RSI fraco em 38,17 e MACD negativo abaixo de sua linha de sinal, indicando momentum de baixa a curto prazo. No entanto, a tendência de longo prazo permanece positiva com o preço 15,70% acima da SMA200, sugerindo uma correção dentro de uma tendência de alta maior sem sinal claro de reversão ou entrada.",
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
Features: {"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está acima da SMA200 (tendência de longo prazo positiva), mas abaixo da SMA50 e próximo à banda inferior de Bollinger. O MACD opera abaixo de zero e abaixo da sua linha de sinal, acompanhado por um RSI em 38,17 indicando fraqueza no curto prazo sem caracterizar sobrevenda extrema. Os sinais são mistos entre a estrutura de longo e curto prazo.",
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
Features: {"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.62,
  "justification": "O preço está bem próximo da banda inferior de Bollinger (bb_lower_gap de 0,66%) e abaixo da SMA50 (-7,89%), com momentum negativo evidenciado pelo MACD abaixo da linha de sinal e RSI em 38,17. Contudo, o ativo ainda se mantém confortavelmente acima da SMA200 (+15,70%), sugerindo uma correção dentro de uma tendência de alta maior, sem confirmação suficiente de reversão para compra ou continuação de queda severa para venda.",
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
Features: {"bb_lower_gap": 0.006581, "bb_upper_gap": -0.195305, "bb_width": 0.222922, "macd_ratio": -0.002296, "macd_signal_ratio": 0.017815, "rsi": 38.16702, "sma200_gap": 0.157029, "sma50_gap": -0.078878}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O preço está acima da SMA200 indicando tendência primária de alta, porém opera abaixo da SMA50 com MACD negativo e abaixo da linha de sinal, sinalizando correção de médio prazo. Como o RSI está em 38.17 e o preço se aproxima da banda inferior de Bollinger sem configurar sobrevenda extrema, a postura mais prudente é aguardar definição.",
  "signal": "MANTER"
}
```

## 2023-06-26

Features: `{"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}`

Consenso: `{"vote_counts": {"COMPRA": 3, "MANTER": 2, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "VETADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": false, "portfolio_source": null, "portfolio_rule": null, "portfolio_decision": null, "target_weight": null, "final_cause": "RISK_VETO_LLM"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo apresenta forte tendência de alta, com preço bem acima das médias móveis de 50 e 200 períodos e MACD positivo e acima do sinal. No entanto, o RSI aproxima-se da região de sobrecompra (69,19) e o preço já está próximo da banda superior de Bollinger, sugerindo cautela para novas entradas e recomendando a manutenção da posição.",
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
Features: {"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.65,
  "justification": "O ativo exibe forte tendência de alta com preço bem acima das médias de 50 e 200 períodos (sma50_gap e sma200_gap positivos) e MACD acima da linha de sinal e do zero. No entanto, o RSI aproxima-se da região de sobrecompra (69,19) e o preço negocia dentro das bandas de Bollinger, sugerindo manutenção da posição para evitar entradas tardias em níveis esticados.",
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
Features: {"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço está solidamente acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), com o MACD acima de zero e superando sua linha de sinal, além de um RSI forte próximo a 69 demonstrando predomínio comprador dentro das bandas de Bollinger.",
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
Features: {"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O preço está fortemente acima das médias móveis de 50 e 200 períodos (sma50_gap de 22,49% e sma200_gap de 36,00%), indicando tendência de alta robusta. O MACD opera acima de zero e de sua linha de sinal (macd_ratio > macd_signal_ratio), confirmando momentum positivo. O RSI em 69,19 reflete força compradora sem estar em patamar extremo de exaustão, e o fechamento permanece dentro das bandas de Bollinger.",
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
Features: {"bb_lower_gap": 0.32177, "bb_upper_gap": -0.070077, "bb_width": 0.348047, "macd_ratio": 0.059052, "macd_signal_ratio": 0.05556, "rsi": 69.188726, "sma200_gap": 0.360013, "sma50_gap": 0.224886}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.78,
  "justification": "O ativo apresenta forte tendência de alta, situando-se bem acima das médias de 50 e 200 períodos. O MACD opera positivo e acima da linha de sinal, e o RSI em 69 reflete forte momentum comprador sem ainda romper a banda superior de Bollinger.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.
Avalie apenas o sinal e as métricas fornecidas. Preserve capital, não invente
dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.364617}, "technical_signal": {"confidence": 0.462, "justification": "Consenso coletivo: 3/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "O sinal técnico apresenta uma confiança baixa de 0.462 (abaixo do limiar de 50%), com consenso fraco (3/5 votos). Somado à volatilidade recente elevada de 36.46%, a relação risco/retorno é desfavorável para a preservação de capital.",
  "risk_metrics": {
    "confidence": 0.462,
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.364617
  },
  "verdict": "VETADO"
}
```

## 2023-12-18

Features: `{"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}`

Consenso: `{"vote_counts": {"COMPRA": 5, "MANTER": 0, "VENDA": 0}, "valid_votes": 5, "consensus_reached": true, "technical_outcome": "COMPRA"}`

Códigos: `{"risk_verdict": "APROVADO", "risk_source": "LLM", "risk_rule": null, "portfolio_called": true, "portfolio_source": "LLM", "portfolio_rule": null, "portfolio_decision": "COMPRA", "target_weight": 1.0, "final_cause": "ACTION_BUY"}`

Checker semântico: `{"technical_votes": 5, "votes_with_contradiction": 0, "votes_with_transition": 0, "contradiction_rate": 0.0, "transition_rate": 0.0}`

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
Features: {"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando forte tendência de alta. O MACD está acima de zero e da sua linha de sinal (macd_ratio > macd_signal_ratio), enquanto o RSI em 59,6 indica momentum favorável sem sobrecompra. O fechamento permanece contido dentro das bandas de Bollinger, próximo à banda superior.",
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
Features: {"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando forte tendência de alta. O MACD está acima de zero e superando sua linha de sinal, enquanto o RSI em 59,6 indica momentum comprador saudável sem condições de sobrecompra, com o preço contido dentro das bandas de Bollinger.",
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
Features: {"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando forte tendência de alta. O MACD está positivo e acima da sua linha de sinal, com RSI em patamar construtivo (59.60) sem indicar sobrecompra extrema, e as cotações permanecem dentro das bandas de Bollinger próximas ao limite superior.",
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
Features: {"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O preço opera acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos), confirmando forte tendência de alta. O MACD está positivo e acima de sua linha de sinal, acompanhado por um RSI em 59,60 em zona construtiva sem sobrecompra, com o preço contido dentro das bandas de Bollinger próximo à banda superior.",
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
Features: {"bb_lower_gap": 0.068378, "bb_upper_gap": -0.013709, "bb_width": 0.079902, "macd_ratio": 0.005123, "macd_signal_ratio": 0.003284, "rsi": 59.599672, "sma200_gap": 0.29143, "sma50_gap": 0.036253}
Emit COMPRA, VENDA, or MANTER based solely on these quantitative metrics.
```

Saída visível:

```json
{
  "confidence": 0.75,
  "justification": "O ativo opera em clara tendência de alta estrutural, com o preço acima das médias móveis de 50 e 200 períodos (sma50_gap e sma200_gap positivos). O momentum segue altista com a linha MACD acima da linha de sinal e RSI em patamar favorável (59.6) sem indicar sobrecompra, mantendo-se dentro das bandas de Bollinger.",
  "signal": "COMPRA"
}
```

### risk_manager

System prompt:

```text
Você é o gestor de risco do Hedge-fund-lab.
Avalie apenas o sinal e as métricas fornecidas. Preserve capital, não invente
dados e retorne APROVADO ou VETADO com análise objetiva.
```

User prompt:

```text
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.239236}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "analysis": "Sinal de COMPRA com alta confiança (75%) respaldado por consenso unânime dos modelos. As métricas de risco atuais estão totalmente controladas, apresentando drawdown zerado, ausência de concentração e volatilidade recente compatível com os limites operacionais aceitáveis.",
  "risk_metrics": {
    "current_concentration": 0.0,
    "current_drawdown": 0.0,
    "recent_volatility": 0.239236
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
{"risk_verdict": {"analysis": "Sinal de COMPRA com alta confiança (75%) respaldado por consenso unânime dos modelos. As métricas de risco atuais estão totalmente controladas, apresentando drawdown zerado, ausência de concentração e volatilidade recente compatível com os limites operacionais aceitáveis.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.239236}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

Saída visível:

```json
{
  "decision": "COMPRA",
  "reasoning": "Sinal técnico de COMPRA aprovado pelo gerenciamento de risco com 75% de confiança e consenso unânime dos modelos, respaldado por métricas de risco favoráveis e drawdown controlado."
}
```

