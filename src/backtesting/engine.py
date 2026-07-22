"""Motor principal de backtesting.

Executa uma estratégia sobre dados históricos e produz a curva de equity,
lista de trades e métricas de desempenho.
"""

import logging
from dataclasses import dataclass, field
from datetime import date as Date

import pandas as pd

from src.backtesting.costs import CostModel

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Representa uma transação executada pelo backtest.

    Attributes:
        date: Data da execução.
        type: "BUY" ou "SELL".
        price: Preço unitário do ativo.
        quantity: Quantidade de ações negociada.
        cost: Custo total da transação (R$).
    """

    date: Date | pd.Timestamp
    type: str  # "BUY" | "SELL"
    price: float
    quantity: int
    cost: float = 0.0


@dataclass
class BacktestResult:
    """Resultado completo de uma execução de backtest.

    Attributes:
        equity_curve: Série temporal do patrimônio líquido.
        trades: Lista de trades executados.
        initial_capital: Capital inicial.
        final_equity: Patrimônio líquido final.
    """

    equity_curve: pd.Series
    trades: list[Trade] = field(default_factory=list)
    initial_capital: float = 0.0
    final_equity: float = 0.0

    @property
    def returns(self) -> pd.Series:
        """Retornos diários da curva de equity."""
        return self.equity_curve.pct_change().dropna()


class BacktestEngine:
    """Motor de backtesting.

    Itera dia a dia sobre os dados históricos, gera sinais através da
    estratégia e executa trades conforme as regras.

    Attributes:
        strategy: Estratégia que gera sinais {-1, 0, 1}.
        data: DataFrame com dados históricos (coluna 'fechamento').
        initial_capital: Capital inicial em R$.
        cost_model: Modelo de custos de transação.
        allow_short: Se True, permite venda a descoberto.
    """

    def __init__(
        self,
        strategy,
        data: pd.DataFrame,
        initial_capital: float,
        cost_model: CostModel | None = None,
        allow_short: bool = False,
    ):
        if data.empty:
            raise ValueError("data cannot be empty")
        if initial_capital <= 0:
            raise ValueError(
                f"initial_capital must be > 0, got {initial_capital}"
            )

        self.strategy = strategy
        self.data = data
        self.initial_capital = initial_capital
        self.cost_model = cost_model or CostModel()
        self.allow_short = allow_short

    # ── API pública ──────────────────────────────────────────────

    def run(self) -> BacktestResult:
        """Executa o backtest.

        Pré-computa todos os sinais da estratégia de uma vez (a estratégia
        é responsável por não usar dados futuros), depois itera dia a dia
        executando trades conforme os sinais e registrando a curva de equity.

        Returns:
            BacktestResult com equity curve, trades e métricas.
        """
        cash = self.initial_capital
        position = 0  # número de ações
        trades: list[Trade] = []
        equity_curve: list[float] = []
        prices = self.data["fechamento"]

        # Pré-computa todos os sinais de uma vez
        all_signals = self.strategy.generate_signals(self.data)

        # Validação básica dos sinais
        if len(all_signals) != len(self.data):
            raise ValueError(
                f"strategy returned {len(all_signals)} signals "
                f"for {len(self.data)} data points"
            )

        # Estado anterior para evitar trades repetidos
        last_signal = 0

        logger.info(
            "Backtest iniciado: capital=%.2f, %d dias, estrategia=%s",
            self.initial_capital,
            len(self.data),
            self.strategy.get_name() if hasattr(self.strategy, "get_name") else "?",
        )

        for t in range(len(self.data)):
            current_price = float(prices.iloc[t])
            current_signal = int(all_signals.iloc[t])

            # Executa trade se o sinal mudou
            if current_signal != last_signal:
                if current_signal == 1 and position == 0:
                    # COMPRA: converte todo cash em ações
                    trade_cost = self.cost_model.apply_buy(current_price)
                    quantity = int(cash / current_price)
                    if quantity > 0:
                        cash -= quantity * current_price + trade_cost
                        position += quantity
                        trades.append(Trade(
                            date=self.data.index[t],
                            type="BUY",
                            price=current_price,
                            quantity=quantity,
                            cost=trade_cost,
                        ))
                        logger.debug(
                            "BUY %d x %.2f = %.2f (custo=%.2f) cash=%.2f",
                            quantity, current_price, quantity * current_price,
                            trade_cost, cash,
                        )

                elif current_signal == -1 and position > 0:
                    # VENDA: vende todas as ações
                    trade_value = position * current_price
                    trade_cost = self.cost_model.apply_sell(trade_value)
                    cash += trade_value - trade_cost
                    trades.append(Trade(
                        date=self.data.index[t],
                        type="SELL",
                        price=current_price,
                        quantity=position,
                        cost=trade_cost,
                    ))
                    logger.debug(
                        "SELL %d x %.2f = %.2f (custo=%.2f) cash=%.2f",
                        position, current_price, trade_value,
                        trade_cost, cash,
                    )
                    position = 0

                elif current_signal == -1 and position == 0 and self.allow_short:
                    # Venda a descoberto (se permitido)
                    quantity = int(cash / current_price)
                    if quantity > 0:
                        trade_cost = self.cost_model.apply_sell(current_price)
                        cash += quantity * current_price - trade_cost
                        position -= quantity
                        trades.append(Trade(
                            date=self.data.index[t],
                            type="SELL",
                            price=current_price,
                            quantity=quantity,
                            cost=trade_cost,
                        ))

                last_signal = current_signal

            # Registra equity (patrimônio líquido atual)
            equity = cash + position * current_price
            equity_curve.append(equity)

        # Constrói equity_curve como pd.Series
        equity_series = pd.Series(equity_curve, index=self.data.index, dtype=float)
        final_equity = equity_series.iloc[-1]

        logger.info(
            "Backtest concluído: %.2f → %.2f (%.2f%%) | %d trades | custos=%s",
            self.initial_capital,
            final_equity,
            (final_equity / self.initial_capital - 1) * 100,
            len(trades),
            type(self.cost_model).__name__,
        )

        return BacktestResult(
            equity_curve=equity_series,
            trades=trades,
            initial_capital=self.initial_capital,
            final_equity=final_equity,
        )
