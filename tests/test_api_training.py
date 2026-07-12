"""选股训练路由测试"""

from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_training_screen(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/training/screen", json={
        "date": "20250601", "strategies": [], "min_score": 0, "days": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "20250601"
    assert "total_scanned" in data
    assert isinstance(data["results"], list)


def test_training_kline_range(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/training/kline", json={
        "ts_code": "600519.SH", "start_date": "20250110", "end_date": "20250120",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"
    assert len(data["klines"]) > 0
