# zettaranc-skill · Agent 指南

> 本文件面向 AI 编程 Agent。阅读前请确认你已通读本文件，再操作代码或文档。
> 版本：v4.0.0 ｜ 更新日期：2026-07-15 ｜ 与实际代码结构对齐

---

## 项目概述

本项目是一个 **AI Skill（思维框架蒸馏包）+ 真实数据量化工具 + Web 看板** 的混合体。

核心目标：将 B 站 UP 主 / 前阳光私募冠军基金经理 zettaranc（万千）的投资思维框架、决策启发式和表达 DNA，封装为可供 Claude Code / Cursor 等 AI 工具调用的 Skill 文件（`SKILL.md`），同时提供基于真实 Tushare 行情数据的 Python 数据层、FastAPI 接口层与 React 可视化看板。

- **核心交付物**：`SKILL.md`（可直接被 AI 工具加载的角色扮演协议）
- **数据层**：`core/`（领域计算）+ `modules/`（CLI/数据同步/交易/意图）+ SQLite 数据库 + Tushare API（JNB 模式）
- **接口层**：`api/`（FastAPI，`/api/v1` 前缀，11 路由）
- **展示层**：`frontend/`（React + Vite + ECharts 看板，8 页面）；`web/`（旧 Jinja 模板，已被取代但保留兼容）
- **语料基础**：约 467 篇直播/付费课整理文章（~200 万字）+ 13 个 ztalk 视频 transcript（~12.7 万字）+ 9 篇交易心理系列（~3.3 万字）+ 15 篇 2026.4-5 月新增文章
- **许可证**：MIT
- **版本**：当前 v4.0.0，采用语义化版本

### 双模式架构

| 模式 | 环境变量 | 说明 |
|------|---------|------|
| **JNB 模式** | `DATA_MODE=jnb` | 接入 Tushare 真实行情，具备实时数据查询、技术指标计算、战法识别能力 |
| **普通小万** | `DATA_MODE=websearch` | 纯 LLM 对话，不走任何外部数据接口 |

架构分层（v4.0.0）：

```
Tushare API → data_sync → SQLite (data/stock_data.db ~1GB)
                                    ↓
                        core/（领域计算层）
                        ├─ indicators/      60+ 技术指标
                        ├─ strategies/      30+ 战法识别
                        ├─ screener/        选股评分（5 子模块）
                        ├─ backtest/        回测引擎 + 历史回测 + 参数调优
                        ├─ knowledge/       29 篇知识文档
                        ├─ data_access.py   只读 DataAccess 层
                        └─ domain/          StockProfile 数据类
                                    ↓
                modules/（CLI / 数据同步 / 交易 / 意图 / LLM / 监控）
                + 5 个 shim（database / indicators / strategies / screener / backtest → core/）
                                    ↓
                        api/（FastAPI 接口层，/api/v1）
                        ├─ 11 路由（stock/screen/screener/watchlist/diagnosis/portfolio/backtest/trade/training/system/commentary）
                        └─ 6 service
                                    ↓
                ┌─────────────────────────────────────────────┐
                │ frontend/（React Web UI，:5173）              │   LLM 角色层（SKILL.md）
                │ 8 页面：总览/个股/选股/自选/回测/体检/训练/交易  │   ├─ 角色扮演规则
                │                                              │   ├─ 9 个核心心智模型
                │ web/（旧 Jinja 模板，已被 frontend/ 取代）      │   ├─ 44 条决策启发式
                └─────────────────────────────────────────────┘   └─ 表达 DNA + 诚实边界
```

**关键设计原则**：Python 层只负责**数据准备与计算**，所有点评、分析话术由 LLM 用 Z哥角色生成，避免"AI味"。宿主（Claude Code/Cursor）通过 CLI `--json` 获取结构化数据；Web 端通过 FastAPI 获取。

---

## 技术栈与运行时架构

### 技术栈

