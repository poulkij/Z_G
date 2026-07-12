# Plan 2: API 层实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 FastAPI REST API 层，连接 core/ 领域逻辑，为 Web 前端提供 JSON 接口，覆盖 5 个功能域：个股分析、选股筛选、回测+调优、选股训练、持仓诊断。

**Architecture:** `api/` 目录包含 `app.py`（FastAPI 入口）、`deps.py`（依赖注入）、`schemas.py`（Pydantic 模型）、`routes/`（5 个路由模块）。通过 `Depends()` 注入 DataAccess 等服务，便于测试 mock。

**Tech Stack:** FastAPI 0.104+, Uvicorn, Pydantic v2, pytest + httpx TestClient

---

## 文件结构

### 新建文件

```
api/__init__.py                  # api 包入口
api/app.py                       # FastAPI 应用入口 + 静态文件挂载 + 路由注册
api/deps.py                       # 依赖注入（DataAccess、服务实例工厂）
api/schemas.py                    # Pydantic 响应模型（所有路由共用）
api/routes/__init__.py            # 路由包
api/routes/stock.py               # 个股分析路由
api/routes/screener.py            # 选股筛选路由
api/routes/backtest.py            # 回测 + 调优路由
api/routes/training.py            # 选股训练路由（历史筛选 + 行情供给）
api/routes/portfolio.py           # 持仓诊断路由
tests/test_api_stock.py           # 个股路由测试
tests/test_api_screener.py        # 选股路由测试
tests/test_api_backtest.py        # 回测路由测试
tests/test_api_training.py        # 训练路由测试
tests/test_api_portfolio.py       # 持仓路由测试
```

### 修改文件

```
requirements.txt                  # 添加 fastapi, uvicorn, jinja2, python-multipart
pyproject.toml                    # 添加依赖（如需要）
```

---

## Task 1: 安装依赖 + 创建 api/ 骨架

**Files:**
- Modify: `requirements.txt`
- Create: `api/__init__.py`
- Create: `api/app.py`
- Create: `api/routes/__init__.py`

- [ ] **Step 1: 安装 FastAPI 依赖**

```bash
pip install fastapi uvicorn[standard] jinja2 python-multipart httpx
```

- [ ] **Step 2: 更新 requirements.txt**

Read `requirements.txt`, then add these lines:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
jinja2>=3.1.0
python-multipart>=0.0.6
httpx>=0.25.0
```

- [ ] **Step 3: 创建 api/__init__.py**

```python
"""API 层 — FastAPI REST 接口"""
```

- [ ] **Step 4: 创建 api/routes/__init__.py**

```python
"""API 路由包"""
```

- [ ] **Step 5: 创建 api/app.py 最小骨架**

```python
"""
FastAPI 应用入口
"""

from fastapi import FastAPI

app = FastAPI(
    title="Z哥量化分析平台",
    description="zettaranc-perspective Web API",
    version="4.0.0",
)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}
```

- [ ] **Step 6: 验证应用可启动**

Run: `python -c "from api.app import app; print('OK')"`
Expected: OK

- [ ] **Step 7: 写健康检查测试**

Create `tests/test_api_health.py`:

```python
"""API 健康检查测试"""

from fastapi.testclient import TestClient


def test_health_check():
    from api.app import app

    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 8: 运行测试**

Run: `python -m pytest tests/test_api_health.py -v`
Expected: 1 passed

- [ ] **Step 9: Commit**

```bash
git add api/ tests/test_api_health.py requirements.txt
git commit -m "feat: add FastAPI app skeleton with health check"
```

---

## Task 2: 创建 schemas.py + deps.py

**Files:**
- Create: `api/schemas.py`
- Create: `api/deps.py`

- [ ] **Step 1: 创建 api/schemas.py**

Read `core/domain/profile.py` and `core/screener/__init__.py` to get exact field names, then create:

```python
"""
Pydantic 响应模型 — 所有 API 路由共用
"""

from pydantic import BaseModel
from typing import Optional


class KLineItem(BaseModel):
    """单根 K 线"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    pct_chg: float = 0.0


class IndicatorSnapshot(BaseModel):
    """指标快照"""
    k: float = 0
    d: float = 0
    j: float = 0
    dif: float = 0
    dea: float = 0
    macd_hist: float = 0
    rsi6: float = 0
    boll_mid: float = 0
    boll_upper: float = 0
    boll_lower: float = 0
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    ma60: float = 0
    vol_ratio: float = 0
    zg_white: float = 0
    dg_yellow: float = 0
    bbi: float = 0


class SignalItem(BaseModel):
    """战法信号"""
    trade_date: str
    strategy: str
    action: str
    confidence: float = 0.0
    price: float = 0.0
    note: str = ""


class StockScoreItem(BaseModel):
    """股票评分"""
    ts_code: str
    name: str = ""
    score: float = 0
    b1_score: float = 0
    trend_score: float = 0
    volume_score: float = 0
    risk_score: float = 0
    reasons: list[str] = []
    warnings: list[str] = []
    rating: str = ""


class StockAnalysisResponse(BaseModel):
    """个股分析完整响应"""
    ts_code: str
    name: str = ""
    klines: list[KLineItem] = []
    indicators: IndicatorSnapshot = IndicatorSnapshot()
    signals: list[SignalItem] = []
    score: Optional[StockScoreItem] = None


class ScreenerResponse(BaseModel):
    """选股结果"""
    total: int = 0
    results: list[StockScoreItem] = []


class TradeItem(BaseModel):
    """单笔交易"""
    ts_code: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    hold_days: int = 0
    exit_reason: str = ""


class BacktestResultResponse(BaseModel):
    """回测结果"""
    ts_code: str
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    avg_return: float = 0.0
    total_return: float = 0.0
    trades: list[TradeItem] = []


class TuneResultResponse(BaseModel):
    """参数调优结果"""
    best_params: dict = {}
    best_score: float = 0.0
    all_results: list[dict] = []


class ScreenResultResponse(BaseModel):
    """历史筛选结果"""
    date: str = ""
    total_scanned: int = 0
    results: list[StockScoreItem] = []


class TrainingScreenRequest(BaseModel):
    """选股训练 - 当日筛选请求"""
    date: str
    strategies: list[str] = []
    min_score: float = 0
    days: int = 120


class TrainingScreenResponse(BaseModel):
    """选股训练 - 当日筛选响应"""
    date: str
    total_scanned: int = 0
    results: list[StockScoreItem] = []


class KLineRangeRequest(BaseModel):
    """按日期范围获取 K 线"""
    ts_code: str
    start_date: str
    end_date: str


class KLineRangeResponse(BaseModel):
    """按日期范围获取 K 线响应"""
    ts_code: str
    klines: list[KLineItem] = []


class DiagnosisResponse(BaseModel):
    """持仓诊断响应"""
    ts_code: str
    name: str = ""
    price: float = 0
    price_position: str = ""
    trend_status: str = ""
    kdj_j: float = 0
    macd_veto: bool = False
    bbi: float = 0
    white_line: float = 0
    yellow_line: float = 0
    sell_score: int = 0
    sell_score_desc: str = ""
    exit_signals: list[dict] = []
    buy_signals: list[dict] = []
    kirin_phase: str = "UNKNOWN"
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    recommendation: str = ""
    risk_level: str = "UNKNOWN"


class PortfolioDiagnoseRequest(BaseModel):
    """持仓诊断请求"""
    holdings: list[str]
    days: int = 100


class PortfolioDiagnoseResponse(BaseModel):
    """持仓诊断响应"""
    results: list[DiagnosisResponse] = []


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: str = "ERROR"
```

- [ ] **Step 2: 创建 api/deps.py**

```python
"""
依赖注入 — 提供 DataAccess 等服务实例
"""

from functools import lru_cache
from core.data_access import DataAccess


@lru_cache(maxsize=1)
def get_data_access() -> DataAccess:
    """获取 DataAccess 单例"""
    return DataAccess()
```

- [ ] **Step 3: 验证导入**

Run: `python -c "from api.schemas import StockAnalysisResponse; print('schemas OK')"`
Run: `python -c "from api.deps import get_data_access; print('deps OK')"`
Expected: 两条都 OK

- [ ] **Step 4: Commit**

```bash
git add api/schemas.py api/deps.py
git commit -m "feat: add Pydantic schemas and dependency injection"
```

---

## Task 3: 个股分析路由 (api/routes/stock.py)

**Files:**
- Create: `api/routes/stock.py`
- Create: `tests/test_api_stock.py`
- Modify: `api/app.py` (注册路由)

