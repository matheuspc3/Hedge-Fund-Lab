"""Registry explícito dos participantes suportados pelo runner.

O registry existe para que uma spec serializada nunca precise carregar um
import path arbitrário. Cada chamada a :func:`build_participant` devolve uma
instância nova: participantes guardam estado entre sessões (``_target_weight``,
``_session_index``, o pico de patrimônio do ``llm_agent``) e reutilizar a mesma
instância entre runs contaminaria a segunda execução.

``llm_agent`` entra pelo mesmo caminho dos clássicos: a spec descreve provedor,
modelo, quorum e limites como escalares JSON, e a credencial continua vindo do
ambiente — segredo não entra em spec, manifest nem log.
"""

import inspect
from typing import Any, Callable, Mapping

from src.agents.participant import LLMParticipant
from src.backtesting.arena import Participant
from src.backtesting.portfolio import EqualWeightParticipant, MinVarianceParticipant
from src.experiments.spec import ParticipantSpec
from src.strategies.bollinger_bands import BollingerParticipant
from src.strategies.buy_and_hold import BuyAndHoldParticipant
from src.strategies.indicator_family_control import IndicatorFamilyControlParticipant
from src.strategies.sma_cross import SMACrossParticipant

PARTICIPANT_REGISTRY: Mapping[str, Callable[..., Participant]] = {
    "bollinger": BollingerParticipant,
    "buy_and_hold": BuyAndHoldParticipant,
    "equal_weight": EqualWeightParticipant,
    "indicator_family_control": IndicatorFamilyControlParticipant,
    "llm_agent": LLMParticipant,
    "min_variance": MinVarianceParticipant,
    "sma_cross": SMACrossParticipant,
}

# Participantes single-asset declaram o ativo neste parâmetro; os de carteira
# não o declaram e recebem o universo inteiro do snapshot.
TICKER_PARAM = "ticker"


def _factory(spec: ParticipantSpec) -> Callable[..., Participant]:
    factory = PARTICIPANT_REGISTRY.get(spec.kind)
    if factory is None:
        supported = ", ".join(sorted(PARTICIPANT_REGISTRY))
        raise ValueError(
            f"unsupported participant kind: {spec.kind!r}; supported: {supported}"
        )
    return factory


def preflight_participant(spec: ParticipantSpec, *, scientific: bool) -> object | None:
    """Gate local do participante, **antes** de construí-lo.

    Participante que declara ``preflight(params, *, scientific)`` confere a
    própria spec sem rede e sem instanciar nada — hoje só o ``llm_agent``,
    para capacidade do provedor e entrada científica estrita. Os demais não
    declaram nada e passam. O runner continua sem conhecer participante algum.
    """
    preflight = getattr(_factory(spec), "preflight", None)
    return None if preflight is None else preflight(spec.params, scientific=scientific)


def build_participant(spec: ParticipantSpec) -> Participant:
    """Constrói uma instância nova a partir da descrição serializável."""
    factory = _factory(spec)
    try:
        inspect.signature(factory).bind(**spec.params)
    except TypeError as exc:
        raise ValueError(f"invalid params for participant {spec.kind!r}: {exc}") from exc
    return factory(**spec.params)


def required_tickers(spec: ParticipantSpec) -> tuple[str, ...]:
    """Tickers que a spec exige explicitamente do snapshot.

    Vazio para participantes de carteira: eles não escolhem ativos, recebem o
    universo do snapshot. Nenhuma seleção dinâmica acontece aqui.
    """
    ticker: Any = spec.params.get(TICKER_PARAM)
    return (str(ticker),) if ticker is not None else ()
