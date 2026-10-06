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


#: CAL-B2 (Amendment 8): novo holdout da v2, preenchido só pelo commit de
#: compromisso, antes de qualquer chamada live v2. Selado como a CAL-B.
CAL_B2_ANCHORS: tuple[str, ...] = (
    "2018-08-16", "2019-04-05", "2019-10-07", "2020-07-01", "2021-01-21",
    "2021-09-22", "2022-04-07", "2022-11-01", "2023-06-26", "2023-12-18",
)
CAL_B2_COMMITMENT_SHA256: str | None = "518dd9ddc132244726fc40b2939684876c6f69bf6bad67ea1f91a78fc4e9b167"
CAL_B2_SELECTION_EVIDENCE = "docs/evidence/cal_b2/selection.json"
#: CONSUMED desde o lote one-shot (Amendment 9): ``authorize_cal_b2`` recusa
#: reabri-la, com PASS ou FAIL.
CAL_B2_STATUS = "CONSUMED"


#: CAL-B3 (Amendment 10): novo holdout da v3, preenchido só pelo commit de
#: compromisso, antes de qualquer chamada live v3. Selada; não executada.
CAL_B3_ANCHORS: tuple[str, ...] = (
    "2018-08-03", "2019-03-19", "2019-10-18", "2020-05-13", "2021-01-06",
    "2021-08-17", "2022-03-11", "2022-11-29", "2023-05-12", "2024-01-11",
)
CAL_B3_COMMITMENT_SHA256: str | None = "a5cadecd361de5059370bf4bfa97b1417b82eb8951950cf92b0aebc7edecdbaf"
CAL_B3_SELECTION_EVIDENCE = "docs/evidence/cal_b3/selection.json"
CAL_B3_STATUS = "SEALED"


def sealed_holdout_anchors() -> tuple[str, ...]:
    """Datas que nenhuma janela de development pode tocar (CAL-B1, CAL-B2 e CAL-B3)."""
    return (*CAL_B_ANCHORS, *CAL_B2_ANCHORS, *CAL_B3_ANCHORS)


def require_cal_b_locked(decision_start: Any, decision_end: Any) -> None:
    """Recusa janela que contenha âncora de CAL-B (B1 ou B2) antes da fase autorizada."""
    if CAL_B_AUTHORIZED:
        return
    start, end = pd.Timestamp(decision_start), pd.Timestamp(decision_end)
    touched = [day for day in sealed_holdout_anchors() if start <= pd.Timestamp(day) <= end]
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


# ── Execução de CAL-A (Amendment 3), registrada antes da primeira execução ──

#: Repetições independentes por âncora. O tratamento tem inferência estocástica
#: sem seed; R = 3 (dentro do teto R <= 3 do protocolo) evita escolher uma
#: configuração por uma realização técnica favorável ao acaso.
CAL_A_REPETITIONS = 3
#: Contrato de âncora: capital em caixa, posição zero, decisão em close(t),
#: execução em open(t+1), CostSpec congelado (protocolo, seção 10).
CAL_A_INITIAL_CAPITAL = 100_000.0
CAL_A_MINIMUM_HISTORY_SESSIONS = 504
CAL_A_COST_SPEC = {"brokerage_fixed": 0.0, "spread_bps": 5.0, "tax_rate": 0.00032}
#: anchor_score[c, a] = média dos retornos líquidos realizados das R repetições;
#: S1[c] = média de anchor_score[c, a] sobre as 20 âncoras. Maior S1 vence;
#: empate exato -> menor config_id; todos iguais -> CAL_A_DISCRIMINATION = NONE.
CAL_A_SCORE = "S1"


# ── Resultado de CAL-A (congelado) ───────────────────────────────

#: Seleção mecânica pela regra do Amendment 3. Os seis S1 foram exatamente
#: iguais, então CAL_A_DISCRIMINATION = NONE e o desempate pelo menor
#: config_id escolheu a configuração 1. ``volatility_window`` e
#: ``risk_max_volatility`` ficam congelados e saem da autoridade das fases
#: seguintes; ``risk_max_drawdown`` continua 0.25 (autoridade do Sequential
#: Development).
CAL_A_EVIDENCE = "docs/evidence/cal_a/run_20261004T231101Z/summary.json"
CAL_A_DISCRIMINATION = "NONE"
#: A configuração 1 veio do fallback de empate, não de desempenho superior.
CAL_A_SELECTION_BASIS = "PROTOCOL_TIE_FALLBACK"
CAL_A_SELECTED_CONFIG = {
    "config_id": 1,
    "volatility_window": 21,
    "risk_max_volatility": 0.40,
    "S1": -0.00025157128306495897,
    "ranking": (1, 2, 3, 4, 5, 6),
    "tie": "ALL_SIX_EQUAL_FALLBACK_LOWEST_CONFIG_ID",
}


