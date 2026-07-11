# Web 可视化 + 代码重构 + 选股训练 设计

> **状态**：Draft v1 · 待用户复核
> **创建日期**：2026-07-12
> **作者**：Claude (brainstorming with chenlei)
> **目标分支**：`feature/web-refactor`（从 `main` 拉出）
> **预计工作量**：14-19 天

---

## 1. 背景与目标

### 1.1 现状

zettaranc-skill 当前是一个纯 Python CLI 工具 + AI Skill 文件的混合体：

- `modules/` 包含 60+ 技术指标、30+ 战法识别、选股评分、回测引擎等
- `knowledge/` 包含 14+ 篇交易体系知识文件
- `SKILL.md` 作为 AI 角色扮演协议
- 无 Web 界面，无移动端支持
- `modules/` 目录职责混杂，`screener.py`、`backtest.py` 等单文件过大

### 1.2 目标

1. **代码重构**：将 `modules/` 重组为 `core/` 分层架构，`knowledge/` 纳入 Core 层作为战法权威定义源
2. **Web 可视化**：新增 FastAPI + Jinja2 + ECharts 响应式 Web 应用，5 个页面，支持移动端
3. **选股训练**：新增交互式模拟交易训练器，用户选日期+战法筛选+模拟买卖+结算统计

### 1.3 不在范围

