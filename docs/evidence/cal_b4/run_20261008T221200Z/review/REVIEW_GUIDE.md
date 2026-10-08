# CAL-B4 — guia da revisão obrigatória

Estado automático: CAL_B4_AWAITING_PRIMARY_AUTHOR_REVIEW.

Preencha apenas PRIMARY_AUTHOR.json: reviewer, reviewed_utc e PASS/FAIL nos quatro campos de cada anchor. Nenhum julgamento humano foi preenchido pelo assistente.

1. technical_evidence_factual_validity: evidências correspondem ao snapshot e allowed set.
2. technical_role_signal_coherence: incoerência material evidente entre roles e sinal. Não aplicar regra determinística; evidências podem conflitar. Discordar da recomendação não é FAIL.
3. material_unsupported_claim: fato/regra não fornecido que pesa no texto, principalmente Risk/Portfolio.
4. rationale_action_coherence: Risk analysis/verdict e Portfolio reasoning/decision coerentes.

Um FAIL material reprova; todos os 40 campos PASS são necessários para aprovação humana.
Segunda revisão: NOT_REVIEWED — NONBLOCKING. FINANCIAL_OUTCOME = NOT COMPUTED.

Esta é uma apresentação determinística dos campos do audit_packet.json. Ela não substitui a ficha nem constitui classificação humana.
Source audit_packet SHA256: 9c929c75c59ef8f27ebf3b1d9453ef032d9edddb31d4304bf6996fbae6e0b068

## 2018-08-21

Features causais (8):

```json
{
  "sma50_gap": -0.018905,
  "sma200_gap": -0.065967,
  "bb_upper_gap": -0.172587,
  "bb_lower_gap": -0.01443,
  "bb_width": 0.174472,
  "rsi": 36.476643,
  "macd_ratio": -0.00273,
  "macd_signal_ratio": 0.016864
}
```