| 层级 | 技术 |
|------|------|
| 领域计算 | Python 3.10+（标准库 + `sqlite3`、`pathlib`、`dataclasses`、`pandas`） |
| 外部数据 | `tushare`（Pro API，支持中转 URL）、`requests` |
| 数据库 | SQLite（本地文件，**15 张表**，~1GB 真实数据） |
| API 层 | `fastapi` + `uvicorn` + `pydantic-settings`（`/api/v1` 前缀） |
| Web 前端 | React 19 + TypeScript + Vite 8 + TailwindCSS v4 + TanStack Query + Zustand + ECharts |
| 测试框架 | `pytest`（49 文件，**835 用例**） |
| 环境配置 | `python-dotenv`（`.env` 文件） |
| 视频下载 | `yt-dlp`（语料采集，optional） |
| 语音转写 | `faster-whisper`（语料采集，optional） |
| 文档格式 | Markdown（全部文档与语料） |
| 版本控制 | Git + pre-commit（`.pre-commit-config.yaml`） |

### 配置说明

**`requirements.txt`**：
```
tushare>=1.4.0
python-dotenv>=1.0.0
pandas>=2.0.0
requests>=2.28.0
```
> FastAPI/uvicorn/pydantic-settings 为 API 层依赖（`pip install -e .` 后随 pyproject 安装）；yt-dlp/faster-whisper 为语料采集可选依赖（`pip install -e ".[corpus]"`）。

**`pyproject.toml`**：定义 `pip install -e .` 可安装为本地包，注册 3 个命令入口：
- `zt` → `modules.cli:main`（CLI 主入口）
- `zt-web` → `api.main:start_web`（启动 FastAPI 后端）
- `zt-monitor` → `modules.monitor:main`（监控）

**`.env.example`** 环境变量模板：
```ini
DATA_MODE=jnb
TUSHARE_TOKEN=你的56位token
TUSHARE_API_URL=需要配置中转地址
TUSHARE_VERIFY_TOKEN_URL=
DATA_DIR=data
DB_PATH=data/stock_data.db
```

> v2.1.1 之后，所有 Tushare URL 均从环境变量读取，代码中不再硬编码任何内部域名。

---

## 项目结构与模块划分

