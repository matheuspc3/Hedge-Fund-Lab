"""Contrato do Risk científico v2, semântica da confidence técnica e o checker de regras numéricas.

Por que existe (Amendment 10): na CAL-B2 (âncora 2023-06-26) o Risk vetou dizendo
"confiança baixa de 0.462 (abaixo do limiar de 50%)". Não existe limiar de
confidence no protocolo nem no Risk: o LLM criou uma regra numérica e a usou para
justificar ``VETADO``. O mesmo padrão aparece em toda a evidência de development
v1/v2. A v3 muda SÓ o system prompt do Risk; regras duras, payload, schema,
Technical e Portfolio ficam idênticos.

:func:`audit_risk_rationale` confere o rationale VISÍVEL do Risk (nunca o
raciocínio oculto) contra o payload que o próprio Risk recebeu. Ferramenta de
auditoria: não reescreve decisão.
"""

import hashlib
import re
from collections.abc import Mapping
from typing import Any

#: Risk prompt v1 (o ``SYSTEM_PROMPT`` de ``risk_manager``), reproduzível.
RISK_SYSTEM_PROMPT_V1_SHA256 = "57ee8505ad8f6549d0c7c9a6e307bce1b5d6d7f5d4b3eeb165faeb7c330ad114"

RISK_SYSTEM_PROMPT_V2 = """Você é o gestor de risco do Hedge-fund-lab.

Avalie somente o sinal técnico e as métricas de risco explicitamente fornecidas no payload. Não use notícias, conhecimento externo, identidade do ativo, datas ou informação futura.

As regras duras numéricas do sistema são aplicadas deterministicamente antes desta etapa. Se esta chamada foi alcançada, essas regras anteriores não vetaram a operação.

Não invente, suponha nem aplique novos thresholds numéricos que não estejam explicitamente fornecidos no seu payload ou no seu contrato.

O campo confidence do sinal técnico é metadado qualitativo. Não existe um limiar numérico de confidence configurado para aprovação ou veto. Nunca diga ou implique que uma confidence está acima ou abaixo de um threshold inexistente, e nunca aprove ou vete uma operação somente porque a confidence é baixa ou alta.

Você pode considerar confidence qualitativamente em conjunto com as métricas efetivamente fornecidas, mas sem criar cortes numéricos ou regras ocultas.

Você ainda pode retornar VETADO quando a combinação do sinal e das métricas fornecidas indicar risco inadequado. Nesse caso, a justificativa deve se apoiar somente nos valores e relações presentes no payload, sem inventar regras quantitativas externas.

Preserve capital, não invente dados e retorne APROVADO ou VETADO com análise objetiva."""
#: Identidade do prompt v2; mudar o texto exige nova versão de prompt.
RISK_SYSTEM_PROMPT_V2_SHA256 = "990424e307e2c593afc40ebafef2c12387029ecf46a285f18a595c447e1e2151"

#: Semântica da ``confidence`` do Technical, documentada e versionada. Nada aqui
#: muda como o Technical a gera nem como o consenso a agrega.
TECHNICAL_CONFIDENCE_SEMANTICS_V1: Mapping[str, Any] = {
    "version": 1,
    "range": (0.0, 1.0),
    "nature": "qualitative self-reported metadata of the technical signal",
    "calibrated_probability": False,
    "probability_of_positive_return": False,
    "decision_threshold": None,
    "controls_position_sizing": False,
    "creates_hard_rule": False,
    "sole_basis_for_risk_verdict": False,
}


# ── Checker do rationale visível do Risk ─────────────────────────

