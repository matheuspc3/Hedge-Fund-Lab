"""Módulo de indicadores técnicos — funções puras.

Cada indicador é uma função pura: recebe uma série pandas e retorna
a(s) série(s) calculada(s). Sem estado, sem IO, sem efeitos colaterais.
"""

from src.indicators.sma import sma
from src.indicators.bollinger import bollinger_bands
from src.indicators.rsi import rsi
from src.indicators.macd import macd

__all__ = ["sma", "bollinger_bands", "rsi", "macd"]