```
zettaranc-perspective/
├── SKILL.md                    # 核心 Skill 文件（Agent 角色扮演协议）
├── README.md                   # 面向人类用户的项目介绍
├── AGENTS.md                   # 本文件（AI Agent 开发指南）
├── CLAUDE.md / GEMINI.md       # 各 Agent 平台项目上下文
├── CONTEXT.md                  # 领域术语表（Domain Glossary）
├── LICENSE                     # MIT
├── pyproject.toml              # 包定义 + zt/zt-web/zt-monitor 命令入口
├── requirements.txt            # Python 依赖
├── .env / .env.example         # 本地配置（.env 不入库）
├── .editorconfig / .pre-commit-config.yaml
│
├── core/                       # ★ 核心领域层（v4.0.0 从 modules/ 拆出，实际计算在此）
│   ├── __init__.py             # dotenv 加载 + get_data_mode() + get_project_root()
│   ├── database.py             # SQLite 管理：15 张表、事务上下文、CRUD（真正实现）
│   ├── data_access.py          # 只读 DataAccess 层（Web/回测/训练共用）
│   ├── auto_screener.py        # 自动选股器
│   ├── simulator.py            # 少妇模拟器（自动择时+选股+买入+卖出闭环）
│   ├── timing.py               # 择时模块
│   ├── domain/
│   │   └── profile.py          # StockProfile / IndicatorResult / StockScore / DiagnosisReport 数据类
│   ├── indicators/             # 技术指标计算引擎：60+ 指标
│   │   ├── core.py             # 基础类型 + 数学工具 + 核心指标（KDJ/MACD/BBI/RSI/WR/布林/MA/DMI）
│   │   ├── price_patterns/     # 价格形态子包（7 文件：base/brick/bull_rope/complex_patterns/key_candles/sandglass/screener_helper）
│   │   ├── volume_patterns.py  # 量价信号（卖出评分/交易信号/量比异动/出货五式）
│   │   ├── wave_theory.py      # 三波理论识别（建仓/拉升/冲刺波）
│   │   ├── kirin_detector.py   # 麒麟会四阶段（吸筹/拉升/派发/回落）
│   │   └── data_layer.py       # 数据接入（get_kline_data/analyze_stock/缓存层/可视化）
│   ├── strategies/             # 战法识别引擎（6 子模块：core/base_strategies/compound_strategies/sell_signals/orchestrator/vectorized）
│   ├── screener/               # 选股评分包（criteria/b1_score/trend_score/volume_score/risk_score/_utils）
│   ├── backtest/               # 回测包（engine/historical_screener/param_tuner）
│   └── knowledge/              # 知识文档（29 个 md，含 macro/ strategies/ reference/ 子目录）
│       ├── trading-core.md / indicators.md / sell-discipline.md / position-management.md
│       ├── market-macro.md / portfolio-management.md / trading-psychology.md / stock-glossary.md
│       ├── trend-lines.md / exit-strategies.md / key-candles.md / advanced-patterns.md
│       ├── breathing-theory.md / three-best-principles.md / iron-butterfly.md / four-rhythms.md
│       ├── six-tracks-2026.md / life-decision.md / career-development.md / business-judgment.md
│       ├── heuristics.md / framework-extraction.md / data_dictionary.md / signal_dictionary.md
│       ├── macro/etf-strategy.md / strategies/choppy-market-sop.md / reference/thresholds.md
│       └── *-research.md（life-decision/business-judgment 调研稿）
│
├── modules/                    # CLI / 数据同步 / 交易 / 意图 / LLM / 监控 + 5 个 core shim
│   ├── __init__.py             # 包导出 + dotenv 统一加载 + get_data_mode()
│   ├── ① shim（向后兼容，转发到 core/）：
│   │   ├── database.py         # → core.database
│   │   ├── indicators/         # → core.indicators（含 core.py/data_layer.py 等薄壳）
│   │   ├── strategies/         # → core.strategies
│   │   ├── screener.py         # → core.screener
│   │   └── backtest.py         # → core.backtest
│   ├── ② CLI 入口：
│   │   ├── cli.py              # zt 命令主入口（analyze/screen/score/workflow/watchlist/diagnose/sync/daily）
│   │   └── cli_commands.py     # 扩展命令（backtest/trade/daily）
│   ├── ③ 数据同步：
│   │   ├── tushare_client.py   # Tushare API 封装（限流 120次/分）
│   │   └── data_sync.py        # 增量/全量同步器
│   ├── ④ 交易记录：
│   │   ├── trade_parser.py     # 口语化/JSON/CSV 多格式输入解析
│   │   ├── trade_manager.py    # 交易记录 CRUD、持仓计算、盈亏统计
│   │   └── trade_reviewer.py   # 交割单数据准备层（ReviewContext → LLM 提示词）
│   ├── ⑤ 分析/报告：
│   │   ├── portfolio_diagnosis.py  # 持股检查端到端（蜈蚣图/牛绳/沙漏诊断）
│   │   ├── watchlist.py        # 自选股观察池
│   │   ├── report.py           # Z哥量化评估报告（assess_watchlist + render + write）
│   │   ├── backtest_six_step.py # 少妇战法六步闭环回测
│   │   ├── loop_engine.py      # 六步闭环状态机
│   │   ├── commentary_service.py # 点评生成服务
│   │   └── review_generator.py
│   ├── ⑥ 意图/LLM：
│   │   ├── intent_router.py    # 意图路由：YAML 规则匹配
│   │   ├── intent_chat.py      # LLM 聊天接口
│   │   ├── knowledge_retriever.py # RAG 知识检索适配器
│   │   └── llm_providers.py    # LLM 提供者抽象
│   ├── ⑦ 监控/追踪/自优化：
│   │   ├── monitor.py          # zt-monitor 入口
│   │   ├── notifier.py / bridge_client.py / harness_updater.py
│   │   ├── improvement_logger.py / tracking_manager.py / tracking_syncer.py
│   │   └── self_optimizer/     # 自优化子包
│   └── setup_wizard.py         # 初始化向导：JNB/websearch 双模式切换
│
├── api/                        # ★ FastAPI 接口层（v4.0.0 新增）
│   ├── app.py                  # FastAPI 应用（挂载 web/static + 注册路由 + web_routes）
│   ├── main.py                 # uvicorn 启动入口（zt-web 调用）
│   ├── config.py               # Settings（pydantic-settings，读 .env）
│   ├── deps.py                 # 依赖注入（DataAccess 只读层）
│   ├── schemas.py              # Pydantic 模型
│   ├── web_routes.py           # 旧 Jinja 页面路由（兼容 web/）
│   ├── routes/                 # 11 路由模块
│   │   ├── stock.py / screen.py / screener.py / watchlist.py
│   │   ├── diagnosis.py / portfolio.py / backtest.py / trade.py
│   │   ├── training.py / system.py / commentary.py
│   ├── services/               # 6 service（stock/screen/diagnosis/portfolio/backtest/trade/watchlist）
│   ├── models/ / utils/
│
├── frontend/                   # ★ React Web UI（v4.0.0 新增，Vite dev :5173）
│   ├── package.json            # React19 + Vite8 + TailwindCSS4 + TanStack Query + Zustand + ECharts
│   ├── vite.config.ts          # 代理 /api → localhost:8000
│   ├── dev-server.mjs          # 独立 dev server 入口（:5180）
│   └── src/
│       ├── App.tsx             # 路由 + QueryClient + AppShell
│       ├── pages/              # 9 页面：Dashboard/StockAnalysis/Screener/Watchlist/Backtest/Portfolio/Training/Trades/Settings
│       ├── components/         # charts/ layout/ stock/ ui/
│       ├── api/                # 11 个 API 客户端模块 + types.ts
│       ├── hooks/ / lib/ / stores/ / styles/
│
├── web/                        # 旧 Jinja 模板前端（已被 frontend/ 取代，保留兼容）
│   ├── templates/              # base.html + stock/ screener/ backtest/ portfolio/ training/
│   └── static/                 # css/ js/
│
├── data/                       # 本地 SQLite 数据库（不入库）
│   └── stock_data.db           # 主数据库（15 张表 + 索引，~1GB）
│
├── tests/                      # 单元测试（pytest，49 文件，835 用例）
│   ├── conftest.py             # 测试基础设施：临时数据库 fixture、K线工厂函数
│   ├── test_database.py / test_data_access.py / test_data_sync_extensions.py
│   ├── test_indicators.py / test_indicators_realdata.py / test_indicator_cache.py
│   ├── test_strategies.py / test_wave_theory.py / test_kirin_detector.py
│   ├── test_screener.py / test_screener_p3.py / test_scorer.py / test_screen_service.py
│   ├── test_backtest.py / test_backtest_scorer.py / test_historical_screener.py / test_param_tuner.py
│   ├── test_loop_engine.py / test_portfolio_diagnosis.py / test_watchlist.py
│   ├── test_trade_parser.py / test_trade_manager.py / test_tushare_client.py
│   ├── test_cli_screen.py / test_cli_subparser.py
│   ├── test_api_*.py           # API 路由测试（stock/screener/backtest/portfolio/training/health/realdata_e2e）
│   ├── test_web_routes.py / test_bridge_client.py / test_monitor.py / test_notifier.py
│   ├── test_intent_router.py / test_quality_check.py / test_rate_limiter.py
│   ├── test_exam_rules.py / test_setup_wizard.py / test_report.py
│   ├── test_break_signal.py / test_reflex_blacklist.py / test_mutator.py
│   ├── test_param_registry.py / test_tracking_system.py
│   └── test_self_optimizer_e2e.py / test_self_optimizer_integration.py
│
├── scripts/                    # 工具脚本（薄壳，业务逻辑在 core/modules/）
│   ├── _common.py              # 共享工具（load_watchlist 等）
│   ├── sync_watchlist.py       # 同步缺失的自选股 K 线
│   ├── sync_and_compute.py     # 一站式同步 + 指标计算
│   ├── batch_compute_indicators.py  # 批量计算指标缓存
│   ├── generate_report.py      # 生成 Z 哥量化评估报告
│   ├── import_local_csv.py     # 导入本地 CSV 行情
│   ├── e2e_data_integrity.py   # 端到端数据完整性检查
│   └── eval_strategies.py      # 战法评估
│
├── corpus/                     # 语料采集与质检工具
│   ├── quality_check.py        # SKILL.md 质量自动检查（8+4 项维度）
│   ├── batch_download_bilibili.py  # 批量下载 B 站视频
│   ├── batch_transcribe.py     # 批量音频转写
│   ├── srt_to_transcript.py    # 字幕清洗为纯文本
│   ├── merge_research.py       # 合并调研结果
│   └── download_subtitles.sh
│
├── rules/                      # 意图识别规则与角色框架
│   ├── intent_rules.yaml       # 意图匹配规则（keywords + patterns）
│   ├── career_prompt.md        # Z哥职业决策框架
│   └── life_prompt.md          # Z哥人生决策框架
│
├── references/
│   └── research/               # 11 份调研提炼文件（蒸馏中间产物）
│       ├── 01-writings.md / 02-conversations.md / 03-expression-dna.md
│       ├── 04-external-views.md / 05-decisions.md / 06-timeline.md
│       └── 07-11-*.md          # 5 个语料源调研（xiaocainiao/dafuweng/tangoo/fupan/kedebiao）
│
└── docs/                       # 项目说明文档
    ├── CHANGELOG.md / TODO.md / CONTRIBUTING.md
    ├── USER_GUIDE.md / CONFIG_GUIDE.md
    ├── intent-router-design.md
    ├── adr/ agents/ superpowers/
    └── CHANGELOG-v3.0.md
```

