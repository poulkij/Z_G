"""
真实数据端到端测试 — 使用 data/stock_data.db 中的真实 Tushare 行情

与 test_api_*.py 系列的区别：
  - 后者使用 conftest.py 的 mock_env_for_tests + generate_uptrend_klines 合成数据
  - 本文件连接真实 210MB SQLite 数据库（5530 只股票、136 万+ K 线记录）
  - 验证完整管道：DataAccess → indicators → strategies → screener → API 响应

运行条件（全部满足才跑）：
  1. data/stock_data.db 存在且可读
  2. RUN_REALDATA=true

用法：
  $env:RUN_REALDATA='true'; python -m pytest tests/test_api_realdata_e2e.py -v
"""

import os
import sqlite3
from pathlib import Path

import pytest

# ==================== 跳过条件 ====================

_PROJECT_ROOT = Path(__file__).parent.parent
_REAL_DB = _PROJECT_ROOT / "data" / "stock_data.db"
_RUN_REALDATA = os.environ.get("RUN_REALDATA", "").lower() == "true"

pytestmark = pytest.mark.skipif(
    not (_REAL_DB.exists() and _RUN_REALDATA),
    reason=f"需 data/stock_data.db 存在且 RUN_REALDATA=true（当前 DB exists: {_REAL_DB.exists()}, RUN_REALDATA: {_RUN_REALDATA}）",
)

# 测试用股票（数据库中确认有 483 天 K 线数据，20240628~20260626）
TEST_STOCK = "600519.SH"       # 贵州茅台
TEST_STOCK_2 = "000001.SZ"     # 平安银行
TEST_STOCK_3 = "000858.SZ"     # 五粮液
TEST_DATE_START = "20250101"
TEST_DATE_END = "20250601"


# ==================== Fixture：覆盖 mock_env_for_tests ====================


@pytest.fixture(autouse=True)
def real_db_env(mock_env_for_tests):
    """覆盖 mock_env_for_tests 的 DB_PATH，指向真实数据库

    mock_env_for_tests 是 autouse、function scope，会把 DB_PATH 设为临时文件。
    本 fixture 显式依赖它（保证执行顺序），然后把 DB_PATH 改回真实路径。
    """
    real_path = str(_REAL_DB)
    os.environ["DB_PATH"] = real_path
    os.environ["DATA_MODE"] = "jnb"
    yield real_path


@pytest.fixture(scope="module")
def real_db_conn():
    """直接连接真实数据库（用于预检断言）"""
    conn = sqlite3.connect(str(_REAL_DB))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ==================== 1. 数据库预检 ====================


class TestRealDatabasePrecheck:
    """验证真实数据库结构和数据量"""

    def test_database_has_stock_basic(self, real_db_conn):
        """stock_basic 表有数据"""
        count = real_db_conn.execute("SELECT COUNT(*) FROM stock_basic").fetchone()[0]
        assert count > 5000, f"stock_basic 仅 {count} 条，预期 5000+"

    def test_database_has_daily_kline(self, real_db_conn):
        """daily_kline 表有数据"""
        count = real_db_conn.execute("SELECT COUNT(*) FROM daily_kline").fetchone()[0]
        assert count > 1_000_000, f"daily_kline 仅 {count} 条，预期 100 万+"

    def test_test_stock_has_klines(self, real_db_conn):
        """测试股票有足够 K 线数据"""
        count = real_db_conn.execute(
            "SELECT COUNT(*) FROM daily_kline WHERE ts_code = ?", (TEST_STOCK,)
        ).fetchone()[0]
        assert count >= 120, f"{TEST_STOCK} 仅 {count} 条 K 线，需要 120+"

    def test_test_stock_name(self, real_db_conn):
        """测试股票名称可查"""
        row = real_db_conn.execute(
            "SELECT name FROM stock_basic WHERE ts_code = ?", (TEST_STOCK,)
        ).fetchone()
        assert row is not None
        assert len(row["name"]) > 0


# ==================== 2. DataAccess 层 ====================


