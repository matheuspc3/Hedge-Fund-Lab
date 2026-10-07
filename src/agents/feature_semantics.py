"""Contrato semântico das 8 features e o prompt técnico científico v2.

Fonte única da verdade: o glossário enviado ao Technical (``TECHNICAL_SYSTEM_PROMPT_V2``)
é GERADO de :data:`FEATURE_SEMANTICS`, e o checker (:func:`audit_rationale`) confere
o rationale visível contra as mesmas relações. Nada daqui muda features, fórmulas
ou schema (``LLM_FEATURE_SCHEMA_VERSION`` continua 2); muda só o que o prompt diz
sobre elas.

Por que existe (Amendment 8): na v1 o prompt entregava só os nomes das razões, e o
modelo lia ``bb_upper_gap < 0`` como rompimento da banda superior.
"""

import re
from collections.abc import Mapping
from typing import Any

from src.agents.features import FEATURE_KEYS

#: Definição matemática e convenção de sinal de cada feature, na ordem de
#: ``FEATURE_KEYS``. Fórmulas iguais às de ``dimensionless_features`` e aos
#: parâmetros do ``DataTransformer`` (SMA 50/200, Bollinger 20/2, RSI de Wilder
#: 14, MACD 12/26/9).
FEATURE_SEMANTICS: Mapping[str, str] = {
    "bb_lower_gap": (
        "close / BollingerLower - 1. < 0: the close is below the lower band; = 0: on the lower band; "
        "> 0: above the lower band. A positive bb_lower_gap does NOT mean a close above the upper band, "
        "an upper breakout or overbought."
    ),
    "bb_upper_gap": (
        "close / BollingerUpper - 1. > 0: the close is above the upper band; = 0: on the upper band; "
        "< 0: below the upper band. A negative bb_upper_gap does NOT mean a close below the lower band, "
        "a break above the upper band, overbought, or a price above the band."
    ),
    "bb_width": (
        "(BollingerUpper - BollingerLower) / BollingerMiddle, the relative width of the bands: larger means "
        "relatively wider bands, smaller means relatively narrower bands. It has no bullish or bearish "
        "direction by itself."
    ),
    "macd_ratio": "MACD / close. Its sign tells whether the MACD line is currently above (> 0) or below (< 0) zero.",
    "macd_signal_ratio": (
        "MACD signal line / close, on the same dimensionless scale. If macd_ratio > macd_signal_ratio the MACD "
        "line is currently above its signal line; if macd_ratio < macd_signal_ratio it is currently below."
    ),
    "rsi": (
        "Wilder RSI, period 14, on a 0 to 100 scale. Higher values mean recent gains predominate over recent "
        "losses; lower values mean recent losses predominate."
    ),
    "sma200_gap": "close / SMA200 - 1. > 0: the close is above the SMA200; = 0: at the SMA200; < 0: below the SMA200.",
    "sma50_gap": "close / SMA50 - 1. > 0: the close is above the SMA50; = 0: at the SMA50; < 0: below the SMA50.",
}
assert tuple(FEATURE_SEMANTICS) == FEATURE_KEYS

BAND_RELATION = (
    "Inside the bands: bb_upper_gap <= 0 and bb_lower_gap >= 0. bb_upper_gap > 0 means the close is above the "
    "upper band; bb_lower_gap < 0 means the close is below the lower band."
)
STATE_NOT_TRANSITION = (
    "State, not transition: the features describe only the current session t; no earlier values are provided. "
    "You may state positions derivable from this snapshot (is above, is below, the MACD is above its signal "
    "line, the close is beyond the upper band). Do not state transitions that would require comparing with an "
    "earlier session (crossed, crossover, broke out, reversed, just entered), because a single snapshot cannot "
    "show them."
)
#: Papel, proibições e schema exatamente como no prompt v1.
_ROLE = (
    "You are the technical analyst for Hedge-fund-lab.\n"
    "Exclusively evaluate the dimensionless technical features provided. They are scale-free ratios: no price "
    "level, no asset identity and no calendar date are available, and none is required for this decision. "
    "Ignore news, external knowledge, and future prices."
)
_SCHEMA = (
    "Return JSON with signal (COMPRA, VENDA, or MANTER), a concise justification in Portuguese, and confidence "
    "between 0 and 1."
)


