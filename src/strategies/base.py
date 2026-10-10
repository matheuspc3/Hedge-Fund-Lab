"""Interfaces abstratas de estratégias e de participantes single-asset."""

from abc import ABC, abstractmethod
from typing import cast

import pandas as pd

from src.backtesting.arena import MarketObservation, OrderIntent


class Strategy(ABC):
    """Interface base para todas as estratégias de investimento.

    Toda estratégia concreta deve implementar:
        - ``generate_signals(data)`` → pd.Series com valores em {-1, 0, 1}
        - ``get_name()`` → str com o nome da estratégia

    Convenção de sinais:
        - 1  = COMPRAR (entrar ou aumentar posição)
        - -1 = VENDER (sair ou reduzir posição)
        - 0  = MANTER (não alterar posição)
    """

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Gera sinais de trading com base nos dados fornecidos.

        Args:
            data: DataFrame com dados históricos. Deve conter ao menos
                  a coluna ``fechamento`` (e indicadores conforme a estratégia).

        Returns:
            pd.Series com mesma indexação de *data* e valores em {-1, 0, 1}.

        Raises:
            ValueError: Se os dados não tiverem as colunas necessárias.
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Retorna o nome legível da estratégia."""
        ...


class SignalParticipant(ABC):
    """Participante single-asset que alterna entre 100% investido e caixa.

    O sinal é recalculado a cada observação usando apenas o histórico já
    truncado em ``t``; a arena nunca entrega o DataFrame completo. O peso alvo
    só vira intenção quando muda, portanto uma posição mantida não gera trade
    repetido. Long-only: não existe peso negativo nem alavancagem.

    Uma instância acompanha uma execução: o peso alvo é reiniciado quando a
    observação mostra a primeira sessão do recorte.
    """

    def __init__(self, ticker: str) -> None:
        if not ticker.strip():
            raise ValueError("ticker cannot be empty")
        self.ticker = ticker.strip()
        self._target_weight = 0.0
        self._last_session: pd.Timestamp | None = None

    @abstractmethod
    def _signal(self, close: pd.Series) -> int:
        """Retorna 1 (entrar), -1 (sair) ou 0 (manter) a partir de ``close`` até ``t``."""
        ...

    def decide(self, observation: MarketObservation) -> list[OrderIntent]:
        history = observation.history.get(self.ticker)
        if history is None:
            raise ValueError(f"observation missing ticker: {self.ticker}")
        # Início de execução pelo relógio de sessões, não por ``len(history)``:
        # com janela avaliada a primeira decisão já observa o warm-up inteiro,
        # e o tamanho do histórico deixaria a carteira-alvo herdada de um run
        # anterior. A posição nasce zerada em ``decision_start``.
        previous = self._last_session
        self._last_session = observation.session
        if previous is None or observation.session <= previous:
            self._target_weight = 0.0

        signal = self._signal(cast(pd.Series, history["fechamento"]))
        target = {1: 1.0, -1: 0.0}.get(signal, self._target_weight)
        if target == self._target_weight:
            return []
        self._target_weight = target
        return [
            OrderIntent(
                ticker=self.ticker,
                target_weight=target,
                decision_time=observation.session,
            )
        ]