class TestDataAccessReal:
    """DataAccess 只读层 — 真实数据"""

    def test_get_klines_returns_real_data(self):
        from core.data_access import DataAccess

        da = DataAccess()
        klines = da.get_klines(TEST_STOCK, days=120)
        assert len(klines) == 120
        assert klines[0].ts_code == TEST_STOCK
        # 茅台股价应该在合理范围（1000~2000）
        assert klines[-1].close > 100
        assert klines[-1].close < 10000

    def test_get_klines_ascending_order(self):
        from core.data_access import DataAccess

        da = DataAccess()
        klines = da.get_klines(TEST_STOCK, days=30)
        dates = [k.trade_date for k in klines]
        assert dates == sorted(dates), "K 线应按日期升序"

    def test_get_klines_by_range(self):
        from core.data_access import DataAccess

        da = DataAccess()
        klines = da.get_klines_by_range(TEST_STOCK, TEST_DATE_START, TEST_DATE_END)
        assert len(klines) > 0
        assert klines[0].trade_date >= TEST_DATE_START
        assert klines[-1].trade_date <= TEST_DATE_END

    def test_get_stock_list_has_real_stocks(self):
        from core.data_access import DataAccess

        da = DataAccess()
        stocks = da.get_stock_list()
        assert len(stocks) > 5000
        codes = [s["ts_code"] for s in stocks]
        assert TEST_STOCK in codes

    def test_get_klines_unknown_stock_empty(self):
        from core.data_access import DataAccess

        da = DataAccess()
        klines = da.get_klines("999999.SZ", days=60)
        assert klines == []


# ==================== 3. 指标计算管道 ====================


class TestIndicatorPipelineReal:
    """analyze_stock 全管道 — 真实数据"""

    def test_analyze_stock_returns_valid_result(self):
        from core.indicators import analyze_stock

        result = analyze_stock(TEST_STOCK, days=120)
        assert result is not None
        assert result.ts_code == TEST_STOCK
        assert len(result.trade_date) == 8  # YYYYMMDD

    def test_analyze_stock_kdj_values_reasonable(self):
        from core.indicators import analyze_stock

        result = analyze_stock(TEST_STOCK, days=120)
        # KDJ K/D 在 0~100，J 可以略超出
        assert -20 <= result.k <= 120
        assert -20 <= result.d <= 120
        assert -50 <= result.j <= 150

    def test_analyze_stock_macd_values(self):
        from core.indicators import analyze_stock

        result = analyze_stock(TEST_STOCK, days=120)
        # MACD dif/dea 可正可负，但不应是 NaN
        assert result.dif == result.dif  # not NaN
        assert result.dea == result.dea

    def test_analyze_stock_bollinger(self):
        from core.indicators import analyze_stock

        result = analyze_stock(TEST_STOCK, days=120)
        assert result.boll_upper >= result.boll_mid >= result.boll_lower

    def test_analyze_stock_ma_lines(self):
        from core.indicators import analyze_stock

        result = analyze_stock(TEST_STOCK, days=120)
        assert result.ma5 > 0
        assert result.ma10 > 0
        assert result.ma20 > 0
        assert result.ma60 > 0

    def test_analyze_stock_multiple_stocks(self):
        """多只股票都能正常计算"""
        from core.indicators import analyze_stock

        for code in [TEST_STOCK, TEST_STOCK_2, TEST_STOCK_3]:
            result = analyze_stock(code, days=120)
            assert result is not None
            assert result.ts_code == code


# ==================== 4. 战法识别管道 ====================


class TestStrategyDetectionReal:
    """detect_all_strategies — 真实数据"""

    def test_detect_returns_list(self):
        from core.strategies import detect_all_strategies

        signals = detect_all_strategies(TEST_STOCK, days=120)
        assert isinstance(signals, list)

    def test_detect_multiple_stocks(self):
        """多只股票战法识别不报错"""
        from core.strategies import detect_all_strategies

        for code in [TEST_STOCK, TEST_STOCK_2, TEST_STOCK_3]:
            signals = detect_all_strategies(code, days=120)
            assert isinstance(signals, list)

    def test_signal_structure(self):
        """如果有信号，结构合法"""
        from core.strategies import detect_all_strategies

        # 用三只股票的信号汇总来检查结构（单只可能无信号）
        all_signals = []
        for code in [TEST_STOCK, TEST_STOCK_2, TEST_STOCK_3]:
            all_signals.extend(detect_all_strategies(code, days=240))

        if all_signals:
            sig = all_signals[0]
            assert hasattr(sig, "trade_date")
            assert hasattr(sig, "strategy")
            assert hasattr(sig, "action")
            assert hasattr(sig, "confidence")
            assert hasattr(sig, "price")
            assert hasattr(sig, "reason")


# ==================== 5. 选股评分管道 ====================


