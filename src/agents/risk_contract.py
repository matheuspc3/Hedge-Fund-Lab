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

# ── VERDICT_TEXT_CONTRADICTION com negação por sentença/cláusula (checker v2) ──
#
# v1 aceitava negação só até 30 caracteres antes da palavra e marcava "Não há
# fatores adversos nas métricas fornecidas que justifiquem veto" (APROVADO)
# como contradição. v2 (Amendment 11) decide a polaridade pela construção, dentro
# da sentença: negação direta, verbo licenciador negado, "não há X que
# justifique", "sem motivo para". Instrumento de auditoria; o tratamento não muda.

RISK_RATIONALE_CHECKER_VERSION = 2

#: Palavras funcionais (classe fechada) que podem ficar entre a negação e o alvo.
_FW = (r"(?:o|a|os|as|um|uma|ao|aos|à|às|do|da|dos|das|de|para|por|pelo|pela|pelos|pelas|qualquer|quaisquer|"
       r"se|é|foi|foram|será|seria|seriam|são|ser|sido|está|estão|h[áa]|houve|haver|deve|devem|deveria|deveriam|"
       r"pode|podem|poderia|poderiam|tem|têm|tenha|tenham|teve|tinha|"
       r"the|an|any|to|be|been|is|are|was|were|will|would|should|could|can|must|do|does|did|has|have|had|it|"
       r"for|of|by)")
_ADV = r"(?:\w+mente|\w+ly|por\s+si\s+s[óo]|em\s+si|isoladamente|ainda|by\s+itself|alone|therefore|thus|still)"
_GLUE = rf"(?:[\s,]+(?:{_FW}|{_ADV}))*[\s,]*"
#: Negação verbal/adverbial: governa o que vem logo depois.
_NEG = (r"(?:\bn[ãa]o|\bnem|\bnunca|\bjamais|\bsem|\bnenhum\w*|\bnada|\bnot|\bnever|\bwithout|\bcannot|"
        r"\bthere\s+(?:is|are|was|were)\s+no|n['’]t)\b")  # noqa: RUF001
#: Negação existencial/quantificadora: abre um sintagma ("não há fatores...").
#: "no" inglês só antes de substantivo licenciador (em português "no" é em + o).
_NEG_EXIST = re.compile(
    r"\b(?:there\s+(?:is|are|was|were)\s+no|(?:n[ãa]o|not|never|nunca|jamais)\s+\w+|sem|nenhum\w*|nada|nem|"
    r"inexist\w*|aus[êe]ncia\s+de|falta\s+de|nothing|none|without|absence\s+of|lack\s+of|"
    r"no(?=(?:\s+\w+){0,2}\s+(?:reasons?|grounds?|basis|need|cause|justification|room|case)\b))\b", re.I)
#: Verbo cujo objeto é o veredito ("justifiquem veto", "justify a veto").
_LIC_VERB = (r"(?:justific\w*|justifiqu\w*|recomend\w*|exig\w*|requer\w*|demand\w*|imp[õo]\w*|sustent\w*|"
             r"fundament\w*|embas\w*|ensej\w*|permit\w*|autoriz\w*|suport\w*|indic\w*|aconselh\w*|suger\w*|"
             r"sugir\w*|justify|justifies|justified|warrant\w*|recommend\w*|requir\w*|calls?\s+for|merit\w*|"
             r"support\w*|allow\w*|authori[sz]\w*|indicat\w*|suggest\w*)")
#: Substantivo cujo complemento é o veredito ("motivo para veto", "reason to veto").
_LIC_NOUN = (r"(?:motivos?|raz[õoã]\w*|fundamentos?|bases?|justificativas?|justifica[çc][ãa]o|condi[çc]\w+|"
             r"espa[çc]o|margem|necessidade|ind[íi]cios?|reasons?|grounds?|basis|justification|cause|room|need|"
             r"case)")
#: Relativo restritivo ("fatores QUE justifiquem"); "o que" e ", which" retomam a
#: oração inteira e afirmam algo novo, então não herdam a negação.
_REL = r"(?:(?<!\bo\s)\bque|\bthat|(?<!,\s)\bwhich)"
#: Fecha o escopo de uma negação existencial: novo predicado afirmado ou adversativa.
_CLOSER = re.compile(r"\b(?:h[áa]|existem?|houve|é|são|está|estão|foi|foram|mas|por[ée]m|contudo|entretanto|"
                     r"todavia|no\s+entanto|is|are|was|were|but|however|yet)\b", re.I)
