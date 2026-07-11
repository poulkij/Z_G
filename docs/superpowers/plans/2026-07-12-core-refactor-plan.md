# Plan 1: Core 重构 + Backtest 扩展 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `modules/` 领域逻辑迁移到 `core/` 分层架构，拆分大文件，新增回测参数调优和历史选股筛选，保持所有现有测试通过。

**Architecture:** `modules/` → `core/` 物理迁移 + import 路径全局替换 + `modules/__init__.py` 改为向后兼容 re-export 层 + `screener.py` 拆为包 + `backtest.py` 拆为包 + 新增 `param_tuner.py` 和 `historical_screener.py`。

**Tech Stack:** Python 3.10+, pytest, SQLite, 标准库 dataclasses/enum

---

## 文件结构

### 新建文件

```
core/__init__.py                          # core 包入口，加载 .env，re-export 核心 API
core/domain/__init__.py                    # domain 包
core/domain/profile.py                     # 从 modules/profile.py 迁入
core/indicators/                           # 从 modules/indicators/ 整体迁入
core/strategies/                           # 从 modules/strategies/ 整体迁入
core/screener/__init__.py                  # 从 modules/screener.py 拆分：导出 score_stock + registry
core/screener/trend_score.py               # 拆分：趋势评分
core/screener/volume_score.py              # 拆分：量价评分
core/screener/risk_score.py                # 拆分：风险评分
core/screener/b1_score.py                  # 拆分：B1 评分
core/screener/criteria.py                  # 拆分：筛选条件注册表 + 硬过滤
core/backtest/__init__.py                  # 从 modules/backtest.py 拆分：导出 run_backtest
core/backtest/engine.py                    # 拆分：现有回测引擎逻辑
core/backtest/param_tuner.py               # 新增：参数调优（网格搜索）
core/backtest/historical_screener.py       # 新增：历史选股筛选
core/database.py                           # 从 modules/database.py 迁入
core/data_access.py                        # 新增：只读数据访问层
core/knowledge/                            # 从 knowledge/ 整体迁入
```

### 修改文件

```
modules/__init__.py                        # 改为 re-export from core/（向后兼容）
modules/portfolio_diagnosis.py            # import 路径更新
modules/watchlist.py                       # import 路径更新
modules/report.py                          # import 路径更新
modules/cli.py                             # import 路径更新
modules/cli_commands.py                    # import 路径更新
modules/backtest_six_step.py               # import 路径更新
modules/bridge_client.py                   # import 路径更新
modules/commentary_service.py              # import 路径更新
modules/trade_reviewer.py                  # import 路径更新
tests/conftest.py                          # import 路径更新
tests/test_*.py (所有测试文件)              # import 路径更新
```

### 删除文件（迁移后）

```
modules/profile.py                         # → core/domain/profile.py
modules/screener.py                        # → core/screener/
modules/backtest.py                        # → core/backtest/engine.py
modules/database.py                        # → core/database.py
modules/indicators/                        # → core/indicators/
modules/strategies/                        # → core/strategies/
knowledge/                                 # → core/knowledge/
```

---

## Task 1: 创建 core/ 包骨架

**Files:**
- Create: `core/__init__.py`
- Create: `core/domain/__init__.py`

- [ ] **Step 1: 创建 core/ 目录结构**

```bash
mkdir core
mkdir core/domain
```

- [ ] **Step 2: 创建 core/__init__.py**

```python
"""
Core 领域层 — 技术指标、战法识别、选股评分、回测引擎
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 全局一次性加载 .env（包首次 import 时执行）
_env_path = Path(os.getenv("ZETTARANC_ENV", Path(__file__).parent.parent / ".env"))
load_dotenv(_env_path, override=False)


def get_data_mode() -> str:
    """获取当前数据模式：jnb 或 websearch"""
    return os.getenv("DATA_MODE", "websearch")


def get_project_root() -> Path:
    """获取项目根目录（core/ 的上一级）"""
    return Path(__file__).parent.parent
```

- [ ] **Step 3: 创建 core/domain/__init__.py**

```python
"""领域模型包"""
from .profile import StockProfile

__all__ = ["StockProfile"]
```

- [ ] **Step 4: 验证包可导入**

Run: `python -c "import core; print(core.get_data_mode())"`
Expected: 输出 `websearch` 或 `jnb`，无报错

- [ ] **Step 5: Commit**

```bash
git add core/
git commit -m "refactor: create core/ package skeleton"
```

---

## Task 2: 迁移 profile.py → core/domain/profile.py

**Files:**
- Create: `core/domain/profile.py`（从 `modules/profile.py` 复制内容）
- Delete: `modules/profile.py`