class TestScreenerReal:
    """score_stock — 真实数据"""

    def test_score_stock_returns_score(self):
        from core.screener import score_stock

        sc = score_stock(TEST_STOCK)
        assert sc.ts_code == TEST_STOCK
        assert 0 <= sc.score <= 100
        assert len(sc.rating) > 0
        assert "★" in sc.rating  # 评级格式如 "★★☆☆☆ 谨慎"

    def test_score_stock_has_name(self):
        from core.screener import score_stock

        sc = score_stock(TEST_STOCK)
        assert len(sc.name) > 0

    def test_score_multiple_stocks(self):
        from core.screener import score_stock

        for code in [TEST_STOCK, TEST_STOCK_2, TEST_STOCK_3]:
            sc = score_stock(code)
            assert sc.ts_code == code
            assert 0 <= sc.score <= 100


# ==================== 6. API 端点 — 个股分析 ====================


class TestAPIStockReal:
    """API /api/stock/* — 真实数据"""

    def test_stock_analysis_full(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/api/v1/stock/{TEST_STOCK}?days=120")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ts_code"] == TEST_STOCK
        assert len(data["klines"]) == 120
        assert data["name"] != TEST_STOCK  # 应该返回中文名

    def test_stock_analysis_indicators_populated(self):
        """指标快照应有非零值（真实数据 120 天足够算 MA60）"""
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/api/v1/stock/{TEST_STOCK}?days=120")
        data = resp.json()
        ind = data["indicators"]
        assert ind["ma5"] > 0
        assert ind["ma60"] > 0
        assert ind["boll_upper"] >= ind["boll_mid"]

    def test_stock_kline_endpoint(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/api/v1/stock/{TEST_STOCK}/kline?days=30")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 30
        assert "date" in data[0]
        assert "open" in data[0]
        assert "close" in data[0]

    def test_stock_signals_endpoint(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/api/v1/stock/{TEST_STOCK}/signals?days=240")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_stock_analysis_unknown_stock(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/api/v1/stock/999999.SZ?days=60")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["klines"]) == 0


# ==================== 7. API 端点 — 选股评分 ====================


class TestAPIScreenerReal:
    """API /api/screener/* — 真实数据"""

    def test_stock_score_endpoint(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/api/screener/score/{TEST_STOCK}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ts_code"] == TEST_STOCK
        assert 0 <= data["score"] <= 100


# ==================== 8. API 端点 — 回测 ====================


class TestAPIBacktestReal:
    """API /api/backtest — 真实数据"""

    def test_backtest_returns_result(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.post(
            "/api/v1/backtest",
            json={
                "ts_code": TEST_STOCK,
                "days": 240,
                "stop_loss_pct": 0.07,
                "take_profit_pct": 0.15,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ts_code"] == TEST_STOCK
        assert data["total_trades"] >= 0
        assert 0 <= data["win_rate"] <= 1


# ==================== 9. API 端点 — 持仓诊断 ====================


class TestAPIPortfolioReal:
    """API /api/portfolio/diagnose — 真实数据"""

    def test_diagnose_single_stock(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.post(
            "/api/portfolio/diagnose",
            json={"holdings": [TEST_STOCK], "days": 100},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 1
        r = data["results"][0]
        assert r["ts_code"] == TEST_STOCK
        assert len(r["recommendation"]) > 0

    def test_diagnose_multiple_stocks(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.post(
            "/api/portfolio/diagnose",
            json={"holdings": [TEST_STOCK, TEST_STOCK_2, TEST_STOCK_3], "days": 100},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) == 3


# ==================== 10. API 端点 — 选股训练 ====================


class TestAPITrainingReal:
    """API /api/training/kline — 真实数据"""

    def test_training_kline_range(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.post(
            "/api/training/kline",
            json={
                "ts_code": TEST_STOCK,
                "start_date": TEST_DATE_START,
                "end_date": TEST_DATE_END,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ts_code"] == TEST_STOCK
        assert len(data["klines"]) > 0


# ==================== 11. Web 页面渲染 ====================


class TestWebPagesReal:
    """Web 页面能正常渲染（不依赖真实数据内容，但验证模板不报错）"""

    def test_home_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_stock_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get(f"/stock/{TEST_STOCK}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_screener_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/screener")
        assert resp.status_code == 200

    def test_backtest_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/backtest")
        assert resp.status_code == 200

    def test_training_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/training")
        assert resp.status_code == 200

    def test_portfolio_page(self):
        from fastapi.testclient import TestClient
        from api.app import app

        client = TestClient(app)
        resp = client.get("/portfolio")
        assert resp.status_code == 200
