"""Registry explícito dos participantes clássicos suportados pelo runner.

O registry existe para que uma spec serializada nunca precise carregar um
import path arbitrário. Cada chamada a :func:`build_participant` devolve uma
instância nova: participantes clássicos guardam estado entre sessões
(``_target_weight``, ``_session_index``) e reutilizar a mesma instância entre
runs contaminaria a segunda execução.
"""

import inspect
from typing import Any, Callable, Mapping

from src.backtesting.arena import Participant
from src.backtesting.portfolio import EqualWeightParticipant, MinVarianceParticipant
from src.experiments.spec import ParticipantSpec
from src.strategies.bollinger_bands import BollingerParticipant
from src.strategies.buy_and_hold import BuyAndHoldParticipant
from src.strategies.sma_cross import SMACrossParticipant

PARTICIPANT_REGISTRY: Mapping[str, Callable[..., Participant]] = {
    "bollinger": BollingerParticipant,
    "buy_and_hold": BuyAndHoldParticipant,
    "equal_weight": EqualWeightParticipant,
    "min_variance": MinVarianceParticipant,
    "sma_cross": SMACrossParticipant,
}

# Participantes single-asset declaram o ativo neste parâmetro; os de carteira
# não o declaram e recebem o universo inteiro do snapshot.
TICKER_PARAM = "ticker"


def build_participant(spec: ParticipantSpec) -> Participant:
    """Constrói uma instância nova a partir da descrição serializável."""
    factory = PARTICIPANT_REGISTRY.get(spec.kind)
    if factory is None:
        supported = ", ".join(sorted(PARTICIPANT_REGISTRY))
        raise ValueError(
            f"unsupported participant kind: {spec.kind!r}; supported: {supported}"
        )
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
