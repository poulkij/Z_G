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
