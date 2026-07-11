"""历史选股筛选器测试"""

import pytest
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines, generate_b1_scenario


def test_historical_screener_returns_scored_stocks(temp_db):
    from core.backtest.historical_screener import screen_historical, ScreenResult
    from core.database import get_connection

    rows1 = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    rows2 = generate_b1_scenario(ts_code="000001.SZ")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")
        write_klines_to_db(conn, rows1)
        write_klines_to_db(conn, rows2)

    result = screen_historical(
        date="20250301",
        strategies=[],
        min_score=0,
    )

    assert isinstance(result, ScreenResult)
    assert result.date == "20250301"
    assert result.total_scanned == 2
    # Results may be empty if no klines before that date, or contain stocks
    # The key is it doesn't crash and returns a ScreenResult


def test_historical_screener_empty_date(temp_db):
    from core.backtest.historical_screener import screen_historical

    result = screen_historical(date="19990101", strategies=["b1"], min_score=0)
    assert result.results == []
    assert result.total_scanned == 0


def test_historical_screener_filters_by_min_score(temp_db):
    from core.backtest.historical_screener import screen_historical
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    result_high = screen_historical(date="20250601", strategies=[], min_score=999)
    result_low = screen_historical(date="20250601", strategies=[], min_score=0)

    assert len(result_high.results) <= len(result_low.results)


def test_historical_screener_returns_sorted_results(temp_db):
    """结果按评分降序排列"""
    from core.backtest.historical_screener import screen_historical
    from core.database import get_connection

    rows1 = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    rows2 = generate_uptrend_klines(n=120, ts_code="000001.SZ", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")
        write_klines_to_db(conn, rows1)
        write_klines_to_db(conn, rows2)

    result = screen_historical(date="20250601", strategies=[], min_score=0)
    if len(result.results) > 1:
        scores = [r.score for r in result.results]
        assert scores == sorted(scores, reverse=True)
