"""Diagnostic Hardening: conjunto H dedicado, harness de decisão e diagnósticos.

A configuração do H2, o conjunto H, os gates e a escada de thinking estão
congelados pelo **H2 METHODOLOGICAL FREEZE V1**
(``docs/H2_METHODOLOGICAL_FREEZE_V1.md``). Nada aqui produz resultado
financeiro; o harness decide estados congelados sem liquidar.

**Conjunto H, disjunto por construção.** ``H = H_syn + H_real``:

- ``H_syn`` são séries sintéticas determinísticas, sem data real, sem ativo
  real e sem ``t+1``: não podem coincidir com CAL-A, CAL-B, Stress, Validation
  ou Final Test, nem abrir canal de memorização;
- ``H_real`` são quatro sessões reais de PETR4 reservadas por regra mecânica
  de quantis (:data:`H_REAL_SESSIONS`), sem olhar comportamento ou
  desempenho; :func:`require_disjoint` recusa sobreposição com os demais
  conjuntos, que precisam excluí-las.

**Outcome-blind por construção.** O harness chama ``participant.decide()``
sobre o estado congelado e nunca liquida: não existe sessão seguinte, então
nenhum retorno, P&L ou métrica financeira pode ser calculado aqui. Os
diagnósticos leem apenas causas estruturadas (``decisions``) e o trace.
"""

import hashlib
import math
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from types import MappingProxyType
from typing import Any, cast

import numpy as np
import pandas as pd

from src.agents.features import canonical_prompt_json
from src.agents.llm_client import MockLLMClient
from src.agents.llm_trace import load_trace
from src.agents.participant import (
    BUY_AT_TARGET_NOOP,
    FAILURE_CAUSES,
    NOT_ELIGIBLE,
    PORTFOLIO_HOLD,
    RISK_VETO_CAUSES,
    TECH_EXPLICIT_HOLD,
    TECH_NO_MAJORITY,
    LLMDecisionError,
    LLMDecisionRecord,
    LLMParticipant,
)
from src.artifacts import RunArtifact
from src.backtesting.arena import MarketObservation

PENDING_ADVISOR_RATIFICATION = "PENDING_ADVISOR_RATIFICATION"

#: Configuração Self-Consistency **provisória** do H2. Suportada e
#: configurável; nada aqui está congelado. Provedor, modelo e
#: ``thinking_level`` ficam de fora de propósito: escolhê-los é decisão
#: pendente e nunca será feita por resultado.
H2_SC_PROVISIONAL_PARAMS: Mapping[str, Any] = MappingProxyType(
    {
        "analyst_count": 5,
        "consensus_threshold": 0.6,
        "require_all_votes": True,
        "temperature": 1.0,
        "decision_frequency": 1,
        "strict_inputs": True,
        # Recomendação do review: inversão pelo PM derruba a decisão em vez de
        # virar HOLD econômico. PENDING_ADVISOR_RATIFICATION como o resto.
        "portfolio_inversion_policy": "fail",
        "long_target_weight": 1.0,
        "risk_max_concentration": 1.0,
    }
)
H2_SC_PROVISIONAL_STATUS = PENDING_ADVISOR_RATIFICATION

# ── H2 METHODOLOGICAL FREEZE V1 ──────────────────────────────────

H2_FREEZE_VERSION = "H2_METHODOLOGICAL_FREEZE_V1"
H2_FREEZE_STATUS = "FROZEN_BY_AUTHORS"

