# Plan 3: Web 基础 + 个股看板实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建响应式 Web 前端基础框架（Jinja2 模板 + ECharts + PWA），实现个股看板页面（K线主图 + 通达信式自定义副图 + 信号标注 + 评分雷达图），支持移动端。

**Architecture:** `web/` 目录包含 Jinja2 模板、静态资源（CSS/JS）、PWA 配置。FastAPI 通过 `app.py` 挂载静态文件和模板渲染。个股看板通过 API 获取数据，前端 ECharts 渲染图表，副图配置存 localStorage。

**Tech Stack:** Jinja2 3.1+, ECharts 5.x (CDN), 原生 JavaScript, CSS Grid/Flexbox, PWA Service Worker

---

## 文件结构

### 新建文件

```
web/__init__.py
web/templates/base.html                    # 基础布局（响应式 nav）
web/templates/stock/analysis.html         # 个股看板
web/templates/index.html                   # 首页（导航到各功能页）
web/static/css/app.css                     # 响应式样式
web/static/js/api.js                       # fetch API 封装
web/static/js/charts/kline.js              # K线主图组件
web/static/js/charts/indicator.js          # 副图指标（通达信式自定义）
web/static/js/charts/signal.js             # 信号标注
web/static/js/charts/radar.js              # 评分雷达图
web/static/js/pages/stock.js               # 个股页交互逻辑
web/static/manifest.json                   # PWA manifest
web/static/sw.js                           # Service Worker
api/web_routes.py                          # Web 页面路由（Jinja2 渲染）
tests/test_web_routes.py                   # Web 路由测试
```

### 修改文件

```
api/app.py                                 # 挂载静态文件 + 注册 web 路由
```

---

## Task 1: Web 基础框架 — base 模板 + 静态资源 + PWA

**Files:**
- Create: `web/__init__.py`
- Create: `web/templates/base.html`
- Create: `web/templates/index.html`
- Create: `web/static/css/app.css`
- Create: `web/static/manifest.json`
- Create: `web/static/sw.js`
- Create: `api/web_routes.py`
- Modify: `api/app.py`

- [ ] **Step 1: 创建 web/ 目录结构**

```bash
mkdir web
mkdir web\templates
mkdir web\templates\stock
mkdir web\static
mkdir web\static\css
mkdir web\static\js
mkdir web\static\js\charts
mkdir web\static\js\pages
```

- [ ] **Step 2: 创建 web/__init__.py**

```python
"""Web 层 — Jinja2 模板 + ECharts 前端"""
```

- [ ] **Step 3: 创建 web/templates/base.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Z哥量化分析平台{% endblock %}</title>
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#1a1a2e">
    <link rel="stylesheet" href="/static/css/app.css">
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">
            <a href="/">Z哥量化分析平台</a>
        </div>
        <button class="nav-toggle" onclick="document.querySelector('.nav-menu').classList.toggle('active')">
            <span></span><span></span><span></span>
        </button>
        <ul class="nav-menu">
            <li><a href="/stock/600519.SH">个股看板</a></li>
            <li><a href="/screener">选股</a></li>
            <li><a href="/backtest">回测</a></li>
            <li><a href="/training">选股训练</a></li>
            <li><a href="/portfolio">持仓诊断</a></li>
        </ul>
    </nav>
    <main class="content">
        {% block content %}{% endblock %}
    </main>
    <script src="/static/js/api.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 4: 创建 web/templates/index.html**

```html
{% extends "base.html" %}

{% block title %}Z哥量化分析平台 — 首页{% endblock %}

{% block content %}
<div class="home-grid">
    <a href="/stock/600519.SH" class="home-card">
        <h2>个股看板</h2>
        <p>K线 + 技术指标 + 战法信号 + 评分</p>
    </a>
    <a href="/screener" class="home-card">
        <h2>选股筛选</h2>
        <p>多策略筛选 + 评分排序</p>
    </a>
    <a href="/backtest" class="home-card">
        <h2>策略回测</h2>
        <p>历史回测 + 参数调优</p>
    </a>
    <a href="/training" class="home-card">
        <h2>选股训练</h2>
        <p>日期选股 + 模拟交易 + 结算</p>
    </a>
    <a href="/portfolio" class="home-card">
        <h2>持仓诊断</h2>
        <p>持股诊断 + 交割单复盘</p>
    </a>
</div>
{% endblock %}
```