Allowed evidence codes: `CLOSE_BELOW_SMA50, CLOSE_BELOW_SMA200, CLOSE_BELOW_BB_LOWER, MACD_NEGATIVE, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: VENDA; votos {"COMPRA": 0, "MANTER": 0, "VENDA": 5}.
Final cause: ACTION_SELL; Risk APROVADO (AUTO_APPROVE); Portfolio VENDA.

### Technical — 5 votos

Voto 1: **VENDA**; confidence 0.78.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_BELOW_SMA50 | SUPPORTS_VENDA | fechamento abaixo da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| CLOSE_BELOW_BB_LOWER | SUPPORTS_VENDA | fechamento abaixo da banda inferior de Bollinger |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 36.476643 |

Voto 2: **VENDA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_BELOW_SMA50 | SUPPORTS_VENDA | fechamento abaixo da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| CLOSE_BELOW_BB_LOWER | SUPPORTS_VENDA | fechamento abaixo da banda inferior de Bollinger |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 36.476643 |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.174472 |

Voto 3: **VENDA**; confidence 0.8.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| CLOSE_BELOW_SMA50 | SUPPORTS_VENDA | fechamento abaixo da SMA50 |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| CLOSE_BELOW_BB_LOWER | SUPPORTS_VENDA | fechamento abaixo da banda inferior de Bollinger |
| RSI_CURRENT | CAUTION | RSI atual = 36.476643 |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.174472 |

Voto 4: **VENDA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_BELOW_SMA50 | SUPPORTS_VENDA | fechamento abaixo da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| CLOSE_BELOW_BB_LOWER | SUPPORTS_VENDA | fechamento abaixo da banda inferior de Bollinger |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 36.476643 |

Voto 5: **VENDA**; confidence 0.78.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_BELOW_SMA50 | SUPPORTS_VENDA | fechamento abaixo da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| CLOSE_BELOW_BB_LOWER | SUPPORTS_VENDA | fechamento abaixo da banda inferior de Bollinger |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 36.476643 |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.174472 |

### Risk — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

### Portfolio — texto visível

Resultado: **VENDA**.

Sinal técnico com forte consenso de venda (5/5 votos, confiança de 77.2%) e devidamente aprovado pela gestão de risco sem aumento de exposição.

Payload recebido:

```json
{"risk_verdict": {"analysis": "Operação não aumenta a exposição", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.363847}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.772, "justification": "Consenso coletivo: 5/5 votos em VENDA", "signal": "VENDA"}}
```

## 2019-01-29

Features causais (8):

```json
{
  "sma50_gap": 0.05827,
  "sma200_gap": 0.207783,
  "bb_upper_gap": -0.032761,
  "bb_lower_gap": 0.072968,
  "bb_width": 0.103646,
  "rsi": 58.223999,
  "macd_ratio": 0.018685,
  "macd_signal_ratio": 0.018516
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_ABOVE_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: COMPRA; votos {"COMPRA": 5, "MANTER": 0, "VENDA": 0}.
Final cause: ACTION_BUY; Risk APROVADO (LLM); Portfolio COMPRA.

### Technical — 5 votos

Voto 1: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 58.223999 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.103646 |

Voto 2: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 58.223999 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 58.223999 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.103646 |

Voto 4: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.223999 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.103646 |

Voto 5: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 58.223999 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Resultado: **APROVADO**.

A operação de compra apresenta alinhamento técnico unânime (5/5 votos em COMPRA). As métricas de risco atuais estão controladas, com concentração nula (0.0) e drawdown zerado (0.0), permitindo a absorção da volatilidade recente observada (0.325005) sem indicar risco inadequado para a preservação de capital.

Payload recebido:

```json
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.325005}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

### Portfolio — texto visível

Resultado: **COMPRA**.

Sinal técnico unânime de compra validado e aprovado pela gestão de risco, com métricas de concentração e drawdown zeradas.

Payload recebido:

```json
{"risk_verdict": {"analysis": "A operação de compra apresenta alinhamento técnico unânime (5/5 votos em COMPRA). As métricas de risco atuais estão controladas, com concentração nula (0.0) e drawdown zerado (0.0), permitindo a absorção da volatilidade recente observada (0.325005) sem indicar risco inadequado para a preservação de capital.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.325005}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

## 2019-10-28

Features causais (8):

```json
{
  "sma50_gap": 0.103835,
  "sma200_gap": 0.114192,
  "bb_upper_gap": 0.001362,
  "bb_lower_gap": 0.16009,
  "bb_width": 0.146871,
  "rsi": 69.728381,
  "macd_ratio": 0.020491,
  "macd_signal_ratio": 0.01356
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_ABOVE_BB_UPPER, MACD_POSITIVE, MACD_ABOVE_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: COMPRA; votos {"COMPRA": 5, "MANTER": 0, "VENDA": 0}.
Final cause: ACTION_BUY; Risk APROVADO (LLM); Portfolio COMPRA.

### Technical — 5 votos

Voto 1: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_BB_UPPER | CAUTION | fechamento acima da banda superior de Bollinger |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 69.728381 |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.146871 |

Voto 2: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| CLOSE_ABOVE_BB_UPPER | CAUTION | fechamento acima da banda superior de Bollinger |
| RSI_CURRENT | CAUTION | RSI atual = 69.728381 |

Voto 3: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_BB_UPPER | CAUTION | fechamento acima da banda superior de Bollinger |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 69.728381 |

Voto 4: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| CLOSE_ABOVE_BB_UPPER | CAUTION | fechamento acima da banda superior de Bollinger |
| RSI_CURRENT | CAUTION | RSI atual = 69.728381 |

Voto 5: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| CLOSE_ABOVE_BB_UPPER | CAUTION | fechamento acima da banda superior de Bollinger |
| RSI_CURRENT | CAUTION | RSI atual = 69.728381 |

### Risk — texto visível

Resultado: **APROVADO**.

O sinal de COMPRA apresenta consenso pleno (5/5) e suporte qualitativo adequado com confiança de 0.75. As métricas de risco mostram concentração atual zerada (0.0) e ausência de drawdown recente (0.0), com volatilidade controlada em 0.245737. O contexto de risco suporta a execução da operação sem indicação de exposição excessiva.

Payload recebido:

```json
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.245737}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

### Portfolio — texto visível

Resultado: **COMPRA**.

Sinal técnico de COMPRA com consenso unânime (5/5) e confiança de 0.75 devidamente aprovado pelo comitê de risco, apresentando métricas de volatilidade controladas e ausência de drawdown ou concentração prévia.

Payload recebido:

```json
{"risk_verdict": {"analysis": "O sinal de COMPRA apresenta consenso pleno (5/5) e suporte qualitativo adequado com confiança de 0.75. As métricas de risco mostram concentração atual zerada (0.0) e ausência de drawdown recente (0.0), com volatilidade controlada em 0.245737. O contexto de risco suporta a execução da operação sem indicação de exposição excessiva.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.245737}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.75, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

## 2020-06-03

Features causais (8):

```json
{
  "sma50_gap": 0.252991,
  "sma200_gap": -0.126102,
  "bb_upper_gap": -0.004953,
  "bb_lower_gap": 0.298448,
  "bb_width": 0.264576,
  "rsi": 70.605385,
  "macd_ratio": 0.044604,
  "macd_signal_ratio": 0.033551
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_BELOW_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_ABOVE_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: MANTER; votos {"COMPRA": 0, "MANTER": 5, "VENDA": 0}.
Final cause: TECH_EXPLICIT_HOLD; Risk APROVADO (AUTO_APPROVE); Portfolio MANTER.

### Technical — 5 votos

Voto 1: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 70.605385 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 2: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 70.605385 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 70.605385 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | CAUTION | RSI atual = 70.605385 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 5: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| CLOSE_BELOW_SMA200 | SUPPORTS_VENDA | fechamento abaixo da SMA200 |
| RSI_CURRENT | CAUTION | RSI atual = 70.605385 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.264576 |

### Risk — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

### Portfolio — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

## 2021-02-18

Features causais (8):

```json
{
  "sma50_gap": 0.036025,
  "sma200_gap": 0.267027,
  "bb_upper_gap": -0.014674,
  "bb_lower_gap": 0.104441,
  "bb_width": 0.113999,
  "rsi": 57.376505,
  "macd_ratio": 0.007232,
  "macd_signal_ratio": 0.003829
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_ABOVE_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: COMPRA; votos {"COMPRA": 5, "MANTER": 0, "VENDA": 0}.
Final cause: ACTION_BUY; Risk APROVADO (LLM); Portfolio COMPRA.

### Technical — 5 votos

Voto 1: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 57.376505 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 2: **COMPRA**; confidence 0.78.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 57.376505 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 57.376505 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 57.376505 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 5: **COMPRA**; confidence 0.75.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 57.376505 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Resultado: **APROVADO**.

O sinal técnico de compra apresenta unanimidade no consenso com nível de confiança positivo. As métricas de risco indicam ausência de drawdown atual (0.0) e concentração zerada (0.0), permitindo a alocação de capital sob a volatilidade recente reportada (0.348847) sem violar restrições da carteira.

Payload recebido:

```json
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.348847}, "technical_signal": {"confidence": 0.756, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

### Portfolio — texto visível

Resultado: **COMPRA**.

O sinal técnico de COMPRA foi aprovado por unanimidade (5/5) com confiança de 0.756 e devidamente validado pela gestão de risco sem violações de limites de carteira.

Payload recebido:

```json
{"risk_verdict": {"analysis": "O sinal técnico de compra apresenta unanimidade no consenso com nível de confiança positivo. As métricas de risco indicam ausência de drawdown atual (0.0) e concentração zerada (0.0), permitindo a alocação de capital sob a volatilidade recente reportada (0.348847) sem violar restrições da carteira.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.348847}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.756, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

## 2021-09-02

Features causais (8):

```json
{
  "sma50_gap": 0.000597,
  "sma200_gap": 0.081449,
  "bb_upper_gap": -0.060032,
  "bb_lower_gap": 0.019727,
  "bb_width": 0.0814,
  "rsi": 46.791693,
  "macd_ratio": 0.010544,
  "macd_signal_ratio": 0.012989
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: MANTER; votos {"COMPRA": 0, "MANTER": 5, "VENDA": 0}.
Final cause: TECH_EXPLICIT_HOLD; Risk APROVADO (AUTO_APPROVE); Portfolio MANTER.

### Technical — 5 votos

Voto 1: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 46.791693 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_POSITIVE | CAUTION | MACD acima de zero |

Voto 2: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 46.791693 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_POSITIVE | CAUTION | MACD acima de zero |

Voto 3: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 46.791693 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 46.791693 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_POSITIVE | CAUTION | MACD acima de zero |

Voto 5: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | NEUTRAL | fechamento acima da SMA50 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 46.791693 |

### Risk — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

### Portfolio — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

## 2022-03-30

Features causais (8):

```json
{
  "sma50_gap": 0.013474,
  "sma200_gap": 0.223392,
  "bb_upper_gap": -0.039579,
  "bb_lower_gap": 0.101705,
  "bb_width": 0.137028,
  "rsi": 55.069401,
  "macd_ratio": -0.002302,
  "macd_signal_ratio": -0.005071
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_NEGATIVE, MACD_ABOVE_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: COMPRA; votos {"COMPRA": 5, "MANTER": 0, "VENDA": 0}.
Final cause: ACTION_BUY; Risk APROVADO (LLM); Portfolio COMPRA.

### Technical — 5 votos

Voto 1: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| MACD_NEGATIVE | CAUTION | MACD abaixo de zero |
| RSI_CURRENT | NEUTRAL | RSI atual = 55.069401 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 2: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| MACD_NEGATIVE | CAUTION | MACD abaixo de zero |
| RSI_CURRENT | NEUTRAL | RSI atual = 55.069401 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| MACD_NEGATIVE | CAUTION | MACD abaixo de zero |
| RSI_CURRENT | NEUTRAL | RSI atual = 55.069401 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 55.069401 |
| MACD_NEGATIVE | CAUTION | MACD abaixo de zero |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 5: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_ABOVE_SIGNAL | SUPPORTS_COMPRA | MACD acima da linha de sinal |
| MACD_NEGATIVE | CAUTION | MACD abaixo de zero |
| RSI_CURRENT | NEUTRAL | RSI atual = 55.069401 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Resultado: **APROVADO**.

A operação foi aprovada considerando que a concentração e o drawdown atuais estão zerados, permitindo alocação de risco. O sinal técnico aponta compra com consenso integral (5/5 votos) e nível de confiança qualitativamente consistente. A volatilidade recente de 0.417316 é absorvida sem conflito com o estado zerado de risco prévio da carteira.

Payload recebido:

```json
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.417316}, "technical_signal": {"confidence": 0.65, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

### Portfolio — texto visível

Resultado: **COMPRA**.

O sinal técnico de COMPRA obteve consenso integral de 5/5 votos com 65% de confiança, e a operação foi expressamente aprovada pelo comitê de risco, dado que a carteira possui concentração e drawdown zerados, permitindo alocação segura na direção apontada.

Payload recebido:

```json
{"risk_verdict": {"analysis": "A operação foi aprovada considerando que a concentração e o drawdown atuais estão zerados, permitindo alocação de risco. O sinal técnico aponta compra com consenso integral (5/5 votos) e nível de confiança qualitativamente consistente. A volatilidade recente de 0.417316 é absorvida sem conflito com o estado zerado de risco prévio da carteira.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.417316}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.65, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

## 2022-10-03

Features causais (8):

```json
{
  "sma50_gap": 0.048174,
  "sma200_gap": 0.31908,
  "bb_upper_gap": -0.030207,
  "bb_lower_gap": 0.119357,
  "bb_width": 0.143182,
  "rsi": 58.184233,
  "macd_ratio": -0.00678,
  "macd_signal_ratio": -0.003245
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_NEGATIVE, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: MANTER; votos {"COMPRA": 0, "MANTER": 5, "VENDA": 0}.
Final cause: TECH_EXPLICIT_HOLD; Risk APROVADO (AUTO_APPROVE); Portfolio MANTER.

### Technical — 5 votos

Voto 1: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.184233 |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |

Voto 2: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.184233 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.184233 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.184233 |

Voto 5: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_NEGATIVE | SUPPORTS_VENDA | MACD abaixo de zero |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 58.184233 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

### Portfolio — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

## 2023-07-17

Features causais (8):

```json
{
  "sma50_gap": 0.054394,
  "sma200_gap": 0.255787,
  "bb_upper_gap": -0.08682,
  "bb_lower_gap": 0.019024,
  "bb_width": 0.109558,
  "rsi": 49.420307,
  "macd_ratio": 0.013234,
  "macd_signal_ratio": 0.025325
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: MANTER; votos {"COMPRA": 0, "MANTER": 5, "VENDA": 0}.
Final cause: TECH_EXPLICIT_HOLD; Risk APROVADO (AUTO_APPROVE); Portfolio MANTER.

### Technical — 5 votos

Voto 1: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 49.420307 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 2: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 49.420307 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | SUPPORTS_VENDA | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 49.420307 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| RSI_CURRENT | NEUTRAL | RSI atual = 49.420307 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 5: **MANTER**; confidence 0.55.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| MACD_POSITIVE | NEUTRAL | MACD acima de zero |
| RSI_CURRENT | NEUTRAL | RSI atual = 49.420307 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

### Portfolio — texto visível

Não chamado nesta anchor; consulte o fluxo e reason codes acima.

## 2024-01-12

Features causais (8):

```json
{
  "sma50_gap": 0.073394,
  "sma200_gap": 0.304207,
  "bb_upper_gap": -0.038292,
  "bb_lower_gap": 0.101486,
  "bb_width": 0.135497,
  "rsi": 63.676322,
  "macd_ratio": 0.022399,
  "macd_signal_ratio": 0.022457
}
```

Allowed evidence codes: `CLOSE_ABOVE_SMA50, CLOSE_ABOVE_SMA200, CLOSE_INSIDE_BOLLINGER, MACD_POSITIVE, MACD_BELOW_SIGNAL, RSI_CURRENT, BB_WIDTH_CURRENT`.

Consenso: COMPRA; votos {"COMPRA": 5, "MANTER": 0, "VENDA": 0}.
Final cause: ACTION_BUY; Risk APROVADO (LLM); Portfolio COMPRA.

### Technical — 5 votos

Voto 1: **COMPRA**; confidence 0.68.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 63.676322 |
| BB_WIDTH_CURRENT | NEUTRAL | largura relativa atual das bandas = 0.135497 |

Voto 2: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 63.676322 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 3: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 63.676322 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 4: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 63.676322 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

Voto 5: **COMPRA**; confidence 0.65.

| Code | Role | Fato no renderer |
|---|---|---|
| CLOSE_ABOVE_SMA50 | SUPPORTS_COMPRA | fechamento acima da SMA50 |
| CLOSE_ABOVE_SMA200 | SUPPORTS_COMPRA | fechamento acima da SMA200 |
| MACD_POSITIVE | SUPPORTS_COMPRA | MACD acima de zero |
| RSI_CURRENT | SUPPORTS_COMPRA | RSI atual = 63.676322 |
| MACD_BELOW_SIGNAL | CAUTION | MACD abaixo da linha de sinal |
| CLOSE_INSIDE_BOLLINGER | NEUTRAL | fechamento dentro das bandas de Bollinger |

### Risk — texto visível

Resultado: **APROVADO**.

A operação de COMPRA apresenta métricas de risco favoráveis com concentração e drawdown zerados (0.0). A volatilidade recente de 0.174734 é compatível com a tomada de risco, e o consenso técnico unânime com confiança moderada-alta apoia a entrada sem indicar risco excessivo.

Payload recebido:

```json
{"risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.174734}, "technical_signal": {"confidence": 0.656, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

### Portfolio — texto visível

Resultado: **COMPRA**.

O sinal técnico foi unânime (5/5) para COMPRA com confiança de 0.656 e o parecer de risco foi plenamente aprovado, apresentando métricas favoráveis de drawdown e concentração zerados com volatilidade controlada.

Payload recebido:

```json
{"risk_verdict": {"analysis": "A operação de COMPRA apresenta métricas de risco favoráveis com concentração e drawdown zerados (0.0). A volatilidade recente de 0.174734 é compatível com a tomada de risco, e o consenso técnico unânime com confiança moderada-alta apoia a entrada sem indicar risco excessivo.", "risk_metrics": {"current_concentration": 0.0, "current_drawdown": 0.0, "recent_volatility": 0.174734}, "verdict": "APROVADO"}, "technical_signal": {"confidence": 0.656, "justification": "Consenso coletivo: 5/5 votos em COMPRA", "signal": "COMPRA"}}
```

