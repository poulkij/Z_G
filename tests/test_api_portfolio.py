"""持仓诊断路由测试"""

from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_portfolio_diagnose(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/portfolio/diagnose", json={
        "holdings": ["600519.SH"], "days": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["ts_code"] == "600519.SH"


def test_portfolio_diagnose_empty(temp_db):
    from api.app import app

    client = TestClient(app)
    response = client.post("/api/portfolio/diagnose", json={
        "holdings": [], "days": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
