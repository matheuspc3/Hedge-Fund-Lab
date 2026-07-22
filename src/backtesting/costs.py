"""Modelo de custos de transação."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CostModel:
    """Modelo de custos de transação financeira.

    Attributes:
        brokerage_fixed: Corretagem fixa por ordem (R$). Padrão 0.
        spread_bps: Spread em basis points (1 bps = 0.01%). Padrão 0.
        tax_rate: Alíquota de impostos/emolumentos (decimal). Padrão 0.
    """

    brokerage_fixed: float = 0.0
    spread_bps: float = 0.0
    tax_rate: float = 0.0

    def __post_init__(self):
        if self.brokerage_fixed < 0:
            raise ValueError(f"brokerage_fixed must be >= 0, got {self.brokerage_fixed}")
        if self.spread_bps < 0:
            raise ValueError(f"spread_bps must be >= 0, got {self.spread_bps}")
        if self.tax_rate < 0:
            raise ValueError(f"tax_rate must be >= 0, got {self.tax_rate}")
        if self.brokerage_fixed > 0 or self.spread_bps > 0 or self.tax_rate > 0:
            logger.info(
                "CostModel criado: brokerage=%.2f spread=%.1fbps tax=%.4f",
                self.brokerage_fixed,
                self.spread_bps,
                self.tax_rate,
            )

    def _apply(self, trade_value: float) -> float:
        """Calcula o custo total de uma transação.

        Args:
            trade_value: Valor financeiro da transação (R$).

        Returns:
            Custo total em R$.

        Raises:
            ValueError: Se trade_value < 0.
        """
        if trade_value < 0:
            raise ValueError(f"trade_value must be >= 0, got {trade_value}")
        spread_cost = trade_value * (self.spread_bps / 10_000)
        tax_cost = trade_value * self.tax_rate
        return self.brokerage_fixed + spread_cost + tax_cost

    def apply_buy(self, trade_value: float) -> float:
        """Retorna o custo total de uma compra."""
        return self._apply(trade_value)

    def apply_sell(self, trade_value: float) -> float:
        """Retorna o custo total de uma venda."""
        return self._apply(trade_value)