#: Spec científica congelada do ``llm_agent`` no H2 v1, sem ``ticker`` e sem
#: ``thinking_level`` — este sai da escada abaixo, nunca de escolha livre.
#: Todo parâmetro material está escrito, inclusive os que coincidem com o
#: default do código (protocolo, seção 5.7):
#:
#: - geração, ensemble e políticas: decisões do freeze;
#: - ``long_target_weight`` e ``risk_max_concentration``: já DECIDIDOS (seção 11);
#: - ``risk_max_volatility``, ``volatility_window`` e ``risk_max_drawdown``:
#:   valores técnicos existentes adotados como baseline B0 ex ante; a
#:   autoridade de mudá-los continua em CAL-A / Sequential Development;
#: - ``retry_attempts``/``retry_base_delay``: operacionais (autoridade do
#:   Hardening, seção 5.12), fixados antes da primeira chamada a partir dos 503
#:   observados no DEV_SMOKE; não mudam conteúdo de decisão.
H2_FREEZE_V1_PARAMS: Mapping[str, Any] = MappingProxyType(
    {
        "provider": "gemini",
        "model": "gemini-3.8-flash",
        "temperature": 1.0,
        "max_output_tokens": 8192,
        "analyst_count": 5,
        "consensus_threshold": 0.6,
        "require_all_votes": True,
        "decision_frequency": 1,
        "strict_inputs": True,
        "portfolio_inversion_policy": "fail",
        "long_target_weight": 1.0,
        "risk_max_concentration": 1.0,
        "risk_max_volatility": 0.5,
        "risk_max_drawdown": 0.25,
        "volatility_window": 21,
        "retry_attempts": 6,
        "retry_base_delay": 2.0,
    }
)

#: Escada predeclarada de menor custo, nunca competição: começa em ``low``;
#: só sobe se o nível falhar exclusivamente por G-I ou G-F, depois de um
#: DEV_SMOKE técnico do próximo nível e de rodar H inteiro de novo.
H2_THINKING_LADDER: tuple[str, ...] = ("low", "medium", "high")


#: Resultado mecânico da escada: ``low`` passou em G-A, G-T, G-I e G-F no
#: Diagnostic Hardening de 2026-10-04 e fica congelado para o H2 v1.
#: ``medium`` e ``high`` nunca foram testados, como a regra manda.
H2_FROZEN_THINKING_LEVEL = "low"
H2_FROZEN_THINKING_EVIDENCE = "docs/evidence/h2/hardening_low_20261004T194849Z/manifest.json"


def h2_freeze_v1_params(thinking_level: str) -> dict[str, Any]:
    """Spec congelada com o nível de thinking da escada."""
    if thinking_level not in H2_THINKING_LADDER:
        raise ValueError(f"thinking_level must be one of {H2_THINKING_LADDER}")
    return {**H2_FREEZE_V1_PARAMS, "thinking_level": thinking_level}

# ── H_syn ────────────────────────────────────────────────────────

#: Versão dos geradores. Qualquer mudança de fórmula ou parâmetro é uma nova
#: versão: o instrumento de hardening não é ajustado depois de ver respostas.
#: Congelada a partir da primeira resposta real de provedor; mudar geradores
#: depois disso exige nova versão ou amendment explícito.
H_SYN_VERSION = 1

#: Congelamento verificável de ``H_SYN_VERSION = 1``: SHA-256 do payload
#: científico **canônico** de cada estado — as oito features e a volatilidade
#: anualizada, quantizadas a ``LLM_NUMERIC_PRECISION`` e serializadas por
#: ``canonical_prompt_json``, exatamente o que chega ao provedor. Diferença de
#: plataforma abaixo da quantização não muda o digest; mudança material muda.
H_SYN_PAYLOAD_DIGESTS: Mapping[str, str] = MappingProxyType(
    {
        "steady_uptrend": (
            "4f7eed9707fadf2876256376355098ac"
            "f0ea8707e49a5acfad4b54cbb4781971"
        ),
        "steady_downtrend": (
            "a20048684533b98c69f40e10672264df"
            "277d16a3edd9cd0c875622219476be23"
        ),
        "range_low_vol": (
            "5a2ae2c2973086b67b6405d3d88fbe36"
            "5ae4efc63bdcc92df3696e69e4469cfa"
        ),
        "range_high_vol": (
            "ddf2a6995d4fef8c8605522e7f69c6da"
            "a86bd0773eec010887d93787787bbcee"
        ),
        "extended_rally": (
            "b277d7cb1cbf4878156440bbb39ec851"
            "062a8964647598f454416e156128016c"
        ),
        "extended_selloff": (
            "0854c1709ff5ede12f6772639616c1eb"
            "24aa2812ec31e0e55bf45543724e21e7"
        ),
        "mixed_signals": (
            "354eb83d38ba9d7751426aa3aa74655b"
            "e577c217d11c8066d9b235e35432b821"
        ),
        "volatility_breach": (
            "3af92337d74006928d9ec4a4f331b6cf"
            "bfa3613c1d4f66a7b319523c200b3ca5"
        ),
    }
)
#: Sessões por série: o mínimo científico de 504 com folga.
H_SYN_SESSIONS = 600
#: Rótulo de calendário das barras sintéticas. Não é data de mercado e nunca
#: chega ao provedor (o contrato causal já não transmite data).
H_SYN_START = "2000-01-03"
H_SYN_BASE_PRICE = 100.0
#: Período, em sessões, da oscilação determinística do log-retorno. Não
#: inteiro, para que a janela de 21 sessões cubra fases variadas.
H_SYN_OSCILLATION_PERIOD = 5.3
#: Meia amplitude da faixa máxima/mínima em torno de abertura e fechamento.
H_SYN_RANGE = 0.002
H_SYN_VOLUME = 1_000_000.0
#: Ativo rótulo das séries sintéticas — não é um ativo real.
H_SYN_TICKER = "SYN"