UNSUPPORTED_CONFIDENCE_THRESHOLD = "UNSUPPORTED_CONFIDENCE_THRESHOLD"
UNSUPPORTED_NUMERIC_RULE = "UNSUPPORTED_NUMERIC_RULE"
#: Veredito apoiado só no sinal técnico (confidence/consenso), sem métrica de risco.
CONFIDENCE_ONLY_DECISION = "CONFIDENCE_ONLY_DECISION"
#: O texto declara o veredito oposto ao campo ``verdict``.
VERDICT_TEXT_CONTRADICTION = "VERDICT_TEXT_CONTRADICTION"
#: Gate de cada código (Amendment 10): V3-R1, V3-R2, V3-R3.
GATE_OF = {
    UNSUPPORTED_CONFIDENCE_THRESHOLD: "V3-R1",
    UNSUPPORTED_NUMERIC_RULE: "V3-R2",
    CONFIDENCE_ONLY_DECISION: "V3-R3",
    VERDICT_TEXT_CONTRADICTION: "V3-R3",
}

_W = r"[\wÀ-ÿ]+"
#: Número citado; frações de votos ("3/5") ficam de fora.
_NUM = r"(?<![\w/.,])(\d+(?:[.,]\d+)?)(?![/\d])\s*(%|por\s*cento|percent)?"
_LIMIT = (r"(?:limiar(?:es)?|limites?|threshold|cutoff|cut-off|corte|teto|piso|m[íi]nim[oa]s?|m[áa]xim[oa]s?|"
          r"minimum|maximum|limits?|floor|cap)\b")
_COMPARE = (r"(?:abaixo|acima|aqu[ée]m|al[ée]m|inferior(?:es)?|superior(?:es)?|menor(?:es)?|maior(?:es)?|"
            r"below|above|under|over|less|lower|greater|higher|beneath)")
_BREACH = (r"(?:exced\w*|excede\w*|ultrapass\w*|super(?:a|am|ou|ando|ar)|viol\w*|romp\w*|extrapol\w*|"
           r"exceed\w*|breach\w*|surpass\w*)")
_LINK = (rf"\s+(?:(?:a|ao|aos|à|às|de|do|da|dos|das|que|o|os|um|uma|the|a|an|of|than|to)\s+){{0,2}}"
         rf"(?:{_W}\s+){{0,2}}?")
_PATTERNS = (
    # "abaixo do limiar de 50%", "inferior ao limite prudencial", "menor que o mínimo", "below the threshold"
    ("COMPARE_LIMIT", re.compile(rf"\b{_COMPARE}{_LINK}{_LIMIT}", re.I)),
    # "excede os limites prudenciais", "ultrapassa o teto", "exceeds the limit"
    ("BREACH_LIMIT", re.compile(rf"\b{_BREACH}\s+(?:{_W}\s+){{0,3}}?{_LIMIT}", re.I)),
    # "não atinge a margem mínima", "não alcança o limiar", "does not reach the minimum"
    ("NOT_REACH_LIMIT", re.compile(rf"\b(?:n[ãa]o\s+(?:atinge|atingir|alcan[çc]a|chega\s+a|satisfaz|cumpre|atende)|"
                                   rf"(?:does\s+not|doesn't|fails\s+to)\s+(?:reach|meet|clear|satisfy))"
                                   rf"\s+(?:{_W}\s+){{0,3}}?{_LIMIT}", re.I)),
    # "limiar aceitável", "nível mínimo", "convicção mínima" (só com confidence)
    ("LIMIT_NOUN", re.compile(r"\b(?:limiar(?:es)?|threshold|cutoff|cut-off|(?:patamar|n[íi]vel|margem)\s+m[íi]nim[oa]|"
                              r"(?:confian[çc]a|convic[çc][ãa]o)\s+m[íi]nima|m[íi]nimo\s+(?:aceit[áa]vel|exigido|"
                              r"necess[áa]rio|requerido)|minimum\s+(?:confidence|conviction|level|acceptable|required))\b",
                              re.I)),
    # "abaixo de 50%", "(>50%)", "excede 0.30", "below 0.5"
    ("COMPARE_NUMBER", re.compile(rf"(?:\b(?:{_COMPARE}|{_BREACH}){_LINK}|[<>]=?\s*){_NUM}", re.I)),
)
#: Só estes substantivos são negáveis ("não existe limiar"); "sem convicção mínima"
#: afirma um mínimo e continua sendo regra.
_NEGATABLE_NOUN = re.compile(r"^(?:limiar|threshold|cutoff|cut-off)", re.I)
_CONFIDENCE = re.compile(r"\b(?:confian[çc]as?|confidence|convic[çc][ãa]o|convic[çc][õo]es|conviction|certeza)\b", re.I)
_SUBJECT = re.compile(r"\b(?P<conf>confian[çc]as?|confidence|convic[çc][ãa]o|conviction|certeza)\b|"
                      r"\b(?P<metric>volatilidade|volatility|vol|drawdown|rebaixamento|concentra[çc][ãa]o|"
                      r"concentration|exposi[çc][ãa]o|exposure)\b|"
                      r"\b(?P<cons>consenso|consensus|votos?|votes?)\b", re.I)
