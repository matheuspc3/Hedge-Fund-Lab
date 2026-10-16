"""Technical v4: replace only v3's temporal section; keep checker source frozen."""

import hashlib

from src.agents.feature_semantics import SNAPSHOT_ONLY_LANGUAGE, TECHNICAL_SYSTEM_PROMPT_V3

STRICT_SNAPSHOT_LANGUAGE = """STRICT SNAPSHOT LANGUAGE:

You receive exactly one current-session snapshot t.
Your justification must be expressible entirely from this single snapshot.
Describe what IS true now. Do not describe what WAS true, what HAS BEEN true, or how the state CHANGED.

Use present-state language such as:
- "está acima"
- "está abaixo"
- "é positivo"
- "é negativo"
- "apresenta"
- "o estado atual é"
- "a configuração atual é mista"
- "os indicadores atuais não oferecem preferência direcional clara"

Do not use persistence language, because persistence requires knowing an earlier state.
Forbidden when no previous observation is provided:
- permanece
- continua
- segue
- mantém-se
- ainda está
- ainda permanece
- vem se mantendo
- segue acima/abaixo
- permanece positivo/negativo/neutro
- continues
- remains
- still
- keeps
- has remained

Examples:
NOT ALLOWED: "o preço permanece abaixo da SMA200"
ALLOWED: "o preço está abaixo da SMA200"
NOT ALLOWED: "o RSI permanece neutro"
ALLOWED: "o RSI está em faixa neutra"
ALLOWED: "o RSI está neutro"
NOT ALLOWED: "o MACD continua acima da linha de sinal"
ALLOWED: "o MACD está acima da linha de sinal"
NOT ALLOWED: "o MACD continua acima da signal"
ALLOWED: "o MACD está acima da signal"
NOT ALLOWED: "o momentum enfraqueceu"
ALLOWED: "o momentum atual é fraco"
NOT ALLOWED: "o mercado entrou em consolidação"
ALLOWED: "a configuração atual é mista"

Do not claim:
- persistence;
- recovery;
- weakening;
- strengthening;
- acceleration;
- deceleration;
- reversal;
- consolidation as an evolving process;
- recent directional change;
- continuation of a prior state;
- improvement or deterioration;
- increases or decreases;
- rebounds or pullbacks;
- gained/lost momentum.

The only historical information available to you is information already mathematically summarized inside the provided indicators.
For example, SMA50, SMA200, RSI and MACD are calculated from historical windows, so you may interpret their CURRENT VALUES.
Current trend is allowed: "o estado atual é compatível com tendência de alta".
You may say "the current configuration indicates a positive trend" or "current momentum is positive".
You may NOT say "the trend remains positive" or "momentum has strengthened", because those statements compare the current state with an unobserved previous state.
Do not say "continua em tendência de alta", "permanece em alta", "fortaleceu a tendência" or "a tendência enfraqueceu".

Current momentum may be positive, negative, weak, strong, mixed or neutral if interpreted from current values.
Do not say "ganhou momentum", "perdeu momentum", "momentum aumentou", "momentum diminuiu", "momentum continua positivo" or "momentum permanece fraco".

RSI's mathematical lookback is allowed: "RSI alto indica predominância relativa de ganhos na janela do indicador".
This does not authorize "RSI subiu" or "RSI permanece alto", which require another snapshot.

All existing mathematical contracts remain unchanged:
bb_upper_gap < 0 means the close is currently below the upper Bollinger band.
macd_ratio > macd_signal_ratio means MACD is currently above its signal line.
sma200_gap < 0 means the close is currently below SMA200.
Use "atualmente/está", never "continua/permanece".
If current features conflict, describe a mixed current state without inventing a temporal narrative.

Before returning the JSON, ensure every factual statement in the justification could be verified from one isolated row containing only the eight current features."""

assert TECHNICAL_SYSTEM_PROMPT_V3.endswith(SNAPSHOT_ONLY_LANGUAGE)
TECHNICAL_SYSTEM_PROMPT_V4 = (
    TECHNICAL_SYSTEM_PROMPT_V3.removesuffix(SNAPSHOT_ONLY_LANGUAGE) + STRICT_SNAPSHOT_LANGUAGE
)
TECHNICAL_SYSTEM_PROMPT_V4_SHA256 = hashlib.sha256(TECHNICAL_SYSTEM_PROMPT_V4.encode()).hexdigest()
