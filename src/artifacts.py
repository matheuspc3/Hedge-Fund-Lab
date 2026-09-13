"""Evidência publicável que um participante produz durante uma execução.

Contrato genérico e deliberadamente pequeno: o runner publica o que o
participante declara como evidência e **não conhece nenhum participante em
particular**. Não existe ``isinstance(participant, LLMParticipant)`` na camada
experimental; existe um ``Protocol`` que qualquer participante pode satisfazer
e que os clássicos simplesmente não implementam.

Este módulo fica fora de ``src.agents`` e de ``src.experiments`` de propósito:
os dois lados precisam do contrato e importá-lo de qualquer um deles criaria
ciclo (``experiments.participants`` importa ``agents.participant``).
"""

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

#: Nomes reservados pelo próprio runner; um artefato de participante não pode
#: sobrescrevê-los.
_INVALID_FILENAME_CHARS = ("/", "\\", ":")


def canonical_json(payload: Any) -> str:
    """Serialização estável: chaves ordenadas, sem espaço supérfluo."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class RunArtifact:
    """Arquivo de evidência **já congelado** no fim da execução.

    Guarda os bytes finais serializados, não o objeto vivo que os produziu:
    publicar um run não pode reconsultar o participante, o provedor nem
    qualquer estado externo — a mesma regra que ``SnapshotEvidence`` aplica ao
    snapshot. ``sha256`` é calculado exatamente sobre esses bytes, de modo que
    "manifest íntegro, arquivo adulterado" seja um estado detectável.

    ``summary`` carrega os poucos escalares que o manifest publica junto do
    hash (por exemplo ``call_count``); ele descreve o conteúdo, não o repete.
    """

    name: str
    filename: str
    schema_version: int
    content: bytes
    summary: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = self.name.strip()
        filename = self.filename.strip()
        if not name:
            raise ValueError("artifact name cannot be empty")
        if not filename:
            raise ValueError("artifact filename cannot be empty")
        if any(char in filename for char in _INVALID_FILENAME_CHARS):
            raise ValueError(
                f"artifact filename {filename!r} must be a plain file name, " "not a path"
            )
        if filename in {".", ".."}:
            raise ValueError(f"artifact filename {filename!r} is not a file name")
        if not isinstance(self.schema_version, int) or isinstance(
            self.schema_version, bool
        ):
            raise ValueError("artifact schema_version must be an integer")
        if self.schema_version < 1:
            raise ValueError("artifact schema_version must be >= 1")
        if not isinstance(self.content, bytes):
            raise ValueError("artifact content must be bytes already serialized")
        summary = dict(self.summary)
        for key, value in summary.items():
            if not isinstance(key, str) or not key:
                raise ValueError("artifact summary keys must be non-empty strings")
            if value is not None and not isinstance(value, (str, int, float, bool)):
                raise ValueError(
                    f"artifact summary {key!r} must be a JSON scalar, "
                    f"got {type(value).__name__}"
                )
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "filename", filename)
        object.__setattr__(self, "summary", MappingProxyType(summary))

    @property
    def sha256(self) -> str:
        """SHA-256 dos bytes publicados, e de mais nada."""
        return hashlib.sha256(self.content).hexdigest()

    def describe(self) -> dict[str, Any]:
        """Forma que o manifest publica: onde está, o que é e como conferir."""
        return {
            "path": self.filename,
            "schema_version": self.schema_version,
            "sha256": self.sha256,
            "bytes": len(self.content),
            **dict(self.summary),
        }


@runtime_checkable
class RunArtifactProvider(Protocol):
    """Participante que publica evidência própria junto do run.

    Quem não implementa continua funcionando: o runner publica apenas curva,
    trades e manifest, e o manifest registra ``participant_artifacts`` vazio.
    """

    def run_artifacts(self) -> tuple[RunArtifact, ...]:
        """Evidência congelada desta execução, pronta para ser escrita."""
        ...
