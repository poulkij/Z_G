# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

zettaranc-skill 是 **AI Skill（思维框架蒸馏包）+ 真实数据量化工具**的混合系统。将 zettaranc（万千）的投资思维框架封装为 AI 可加载的 `SKILL.md`，同时提供基于 Tushare 行情数据的 Python 量化分析层（60+ 指标、30+ 战法、选股/回测/诊断）。

**核心设计原则**：Python 层只做数据准备，所有点评/分析话术由 LLM 用 Z 哥角色生成。

## 常用命令

### 安装与配置

```bash
pip install -r requirements.txt   # 安装依赖
pip install -e .                  # 开发模式安装，注册 zt 命令
cp .env.example .env              # 配置 Tushare Token 和 API URL
```

### 测试

```bash
python -m pytest tests/ -v                         # 全部测试（49 文件，835 用例）
python -m pytest tests/test_indicators.py -v        # 单文件测试
python -m pytest tests/test_indicators.py -v -k b1  # 按关键字过滤单个测试
python -m pytest tests/ -v --tb=long                # 长 traceback 调试
```

### Lint 与格式化

```bash
ruff check modules/ tests/ --select=F,E,W,UP --ignore=E501,F401,F403   # lint
ruff format --check modules/ tests/                                     # 格式检查
ruff format modules/ tests/                                             # 自动格式化
```

### 数据库与数据同步

```bash
python -m core.database                                         # 初始化数据库（15 张表）
python -m modules.data_sync sync                                 # 同步股票基本信息（全量 5525 只）
python -m modules.data_sync sync --ts_code 600487.SH --days 120  # 同步单只 K 线
python -m modules.data_sync sync --ts_code 600487.SH --days 120 --indicators  # 同步 + 指标缓存
python -m modules.data_sync status                               # 查看同步状态
```

### CLI 工具

```bash
python -m modules.cli analyze 600487.SH                           # 股票分析
python -m modules.cli screen --strategy B1 --limit 20             # 选股扫描
python -m modules.cli diagnose 600487.SH                          # 持仓诊断
python -m modules.cli watchlist scan                              # 观察池扫描
python -m modules.cli watchlist add 600487.SH --tags 波段,通信     # 添加自选股
```

### 质量检查

```bash
python corpus/quality_check.py SKILL.md          # SKILL.md 质量检查（8 项维度）
python corpus/quality_check.py SKILL.md --strict  # 严格模式
```

## 架构概览

### 双模式架构

| 模式 | 环境变量 | 说明 |
|------|---------|------|
| JNB 模式 | `DATA_MODE=jnb` | 接入 Tushare 真实行情，实时数据查询 + 指标计算 + 战法识别 |
| 普通小万 | `DATA_MODE=websearch` | 纯 LLM 对话，不走外部数据接口 |

### 数据流

```
Tushare API → data_sync → SQLite → core/indicators/ → core/strategies/ → core/backtest/
                                                        ↓
                                              SKILL.md (LLM 角色层)

用户输入 → 意图识别(intent_router) → 规则匹配 → 角色框架(SKILL.md / career / life)
                                               → 知识库检索(Qdrant RAG, 可选)
                                               → LLM 生成(MiniMax / OpenAI 兼容, 可选)

Web 端：frontend/(React) → api/(FastAPI /api/v1) → core/(领域计算) → SQLite
```

### 核心模块

> v4.0.0 起，实际计算在 `core/`，`modules/` 下同名文件为向后兼容 shim（re-export）。新代码 import `core.*`。

- **`core/indicators/`** — 60+ 技术指标引擎（含 price_patterns/ 子包：base/brick/bull_rope/complex_patterns/key_candles/sandglass/screener_helper）
- **`core/strategies/`** — 30+ 战法识别引擎（6 子模块：core/base_strategies/compound_strategies/sell_signals/orchestrator/vectorized）
- **`core/screener/`** — 选股评分包（criteria/b1_score/trend_score/volume_score/risk_score）
- **`core/backtest/`** — 回测包（engine/historical_screener/param_tuner）
- **`core/data_access.py`** — 只读 DataAccess 层（Web/回测/训练共用）
- **`modules/cli.py`** — CLI 入口（`zt` 命令），子命令：analyze/screen/diagnose/watchlist/trade/review/setup
- **`modules/intent_router.py`** — 意图路由（stock/career/life/chat 四意图，规则匹配零 token 消耗）
- **`api/`** — FastAPI 接口层（`/api/v1` 前缀，11 路由 + 6 service）
- **`frontend/`** — React + Vite + ECharts Web UI（8 页面，dev :5173）

