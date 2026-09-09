"""Motor de backtesting multi-ativo com gestão de portfólio.

Gerencia uma carteira de N ativos com pesos determinados por uma
:class:`PortfolioStrategy`, executando rebalanceamentos periódicos e
registrando a evolução patrimonial, alocação histórica e trades.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date as Date

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.backtesting.costs import CostModel

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Estratégia de Portfólio (interface abstrata)
# ═══════════════════════════════════════════════════════════════════


class PortfolioStrategy(ABC):
    """Estratégia multi-ativo que retorna pesos alvo para cada ticker.

    A cada rebalanceamento, o motor de portfólio consulta
    ``get_weights(data, current_date)`` para obter os pesos
    desejados e ajusta as posições.
    """

    @abstractmethod
    def get_weights(
        self,
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
    ) -> dict[str, float]:
        """Retorna pesos {ticker: weight} para rebalanceamento.

        Args:
            data: Histórico observável de cada ticker até ``current_date``.
            current_date: Data atual do rebalanceamento.

        Returns:
            Dict com pesos por ticker (devem somar 1.0).
        """
        ...

    @abstractmethod
    def get_name(self) -> str: ...


# ═══════════════════════════════════════════════════════════════════
# Equal Weight
# ═══════════════════════════════════════════════════════════════════


class EqualWeightPortfolio(PortfolioStrategy):
    """Distribui o capital igualmente entre todos os ativos.

    Attributes:
        rebalance_freq: Frequência de rebalanceamento em dias (default 63).
            Usado pelo motor, não pela estratégia em si.
    """

    def __init__(self, rebalance_freq: int = 63):
        self.rebalance_freq = rebalance_freq
        logger.info("EqualWeightPortfolio criada: rebalance_freq=%d", rebalance_freq)

    def get_weights(
        self,
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
    ) -> dict[str, float]:
        n = len(data)
        if n == 0:
            return {}
        w = 1.0 / n
        result = {ticker: w for ticker in data}
        logger.debug(
            "EqualWeight em %s: %d ativos, peso=%.4f cada",
            current_date.date(),
            n,
            w,
        )
        return result

    def get_name(self) -> str:
        return "Equal Weight (Portfólio)"


# ═══════════════════════════════════════════════════════════════════
# Mínima Variância (multi-ativo)
# ═══════════════════════════════════════════════════════════════════


class MinVariancePortfolio(PortfolioStrategy):
    """Minimiza a variância do portfólio usando a matriz de covariância
    histórica dos retornos dos ativos.

    Attributes:
        window: Janela histórica em dias para estimar covariância (default 252).
        allow_short: Se True, permite pesos negativos (default False).
    """

    def __init__(self, window: int = 252, allow_short: bool = False):
        self.window = window
        self.allow_short = allow_short
        logger.info(
            "MinVariancePortfolio criada: window=%d allow_short=%s",
            window,
            allow_short,
        )

    def get_weights(
        self,
        data: dict[str, pd.DataFrame],
        current_date: pd.Timestamp,
    ) -> dict[str, float]:
        tickers = sorted(data.keys())
        n = len(tickers)

        # Se houver menos de 2 ativos, pesos iguais
        if n < 2:
            return {t: 1.0 for t in tickers}

        # Monta DataFrame de retornos diários até a data atual
        returns_list = []
        valid_tickers = []
        for t in tickers:
            df = data[t]
            close = df["fechamento"].loc[:current_date]
            if len(close) < self.window + 1:
                logger.debug(
                    "MinVariance: %s possui apenas %d dias (< window=%d) — pulando",
                    t,
                    len(close),
                    self.window,
                )
                continue
            ret = close.pct_change().dropna()
            returns_list.append(ret)
            valid_tickers.append(t)

        # Se nenhum ativo válido, fallback para equal weight
        if not valid_tickers or len(valid_tickers) < 2:
            logger.warning(
                "MinVariance: dados insuficientes em %s — fallback equal weight",
                current_date.date(),
            )
            return {t: 1.0 / n for t in tickers}

        returns_df = pd.concat(returns_list, axis=1, keys=valid_tickers).dropna()

        # Últimos N dias úteis
        recent = returns_df.iloc[-min(self.window, len(returns_df)) :]
        cov = recent.cov().values
        m = cov.shape[0]

        # Otimização: minimizar w^T Σ w
        bounds = [(0.0, 1.0)] * m if not self.allow_short else [(None, None)] * m

        def portfolio_var(w: np.ndarray) -> float:
            return w.T @ cov @ w

        constraints = {"type": "eq", "fun": lambda w: w.sum() - 1.0}
        initial = np.array([1.0 / m] * m)

        result = minimize(
            portfolio_var,
            initial,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if not result.success:
            logger.warning(
                "MinVariance: otimização não convergiu em %s — %s",
                current_date.date(),
                result.message,
            )
            return {t: 1.0 / n for t in tickers}

        # Expande pesos para todos os tickers (0.0 nos excluídos)
        opt_weights = {t: float(result.x[i]) for i, t in enumerate(valid_tickers)}
        for t in tickers:
            if t not in opt_weights:
                opt_weights[t] = 0.0

        # Normaliza para somar 1.0 (por causa de ativos excluídos)
        total = sum(opt_weights.values())
        if total > 0:
            opt_weights = {t: w / total for t, w in opt_weights.items()}

        logger.debug(
            "MinVariance em %s: pesos=%s",
            current_date.date(),
            {t: f"{w:.3f}" for t, w in opt_weights.items() if w > 0.01},
        )
        return opt_weights

    def get_name(self) -> str:
        short_str = "s" if self.allow_short else "n"
        return f"Mínima Variância ({self.window},{short_str})"


# ═══════════════════════════════════════════════════════════════════
# Resultado do Backtest Multi-Ativo
# ═══════════════════════════════════════════════════════════════════


@dataclass
class PortfolioBacktestResult:
    """Resultado completo de um backtest multi-ativo.

    Attributes:
        equity_curve: Série temporal do patrimônio líquido total.
        weights_history: DataFrame (dates x tickers) com os pesos
            efetivos *após* cada rebalanceamento.
        allocation_history: DataFrame (dates x tickers) com o valor
            financeiro alocado em cada ativo.
        trades: Lista de trades executados.
        initial_capital: Capital inicial (R$).
        final_equity: Patrimônio líquido final (R$).
    """

    equity_curve: pd.Series
    weights_history: pd.DataFrame
    allocation_history: pd.DataFrame
    trades: list = field(default_factory=list)
    initial_capital: float = 0.0
    final_equity: float = 0.0

    @property
    def returns(self) -> pd.Series:
        """Retornos diários da curva de equity."""
        return self.equity_curve.pct_change().dropna()


# ═══════════════════════════════════════════════════════════════════
# Motor de Backtesting Multi-Ativo
# ═══════════════════════════════════════════════════════════════════


@dataclass
class PortfolioTrade:
    """Trade individual dentro de um portfólio multi-ativo.

    Attributes:
        date: Data da execução.
        ticker: Ativo negociado.
        type: "BUY" ou "SELL".
        price: Preço unitário.
        quantity: Quantidade de ações.
        cost: Custo da transação (R$).
    """

    date: Date | pd.Timestamp
    ticker: str
    type: str  # "BUY" | "SELL"
    price: float
    quantity: int
    cost: float = 0.0


class PortfolioBacktestEngine:
    """Motor de backtesting multi-ativo.

    Gerencia uma carteira de N ativos, rebalanceando conforme a
    estratégia e registrando a evolução do patrimônio.

    Attributes:
        strategy: Estratégia de portfólio (define pesos alvo).
        data: dict[ticker -> DataFrame com ``abertura`` e ``fechamento``].
        initial_capital: Capital inicial em R$.
        rebalance_freq: Dias úteis entre rebalanceamentos (default 63).
        cost_model: Modelo de custos de transação.
    """

    def __init__(
        self,
        strategy: PortfolioStrategy,
        data: dict[str, pd.DataFrame],
        initial_capital: float = 100_000.0,
        rebalance_freq: int = 63,
        cost_model: CostModel | None = None,
    ):
        if not data:
            raise ValueError("data dict cannot be empty")
        for ticker, frame in data.items():
            missing = {"abertura", "fechamento"} - set(frame.columns)
            if missing:
                raise ValueError(
                    f"data for {ticker} missing columns: {', '.join(sorted(missing))}"
                )
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be > 0, got {initial_capital}")

        self.strategy = strategy
        self.data = data
        self.initial_capital = initial_capital
        self.rebalance_freq = rebalance_freq
        self.cost_model = cost_model or CostModel()

        logger.info(
            "PortfolioBacktestEngine criada: estrategia=%s, %d ativos, "
            "capital=%.2f, rebalance=%d dias",
            strategy.get_name(),
            len(data),
            initial_capital,
            rebalance_freq,
        )

    # ── API pública ──────────────────────────────────────────────

    def run(self) -> PortfolioBacktestResult:
        """Executa o backtest multi-ativo.

        1. Alinha as datas de todos os tickers (interseção).
        2. Itera dia a dia.
        3. Calcula pesos com dados até o fechamento de ``t`` e ajusta posições
           na abertura de ``t+1``.
        4. Entre rebalanceamentos, o portfólio deriva naturalmente.

        Returns:
            PortfolioBacktestResult com equity curve, pesos e trades.
        """
        tickers = sorted(self.data.keys())

        # Alinha datas: interseção de todos os índices de data
        common_dates = self._align_dates(tickers)
        logger.info(
            "PortfolioBacktest iniciado: %d ativos, %d datas comuns, %s",
            len(tickers),
            len(common_dates),
            self.strategy.get_name(),
        )

        # Estado inicial
        cash = self.initial_capital
        positions: dict[str, int] = {t: 0 for t in tickers}

        equity_curve: list[float] = []
        weights_records: list[dict] = []
        allocation_records: list[dict] = []
        trades: list[PortfolioTrade] = []

        last_rebalance_idx = -self.rebalance_freq
        pending_weights: dict[str, float] | None = None

        for i, date in enumerate(common_dates):
            open_prices = {
                t: float(self.data[t].loc[date, "abertura"]) for t in tickers
            }
            close_prices = {
                t: float(self.data[t].loc[date, "fechamento"]) for t in tickers
            }

            if pending_weights is not None:
                total_at_open = cash + sum(
                    positions[t] * open_prices[t] for t in tickers
                )
                target_positions = {}
                for t in tickers:
                    weight = float(pending_weights.get(t, 0.0))
                    if not np.isfinite(weight) or weight < 0:
                        raise ValueError(
                            "negative or non-finite portfolio weights are not supported"
                        )
                    target_positions[t] = int(total_at_open * weight / open_prices[t])

                # Vendas primeiro liberam o caixa usado pelas compras seguintes.
                for t in tickers:
                    shares = max(0, positions[t] - target_positions[t])
                    if shares == 0:
                        continue
                    trade_value = shares * open_prices[t]
                    trade_cost = self.cost_model.apply_sell(trade_value)
                    if cash + trade_value - trade_cost < 0:
                        continue
                    cash += trade_value - trade_cost
                    positions[t] -= shares
                    trades.append(
                        PortfolioTrade(
                            date=date,
                            ticker=t,
                            type="SELL",
                            price=open_prices[t],
                            quantity=shares,
                            cost=trade_cost,
                        )
                    )

                for t in tickers:
                    requested = max(0, target_positions[t] - positions[t])
                    shares = min(
                        requested,
                        self.cost_model.max_affordable_quantity(cash, open_prices[t]),
                    )
                    if shares == 0:
                        continue
                    trade_value = shares * open_prices[t]
                    trade_cost = self.cost_model.apply_buy(trade_value)
                    cash -= trade_value + trade_cost
                    positions[t] += shares
                    trades.append(
                        PortfolioTrade(
                            date=date,
                            ticker=t,
                            type="BUY",
                            price=open_prices[t],
                            quantity=shares,
                            cost=trade_cost,
                        )
                    )

                pending_weights = None

            # Pesos decididos no fechamento atual só valem na próxima abertura.
            if i - last_rebalance_idx >= self.rebalance_freq:
                observable_data = {t: self.data[t].loc[:date] for t in tickers}
                pending_weights = self.strategy.get_weights(observable_data, date)
                last_rebalance_idx = i

            # Recalcula valor do portfólio e pesos efetivos
            positions_value = sum(positions[t] * close_prices[t] for t in tickers)
            total_value = cash + positions_value
            equity_curve.append(total_value)

            # Registra alocação e pesos
            alloc_row = {t: positions[t] * close_prices[t] for t in tickers}
            alloc_row["cash"] = cash
            allocation_records.append(alloc_row)

            total_for_weight = total_value if total_value > 0 else 1.0
            weight_row = {
                t: (positions[t] * close_prices[t]) / total_for_weight for t in tickers
            }
            weights_records.append(weight_row)

        # Constrói Series / DataFrames de resultado
        index = pd.DatetimeIndex(common_dates)
        equity_series = pd.Series(equity_curve, index=index, dtype=float)
        weights_df = pd.DataFrame(weights_records, index=index)
        alloc_df = pd.DataFrame(allocation_records, index=index)

        final_equity = equity_series.iloc[-1]

        logger.info(
            "PortfolioBacktest concluído: %.2f → %.2f (%.2f%%) | %d trades",
            self.initial_capital,
            final_equity,
            (final_equity / self.initial_capital - 1) * 100,
            len(trades),
        )

        return PortfolioBacktestResult(
            equity_curve=equity_series,
            weights_history=weights_df,
            allocation_history=alloc_df,
            trades=trades,
            initial_capital=self.initial_capital,
            final_equity=final_equity,
        )

    # ── Métodos auxiliares ───────────────────────────────────────

    def _align_dates(self, tickers: list[str]) -> list[pd.Timestamp]:
        """Encontra a interseção das datas de todos os tickers."""
        common: set | None = None
        for t in tickers:
            dates = set(self.data[t].index)
            if common is None:
                common = dates
            else:
                common &= dates
        return sorted(common) if common else []