- [ ] **Step 1: 写失败测试**

Create `tests/test_api_stock.py`:

```python
"""个股分析路由测试"""

import pytest
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
    assert data["name"] == "贵州茅台"
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
    assert "open" in data[0]
    assert "close" in data[0]


def test_get_stock_analysis_not_found(temp_db):
    from api.app import app

    client = TestClient(app)
    response = client.get("/api/stock/999999.SZ?days=60")
    assert response.status_code == 200  # 返回空数据而非404
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
    data = response.json()
    assert isinstance(data, list)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_stock.py -v`
Expected: FAIL (路由不存在)

- [ ] **Step 3: 实现 api/routes/stock.py**

Read `core/indicators/data_layer.py` to understand `analyze_stock()` and `get_kline_data()` signatures.
Read `core/strategies/orchestrator.py` to understand `detect_all_strategies()`.
Read `core/screener/__init__.py` to understand `score_stock()`.

```python
"""个股分析路由"""

from fastapi import APIRouter, Depends
from api.deps import get_data_access
from api.schemas import (
    StockAnalysisResponse,
    KLineItem,
    IndicatorSnapshot,
    SignalItem,
    StockScoreItem,
)
from core.data_access import DataAccess

router = APIRouter(prefix="/api/stock", tags=["个股分析"])


@router.get("/{ts_code}", response_model=StockAnalysisResponse)
def get_stock_analysis(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取个股完整分析（K线 + 指标 + 信号 + 评分）"""
    from core.indicators import analyze_stock
    from core.strategies import detect_all_strategies
    from core.screener import score_stock

    # 获取 K 线
    klines = da.get_klines(ts_code, days=days)
    kline_items = [
        KLineItem(
            date=k.trade_date,
            open=k.open,
            close=k.close,
            high=k.high,
            low=k.low,
            volume=k.vol,
            pct_chg=k.pct_chg,
        )
        for k in klines
    ]

    # 获取股票名称
    name = ts_code
    stock_list = da.get_stock_list()
    for s in stock_list:
        if s["ts_code"] == ts_code:
            name = s["name"]
            break

    # 获取指标快照
    indicators = IndicatorSnapshot()
    try:
        result = analyze_stock(ts_code, days=days)
        if result:
            indicators = IndicatorSnapshot(
                k=result.k, d=result.d, j=result.j,
                dif=result.dif, dea=result.dea, macd_hist=result.macd_hist,
                rsi6=result.rsi6,
                boll_mid=result.boll_mid, boll_upper=result.boll_upper, boll_lower=result.boll_lower,
                ma5=result.ma5, ma10=result.ma10, ma20=result.ma20, ma60=result.ma60,
                vol_ratio=result.vol_ratio,
                zg_white=result.zg_white, dg_yellow=result.dg_yellow,
                bbi=result.bbi,
            )
    except Exception:
        pass

    # 获取战法信号
    signals = []
    try:
        strategy_signals = detect_all_strategies(ts_code, days=days)
        for sig in strategy_signals:
            signals.append(SignalItem(
                trade_date=sig.trade_date,
                strategy=sig.strategy.value if hasattr(sig.strategy, "value") else str(sig.strategy),
                action=sig.action.value if hasattr(sig.action, "value") else str(sig.action),
                confidence=sig.confidence,
                price=sig.price,
                note=sig.details.get("note", "") if hasattr(sig, "details") else "",
            ))
    except Exception:
        pass

    # 获取评分
    score = None
    try:
        sc = score_stock(ts_code)
        score = StockScoreItem(
            ts_code=sc.ts_code, name=sc.name,
            score=sc.score, b1_score=sc.b1_score,
            trend_score=sc.trend_score, volume_score=sc.volume_score,
            risk_score=sc.risk_score,
            reasons=sc.reasons, warnings=sc.warnings,
            rating=sc.rating,
        )
    except Exception:
        pass

    return StockAnalysisResponse(
        ts_code=ts_code, name=name,
        klines=kline_items, indicators=indicators,
        signals=signals, score=score,
    )


@router.get("/{ts_code}/kline", response_model=list[KLineItem])
def get_stock_kline(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取 K 线数据"""
    klines = da.get_klines(ts_code, days=days)
    return [
        KLineItem(
            date=k.trade_date, open=k.open, close=k.close,
            high=k.high, low=k.low, volume=k.vol, pct_chg=k.pct_chg,
        )
        for k in klines
    ]


@router.get("/{ts_code}/signals", response_model=list[SignalItem])
def get_stock_signals(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取战法信号"""
    from core.strategies import detect_all_strategies

    signals = []
    try:
        strategy_signals = detect_all_strategies(ts_code, days=days)
        for sig in strategy_signals:
            signals.append(SignalItem(
                trade_date=sig.trade_date,
                strategy=sig.strategy.value if hasattr(sig.strategy, "value") else str(sig.strategy),
                action=sig.action.value if hasattr(sig.action, "value") else str(sig.action),
                confidence=sig.confidence,
                price=sig.price,
                note=sig.details.get("note", "") if hasattr(sig, "details") else "",
            ))
    except Exception:
        pass
    return signals
```

