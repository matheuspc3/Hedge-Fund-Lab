"""Camada experimental: especificação, orquestração e resultado auditável."""

from src.experiments.participants import (
    PARTICIPANT_REGISTRY,
    build_participant,
    required_tickers,
)
from src.experiments.runner import DirtyRepositoryError, ExperimentRunner, RunResult
from src.experiments.spec import (
    SPEC_SCHEMA_VERSION,
    CostSpec,
    ExperimentSpec,
    MetricSpec,
    ParticipantSpec,
    canonical_json,
)

__all__ = [
    "PARTICIPANT_REGISTRY",
    "SPEC_SCHEMA_VERSION",
    "CostSpec",
    "DirtyRepositoryError",
    "ExperimentRunner",
    "ExperimentSpec",
    "MetricSpec",
    "ParticipantSpec",
    "RunResult",
    "build_participant",
    "canonical_json",
    "required_tickers",
]