**注意**：
- `references/sources/` 下的原始语料因版权和体积原因**不提交到 Git**。仓库中只保留调研提炼文件和 `SKILL.md`。
- `modules/` 中的 `database.py` / `indicators/` / `strategies/` / `screener.py` / `backtest.py` 是 **shim**（向后兼容转发到 `core/`），实际实现不要在这些文件里改，改 `core/` 对应文件。
- 修改代码前先判断目标在 `core/`（领域计算）还是 `modules/`（CLI/同步/交易/意图）。`from modules.indicators import ...` 和 `from core.indicators import ...` 都能用，但新代码应优先用 `core.*`。

---

## 数据库架构

SQLite 数据库包含 **15 张表**（`core/database.py` 中定义，`data/stock_data.db` ~1GB）：

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `stock_basic` | 股票基本信息 | ts_code/name/industry/market |
| `daily_kline` | 日线 K 线 | open/high/low/close/vol/pct_chg/is_limit_up |
| `indicator_cache` | 技术指标缓存（每日快照） | KDJ/MACD/BBI/MA/RSI/WR/布林带/双线/砖形图/DMI/量比/信号 |
| `moneyflow` | 资金流向 | 大小单买卖金额、净流入 |
| `financial_data` | 财务报表 | revenue/net_profit/total_assets/pe/pb/ps |
| `trade_signals` | 交易信号记录 | signal_type/signal_score/signal_price |
| `trade_records` | 随堂测试/交易记录 | action/price/quantity/reason/signal_type/zg_review |
| `sync_log` | 数据同步日志 | data_type/last_date/status |
| `watchlist` | 自选股观察池 | ts_code/name/tags/add_date |
| `tushare_indicator_cache` | Tushare 官方指标（diff 验证） | macd_dif/rsi_6/kdj_k/boll_mid 等 |
| `llm_response_log` | LLM 响应耗时日志 | ts_code/request_date/model/response_time_ms/success |
| `tracking_pool_self` | 追踪池 | — |
| `tracking_records_self` | 追踪记录 | — |
| `monthly_reviews_self` | 月度复盘 | — |
| `strategy_performance_self` | 策略表现 | — |

