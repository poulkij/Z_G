"""选股筛选路由测试"""

from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_screener_returns_results(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/screener?strategy=b1&max_stocks=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_screener_score_single(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/screener/score/600519.SH")
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"


def test_screener_historical(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post(
        "/api/screener/historical",
        json={"date": "20250601", "strategies": ["b1"], "min_score": 0, "days": 150, "limit": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)
