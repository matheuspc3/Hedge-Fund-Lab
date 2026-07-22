"""Gera data.json para o dashboard usando o banco como fonte primária.

Uso:
    python scripts/generate_dashboard_data.py

Fluxo:
  1. Verifica se o banco tem dados dos 10 tickers
  2. Se não, executa o pipeline ETL (que baixa e salva no banco)
  3. Lê cotações + indicadores do banco via SQLAlchemy
  4. Calcula indicadores que faltarem
  5. Roda backtests single-asset em TODOS os tickers (agregado)
  6. Roda backtests de portfólio multi-ativo
  7. Salva dashboard/data.json com curvas de drawdown e scatter data
"""

import json
import logging
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TICKER_INFO, settings
from src.logger import setup_logger
from src.db.connection import engine, get_session
from src.db.models import Ativo, CotacaoDiaria, IndicadorTecnico
from src.pipeline.transform import DataTransformer

setup_logger(level="INFO", log_file=settings.log_file)
logger = logging.getLogger("generate_dashboard_data")

# ── Timer helper ────────────────────────────────────────────────
_t_start: float | None = None


def _log_tick(label: str) -> None:
    """Loga elapsed time desde o último tick (ou início)."""
    global _t_start
    now = time.perf_counter()
    if _t_start is None:
        _t_start = now
        logger.info("⏱  %s", label)
    else:
        elapsed = now - _t_start
        if elapsed < 60:
            logger.info("⏱  %s  [%ds]", label, round(elapsed))
        else:
            logger.info("⏱  %s  [%dm %ds]", label, int(elapsed // 60), round(elapsed % 60))
        _t_start = now


def sanitize(v):
    """Converte NaN/Inf para None para serialização JSON."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def check_db_has_data() -> bool:
    """Verifica se o banco possui dados para todos os tickers de settings."""
    try:
        with get_session() as session:
            tickers_no_db = session.query(Ativo.ticker).all()
            tickers_no_db = {r[0] for r in tickers_no_db}
            expected = set(settings.default_tickers)
            missing = expected - tickers_no_db
            if missing:
                logger.info("Tickers faltando no banco: %s", sorted(missing))
                return False

            problems: list[str] = []
            for ticker in expected:
                ativo = session.query(Ativo).filter(Ativo.ticker == ticker).first()
                if ativo is None:
                    problems.append(f"{ticker}: ativo não encontrado")
                    continue
                count = session.query(CotacaoDiaria).filter(
                    CotacaoDiaria.ativo_id == ativo.id
                ).count()
                if count < 100:
                    problems.append(f"{ticker}: apenas {count} registros (< 100)")

            if problems:
                for p in problems:
                    logger.info("  Problema: %s", p)
                return False

            logger.info("Banco com dados completos para %d tickers", len(expected))
            return True
    except Exception as exc:
        logger.warning("Erro ao verificar banco: %s", exc, exc_info=True)
        return False


def run_pipeline_etl() -> None:
    """Executa o pipeline ETL para popular o banco."""
    logger.info("=" * 50)
    logger.info("Executando pipeline ETL para popular o banco...")
    logger.info("=" * 50)

    from src.db.models import Base
    Base.metadata.create_all(engine)

    from src.pipeline.extract import DataExtractor
    from src.pipeline.load import DataLoader

    extractor = DataExtractor()
    transformer = DataTransformer()
    loader = DataLoader(get_session)

    n_ok = 0
    n_fail = 0
    failed_tickers: list[str] = []
    for i, ticker in enumerate(settings.default_tickers, 1):
        logger.info("[%d/%d] Processando %s...", i, len(settings.default_tickers), ticker)
        t0 = time.perf_counter()
        try:
            df = extractor.download(ticker, settings.start_date, settings.end_date)
            df_clean = transformer.clean(df)
            df_result = transformer.calculate_indicators(df_clean)

            cotacoes_cols = ["data", "abertura", "maxima", "minima", "fechamento", "volume"]
            indicadores_cols = [
                "data", "sma_50", "sma_200", "bb_upper", "bb_middle",
                "bb_lower", "rsi", "macd", "macd_sinal",
            ]

            cotacoes_to_insert = df_result[[c for c in cotacoes_cols if c in df_result.columns]]
            indicadores_to_insert = df_result[[c for c in indicadores_cols if c in df_result.columns]]

            loader.upsert_cotacoes(ticker, cotacoes_to_insert)
            loader.batch_insert_indicators(ticker, indicadores_to_insert)

            elapsed = time.perf_counter() - t0
            logger.info("[%d/%d] %s concluído — %d registros em %.1fs",
                        i, len(settings.default_tickers), ticker, len(df_result), elapsed)
            n_ok += 1
        except Exception as exc:
            elapsed = time.perf_counter() - t0
            logger.error("[%d/%d] %s FALHOU após %.1fs: %s",
                         i, len(settings.default_tickers), ticker, elapsed, exc)
            n_fail += 1
            failed_tickers.append(ticker)

    if n_fail:
        logger.warning("Pipeline ETL finalizado com falhas. OK=%d  FALHA=%d  Fail: %s",
                       n_ok, n_fail, ", ".join(failed_tickers))
    else:
        logger.info("Pipeline ETL finalizado com sucesso. %d ticker(s) processados.", n_ok)


def read_ticker_from_db(ticker: str) -> pd.DataFrame | None:
    """Lê cotações + indicadores de um ticker do banco como DataFrame."""
    try:
        with get_session() as session:
            ativo = session.query(Ativo).filter(Ativo.ticker == ticker).first()
            if ativo is None:
                logger.warning("Ticker %s não encontrado no banco", ticker)
                return None

            cots = (
                session.query(CotacaoDiaria)
                .filter(CotacaoDiaria.ativo_id == ativo.id)
                .order_by(CotacaoDiaria.data)
                .all()
            )
            if not cots:
                logger.warning("Nenhuma cotação para %s", ticker)
                return None

            rows = []
            for c in cots:
                rows.append({
                    "data": c.data,
                    "fechamento": c.fechamento,
                    "abertura": c.abertura,
                    "maxima": c.maxima,
                    "minima": c.minima,
                    "volume": c.volume,
                })

            df = pd.DataFrame(rows).set_index("data")
            df.index = pd.DatetimeIndex(df.index)
            df.sort_index(inplace=True)

            dup_count = df.index.duplicated(keep="last").sum()
            if dup_count:
                logger.info("  %s: removendo %d linhas duplicadas", ticker, dup_count)
                df = df[~df.index.duplicated(keep="last")]

            inds = (
                session.query(IndicadorTecnico)
                .filter(IndicadorTecnico.ativo_id == ativo.id)
                .order_by(IndicadorTecnico.data)
                .all()
            )
            if inds:
                ind_rows = []
                for ind in inds:
                    ind_rows.append({
                        "data": ind.data,
                        "sma_50": ind.sma_50,
                        "sma_200": ind.sma_200,
                        "bb_upper": ind.bb_upper,
                        "bb_middle": ind.bb_middle,
                        "bb_lower": ind.bb_lower,
                        "rsi": ind.rsi,
                        "macd": ind.macd,
                        "macd_sinal": ind.macd_sinal,
                    })
                df_inds = pd.DataFrame(ind_rows).set_index("data")
                df_inds.index = pd.DatetimeIndex(df_inds.index)
                dup_ind = df_inds.index.duplicated(keep="last").sum()
                if dup_ind:
                    df_inds = df_inds[~df_inds.index.duplicated(keep="last")]
                df = df.join(df_inds)

            transformer = DataTransformer()
            has_indicators = "sma_50" in df.columns and df["sma_50"].notna().any()
            if not has_indicators:
                logger.info("  %s: calculando indicadores (SMA, BB, RSI, MACD)...", ticker)
                df = transformer.calculate_indicators(df)
            else:
                logger.info("  %s: indicadores já existentes no banco", ticker)

            # Loga período
            logger.info("  %s: período %s → %s  (%d pregões)",
                        ticker, df.index[0].date(), df.index[-1].date(), len(df))
            return df

    except Exception as exc:
        logger.error("Erro ao ler %s do banco: %s", ticker, exc)
        return None


def ticker_to_json(ticker: str, df: pd.DataFrame) -> dict | None:
    """Converte DataFrame de um ticker para formato JSON do dashboard."""
    if df is None or df.empty:
        return None

    records = []
    for date, row in df.iterrows():
        fech = sanitize(row.get("fechamento"))
        if fech is None:
            continue
        rec = {
            "Data": str(date.date()),
            "fechamento": fech,
            "abertura": sanitize(row.get("abertura")),
            "maxima": sanitize(row.get("maxima")),
            "minima": sanitize(row.get("minima")),
            "volume": int(row.get("volume")) if row.get("volume") is not None and not (isinstance(row.get("volume"), float) and math.isnan(row["volume"])) else None,
            "sma_50": sanitize(row.get("sma_50")),
            "sma_200": sanitize(row.get("sma_200")),
            "bb_upper": sanitize(row.get("bb_upper")),
            "bb_middle": sanitize(row.get("bb_middle")),
            "bb_lower": sanitize(row.get("bb_lower")),
            "rsi": sanitize(row.get("rsi")),
            "macd": sanitize(row.get("macd")),
            "macd_sinal": sanitize(row.get("macd_sinal")),
            "macd_hist": sanitize(row.get("macd_hist")),
        }
        records.append(rec)

    if not records:
        logger.warning("  %s: nenhum registro com fechamento válido após sanitização", ticker)
        return None

    ultimo = records[-1].copy()
    info = TICKER_INFO.get(ticker, {})

    return {
        "ticker": ticker,
        "nome": info.get("nome", ticker),
        "setor": info.get("setor", "—"),
        "data": records,
        "ultimo": ultimo,
        "total_dias": len(records),
        "periodo": {"inicio": settings.start_date, "fim": settings.end_date},
    }


def compute_metrics(equity_curve: pd.Series, rf: float = 0.0) -> dict:
    """Calcula métricas de uma série de equity."""
    if len(equity_curve) < 2:
        return {
            "sharpe": None, "sortino": None, "max_drawdown": None,
            "volatilidade": None, "retorno_acumulado": None, "retorno_percent": None,
        }

    rets = equity_curve.pct_change().dropna()
    if len(rets) == 0:
        return {
            "sharpe": None, "sortino": None, "max_drawdown": None,
            "volatilidade": None,
            "retorno_acumulado": float(equity_curve.iloc[-1] - equity_curve.iloc[0]),
            "retorno_percent": None,
        }

    mean_ret = rets.mean()
    vol = rets.std()
    annual_vol = vol * math.sqrt(252)
    annual_ret = mean_ret * 252
    sharpe = (annual_ret - rf) / annual_vol if annual_vol > 1e-15 else (0.0 if abs(annual_ret - rf) < 1e-10 else None)

    downside = rets[rets < 0]
    downside_vol = downside.std() * math.sqrt(252) if len(downside) > 0 else 0.0
    sortino = (annual_ret - rf) / downside_vol if downside_vol > 1e-15 else (
        0.0 if abs(annual_ret - rf) < 1e-10 else None
    )

    peak = equity_curve.expanding().max()
    dd = (equity_curve - peak) / peak
    max_dd = dd.min()

    retorno_pct = float((equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100)

    return {
        "sharpe": round(sharpe, 4) if sharpe is not None else None,
        "sortino": round(sortino, 4) if sortino is not None else None,
        "max_drawdown": round(float(max_dd), 6),
        "volatilidade": round(float(annual_vol * 100), 2),
        "retorno_acumulado": round(retorno_pct, 2),
        "retorno_percent": round(retorno_pct, 2),
    }


# ── Helpers novos ────────────────────────────────────────────────

def _compute_drawdown_series(equity_curve: pd.Series) -> list[float]:
    """Calcula a série de drawdown a partir da curva de equity."""
    if len(equity_curve) < 2:
        return [0.0] * len(equity_curve)
    peak = equity_curve.expanding().max()
    dd = (equity_curve - peak) / peak
    return [round(float(v), 6) for v in dd]


def _aggregate_ticker_metrics(metrics_list: list[dict]) -> tuple[dict, dict]:
    """Calcula média e desvio padrão das métricas entre tickers."""
    keys = ["sharpe", "sortino", "max_drawdown", "retorno_percent", "volatilidade", "n_trades"]
    avg_m = {}
    std_m = {}
    for key in keys:
        vals = [m[key] for m in metrics_list if m[key] is not None and not (isinstance(m[key], float) and (math.isnan(m[key]) or math.isinf(m[key])))]
        if vals:
            avg_m[key] = round(float(pd.Series(vals).mean()), 4)
            std_m[key] = round(float(pd.Series(vals).std()), 4)
        else:
            avg_m[key] = None
            std_m[key] = None
    return avg_m, std_m


# ── Format helpers (log) ─────────────────────────────────────────

def _fmt(v):
    return f"{v:.4f}" if v is not None else "N/A"

def _fmt_ret(v):
    return f"{v:.2f}" if v is not None else "N/A"

def _fmt_dd(v):
    if v is None:
        return "N/A"
    return f"{v * 100:.2f}"


# ── Backtests ────────────────────────────────────────────────────

def run_single_asset_backtests(all_data: dict[str, pd.DataFrame],
                                tickers: list[str]) -> dict[str, dict]:
    """Roda backtests single-asset em TODOS os tickers e agrega.

    Para cada estratégia, executa o backtest em cada ticker individualmente,
    alinha as curvas de equity pela interseção das datas e calcula a média.

    Returns:
        Dict::
            {nome_estrategia: {
                "metrics": {...},         # métricas da curva média
                "equity": [...],          # curva de equity média
                "dates": [...],
                "drawdown": [...],        # série de drawdown da curva média
                "avg_ticker_metrics": {...},  # média das métricas individuais
                "std_ticker_metrics": {...},  # desvio padrão
                "per_ticker": {ticker: {     # métricas por ticker
                    "metrics": {...}
                }}
            }}
    """
    from src.backtesting.engine import BacktestEngine
    from src.backtesting.metrics import max_drawdown, sharpe_ratio, sortino_ratio
    from src.strategies.bollinger_bands import BollingerBandsStrategy
    from src.strategies.buy_and_hold import BuyAndHold
    from src.strategies.sma_cross import SMACross

    capital = 100_000.0
    strategies = {
        "Buy & Hold": BuyAndHold(),
        "SMA Cross (50/200)": SMACross(fast_window=50, slow_window=200),
        "Bollinger Bands (20,2)": BollingerBandsStrategy(window=20, k=2.0),
    }

    # per_ticker[strategy_name][ticker] = BacktestResult
    per_ticker: dict[str, dict] = {}

    for ticker in tickers:
        df = all_data[ticker]
        for name, strat in strategies.items():
            engine = BacktestEngine(strat, df, capital)
            result = engine.run()
            per_ticker.setdefault(name, {})[ticker] = result

    # Agrega resultados por estratégia
    results = {}
    for name, ticker_results in per_ticker.items():
        # Alinha curvas de equity pela interseção das datas
        curves = {t: r.equity_curve for t, r in ticker_results.items()}
        df_curves = pd.DataFrame(curves)
        avg_eq = df_curves.mean(axis=1)

        # Métricas da curva média
        avg_rets = avg_eq.pct_change().dropna()
        avg_sharpe = round(float(sharpe_ratio(avg_rets)), 4) if len(avg_rets) > 0 else None
        avg_sortino = round(float(sortino_ratio(avg_rets)), 4) if len(avg_rets) > 0 else None
        avg_dd = round(float(max_drawdown(avg_eq)), 6)
        avg_ret = round(float((avg_eq.iloc[-1] / avg_eq.iloc[0] - 1) * 100), 2)

        # Métricas por ticker
        ticker_metrics = {}
        metrics_list = []
        for ticker, result in ticker_results.items():
            eq = result.equity_curve
            rets = result.returns
            vol = round(float(rets.std() * math.sqrt(252) * 100), 2) if len(rets) > 0 else None
            m = {
                "sharpe": round(float(sharpe_ratio(rets)), 4),
                "sortino": round(float(sortino_ratio(rets)), 4),
                "max_drawdown": round(float(max_drawdown(eq)), 6),
                "retorno_percent": round(float((result.final_equity / result.initial_capital - 1) * 100), 2),
                "final_equity": round(float(result.final_equity), 2),
                "n_trades": len(result.trades),
                "volatilidade": vol,
            }
            ticker_metrics[ticker] = m
            metrics_list.append(m)

        avg_m, std_m = _aggregate_ticker_metrics(metrics_list)

        # ── Log do resultado agregado ─────────────────────────────
        logger.info("  ▌ %s", "─" * 55)
        logger.info("  ▌ Estratégia: %s", name)
        logger.info("  ▌   Sharpe médio     = %s", _fmt(avg_m.get("sharpe")))
        logger.info("  ▌   Sortino médio     = %s", _fmt(avg_m.get("sortino")))
        logger.info("  ▌   Retorno médio     = %s%%", _fmt_ret(avg_m.get("retorno_percent")))
        logger.info("  ▌   Drawdown médio    = %s%%", _fmt_dd(avg_m.get("max_drawdown")))
        logger.info("  ▌   Volatilidade méd  = %s%%", _fmt(avg_m.get("volatilidade")))
        logger.info("  ▌   Trades (total)    = %s", sum(m["n_trades"] for m in metrics_list))
        logger.info("  ▌   Tickers           = %s", ", ".join(sorted(ticker_results.keys())))
        logger.info("  ▌ %s", "─" * 55)

        results[name] = {
            "metrics": {
                "sharpe": avg_sharpe,
                "sortino": avg_sortino,
                "max_drawdown": avg_dd,
                "retorno_percent": avg_ret,
                "final_equity": round(float(avg_eq.iloc[-1]), 2),
                "n_trades": sum(m["n_trades"] for m in metrics_list),
            },
            "equity": [round(float(v), 2) for v in avg_eq.values],
            "dates": [str(d.date()) for d in avg_eq.index],
            "drawdown": _compute_drawdown_series(avg_eq),
            "avg_ticker_metrics": avg_m,
            "std_ticker_metrics": std_m,
            "per_ticker": ticker_metrics,
        }

    return results


def run_portfolio_backtests(all_data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Roda backtests multi-ativo (Equal Weight, Min Variance)."""
    from src.backtesting.metrics import max_drawdown, sharpe_ratio, sortino_ratio
    from src.backtesting.portfolio import (
        EqualWeightPortfolio, MinVariancePortfolio, PortfolioBacktestEngine,
    )

    capital = 100_000.0
    strategies = {
        "Equal Weight": EqualWeightPortfolio(rebalance_freq=63),
        "Min Variance": MinVariancePortfolio(window=252, allow_short=False),
    }

    results = {}
    for name, strat in strategies.items():
        logger.info("  ▌ %s", "─" * 55)
        logger.info("  ▌ Portfolio: %s", name)
        t0 = time.perf_counter()

        engine = PortfolioBacktestEngine(strat, all_data, capital, rebalance_freq=63)
        result = engine.run()

        elapsed = time.perf_counter() - t0
        eq = result.equity_curve
        rets = eq.pct_change().dropna()
        metrics = {
            "sharpe": round(float(sharpe_ratio(rets)), 4),
            "sortino": round(float(sortino_ratio(rets)), 4),
            "max_drawdown": round(float(max_drawdown(eq)), 6),
            "retorno_percent": round(float((result.final_equity / result.initial_capital - 1) * 100), 2),
            "final_equity": round(float(result.final_equity), 2),
            "n_trades": sum(1 for t in result.trades if t.type == "BUY"),
        }

        latest_weights = result.weights_history.iloc[-1].to_dict() if len(result.weights_history) > 0 else {}
        top_weights = sorted(latest_weights.items(), key=lambda x: -x[1])[:5]

        logger.info("  ▌   Sharpe        = %s", _fmt(metrics["sharpe"]))
        logger.info("  ▌   Sortino       = %s", _fmt(metrics["sortino"]))
        logger.info("  ▌   Retorno       = %s%%", metrics["retorno_percent"])
        logger.info("  ▌   Drawdown      = %s%%", _fmt_dd(metrics["max_drawdown"]))
        logger.info("  ▌   Final Equity  = R$ %.2f", metrics["final_equity"])
        logger.info("  ▌   Trades        = %s", metrics["n_trades"])
        logger.info("  ▌   Tempo         = %.1fs", elapsed)
        if top_weights:
            logger.info("  ▌   Top pesos     = %s", ", ".join(f"{t}: {w*100:.0f}%" for t, w in top_weights))
        logger.info("  ▌ %s", "─" * 55)

        results[name] = {
            "metrics": metrics,
            "equity": [round(float(v), 2) for v in eq.values],
            "dates": [str(d.date()) for d in eq.index],
            "drawdown": _compute_drawdown_series(eq),
            "latest_weights": {k: round(float(v) * 100, 1) for k, v in latest_weights.items() if v > 0.01},
        }

    return results


def build_comparison_table(single_results: dict[str, dict],
                           portfolio_results: dict[str, dict]) -> list[dict]:
    """Monta tabela comparativa de todas as estratégias.

    Single-asset agora mostra média ± desvio entre os tickers.
    Portfolio mostra suas próprias métricas.
    """
    table = []
    for strat_name, data in single_results.items():
        m = data["metrics"]
        avg = data.get("avg_ticker_metrics", {})
        std = data.get("std_ticker_metrics", {})
        table.append({
            "estrategia": strat_name,
            "tipo": "Single-Asset (média 10 ativos)",
            "sharpe": m["sharpe"],
            "sharpe_avg": avg.get("sharpe"),
            "sharpe_std": std.get("sharpe"),
            "sortino": m["sortino"],
            "max_drawdown": m["max_drawdown"],
            "retorno_percent": m["retorno_percent"],
            "retorno_avg": avg.get("retorno_percent"),
            "retorno_std": std.get("retorno_percent"),
            "n_trades": m["n_trades"],
        })
    for strat_name, data in portfolio_results.items():
        m = data["metrics"]
        table.append({
            "estrategia": strat_name,
            "tipo": "Portfólio (10 Ativos)",
            "sharpe": m["sharpe"],
            "sortino": m["sortino"],
            "max_drawdown": m["max_drawdown"],
            "retorno_percent": m["retorno_percent"],
            "n_trades": m["n_trades"],
        })
    return table


def build_scatter_data(single_results: dict[str, dict],
                       portfolio_results: dict[str, dict]) -> list[dict]:
    """Constrói dados para scatter plot risco × retorno.

    Cada estratégia gera um ponto com:
      - volatilidade (x)
      - retorno_percent (y)
      - sharpe (cor)
      - tipo (single vs portfolio)
    """
    points = []
    for strat_name, data in single_results.items():
        m = data["metrics"]
        avg = data.get("avg_ticker_metrics", {})
        points.append({
            "estrategia": strat_name,
            "tipo": "Single-Asset (média)",
            "volatilidade": avg.get("volatilidade"),
            "retorno": m["retorno_percent"],
            "sharpe": m["sharpe"],
        })
    for strat_name, data in portfolio_results.items():
        m = data["metrics"]
        points.append({
            "estrategia": strat_name,
            "tipo": "Portfólio (10 Ativos)",
            "volatilidade": round(float(m.get("retorno_percent", 0) / m.get("sharpe", 1)) if m.get("sharpe") and m.get("sharpe") != 0 else 0, 2),
            "retorno": m["retorno_percent"],
            "sharpe": m["sharpe"],
        })
    return points


def main():
    _log_tick("Início da execução")
    logger.info("%s", "=" * 60)
    logger.info("GERADOR DE DADOS DO DASHBOARD (fonte: banco)")
    logger.info("Tickers: %s", settings.default_tickers)
    logger.info("Período: %s → %s", settings.start_date, settings.end_date)
    logger.info("Banco: %s", settings.database_url)
    logger.info("%s", "=" * 60)

    # ── 1. Verifica / popula o banco ─────────────────────────────
    from src.db.models import Base
    Base.metadata.create_all(engine)

    if not check_db_has_data():
        logger.info("Banco sem dados completos — executando pipeline ETL...")
        run_pipeline_etl()
    else:
        logger.info("Banco já possui dados completos.")
    _log_tick("Banco verificado/populado")

    # ── 2. Lê dados do banco ─────────────────────────────────────
    all_data: dict[str, pd.DataFrame] = {}
    assets_json = []
    tickers_ok = []

    for ticker in settings.default_tickers:
        df = read_ticker_from_db(ticker)
        if df is not None:
            result = ticker_to_json(ticker, df)
            if result is not None:
                assets_json.append(result)
                df_dedup = df[["fechamento"]].copy()
                df_dedup = df_dedup[~df_dedup.index.duplicated(keep="last")]
                all_data[ticker] = df_dedup
                tickers_ok.append(ticker)

    if not tickers_ok:
        logger.error("Nenhum ticker com dados válidos. Abortando.")
        sys.exit(1)

    logger.info("Dados OK: %d/%d tickers (fonte: banco)", len(tickers_ok), len(settings.default_tickers))
    logger.info("Tickers OK: %s", ", ".join(tickers_ok))
    _log_tick("Dados lidos do banco")

    # ── 3. Single-asset backtests em TODOS os tickers ────────────
    logger.info("%s", "─" * 60)
    logger.info("FASE: Backtests Single-Asset (%d tickers)", len(tickers_ok))
    logger.info("%s", "─" * 60)
    single_results = run_single_asset_backtests(all_data, tickers_ok)
    _log_tick("Backtests single-asset concluídos")

    # ── 4. Portfolio backtests ───────────────────────────────────
    logger.info("%s", "─" * 60)
    logger.info("FASE: Backtests de Portfólio Multi-Ativo")
    logger.info("%s", "─" * 60)
    portfolio_results = run_portfolio_backtests(all_data)
    _log_tick("Backtests de portfólio concluídos")

    # ── 5. Tabela comparativa + scatter ──────────────────────────
    logger.info("Montando tabela comparativa e scatter plot...")
    comparison = build_comparison_table(single_results, portfolio_results)
    scatter_data = build_scatter_data(single_results, portfolio_results)
    logger.info("Comparação: %d estratégias | Scatter: %d pontos", len(comparison), len(scatter_data))
    _log_tick("Tabela e scatter montados")

    # ── 6. Monta JSON final ──────────────────────────────────────
    portfolio_output = {}
    for name, data in portfolio_results.items():
        portfolio_output[name] = {
            "equity": data["equity"], "dates": data["dates"],
            "drawdown": data.get("drawdown", []),
            "metrics": data["metrics"],
            "latest_weights": data.get("latest_weights", {}),
        }

    single_output = {}
    for name, data in single_results.items():
        single_output[name] = {
            "equity": data["equity"], "dates": data["dates"],
            "drawdown": data.get("drawdown", []),
            "metrics": data["metrics"],
        }

    # Sumário single-asset (para tabela detalhada por ticker)
    single_asset_summary = {}
    for name, data in single_results.items():
        single_asset_summary[name] = {
            "avg_metrics": data.get("avg_ticker_metrics", {}),
            "std_metrics": data.get("std_ticker_metrics", {}),
            "per_ticker": data.get("per_ticker", {}),
        }

    output = {
        "ativos": assets_json,
        "portfolio": {
            "strategies": {**portfolio_output, **single_output},
            "single_asset_summary": single_asset_summary,
            "scatter_data": scatter_data,
            "comparison": comparison,
            "n_tickers": len(tickers_ok),
        },
    }

    # ── 7. Salva ─────────────────────────────────────────────────
    output_path = Path(__file__).resolve().parent.parent / "dashboard" / "data.json"
    json_bytes = json.dumps(output, ensure_ascii=False, indent=2).encode("utf-8")
    with open(output_path, "wb") as f:
        f.write(json_bytes)

    logger.info("=" * 60)
    logger.info("ARQUIVO SALVO: %s  (%d KB)", output_path, len(json_bytes) // 1024)
    logger.info("Tickers: %d | Estratégias: %d single + %d portfólio",
                len(assets_json), len(single_output), len(portfolio_output))
    _log_tick("Arquivo salvo")

    # ── Resumo final (console + log) ─────────────────────────────
    logger.info("")
    logger.info("📊 RESULTADOS — Tabela Comparativa")
    logger.info("")
    logger.info("  %-30s %8s %8s %10s %8s", "Estratégia", "Sharpe", "Sortino", "MaxDD", "Retorno")
    logger.info("  " + "-" * 68)
    for row in comparison:
        s = row["sharpe"] if row["sharpe"] is not None else 0
        so = row["sortino"] if row["sortino"] is not None else 0
        dd = f"{row['max_drawdown']*100:.1f}%" if row["max_drawdown"] is not None else "N/A"
        ret = f"{row['retorno_percent']:.1f}%" if row["retorno_percent"] is not None else "N/A"
        logger.info("  %-30s %8.4f %8.4f %10s %8s", row["estrategia"], s, so, dd, ret)
    logger.info("")


if __name__ == "__main__":
    main()