每张表均建立合适的复合索引（ts_code + trade_date DESC）。

---

## 构建、测试与常用命令

### 安装依赖

```bash
pip install -r requirements.txt
# 或安装为本地包（注册 zt / zt-web / zt-monitor 命令）
pip install -e .
# 语料采集可选依赖
pip install -e ".[corpus]"
```

### 运行测试

```bash
# 全部测试（49 文件，835 用例）
python -m pytest tests/ -v

# 单文件测试
python -m pytest tests/test_indicators.py -v
```

### 数据库初始化与数据同步

```bash
# 初始化数据库（创建 15 张表）
python -m core.database        # 实际实现
python -m modules.database     # shim，等价

# 同步股票基本信息（全量 5525 只）
python -m modules.data_sync sync

# 同步单只股票 K 线 + 指标缓存
python -m modules.data_sync sync --ts_code 600487.SH --days 365 --indicators

# 查看同步状态
python -m modules.data_sync status

# 同步 Tushare 官方指标（diff 验证）
python -m modules.data_sync stk-factor --ts_code 600487.SH --days 365
```

### 启动 Web 看板（前后端）

```bash
# ① 后端 FastAPI（:8000）
zt-web                          # 通过注册命令
# 或
python -m api.main              # 直接运行（含 reload）

# ② 前端 Vite dev server（:5173，代理 /api → :8000）
cd frontend && npm install && npm run dev

# 浏览器打开 http://localhost:5173
```

