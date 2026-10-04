"""Âncoras CAL-A / CAL-B e grade de CAL-A, congeladas por regra mecânica.

Regra (H2 Methodological Freeze v1, após o Amendment 1), aplicada sobre o
snapshot corrigido antes de qualquer resultado de âncora:

```text
domínio   sessões PETR4.SA do snapshot (sessão oficial B3 com barra observada)
          com 2018-01-12 <= t <= 2024-02-28, available_history_sessions >= 504,
          contrato causal satisfeito, MENOS as 4 sessões de H_real
estratos  30 blocos cronológicos contíguos, tamanhos tão iguais quanto possível
          (numpy.array_split: os primeiros len % 30 estratos têm 1 a mais)
âncora    sessão mediana do estrato; índice (k - 1) // 2 em base 0, ou seja,
          a mediana inferior quando k é par
CAL-B     estratos 3, 6, 9, ..., 30           (10 âncoras)
CAL-A     demais estratos                     (20 âncoras)
```

Nenhum retorno, regime, volatilidade ou resposta de modelo entra na seleção.
CAL-B fica trancada no runner (:func:`require_cal_b_locked`) até a fase
autorizada; Stress Probing não pode usar nenhum estrato de CAL-B.
"""

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

ANCHOR_SNAPSHOT_ID = "20261004T201258177516Z-b4cf39fc761f251d2dd18e787008345a"
ANCHOR_WINDOW = ("2018-01-12", "2024-02-28")
STRATA_COUNT = 30
CAL_B_STRATA: tuple[int, ...] = tuple(range(3, STRATA_COUNT + 1, 3))

ANCHOR_DOMAIN_COUNT = 1515
#: SHA-256 do domínio ordenado (datas ISO unidas por ``\n``).
ANCHOR_DOMAIN_SHA256 = "9dd54e3fdf8e377429e0d87b431600df569ee6cab00f0f30297ac8a289828827"


@dataclass(frozen=True)
class Stratum:
    stratum_id: int
    first: str
    last: str
    size: int
    anchor: str

    @property
    def subset(self) -> str:
        return "CAL-B" if self.stratum_id in CAL_B_STRATA else "CAL-A"


STRATA: tuple[Stratum, ...] = (
    Stratum(1, "2018-01-12", "2018-03-28", 51, "2018-02-21"),
    Stratum(2, "2018-03-29", "2018-06-12", 51, "2018-05-07"),
    Stratum(3, "2018-06-13", "2018-08-23", 51, "2018-07-19"),
    Stratum(4, "2018-08-24", "2018-11-07", 51, "2018-10-01"),
    Stratum(5, "2018-11-08", "2019-01-28", 51, "2018-12-17"),
    Stratum(6, "2019-01-29", "2019-04-12", 51, "2019-03-07"),
    Stratum(7, "2019-04-15", "2019-06-27", 51, "2019-05-22"),
    Stratum(8, "2019-06-28", "2019-09-09", 51, "2019-08-05"),
    Stratum(9, "2019-09-10", "2019-11-21", 51, "2019-10-15"),
    Stratum(10, "2019-11-22", "2020-02-06", 51, "2020-01-02"),
    Stratum(11, "2020-02-07", "2020-04-23", 51, "2020-03-17"),
    Stratum(12, "2020-04-24", "2020-07-08", 51, "2020-06-01"),
    Stratum(13, "2020-07-09", "2020-09-18", 51, "2020-08-13"),
    Stratum(14, "2020-09-21", "2020-12-02", 51, "2020-10-27"),
    Stratum(15, "2020-12-03", "2021-02-22", 51, "2021-01-13"),
    Stratum(16, "2021-02-23", "2021-05-05", 50, "2021-03-29"),
    Stratum(17, "2021-05-06", "2021-07-16", 50, "2021-06-10"),
    Stratum(18, "2021-07-19", "2021-09-28", 50, "2021-08-20"),
    Stratum(19, "2021-09-29", "2021-12-10", 50, "2021-11-04"),
    Stratum(20, "2021-12-13", "2022-02-22", 50, "2022-01-18"),
    Stratum(21, "2022-02-23", "2022-05-09", 50, "2022-03-31"),
    Stratum(22, "2022-05-10", "2022-07-19", 50, "2022-06-13"),
    Stratum(23, "2022-07-20", "2022-09-28", 50, "2022-08-23"),
    Stratum(24, "2022-09-29", "2022-12-13", 50, "2022-11-04"),
    Stratum(25, "2022-12-14", "2023-02-24", 50, "2023-01-18"),
    Stratum(26, "2023-02-27", "2023-05-10", 50, "2023-03-31"),
    Stratum(27, "2023-05-11", "2023-07-20", 50, "2023-06-15"),
    Stratum(28, "2023-07-21", "2023-09-29", 50, "2023-08-24"),
    Stratum(29, "2023-10-02", "2023-12-13", 50, "2023-11-07"),
    Stratum(30, "2023-12-14", "2024-02-28", 50, "2024-01-22"),
)