- 不引入 Node/npm 工具链
- 不做用户认证/登录
- 不做实时行情推送（只读本地 SQLite 缓存）
- 不做云端部署配置（本地运行）
- 不做 ML 模型训练

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────┐
│  Web 层 (web/)                                        │
│  Jinja2 模板 + ECharts + PWA（响应式）                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐      │
│  │个股看板│ │选股页 │ │回测页 │ │选股训练│ │持仓页│      │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘      │
├─────┼────────┼────────┼────────┼────────┼──────────┤
│  API 层 (api/)  FastAPI 路由                           │
│  /api/stock  /api/screener  /api/backtest             │
│  /api/training  /api/portfolio                       │
├─────┼────────┼────────┼────────┼────────┼──────────┤
│  Core 层 (core/)                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │knowledge/│ │indicators/│ │strategies/│            │
│  │交易体系源 │ │60+ 指标   │ │30+ 战法   │            │
│  │(权威定义) │ │           │ │← 以knowledge为准│      │
│  └──────────┘ └──────────┘ └──────────┘             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
│  │domain/   │ │screener/  │ │backtest/  │            │
│  │Profile   │ │评分体系    │ │回测+调优   │            │
│  └──────────┘ └──────────┘ └──────────┘             │
│  ┌──────────┐                                         │
│  │data_access│ 只读 SQLite 数据访问层                  │
│  └──────────┘                                         │
├──────────────────────────────────────────────────────┤
│  数据层  data/stock_data.db（只读 SQLite 缓存）        │
└──────────────────────────────────────────────────────┘
```

### 2.1 数据流

浏览器请求 → FastAPI 路由 → 调用 core/ 领域逻辑 → 读取 SQLite 缓存 → 返回 JSON → Jinja2 渲染 + ECharts 图表

### 2.2 knowledge 与 strategies 对应关系

`knowledge/` 纳入 Core 层，作为交易体系的**权威定义源**。`strategies/` 战法引擎以 knowledge 文件为准——knowledge 定义"什么是 B1/少妇/麒麟会"，strategies 实现"如何检测它们"。

| knowledge 文件 | strategies 实现 |
|---|---|
| `trading-core.md` (B1/B2/B3/少妇/四块砖) | `base_strategies.py` + `compound_strategies.py` |
| `indicators.md` (麒麟会/三波理论) | `kirin_detector.py` + `wave_theory.py` |
| `sell-discipline.md` (S1/S2/S3/防卖飞) | `sell_signals.py` |
| `advanced-patterns.md` (长安/对称VA) | `compound_strategies.py` |
| `trend-lines.md` (双线/牛绳) | `price_patterns/` |
| `position-management.md` (曼城/防火墙) | `screener/` 评分参考 |

### 2.3 启动方式

```bash
uvicorn api.app:app --reload --port 8000
# 或注册到 zt 命令
zt web  # 启动 Web 服务
```

单进程，端口 8000。

---

## 3. Core 层重构

### 3.1 目录迁移

现有 `modules/` → `core/`，按职责重组：

```
core/
├── domain/
│   └── profile.py          # 从 modules/profile.py 迁入
├── indicators/             # 从 modules/indicators/ 迁入（整体移动）
│   ├── core.py
│   ├── price_patterns/
│   ├── volume_patterns.py
│   ├── wave_theory.py
│   ├── kirin_detector.py
│   └── data_layer.py
├── strategies/            # 从 modules/strategies/ 迁入
│   ├── core.py
│   ├── base_strategies.py
│   ├── compound_strategies.py
│   ├── sell_signals.py
│   └── orchestrator.py
├── screener/              # 从 modules/screener.py 拆为包
│   ├── __init__.py         # 导出 score_stock
│   ├── trend_score.py      # 趋势评分
│   ├── volume_score.py     # 量价评分
│   ├── risk_score.py       # 风险评分
│   └── b1_score.py         # B1 评分
├── backtest/              # 从 modules/backtest.py 拆为包 + 新增调优
│   ├── __init__.py         # 导出 run_backtest
│   ├── engine.py          # 现有回测引擎
│   ├── param_tuner.py     # 新增：参数调优（网格搜索）
│   └── historical_screener.py  # 新增：历史选股筛选
├── knowledge/             # 从项目根 knowledge/ 迁入
│   └── (现有 .md 文件)
├── database.py            # 从 modules/database.py 迁入
└── data_access.py         # 新增：只读数据访问层
```

### 3.2 import 路径更新

全局替换：
- `from modules.` → `from core.`
- `import modules.` → `import core.`
- 测试中 `from modules.` → `from core.`

### 3.3 保留在 modules/ 的部分

- `modules/tushare_client.py` — 数据同步不属于 core 领域逻辑
- `modules/data_sync.py` — 同上
- `modules/cli.py` — CLI 入口
- `modules/trade_*.py` — 交易记录 CRUD（数据管理类）

### 3.4 screener 拆分

现有 `screener.py` ~350 行单文件，拆为 4 个评分模块，每个独立可测试：

- `trend_score.py` — 趋势评分（双线、均线排列、动量）
- `volume_score.py` — 量价评分（量比、缩量/放量）
- `risk_score.py` — 风险评分（位置、波动、回撤）
- `b1_score.py` — B1 机会评分（J 值、背离、缩量回调）

### 3.5 backtest 扩展

现有 `backtest.py` 只有回测引擎，新增：

- `param_tuner.py` — 对战法参数做网格搜索（如 B1 的 J 值阈值、量比阈值），输出最优参数 + 胜率报告
- `historical_screener.py` — 扫描全市场历史数据，按 Z 哥评分体系筛选股票池，支持时间段回放

---

## 4. API 层设计

### 4.1 目录结构

```
api/
├── app.py                 # FastAPI 应用入口 + 静态文件挂载
├── deps.py                # 依赖注入（DB 连接、核心服务实例）
├── schemas.py             # Pydantic 响应模型
└── routes/
    ├── stock.py           # 个股分析
    ├── screener.py        # 选股筛选
    ├── backtest.py        # 回测 + 调优
    ├── training.py        # 选股训练（历史筛选 + 行情数据供给）
    └── portfolio.py       # 持仓诊断
```

### 4.2 路由设计

| 路由 | 方法 | 参数 | 返回 | 用途 |
|------|------|------|------|------|
| `/api/stock/{ts_code}` | GET | ts_code, days=120 | StockAnalysis JSON | 个股指标+战法信号+评分 |
| `/api/stock/{ts_code}/kline` | GET | ts_code, days=120 | KLine JSON | K线数据（ECharts格式） |
| `/api/stock/{ts_code}/signals` | GET | ts_code, days=120 | Signal[] JSON | 战法信号列表 |
| `/api/screener` | GET | date, min_score, strategy | StockScore[] JSON | 选股结果列表 |
| `/api/screener/score/{ts_code}` | GET | ts_code | StockScore JSON | 单股评分详情 |
| `/api/backtest` | POST | strategy, params, date_range | BacktestResult JSON | 单次回测 |
| `/api/backtest/tune` | POST | strategy, param_grid, date_range | TuneResult JSON | 参数调优 |
| `/api/backtest/screener` | POST | date_range, criteria | ScreenResult JSON | 历史选股筛选 |
| `/api/training/screen` | POST | date, strategies, min_score | StockScore[] JSON | 当日战法筛选 |
| `/api/trading/kline` | GET | ts_code, start_date, end_date | KLine JSON | 训练用行情数据 |
| `/api/portfolio/diagnose` | POST | holdings[] | Diagnosis[] JSON | 持仓诊断 |
| `/api/portfolio/review` | POST | trades[] | ReviewResult JSON | 交割单复盘 |

### 4.3 Pydantic schemas

```python
class KLineItem(BaseModel):
    date: str
    open: float
    close: float
    low: float
    high: float
    volume: float
    pct_chg: float