@dataclass(frozen=True)
class SyntheticArchetype:
    """Gerador determinístico, sem RNG, de uma série de preços.

    ``log r_t = drift + amplitude · sin(2π t / período)``; nas últimas
    ``tail_sessions`` sessões valem ``tail_drift`` e ``tail_amplitude``. A
    volatilidade anualizada de 21 sessões é ≈ ``amplitude / √2 · √252``.
    """

    name: str
    drift: float
    amplitude: float
    tail_sessions: int = 0
    tail_drift: float = 0.0
    tail_amplitude: float | None = None


#: Os oito arquétipos, escolhidos por **cobertura de contrato** — estados de
#: família e regra de risco que o tratamento precisa atravessar sem
#: degenerar —, nunca por resultado.
H_SYN_ARCHETYPES: tuple[SyntheticArchetype, ...] = (
    # 1. acima das SMAs, RSI moderado, dentro das bandas
    SyntheticArchetype("steady_uptrend", drift=0.0008, amplitude=0.006),
    # 2. espelho: abaixo das SMAs
    SyntheticArchetype("steady_downtrend", drift=-0.0008, amplitude=0.006),
    # 3. lateral, volatilidade anualizada ≈ 0,05
    SyntheticArchetype("range_low_vol", drift=0.0, amplitude=0.004),
    # 4. lateral, volatilidade ≈ 0,35 (abaixo do default técnico 0,50)
    SyntheticArchetype("range_high_vol", drift=0.0, amplitude=0.03),
    # 5. RSI > 70 e fechamento acima da banda superior
    SyntheticArchetype(
        "extended_rally",
        drift=0.0005,
        amplitude=0.006,
        tail_sessions=8,
        tail_drift=0.012,
        tail_amplitude=0.002,
    ),
    # 6. RSI < 30 e fechamento abaixo da banda inferior
    SyntheticArchetype(
        "extended_selloff",
        drift=-0.0005,
        amplitude=0.006,
        tail_sessions=8,
        tail_drift=-0.012,
        tail_amplitude=0.002,
    ),
    # 7. acima da SMA50 e abaixo da SMA200
    SyntheticArchetype(
        "mixed_signals",
        drift=-0.0012,
        amplitude=0.006,
        tail_sessions=40,
        tail_drift=0.0015,
    ),
    # 8. volatilidade ≈ 0,80, acima do default técnico 0,50 de risco
    SyntheticArchetype("volatility_breach", drift=0.0, amplitude=0.07),
)


def synthetic_frame(
    archetype: SyntheticArchetype, sessions: int = H_SYN_SESSIONS
) -> pd.DataFrame:
    """OHLCV determinístico do arquétipo; passa no gate ``validate_ohlcv``."""
    steps = np.arange(1, sessions)
    wave = np.sin(2 * math.pi * steps / H_SYN_OSCILLATION_PERIOD)
    tail = steps >= sessions - archetype.tail_sessions
    tail_amplitude = (
        archetype.amplitude
        if archetype.tail_amplitude is None
        else archetype.tail_amplitude
    )
    log_returns = np.where(
        tail,
        archetype.tail_drift + tail_amplitude * wave,
        archetype.drift + archetype.amplitude * wave,
    )
    close = H_SYN_BASE_PRICE * np.exp(np.concatenate([[0.0], np.cumsum(log_returns)]))
    open_ = np.concatenate([[close[0]], close[:-1]])
    return pd.DataFrame(
        {
            "abertura": open_,
            "maxima": np.maximum(open_, close) * (1 + H_SYN_RANGE),
            "minima": np.minimum(open_, close) * (1 - H_SYN_RANGE),
            "fechamento": close,
            "volume": np.full(sessions, H_SYN_VOLUME),
        },
        index=pd.bdate_range(H_SYN_START, periods=sessions),
    )