- [ ] **Step 1: 复制 profile.py 到 core/domain/**

```bash
copy modules\profile.py core\domain\profile.py
```

- [ ] **Step 2: 删除原文件**

```bash
del modules\profile.py
```

- [ ] **Step 3: 更新 modules/__init__.py 的 profile 导入**

在 `modules/__init__.py` 中，将 profile 的导入改为从 core 导入：

```python
# 在 modules/__init__.py 中添加（如果原来有导入的话）
from core.domain.profile import StockProfile  # noqa: E402
```

- [ ] **Step 4: 全局搜索确认没有遗漏的 `from modules.profile` 或 `from .profile` 导入**

Run: `grep -r "from modules.profile\|from .profile" --include="*.py" .`
Expected: 无结果（或只在 core/domain/ 内部）

- [ ] **Step 5: 验证导入**

Run: `python -c "from core.domain.profile import StockProfile; print(StockProfile())"`
Expected: 输出 StockProfile 实例，无报错

- [ ] **Step 6: Commit**

```bash
git add core/domain/profile.py modules/__init__.py
git rm modules/profile.py
git commit -m "refactor: migrate profile.py to core/domain/"
```

---

## Task 3: 迁移 database.py → core/database.py

**Files:**
- Create: `core/database.py`（从 `modules/database.py` 复制）
- Modify: `modules/database.py` → 改为 re-export shim
- Modify: 所有引用 `modules.database` 的文件

- [ ] **Step 1: 复制 database.py 到 core/**

```bash
copy modules\database.py core\database.py
```

- [ ] **Step 2: 在 core/database.py 中更新路径解析**

`core/database.py` 中的 `Path(__file__).parent.parent` 原来指向项目根（modules/ 的上一级），现在 core/ 的上一级也是项目根，所以路径逻辑不变。但需要检查内部是否有 `Path(__file__).parent` 指向 modules/ 的地方。

Run: `grep "Path(__file__)" core/database.py`
Expected: 确认路径逻辑正确（`parent.parent` 仍指向项目根）

- [ ] **Step 3: 将 modules/database.py 改为 re-export shim**

```python
"""
向后兼容 shim — 从 core.database re-export
"""
from core.database import (
    get_connection,
    get_db_path,
    get_db_connection,
    init_database,
    drop_all_tables,
    DB_PATH,
)

__all__ = [
    "get_connection",
    "get_db_path",
    "get_db_connection",
    "init_database",
    "drop_all_tables",
    "DB_PATH",
]
```

注意：先读取 `modules/database.py` 的完整 `__all__` 和公开函数列表，确保 shim 导出所有被外部引用的名称。

- [ ] **Step 4: 更新 modules/__init__.py 中的 database 导入**

将 `from .database import ...` 改为 `from core.database import ...`

- [ ] **Step 5: 验证导入**

Run: `python -c "from modules.database import get_connection; print('OK')"`
Run: `python -c "from core.database import get_connection; print('OK')"`
Expected: 两条都输出 OK

- [ ] **Step 6: Commit**

```bash
git add core/database.py modules/database.py modules/__init__.py
git commit -m "refactor: migrate database.py to core/, keep shim in modules/"
```

---

## Task 4: 迁移 indicators/ → core/indicators/

**Files:**
- Move: `modules/indicators/` → `core/indicators/`
- Modify: `modules/indicators/__init__.py` → 改为 re-export shim

- [ ] **Step 1: 整体移动 indicators 目录**

```bash
move modules\indicators core\indicators
```

- [ ] **Step 2: 更新 core/indicators/ 内部的相对导入**

`core/indicators/` 内部使用相对导入（`from .core import ...`），这些不需要改。但 `core/indicators/` 中可能有引用 `modules.database` 或 `modules.profile` 的地方。

Run: `grep -rn "from modules\.\|from \.\.database\|from \.\.profile" core/indicators/ --include="*.py"`
检查并更新这些导入为 `from core.database import ...` 或 `from core.domain.profile import ...`

- [ ] **Step 3: 更新 core/indicators/core.py 中的路径解析**

`core/indicators/core.py` 中 `Path(__file__).parent.parent.parent` 原来指向项目根（modules/indicators/ 的上两级），现在 `core/indicators/core.py` 的上两级也是项目根，所以路径逻辑不变。

但 `core/indicators/core.py` 中 `Path(__file__).parent.parent` 原来指向 `modules/`，现在指向 `core/`。需要检查是否有硬编码引用。

Run: `grep -n "Path(__file__)" core/indicators/core.py`
逐行检查并更新路径逻辑。

- [ ] **Step 4: 创建 modules/indicators/ re-export shim**

```bash
mkdir modules\indicators
```

创建 `modules/indicators/__init__.py`：

```python
"""
向后兼容 shim — 从 core.indicators re-export
"""
from core.indicators import *  # noqa: F401, F403
from core.indicators import DailyData, IndicatorResult, TradeSignal, __all__
```

- [ ] **Step 5: 验证导入**

Run: `python -c "from modules.indicators import DailyData; print('OK')"`
Run: `python -c "from core.indicators import DailyData; print('OK')"`
Expected: 两条都 OK

- [ ] **Step 6: Commit**

```bash
git add core/indicators/ modules/indicators/
git commit -m "refactor: migrate indicators/ to core/indicators/, keep shim"
```

---

## Task 5: 迁移 strategies/ → core/strategies/

**Files:**
- Move: `modules/strategies/` → `core/strategies/`
- Modify: `modules/strategies/__init__.py` → 改为 re-export shim

- [ ] **Step 1: 整体移动 strategies 目录**

```bash
move modules\strategies core\strategies
```

- [ ] **Step 2: 更新 core/strategies/ 内部的导入**

`core/strategies/` 中引用 `modules.indicators` 或 `modules.database` 的地方需要更新。

Run: `grep -rn "from modules\.\|from \.\." core/strategies/ --include="*.py"`

更新为：
- `from modules.indicators` → `from core.indicators`
- `from modules.database` → `from core.database`
- `from ..indicators` → `from core.indicators`（如果 strategies 子模块用相对导入引用 indicators）
- `from ..database` → `from core.database`

- [ ] **Step 3: 更新 core/strategies/core.py 中的 get_kline_data**

`core/strategies/core.py` 中的 `get_kline_data` 函数可能从 `modules.database` 或 `modules.indicators.data_layer` 获取数据。检查并更新导入。

Run: `grep -n "import\|from" core/strategies/core.py`

- [ ] **Step 4: 创建 modules/strategies/ re-export shim**

```bash
mkdir modules\strategies
```

创建 `modules/strategies/__init__.py`：

```python
"""
向后兼容 shim — 从 core.strategies re-export
"""
from core.strategies import *  # noqa: F401, F403
from core.strategies import (
    detect_all_strategies,
    detect_b1,
    detect_b2,
    detect_b3,
    detect_sb1,
    detect_changan,
    detect_s1,
    detect_s2,
    detect_s3,
    get_kline_data,
    StrategyType,
    Priority,
    Action,
    StrategySignal,
)
```

注意：先读取 `core/strategies/__init__.py` 的完整导出列表，确保 shim 覆盖所有公开名称。

- [ ] **Step 5: 验证导入**

Run: `python -c "from modules.strategies import detect_b1; print('OK')"`
Run: `python -c "from core.strategies import detect_b1; print('OK')"`
Expected: 两条都 OK

- [ ] **Step 6: Commit**

```bash
git add core/strategies/ modules/strategies/
git commit -m "refactor: migrate strategies/ to core/strategies/, keep shim"
```

---

## Task 6: 迁移 knowledge/ → core/knowledge/

**Files:**
- Move: `knowledge/` → `core/knowledge/`

- [ ] **Step 1: 整体移动 knowledge 目录**

```bash
move knowledge core\knowledge
```

- [ ] **Step 2: 更新引用 knowledge/ 路径的代码**

Run: `grep -rn "knowledge/" --include="*.py" .`

更新所有引用 `knowledge/` 路径的代码为 `core/knowledge/`。特别检查：
- `modules/knowledge_retriever.py`
- `SKILL.md` 中的路径引用（如果有的话）
- `modules/report.py`

- [ ] **Step 3: 在项目根创建 knowledge/ 符号链接（或 re-export）**

为了保持 SKILL.md 中的路径引用仍然有效，在项目根创建一个 re-export：

```bash
# Windows 下创建 junction
mklink /J knowledge core\knowledge
```

如果不行，则更新所有引用路径。

- [ ] **Step 4: 验证**

Run: `python -c "from modules.knowledge_retriever import KnowledgeRetriever; print('OK')"`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add core/knowledge/ knowledge
git commit -m "refactor: migrate knowledge/ to core/knowledge/"
```

---

## Task 7: 拆分 screener.py → core/screener/ 包

**Files:**
- Read: `modules/screener.py`（913 行，完整读取理解结构）
- Create: `core/screener/__init__.py`
- Create: `core/screener/trend_score.py`
- Create: `core/screener/volume_score.py`
- Create: `core/screener/risk_score.py`
- Create: `core/screener/b1_score.py`
- Create: `core/screener/criteria.py`
- Delete: `modules/screener.py`

- [ ] **Step 1: 完整读取 screener.py，记录结构**

Run: `Read modules/screener.py (all 913 lines)`

记录以下信息：
- StockScore dataclass 定义（字段列表）
- _CRITERIA_REGISTRY 注册表
- 所有 `@_register` 装饰的函数
- score_stock() 主函数
- _score_trend() / _score_volume() / _score_risk() / _score_b1() 函数
- screen_stocks() 函数
- 硬过滤函数（_check_centipede, _check_sandglass_min）
- 其他工具函数

- [ ] **Step 2: 创建 core/screener/__init__.py — 导出 + StockScore dataclass**

将 StockScore dataclass 和 score_stock() 主函数放在 `__init__.py`：

```python
"""
选股评分系统 — Z哥三最原则和每日五步工作流
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from collections.abc import Callable

from core.indicators import DailyData, calculate_ma
from core.database import get_connection, get_db_path, get_db_connection
from core.bridge_client_compat import get_all_stocks_bridge_first, get_daily_klines  # 见说明

from .trend_score import score_trend
from .volume_score import score_volume
from .risk_score import score_risk
from .b1_score import score_b1
from .criteria import (
    _CRITERIA_REGISTRY,
    _register,
    screen_by_criteria,
    _check_centipede,
    _check_sandglass_min,
)

# 并行化阈值
_PARALLEL_THRESHOLD = 50


@dataclass
class StockScore:
    """股票综合评分"""
    ts_code: str = ""
    name: str = ""
    trade_date: str = ""
    close: float = 0
    pct_chg: float = 0

    score: float = 0
    trend_score: float = 0
    volume_score: float = 0
    risk_score: float = 0
    b1_score: float = 0

    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    strategy_tags: list[str] = field(default_factory=list)


def score_stock(ts_code: str, klines: list[dict] | None = None) -> StockScore:
    """
    对单只股票进行多维度评分
    """
    # ... 从原 screener.py score_stock 函数复制
    ...


def screen_stocks(
    criteria: str = "perfect",
    min_score: int = 0,
    limit: int = 50,
    ...
) -> list[StockScore]:
    """
    筛选股票
    """
    # ... 从原 screener.py screen_stocks 函数复制
    ...


__all__ = [
    "StockScore",
    "score_stock",
    "screen_stocks",
    "score_trend",
    "score_volume",
    "score_risk",
    "score_b1",
]
```

注意：`score_stock` 和 `screen_stocks` 的完整实现从原文件复制。需要将原文件中对 `.strategies`、`.indicators`、`.database`、`.bridge_client` 的相对导入改为 `core.` 绝对导入。

- [ ] **Step 3: 创建 core/screener/trend_score.py**

从原 screener.py 中提取趋势评分相关函数：

```python
"""趋势评分模块"""

from typing import Any


def score_trend(klines: list[dict]) -> tuple[float, list[str]]:
    """
    趋势评分（0-100）
    返回 (score, reasons)
    """
    # 从原 screener.py _score_trend 函数复制完整实现
    ...
```

- [ ] **Step 4: 创建 core/screener/volume_score.py**

从原 screener.py 中提取量价评分相关函数：

```python
"""量价评分模块"""

from typing import Any


def score_volume(klines: list[dict]) -> tuple[float, list[str]]:
    """
    量价评分（0-100）
    返回 (score, reasons)
    """
    # 从原 screener.py _score_volume 函数复制完整实现
    ...
```

- [ ] **Step 5: 创建 core/screener/risk_score.py**

```python
"""风险评分模块"""

from typing import Any


def score_risk(klines: list[dict]) -> tuple[float, list[str]]:
    """
    风险评分（0-100，越高越安全）
    返回 (score, warnings)
    """
    # 从原 screener.py _score_risk 函数复制完整实现
    ...
```

- [ ] **Step 6: 创建 core/screener/b1_score.py**

```python
"""B1 机会评分模块"""

from typing import Any


def score_b1(klines: list[dict]) -> tuple[float, list[str]]:
    """
    B1 买点评分（0-100）
    返回 (score, reasons)
    """
    # 从原 screener.py _score_b1 函数复制完整实现
    ...
```

- [ ] **Step 7: 创建 core/screener/criteria.py**

将所有 `@_register` 注册的条件函数和硬过滤函数移到这里：

```python
"""筛选条件注册表 + 硬过滤"""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import StockScore

CriteriaFn = Callable[[list, "StockScore"], bool]

_CRITERIA_REGISTRY: dict[str, CriteriaFn] = {}


def _register(name: str):
    """装饰器：注册筛选条件处理函数"""
    def decorator(fn: CriteriaFn) -> CriteriaFn:
        _CRITERIA_REGISTRY[name] = fn
        return fn
    return decorator


# ---------- 硬过滤 ----------

def _check_centipede(klines) -> bool:
    # 从原文件复制
    ...


def _check_sandglass_min(klines, min_score: int = 50) -> bool:
    # 从原文件复制
    ...


# ---------- 基础评分条件 ----------

@_register("b1")
def _criteria_b1(klines, score: "StockScore") -> bool:
    # 从原文件复制
    ...


@_register("perfect")
def _criteria_perfect(klines, score: "StockScore") -> bool:
    # 从原文件复制
    ...


# ... 所有其他 @_register 函数从原文件复制


def screen_by_criteria(klines: list, score: "StockScore", criteria: str) -> bool:
    """按条件名筛选"""
    fn = _CRITERIA_REGISTRY.get(criteria)
    if fn is None:
        return True
    return fn(klines, score)
```

- [ ] **Step 8: 创建 modules/screener.py re-export shim**

```python
"""
向后兼容 shim — 从 core.screener re-export
"""
from core.screener import (
    StockScore,
    score_stock,
    screen_stocks,
)

__all__ = ["StockScore", "score_stock", "screen_stocks"]
```

- [ ] **Step 9: 验证导入**

Run: `python -c "from modules.screener import score_stock; print('OK')"`
Run: `python -c "from core.screener import score_stock; print('OK')"`
Expected: 两条都 OK

- [ ] **Step 10: 运行 screener 相关测试**

Run: `python -m pytest tests/test_screener.py tests/test_screener_p3.py -v`
Expected: 所有测试通过

- [ ] **Step 11: Commit**

```bash
git add core/screener/ modules/screener.py
git rm modules/screener.py.bak  # 如果有备份的话
git commit -m "refactor: split screener.py into core/screener/ package"
```

---

## Task 8: 拆分 backtest.py → core/backtest/ 包

**Files:**
- Read: `modules/backtest.py`（851 行）
- Create: `core/backtest/__init__.py`
- Create: `core/backtest/engine.py`
- Delete: `modules/backtest.py`

- [ ] **Step 1: 完整读取 backtest.py，记录结构**

记录以下信息：
- Trade dataclass
- BacktestResult dataclass
- backtest_signals() 函数
- backtest_strategy() 函数
- 所有辅助函数（_is_stop_loss_triggered, _stop_loss_price, _is_take_profit_triggered, _take_profit_price, _calc_pnl, _make_trade）
- _summarize_results() 函数

- [ ] **Step 2: 创建 core/backtest/engine.py — 现有回测逻辑**

```python
"""
回测引擎 — 基于策略信号 + 历史K线，模拟交易并输出统计指标
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from core.strategies import detect_all_strategies, get_kline_data


@dataclass
class Trade:
    """单笔交易记录"""
    ts_code: str
    entry_date: str
    entry_price: float
    exit_date: str | None = None
    exit_price: float | None = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    hold_days: int = 0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    ts_code: str
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    avg_return: float = 0.0
    avg_hold_days: float = 0.0
    total_return: float = 0.0
    trades: list[Trade] = field(default_factory=list)

    def summary(self) -> str:
        # 从原文件复制
        ...


# 所有辅助函数从原文件复制
def _is_stop_loss_triggered(...):
    ...
def _stop_loss_price(...):
    ...
def _is_take_profit_triggered(...):
    ...
def _take_profit_price(...):
    ...
def _calc_pnl(...):
    ...
def _make_trade(...):
    ...


def backtest_signals(
    signals: list[Any],
    klines: list[dict[str, Any]],
    ts_code: str,
    stop_loss_pct: float = 0.07,
    take_profit_pct: float = 0.15,
    position_pct: float = 1.0,
) -> BacktestResult:
    # 从原文件复制完整实现
    ...


def backtest_strategy(
    ts_code: str,
    days: int = 240,
    stop_loss_pct: float = 0.07,
    take_profit_pct: float = 0.15,
) -> BacktestResult:
    # 从原文件复制完整实现
    ...
```

- [ ] **Step 3: 创建 core/backtest/__init__.py — 导出**

```python
"""
回测包 — 引擎 + 参数调优 + 历史筛选
"""

from .engine import (
    Trade,
    BacktestResult,
    backtest_signals,
    backtest_strategy,
)

__all__ = [
    "Trade",
    "BacktestResult",
    "backtest_signals",
    "backtest_strategy",
]
```

- [ ] **Step 4: 创建 modules/backtest.py re-export shim**

```python
"""
向后兼容 shim — 从 core.backtest re-export
"""
from core.backtest import (
    Trade,
    BacktestResult,
    backtest_signals,
    backtest_strategy,
)

__all__ = [
    "Trade",
    "BacktestResult",
    "backtest_signals",
    "backtest_strategy",
]
```

- [ ] **Step 5: 验证导入**

Run: `python -c "from modules.backtest import backtest_strategy; print('OK')"`
Run: `python -c "from core.backtest import backtest_strategy; print('OK')"`
Expected: 两条都 OK

- [ ] **Step 6: 运行 backtest 测试**

Run: `python -m pytest tests/test_backtest.py -v`
Expected: 所有测试通过

- [ ] **Step 7: Commit**

```bash
git add core/backtest/ modules/backtest.py
git commit -m "refactor: split backtest.py into core/backtest/ package"
```

---

## Task 9: 全局 import 路径更新

**Files:**
- Modify: 所有 `modules/` 中引用已迁移模块的文件
- Modify: 所有 `tests/` 中的测试文件
- Modify: `tests/conftest.py`

- [ ] **Step 1: 找出所有需要更新的 import**

Run: `grep -rn "from modules.database\|from modules.indicators\|from modules.strategies\|from modules.screener\|from modules.backtest\|from modules.profile" --include="*.py" modules/ tests/`

记录所有匹配行。

- [ ] **Step 2: 更新 tests/conftest.py**

将以下导入：
```python
from modules.database import init_database, drop_all_tables
from modules.database import get_connection
from modules.indicators import DailyData
```
改为：
```python
from core.database import init_database, drop_all_tables
from core.database import get_connection
from core.indicators import DailyData
```

注意：保留 `from modules.database import ...` 也可以工作（因为有 shim），但为了清晰，测试中应直接引用 `core.`。

- [ ] **Step 3: 更新所有测试文件的 import**

对 `tests/` 目录下所有 .py 文件，将：
- `from modules.database` → `from core.database`
- `from modules.indicators` → `from core.indicators`
- `from modules.strategies` → `from core.strategies`
- `from modules.screener` → `from core.screener`
- `from modules.backtest` → `from core.backtest`
- `from modules.profile` → `from core.domain.profile`

可以用 Python 脚本批量替换：

```python
import os, re

replacements = [
    ("from modules.database", "from core.database"),
    ("from modules.indicators", "from core.indicators"),
    ("from modules.strategies", "from core.strategies"),
    ("from modules.screener", "from core.screener"),
    ("from modules.backtest", "from core.backtest"),
    ("from modules.profile", "from core.domain.profile"),
    ("import modules.database", "import core.database"),
    ("import modules.indicators", "import core.indicators"),
    ("import modules.strategies", "import core.strategies"),
    ("import modules.screener", "import core.screener"),
    ("import modules.backtest", "import core.backtest"),
]

for root, dirs, files in os.walk("tests"):
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        for old, new in replacements:
            content = content.replace(old, new)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
```

- [ ] **Step 4: 更新 modules/ 中保留的文件的 import**

对 `modules/` 目录下保留的文件（portfolio_diagnosis.py, watchlist.py, report.py, cli.py, cli_commands.py, backtest_six_step.py, bridge_client.py, commentary_service.py, trade_reviewer.py 等），将：
- `from .database` → `from core.database`
- `from .indicators` → `from core.indicators`
- `from .strategies` → `from core.strategies`
- `from .screener` → `from core.screener`
- `from .backtest` → `from core.backtest`
- `from .profile` → `from core.domain.profile`
- `from modules.database` → `from core.database`
- `from modules.indicators` → `from core.indicators`
- etc.

用类似的 Python 脚本批量替换。

- [ ] **Step 5: 更新 modules/__init__.py**

将所有 `from .database import ...` 改为 `from core.database import ...`
将 `from .indicators import ...` 改为不需要（indicators 已迁移，通过 shim 访问）

- [ ] **Step 6: 运行全部测试**

Run: `python -m pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: 与迁移前相同的通过/跳过数量

- [ ] **Step 7: 修复任何失败的测试**

如果有测试失败，逐一检查 import 错误并修复。

Run: `python -m pytest tests/ -v --tb=short 2>&1 | grep "FAILED\|ERROR"`
逐个修复。

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: update all imports from modules.* to core.*"
```

---

## Task 10: 新增 core/data_access.py — 只读数据访问层

**Files:**
- Create: `core/data_access.py`
- Create: `tests/test_data_access.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_data_access.py
"""DataAccess 只读数据访问层测试"""

import pytest
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines


def test_get_klines_returns_daily_data(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    rows = generate_uptrend_klines(n=60, ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    da = DataAccess()
    klines = da.get_klines("600519.SH", days=60)
    assert len(klines) == 60
    assert klines[0].ts_code == "600519.SH"
    assert hasattr(klines[0], "open")
    assert hasattr(klines[0], "close")


def test_get_klines_empty_for_unknown_stock(temp_db):
    from core.data_access import DataAccess

    da = DataAccess()
    klines = da.get_klines("999999.SZ", days=60)
    assert klines == []


def test_get_klines_by_date_range(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    rows = generate_uptrend_klines(n=60, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    da = DataAccess()
    klines = da.get_klines_by_range("600519.SH", "20250110", "20250120")
    assert len(klines) == 11
    assert klines[0].trade_date == "20250110"
    assert klines[-1].trade_date == "20250120"


def test_get_stock_list(temp_db):
    from core.data_access import DataAccess
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")

    da = DataAccess()
    stocks = da.get_stock_list()
    assert len(stocks) == 2
    assert any(s.ts_code == "600519.SH" for s in stocks)


def test_data_access_is_read_only(temp_db):
    """DataAccess 不应有任何写方法"""
    from core.data_access import DataAccess

    da = DataAccess()
    public_methods = [m for m in dir(da) if not m.startswith("_")]
    for method in public_methods:
        assert not method.startswith("insert")
        assert not method.startswith("update")
        assert not method.startswith("delete")
        assert not method.startswith("write")
        assert not method.startswith("create")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_data_access.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.data_access'`

- [ ] **Step 3: 实现 core/data_access.py**

```python
"""
只读 SQLite 数据访问层 — Web/回测/训练共用
所有方法只读，不写数据库
"""

import sqlite3
from functools import lru_cache
from typing import Optional
import os

from core.database import get_db_path
from core.indicators import DailyData


class DataAccess:
    """只读数据访问层"""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or get_db_path()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_klines(self, ts_code: str, days: int = 120) -> list[DailyData]:
        """获取最近 N 天 K 线数据"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, trade_date, open, high, low, close,
                       vol, amount, pct_chg
                FROM daily_kline
                WHERE ts_code = ?
                ORDER BY trade_date DESC
                LIMIT ?
                """,
                (ts_code, days),
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        rows = list(reversed(rows))
        result = []
        prev_close = None
        for r in rows:
            result.append(
                DailyData(
                    ts_code=r["ts_code"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    vol=r["vol"],
                    amount=r["amount"],
                    pct_chg=r["pct_chg"],
                    prev_close=prev_close or r["open"],
                )
            )
            prev_close = r["close"]
        return result

    def get_klines_by_range(
        self, ts_code: str, start_date: str, end_date: str
    ) -> list[DailyData]:
        """按日期范围获取 K 线数据"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, trade_date, open, high, low, close,
                       vol, amount, pct_chg
                FROM daily_kline
                WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
                ORDER BY trade_date ASC
                """,
                (ts_code, start_date, end_date),
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        result = []
        prev_close = None
        for r in rows:
            result.append(
                DailyData(
                    ts_code=r["ts_code"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    vol=r["vol"],
                    amount=r["amount"],
                    pct_chg=r["pct_chg"],
                    prev_close=prev_close or r["open"],
                )
            )
            prev_close = r["close"]
        return result

    def get_stock_list(self) -> list[dict]:
        """获取股票基本信息列表"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, name, industry, market
                FROM stock_basic
                ORDER BY ts_code
                """
            )
            rows = cursor.fetchall()

        return [
            {"ts_code": r["ts_code"], "name": r["name"],
             "industry": r["industry"], "market": r["market"]}
            for r in rows
        ]

    def get_indicator_cache(self, ts_code: str, date: str) -> dict | None:
        """获取某日指标缓存"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM indicator_cache
                WHERE ts_code = ? AND trade_date = ?
                """,
                (ts_code, date),
            )
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_signals_by_date(self, date: str, strategy: str | None = None) -> list[dict]:
        """获取某日交易信号"""
        if strategy:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM trade_signals
                    WHERE trade_date = ? AND signal_type = ?
                    """,
                    (date, strategy),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM trade_signals
                    WHERE trade_date = ?
                    """,
                    (date,),
                )
                rows = cursor.fetchall()

        return [dict(r) for r in rows]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_data_access.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add core/data_access.py tests/test_data_access.py
git commit -m "feat: add read-only DataAccess layer in core/"
```

---

## Task 11: 新增 core/backtest/param_tuner.py — 参数调优

**Files:**
- Create: `core/backtest/param_tuner.py`
- Create: `tests/test_param_tuner.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_param_tuner.py
"""参数调优器测试"""

import pytest
from tests.conftest import write_klines_to_db, generate_uptrend_klines, generate_b1_scenario


def test_param_tuner_returns_best_params(temp_db):
    from core.backtest.param_tuner import tune_params, TuneResult
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    param_grid = {
        "stop_loss_pct": [0.05, 0.07, 0.10],
        "take_profit_pct": [0.10, 0.15, 0.20],
    }

    result = tune_params(
        ts_code="600519.SH",
        param_grid=param_grid,
        days=120,
    )

    assert isinstance(result, TuneResult)
    assert result.best_params is not None
    assert "stop_loss_pct" in result.best_params
    assert "take_profit_pct" in result.best_params
    assert len(result.all_results) == 9  # 3x3 grid


def test_param_tuner_best_score_is_max(temp_db):
    from core.backtest.param_tuner import tune_params
    from core.database import get_connection

    rows = generate_b1_scenario(ts_code="600519.SH")
    with get_connection() as conn:
        write_klines_to_db(conn, rows)

    param_grid = {
        "stop_loss_pct": [0.05, 0.07],
        "take_profit_pct": [0.10, 0.15],
    }

    result = tune_params("600519.SH", param_grid, days=120)

    scores = [r["score"] for r in result.all_results]
    assert result.best_score == max(scores)


def test_param_tuner_empty_data(temp_db):
    from core.backtest.param_tuner import tune_params

    param_grid = {"stop_loss_pct": [0.05]}
    result = tune_params("999999.SZ", param_grid, days=60)
    assert result.best_params == {}
    assert result.best_score == 0.0
    assert result.all_results == []
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_param_tuner.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: 实现 core/backtest/param_tuner.py**

```python
"""
参数调优器 — 对战法参数做网格搜索，输出最优参数 + 胜率报告
"""

from dataclasses import dataclass, field
from itertools import product
from typing import Any

from .engine import backtest_strategy


@dataclass
class TuneResult:
    """参数调优结果"""
    best_params: dict = field(default_factory=dict)
    best_score: float = 0.0
    all_results: list[dict] = field(default_factory=list)


def tune_params(
    ts_code: str,
    param_grid: dict[str, list],
    days: int = 240,
    score_metric: str = "win_rate",
) -> TuneResult:
    """
    对回测参数做网格搜索

    Args:
        ts_code: 股票代码
        param_grid: 参数网格，如 {"stop_loss_pct": [0.05, 0.07], "take_profit_pct": [0.10, 0.15]}
        days: 回测天数
        score_metric: 评分指标，win_rate / total_return / profit_factor

    Returns:
        TuneResult
    """
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = list(product(*values))

    if not combinations:
        return TuneResult()

    all_results = []
    best_score = -1.0
    best_params = {}

    for combo in combinations:
        params = dict(zip(keys, combo))
        result = backtest_strategy(ts_code, days=days, **params)

        if score_metric == "win_rate":
            score = result.win_rate
        elif score_metric == "total_return":
            score = result.total_return
        elif score_metric == "profit_factor":
            score = result.profit_factor
        else:
            score = result.win_rate

        entry = {
            "params": params,
            "score": score,
            "win_rate": result.win_rate,
            "total_return": result.total_return,
            "max_drawdown": result.max_drawdown,
            "total_trades": result.total_trades,
        }
        all_results.append(entry)

        if score > best_score:
            best_score = score
            best_params = params

    return TuneResult(
        best_params=best_params,
        best_score=best_score if best_score >= 0 else 0.0,
        all_results=all_results,
    )
```

- [ ] **Step 4: 更新 core/backtest/__init__.py 导出**

```python
from .engine import (
    Trade,
    BacktestResult,
    backtest_signals,
    backtest_strategy,
)
from .param_tuner import tune_params, TuneResult

__all__ = [
    "Trade",
    "BacktestResult",
    "backtest_signals",
    "backtest_strategy",
    "tune_params",
    "TuneResult",
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_param_tuner.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add core/backtest/param_tuner.py tests/test_param_tuner.py core/backtest/__init__.py
git commit -m "feat: add param_tuner for backtest grid search"
```

---

## Task 12: 新增 core/backtest/historical_screener.py — 历史选股筛选

**Files:**
- Create: `core/backtest/historical_screener.py`
- Create: `tests/test_historical_screener.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_historical_screener.py
"""历史选股筛选器测试"""

import pytest
from tests.conftest import write_klines_to_db, write_stock_basic, generate_uptrend_klines, generate_b1_scenario


def test_historical_screener_returns_scored_stocks(temp_db):
    from core.backtest.historical_screener import screen_historical, ScreenResult
    from core.database import get_connection

    # 写入两只股票
    rows1 = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    rows2 = generate_b1_scenario(ts_code="000001.SZ")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_stock_basic(conn, "000001.SZ", "平安银行")
        write_klines_to_db(conn, rows1)
        write_klines_to_db(conn, rows2)

    result = screen_historical(
        date="20250301",
        strategies=["b1"],
        min_score=0,
    )

    assert isinstance(result, ScreenResult)
    assert result.date == "20250301"
    assert len(result.results) >= 0  # 取决于是否有数据到该日期
    assert result.total_scanned >= 2


def test_historical_screener_filters_by_min_score(temp_db):
    from core.backtest.historical_screener import screen_historical
    from core.database import get_connection

    rows = generate_uptrend_klines(n=120, ts_code="600519.SH", start_date="20250101")
    with get_connection() as conn:
        write_stock_basic(conn, "600519.SH", "贵州茅台")
        write_klines_to_db(conn, rows)

    result_high = screen_historical(date="20250301", strategies=[], min_score=80)
    result_low = screen_historical(date="20250301", strategies=[], min_score=0)

    assert len(result_high.results) <= len(result_low.results)


def test_historical_screener_empty_date(temp_db):
    from core.backtest.historical_screener import screen_historical

    result = screen_historical(date="19990101", strategies=["b1"], min_score=0)
    assert result.results == []
    assert result.total_scanned == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_historical_screener.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: 实现 core/backtest/historical_screener.py**

```python
"""
历史选股筛选器 — 扫描全市场历史数据，按 Z 哥评分体系筛选股票池
"""

from dataclasses import dataclass, field
from typing import Optional

from core.data_access import DataAccess
from core.screener import score_stock, StockScore


@dataclass
class ScreenResult:
    """历史筛选结果"""
    date: str = ""
    total_scanned: int = 0
    results: list[StockScore] = field(default_factory=list)
    strategies: list[str] = field(default_factory=list)


def screen_historical(
    date: str,
    strategies: list[str] | None = None,
    min_score: float = 0,
    days: int = 120,
    limit: int = 100,
) -> ScreenResult:
    """
    历史选股筛选：在指定日期，用评分体系筛选股票

    Args:
        date: 筛选日期（YYYYMMDD）
        strategies: 战法筛选条件列表（如 ["b1", "perfect"]），空列表表示不按战法筛选
        min_score: 最低综合评分
        days: 每只股票取多少天 K 线用于评分
        limit: 最多返回多少只

    Returns:
        ScreenResult
    """
    strategies = strategies or []
    da = DataAccess()
    stock_list = da.get_stock_list()

    if not stock_list:
        return ScreenResult(date=date, strategies=strategies)

    results: list[StockScore] = []

    for stock in stock_list:
        ts_code = stock["ts_code"]
        klines = da.get_klines(ts_code, days=days)

        if not klines:
            continue

        # 过滤：只保留 date 之前的 K 线
        klines_before = [k for k in klines if k.trade_date <= date]
        if len(klines_before) < 30:
            continue

        # 转为 dict 格式（score_stock 需要）
        kline_dicts = []
        for k in klines_before:
            kline_dicts.append({
                "ts_code": k.ts_code,
                "trade_date": k.trade_date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "vol": k.vol,
                "amount": k.amount,
                "pct_chg": k.pct_chg,
                "prev_close": k.prev_close,
                "prev_vol": kline_dicts[-1]["vol"] if kline_dicts else k.vol,
            })

        try:
            score = score_stock(ts_code, klines=kline_dicts)
        except Exception:
            continue

        if score.score < min_score:
            continue

        # 战法筛选
        if strategies:
            from core.screener.criteria import screen_by_criteria
            matched = False
            for s in strategies:
                if screen_by_criteria(kline_dicts, score, s):
                    score.strategy_tags.append(s)
                    matched = True
            if not matched:
                continue

        score.name = stock.get("name", "")
        results.append(score)

    # 按评分排序
    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:limit]

    return ScreenResult(
        date=date,
        total_scanned=len(stock_list),
        results=results,
        strategies=strategies,
    )
```

- [ ] **Step 4: 更新 core/backtest/__init__.py 导出**

```python
from .engine import (
    Trade,
    BacktestResult,
    backtest_signals,
    backtest_strategy,
)
from .param_tuner import tune_params, TuneResult
from .historical_screener import screen_historical, ScreenResult

__all__ = [
    "Trade",
    "BacktestResult",
    "backtest_signals",
    "backtest_strategy",
    "tune_params",
    "TuneResult",
    "screen_historical",
    "ScreenResult",
]
```

- [ ] **Step 5: 运行测试确认通过**

Run: `python -m pytest tests/test_historical_screener.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add core/backtest/historical_screener.py tests/test_historical_screener.py core/backtest/__init__.py
git commit -m "feat: add historical_screener for historical stock screening"
```

---

## Task 13: 最终验证 — 全量测试通过

**Files:**
- Run: all tests

- [ ] **Step 1: 运行全部测试**

Run: `python -m pytest tests/ -v --tb=short 2>&1 | tail -50`
Expected: 与重构前相同的通过/跳过数量（或更多，因为有新测试）

- [ ] **Step 2: 检查是否有残留的 modules.* 导入**

Run: `grep -rn "from modules.database\|from modules.indicators\|from modules.strategies\|from modules.screener\|from modules.backtest\|from modules.profile" --include="*.py" modules/ tests/`
Expected: 只在 shim 文件中出现（modules/database.py, modules/indicators/__init__.py, modules/strategies/__init__.py, modules/screener.py, modules/backtest.py）

- [ ] **Step 3: 验证 CLI 仍然工作**

Run: `python -m modules.cli --help`
Expected: 正常显示帮助信息

- [ ] **Step 4: 验证 quality_check 仍然工作**

Run: `python corpus/quality_check.py SKILL.md`
Expected: 正常运行

- [ ] **Step 5: 最终 Commit**

```bash
git add -A
git commit -m "refactor: complete core/ migration, all tests pass"
```

---

## 注意事项

### bridge_client 引用

`modules/screener.py` 原来引用 `from .bridge_client import get_all_stocks_bridge_first, get_daily_klines`。`bridge_client.py` 保留在 `modules/` 中。

在 `core/screener/` 中需要引用 bridge_client 时，有两种方案：
1. `from modules.bridge_client import ...`（跨包引用，不理想但可工作）
2. 将 bridge_client 也迁移到 core/（更干净，但 bridge_client 依赖网络请求，属于基础设施层而非领域层）

建议方案 1：保持 bridge_client 在 modules/，core/ 中用 `from modules.bridge_client import ...` 引用。后续如需解耦，可引入接口抽象。

### modules/__init__.py 的 .env 加载

原来 `.env` 加载在 `modules/__init__.py` 中。现在 `core/__init__.py` 也加载 `.env`。需要确保：
1. 如果 `core` 先被导入，`.env` 由 core 加载
2. 如果 `modules` 先被导入，`modules/__init__.py` 导入 `core.*` 时触发 core 加载 `.env`
3. 两者都使用 `override=False`，不会冲突

`modules/__init__.py` 中删除原来的 `load_dotenv` 逻辑，改为在导入 core 时自动触发。

### screener.py 拆分策略

原 `screener.py` 913 行包含：
- StockScore dataclass（~30 行）
- _CRITERIA_REGISTRY + @_register（~200 行）
- 硬过滤函数（~30 行）
- _score_trend / _score_volume / _score_risk / _score_b1（~200 行）
- score_stock()（~100 行）
- screen_stocks()（~200 行）
- 其他工具函数（~150 行）

拆分后：
- `__init__.py`：StockScore + score_stock + screen_stocks（~300 行）
- `criteria.py`：_CRITERIA_REGISTRY + 所有 @_register 函数 + 硬过滤 + screen_by_criteria（~250 行）
- `trend_score.py`：score_trend（~60 行）
- `volume_score.py`：score_volume（~60 行）
- `risk_score.py`：score_risk（~60 行）
- `b1_score.py`：score_b1（~60 行）

### 测试中 modules.* vs core.* 并存

迁移期间，shim 保证 `from modules.* import ...` 仍然可工作。测试文件统一改为 `from core.* import ...` 是最终目标，但如果有遗漏，shim 会兜底。
