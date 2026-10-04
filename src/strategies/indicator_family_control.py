"""Indicator-family-matched classical control.

Controle clássico determinístico que consome as **mesmas quatro famílias** de
indicadores que o participante LLM recebe — SMA, Bollinger, RSI e MACD — com
os mesmos parâmetros do pipeline de features (``DataTransformer``).

Não é "information-matched": o LLM vê o *estado* contínuo das oito features
em ``t``, sem defasagem; este controle vê *eventos* de cruzamento ``t-1 -> t``
e descarta magnitudes. Nenhum dos dois information sets contém o outro. O
controle iguala famílias de indicadores, não informação — limitação declarada.

Papel: ablation adicional do H2 ("o LLM acrescenta algo além de consumir as
quatro famílias ao mesmo tempo?"). Não substitui benchmark algum: Buy & Hold
continua primário; SMA e Bollinger, secundários.
"""

from collections.abc import Mapping

import pandas as pd

from src.indicators.macd import macd
from src.indicators.rsi import rsi
from src.strategies.base import SignalParticipant
from src.strategies.bollinger_bands import BollingerParticipant
from src.strategies.sma_cross import SMACrossParticipant

# Parâmetros fixos, iguais aos de ``DataTransformer.calculate_indicators``.
# Não são argumentos do construtor de propósito: o controle não tem nada a
# calibrar — sem pesos, sem limiar de agregação, sem prioridade entre famílias.
SMA_FAST, SMA_SLOW = 50, 200
BB_WINDOW, BB_K = 20, 2.0
RSI_PERIOD = 14
MACD_FAST, MACD_SLOW, MACD_SIGNAL = 12, 26, 9

#: PENDING_ADVISOR_RATIFICATION — direção da regra de RSI. Proposta v1:
#: entrada na zona extrema (cruza para baixo de 30 -> +1; cruza para cima de 70
#: -> -1), por consistência com o ``BollingerParticipant``, que também reage à
#: entrada na região extrema. É decisão metodológica ex ante, não consequência
#: da definição do RSI; Wilder (1978) sustenta só o período e as referências
#: 70/30, não a direção desta regra.
RSI_OVERSOLD, RSI_OVERBOUGHT = 30.0, 70.0


def crossing_signal(fast_prev: float, slow_prev: float, fast: float, slow: float) -> int:
    """Cruzamento ``t-1 -> t`` com a mesma regra do ``SMACrossParticipant``."""
    if any(pd.isna(value) for value in (fast_prev, slow_prev, fast, slow)):
        return 0
    if fast_prev <= slow_prev and fast > slow:
        return 1
    if fast_prev >= slow_prev and fast < slow:
        return -1
    return 0


def rsi_entry_signal(previous: float, current: float) -> int:
    """Entrada do RSI na zona extrema, espelhando a regra do Bollinger."""
    if pd.isna(previous) or pd.isna(current):
        return 0
    if previous >= RSI_OVERSOLD and current < RSI_OVERSOLD:
        return 1
    if previous <= RSI_OVERBOUGHT and current > RSI_OVERBOUGHT:
        return -1
    return 0


def aggregate(signals: Mapping[str, int]) -> int:
    """``score = SMA + BB + RSI + MACD`` com pesos iguais; o sinal é o voto.

    Maioria 3/4 seria estruturalmente inadequada: cada família só vale ±1 no
    dia do próprio cruzamento, e exigir três eventos raros na mesma sessão e
    na mesma direção transformaria o controle em caixa permanente.
    """
    score = sum(signals.values())
    return (score > 0) - (score < 0)


class IndicatorFamilyControlParticipant(SignalParticipant):
    """Participante do indicator-family-matched classical control.

    Herda de ``SignalParticipant`` o sizing e o contrato causal dos
    benchmarks clássicos: +1 -> alvo 1.0, -1 -> alvo 0.0, 0 -> mantém o alvo,
    com indicadores recalculados sobre o histórico truncado em ``t``.

    ponytail: quatro famílias recalculadas por sessão, O(n) por passo, como os
    demais participantes de sinal.
    """

    def __init__(self, ticker: str) -> None:
        super().__init__(ticker)
        # Reuso literal das regras de cruzamento dos benchmarks secundários.
        self._sma = SMACrossParticipant(ticker, SMA_FAST, SMA_SLOW)
        self._bollinger = BollingerParticipant(ticker, BB_WINDOW, BB_K)

    def family_signals(self, close: pd.Series) -> dict[str, int]:
        """Sinal -1/0/+1 de cada família, só com informação até ``t``."""
        signals = {
            "sma": self._sma._signal(close),
            "bollinger": self._bollinger._signal(close),
            "rsi": 0,
            "macd": 0,
        }
        if len(close) < 2:
            return signals
        rsi_values = rsi(close, RSI_PERIOD)
        macd_line, signal_line, _ = macd(close, MACD_FAST, MACD_SLOW, MACD_SIGNAL)
        signals["rsi"] = rsi_entry_signal(rsi_values.iloc[-2], rsi_values.iloc[-1])
        signals["macd"] = crossing_signal(
            macd_line.iloc[-2],
            signal_line.iloc[-2],
            macd_line.iloc[-1],
            signal_line.iloc[-1],
        )
        return signals

    def _signal(self, close: pd.Series) -> int:
        return aggregate(self.family_signals(close))