- [ ] **Step 5: 创建 web/static/css/app.css**

```css
/* ===== 基础重置 ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --bg: #0f0f1e;
    --card-bg: #1a1a2e;
    --text: #e0e0e0;
    --text-dim: #888;
    --accent: #e94560;
    --green: #00b386;
    --red: #e74c3c;
    --border: #2a2a4a;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
}

/* ===== 导航栏 ===== */
.navbar {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 0 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-brand a {
    color: var(--accent);
    text-decoration: none;
    font-weight: bold;
    font-size: 1.1rem;
}

.nav-menu {
    list-style: none;
    display: flex;
    gap: 1.5rem;
}

.nav-menu a {
    color: var(--text-dim);
    text-decoration: none;
    transition: color 0.2s;
}

.nav-menu a:hover { color: var(--text); }

.nav-toggle {
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    flex-direction: column;
    gap: 4px;
}

.nav-toggle span {
    width: 24px;
    height: 2px;
    background: var(--text);
}

/* ===== 内容区 ===== */
.content {
    padding: 1rem;
    max-width: 1400px;
    margin: 0 auto;
}

/* ===== 首页卡片 ===== */
.home-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
    margin-top: 2rem;
}

.home-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    text-decoration: none;
    color: var(--text);
    transition: border-color 0.2s, transform 0.2s;
}

.home-card:hover {
    border-color: var(--accent);
    transform: translateY(-2px);
}

.home-card h2 {
    color: var(--accent);
    margin-bottom: 0.5rem;
    font-size: 1.2rem;
}

.home-card p {
    color: var(--text-dim);
    font-size: 0.9rem;
}

/* ===== 个股看板 ===== */
.stock-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.stock-title {
    font-size: 1.4rem;
}

.stock-title .name { color: var(--text-dim); font-size: 1rem; margin-left: 0.5rem; }

.stock-search {
    display: flex;
    gap: 0.5rem;
}

.stock-search input {
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem;
    border-radius: 4px;
    width: 200px;
}

.stock-search button {
    background: var(--accent);
    border: none;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
}

/* ===== 图表容器 ===== */
.chart-grid {
    display: grid;
    gap: 0.5rem;
}

.chart-main { height: 400px; }

.chart-sub-windows {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.chart-sub {
    height: 150px;
    position: relative;
}

.chart-sub .sub-toolbar {
    position: absolute;
    top: 0;
    right: 0;
    z-index: 10;
    display: flex;
    gap: 0.25rem;
}

.chart-sub .sub-toolbar select {
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 2px 6px;
    border-radius: 2px;
    font-size: 0.8rem;
}

.chart-sub .sub-toolbar button {
    background: var(--card-bg);
    border: 1px solid var(--border);
    color: var(--text-dim);
    padding: 2px 8px;
    border-radius: 2px;
    cursor: pointer;
    font-size: 0.8rem;
}

/* ===== 侧栏 ===== */
.stock-sidebar {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 1rem;
}

.sidebar-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
}

.sidebar-card h3 {
    color: var(--accent);
    font-size: 0.95rem;
    margin-bottom: 0.75rem;
}

.radar-chart { height: 250px; }

.signal-list {
    list-style: none;
    max-height: 250px;
    overflow-y: auto;
}

.signal-list li {
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.85rem;
    display: flex;
    justify-content: space-between;
}

.signal-list .signal-buy { color: var(--red); }
.signal-list .signal-sell { color: var(--green); }

/* ===== 响应式 ===== */
@media (max-width: 768px) {
    .nav-toggle { display: flex; }
    .nav-menu {
        position: absolute;
        top: 56px;
        left: 0;
        right: 0;
        background: var(--card-bg);
        flex-direction: column;
        padding: 1rem;
        gap: 0.5rem;
        display: none;
    }
    .nav-menu.active { display: flex; }

    .stock-sidebar { grid-template-columns: 1fr; }
    .chart-main { height: 300px; }
    .stock-search input { width: 140px; }
}
```

- [ ] **Step 6: 创建 web/static/manifest.json**