IMPORTANT: Check the actual `detect_all_strategies` signature and `StrategySignal` fields before implementing. The `strategy` and `action` fields may be enums or strings.

- [ ] **Step 4: 注册路由到 app.py**

Read `api/app.py`, add after the health check:
```python
from api.routes import stock

app.include_router(stock.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_stock.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add api/routes/stock.py tests/test_api_stock.py api/app.py
git commit -m "feat: add stock analysis API routes"
```

---

## Task 4: 选股筛选路由 (api/routes/screener.py)

**Files:**
- Create: `api/routes/screener.py`
- Create: `tests/test_api_screener.py`
- Modify: `api/app.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_api_screener.py`:

```python
"""选股筛选路由测试"""

import pytest
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
    response = client.get("/api/screener?min_score=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_screener_with_strategy_filter(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.get("/api/screener?strategy=b1&min_score=0&limit=10")
    assert response.status_code == 200
    data = response.json()
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
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_screener.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 api/routes/screener.py**

Read `core/screener/__init__.py` to understand `screen_stocks()` and `score_stock()` signatures.

```python
"""选股筛选路由"""

from fastapi import APIRouter, Depends, Query
from api.deps import get_data_access
from api.schemas import ScreenerResponse, StockScoreItem
from core.data_access import DataAccess

router = APIRouter(prefix="/api/screener", tags=["选股筛选"])


@router.get("", response_model=ScreenerResponse)
def screen_stocks(
    strategy: str = Query("perfect", description="筛选策略"),
    min_score: float = Query(0, description="最低评分"),
    limit: int = Query(50, description="最多返回数量"),
    da: DataAccess = Depends(get_data_access),
):
    """选股筛选"""
    from core.screener import screen_stocks as do_screen

    try:
        scores = do_screen(criteria=strategy, min_score=int(min_score), limit=limit)
    except Exception:
        scores = []

    results = [
        StockScoreItem(
            ts_code=s.ts_code, name=s.name,
            score=s.score, b1_score=s.b1_score,
            trend_score=s.trend_score, volume_score=s.volume_score,
            risk_score=s.risk_score,
            reasons=s.reasons, warnings=s.warnings,
            rating=s.rating,
        )
        for s in scores
    ]

    return ScreenerResponse(total=len(results), results=results)


@router.get("/score/{ts_code}", response_model=StockScoreItem)
def get_stock_score(ts_code: str, da: DataAccess = Depends(get_data_access)):
    """获取单只股票评分"""
    from core.screener import score_stock

    sc = score_stock(ts_code)
    return StockScoreItem(
        ts_code=sc.ts_code, name=sc.name,
        score=sc.score, b1_score=sc.b1_score,
        trend_score=sc.trend_score, volume_score=sc.volume_score,
        risk_score=sc.risk_score,
        reasons=sc.reasons, warnings=sc.warnings,
        rating=sc.rating,
    )