_METRIC = re.compile(r"\b(?:volatilidade|volatility|drawdown|rebaixamento|concentra[çc][ãa]o|concentration|"
                     r"perdas?\s+acumuladas?)\b", re.I)
_NEGATION = re.compile(r"\b(?:n[ãa]o|sem|nem|nenhum\w*|inexist\w*|aus[êe]ncia|not|no|without|never)\b[^.;,]{0,25}$",
                       re.I)
_CONCESSIVE = re.compile(r"\b(?:apesar|embora|ainda\s+que|mesmo\s+(?:com|que|diante|sendo)|conquanto|"
                         r"n[ãa]o\s+obstante|despite|although|even\s+though|notwithstanding)\b", re.I)
#: Fim de sentença: pontuação seguida de espaço ou fim ("33.41%" e "3/5." não quebram errado).
_SENTENCE = re.compile(r"[.;!?](?:\s+|$)")
_CLAUSE = re.compile(r"[.;!?](?:\s+|$)|,\s|\s[-–—]\s")  # noqa: RUF001
_SAYS_APPROVED = re.compile(r"\b(?:aprovad[oa]s?|aprova-se|aprovamos|aprovo|approved|approve)\b", re.I)
_SAYS_VETOED = re.compile(r"\b(?:vetad[oa]s?|veta-se|vetamos|vetar|veto|vetoed|rejected|reject)\b", re.I)


def _numbers(value: Any) -> list[float]:
    """Todo número do payload (métricas, confidence e os do texto do sinal)."""
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, Mapping):
        return [n for v in value.values() for n in _numbers(v)]
    if isinstance(value, str):
        return [float(m.replace(",", ".")) for m in re.findall(r"\d+(?:[.,]\d+)?", value)]
    return []


def _supported(raw: str, percent: str | None, payload_numbers: list[float]) -> bool:
    """O número citado é um valor do payload (na escala citada, até o arredondamento citado)?"""
    digits = raw.replace(",", ".")
    decimals = len(digits.split(".")[1]) if "." in digits else 0
    value, tol = float(digits), 0.5 * 10 ** -decimals + 1e-12
    if percent:
        value, tol = value / 100, tol / 100
    return any(abs(value - p) <= tol for p in payload_numbers)


def _sentence_bounds(text: str, start: int) -> tuple[int, int]:
    begin = max((m.end() for m in _SENTENCE.finditer(text, 0, start)), default=0)
    end = next((m.start() for m in _SENTENCE.finditer(text, start)), len(text))
    return begin, end


def _subject(text: str, start: int, end: int) -> str | None:
    """De quem é a comparação: confidence mencionada logo depois, senão o sujeito mais próximo antes."""
    begin, stop = _sentence_bounds(text, start)
    if _CONFIDENCE.search(text[start:min(stop, end + 30)]):
        return "conf"
    before = list(_SUBJECT.finditer(text, begin, start))
    return before[-1].lastgroup if before else None


