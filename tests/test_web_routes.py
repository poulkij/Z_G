"""Web 页面路由测试"""

from fastapi.testclient import TestClient


def test_home_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Z哥量化分析平台" in response.text


def test_stock_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/stock/600519.SH")
    assert response.status_code == 200
    assert "600519.SH" in response.text


def test_static_css():
    from api.app import app
    client = TestClient(app)
    response = client.get("/static/css/app.css")
    assert response.status_code == 200
    assert "background" in response.text


def test_screener_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/screener")
    assert response.status_code == 200
    assert "选股筛选" in response.text


def test_backtest_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/backtest")
    assert response.status_code == 200
    assert "策略回测" in response.text


def test_training_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/training")
    assert response.status_code == 200
    assert "选股训练" in response.text


def test_portfolio_page():
    from api.app import app
    client = TestClient(app)
    response = client.get("/portfolio")
    assert response.status_code == 200
    assert "持仓诊断" in response.text
