"""Calendário das fases do H2 e a fronteira que nenhuma ordem pode cruzar.

Decisão em close(t) executa em open(t+1). Uma decisão tomada na última sessão
de uma fase executaria na fase seguinte, por isso a regra geral:

```text
no_order_execution_may_cross_phase_boundary
    a sessão de liquidação (a sessão seguinte a decision_end) precisa estar
    dentro da mesma fase da janela de decisão
```

Ela vale para toda fronteira declarada aqui (Sequential Development ->
Validation e, quando forem congeladas, Validation -> Final Test). O runner
também recorta os dados de mercado no fim da fase: nenhum preço posterior
chega ao motor.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class PhaseWindow:
    name: str
    start: str
    end: str


SEQUENTIAL_DEVELOPMENT_START = "2024-03-01"
SEQUENTIAL_DEVELOPMENT_END = "2024-08-30"
#: Última sessão de decisão: a liquidação dela é 2024-08-30, dentro da fase.
SEQUENTIAL_DEVELOPMENT_LAST_DECISION = "2024-08-29"
VALIDATION_START = "2024-09-02"

PHASES: tuple[PhaseWindow, ...] = (
    PhaseWindow("SEQUENTIAL_DEVELOPMENT", SEQUENTIAL_DEVELOPMENT_START, SEQUENTIAL_DEVELOPMENT_END),
)


def phase_of(
    decision_start: Any, decision_end: Any, extra: tuple[PhaseWindow, ...] = ()
) -> PhaseWindow | None:
    """A fase que contém a janela; recusa janela que atravessa uma fronteira.

    ``extra`` acrescenta fronteiras declaradas pelo run (ex.: uma janela de
    Stress), com a mesma regra das fases globais.
    """
    start, end = pd.Timestamp(decision_start), pd.Timestamp(decision_end)
    for phase in (*PHASES, *extra):
        low, high = pd.Timestamp(phase.start), pd.Timestamp(phase.end)
        inside = (low <= start <= high, low <= end <= high)
        if all(inside):
            return phase
        if any(inside):
            raise ValueError(
                f"decision window {start.date()}..{end.date()} crosses the "
                f"{phase.name} boundary {phase.start}..{phase.end}"
            )
    return None


def require_execution_within_phase(settlement_session: Any, phase: PhaseWindow) -> None:
    """no_order_execution_may_cross_phase_boundary."""
    settlement = pd.Timestamp(settlement_session)
    if settlement > pd.Timestamp(phase.end):
        raise ValueError(
            f"no_order_execution_may_cross_phase_boundary: the last decision "
            f"would execute on {settlement.date()}, after {phase.name} ends on "
            f"{phase.end}"
        )


# ── Sequential Development (Amendment 5) ─────────────────────────

#: Grade congelada de ``risk_max_drawdown``; D01 é o baseline e vence empate.
SEQUENTIAL_DEV_GRID: tuple[dict[str, Any], ...] = (
    {"config_id": 1, "name": "D01", "risk_max_drawdown": 0.25},
    {"config_id": 2, "name": "D02", "risk_max_drawdown": 0.15},
    {"config_id": 3, "name": "D03", "risk_max_drawdown": 0.35},
)
SEQUENTIAL_DEV_REPETITIONS = 3
#: S2[c] = média do Sharpe científico v1 nas 3 repetições; maior vence;
#: empate exato -> menor config_id; três iguais -> DISCRIMINATION = NONE.
SEQUENTIAL_DEV_SCORE = "S2"


# ── Resultado do Sequential Development (congelado) ──────────────

#: Seleção mecânica pela regra do Amendment 5. O drawdown canônico máximo
#: (0.080) não chegou a nenhum limite da grade, as três trajetórias foram
#: idênticas em cada repetição e os três S2 exatamente iguais: DISCRIMINATION
#: = NONE, D01 pelo fallback do protocolo — não por desempenho superior.
SEQUENTIAL_DEV_FREEZE_COMMIT = "2461952a4b1ee84a08aa63261f6a677d79cca3bb"
SEQUENTIAL_DEV_EVIDENCE = "docs/evidence/sequential_dev/run_20261004T235634Z/summary.json"
SEQUENTIAL_DEV_DISCRIMINATION = "NONE"
SEQUENTIAL_DEV_SELECTION_BASIS = "PROTOCOL_TIE_FALLBACK"
SEQUENTIAL_DEV_SELECTED_CONFIG = {
    "config_id": 1,
    "name": "D01",
    "risk_max_drawdown": 0.25,
    "S2": 1.8995241002787928,
    "ranking": (1, 2, 3),
    "discrimination": SEQUENTIAL_DEV_DISCRIMINATION,
    "selection_basis": SEQUENTIAL_DEV_SELECTION_BASIS,
    "freeze_commit": SEQUENTIAL_DEV_FREEZE_COMMIT,
    "evidence": SEQUENTIAL_DEV_EVIDENCE,
}