def technical_system_prompt_v2() -> str:
    glossary = "\n".join(f"- {key} = {FEATURE_SEMANTICS[key]}" for key in FEATURE_KEYS)
    return (
        f"{_ROLE}\n\nFeature definitions (close = closing price of the current session t; SMA50/SMA200 = simple "
        f"moving averages of the close over 50/200 sessions; Bollinger bands 20 sessions, 2 standard deviations; "
        f"MACD 12/26/9):\n{glossary}\n{BAND_RELATION}\n\n{STATE_NOT_TRANSITION}\n\n{_SCHEMA}"
    )


TECHNICAL_SYSTEM_PROMPT_V2 = technical_system_prompt_v2()
#: Identidade do prompt v2; mudar o texto exige nova versão de prompt.
TECHNICAL_SYSTEM_PROMPT_V2_SHA256 = "a3dec11f4c8911397c0f04ec5c0b7eb6265c420b3b6f7e3f494dd79ca43782e1"

SNAPSHOT_ONLY_LANGUAGE = """Snapshot-only language:
You receive only the current-session snapshot t. Therefore describe only relations observable in that snapshot.

Allowed examples:
- "the close is above the SMA50"
- "MACD is below its signal line"
- "RSI is neutral"
- "the current configuration is mixed"
- "the current indicators do not provide a clear directional preference"

Do not describe or imply how the state evolved over time unless previous-session values are explicitly provided.
Do not claim that price, trend, momentum or any indicator:
- recovered;
- weakened;
- strengthened;
- accelerated;
- decelerated;
- improved;
- deteriorated;
- increased or decreased;
- reversed;
- rebounded;
- pulled back;
- consolidated or is consolidating;
- recently changed;
- continues/remains in a state based on previous observations;
- gained/lost momentum.

Avoid temporal language such as "recently", "recent recovery", "continues", "remains", "has weakened", or equivalent expressions when they imply an unobserved earlier state.
You may describe current momentum as positive, negative, strong, weak, mixed or neutral when that characterization follows from the current features. Do not say that momentum became stronger/weaker.
If the snapshot is conflicting, describe it simply as a mixed current state. Do not invent a temporal narrative to explain the conflict."""

# Exact v2 text preserved as a prefix; no change to MANTER or feature semantics.
TECHNICAL_SYSTEM_PROMPT_V3 = TECHNICAL_SYSTEM_PROMPT_V2 + "\n\n" + SNAPSHOT_ONLY_LANGUAGE
TECHNICAL_SYSTEM_PROMPT_V3_SHA256 = "ca283bd920bbd0655d9c9a23eacd98fb6da48e6609097cb27cd835e9dee50759"
TECHNICAL_RATIONALE_CHECKER_VERSION = 3


# ── Checker semântico do rationale visível ───────────────────────

UNSUPPORTED_TRANSITION_CLAIM = "UNSUPPORTED_TRANSITION_CLAIM"
UNSUPPORTED_TEMPORAL_STATE_CLAIM = "UNSUPPORTED_TEMPORAL_STATE_CLAIM"

# ponytail: bounded clause patterns, not a language parser. New paraphrases need
# development-only golden cases and a new checker version, never holdout tuning.
_MARKET_SUBJECT = re.compile(
    r"\b(pre[çc]o|fechamento|ativo|tend[êe]ncia|momentum|momento|for[çc]a|rsi|macd|sma\w*|"
    r"m[ée]dia\w*|bandas?|indicador\w*|volatilidade|price|close|asset|trend|strength|"
    r"signal|indicators?|bands?|volatility)\b", re.I)