# ── Estados congelados ───────────────────────────────────────────


@dataclass(frozen=True)
class HardeningState:
    """Um estado causal congelado: a última barra de ``history`` é ``t``."""

    state_id: str
    ticker: str
    history: pd.DataFrame


def synthetic_states() -> tuple[HardeningState, ...]:
    return tuple(
        HardeningState(
            f"syn-v{H_SYN_VERSION}:{item.name}", H_SYN_TICKER, synthetic_frame(item)
        )
        for item in H_SYN_ARCHETYPES
    )


# ── H_real: reservado pelo freeze v1 ─────────────────────────────

#: Ativo científico do H2, que é single-asset. O universo não é ampliado aqui.
H_REAL_TICKER = "PETR4.SA"

#: Regra mecânica de seleção, aplicada antes de qualquer chamada ao provedor
#: e sem olhar retorno, regime, volatilidade, evento ou resposta de modelo:
#: ``E`` = sessões do calendário comum do snapshot (protocolo, seção 5.11)
#: entre 2018-01-12 e 2024-02-28, com ``available_history_sessions >= 504``
#: e contrato causal estrito satisfeito; para ``q`` em ``H_REAL_QUANTILES``,
#: reserva-se ``E[floor(q · (len(E) - 1))]``.
H_REAL_WINDOW = ("2018-01-12", "2024-02-28")
H_REAL_QUANTILES: tuple[float, ...] = (0.20, 0.40, 0.60, 0.80)
H_REAL_SNAPSHOT_ID = "20261004T193839031891Z-6f5e24390ab2bca68131ecfc052b9d23"
H_REAL_SNAPSHOT_IDENTITY_DIGEST = (
    "6f5e24390ab2bca68131ecfc052b9d2381411aaaad35f0e56640fffcd6e766db"
)
H_REAL_ELIGIBLE_COUNT = 1519
#: SHA-256 da lista ordenada de ``E`` (datas ISO separadas por ``\n``).
H_REAL_ELIGIBLE_SHA256 = (
    "bada89626b03ca440c0e989fdf20bd4c3d4ea83be4faa66264cde655c9a46548"
)
#: Sessões reais reservadas **exclusivamente** ao Hardening. Ficam excluídas
#: de CAL-A, CAL-B, Stress, Sequential Development e qualquer outro conjunto.
H_REAL_SESSIONS: tuple[str, ...] = ("2019-04-08", "2020-06-29", "2021-09-17", "2022-12-07")
H_REAL_INDICES: tuple[int, ...] = (303, 607, 910, 1214)
#: Payload científico canônico de cada estado real (mesma definição de
#: :data:`H_SYN_PAYLOAD_DIGESTS`), conferido antes de qualquer chamada.
H_REAL_PAYLOAD_DIGESTS: Mapping[str, str] = MappingProxyType(
    {
        "2019-04-08": "20d95f5a7cf0cccfb74f9cc43330c38065578234b745f6e7984a958946fe5b0e",
        "2020-06-29": "28065db7fc72b97e0098554bc273cae73219465d49ccaaaa85fcdd8a8060be0b",
        "2021-09-17": "c16e53020d2fc6852b1256a664a5c71eeaab5b4e950d9f4c20bde57d3ff9163b",
        "2022-12-07": "06976959d02c8dc0786ac206fe5b870493f712bbe6bace3df20dc98bdc34c744",
    }
)
#: Conjuntos com que H_real precisa ser disjunto. Nenhum tem datas ainda
#: (todos ``TBD`` no protocolo): H_real foi reservado primeiro, e são eles que
#: precisam excluí-lo quando forem definidos.
H_REAL_RESERVED_AT_FREEZE: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {name: () for name in ("CAL-A", "CAL-B", "STRESS", "SEQUENTIAL_DEV", "VALIDATION", "FINAL_TEST")}
)
H_REAL_STATUS = H2_FREEZE_STATUS


