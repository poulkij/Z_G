"""回测路由测试"""

from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, write_stock_basic, generate_b1_scenario, generate_uptrend_klines


def test_backtest_post(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/backtest", json={
        "ts_code": "600519.SH", "days": 120,
        "stop_loss_pct": 0.07, "take_profit_pct": 0.15,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"
    assert "total_trades" in data


def test_backtest_tune(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/backtest/tune", json={
        "ts_code": "600519.SH",
        "param_grid": {"stop_loss_pct": [0.05, 0.07], "take_profit_pct": [0.10, 0.15]},
        "days": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert "best_params" in data
    assert len(data["all_results"]) == 4


def test_backtest_screener(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/backtest/screener", json={
        "date_range": {"start": "20250301", "end": "20250601"},
        "criteria": {"min_score": 0, "strategies": []},
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
