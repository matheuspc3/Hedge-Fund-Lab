"""O fator de ajuste não carrega informação futura material para as features.

O fator de retorno total de uma sessão ``s`` depende dos proventos pagos depois
de ``s`` até a data do download. Para a decisão em ``t``, os proventos
**posteriores** a ``t`` multiplicam todo o histórico causal ``[.., t]`` pela
mesma constante; só os proventos **anteriores** a ``t`` (informação passada,
legítima) mudam a forma da série. Logo basta que as features científicas — gaps
de SMA, gaps e largura de Bollinger, RSI, razões de MACD — e a volatilidade de
risco sejam invariantes a multiplicar o histórico causal inteiro por uma
constante.
"""

import pytest

from src.agents.features import canonical_prompt_json
from src.agents.llm_client import MockLLMClient
from src.agents.participant import LLMParticipant
from src.experiments.hardening import (
    H_SYN_ARCHETYPES,
    HardeningState,
    frozen_observation,
    synthetic_frame,
)

PRICE_COLUMNS = ["abertura", "maxima", "minima", "fechamento"]


def payload(history) -> tuple[dict, float, str]:
    participant = LLMParticipant("SYN", llm_client=MockLLMClient())
    state = HardeningState("x", "SYN", history)
    close = float(history["fechamento"].iloc[-1])
    built = participant._agent_state(frozen_observation(state, 1e5), history, 1e5, close)
    canonical = canonical_prompt_json(
        {"features": built["features"], "recent_volatility": built["recent_volatility"]}
    )
    return built["features"], built["recent_volatility"], canonical


def scaled(history, factor: float):
    copy = history.copy()
    copy[PRICE_COLUMNS] = copy[PRICE_COLUMNS] * factor
    return copy


@pytest.mark.parametrize("archetype", H_SYN_ARCHETYPES, ids=lambda item: item.name)
def test_fator_comum_potencia_de_dois_e_exatamente_invariante(archetype) -> None:
    """Escala por 2^k é exata em ponto flutuante: igualdade bit a bit."""
    history = synthetic_frame(archetype)
    base = payload(history)
    for factor in (0.25, 2.0):
        assert payload(scaled(history, factor)) == base


@pytest.mark.parametrize("factor", [0.2700193, 0.25051104, 1.37])
@pytest.mark.parametrize("archetype", H_SYN_ARCHETYPES, ids=lambda item: item.name)
def test_fator_comum_real_nao_muda_o_payload_canonico(archetype, factor: float) -> None:
    """Fatores reais do PETR4 (e um arbitrário): payload canônico idêntico."""
    history = synthetic_frame(archetype)
    assert payload(scaled(history, factor))[2] == payload(history)[2]


def test_provento_antes_de_t_muda_a_forma_e_portanto_as_features() -> None:
    """Contraprova: ajuste que só atinge o passado distante muda as features.

    É informação passada legítima (o provento já aconteceu antes de ``t``), e
    mostra que a invariância acima é específica do fator comum.
    """
    history = synthetic_frame(H_SYN_ARCHETYPES[0])
    stepped = history.copy()
    stepped.iloc[: len(history) - 30, [stepped.columns.get_loc(c) for c in PRICE_COLUMNS]] *= 0.9
    assert payload(stepped)[2] != payload(history)[2]