def scientific_payload(state: HardeningState) -> str:
    """Payload canônico que o provedor recebe para o estado congelado.

    Montado pelo próprio participante (``_agent_state``, o mesmo da decisão
    real), sem rede: as oito features e a volatilidade, quantizadas e
    serializadas por ``canonical_prompt_json``.
    """
    participant = LLMParticipant(state.ticker, llm_client=MockLLMClient())
    history = state.history
    close = float(history["fechamento"].iloc[-1])
    capital = 100_000.0
    agent_state = participant._agent_state(
        frozen_observation(state, capital), history, capital, close
    )
    return canonical_prompt_json(
        {
            "features": agent_state["features"],
            "recent_volatility": agent_state["recent_volatility"],
        }
    )


def scientific_payload_digest(state: HardeningState) -> str:
    return hashlib.sha256(scientific_payload(state).encode("utf-8")).hexdigest()


def h_real_states(
    frame: pd.DataFrame, reserved: Mapping[str, Iterable[Any]]
) -> tuple[HardeningState, ...]:
    """Os quatro estados reais reservados, conferidos contra o freeze."""
    states = tuple(real_state(frame, session, reserved=reserved) for session in H_REAL_SESSIONS)
    for session, state in zip(H_REAL_SESSIONS, states):
        expected = H_REAL_PAYLOAD_DIGESTS.get(session)
        if expected is not None and scientific_payload_digest(state) != expected:
            raise ValueError(
                f"H_real payload for {session} does not match the frozen digest; "
                "the snapshot or the feature pipeline changed"
            )
    return states


def real_state(
    frame: pd.DataFrame,
    session: Any,
    *,
    reserved: Mapping[str, Iterable[Any]],
    ticker: str = H_REAL_TICKER,
) -> HardeningState:
    """Estado real congelado em ``session``, com o histórico truncado em ``t``.

    ``reserved`` é obrigatório e sem default: um estado real só nasce depois
    de :func:`require_disjoint` provar que ``session`` não pertence a CAL-A,
    CAL-B, Stress, Validation nem Final Test.
    """
    if ticker != H_REAL_TICKER:
        raise ValueError(
            f"H2 is single-asset on {H_REAL_TICKER}; {ticker!r} would silently "
            "widen the universe"
        )
    stamp = pd.Timestamp(session)
    if stamp not in frame.index:
        raise ValueError(f"session {stamp.date()} is not a bar of the frame")
    require_disjoint([stamp], reserved)
    return HardeningState(
        f"real:{ticker}:{stamp.date()}", ticker, frame.loc[:stamp].copy()
    )


def require_disjoint(
    hardening_sessions: Iterable[Any], reserved: Mapping[str, Iterable[Any]]
) -> None:
    """Recusa H_real que toque qualquer sessão de outro conjunto.

    ``reserved`` mapeia o nome do conjunto (``"CAL-A"``, ``"VALIDATION"``…)
    às suas sessões; janelas entram expandidas em sessões.
    """

    def days(items: Iterable[Any]) -> set[str]:
        return {str(cast(pd.Timestamp, pd.Timestamp(item)).date()) for item in items}

    hardening = days(hardening_sessions)
    for name, sessions in reserved.items():
        overlap = hardening & days(sessions)
        if overlap:
            raise ValueError(
                f"hardening set overlaps {name}: {', '.join(sorted(overlap))}"
            )


# ── Harness de decisão ───────────────────────────────────────────


@dataclass(frozen=True)
class HardeningOutcome:
    """Uma repetição sobre um estado, com o trace preservado até na falha."""

    state_id: str
    repetition: int
    record: LLMDecisionRecord | None
    trace: RunArtifact
    error: str | None = None
    reason: str | None = None


