"""Contrato causal transmitido ao provedor de LLM.

Duas garantias vivem aqui, e elas são independentes uma da outra:

**1. Adimensionalidade.** A série de preços do projeto é ajustada por proventos
e splits, e o *nível* dessa série em ``t`` depende de proventos posteriores a
``t``. Os retornos permanecem causalmente limpos — o fator posterior cancela na
razão —, mas o nível não. Transmitir ``close``, ``sma_50`` ou ``macd`` em nível
ao modelo seria, portanto, entregar informação fora do information set. O
contrato abaixo transmite apenas razões, de modo que para qualquer ``k > 0``::

    features(k * historico) == features(historico)

**2. Quantização canônica.** Invariância matemática não produz igualdade de
bits: ``(k*a)/(k*b)`` só é bit-idêntico a ``a/b`` quando ``k`` é potência de
dois. Medido sobre dados reais, o desvio chega a ~2.5e-13 — suficiente para
mudar o SHA-256 do prompt e quebrar replay, ainda que jamais mude uma decisão.
Por isso todo número enviado ao provedor passa por :func:`canonical_number`
antes de ser serializado, e a comparação das regras duras de risco usa o mesmo
valor canônico que o prompt: sem isso, dois vintages poderiam atravessar um
limiar em lados opostos antes mesmo de o modelo ser chamado.

O que **não** está aqui é tão importante quanto o que está: identidade do ativo
e data da sessão não são features e não atravessam esta camada. Elas continuam
inteiras nos artefatos de auditoria (manifest, trace, ``RunContext``), porque
quem audita precisa saber qual ativo e qual data; o provedor, não.
"""

from __future__ import annotations

import json
import math
from typing import Any, Mapping

#: Versão do contrato de features. Muda quando o conjunto de campos ou uma
#: fórmula muda — ou seja, quando a classe de comparabilidade muda.
LLM_FEATURE_SCHEMA_VERSION = 1

#: Casas decimais de todo número científico enviado ao provedor. Ver o item 2
#: do docstring do módulo: é o que torna a invariância de escala verificável em
#: bytes, e não apenas verdadeira em álgebra.
LLM_NUMERIC_PRECISION = 6

#: Conjunto **exato** de features transmitidas. O teste de contrato trava esta
#: tupla: acrescentar um campo que carregue nível é uma falha de teste, não uma
#: revisão de código que passa despercebida.
FEATURE_KEYS: tuple[str, ...] = (
    "bb_lower_gap",
    "bb_upper_gap",
    "bb_width",
    "macd_ratio",
    "macd_signal_ratio",
    "rsi",
    "sma200_gap",
    "sma50_gap",
)


class FeatureContractError(ValueError):
    """Um valor não pode ser publicado sob o contrato causal."""


def canonical_number(value: Any) -> float:
    """Quantiza um número para a precisão canônica do contrato.

    Falha fechado em não-finito: ``NaN`` e infinito nunca são serializados para
    o provedor, porque o que sai daqui é evidência publicada no trace.

    ``-0.0`` é normalizado para ``0.0``: os dois são iguais numericamente e
    diferentes em JSON, e um sinal de zero dependente de arredondamento faria o
    hash do prompt oscilar sem que nada tivesse mudado.
    """
    number = float(value)
    if not math.isfinite(number):
        raise FeatureContractError(f"value must be finite, got {value!r}")
    rounded = round(number, LLM_NUMERIC_PRECISION)
    return 0.0 if rounded == 0 else rounded


def canonical_payload(value: Any) -> Any:
    """Aplica :func:`canonical_number` a todo float de uma estrutura aninhada.

    ``bool`` é tratado antes de número de propósito: ele é subclasse de ``int``
    em Python e viraria ``1.0`` silenciosamente.
    """
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        return canonical_number(value)
    if isinstance(value, Mapping):
        return {key: canonical_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_payload(item) for item in value]
    raise FeatureContractError(
        f"value of type {type(value).__name__} cannot be published to the provider"
    )


def canonical_prompt_json(payload: Any) -> str:
    """Serialização estável do payload enviado ao provedor.

    Mesma disciplina do ``canonical_json`` dos artefatos — chaves ordenadas,
    sem espaço supérfluo — acrescida da quantização numérica.
    """
    return json.dumps(canonical_payload(payload), ensure_ascii=False, sort_keys=True)


def canonical_metrics(metrics: Mapping[str, float]) -> dict[str, float]:
    """Métricas escalares na representação canônica única.

    Usada **antes** das regras duras de risco, e não apenas na serialização:
    é a representação canônica que decide o veredito, de modo que
    ``0.25000000000001`` e ``0.24999999999999`` — dois vintages da mesma série —
    não possam cair em lados opostos do mesmo limiar.
    """
    return {key: canonical_number(value) for key, value in metrics.items()}


def _finite(levels: Mapping[str, float], key: str) -> float | None:
    value = levels.get(key)
    if value is None:
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _gap(close: float, level: float | None) -> float | None:
    """``close / level - 1``: onde o preço está em relação à referência.

    Uma única orientação para todas as referências de nível. A alternativa —
    ``close/sma - 1`` para médias e ``banda/close - 1`` para bandas — inverteria
    o sinal da mesma ideia entre dois grupos de campos do mesmo prompt.
    """
    if level is None or level == 0.0:
        return None
    return close / level - 1.0


def dimensionless_features(
    close: float, levels: Mapping[str, float]
) -> dict[str, float]:
    """Converte níveis de indicadores em razões canônicas, sem nível algum.

    Campos cujo insumo não existe na sessão — janela ainda em warm-up, por
    exemplo — são **omitidos**, nunca preenchidos. Com
    ``minimum_history_sessions = 504`` isso não ocorre em run científico; a
    omissão existe para que o contrato continue honesto fora dele.

    ``bb_middle`` é consumido apenas em ``bb_width``: como
    ``bb_upper = middle + k·sigma`` e ``bb_lower = middle - k·sigma``, vale
    ``middle == (upper + lower)/2``, e um ``bb_middle_gap`` seria exatamente
    derivável dos outros dois campos. ``bb_width`` é mantido por legibilidade,
    declaradamente redundante.
    """
    price = float(close)
    if not math.isfinite(price) or price <= 0:
        raise FeatureContractError(f"close must be finite and > 0, got {close!r}")

    upper = _finite(levels, "bb_upper")
    lower = _finite(levels, "bb_lower")
    middle = _finite(levels, "bb_middle")
    macd = _finite(levels, "macd")
    macd_signal = _finite(levels, "macd_sinal")

    width: float | None = None
    if upper is not None and lower is not None and middle not in (None, 0.0):
        width = (upper - lower) / float(middle)

    raw: dict[str, float | None] = {
        "sma50_gap": _gap(price, _finite(levels, "sma_50")),
        "sma200_gap": _gap(price, _finite(levels, "sma_200")),
        "bb_upper_gap": _gap(price, upper),
        "bb_lower_gap": _gap(price, lower),
        "bb_width": width,
        "rsi": _finite(levels, "rsi"),
        "macd_ratio": None if macd is None else macd / price,
        "macd_signal_ratio": None if macd_signal is None else macd_signal / price,
    }

    features = {
        key: canonical_number(value)
        for key, value in raw.items()
        if value is not None and math.isfinite(value)
    }
    unknown = set(features) - set(FEATURE_KEYS)
    if unknown:
        raise FeatureContractError(
            f"feature(s) outside the declared contract: {', '.join(sorted(unknown))}"
        )
    return features
