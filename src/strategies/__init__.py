"""Estratégias de investimento clássicas.

Cada estratégia implementa a interface ``Strategy`` com o método
``generate_signals(data) → pd.Series`` que retorna -1, 0, ou 1.
"""

from src.strategies.base import SignalParticipant, Strategy
from src.strategies.bollinger_bands import (
    BollingerBandsStrategy,
    BollingerParticipant,
)
from src.strategies.buy_and_hold import BuyAndHold, BuyAndHoldParticipant
from src.strategies.equal_weight import EqualWeight
from src.strategies.min_variance import MinVariance
from src.strategies.sma_cross import SMACross, SMACrossParticipant

__all__ = [
    "SignalParticipant",
    "Strategy",
    "BuyAndHold",
    "BuyAndHoldParticipant",
    "EqualWeight",
    "SMACross",
    "BollingerBandsStrategy",
    "BollingerParticipant",
    "MinVariance",
    "SMACrossParticipant",
]
