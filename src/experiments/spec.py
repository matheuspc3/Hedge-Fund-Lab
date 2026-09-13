"""Especificação serializável de uma execução experimental.

A spec descreve *o que* executar, nunca *como* — nenhum objeto vivo, nenhuma
instância de participante, nenhum caminho local. Dois runs cujas specs
serializam igual compartilham o mesmo ``spec_hash``.

Os defaults de custo e de métrica são os defaults técnicos já existentes em
``CostModel`` e ``performance_metrics``; continuam não congelados
cientificamente e por isso são registrados explicitamente no manifest.
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.backtesting.costs import CostModel

SPEC_SCHEMA_VERSION = 1


def canonical_json(payload: Any) -> str:
    """Serialização estável: chaves ordenadas, sem espaço supérfluo."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


@dataclass(frozen=True)
class ParticipantSpec:
    """Participante descrito por um nome do registry e parâmetros simples.

    ``kind`` é resolvido pelo registry explícito em
    :mod:`src.experiments.participants`; não existe import path arbitrário.
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
        object.__setattr__(self, "params", params)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "params": dict(self.params)}


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
    """

    snapshot_id: str
    participant: ParticipantSpec
    initial_capital: float
    costs: CostSpec = field(default_factory=CostSpec)
    metrics: MetricSpec = field(default_factory=MetricSpec)

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
        }

    @property
    def spec_hash(self) -> str:
        """SHA-256 da spec canônica: mesma configuração, mesmo hash."""
        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()