class HardeningAbortedError(RuntimeError):
    """Exceção fora do contrato de falha interrompeu o lote.

    Falha científica (``LLMDecisionError``) não interrompe nada: vira outcome.
    Qualquer outra exceção é bug e precisa subir — mas sem jogar fora o que
    já foi decidido e pago. ``outcomes`` carrega tudo até ali, inclusive a
    tentativa que quebrou, com o trace dela.
    """

    def __init__(self, message: str, outcomes: list["HardeningOutcome"]) -> None:
        super().__init__(message)
        self.outcomes = outcomes


def frozen_observation(state: HardeningState, capital: float) -> MarketObservation:
    """Observação de âncora: posição zero, capital inicial em caixa.

    Limitação declarada: todo estado de H parte de carteira **zerada** e pico
    igual ao patrimônio. As regras de concentração e de drawdown e o
    ``BUY_AT_TARGET_NOOP`` não são exercitados por H_syn; os diagnósticos de H
    medem a decisão de entrada, não a dinâmica de uma posição já aberta.
    """
    return MarketObservation(
        session=cast(pd.Timestamp, state.history.index[-1]),
        history=MappingProxyType({state.ticker: state.history.copy()}),
        positions=MappingProxyType({state.ticker: 0.0}),
        cash=capital,
        equity=capital,
    )


def run_hardening(
    states: Sequence[HardeningState],
    participant_factory: Callable[[str], LLMParticipant],
    *,
    repetitions: int,
    capital: float = 100_000.0,
) -> list[HardeningOutcome]:
    """Decide cada estado ``repetitions`` vezes, cada vez com instância nova.

    Falha científica (``LLMDecisionError``, o que inclui provedor fora do ar
    em qualquer papel) é registrada com a causa estruturada e o trace da
    tentativa, e o lote continua — run falho do runner não é publicado, e sem
    isso a evidência da falha Classe A se perderia. Qualquer outra exceção
    interrompe o lote como :class:`HardeningAbortedError`, levando junto os
    outcomes já obtidos.
    """
    if (
        isinstance(repetitions, bool)
        or not isinstance(repetitions, int)
        or repetitions < 1
    ):
        raise ValueError("repetitions must be an integer >= 1")
    outcomes: list[HardeningOutcome] = []
    for state in states:
        for repetition in range(repetitions):
            participant = participant_factory(state.ticker)
            error = reason = None
            unexpected: Exception | None = None
            try:
                participant.decide(frozen_observation(state, capital))
            except LLMDecisionError as exc:
                error, reason = str(exc), exc.reason
            except Exception as exc:  # bug: preserva o lote antes de subir
                error, unexpected = f"{type(exc).__name__}: {exc}", exc
            outcomes.append(
                HardeningOutcome(
                    state_id=state.state_id,
                    repetition=repetition,
                    record=participant.decisions[-1] if participant.decisions else None,
                    trace=participant.trace.artifact(),
                    error=error,
                    reason=reason,
                )
            )
            if unexpected is not None:
                raise HardeningAbortedError(
                    f"hardening aborted at {state.state_id} repetition "
                    f"{repetition}: {error}",
                    outcomes,
                ) from unexpected
    return outcomes


# ── Diagnósticos ─────────────────────────────────────────────────

HOLD_RATE_CAUSES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "explicit_hold_rate": frozenset({TECH_EXPLICIT_HOLD}),
        "no_majority_abstention_rate": frozenset({TECH_NO_MAJORITY}),
        # ``BUY_AT_TARGET_NOOP`` fica fora: vetar um no-op não é prudência.
        "risk_veto_rate": RISK_VETO_CAUSES,
        "portfolio_hold_rate": frozenset({PORTFOLIO_HOLD}),
    }
)


def _pair_rate(
    groups: Mapping[str, list[str]], counts: Callable[[str, str], bool]
) -> float | None:
    pairs = hits = 0
    for outcomes in groups.values():
        for left, right in combinations(outcomes, 2):
            pairs += 1
            hits += counts(left, right)
    return hits / pairs if pairs else None