### 质量检查

```bash
# 验证 SKILL.md 是否符合质量标准（8 项基础 + 4 项 V2 表面）
python corpus/quality_check.py SKILL.md
```

### 语料采集脚本

| 脚本 | 用法 | 说明 |
|------|------|------|
| `batch_download_bilibili.py` | `cd corpus && python batch_download_bilibili.py` | 下载 B 站 ztalk 音频 |
| `batch_transcribe.py` | `cd corpus && python batch_transcribe.py` | 音频转写文本 |
| `srt_to_transcript.py` | `python corpus/srt_to_transcript.py input.srt` | 字幕清洗 |

**路径约定**：语料采集脚本位于 `corpus/` 目录（非 `scripts/`），使用硬编码相对路径，**必须在 `corpus/` 目录内执行**。

---

## 代码风格与开发规范

### 通用规范

- 所有脚本文件头包含 `#!/usr/bin/env python3`
- 使用**中文**编写文档字符串和注释
- 使用标准库为主，避免引入不必要的第三方依赖
- 每个模块文件末尾包含 `if __name__ == "__main__":` 命令行入口

### 编辑器配置

项目根目录存在 `.editorconfig`：

| 文件类型 | 缩进 | 大小 |
|---------|------|------|
| `*.py` | space | 4 |
| `*.sh` | space | 4 |
| `*.md` | space | 2（且不裁剪行尾空格） |
| `*.json` | space | 2 |
| 全部 | UTF-8 | LF 换行 |

### Python 模块规范

- **数据库路径**：统一从 `os.getenv("DB_PATH", "data/stock_data.db")` 读取，支持相对路径和绝对路径
- **环境变量加载**：`core/__init__.py` 和 `modules/__init__.py` 均在包首次 import 时一次性加载 `.env`，各子模块不再重复加载
- **DB 路径解析**：`core/*.py` 使用 `Path(__file__).parent.parent`（指向项目根目录）；`core/indicators/*.py` 使用 `Path(__file__).parent.parent.parent`
- **shim 约定**：`modules/` 下的 shim 文件只做 re-export，实际实现一律在 `core/`；新增代码 import `core.*`，旧代码 `modules.*` 仍可用
- **限流控制**：所有 Tushare API 调用必须带 `_rate_limit()`，控制 120 次/分钟
- **事务管理**：数据库操作统一使用 `get_connection()` 上下文管理器（自动 commit/rollback）
- **错误处理**：API 调用用 try/except 包裹，记录 error log，返回空 DataFrame/None 而非抛异常中断
- **包安装**：使用 `pip install -e .` 安装后，可通过 `zt` / `zt-web` / `zt-monitor` 命令或 `python -m modules.cli` / `python -m api.main` 调用
- **DataAccess 只读层**：Web/回测/训练共用 `core/data_access.py`，只读不写

### 前端规范（frontend/）

- TypeScript strict + ESLint + React Hooks 规则
- 状态管理：Zustand（全局 UI 状态）+ TanStack Query（服务端数据缓存）
- 图表：ECharts（`StockAnalysis` 和 `Backtest` 页面按需 lazy 加载，避免首屏体积）
- API 客户端：`src/api/*.ts` 统一用 axios，baseURL `/api/v1`
- 路由：React Router 7，重型页（StockAnalysis/Backtest）用 `lazy()` + `Suspense`