_EVOLUTION = re.compile(
    r"\b(recupera[çc][ãa]o|recuperou|recuperando|rebound(?:ed|ing)?|recover(?:ed|ing|y)|"
    r"fortaleceu|enfraqueceu|fortalec(?:imento|endo)|enfraquec(?:imento|endo)|"
    r"weaken(?:ed|ing)|strengthen(?:ed|ing)|acelerou|desacelerou|melhorou|piorou|deteriorou|"
    r"accelerat(?:ed|ing|ion)|decelerat(?:ed|ing|ion)|improv(?:ed|ing|ement)|worsen(?:ed|ing)|"
    r"deteriorat(?:ed|ing|ion)|consolida[çc][ãa]o|consolidando|consolidat(?:ed|ing|ion)|"
    r"aumentou|diminuiu|subiu|caiu|increased|decreased|reverteu|reversed|pulled\s+back|"
    r"(?:ganhou|perdeu|ganhando|perdendo|ganho|perda|gaining|losing|gained|lost|gain|loss)"
    r"\s+(?:(?:de|of)\s+)?(?:momentum|momento|for[çc]a|strength)|"
    r"(?:ficou|tornou-se|became)\s+(?:mais\s+|more\s+)?(?:forte|fraco|stronger|weaker)|"
    r"(?:mudou|changed)\s+(?:recentemente|recently))\b", re.I)
_PERSISTENCE = re.compile(
    r"\b(permanece\w*|continua\w*|ainda\s+(?:est[áa]|se\s+encontra)|remains?|continues?|still)\b"
    r"(?=[^.;!?]{0,80}\b(?:acima|abaixo|dentro|fora|neutr\w*|positiv\w*|negativ\w*|"
    r"forte|fraco|alta|baixa|above|below|inside|outside|neutral|positive|negative|strong|weak|"
    r"bullish|bearish|overbought|oversold)\b)", re.I)
_TEMPORAL_HEDGE = re.compile(
    r"\b(n[ãa]o|sem|nem|nenhum\w*|not|no|without|never|cannot|can't|"
    r"caso|if|poderia|could|aguardar|await|esperar|wait)\b[^.;!?]{0,65}$", re.I)


def temporal_state_claims(text: str) -> list[dict[str, Any]]:
    """Asserted evolution/persistence in a market clause; static adjectives are OK.

    'Sugere recuperação' still claims evidence of a past change. Negated claims,
    conditional/future scenarios and definitions are not observations of evolution.
    """
    found = []
    for clause in re.split(r"[.;!?]|\b(?:mas|porém|contudo|however|but)\b", text, flags=re.I):
        for pattern in (_EVOLUTION, _PERSISTENCE):
            for m in pattern.finditer(clause):
                # Recovery/consolidation themselves name a market process. Other
                # verb changes/persistence need a market subject in the clause.
                process = re.match(r"(?:recupera[çc][ãa]o|recovery|rebound)\b", m.group(0), re.I) and re.search(
                    r"\b(?:recente\w*|recent\w*|curto\s+prazo|short.term)\b", clause, re.I)
                if not process and not _MARKET_SUBJECT.search(clause):
                    continue
                before, after = clause[:m.start()], clause[m.end():]
                if _TEMPORAL_HEDGE.search(before) or re.match(
                    r"\s*(?:futur\w*|future|possível|possible|esperad\w*|expected)\b", after, re.I
                ):
                    continue
                if re.search(r"\b(?:defini[çc][ãa]o|definition|termo|term|palavra|word)\b", before, re.I):
                    continue
                found.append({"claim": UNSUPPORTED_TEMPORAL_STATE_CLAIM, "text": clause.strip(),
                              "requires": "t-1 values (not in the payload)", "holds": False})
    return found
#: Negação logo antes de uma afirmação: não é afirmação de fato.
_NEGATION = re.compile(r"\b(n[ãa]o|sem|nem|nenhum\w*|aus[êe]ncia)\b[^.;,]{0,15}$", re.IGNORECASE)
#: Negação ou hipótese em torno de um termo de transição: não afirma que a
#: transição aconteceu.
_HEDGE_BEFORE = re.compile(
    r"\b(n[ãa]o|sem|nem|nenhum\w*|aus[êe]ncia|poss[íi]ve\w*|potencia\w*|eventua\w*|pode\w*|poderia\w*|possa\w*|caso|"
    r"aguard\w*|esper\w*|at[ée]|antes|risco|chance|probabilidade|oportunidade|expectativa|futur\w*|"
    r"evitar|busca\w*|prov[áa]ve\w*)\b[^.;,]{0,40}$",
    re.IGNORECASE,
)
_HEDGE_AFTER = re.compile(r"^\W*(?:\w+\W+)?(iminente|futur\w*|poss[íi]ve\w*|potencia\w*|esperad\w*|prov[áa]ve\w*)\b",
                          re.IGNORECASE)
