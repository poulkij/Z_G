"""参数调优器测试"""

import pytest
from tests.conftest import write_klines_to_db, generate_b1_scenario, generate_uptrend_klines


def test_param_tuner_returns_best_params(temp_db):
    from core.backtest.param_tuner import tune_params, TuneResult
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    param_grid = {
        "stop_loss_pct": [0.05, 0.07, 0.10],
        "take_profit_pct": [0.10, 0.15, 0.20],
    }

    result = tune_params(
        ts_code="600519.SH",
        param_grid=param_grid,
        days=120,
    )

    assert isinstance(result, TuneResult)
    assert result.best_params is not None
    assert "stop_loss_pct" in result.best_params
    assert "take_profit_pct" in result.best_params
    assert len(result.all_results) == 9  # 3x3 grid


def test_param_tuner_best_score_is_max(temp_db):
    from core.backtest.param_tuner import tune_params
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    param_grid = {
        "stop_loss_pct": [0.05, 0.07],
        "take_profit_pct": [0.10, 0.15],
    }

    result = tune_params("600519.SH", param_grid, days=120)

    scores = [r["score"] for r in result.all_results]
    assert result.best_score == max(scores)


def test_param_tuner_empty_data(temp_db):
    from core.backtest.param_tuner import tune_params

    param_grid = {"stop_loss_pct": [0.05]}
    result = tune_params("999999.SZ", param_grid, days=60)
    assert result.best_params == {}
    assert result.best_score == 0.0
    assert result.all_results == []


def test_param_tuner_score_metric_total_return(temp_db):
    from core.backtest.param_tuner import tune_params
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    param_grid = {
        "stop_loss_pct": [0.05, 0.10],
        "take_profit_pct": [0.10, 0.20],
    }

    result = tune_params("600519.SH", param_grid, days=120, score_metric="total_return")
    assert len(result.all_results) == 4
    # total_return values should be in the results
    for r in result.all_results:
        assert "total_return" in r
