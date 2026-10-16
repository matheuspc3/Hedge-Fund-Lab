from types import SimpleNamespace

import pandas as pd

from scripts.generate_dashboard_data import (
    _aggregate_equity_curves,
    _dashboard_metrics,
    build_scatter_data,
    run_single_asset_backtests,
    ticker_to_json,
)


def test_equity_aggregation_uses_only_common_dates():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    curves = {
        "A": pd.Series([100.0, 110.0, 120.0], index=dates),
        "B": pd.Series([200.0, 240.0], index=dates[[0, 2]]),
    }

    result = _aggregate_equity_curves(curves)

    assert result.index.tolist() == [dates[0], dates[2]]
    assert result.tolist() == [150.0, 180.0]


def test_scatter_uses_canonical_volatility_instead_of_return_over_sharpe():
    single = {
        "Single": {
            "metrics": {"retorno_percent": 100.0, "sharpe": 2.0, "volatilidade": 7.0}
        }
    }
    portfolio = {
        "Portfolio": {
            "metrics": {"retorno_percent": 60.0, "sharpe": 3.0, "volatilidade": 11.0}
        }
    }

    points = build_scatter_data(single, portfolio)

    assert [point["volatilidade"] for point in points] == [7.0, 11.0]
    assert points[0]["volatilidade"] != 100.0 / 2.0
    assert points[1]["volatilidade"] != 60.0 / 3.0


def test_dashboard_metrics_include_sum_of_executed_trade_costs():
    equity = pd.Series([100.0, 110.0], index=pd.to_datetime(["2024-01-02", "2024-01-03"]))
    trades = [SimpleNamespace(cost=1.25), SimpleNamespace(cost=2.75)]

    metrics = _dashboard_metrics(equity, trades)

    assert metrics["total_transaction_cost"] == 4.0


def test_ticker_period_comes_from_observed_data_not_configured_interval():
    data = pd.DataFrame(
        {"fechamento": [100.0, 110.0]},
        index=pd.to_datetime(["2020-01-02", "2025-12-30"]),
    )

    result = ticker_to_json("TEST3.SA", data)

    assert result is not None
    assert result["periodo"] == {"inicio": "2020-01-02", "fim": "2025-12-30"}


def test_single_asset_result_reports_intersection_as_observed_period():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    data = {
        "A": pd.DataFrame(
            {"abertura": [100.0, 100.0, 100.0], "fechamento": [100.0] * 3},
            index=dates,
        ),
        "B": pd.DataFrame(
            {"abertura": [100.0, 100.0], "fechamento": [100.0] * 2},
            index=dates[[0, 2]],
        ),
    }

    result = run_single_asset_backtests(data, ["A", "B"])["Buy & Hold"]

    assert result["dates"] == ["2024-01-01", "2024-01-03"]
    assert result["periodo"] == {"inicio": "2024-01-01", "fim": "2024-01-03"}