### 数据库（SQLite，15 张表）

`stock_basic` / `daily_kline` / `indicator_cache` / `moneyflow` / `financial_data` / `trade_signals` / `trade_records` / `sync_log` / `watchlist` / `tushare_indicator_cache` / `llm_response_log` / `tracking_pool_self` / `tracking_records_self` / `monthly_reviews_self` / `strategy_performance_self`

最近新增：`llm_response_log`（LLM 响应耗时日志）— 字段 `ts_code` / `request_date`（yyyy-mm-dd）/ `model` / `response_time_ms` / `success` / `error_message`；写入入口 `core.database.record_llm_response()`，由 `commentary_service.generate_commentary()` 在每次 Z 哥点评生成时调用。查询入口 `get_llm_response_log()` 与按日聚合 `get_llm_response_stats()`。

所有表建有复合索引（`ts_code + trade_date DESC`）。详见 `core/database.py`。

## 重要约定

1. **数据库路径**：统一从 `DB_PATH` 环境变量读取，代码中不硬编码
2. **Tushare URL**：统一从 `TUSHARE_API_URL` 环境变量读取，代码中不硬编码
3. **环境变量加载**：`core/__init__.py` 和 `modules/__init__.py` 均在包首次 import 时一次性加载 `.env`，各子模块不重复加载
4. **模块间 DB 路径解析**：`core/*.py` 用 `Path(__file__).parent.parent`；`core/indicators/*.py` 用 `Path(__file__).parent.parent.parent`（`modules/` 同理）
5. **限流控制**：所有 Tushare API 调用必须带 `_rate_limit()`，控制 120 次/分钟
6. **事务管理**：数据库操作统一用 `get_connection()` 上下文管理器
7. **真实数据优先**：不使用 mock 数据，测试基于真实 Tushare 数据管线
8. **最小改动原则**：修改 `SKILL.md` 需语料支撑，不能凭印象
9. **Python 层只做数据准备**：点评话术由 LLM 用 Z 哥角色生成，避免"AI味"

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `poulkij/Z_G`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## 代码风格

- **Python**：4 空格缩进，UTF-8，LF 换行
- **Markdown**：2 空格缩进，不裁剪行尾空格
- **注释与文档字符串**：中文
- **Lint**：ruff（line-length=120, target py310），选择规则 F/E/W/UP，忽略 E501/F401/F403
- **测试 fixture**：`conftest.py` 提供 `mock_env_for_tests`（自动 mock 环境变量到临时目录）、`temp_db`、`db_conn`；数据工厂函数 `make_kline_row()`、`generate_uptrend_klines()` 等

## CI 流水线（.github/workflows/test.yml）

5 个 job：`test`（pytest）→ `lint`（ruff check + format）→ `quality-gate`（SKILL.md 质量门）→ `e2e-realdata`（真实数据回归）→ `pre-commit`（pre-commit hooks）。当前 lint/quality-gate/e2e/pre-commit 均为 `continue-on-error: true`（观察期）。

## 关键文件

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 核心 AI 角色扮演协议（Z 哥思维框架），改动需语料支撑 |
| `AGENTS.md` | 面向 AI 编程 Agent 的完整开发指南 |
| `docs/USER_GUIDE.md` | 详细使用手册 |
| `docs/CHANGELOG.md` | 版本变更日志 |
| `rules/intent_rules.yaml` | 意图匹配规则（keywords + patterns） |
| `core/knowledge/` | 29 篇交易体系知识文档（含 macro/strategies/reference 子目录） |
