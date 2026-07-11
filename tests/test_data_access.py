"""DataAccess 只读数据访问层测试"""

import pytest
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_get_klines_returns_daily_data(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    rows = generate_uptrend_klines(n=60, ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    da = DataAccess()
    klines = da.get_klines("600519.SH", days=60)
    assert len(klines) == 60
    assert klines[0].ts_code == "600519.SH"
    assert hasattr(klines[0], "open")
    assert hasattr(klines[0], "close")


def test_get_klines_empty_for_unknown_stock(temp_db):
    from core.data_access import DataAccess

    da = DataAccess()
    klines = da.get_klines("999999.SZ", days=60)
    assert klines == []


def test_get_klines_by_date_range(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    rows = generate_uptrend_klines(n=60, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    da = DataAccess()
    klines = da.get_klines_by_range("600519.SH", "20250110", "20250120")
    assert len(klines) == 11
    assert klines[0].trade_date == "20250110"
    assert klines[-1].trade_date == "20250120"


def test_get_stock_list(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")

    da = DataAccess()
    stocks = da.get_stock_list()
    assert len(stocks) == 2
    assert any(s["ts_code"] == "600519.SH" for s in stocks)


def test_data_access_is_read_only(temp_db):
    """DataAccess 不应有任何写方法"""
    from core.data_access import DataAccess

    da = DataAccess()
    public_methods = [m for m in dir(da) if not m.startswith("_")]
    for method in public_methods:
        assert not method.startswith("insert")
        assert not method.startswith("update")
        assert not method.startswith("delete")
        assert not method.startswith("write")
        assert not method.startswith("create")