_TRANSITION = re.compile(
    r"\b(cruz(?:ou|aram|ando|amento|amentos|ar)|crossover|crossed|romp(?:eu|eram|endo|imento|e)|"
    r"ultrapass(?:ou|aram|ando)|superou|perfur(?:ou|ando)|revert(?:eu|endo)|revers[ãa]o|entrou|voltou|"
    r"acabou de|virada)\b",
    re.IGNORECASE,
)
_BAND = r"(?:\w+\s+){0,3}?bandas?(?:\s+de\s+bollinger)?\s+"
_POSITIONS = (
    ("ABOVE_UPPER_BAND", re.compile(rf"\b(?:acima\s+d[ae]|al[ée]m\s+da)\s+{_BAND}superior", re.I),
     lambda f: f["bb_upper_gap"] > 0, "bb_upper_gap > 0"),
    ("ABOVE_UPPER_BAND", re.compile(rf"\b(?:romp\w*|ultrapass\w*|superou|perfur\w*)\s+(?:d?[ao]s?\s+)?{_BAND}superior",
                                    re.I), lambda f: f["bb_upper_gap"] > 0, "bb_upper_gap > 0"),
    ("BELOW_UPPER_BAND", re.compile(rf"\babaixo\s+d[ae]\s+{_BAND}superior", re.I),
     lambda f: f["bb_upper_gap"] < 0, "bb_upper_gap < 0"),
    ("BELOW_LOWER_BAND", re.compile(rf"\b(?:abaixo\s+d[ae]|al[ée]m\s+da)\s+{_BAND}inferior", re.I),
     lambda f: f["bb_lower_gap"] < 0, "bb_lower_gap < 0"),
    ("BELOW_LOWER_BAND", re.compile(rf"\b(?:romp\w*|perfur\w*|ultrapass\w*)\s+(?:d?[ao]s?\s+)?{_BAND}inferior", re.I),
     lambda f: f["bb_lower_gap"] < 0, "bb_lower_gap < 0"),
    ("ABOVE_LOWER_BAND", re.compile(rf"\bacima\s+d[ae]\s+{_BAND}inferior", re.I),
     lambda f: f["bb_lower_gap"] > 0, "bb_lower_gap > 0"),
    ("INSIDE_BANDS", re.compile(r"\bdentro\s+d[ae]s?\s+(?:\w+\s+){0,2}?bandas", re.I),
     lambda f: f["bb_upper_gap"] <= 0 and f["bb_lower_gap"] >= 0, "bb_upper_gap <= 0 and bb_lower_gap >= 0"),
    ("MACD_ABOVE_SIGNAL", re.compile(r"\bmacd\b[^.;,]{0,40}?\b(?:acima|superando|supera)\b[^.;,]{0,20}?\bsinal\b|"
                                     r"macd_ratio\s*>\s*macd_signal_ratio", re.I),
     lambda f: f["macd_ratio"] > f["macd_signal_ratio"], "macd_ratio > macd_signal_ratio"),
    ("MACD_BELOW_SIGNAL", re.compile(r"\bmacd\b[^.;,]{0,40}?\babaixo\b[^.;,]{0,20}?\bsinal\b|"
                                     r"macd_ratio\s*<\s*macd_signal_ratio", re.I),
     lambda f: f["macd_ratio"] < f["macd_signal_ratio"], "macd_ratio < macd_signal_ratio"),
)
_SMA_CLAIM = re.compile(r"\b(acima|abaixo)\s+d[aoe]s?\s+(?=([^.;,]{0,60}))", re.IGNORECASE)
_SMA_TARGET = re.compile(r"^(?:\w+\s+){0,2}?(m[ée]dias?|smas?\b|sma\s*\d+)", re.IGNORECASE)
#: O alvo de "acima/abaixo de" termina na próxima palavra de direção ou conectivo
#: ("acima da SMA50 e abaixo da SMA200" afirma uma coisa de cada média).
_SMA_CUT = re.compile(r"\b(mas|por[ée]m|enquanto|contudo|embora|indicando|sugerindo|com|acima|abaixo|colad\w*|"
                      r"pr[óo]xim\w*|perto|apesar|e\s+(?!(?:d[ao]s?\s+)?(?:sma|m[ée]dia|\d)))\b", re.IGNORECASE)
