"""Camada experimental: especificação, orquestração e resultado auditável."""

from src.artifacts import RunArtifact, RunArtifactProvider
from src.experiments.participants import (
    PARTICIPANT_REGISTRY,
    build_participant,
    required_tickers,
)
from src.experiments.runner import (
    RUN_MANIFEST_SCHEMA_VERSION,
    DirtyRepositoryError,
    ExperimentRunner,
    RunResult,
)
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
    "RUN_MANIFEST_SCHEMA_VERSION",
    "SPEC_SCHEMA_VERSION",
    "CostSpec",
    "DirtyRepositoryError",
    "ExperimentRunner",
    "ExperimentSpec",
    "MetricSpec",
    "ParticipantSpec",
    "RunArtifact",
    "RunArtifactProvider",
    "RunResult",
    "build_participant",
    "canonical_json",
    "required_tickers",
]