```json
{
    "name": "Z哥量化分析平台",
    "short_name": "Z哥量化",
    "description": "zettaranc 交易思维量化分析",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0f0f1e",
    "theme_color": "#1a1a2e",
    "icons": []
}
```

- [ ] **Step 7: 创建 web/static/sw.js**

```javascript
// PWA Service Worker — 缓存静态资源
const CACHE_NAME = "zettaranc-v1";
const CACHE_URLS = ["/", "/static/css/app.css", "/static/js/api.js"];

self.addEventListener("install", (e) => {
    e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CACHE_URLS)));
});

self.addEventListener("fetch", (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request))
    );
});
```

- [ ] **Step 8: 创建 api/web_routes.py — Web 页面路由**

```python
"""Web 页面路由 — Jinja2 模板渲染"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["页面"])

_templates_dir = Path(__file__).parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/stock/{ts_code}", response_class=HTMLResponse)
def stock_page(request: Request, ts_code: str):
    """个股看板"""
    return templates.TemplateResponse(
        "stock/analysis.html",
        {"request": request, "ts_code": ts_code},
    )
```

- [ ] **Step 9: 修改 api/app.py — 挂载静态文件 + 注册 web 路由**

Read `api/app.py`, add after the router imports:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 挂载静态文件
_static_dir = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# 注册 Web 页面路由
from api.web_routes import router as web_router
app.include_router(web_router)
```

- [ ] **Step 10: 写测试**

Create `tests/test_web_routes.py`:

```python
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
```

- [ ] **Step 11: 运行测试**

Run: `python -m pytest tests/test_web_routes.py -v`
Expected: 2 passed

- [ ] **Step 12: Commit**

```bash
git add web/ api/web_routes.py api/app.py tests/test_web_routes.py
git commit -m "feat: add web base framework with Jinja2 templates and PWA"
```

---

## Task 2: API 封装 (api.js) + 个股看板页面

**Files:**
- Create: `web/static/js/api.js`
- Create: `web/templates/stock/analysis.html`

- [ ] **Step 1: 创建 web/static/js/api.js**

```javascript
// API 请求封装
const API = {
    async getStockAnalysis(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}?days=${days}`);
        return res.json();
    },

    async getStockKline(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}/kline?days=${days}`);
        return res.json();
    },

    async getStockSignals(tsCode, days = 120) {
        const res = await fetch(`/api/stock/${tsCode}/signals?days=${days}`);
        return res.json();
    },

    async screener(strategy = "b1", maxStocks = 500) {
        const res = await fetch(`/api/screener?strategy=${strategy}&max_stocks=${maxStocks}`);
        return res.json();
    },

    async getStockScore(tsCode) {
        const res = await fetch(`/api/screener/score/${tsCode}`);
        return res.json();
    },

    async backtest(req) {
        const res = await fetch("/api/backtest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async tuneBacktest(req) {
        const res = await fetch("/api/backtest/tune", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async historicalScreener(req) {
        const res = await fetch("/api/backtest/screener", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async trainingScreen(req) {
        const res = await fetch("/api/training/screen", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async trainingKline(req) {
        const res = await fetch("/api/training/kline", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
        });
        return res.json();
    },

    async diagnosePortfolio(holdings, days = 100) {
        const res = await fetch("/api/portfolio/diagnose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ holdings, days }),
        });
        return res.json();
    },
};
```

- [ ] **Step 2: 创建 web/templates/stock/analysis.html**

```html
{% extends "base.html" %}

{% block title %}{{ ts_code }} — 个股看板{% endblock %}

{% block content %}
<div class="stock-header">
    <div class="stock-title">
        <span id="stock-code">{{ ts_code }}</span>
        <span class="name" id="stock-name"></span>
    </div>
    <div class="stock-search">
        <input type="text" id="code-input" placeholder="输入股票代码" value="{{ ts_code }}">
        <button onclick="loadStock(document.getElementById('code-input').value)">查看</button>
    </div>
</div>

<div class="chart-grid">
    <div id="main-chart" class="chart-main"></div>
    <div class="chart-sub-windows" id="sub-windows"></div>
</div>

<div class="stock-sidebar">
    <div class="sidebar-card">
        <h3>评分雷达</h3>
        <div id="radar-chart" class="radar-chart"></div>
    </div>
    <div class="sidebar-card">
        <h3>战法信号</h3>
        <ul class="signal-list" id="signal-list">
            <li style="color:var(--text-dim)">加载中...</li>
        </ul>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script src="/static/js/charts/kline.js"></script>
<script src="/static/js/charts/indicator.js"></script>
<script src="/static/js/charts/signal.js"></script>
<script src="/static/js/charts/radar.js"></script>
<script src="/static/js/pages/stock.js"></script>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add web/static/js/api.js web/templates/stock/analysis.html
git commit -m "feat: add API client and stock analysis page template"
```

---

## Task 3: K线主图组件 (kline.js)

**Files:**
- Create: `web/static/js/charts/kline.js`

- [ ] **Step 1: 创建 web/static/js/charts/kline.js**

```javascript
// K线主图组件 — ECharts candlestick + 均线 + 信号标注

function createKlineChart(containerId) {
    const chart = echarts.init(document.getElementById(containerId));

    const option = {
        backgroundColor: "transparent",
        animation: false,
        grid: { left: "5%", right: "3%", top: "5%", bottom: "10%" },
        xAxis: {
            type: "category",
            data: [],
            axisLine: { lineStyle: { color: "#2a2a4a" } },
            axisLabel: { color: "#888", fontSize: 10 },
        },
        yAxis: {
            type: "value",
            scale: true,
            axisLine: { lineStyle: { color: "#2a2a4a" } },
            axisLabel: { color: "#888", fontSize: 10 },
            splitLine: { lineStyle: { color: "#1a1a2e" } },
        },
        dataZoom: [
            { type: "inside", start: 60, end: 100 },
            { type: "slider", start: 60, end: 100, height: 20, bottom: 0 },
        ],
        tooltip: {
            trigger: "axis",
            axisPointer: { type: "cross" },
            backgroundColor: "#1a1a2e",
            borderColor: "#2a2a4a",
            textStyle: { color: "#e0e0e0" },
        },
        legend: {
            data: ["K线", "MA5", "MA10", "MA20", "MA60"],
            textStyle: { color: "#888" },
            top: 0,
        },
        series: [
            {
                name: "K线",
                type: "candlestick",
                data: [],
                itemStyle: {
                    color: "#e74c3c",
                    color0: "#00b386",
                    borderColor: "#e74c3c",
                    borderColor0: "#00b386",
                },
            },
            { name: "MA5", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA10", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA20", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
            { name: "MA60", type: "line", data: [], smooth: true, lineStyle: { width: 1 }, symbol: "none" },
        ],
    };

    chart.setOption(option);
    window.addEventListener("resize", () => chart.resize());
    return chart;
}

function updateKlineChart(chart, klines, indicators) {
    if (!klines || klines.length === 0) return;

    const dates = klines.map((k) => k.date);
    const ohlc = klines.map((k) => [k.open, k.close, k.low, k.high]);

    chart.setOption({
        xAxis: { data: dates },
        series: [
            { name: "K线", data: ohlc },
        ],
    });

    // 均线由后端 indicators 提供最新值，前端用 K 线收盘价计算
    const closes = klines.map((k) => k.close);
    const ma = (n) => {
        const result = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < n - 1) { result.push(null); continue; }
            let sum = 0;
            for (let j = i - n + 1; j <= i; j++) sum += closes[j];
            result.push(parseFloat((sum / n).toFixed(2)));
        }
        return result;
    };

    chart.setOption({
        series: [
            {},
            { name: "MA5", data: ma(5) },
            { name: "MA10", data: ma(10) },
            { name: "MA20", data: ma(20) },
            { name: "MA60", data: ma(60) },
        ],
    });
}
```

- [ ] **Step 2: Commit**

```bash
git add web/static/js/charts/kline.js
git commit -m "feat: add K-line chart component with moving averages"
```

---

## Task 4: 通达信式自定义副图组件 (indicator.js)

**Files:**
- Create: `web/static/js/charts/indicator.js`

- [ ] **Step 1: 创建 web/static/js/charts/indicator.js**

```javascript
// 通达信式自定义副图 — 支持多窗口、指标切换、配置存 localStorage

const SUB_INDICATORS = {
    MACD: { name: "MACD", params: { fast: 12, slow: 26, signal: 9 } },
    KDJ: { name: "KDJ", params: { n: 9, m1: 3, m2: 3 } },
    RSI: { name: "RSI", params: { n: 6 } },
    WR: { name: "WR", params: { n: 14 } },
    VOLUME: { name: "VOL", params: {} },
    BOLL: { name: "BOLL", params: { n: 20, k: 2 } },
    DMI: { name: "DMI", params: { n: 14 } },
    OBV: { name: "OBV", params: {} },
};

// 副图默认配置
function getDefaultSubConfig() {
    return {
        windows: [
            { indicator: "VOLUME", params: {} },
            { indicator: "MACD", params: {} },
        ],
    };
}

function loadSubConfig() {
    try {
        const saved = localStorage.getItem("subChartConfig");
        return saved ? JSON.parse(saved) : getDefaultSubConfig();
    } catch {
        return getDefaultSubConfig();
    }
}

function saveSubConfig(config) {
    localStorage.setItem("subChartConfig", JSON.stringify(config));
}

// 创建副图容器
function createSubWindowContainer(parentId, index, indicatorName) {
    const parent = document.getElementById(parentId);
    const div = document.createElement("div");
    div.className = "chart-sub";
    div.id = `sub-chart-${index}`;

    const toolbar = document.createElement("div");
    toolbar.className = "sub-toolbar";

    const select = document.createElement("select");
    for (const key of Object.keys(SUB_INDICATORS)) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = key;
        if (key === indicatorName) opt.selected = true;
        select.appendChild(opt);
    }
    select.addEventListener("change", (e) => {
        const config = loadSubConfig();
        config.windows[index].indicator = e.target.value;
        config.windows[index].params = SUB_INDICATORS[e.target.value].params;
        saveSubConfig(config);
        renderSubWindows(parentId);
    });
    toolbar.appendChild(select);

    const closeBtn = document.createElement("button");
    closeBtn.textContent = "×";
    closeBtn.title = "删除副图";
    closeBtn.addEventListener("click", () => {
        const config = loadSubConfig();
        if (config.windows.length > 1) {
            config.windows.splice(index, 1);
            saveSubConfig(config);
            renderSubWindows(parentId);
        }
    });
    toolbar.appendChild(closeBtn);

    div.appendChild(toolbar);
    parent.appendChild(div);
    return div;
}

// 添加副图按钮
function createAddSubButton(parentId) {
    const parent = document.getElementById(parentId);
    const btn = document.createElement("button");
    btn.textContent = "+ 添加副图";
    btn.style.cssText = "background:var(--card-bg);border:1px solid var(--border);color:var(--text-dim);padding:4px 12px;border-radius:4px;cursor:pointer;margin-top:4px;";
    btn.addEventListener("click", () => {
        const config = loadSubConfig();
        if (config.windows.length < 3) {
            config.windows.push({ indicator: "RSI", params: SUB_INDICATORS.RSI.params });
            saveSubConfig(config);
            renderSubWindows(parentId);
        }
    });
    parent.appendChild(btn);
}

// 渲染所有副图
function renderSubWindows(parentId) {
    const parent = document.getElementById(parentId);
    parent.innerHTML = "";
    const config = loadSubConfig();

    const charts = [];
    config.windows.forEach((win, i) => {
        const container = createSubWindowContainer(parentId, i, win.indicator);
        const chart = echarts.init(container);
        charts.push({ chart, indicator: win.indicator });
    });

    createAddSubButton(parentId);

    window.addEventListener("resize", () => charts.forEach((c) => c.chart.resize()));
    return charts;
}

// 计算指标数据
function calcIndicator(indicator, klines, indicatorsSnapshot) {
    if (!klines || klines.length === 0) return {};

    const closes = klines.map((k) => k.close);
    const vols = klines.map((k) => k.volume);
    const highs = klines.map((k) => k.high);
    const lows = klines.map((k) => k.low);
    const dates = klines.map((k) => k.date);

    if (indicator === "VOLUME") {
        return {
            dates,
            series: [
                {
                    name: "成交量",
                    type: "bar",
                    data: vols.map((v, i) => ({
                        value: v,
                        itemStyle: { color: klines[i].close >= klines[i].open ? "#e74c3c" : "#00b386" },
                    })),
                },
            ],
        };
    }

    if (indicator === "MACD") {
        // EMA 计算
        const ema = (n) => {
            const result = [];
            let prev = closes[0];
            for (let i = 0; i < closes.length; i++) {
                prev = (closes[i] * 2 + prev * (n - 1)) / (n + 1);
                result.push(prev);
            }
            return result;
        };
        const ema12 = ema(12);
        const ema26 = ema(26);
        const dif = ema12.map((v, i) => v - ema26[i]);
        const dea = dif.map((v, i) => (i === 0 ? v : (dif.slice(0, i + 1).reduce((a, b) => a + b, 0) / (i + 1))));
        const macd = dif.map((v, i) => 2 * (v - dea[i]));
        return {
            dates,
            series: [
                { name: "DIF", type: "line", data: dif, symbol: "none", lineStyle: { width: 1 } },
                { name: "DEA", type: "line", data: dea, symbol: "none", lineStyle: { width: 1 } },
                {
                    name: "MACD",
                    type: "bar",
                    data: macd.map((v) => ({
                        value: v,
                        itemStyle: { color: v >= 0 ? "#e74c3c" : "#00b386" },
                    })),
                },
            ],
        };
    }

    if (indicator === "KDJ") {
        let k = 50, d = 50;
        const kArr = [], dArr = [], jArr = [];
        for (let i = 0; i < closes.length; i++) {
            const hh = Math.max(...highs.slice(Math.max(0, i - 8), i + 1));
            const ll = Math.min(...lows.slice(Math.max(0, i - 8), i + 1));
            const rsv = hh === ll ? 0 : (closes[i] - ll) / (hh - ll) * 100;
            k = (2 / 3) * k + (1 / 3) * rsv;
            d = (2 / 3) * d + (1 / 3) * k;
            kArr.push(k);
            dArr.push(d);
            jArr.push(3 * k - 2 * d);
        }
        return {
            dates,
            series: [
                { name: "K", type: "line", data: kArr, symbol: "none", lineStyle: { width: 1 } },
                { name: "D", type: "line", data: dArr, symbol: "none", lineStyle: { width: 1 } },
                { name: "J", type: "line", data: jArr, symbol: "none", lineStyle: { width: 1, color: "#e94560" } },
            ],
        };
    }

    if (indicator === "RSI") {
        const rsi = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 6) { rsi.push(50); continue; }
            let gain = 0, loss = 0;
            for (let j = i - 5; j <= i; j++) {
                const diff = closes[j] - closes[j - 1];
                if (diff > 0) gain += diff;
                else loss -= diff;
            }
            rsi.push(loss === 0 ? 100 : 100 - 100 / (1 + gain / loss));
        }
        return {
            dates,
            series: [{ name: "RSI6", type: "line", data: rsi, symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    if (indicator === "WR") {
        const wr = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 13) { wr.push(50); continue; }
            const hh = Math.max(...highs.slice(i - 13, i + 1));
            const ll = Math.min(...lows.slice(i - 13, i + 1));
            wr.push(hh === ll ? 50 : (hh - closes[i]) / (hh - ll) * -100);
        }
        return {
            dates,
            series: [{ name: "WR", type: "line", data: wr, symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    if (indicator === "BOLL") {
        const ma20 = [], upper = [], lower = [];
        for (let i = 0; i < closes.length; i++) {
            if (i < 19) { ma20.push(null); upper.push(null); lower.push(null); continue; }
            const slice = closes.slice(i - 19, i + 1);
            const avg = slice.reduce((a, b) => a + b, 0) / 20;
            const std = Math.sqrt(slice.reduce((s, v) => s + (v - avg) ** 2, 0) / 20);
            ma20.push(avg);
            upper.push(avg + 2 * std);
            lower.push(avg - 2 * std);
        }
        return {
            dates,
            series: [
                { name: "上轨", type: "line", data: upper, symbol: "none", lineStyle: { width: 1 } },
                { name: "中轨", type: "line", data: ma20, symbol: "none", lineStyle: { width: 1 } },
                { name: "下轨", type: "line", data: lower, symbol: "none", lineStyle: { width: 1 } },
            ],
        };
    }

    if (indicator === "OBV") {
        const obv = [0];
        for (let i = 1; i < closes.length; i++) {
            const prev = obv[i - 1];
            if (closes[i] > closes[i - 1]) obv.push(prev + vols[i]);
            else if (closes[i] < closes[i - 1]) obv.push(prev - vols[i]);
            else obv.push(prev);
        }
        return {
            dates,
            series: [{ name: "OBV", type: "line", data: obv, symbol: "none", lineStyle: { width: 1 } }],
        };
    }

    return { dates, series: [] };
}

// 更新副图数据
function updateSubCharts(subCharts, klines, indicators) {
    subCharts.forEach(({ chart, indicator }) => {
        const data = calcIndicator(indicator, klines, indicators);
        chart.setOption({
            backgroundColor: "transparent",
            animation: false,
            grid: { left: "5%", right: "3%", top: "10%", bottom: "15%" },
            xAxis: {
                type: "category",
                data: data.dates || [],
                axisLine: { lineStyle: { color: "#2a2a4a" } },
                axisLabel: { color: "#888", fontSize: 9 },
            },
            yAxis: {
                type: "value",
                scale: true,
                axisLine: { lineStyle: { color: "#2a2a4a" } },
                axisLabel: { color: "#888", fontSize: 9 },
                splitLine: { lineStyle: { color: "#1a1a2e" } },
            },
            tooltip: {
                trigger: "axis",
                backgroundColor: "#1a1a2e",
                borderColor: "#2a2a4a",
                textStyle: { color: "#e0e0e0" },
            },
            legend: { textStyle: { color: "#888", fontSize: 9 }, top: 0 },
            series: data.series || [],
        });
    });
}
```

- [ ] **Step 2: Commit**

```bash
git add web/static/js/charts/indicator.js
git commit -m "feat: add Tongdaxin-style customizable sub-chart indicators"
```

---

## Task 5: 信号标注 + 评分雷达 + 个股页交互

**Files:**
- Create: `web/static/js/charts/signal.js`
- Create: `web/static/js/charts/radar.js`
- Create: `web/static/js/pages/stock.js`

- [ ] **Step 1: 创建 web/static/js/charts/signal.js**

```javascript
// 信号标注 — 在 K 线主图上标记买卖点

function addSignalsToChart(chart, klines, signals) {
    if (!signals || signals.length === 0) return;

    const dateSet = new Set(klines.map((k) => k.date));
    const buyPoints = [];
    const sellPoints = [];

    signals.forEach((sig) => {
        if (!dateSet.has(sig.trade_date)) return;
        if (sig.action === "BUY") {
            buyPoints.push({
                coord: [sig.trade_date, sig.price],
                itemStyle: { color: "#e74c3c" },
                label: { show: true, formatter: sig.strategy, color: "#e74c3c", fontSize: 9, position: "bottom" },
            });
        } else if (sig.action === "SELL") {
            sellPoints.push({
                coord: [sig.trade_date, sig.price],
                itemStyle: { color: "#00b386" },
                label: { show: true, formatter: sig.strategy, color: "#00b386", fontSize: 9, position: "top" },
            });
        }
    });

    chart.setOption({
        series: [
            {},
            { markPoint: { data: buyPoints, symbol: "triangle", symbolSize: 12 } },
        ],
    });

    // SELL 信号加到第二个 series
    if (sellPoints.length > 0) {
        const currentSeries = chart.getOption().series;
        if (currentSeries.length > 2) {
            currentSeries[2].markPoint = { data: sellPoints, symbol: "pin", symbolSize: 12 };
            chart.setOption({ series: currentSeries });
        }
    }
}

function renderSignalList(containerId, signals) {
    const ul = document.getElementById(containerId);
    if (!signals || signals.length === 0) {
        ul.innerHTML = '<li style="color:var(--text-dim)">暂无信号</li>';
        return;
    }
    ul.innerHTML = signals
        .map((s) => {
            const cls = s.action === "BUY" ? "signal-buy" : s.action === "SELL" ? "signal-sell" : "";
            return `<li class="${cls}">
                <span>${s.trade_date} ${s.strategy}</span>
                <span>${s.action} ${s.price.toFixed(2)}</span>
            </li>`;
        })
        .join("");
}
```

- [ ] **Step 2: 创建 web/static/js/charts/radar.js**

```javascript
// 评分雷达图

function createRadarChart(containerId) {
    const chart = echarts.init(document.getElementById(containerId));

    chart.setOption({
        backgroundColor: "transparent",
        radar: {
            indicator: [
                { name: "综合", max: 100 },
                { name: "B1", max: 100 },
                { name: "趋势", max: 100 },
                { name: "量价", max: 100 },
                { name: "风险", max: 100 },
            ],
            axisName: { color: "#888", fontSize: 11 },
            splitLine: { lineStyle: { color: "#2a2a4a" } },
            splitArea: { areaStyle: { color: ["#1a1a2e", "#0f0f1e"] } },
            axisLine: { lineStyle: { color: "#2a2a4a" } },
        },
        series: [{
            type: "radar",
            data: [{
                value: [0, 0, 0, 0, 0],
                areaStyle: { color: "rgba(233,69,96,0.3)" },
                lineStyle: { color: "#e94560", width: 2 },
            }],
        }],
    });

    window.addEventListener("resize", () => chart.resize());
    return chart;
}

function updateRadarChart(chart, score) {
    if (!score) return;
    chart.setOption({
        series: [{
            data: [{
                value: [score.score, score.b1_score, score.trend_score, score.volume_score, score.risk_score],
                name: score.name || score.ts_code,
            }],
        }],
    });
}
```

- [ ] **Step 3: 创建 web/static/js/pages/stock.js**

```javascript
// 个股看板交互逻辑

let mainChart = null;
let subCharts = [];
let radarChart = null;

async function loadStock(tsCode) {
    if (!tsCode) return;

    // 更新 URL（不刷新页面）
    history.pushState({}, "", `/stock/${tsCode}`);
    document.getElementById("stock-code").textContent = tsCode;

    const data = await API.getStockAnalysis(tsCode, 120);

    document.getElementById("stock-name").textContent = data.name || "";

    // 更新主图
    if (!mainChart) mainChart = createKlineChart("main-chart");
    updateKlineChart(mainChart, data.klines, data.indicators);

    // 信号标注
    addSignalsToChart(mainChart, data.klines, data.signals);
    renderSignalList("signal-list", data.signals);

    // 副图
    subCharts = renderSubWindows("sub-windows");
    updateSubCharts(subCharts, data.klines, data.indicators);

    // 雷达图
    if (!radarChart) radarChart = createRadarChart("radar-chart");
    updateRadarChart(radarChart, data.score);
}

// 页面加载
document.addEventListener("DOMContentLoaded", () => {
    const tsCode = document.getElementById("stock-code").textContent;
    loadStock(tsCode);
});

// 搜索框回车
document.getElementById("code-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        loadStock(e.target.value);
    }
});
```

- [ ] **Step 4: 运行 Web 路由测试**

Run: `python -m pytest tests/test_web_routes.py -v`
Expected: 2 passed

- [ ] **Step 5: 手动验证（启动服务器）**

```bash
python -c "import uvicorn; from api.app import app; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

打开浏览器访问 `http://127.0.0.1:8000/` 和 `http://127.0.0.1:8000/stock/600519.SH`，确认页面能加载、ECharts 渲染。

- [ ] **Step 6: Commit**

```bash
git add web/static/js/charts/signal.js web/static/js/charts/radar.js web/static/js/pages/stock.js
git commit -m "feat: add signal markers, radar chart, and stock page interaction"
```

---

## Task 6: 最终验证

**Files:**
- Run: all tests

- [ ] **Step 1: 运行全部测试**

Run: `python -m pytest tests/ --ignore=tests/test_intent_router.py --ignore=tests/test_intent_chat.py --ignore=tests/test_notifier.py --ignore=tests/test_quality_check.py --ignore=tests/test_rate_limiter.py --ignore=tests/test_tushare_client.py --ignore=tests/test_backtest_scorer.py --ignore=tests/test_data_sync_extensions.py --ignore=tests/test_self_optimizer_integration.py --tb=short 2>&1 | Select-Object -Last 5`
Expected: All pass, no new failures

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: complete Plan 3 - web base + stock analysis page"
```