# ── CAL-B: autorização limitada (Amendment 7, CAL_B_PROTOCOL_FREEZE_V1) ──
#
# ``CAL_B_AUTHORIZED`` continua False: o ``ExperimentRunner`` (e qualquer
# janela) segue recusando âncora de CAL-B. A única porta é esta autorização,
# limitada à fase CAL-B, ao hash comprometido, às 10 datas exatas e a UMA
# repetição por data. Depois da execução, ``CAL_B_STATUS = "CONSUMED"`` fecha a
# porta para sempre nesta versão metodológica.

CAL_B_PHASE = "CAL-B"
CAL_B_REPETITIONS = 1
#: CONSUMED desde o lote one-shot (Amendment 7): ``authorize_cal_b`` recusa
#: reabrir o holdout nesta versão metodológica.
CAL_B_STATUS = "CONSUMED"


@dataclass(frozen=True)
class CalBAuthorization:
    phase: str
    commitment_sha256: str
    anchors: tuple[str, ...]
    repetitions: int

    def require_anchor(self, session: Any) -> str:
        """Só as 10 datas comprometidas; qualquer outra continua recusada."""
        day = str(pd.Timestamp(session).date())
        if day not in self.anchors:
            raise ValueError(f"{day} is not a committed CAL-B anchor; refused")
        return day


def authorize_cal_b(phase: str, commitment_sha256: str, dates: Sequence[str],
                    repetitions: int) -> CalBAuthorization:
    """Autorização one-shot; recusa qualquer desvio do compromisso."""
    if CAL_B_STATUS != "SEALED":
        raise ValueError(f"CAL-B is {CAL_B_STATUS}: the holdout cannot be opened again")
    if phase != CAL_B_PHASE:
        raise ValueError(f"CAL-B authorization requires phase {CAL_B_PHASE!r}, got {phase!r}")
    if commitment_sha256 != CAL_B_COMMITMENT_SHA256 or digest(CAL_B_ANCHORS) != CAL_B_COMMITMENT_SHA256:
        raise ValueError("CAL-B commitment hash does not match the frozen anchors")
    if tuple(dates) != CAL_B_ANCHORS:
        raise ValueError("CAL-B authorization requires exactly the 10 committed dates, in order")
    if isinstance(repetitions, bool) or repetitions != CAL_B_REPETITIONS:
        raise ValueError(f"CAL-B is one-shot: repetitions must be {CAL_B_REPETITIONS}")
    return CalBAuthorization(phase, commitment_sha256, tuple(dates), repetitions)


# ── CAL-B2: autorização limitada (Amendment 9, CAL_B2_PROTOCOL_FREEZE_V1) ──
#
# Mesma porta da CAL-B1, mais a identidade do tratamento: só a fase CAL-B2, o
# hash comprometido, as 10 datas, R = 1, tratamento v2, prompt técnico v2 e o
# spec hash congelado. ``CAL_B_AUTHORIZED`` (global) continua False.

CAL_B2_PHASE = "CAL-B2"
CAL_B2_REPETITIONS = 1
CAL_B2_TREATMENT_VERSION = 2
CAL_B2_TECHNICAL_PROMPT_VERSION = 2
#: SHA256(canonical_json(ParticipantSpec("llm_agent", CAL_B2_FROZEN_PARAMS).to_dict())).
CAL_B2_SPEC_SHA256 = "89ac12071d8f68774a3f2af8192c04ff4254a62df90bfc7c5c8d6301767c2324"


def authorize_cal_b2(phase: str, commitment_sha256: str, dates: Sequence[str], repetitions: int,
                     treatment_version: int, technical_prompt_version: int, spec_sha256: str) -> CalBAuthorization:
    """Autorização one-shot da CAL-B2; qualquer desvio falha fechado."""
    if CAL_B2_STATUS != "SEALED":
        raise ValueError(f"CAL-B2 is {CAL_B2_STATUS}: the holdout cannot be opened again")
    if phase != CAL_B2_PHASE:
        raise ValueError(f"CAL-B2 authorization requires phase {CAL_B2_PHASE!r}, got {phase!r}")
    if commitment_sha256 != CAL_B2_COMMITMENT_SHA256 or digest(CAL_B2_ANCHORS) != CAL_B2_COMMITMENT_SHA256:
        raise ValueError("CAL-B2 commitment hash does not match the frozen anchors")
    if tuple(dates) != CAL_B2_ANCHORS:
        raise ValueError("CAL-B2 authorization requires exactly the 10 committed dates, in order")
    if isinstance(repetitions, bool) or repetitions != CAL_B2_REPETITIONS:
        raise ValueError(f"CAL-B2 is one-shot: repetitions must be {CAL_B2_REPETITIONS}")
    if (treatment_version, technical_prompt_version) != (CAL_B2_TREATMENT_VERSION, CAL_B2_TECHNICAL_PROMPT_VERSION):
        raise ValueError("CAL-B2 requires treatment version 2 and technical prompt version 2")
    if spec_sha256 != CAL_B2_SPEC_SHA256:
        raise ValueError("CAL-B2 participant spec hash differs from the frozen H2 v2 spec")
    return CalBAuthorization(phase, commitment_sha256, tuple(dates), repetitions)