_SCOPE = re.compile(r"[.;:!?](?:\s+|$)")
_DIRECT = re.compile(rf"{_NEG}{_GLUE}$", re.I)
_LICENSED_DIRECT = re.compile(rf"{_NEG}{_GLUE}{_LIC_VERB}{_GLUE}$", re.I)
_LICENSED_REL = re.compile(rf"{_REL}{_GLUE}{_LIC_VERB}{_GLUE}$", re.I)
_LICENSED_NOUN = re.compile(rf"\b{_LIC_NOUN}(?:,[^,]*,)?\s+(?:para|de|a|ao|à|to|for|of){_GLUE}$", re.I)
_LICENSED_VERB = re.compile(rf"\b{_LIC_VERB}{_GLUE}$", re.I)
#: Sujeito quantificado negativamente governa o verbo principal ("Nada no payload recomenda veto").
_NEG_QUANT = re.compile(r"\b(?:nada|nenhum\w*|nothing|none)\b", re.I)
#: Menção à camada determinística ("regras de veto", "veto duro", "aprovada pelas
#: regras duras"): descreve as regras duras, não o veredito deste estágio.
_LAYER = r"(?:regras?|filtros?|limites?|crit[ée]rios?|etapas?|camadas?|rules?|filters?|limits?|stages?)"
_LAYER_ADJ = r"(?:dur[oa]s?|determin[íi]stic[oa]s?|num[ée]ric[oa]s?|hard|deterministic|upstream)"
_LAYER_BEFORE = re.compile(rf"\b(?:{_LAYER}|{_LAYER_ADJ})\s+(?:de\s+)?$", re.I)
_LAYER_AFTER = re.compile(rf"^(?:\s+{_FW})*\s+(?:{_LAYER}|{_LAYER_ADJ})\b", re.I)
#: Formas de cada veredito cuja negação licenciada contradiz o próprio campo.
_SAYS_APPROVAL_ANY = re.compile(r"\b(?:aprovad[oa]s?|aprova-se|aprovamos|aprovo|aprovar|aprova[çc][ãa]o|"
                                r"approved|approve|approval)\b", re.I)


def _scope_start(text: str, start: int) -> int:
    return max((m.end() for m in _SCOPE.finditer(text, 0, start)), default=0)


def _licensed_negation(seg: str) -> bool:
    """A negação incide sobre o licenciador do veredito ("não justifica", "não há X que justifique", "sem motivo para")."""
    if _LICENSED_DIRECT.search(seg):
        return True
    for licensed, cue in ((_LICENSED_REL, _NEG_EXIST), (_LICENSED_NOUN, _NEG_EXIST), (_LICENSED_VERB, _NEG_QUANT)):
        lic = licensed.search(seg)
        neg = [n for n in cue.finditer(seg) if n.end() <= lic.start()] if lic else []  # o lookahead de "no" vê além
        # ponytail: o escopo vai da última negação até o licenciador e só um
        # predicado afirmado (há/é/foi...) ou adversativa o fecha; "Com drawdown nulo
        # e sem concentração há fatores que justificam veto" escapa (teto conhecido).
        if neg and not _CLOSER.search(seg, neg[-1].end(), lic.start()):
            return True
    return False


def _layer_reference(text: str, m: re.Match) -> bool:
    return bool(_LAYER_BEFORE.search(text[max(0, m.start() - 40): m.start()]) or
                _LAYER_AFTER.search(text[m.end(): m.end() + 60]))


def _verdict_contradictions(text: str, verdict: str) -> list[tuple[re.Match, str]]:
    """(menção, detalhe) de cada contradição genuína entre texto e ``verdict``."""
    approved = verdict == "APROVADO"
    found = []
    for m in (_SAYS_VETOED if approved else _SAYS_APPROVED).finditer(text):
        seg = text[_scope_start(text, m.start()): m.start()]
        if not (_layer_reference(text, m) or _DIRECT.search(seg) or _licensed_negation(seg)):
            found.append((m, f"text says {m.group(0)!r}, verdict is {verdict}"))
    for m in (_SAYS_APPROVAL_ANY if approved else _SAYS_VETOED).finditer(text):
        seg = text[_scope_start(text, m.start()): m.start()]
        # "Embora não haja motivo para veto, ... vetada": a concessiva concede o oposto.
        conceded = any("," not in seg[c.end():] for c in _CONCESSIVE.finditer(seg))
        if not conceded and not _layer_reference(text, m) and _licensed_negation(seg):
            found.append((m, f"text denies grounds for {m.group(0)!r}, verdict is {verdict}"))
    return found


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
    - texto que declara o veredito oposto sem negá-lo ("operação aprovada" com
      VETADO), ou que nega o fundamento do próprio veredito ("não há condições
      para aprovação" com APROVADO) -> ``VERDICT_TEXT_CONTRADICTION`` (checker
      v2: polaridade pela construção na sentença, ver ``_verdict_contradictions``).
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

    for m, detail in _verdict_contradictions(analysis, verdict):
        add(VERDICT_TEXT_CONTRADICTION, m.start(), m.end(), detail)
    return found


def gate_counts(audit: list[dict[str, Any]]) -> dict[str, bool]:
    """Quais gates o rationale viola (um rationale conta uma vez por gate)."""
    return {gate: any(a["gate"] == gate for a in audit) for gate in ("V3-R1", "V3-R2", "V3-R3")}


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
