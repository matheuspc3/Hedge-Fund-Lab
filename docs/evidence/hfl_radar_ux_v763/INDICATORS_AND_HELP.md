# Indicadores e ajuda contextual

O glossário continua exclusivamente em `dashboard/glossary.js`. Os quatro novos
ids são `sma50`, `sma200`, `sessao-referencia` e `parecer-oficial` (40 termos no total).
Os demais termos reutilizam as definições existentes; não há segundo tooltip.

| Campo registrado | Apresentação | Base validada no código |
|---|---|---|
| `rsi` | Número de 0 a 100 e medidor | Wilder, 14 períodos |
| `sma50_gap`, `sma200_gap` | Percentual relativo | fechamento / média − 1; 50/200 sessões |
| `macd_ratio` | Percentual do fechamento | (EMA12 − EMA26) / fechamento |
| `macd_signal_ratio` | Percentual do fechamento | EMA9 do MACD / fechamento |
| `bb_upper_gap`, `bb_lower_gap` | Distância relativa em % | fechamento / banda − 1 |
| `bb_width` | Largura relativa em % | (banda superior − inferior) / média; 20 períodos, 2 desvios |
| `asset_volatility_21` | Volatilidade anualizada em % | Janela de 21 retornos, não preço absoluto |

Referências lidas: `src/agents/features.py::dimensionless_features`,
`scripts/multiasset_radar.py::technical_input` e regra de risco de `committee`,
além das definições existentes do glossário. A confiança técnica permanece na
escala 0–1; a contagem de votos e o limiar vêm do consenso registrado.

Ajuda disponível para RSI, MACD, médias, Bollinger, volatilidade, consenso,
confiança, Risk, veto, parecer oficial, sessão e inferência paga. Explicação curta,
expansão, exemplo, ressalva e referência de código usam o mecanismo V7.6.2.
Nenhum cálculo científico ou limiar foi alterado.
