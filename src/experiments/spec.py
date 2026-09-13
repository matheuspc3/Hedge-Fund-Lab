"""Especificação serializável de uma execução experimental.

A spec descreve *o que* executar, nunca *como* — nenhum objeto vivo, nenhuma
instância de participante, nenhum caminho local. Dois runs cujas specs
serializam igual compartilham o mesmo ``spec_hash``.

Os defaults de custo e de métrica são os defaults técnicos já existentes em
``CostModel`` e ``performance_metrics``; continuam não congelados
cientificamente e por isso são registrados explicitamente no manifest.
"""

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date as Date
from types import MappingProxyType
from typing import Any, Mapping

import pandas as pd

from src.artifacts import canonical_json
from src.backtesting.costs import CostModel

# Schema 2: a spec passa a declarar a janela avaliada. O período deixou de ser
# consequência da cobertura do snapshot e virou configuração material, dentro
# do ``spec_hash``.
SPEC_SCHEMA_VERSION = 2

# ``canonical_json`` vive em :mod:`src.artifacts` para que a spec e o trace de
# LLM usem literalmente a mesma serialização estável; continua reexportado
# aqui porque é parte da API pública desta camada desde antes.
__all__ = [
    "SPEC_SCHEMA_VERSION",
    "CostSpec",
    "EvaluationSpec",
    "ExperimentSpec",
    "MetricSpec",
    "ParticipantSpec",
    "canonical_json",
]


@dataclass(frozen=True)
class ParticipantSpec:
    """Participante descrito por um nome do registry e parâmetros simples.

    ``kind`` é resolvido pelo registry explícito em
    :mod:`src.experiments.participants`; não existe import path arbitrário.

    ``params`` é copiado na construção e guardado como mapeamento read-only:
    ``frozen=True`` congela o *campo*, não o dicionário que ele aponta, e uma
    spec cujo conteúdo ainda pode mudar não tem identidade estável.
    """

    kind: str
    params: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        kind = self.kind.strip()
        if not kind:
            raise ValueError("participant kind cannot be empty")
        params = dict(self.params)
        for name, value in params.items():
            if not isinstance(name, str) or not name:
                raise ValueError("participant param names must be non-empty strings")
            if not isinstance(value, (str, int, float, bool)) or isinstance(
                value, complex
            ):
                raise ValueError(
                    f"participant param {name!r} must be a JSON scalar, "
                    f"got {type(value).__name__}"
                )
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"participant param {name!r} must be finite")
        object.__setattr__(self, "kind", kind)
        # Cópia defensiva + view read-only: nem o dicionário do chamador nem
        # ``participant.params[...]`` podem alterar a spec depois de criada.
        object.__setattr__(self, "params", MappingProxyType(params))

    def to_dict(self) -> dict[str, Any]:
        """``dict`` novo e JSON-serializável; mutá-lo não atinge a spec."""
        return {"kind": self.kind, "params": dict(self.params)}


def _require_session_date(name: str, value: Any) -> str:
    """Normaliza uma âncora para ``YYYY-MM-DD``, ou recusa a configuração.

    A spec é identidade: ``"2024-01-02"``, ``Timestamp("2024-01-02 00:00")`` e
    ``date(2024, 1, 2)`` descrevem o mesmo pregão e precisam produzir o mesmo
    ``spec_hash``. Guardar o objeto original deixaria a identidade depender de
    como o chamador escreveu a data.

    Horário é recusado em vez de truncado: o contrato da arena é de sessão
    diária, e aceitar ``09:30`` silenciosamente sugeriria uma precisão
    intradiária que o motor não tem.
    """
    if not isinstance(value, (str, Date, pd.Timestamp)):
        raise ValueError(
            f"{name} must be a date or ISO date string, got {type(value).__name__}"
        )
    try:
        stamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} is not a valid date: {value!r}") from exc
    if pd.isna(stamp):
        raise ValueError(f"{name} cannot be NaT")
    if (stamp.hour, stamp.minute, stamp.second, stamp.microsecond) != (0, 0, 0, 0):
        raise ValueError(
            f"{name} must be a calendar date without time-of-day, got {value!r}; "
            "the arena decides once per session"
        )
    if stamp.tzinfo is not None:
        raise ValueError(
            f"{name} must be timezone-naive, got {value!r}; a session date is "
            "not an instant"
        )
    return stamp.date().isoformat()