### 版本规则

采用语义化版本，但含义针对本项目定制：

| 位 | 含义 | 示例 |
|----|------|------|
| MAJOR | 心智模型/架构级别的重构 | v4.0.0：core 包拆分 + FastAPI + React Web UI |
| MINOR | 新增战术/启发式/语料/模块 | v2.0.0：新增 Tushare 数据层和 8 个 Python 模块 |
| PATCH | 排版修正、安全修复、数字更新 | v2.1.1：移除 URL 硬编码 |

---

## 测试策略

### 测试架构

- **框架**：pytest（49 文件，835 用例）
- **Fixture**：`conftest.py` 提供 `mock_env_for_tests`（自动 mock 环境变量到临时目录）、`temp_db`（初始化好的临时数据库）、`db_conn`（数据库连接）
- **数据工厂**：`make_kline_row()`、`make_daily_data()`、`generate_uptrend_klines()`、`generate_downtrend_klines()`、`generate_b1_scenario()` 等用于生成测试数据
- **数据库隔离**：所有测试使用临时 SQLite 文件，互不干扰

### 测试覆盖范围（按类别）

| 类别 | 测试文件 | 覆盖范围 |
|------|---------|---------|
| **数据库/数据访问** | test_database / test_data_access / test_data_sync_extensions | 路径、连接、事务、表初始化、幂等性、DataAccess 只读层 |
| **指标计算** | test_indicators / test_indicators_realdata / test_indicator_cache | 60+ 指标、真实数据验证、缓存读写 |
| **战法识别** | test_strategies / test_wave_theory / test_kirin_detector / test_break_signal | B1/B2/B3/SB1/长安/三波/麒麟会/突破信号 |
| **选股评分** | test_screener / test_screener_p3 / test_scorer / test_screen_service | 评分模型、P3 指标（蜈蚣/牛绳/沙漏）、约束过滤 |
| **回测** | test_backtest / test_backtest_scorer / test_historical_screener / test_param_tuner | 回测框架、历史选股、参数调优 |
| **少妇六步闭环** | test_loop_engine | 状态机（择时→选股→B1→止损→卤煮→BBI离场） |
| **持仓/自选** | test_portfolio_diagnosis / test_watchlist | 持股检查、防卖飞、观察池 CRUD |
| **交易记录** | test_trade_parser / test_trade_manager / test_tushare_client | 解析、CRUD、盈亏统计 |
| **CLI** | test_cli_screen / test_cli_subparser | screen 子命令、子命令分发 |
| **API 路由** | test_api_stock / test_api_screener / test_api_backtest / test_api_portfolio / test_api_training / test_api_health / test_api_realdata_e2e | FastAPI 路由、端到端真实数据 |
| **Web/监控/追踪** | test_web_routes / test_bridge_client / test_monitor / test_notifier / test_tracking_system | 旧 Web 路由、监控、追踪系统 |
| **意图/质检/限流** | test_intent_router / test_quality_check / test_rate_limiter | 意图路由、SKILL.md 质检、限流器 |
| **自优化/其他** | test_self_optimizer_e2e / test_self_optimizer_integration / test_exam_rules / test_setup_wizard / test_report / test_mutator / test_reflex_blacklist / test_param_registry | 自优化闭环、考试规则、初始化、报告 |

### 运行预期

```bash
$ python -m pytest tests/ -v
# 49 文件，835 用例
```

---

## 文件修改优先级

1. **`SKILL.md`** —— 直接影响 Skill 表现，任何改动都需语料支撑
2. **`core/*.py` / `core/*/`** —— 领域计算层（指标/战法/选股/回测/知识），改动需同步更新测试
3. **`modules/*.py`** —— CLI/数据同步/交易/意图/LLM 层（注意区分 shim 与真实实现）
4. **`api/*.py`** —— FastAPI 路由/service/schema 改动需同步 `tests/test_api_*.py`
5. **`frontend/src/**`** —— React Web UI，改完跑 `tsc -b && vite build`
6. **`core/knowledge/*.md`** —— 知识文档，补充新语料或修正旧发现时更新
7. **`references/research/*.md`** —— 调研档案，新增语料源时更新
8. **`README.md` / `docs/CHANGELOG.md`** —— 项目对外文档，版本发布时同步更新
9. **`scripts/`** —— 工具脚本，仅在数据管道或检查逻辑需要改进时修改