class SignalItem(BaseModel):
    trade_date: str
    strategy: str
    action: str
    confidence: float
    price: float
    note: str

class StockAnalysis(BaseModel):
    profile: StockProfile
    klines: list[KLineItem]
    signals: list[SignalItem]
    score: StockScore

class BacktestResult(BaseModel):
    total_trades: int
    win_rate: float
    avg_profit: float
    max_drawdown: float
    trades: list[Trade]

class TuneResult(BaseModel):
    best_params: dict
    best_score: float
    param_grid_results: list[dict]

class TrainingScreenRequest(BaseModel):
    date: str
    strategies: list[str]
    min_score: float = 0

class TrainingScreenResponse(BaseModel):
    results: list[StockScore]
    date: str
```

### 4.4 依赖注入

`deps.py` 提供 `get_db()` 上下文管理器和 `get_indicator_service()` 等工厂函数，路由通过 `Depends()` 注入，方便测试 mock。

---

## 5. Web 层设计

### 5.1 目录结构

```
web/
├── templates/
│   ├── base.html              # 基础布局（响应式 nav + 内容区）
│   ├── stock/
│   │   └── analysis.html      # 个股看板
│   ├── screener/
│   │   └── result.html        # 选股结果
│   ├── backtest/
│   │   └── run.html           # 回测执行页
│   ├── training/
│   │   └── training.html      # 选股训练
│   └── portfolio/
│       ├── diagnose.html      # 持仓诊断
│       └── review.html        # 交割单复盘
├── static/
│   ├── css/
│   │   └── app.css            # 响应式样式（移动端优先）
│   ├── js/
│   │   ├── charts/
│   │   │   ├── kline.js        # K线图组件（ECharts）
│   │   │   ├── indicator.js    # 副图指标（MACD/KDJ，通达信式自定义）
│   │   │   ├── signal.js       # 信号标注
│   │   │   └── radar.js        # 评分雷达图
│   │   ├── pages/
│   │   │   ├── stock.js         # 个股页交互
│   │   │   ├── screener.js      # 选股页交互
│   │   │   ├── backtest.js      # 回测页交互
│   │   │   ├── training.js      # 选股训练交互
│   │   │   └── portfolio.js     # 持仓页交互
│   │   └── api.js              # fetch 封装
│   └── manifest.json          # PWA manifest（可安装到手机桌面）
└── pwa_sw.js                  # Service Worker（离线缓存）
```

### 5.2 页面功能

#### 5.2.1 个股看板（`/stock/{ts_code}`）

- **主图**：K线 + 均线 + 双线趋势 + 信号标注（买卖点用图标标记）
- **副图（通达信式自定义）**：
  - 预设指标：MACD / KDJ / RSI / WR / 量比 / 布林带 / DMI / OBV
  - 支持多副图窗口（最多 3 个），每个窗口可选指标
  - 支持多指标叠加
  - 配置可保存到 localStorage，下次访问恢复
- **侧栏**：评分雷达图（趋势/量价/风险/B1）+ 战法匹配列表
- **响应式**：手机端主副图上下排列，侧栏折叠为底部 tab

#### 5.2.2 选股页（`/screener`）

- 筛选条件栏（日期、最低评分、战法类型）
- 结果表格（代码/名称/评分/匹配战法/涨跌幅），可排序
- 点击行 → 跳转个股看板
- 手机端：表格转为卡片列表

#### 5.2.3 回测页（`/backtest`）

- 表单：选战法 → 设参数 → 选时间段 → 执行
- 结果：胜率 / 平均收益 / 最大回撤 + 交易明细表 + 收益曲线图（ECharts）
- 参数调优：参数网格表 → 热力图展示各参数组合的胜率

#### 5.2.4 选股训练（`/training`）

交互式模拟交易训练器：

```
┌─────────────────────────────────────────┐
│ Step 1: 选日期                           │
│   [日期选择器]  ← 选某一天作为起点        │
│                                          │
│ Step 2: 战法筛选                         │
│   [战法多选] [最低评分] [筛选按钮]        │
│   → 当日符合条件的股票列表（表格）        │
│                                          │
│ Step 3: 模拟交易                         │
│   点击股票 → [买入价] [数量] [买入]      │
│   持仓列表（可卖出）                     │
│                                          │
│ Step 4: 结算                             │
│   [选择结算日期] [结算按钮]              │
│   → 胜率 / 平均收益 / 最大回撤           │
│   → 交易明细表                           │
│   → 收益曲线图（ECharts）                │
└─────────────────────────────────────────┘
```

**核心交互**：
- 选某一天 → 用战法筛选当天符合条件的股票 → 模拟买入 → 选后续某天卖出 → 系统结算统计
- 支持多笔交易，累积统计
- 收益曲线图展示账户净值变化
- 手机端：步骤式布局，每步一屏

**回测 vs 选股训练区别**：
- **回测**：对某战法做批量历史回测，验证策略本身的有效性（参数调优导向）
- **选股训练**：用户手动选某一天、手动筛股、手动买卖，练习交易决策能力（训练导向）

#### 5.2.5 持仓诊断（`/portfolio`）

- 诊断：输入持仓代码 → 逐股诊断报告（战法匹配/卖出信号/止损价）
- 复盘：粘贴交割单 → 逐笔点评 + 统计图表

### 5.3 移动端适配

- CSS Grid + Flexbox 响应式布局
- ECharts `resize` 事件监听
- PWA manifest 支持添加到桌面，全屏模式
- Service Worker 缓存静态资源（离线可看历史结果）

### 5.4 通达信式副图技术细节

```javascript
// 副图配置结构（存 localStorage）
{
  windows: [
    { indicator: 'MACD', params: { fast: 12, slow: 26, signal: 9 } },
    { indicator: 'KDJ', params: { n: 9, m1: 3, m2: 3 } },
    { indicator: 'VOLUME', params: {} }
  ],
  overlays: {  // 主图叠加
    ma: [5, 20, 60],
    boll: true,
    trendLines: true
  }
}
```

- ECharts `grid` 数组动态生成，每个副图一个 grid
- 指标数据由后端 `/api/stock/{ts_code}` 返回，前端按配置渲染
- 用户可通过下拉菜单切换/添加/删除副图指标
- 配置变更自动保存到 localStorage

---

## 6. 数据层与依赖

### 6.1 数据访问层

新增 `core/data_access.py`，统一只读查询入口：

```python
class DataAccess:
    """只读 SQLite 数据访问层，Web/回测/训练共用"""
    def get_klines(ts_code, days) -> list[DailyData]
    def get_klines_by_range(ts_code, start_date, end_date) -> list[DailyData]
    def get_indicator_cache(ts_code, date) -> IndicatorResult | None
    def get_stock_list() -> list[StockBasic]
    def get_signals_by_date(date, strategy) -> list[StrategySignal]
    def get_trade_records() -> list[TradeRecord]