CAL_A_ANCHORS: tuple[str, ...] = tuple(s.anchor for s in STRATA if s.subset == "CAL-A")
CAL_B_ANCHORS: tuple[str, ...] = tuple(s.anchor for s in STRATA if s.subset == "CAL-B")
#: Compromissos registrados antes de qualquer resultado de âncora.
CAL_A_COMMITMENT_SHA256 = "253308eaf069bbeb085e79aa1fe36cf510eecfc3d4cd5b5f6762a77bce36a36f"
CAL_B_COMMITMENT_SHA256 = "51d73b2285d4e0e103bfb3fc4f5cd26892a6b96fe7dbe8d43cd1e429937f38c0"

#: CAL-B só abre com commit que mude isto, na fase autorizada pelo protocolo.
CAL_B_AUTHORIZED = False


def digest(sessions: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sessions).encode("utf-8")).hexdigest()


def strata_of(domain: Sequence[str]) -> tuple[Stratum, ...]:
    """Os 30 estratos e suas âncoras a partir do domínio ordenado."""
    blocks = np.array_split(np.array(list(domain)), STRATA_COUNT)
    return tuple(
        Stratum(i, str(block[0]), str(block[-1]), len(block), str(block[(len(block) - 1) // 2]))
        for i, block in enumerate(blocks, 1)
    )


def require_cal_b_locked(decision_start: Any, decision_end: Any) -> None:
    """Recusa janela que contenha âncora de CAL-B antes da fase autorizada."""
    if CAL_B_AUTHORIZED:
        return
    start, end = pd.Timestamp(decision_start), pd.Timestamp(decision_end)
    touched = [day for day in CAL_B_ANCHORS if start <= pd.Timestamp(day) <= end]
    if touched:
        raise ValueError(
            f"window {start.date()}..{end.date()} contains locked CAL-B anchor(s) "
            f"{', '.join(touched)}; CAL-B opens only in its authorized phase"
        )


# ── Grade de CAL-A ───────────────────────────────────────────────

#: Unidade auditada: ``recent_volatility`` é o desvio-padrão amostral
#: (ddof=1) dos retornos simples diários das últimas ``volatility_window``
#: sessões até ``t``, x sqrt(252) — volatilidade ANUALIZADA em DECIMAL
#: (0.50 = 50%), arredondada a 6 casas antes da regra ``vol > max``.
CAL_A_VOLATILITY_WINDOWS: tuple[int, ...] = (21, 63)
CAL_A_MAX_VOLATILITIES: tuple[float, ...] = (0.40, 0.50, 0.60)
CAL_A_BASELINE = {"volatility_window": 21, "risk_max_volatility": 0.50}

#: Produto cartesiano, ``config_id`` 1..6 nesta ordem. Nenhuma configuração
#: pode ser acrescentada depois do freeze.
CAL_A_GRID: tuple[dict[str, Any], ...] = tuple(
    {"config_id": i, "volatility_window": window, "risk_max_volatility": vol}
    for i, (window, vol) in enumerate(product(CAL_A_VOLATILITY_WINDOWS, CAL_A_MAX_VOLATILITIES), 1)
)

#: Regra de identificabilidade congelada: menos de 3 âncoras distinguíveis
#: remove CAL-A; 3 ou mais a mantém REDUCED.
IDENTIFIABILITY_MIN_DISTINGUISHING = 3
