"""个股分析路由测试"""

from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_get_stock_analysis(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/stock/600519.SH?days=120")
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"
    assert len(data["klines"]) > 0
    assert "indicators" in data


def test_get_stock_kline(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=60, ts_code="000001.SZ", start_date="20250101")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/stock/000001.SZ/kline?days=60")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "date" in data[0]


def test_get_stock_analysis_not_found(temp_db):
    from api.app import app

    client = TestClient(app)
    response = client.get("/api/stock/999999.SZ?days=60")
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "999999.SZ"
    assert len(data["klines"]) == 0


def test_get_stock_signals(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/stock/600519.SH/signals?days=120")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