def _negated(text: str, start: int) -> bool:
    return bool(_NEGATION.search(text[max(0, start - 30): start]))


def audit_risk_rationale(analysis: str, verdict: str, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Achados do rationale do Risk contra o payload recebido.

    Cada item: ``code``, ``gate``, ``text`` e ``detail``. Regras:

    - confidence + limiar/limite/mínimo, ou confidence comparada a número fora do
      payload -> ``UNSUPPORTED_CONFIDENCE_THRESHOLD`` (não existe limiar de
      confidence, nem acima nem abaixo);
    - métrica/consenso comparada a número fora do payload, ou afirmada acima de
      um limite/teto (nenhum limite é fornecido ao Risk e as regras duras já
      passaram) -> ``UNSUPPORTED_NUMERIC_RULE``. Citar o valor do payload
      ("volatilidade de 36.46%") e qualificá-lo ("elevada") é permitido;
    - veredito sem nenhuma métrica de risco fora de oração concessiva
      (apesar/embora...) -> ``CONFIDENCE_ONLY_DECISION``;
    - texto que declara o veredito oposto -> ``VERDICT_TEXT_CONTRADICTION``.
    """
    numbers = _numbers(payload)
    found: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    def add(code: str, start: int, end: int, detail: str) -> None:
        if (start, code) not in seen:
            seen.add((start, code))
            found.append({"code": code, "gate": GATE_OF[code], "text": analysis[max(0, start - 40): end + 20],
                          "detail": detail})

    for kind, pattern in _PATTERNS:
        for m in pattern.finditer(analysis):
            negatable = kind in ("COMPARE_LIMIT", "BREACH_LIMIT", "COMPARE_NUMBER") or (
                kind == "LIMIT_NOUN" and _NEGATABLE_NOUN.match(m.group(0)))
            if negatable and _negated(analysis, m.start()):
                continue
            subject = _subject(analysis, m.start(), m.end())
            if kind == "COMPARE_NUMBER":
                if _supported(m.group(1), m.group(2), numbers):
                    continue
                code = UNSUPPORTED_CONFIDENCE_THRESHOLD if subject == "conf" else UNSUPPORTED_NUMERIC_RULE
                add(code, m.start(), m.end(), f"compared with {m.group(0).strip()!r}, not a payload value")
            elif subject == "conf":
                add(UNSUPPORTED_CONFIDENCE_THRESHOLD, m.start(), m.end(), f"{kind}: no confidence threshold exists")
            elif kind == "LIMIT_NOUN":
                continue
            elif kind == "BREACH_LIMIT" or (kind == "COMPARE_LIMIT" and re.match(
                    r"(?:acima|al[ée]m|superior|maior)", m.group(0), re.I)):
                add(UNSUPPORTED_NUMERIC_RULE, m.start(), m.end(),
                    f"{kind}: claims a limit breach; no limit is given to the Risk and hard rules already passed")

    clauses = [c for c in _CLAUSE.split(analysis) if c.strip()]
    if not any(_METRIC.search(c) and not _CONCESSIVE.search(c) for c in clauses):
        add(CONFIDENCE_ONLY_DECISION, 0, len(analysis),
            f"{verdict} rests only on the technical signal; no risk metric outside a concessive clause")

    opposite = _SAYS_APPROVED if verdict == "VETADO" else _SAYS_VETOED
    for m in opposite.finditer(analysis):
        if not _negated(analysis, m.start()):
            add(VERDICT_TEXT_CONTRADICTION, m.start(), m.end(), f"text says {m.group(0)!r}, verdict is {verdict}")
    return found


def gate_counts(audit: list[dict[str, Any]]) -> dict[str, bool]:
    """Quais gates o rationale viola (um rationale conta uma vez por gate)."""
    return {gate: any(a["gate"] == gate for a in audit) for gate in ("V3-R1", "V3-R2", "V3-R3")}


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