#: Formas aceitas para uma âncora de sessão. Todas colapsam para ``str`` na
#: construção, de modo que a identidade não dependa de como a data foi escrita.
SessionDate = str | Date | pd.Timestamp


@dataclass(frozen=True)
class EvaluationSpec:
    """Janela em que as decisões contam para o experimento.

    Separa **dados disponíveis** de **período avaliado**. O snapshot continua
    descrevendo a cobertura inteira; esta spec declara onde, dentro dela, as
    decisões passam a valer::

        data_start ..... decision_start ..... decision_end . settlement
                   warm-up                avaliado

    As sessões anteriores a ``decision_start`` existem como histórico causal e
    nada mais: não decidem, não negociam e não entram na curva publicada.

    ``minimum_history_sessions`` é **obrigatório e sem default**. Um default
    técnico aqui viraria decisão científica silenciosa: quem executa precisa
    declarar quanto histórico exige antes da primeira decisão. O valor
    científico do protocolo v1 continua ``TBD`` — a spec exige que exista um
    número declarado, não qual número é.

    A semântica contada é a de
    :attr:`~src.backtesting.arena.EvaluationWindow.available_history_sessions`:
    as sessões **comuns** estritamente anteriores a ``decision_start``, mais a
    própria barra de ``decision_start``. O gate é
    ``available_history_sessions >= minimum_history_sessions``, de modo que
    ``available == minimum`` passa e ``available == minimum - 1`` falha.

    ``history_mode`` não é campo: o v1 é sempre expansivo — a decisão em ``t``
    enxerga todo o histórico causal disponível até ``t``. Rolling é ablation
    futura e não existe como parâmetro, para não criar hiperparâmetro morto.
    """

    #: Aceito como texto ISO, ``date`` ou ``Timestamp`` e **normalizado para
    #: ``YYYY-MM-DD``** na construção: depois de criada, a spec guarda sempre a
    #: forma textual, que é o que entra no ``spec_hash``.
    decision_start: SessionDate
    decision_end: SessionDate
    minimum_history_sessions: int

    def __post_init__(self) -> None:
        start = _require_session_date("decision_start", self.decision_start)
        end = _require_session_date("decision_end", self.decision_end)
        if start > end:
            raise ValueError(
                f"decision_start {start} must not be after decision_end {end}"
            )
        minimum = self.minimum_history_sessions
        # ``bool`` é subclasse de ``int``: ``True`` viraria 1 sessão de
        # histórico exigida, uma configuração inválida entrando no hash.
        if isinstance(minimum, bool) or not isinstance(minimum, int):
            raise ValueError(
                "minimum_history_sessions must be an integer, got "
                f"{type(minimum).__name__}: {minimum!r}"
            )
        if minimum < 1:
            raise ValueError(
                "minimum_history_sessions must be >= 1; the first evaluated "
                "decision always observes at least its own session"
            )
        object.__setattr__(self, "decision_start", start)
        object.__setattr__(self, "decision_end", end)
        object.__setattr__(self, "minimum_history_sessions", minimum)

    @property
    def single_anchor(self) -> bool:
        """Calibration Anchor: uma única decisão avaliada."""
        return self.decision_start == self.decision_end

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_start": self.decision_start,
            "decision_end": self.decision_end,
            "minimum_history_sessions": self.minimum_history_sessions,
        }