---

## 内容修改原则

1. **最小改动原则**：只改确实不准确的部分
2. **有依据**：任何改动都需要语料支撑，不能凭印象。优先来源：
   - zettaranc 本人直接产出（视频、直播、付费课、雪球专栏）
   - 权威媒体报道（澎湃新闻等）
   - 证券业协会公示资料
   - **不应作为主要依据**：知乎回答、非本人微信公众号、股吧/雪球帖子（除本人账号外）
3. **保持角色一致性**：修改后的回答仍需符合 zettaranc 的表达 DNA

### 风格验证清单

修改 SKILL.md 后，用以下问题自检：

- [ ] 是否用「我」而非「Z 哥认为...」？
- [ ] 是否包含职业背书开场？
- [ ] 是否分 1/2/3/4 点拆解？
- [ ] 是否用了具体数字或案例？
- [ ] 是否以金句或反问收尾？
- [ ] 是否避免跳出角色的表述？
- [ ] 交易建议是否包含具体的进场/止损/止盈规则？

---

## 安全与合规考虑

1. **免责声明**：`SKILL.md` 和 `README.md` 均包含明确免责声明——**不构成任何投资建议**。
2. **版权边界**：原始语料不提交到仓库。仓库中只保留粉丝整理的 Markdown 提炼文件和转写文本。
3. **敏感信息**：Tushare Token 和 API URL 通过 `.env` 文件管理，**绝不硬编码**。
4. **信息偏差标注**：`SKILL.md` 的「诚实边界」一节明确标注了公开表达与真实想法的差异。
5. **语料截止期**：信息截止到调研时间（2026-04-18 及后续更新）。

---

## 常见任务速查

| 任务 | 操作 |
|------|------|
| 更新心智模型或交易规则 | 先查 `references/research/01-writings.md` 和 `05-decisions.md` → 修改 `SKILL.md` → 运行 `python corpus/quality_check.py SKILL.md` |
| 补充新语料 | 将新文章放入 `references/sources/articles/` → 更新对应 `references/research/*.md` → **不要**将原始语料加入 git |
| 新增 B 站视频 transcript | `cd corpus && python batch_download_bilibili.py && python batch_transcribe.py` |
| 发布新版本 | 更新 `SKILL.md` → 更新 `docs/CHANGELOG.md` → 更新 `README.md` 中的版本 badge → 打 git tag |
| 验证风格一致性 | 对照「风格验证清单」逐项检查 |
| 修复领域计算 bug | 修改 `core/*.py`（**不是** `modules/` shim）→ 补充/更新 `tests/test_*.py` → `pytest tests/ -v` |
| 修复 CLI/同步/交易 bug | 修改 `modules/*.py`（真实实现部分）→ 更新测试 |
| 新增 API 路由 | 在 `api/routes/` 加文件 → `api/app.py` 注册 → `api/services/` 加 service → 补 `tests/test_api_*.py` |
| 新增前端页面 | `frontend/src/pages/` 加 tsx → `App.tsx` 加路由 → `api/` 加对应路由 → `src/api/` 加客户端 |
| 接入新 Tushare 接口 | 修改 `modules/tushare_client.py` → 确认 `core/database.py` 表结构支持 → 补充保存逻辑 |
| 启动 Web 看板 | `zt-web`（后端 :8000）+ `cd frontend && npm run dev`（前端 :5173） |
| 初始化全新环境 | `cp .env.example .env` → 填入 Token → `python -m core.database` → `python -m modules.data_sync sync` → `pytest tests/ -v` |

---

## 外部依赖安装

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install

# yt-dlp 可能需要 ffmpeg（处理音频）
# macOS: brew install ffmpeg
# Windows: choco install ffmpeg
```

**注意**：`faster-whisper` 的 base 模型首次运行时会自动下载到本地缓存（约 150MB）。

---

> Love and Share 🖤