_SIGN_CLAIM = re.compile(
    r"\b(sma50_gap|sma200_gap|bb_upper_gap|bb_lower_gap|macd_ratio|macd_signal_ratio)\b"
    r"(?:\s+(?:e|em|de|do|da|est[áa]|[ée]|segue|permanece|ficou|sma\w+_gap|macd\w*))*?\s+(positiv|negativ)\w*",
    re.IGNORECASE)


def _negated(text: str, start: int) -> bool:
    return bool(_NEGATION.search(text[max(0, start - 30): start]))


def _hypothetical(text: str, start: int, end: int) -> bool:
    return bool(_HEDGE_BEFORE.search(text[max(0, start - 60): start]) or _HEDGE_AFTER.search(text[end:end + 30]))


def audit_rationale(text: str, features: Mapping[str, float]) -> list[dict[str, Any]]:
    """Afirmações objetivas do rationale e se o payload as sustenta.

    Cada item: ``claim``, ``text``, ``requires`` e ``holds``. Contradição =
    ``holds is False``. Transições são sempre ``UNSUPPORTED_TRANSITION_CLAIM``
    (``holds = False``), porque o payload não traz ``t-1``. Ferramenta de
    auditoria: não reescreve decisão.
    """
    found: list[dict[str, Any]] = []
    for claim, pattern, rule, requires in _POSITIONS:
        for m in pattern.finditer(text):
            if not _negated(text, m.start()):
                found.append({"claim": claim, "text": m.group(0), "requires": requires, "holds": bool(rule(features))})
    for m in _SMA_CLAIM.finditer(text):
        target = _SMA_CUT.split(m.group(2), maxsplit=1)[0]
        if not _SMA_TARGET.search(target) or _negated(text, m.start()):
            continue
        has50, has200 = bool(re.search(r"50", target)), bool(re.search(r"200", target))
        if not (has50 or has200):
            if not re.search(r"\bm[ée]dias\b|\bsmas\b", target, re.IGNORECASE):
                continue  # "a média" sem período: ambíguo
            has50 = has200 = True
        above = m.group(1).lower() == "acima"
        for key, present in (("sma50_gap", has50), ("sma200_gap", has200)):
            if present:
                found.append({"claim": f"{'ABOVE' if above else 'BELOW'}_{key[:-4].upper()}", "text": m.group(0) + target,
                              "requires": f"{key} {'>' if above else '<'} 0",
                              "holds": features[key] > 0 if above else features[key] < 0})
    for m in _SIGN_CLAIM.finditer(text):
        key, positive = m.group(1).lower(), m.group(2).lower() == "positiv"
        found.append({"claim": f"{key.upper()}_{'POSITIVE' if positive else 'NEGATIVE'}", "text": m.group(0),
                      "requires": f"{key} {'>' if positive else '<'} 0",
                      "holds": features[key] > 0 if positive else features[key] < 0})
    for m in _TRANSITION.finditer(text):
        if _hypothetical(text, m.start(), m.end()) or re.match(r"revers[ãa]o\s+[àa]\s+m[ée]dia", text[m.start():], re.I):
            continue
        found.append({"claim": UNSUPPORTED_TRANSITION_CLAIM, "text": text[max(0, m.start() - 30): m.end() + 30],
                      "requires": "t-1 values (not in the payload)", "holds": False})
    return found + temporal_state_claims(text)


def contradictions(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [a for a in audit if not a["holds"] and a["claim"] not in
            (UNSUPPORTED_TRANSITION_CLAIM, UNSUPPORTED_TEMPORAL_STATE_CLAIM)]


def transitions(audit: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [a for a in audit if a["claim"] == UNSUPPORTED_TRANSITION_CLAIM]