@dataclass(frozen=True)
class CostSpec:
    """Parâmetros de ``CostModel``, serializados em vez do objeto."""

    brokerage_fixed: float = 0.0
    spread_bps: float = 0.0
    tax_rate: float = 0.0

    def __post_init__(self) -> None:
        for name in ("brokerage_fixed", "spread_bps", "tax_rate"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and >= 0")
            object.__setattr__(self, name, value)

    def build(self) -> CostModel:
        return CostModel(
            brokerage_fixed=self.brokerage_fixed,
            spread_bps=self.spread_bps,
            tax_rate=self.tax_rate,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "brokerage_fixed": self.brokerage_fixed,
            "spread_bps": self.spread_bps,
            "tax_rate": self.tax_rate,
        }


@dataclass(frozen=True)
class MetricSpec:
    """Parâmetros técnicos de ``performance_metrics``.

    ``freq=252``, ``rf=0`` e ``mar=0`` são os defaults técnicos já documentados
    como não congelados; ficam aqui para serem registrados, não aprovados.
    """

    risk_free_rate: float = 0.0
    mar: float = 0.0
    periods_per_year: int = 252

    def __post_init__(self) -> None:
        for name in ("risk_free_rate", "mar"):
            value = float(getattr(self, name))
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, value)
        periods = int(self.periods_per_year)
        if periods <= 0:
            raise ValueError("periods_per_year must be > 0")
        object.__setattr__(self, "periods_per_year", periods)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_free_rate": self.risk_free_rate,
            "mar": self.mar,
            "periods_per_year": self.periods_per_year,
        }


@dataclass(frozen=True)
class ExperimentSpec:
    """Tudo que identifica tecnicamente uma execução, e nada além disso.

    O snapshot entra por ``snapshot_id``, não por caminho: o diretório onde ele
    está é ambiente de execução e não pode alterar a identidade da spec.

    O universo entregue ao motor é derivado deterministicamente: participantes
    single-asset declaram ``ticker`` nos parâmetros e recebem apenas ele;
    participantes de carteira recebem todos os tickers do snapshot. O universo
    efetivo é registrado no manifest de cada run.

    ``evaluation`` declara o período avaliado e entra no ``spec_hash``, porque
    muda as decisões, os trades e as métricas. ``phase`` e ``case_id`` **não**
    entram: são contexto metodológico do run, não configuração computacional —
    dois runs que só diferem na fase produzem exatamente os mesmos números.
    """

    snapshot_id: str
    participant: ParticipantSpec
    initial_capital: float
    costs: CostSpec = field(default_factory=CostSpec)
    metrics: MetricSpec = field(default_factory=MetricSpec)
    #: Janela avaliada. ``None`` é o **modo técnico legado**: toda a cobertura
    #: efetiva do snapshot é decidida, como antes da janela existir. O caminho
    #: científico declara a janela, e o runner recusa executar uma fase
    #: científica sem ela.
    evaluation: EvaluationSpec | None = None

    def __post_init__(self) -> None:
        snapshot_id = self.snapshot_id.strip()
        if not snapshot_id:
            raise ValueError("snapshot_id cannot be empty")
        capital = float(self.initial_capital)
        if not math.isfinite(capital) or capital <= 0:
            raise ValueError("initial_capital must be finite and > 0")
        object.__setattr__(self, "snapshot_id", snapshot_id)
        object.__setattr__(self, "initial_capital", capital)

    def to_dict(self) -> dict[str, Any]:
        """Forma canônica da spec — base do ``spec_hash``."""
        return {
            "schema_version": SPEC_SCHEMA_VERSION,
            "snapshot_id": self.snapshot_id,
            "participant": self.participant.to_dict(),
            "initial_capital": self.initial_capital,
            "costs": self.costs.to_dict(),
            "metrics": self.metrics.to_dict(),
            # Sempre presente na forma canônica, inclusive como ``null``: a
            # ausência de janela é uma configuração, não um campo que sumiu.
            "evaluation": (
                None if self.evaluation is None else self.evaluation.to_dict()
            ),
        }

    @property
    def spec_hash(self) -> str:
        """SHA-256 da spec canônica: mesma configuração, mesmo hash."""
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()