```

- 所有方法只读，不写数据库
- 缓存查询结果（functools.lru_cache）
- Web 层和训练页的模拟交易不写入数据库，状态保存在 localStorage

### 6.2 模拟交易状态管理

选股训练页的买入卖出状态保存：

| 方案 | 说明 | 选择 |
|------|------|------|
| 前端 localStorage | 交易记录存浏览器，刷新不丢，换设备丢 | ✅ |
| 服务端 session | 需后端存储，复杂 | ❌ |
| 数据库表 | 违背只读原则 | ❌ |

用 localStorage：前端管理交易状态，结算时前端计算统计指标 + 画收益曲线，后端只提供历史行情数据。

### 6.3 新增依赖

```
# requirements.txt 新增
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
jinja2>=3.1.0
python-multipart>=0.0.6
```

ECharts 通过 CDN 引入（不装 npm）。PWA manifest + Service Worker 纯静态文件。

### 6.4 测试策略

| 层 | 测试 | 工具 |
|----|------|------|
| core/ | 现有 pytest 测试迁移，import 路径更新 | pytest |
| api/ | 每个路由用 TestClient 测试 | httpx + pytest |
| web/ | 模板渲染冒烟测试 | pytest + Jinja2 |
| 集成 | 端到端：API → core → DB | pytest fixture |

---

## 7. 实施顺序与风险

### 7.1 实施阶段

| 阶段 | 内容 | 预计工作量 |
|------|------|-----------|
| **P1: Core 重构** | `modules/` → `core/` 迁移、import 更新、screener 拆分、现有测试通过 | 2-3 天 |
| **P2: Backtest 扩展** | `param_tuner.py` + `historical_screener.py` + 测试 | 1-2 天 |
| **P3: API 层** | FastAPI 应用 + 5 个路由模块 + Pydantic schemas + 测试 | 2-3 天 |
| **P4: Web 基础** | base 模板 + 静态资源 + 响应式布局 + PWA | 1 天 |
| **P5: 个股看板** | K线主图 + 自定义副图(通达信式) + 信号标注 + 雷达图 | 2-3 天 |
| **P6: 选股页** | 筛选表单 + 结果表格 + 卡片模式 | 1 天 |
| **P7: 回测页** | 原回测功能 Web 化 + 收益曲线图 + 参数调优热力图 | 1-2 天 |
| **P8: 选股训练** | 日期选择+战法筛选+模拟交易+结算统计+收益曲线 | 2-3 天 |
| **P9: 持仓页** | 持仓诊断 + 交割单复盘 | 1-2 天 |
| **P10: 集成测试** | 端到端测试 + 移动端验证 | 1 天 |

总计约 14-19 天，按 P1-P10 顺序执行。

### 7.2 关键风险

| 风险 | 应对 |
|------|------|
| import 路径迁移导致大面积测试失败 | P1 用脚本批量替换 + 全量跑 pytest |
| 通达信式副图交互复杂度高 | P5 先实现 2 个预设指标切换，多窗口叠加作为后续迭代 |
| 选股训练前端状态管理复杂 | 用 localStorage + 前端计算，后端纯数据供给 |
| SQLite 只读缓存数据不全 | Web 层对缺失数据做友好降级（显示"数据未同步"） |

---

## 8. 文件清单

### 8.1 新增文件

```
core/data_access.py
core/screener/__init__.py
core/screener/trend_score.py
core/screener/volume_score.py
core/screener/risk_score.py
core/screener/b1_score.py
core/backtest/param_tuner.py
core/backtest/historical_screener.py
api/app.py
api/deps.py
api/schemas.py
api/routes/stock.py
api/routes/screener.py
api/routes/backtest.py
api/routes/training.py
api/routes/portfolio.py
web/templates/base.html
web/templates/stock/analysis.html
web/templates/screener/result.html
web/templates/backtest/run.html
web/templates/training/training.html
web/templates/portfolio/diagnose.html
web/templates/portfolio/review.html
web/static/css/app.css
web/static/js/charts/kline.js
web/static/js/charts/indicator.js
web/static/js/charts/signal.js
web/static/js/charts/radar.js
web/static/js/pages/stock.js
web/static/js/pages/screener.js
web/static/js/pages/backtest.js
web/static/js/pages/training.js
web/static/js/pages/portfolio.js
web/static/js/api.js
web/static/manifest.json
web/pwa_sw.js
tests/test_api_stock.py
tests/test_api_screener.py
tests/test_api_backtest.py
tests/test_api_training.py
tests/test_api_portfolio.py
tests/test_data_access.py
tests/test_param_tuner.py
tests/test_historical_screener.py
```

### 8.2 迁移文件（modules/ → core/）

```
modules/profile.py          → core/domain/profile.py
modules/indicators/         → core/indicators/（整体移动）
modules/strategies/         → core/strategies/（整体移动）
modules/screener.py         → core/screener/（拆分为包）
modules/backtest.py         → core/backtest/engine.py
modules/database.py         → core/database.py
knowledge/                  → core/knowledge/（整体移动）
```

### 8.3 保留在 modules/

```
modules/tushare_client.py
modules/data_sync.py
modules/cli.py
modules/trade_parser.py
modules/trade_manager.py
modules/trade_reviewer.py
modules/setup_wizard.py
modules/report.py
modules/intent_router.py
modules/intent_chat.py
modules/knowledge_retriever.py
modules/llm_providers.py
modules/watchlist.py
modules/portfolio_diagnosis.py
modules/backtest_six_step.py
```