def diagnostic_metrics(outcomes: Sequence[HardeningOutcome]) -> dict[str, Any]:
    """Inatividade e instabilidade, só de causas estruturadas e do trace.

    Denominador das taxas de HOLD: decisões válidas (sem falha, elegíveis).
    Falhas são contadas à parte — falha técnica nunca é prudência.

    ``same_state_flip_rate``: fração dos pares de repetições do **mesmo**
    estado congelado cujo resultado técnico é {COMPRA, VENDA}.
    ``same_state_disagreement_rate``: fração dos pares com qualquer diferença.
    """
    def failed(outcome: HardeningOutcome) -> bool:
        record = outcome.record
        return (
            outcome.error is not None
            or record is None
            or record.final_cause in FAILURE_CAUSES
        )

    failures = [outcome for outcome in outcomes if failed(outcome)]
    decided = [
        cast(LLMDecisionRecord, outcome.record)
        for outcome in outcomes
        if not failed(outcome)
        and cast(LLMDecisionRecord, outcome.record).final_cause != NOT_ELIGIBLE
    ]
    causes = Counter(record.final_cause for record in decided)
    total = len(decided)

    metrics: dict[str, Any] = {
        "decision_count": total,
        # Só falha de verdade: causa técnica, erro levantado ou sessão sem
        # registro. Sessão não elegível não é falha e não entra aqui.
        "failure_count": len(failures),
        "failure_causes": dict(
            Counter(
                outcome.reason
                or (outcome.record.final_cause if outcome.record else None)
                or "UNCLASSIFIED"
                for outcome in failures
            )
        ),
        "buy_at_target_noop_count": causes[BUY_AT_TARGET_NOOP],
    }
    for name, members in HOLD_RATE_CAUSES.items():
        hits = sum(causes[cause] for cause in members)
        metrics[name] = hits / total if total else None
    metrics["total_hold_rate"] = (
        sum(metrics[name] for name in HOLD_RATE_CAUSES) if total else None
    )

    by_state: dict[str, list[str]] = defaultdict(list)
    for outcome in outcomes:
        record = outcome.record
        if outcome.error is None and record is not None and record.technical_outcome:
            by_state[outcome.state_id].append(record.technical_outcome)
    metrics["same_state_flip_rate"] = _pair_rate(
        by_state, lambda left, right: {left, right} == {"COMPRA", "VENDA"}
    )
    metrics["same_state_disagreement_rate"] = _pair_rate(
        by_state, lambda left, right: left != right
    )
    metrics["max_tokens_count"] = sum(
        record.finish_reason == "MAX_TOKENS"
        for outcome in outcomes
        for record in load_trace(outcome.trace.content)
    )
    return metrics


@dataclass(frozen=True)
class ProposedGates:
    """Gates do Diagnostic Hardening propostos no memo — **não ratificados**.

    Existem como configuração para que o cálculo fique pronto; não produzem
    freeze, B0 nem seleção de configuração enquanto ``status`` for pendente.
    """

    #: ``total_hold_rate`` igual ou acima disto -> DEGENERATE_INACTIVE.
    max_total_hold_rate: float = 0.90
    #: ``same_state_flip_rate`` acima disto -> DEGENERATE_UNSTABLE.
    max_same_state_flip_rate: float = 0.10
    status: str = field(default=PENDING_ADVISOR_RATIFICATION)


PROPOSED_GATES = ProposedGates()

#: Gates G-I (0.90) e G-F (0.10) congelados pelo freeze v1, com os mesmos
#: limiares propostos. G-A (zero falha final) e G-T (zero truncamento) são
#: ``contract_failures`` e ``truncated_outputs`` de :func:`gate_flags`.
H2_FREEZE_V1_GATES = ProposedGates(status="FROZEN_V1")


def gate_flags(
    metrics: Mapping[str, Any], gates: ProposedGates = PROPOSED_GATES
) -> dict[str, Any]:
    """Sinalizações dos gates propostos; passa ou falha, sem ranking."""
    hold = metrics["total_hold_rate"]
    flip = metrics["same_state_flip_rate"]
    return {
        "status": gates.status,
        "contract_failures": metrics["failure_count"] > 0,
        "truncated_outputs": metrics["max_tokens_count"] > 0,
        "degenerate_inactive": hold is not None and hold >= gates.max_total_hold_rate,
        "degenerate_unstable": flip is not None and flip > gates.max_same_state_flip_rate,
    }