```

IMPORTANT: Check the actual `screen_stocks()` signature in `core/screener/__init__.py` — the parameter names may differ (e.g., `criteria` vs `strategy`).

- [ ] **Step 4: 注册路由到 app.py**

Add:
```python
from api.routes import screener
app.include_router(screener.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_screener.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add api/routes/screener.py tests/test_api_screener.py api/app.py
git commit -m "feat: add screener API routes"
```

---

## Task 5: 回测 + 调优路由 (api/routes/backtest.py)

**Files:**
- Create: `api/routes/backtest.py`
- Create: `tests/test_api_backtest.py`
- Modify: `api/app.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_api_backtest.py`:

```python
"""回测路由测试"""

import pytest
from fastapi.testclient import TestClient
from tests.conftest import write_klines_to_db, generate_b1_scenario


def test_backtest_post(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/backtest", json={
        "ts_code": "600519.SH",
        "days": 120,
        "stop_loss_pct": 0.07,
        "take_profit_pct": 0.15,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"
    assert "total_trades" in data
    assert "win_rate" in data


def test_backtest_tune(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/backtest/tune", json={
        "ts_code": "600519.SH",
        "param_grid": {
            "stop_loss_pct": [0.05, 0.07],
            "take_profit_pct": [0.10, 0.15],
        },
        "days": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert "best_params" in data
    assert "best_score" in data
    assert len(data["all_results"]) == 4


def test_backtest_screener(temp_db):
    from api.app import app
    from core.database import get_connection
    from tests.conftest import write_stock_basic, generate_uptrend_klines

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
    assert "date" in data or "results" in data
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_backtest.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 api/routes/backtest.py**

Read `core/backtest/__init__.py` for `backtest_strategy`, `tune_params`, `screen_historical` signatures.

```python
"""回测 + 调优路由"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from api.schemas import BacktestResultResponse, TuneResultResponse, ScreenResultResponse, StockScoreItem

router = APIRouter(prefix="/api/backtest", tags=["回测"])


class BacktestRequest(BaseModel):
    ts_code: str
    days: int = 240
    stop_loss_pct: float = 0.07
    take_profit_pct: float = 0.15


class TuneRequest(BaseModel):
    ts_code: str
    param_grid: dict[str, list]
    days: int = 240
    score_metric: str = "win_rate"


class HistoricalScreenRequest(BaseModel):
    date_range: dict[str, str]  # {"start": "20250101", "end": "20250601"}
    criteria: dict = {}  # {"min_score": 0, "strategies": ["b1"]}


@router.post("", response_model=BacktestResultResponse)
def run_backtest(req: BacktestRequest):
    """单次回测"""
    from core.backtest import backtest_strategy

    result = backtest_strategy(
        req.ts_code, days=req.days,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
    )
    return BacktestResultResponse(
        ts_code=result.ts_code,
        total_trades=result.total_trades,
        win_trades=result.win_trades,
        loss_trades=result.loss_trades,
        win_rate=result.win_rate,
        profit_factor=result.profit_factor,
        max_drawdown=result.max_drawdown,
        avg_return=result.avg_return,
        total_return=result.total_return,
        trades=[
            {"ts_code": t.ts_code, "entry_date": t.entry_date, "entry_price": t.entry_price,
             "exit_date": t.exit_date, "exit_price": t.exit_price,
             "pnl": t.pnl, "pnl_pct": t.pnl_pct, "hold_days": t.hold_days,
             "exit_reason": t.exit_reason}
            for t in result.trades
        ],
    )


@router.post("/tune", response_model=TuneResultResponse)
def tune_backtest(req: TuneRequest):
    """参数调优（网格搜索）"""
    from core.backtest import tune_params

    result = tune_params(
        req.ts_code, req.param_grid,
        days=req.days, score_metric=req.score_metric,
    )
    return TuneResultResponse(
        best_params=result.best_params,
        best_score=result.best_score,
        all_results=result.all_results,
    )


@router.post("/screener", response_model=ScreenResultResponse)
def historical_screen(req: HistoricalScreenRequest):
    """历史选股筛选"""
    from core.backtest import screen_historical

    end_date = req.date_range.get("end", "")
    strategies = req.criteria.get("strategies", [])
    min_score = req.criteria.get("min_score", 0)

    result = screen_historical(
        date=end_date, strategies=strategies, min_score=min_score,
    )
    return ScreenResultResponse(
        date=result.date,
        total_scanned=result.total_scanned,
        results=[
            StockScoreItem(
                ts_code=s.ts_code, name=s.name, score=s.score,
                b1_score=s.b1_score, trend_score=s.trend_score,
                volume_score=s.volume_score, risk_score=s.risk_score,
                reasons=s.reasons, warnings=s.warnings, rating=s.rating,
            )
            for s in result.results
        ],
    )
```

- [ ] **Step 4: 注册路由到 app.py**

Add:
```python
from api.routes import backtest
app.include_router(backtest.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_backtest.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add api/routes/backtest.py tests/test_api_backtest.py api/app.py
git commit -m "feat: add backtest and tuning API routes"
```

---

## Task 6: 选股训练路由 (api/routes/training.py)

**Files:**
- Create: `api/routes/training.py`
- Create: `tests/test_api_training.py`
- Modify: `api/app.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_api_training.py`:

```python
"""选股训练路由测试"""

import pytest
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
        "date": "20250601",
        "strategies": [],
        "min_score": 0,
        "days": 120,
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
        "ts_code": "600519.SH",
        "start_date": "20250110",
        "end_date": "20250120",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["ts_code"] == "600519.SH"
    assert len(data["klines"]) > 0


def test_training_screen_with_strategies(temp_db):
    from api.app import app
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    client = TestClient(app)
    response = client.post("/api/training/screen", json={
        "date": "20250601",
        "strategies": ["b1"],
        "min_score": 0,
        "days": 120,
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["results"], list)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_training.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 api/routes/training.py**

```python
"""选股训练路由 — 历史筛选 + 行情数据供给"""

from fastapi import APIRouter, Depends
from api.deps import get_data_access
from api.schemas import (
    TrainingScreenRequest, TrainingScreenResponse,
    KLineRangeRequest, KLineRangeResponse,
    KLineItem, StockScoreItem,
)
from core.data_access import DataAccess

router = APIRouter(prefix="/api/training", tags=["选股训练"])


@router.post("/screen", response_model=TrainingScreenResponse)
def training_screen(req: TrainingScreenRequest, da: DataAccess = Depends(get_data_access)):
    """当日战法筛选 — 选股训练 Step 2"""
    from core.backtest import screen_historical

    result = screen_historical(
        date=req.date,
        strategies=req.strategies,
        min_score=req.min_score,
        days=req.days,
    )
    return TrainingScreenResponse(
        date=result.date,
        total_scanned=result.total_scanned,
        results=[
            StockScoreItem(
                ts_code=s.ts_code, name=s.name, score=s.score,
                b1_score=s.b1_score, trend_score=s.trend_score,
                volume_score=s.volume_score, risk_score=s.risk_score,
                reasons=s.reasons, warnings=s.warnings, rating=s.rating,
            )
            for s in result.results
        ],
    )


@router.post("/kline", response_model=KLineRangeResponse)
def training_kline(req: KLineRangeRequest, da: DataAccess = Depends(get_data_access)):
    """按日期范围获取 K 线 — 选股训练 Step 3 行情供给"""
    klines = da.get_klines_by_range(req.ts_code, req.start_date, req.end_date)
    return KLineRangeResponse(
        ts_code=req.ts_code,
        klines=[
            KLineItem(
                date=k.trade_date, open=k.open, close=k.close,
                high=k.high, low=k.low, volume=k.vol, pct_chg=k.pct_chg,
            )
            for k in klines
        ],
    )
```

- [ ] **Step 4: 注册路由到 app.py**

Add:
```python
from api.routes import training
app.include_router(training.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_training.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add api/routes/training.py tests/test_api_training.py api/app.py
git commit -m "feat: add training API routes"
```

---

## Task 7: 持仓诊断路由 (api/routes/portfolio.py)

**Files:**
- Create: `api/routes/portfolio.py`
- Create: `tests/test_api_portfolio.py`
- Modify: `api/app.py`

- [ ] **Step 1: 写失败测试**

Create `tests/test_api_portfolio.py`:

```python
"""持仓诊断路由测试"""

import pytest
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
        "holdings": ["600519.SH"],
        "days": 100,
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
        "holdings": [],
        "days": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []


def test_portfolio_diagnose_multiple(temp_db):
    from api.app import app
    from core.database import get_connection

    rows1 = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    rows2 = generate_uptrend_klines(n=120, ts_code="000001.SZ", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")
        write_klines_to_db(conn, rows1)
        write_klines_to_db(conn, rows2)

    client = TestClient(app)
    response = client.post("/api/portfolio/diagnose", json={
        "holdings": ["600519.SH", "000001.SZ"],
        "days": 100,
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_api_portfolio.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 api/routes/portfolio.py**

Read `modules/portfolio_diagnosis.py` to understand `diagnose_stock()` and `DiagnosisReport` fields.

```python
"""持仓诊断路由"""

from fastapi import APIRouter
from api.schemas import PortfolioDiagnoseRequest, PortfolioDiagnoseResponse, DiagnosisResponse

router = APIRouter(prefix="/api/portfolio", tags=["持仓诊断"])


@router.post("/diagnose", response_model=PortfolioDiagnoseResponse)
def diagnose_holdings(req: PortfolioDiagnoseRequest):
    """持仓诊断"""
    from modules.portfolio_diagnosis import diagnose_stock

    results = []
    for ts_code in req.holdings:
        try:
            report = diagnose_stock(ts_code, days=req.days)
            results.append(DiagnosisResponse(
                ts_code=report.ts_code,
                name=report.name,
                price=report.price,
                price_position=report.price_position,
                trend_status=report.trend_status,
                kdj_j=report.kdj_j,
                macd_veto=report.macd_veto,
                bbi=report.bbi,
                white_line=report.white_line,
                yellow_line=report.yellow_line,
                sell_score=report.sell_score,
                sell_score_desc=report.sell_score_desc,
                exit_signals=report.exit_signals,
                buy_signals=report.buy_signals,
                kirin_phase=report.kirin_phase,
                stop_loss=report.stop_loss,
                target_price=report.target_price,
                recommendation=report.recommendation,
                risk_level=report.risk_level,
            ))
        except Exception as e:
            results.append(DiagnosisResponse(
                ts_code=ts_code,
                name="",
                recommendation=f"诊断失败: {e}",
                risk_level="UNKNOWN",
            ))

    return PortfolioDiagnoseResponse(results=results)
```

IMPORTANT: Check the actual `DiagnosisReport` fields in `modules/portfolio_diagnosis.py` and match them to the `DiagnosisResponse` schema. Adjust field names as needed.

- [ ] **Step 4: 注册路由到 app.py**

Add:
```python
from api.routes import portfolio
app.include_router(portfolio.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_api_portfolio.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add api/routes/portfolio.py tests/test_api_portfolio.py api/app.py
git commit -m "feat: add portfolio diagnosis API routes"
```

---

## Task 8: 集成测试 + 最终验证

**Files:**
- Run: all API tests

- [ ] **Step 1: 运行所有 API 测试**

Run: `python -m pytest tests/test_api_*.py -v --tb=short`
Expected: All API tests pass

- [ ] **Step 2: 启动服务器验证**

Run in one terminal: `python -c "from api.app import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"`
Run in another: `curl http://127.0.0.1:8000/api/health`
Expected: `{"status":"ok"}`

Or test with TestClient:
```python
python -c "
from fastapi.testclient import TestClient
from api.app import app
client = TestClient(app)
print('Health:', client.get('/api/health').json())
print('Docs:', client.get('/docs').status_code)
"
```

- [ ] **Step 3: 运行全部测试确保无回归**

Run: `python -m pytest tests/ --tb=short --ignore=tests/test_intent_router.py --ignore=tests/test_intent_chat.py --ignore=tests/test_notifier.py --ignore=tests/test_quality_check.py --ignore=tests/test_rate_limiter.py --ignore=tests/test_tushare_client.py --ignore=tests/test_backtest_scorer.py --ignore=tests/test_data_sync_extensions.py --ignore=tests/test_self_optimizer_integration.py 2>&1 | Select-Object -Last 10`
Expected: All pass, no new failures

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: complete API layer with all 5 route modules"
```

---

## 注意事项

### FastAPI TestClient 与数据库

TestClient 使用与 pytest 相同的进程，所以 `temp_db` fixture 设置的环境变量（`DB_PATH`）会被 API 路由中的 `DataAccess` 读取到。无需特殊配置。

### Pydantic v2

项目可能安装的是 Pydantic v2。主要区别：
- `BaseModel` 配置使用 `model_config = ConfigDict(...)` 而非 `class Config`
- `model_dump()` 代替 `dict()`
- `model_validate()` 代替 `parse_obj()`

本计划中的 schemas 使用 Pydantic v2 兼容写法。

### 错误处理

路由中对 core 层调用都用 try/except 包裹，返回空数据而非 500 错误。这样前端不会因为单只股票数据缺失而崩溃。

### 启动方式

```bash
uvicorn api.app:app --reload --port 8000
# 或注册到 zt 命令
zt web  # 后续 Plan 3 添加
```
