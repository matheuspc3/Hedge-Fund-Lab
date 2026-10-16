"""Contexto metodológico de uma execução, declarado antes de executá-la.

``phase`` e ``case_id`` respondem *que papel este run tem no experimento*, e
não *o que ele computa*. Por isso ficam deliberadamente fora do ``spec_hash``:
dois runs que só diferem na fase produzem exatamente os mesmos números, e um
hash que os separasse deixaria de significar "mesma configuração, mesmo
resultado" — a propriedade que o repositório já pagou para manter quando
removeu parâmetros mortos da ``ParticipantSpec``.

O controle correto contra reclassificação não é hashear o rótulo — bastaria
construir a spec já com o rótulo desejado — e sim **declará-lo antes de
executar**. Por isso o contexto entra pelo construtor do runner, é congelado
ali, e ``persist()`` não tem como anexá-lo ou trocá-lo depois de ver o
resultado. Diretório nunca é identidade metodológica.
"""

from dataclasses import dataclass
from typing import Any

#: Fases científicas do protocolo de calibração retrospectiva. Ordem de
#: declaração, não hierarquia; nenhuma data está escolhida em lugar algum.
PHASE_CALIBRATION = "CALIBRATION"
PHASE_VALIDATION = "VALIDATION"
PHASE_FINAL_TEST = "FINAL_TEST"
PHASE_LIVE_SHADOW = "LIVE_SHADOW"

SCIENTIFIC_PHASES: tuple[str, ...] = (
    PHASE_CALIBRATION,
    PHASE_VALIDATION,
    PHASE_FINAL_TEST,
    PHASE_LIVE_SHADOW,
)

#: Comprimento máximo de ``case_id``: rótulo humano curto, não descrição.
MAX_CASE_ID_LENGTH = 120


@dataclass(frozen=True)
class RunContext:
    """Papel metodológico declarado de uma execução.

    ``case_id`` é opcional e puramente humano (``"calibration-election-01"``).
    Como ``phase``, não altera comportamento algum e não entra no
    ``spec_hash``; existe para que um Calibration Case tenha nome estável no
    manifest sem que o nome do diretório vire evidência.
    """

    phase: str
    case_id: str | None = None

    def __post_init__(self) -> None:
        phase = self.phase.strip() if isinstance(self.phase, str) else self.phase
        if not isinstance(phase, str) or not phase:
            raise ValueError("phase cannot be empty")
        if phase not in SCIENTIFIC_PHASES:
            supported = ", ".join(SCIENTIFIC_PHASES)
            raise ValueError(f"unsupported phase: {phase!r}; supported: {supported}")

        case_id = self.case_id
        if case_id is not None:
            if not isinstance(case_id, str):
                raise ValueError(
                    f"case_id must be a string, got {type(case_id).__name__}"
                )
            case_id = case_id.strip()
            if not case_id:
                raise ValueError(
                    "case_id cannot be blank; omit it entirely when the run has "
                    "no methodological case label"
                )
            if len(case_id) > MAX_CASE_ID_LENGTH:
                raise ValueError(
                    f"case_id must be at most {MAX_CASE_ID_LENGTH} characters"
                )

        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "case_id", case_id)

    def to_dict(self) -> dict[str, Any]:
        """Forma publicada no manifest — nunca na spec."""
        return {"phase": self.phase, "case_id": self.case_id}
