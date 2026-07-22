"""Interface abstrata para estratégias de investimento."""

from abc import ABC, abstractmethod

import pandas as pd


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
