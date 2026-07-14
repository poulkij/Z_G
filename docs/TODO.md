# TODO

> Zettaranc Skill 待办清单
> 更新日期：2026-07-12
> 当前版本：v4.0.0
> 状态：✅ 已完成 / ⏳ 进行中 / 📋 待规划

---

## ✅ 已完成（v3.3.1 Web 搜索模糊化 + 选股约束面板）

### 股票搜索改造
- [x] 后端 `search_stocks` 改用 `re.search` 正则匹配（代码+名称任一命中，IGNORECASE）
- [x] 新增前端 `StockSearchInput` 通用搜索组件（debounce + 下拉候选 + 键盘导航 + 输入类型识别 + 搜索历史）
- [x] 替换 Dashboard Hero / Header ⌘K / Watchlist 添加三处搜索入口

### 选股筛选增强
- [x] `ScreenRequest` 新增 10 个约束字段（5 评分 + 5 基础）
- [x] `screen_service` 实现两层过滤：评分约束（内存）+ 基础约束（DB 查询）
- [x] 新增 `STRATEGY_FORMULAS` 字典：11 个战法选股公式文本
- [x] 前端 `Screener.tsx` 重写：选股公式卡片 + 约束面板（滑块/输入/复选框）+ 分类标签
- [x] 新增 `tests/test_screen_service.py` 8 个约束过滤用例

---

## ✅ 已完成（v3.3.0 Skill-Schema-V2 合规改造）

### Schema 对齐（V2 三表面 + 安全边界）
- [x] YAML frontmatter description 改为路由触发器格式（Load when / Do NOT load / Risk level）
- [x] 新增 路由声明（Routing Surface）：触发条件表格 + 不加载场景 + 优先级规则
- [x] 新增 契约（Contract Surface）：输入契约（5 类输入）、输出契约（5 类任务验收标准）、边界与限制
- [x] 新增 运行时资源索引（Runtime Boundary）：12 知识文件加载时机 + 6 工具链调用条件 + 5 失败退路
- [x] 新增 安全边界（Safety Surface）：高风险动作规则 + 人类确认点（3 个必须停下来的场景）+ 禁区（6 条绝对红线）+ 版本追踪
- [x] 质量门升级：新增 4 项 V2 表面检查（路由/契约/运行时/安全），12/12 全通过

### 知识文件补完
- [x] 23 个 knowledge/*.md 添加 Skill-Runtime 元数据头部（加载时机 + 用途 + 大小）

---

## ✅ 已完成（v3.2.0 P3 指标接入 screener + 数据层整合）

### 编排模式与角色扩展
- [x] 用户问题自动路由到对应模块（股票/投资、人生/职业决策、创业/商业判断）
- [x] 核心心智模型扩展 +3（人生四圈框架、职业发展四层模型、时代主线判断）
- [x] 知识文件扩展 +3（life-decision.md、career-development.md、business-judgment.md）
- [x] 决策启发式扩展 +14 条（人生/职业决策 +10、创业/商业判断 +4）
- [x] 蒸馏流程执行：采集 499 个语料文件，提取 9 个核心模型，三重验证通过
- [x] 路由逻辑测试用例 +15 个

---

## ✅ 已完成（v2.10.0 工程质量）

### CLI 修复与统一入口
- [x] 修 3 个必修 CLI bug（cmd_screen 字段错位 / cmd_watchlist scan key 不匹配 / 11 种 strategy 中文别名映射）
- [x] 6 业务脚本薄壳化（3623 → 203 行，-94%）
- [x] 5 个独立 main() 合并到 zt 统一入口（7 个顶层命令 + 9 个子动作）
- [x] 6 语料脚本迁 `corpus/`

### CI 与质量护栏
- [x] 5 个 CI job（test / lint / quality-gate / e2e-realdata / pre-commit）
- [x] SKILL.md 质量门接 CI（`corpus/quality_check.py --json --strict`）
- [x] pre-commit 钩子（ruff + mypy + 质量门 + 标准文件检查）
- [x] 真实数据回归（600519.SH × MACD/KDJ/RSI vs stk_factor）
- [x] 限流升级 multiprocessing 安全（token bucket + 滑动窗口）

### 测试覆盖
- [x] 测试从 264 → 367 passed, 10 skipped
- [x] 新增 5 个测试文件（cli_screen / cli_subparser / data_sync_extensions / rate_limiter / indicators_realdata / quality_check）
- [x] trade_parser（53）、tushare_client（27）、report（54）三模块从零覆盖

### 代码审查
- [x] 源码 bug 修复（`_fmt_opt` 缺 `sign` 参数 + `render_assessment` f-string 语法错误）
- [x] 移除 `zettaranc_voice.py`（-492 行），常量迁移至 `trade_reviewer.py`
- [x] 死代码清零 + NameError 修复 + 硬编码路径清零

---

## ✅ 已完成（v2.9.0 性能与架构优化）

### 性能极限优化
- [x] 指标计算向量化（60x 提速）：Pandas 原生重写 MACD/KDJ/BBI，与通达信精度一致
- [x] SQLite 写入加速（10x-50x）：`executemany` 批量插入替换 `iterrows` 单行插入
- [x] 多线程并发拉取：`ThreadPoolExecutor`（5 并发）+ 线程安全限流锁
- [x] SQLite WAL 模式：解决并发 `Database is locked` 问题

### 策略智能升级（MDC 2.0）
- [x] 多维验证体系：资金流 + 布林带 + DMI 动能加分/权重机制
- [x] 麒麟阶段背景校验：B1/B2 根据吸筹/拉升/派发阶段动态调整置信度
- [x] 资金流深度对齐：S1/长安战法校验主力大单净流入/流出比例
- [x] DMI 趋势过滤：ADX 高位动能竭尽 + DI 趋势金叉验证

### 架构解耦
- [x] `strategies.py`（1700 行）→ `strategies/` 包（6 子模块：core/base/compound/kirin/sell/vectorized）
- [x] 向后兼容：`__init__.py` 保留 API，264 用例 100% 通过

---

## ✅ 已完成（v2.8.0 意图识别编排层）

- [x] 意图识别规则引擎（rules/intent_rules.yaml）
- [x] 四意图路由：stock / career / life / chat
- [x] 向量知识库适配器（modules/knowledge_retriever.py，Qdrant RAG，默认关闭）
- [x] LLM 生成层（MiniMax / OpenAI 兼容，可选）
- [x] Z哥职业决策框架（rules/career_prompt.md）
- [x] Z哥人生决策框架（rules/life_prompt.md）
- [x] 交互式聊天界面（modules/intent_chat.py）
- [x] 配置指南文档（docs/CONFIG_GUIDE.md）

---

## ✅ 已完成（v3.1.0 P3 指标补完）

- [x] **蜈蚣图识别** — `detect_centipede_pattern()` in `modules/indicators/price_patterns.py`
  - 5 因子评分（长上影/长下影/十字星/量能无规律/价格无趋势），≥60 分判定为蜈蚣图
- [x] **牛绳理论量化** — `detect_bull_rope()` in `modules/indicators/price_patterns.py`
  - 基于白线/黄线关系判定：牵牛/牛绳断/金叉/死叉 + 缺口百分比 + 白线趋势
- [x] **量比战法引擎** — `detect_volume_ratio_strategy()` in `modules/indicators/volume_patterns.py`
  - 6 种场景判定（攻击日/出货日/单向拉升/正常震荡/弱势日/超级攻击）
- [x] **沙漏评分 V9** — `calculate_sandglass_score()` in `modules/indicators/price_patterns.py`
  - 5 因子评分（缩量收敛/枢轴邻近/量能斜率/均线结构/事件风险），≥80 分为完美图形

> 测试：523 passed, 10 skipped（新增 ~156 用例）

---

## ✅ 已完成（v3.2.0 P3 指标接入 screener + 数据层整合）

### P3 指标深度接入评分体系
- [x] **量比战法融入 `score_volume_pattern`**：6 场景判定（超级攻击+30/攻击日+25/单向拉升+18/出货日-25/弱势日-15/震荡吸筹+5），降级回简单量比计算
- [x] **沙漏评分融入 `score_b1_opportunity`**：3 因子增强（缩量收敛+10/+5、枢轴邻近+8/+4、完美图形+15/良好+5）
- [x] **CLI choices 补全**：`bull_rope` / `sandglass_perfect` / `volume_ratio_super` 正式可用
- [x] 新增 `tests/test_screener_p3.py`：14 个用例（量比 6 场景 + 沙漏 B1 + 注册表验证）
- [x] 测试：36 passed（原有 22 + 新增 14），0 破坏

### 数据层整合（skill ↔ tushare-data-bridge）
- [x] **新增 `modules/bridge_client.py`**：封装 bridge HTTP API（5 个端点）
  - 3 种运行模式：`auto` / `always` / `never`（`TUSHARE_BRIDGE_ENABLED` 控制）
  - 降级网关：bridge 不通时自动回退到本地 SQLite
- [x] **改造 `modules/screener.py` 数据接入层**：`get_all_stocks()` / `get_recent_klines()` 优先 bridge，失败回退本地
- [x] 新增 `tests/test_bridge_client.py`：20 个用例（配置/健康检查/GET/POST/降级网关）
- [x] 测试：56 passed（screener 36 + bridge 20），0 破坏

---

## 📋 待实现

（暂无）

---

## ✅ 已完成（v4.0.0 少妇模拟器完整版）

### Phase 1：宏观择时层 — 活跃市值量化
- [x] `data/market_timing_windows.json`：7 段多头 + 7 段空头历史窗口（2024-09 至今）
- [x] `core/timing.py` MarketTiming 模块：多空窗口查询 + 统计 + 单例
- [x] `LoopConfig` 新增 `timing_enabled` / `timing_data_file` 开关
- [x] `loop_engine.py` 入场前调用 `_should_trade_by_timing()` 门控
- [x] 择时门控单元测试 6 例

### Phase 2：自动选股层 — Screener → Engine 热插拔
- [x] `core/auto_screener.py` AutoScreener：封装 screen_stocks + 沙漏过滤 + 牛绳预筛
- [x] `ScreenResult` 数据结构 + 单例 + CLI 入口

### Phase 3：ShaofuSimulator 实时引擎
- [x] `core/simulator.py` ShaofuSimulator：集成 timing + screener + loop_engine
- [x] 状态机：TIMING → SELECTING → WAITING_B1 → HOLDING → EXITED 循环
- [x] 每日信号 `DailySignal` + 持仓 `Position` + 报告 `SimulatorReport`
- [x] 区间回测 `run_backtest()` + 单日处理 `run_day()`
- [x] 模拟器集成测试 5 例

### Phase 4：S1/S2/S3 卖出体系深度集成
- [x] `LoopConfig` 新增 `sell_signals_enabled` / `sell_score_min_hold`
- [x] `_check_sell_signals()`：S1（大绿帽）→ S2（顶背离）→ S3（最后逃生）优先级检测
- [x] `_check_anti_sell_fly()`：防卖飞评分 ≥4 时覆盖离场，保护利润
- [x] 卖出体系测试 5 例

### Phase 5：CLI 集成 + 测试覆盖
- [x] `zt simulate` 子命令：区间回测 + JSON 输出 + 6 个开关
- [x] 全量测试：754 passed, 43 skipped，0 破坏
- [x] V4 测试新增 17 例（择时 6 + 卖出 5 + 模拟器 5 + 配置 1）

---

## ⏳ 进行中

### Phase 3: SKILL.md 拆分（数据字典外迁 → 心智模型拆分）
- [ ] 数据字典外迁至 `knowledge/data_dictionary.md` + `knowledge/signal_dictionary.md`
- [ ] 心智模型独立文件（6 个）+ 启发式索引
- [ ] 主文件保留"角色扮演规则 + 表达 DNA + 诚实边界"核心

---

## 版本路线图

| 版本 | 主题 | 状态 |
|------|------|------|
| **v2.4.0** | CLI 工具 + 回测框架 + 递推修复 | ✅ 已完成 |
| **v2.5.0** | P0/P1 指标补全 + 工程化补完 | ✅ 已完成 |
| **v2.6.0** | P2 核心模块（三波理论/麒麟会） | ✅ 已完成 |
| **v2.7.0** | 数据层充实 + SAT/UAT 测试 + 使用手册 | ✅ 已完成 |
| **v2.8.0** | 意图识别编排层 + RAG + 可选 LLM | ✅ 已完成 |
| **v2.9.0** | 性能极限优化（60x/多线程/WAL）+ MDC 2.0 + 架构解耦 | ✅ 已完成 |
| **v2.10.0** | CLI 修复 + 脚本薄壳化 + 5 CI job + 501 测试 + 代码审查 | ✅ 已完成 |
| **v3.0.0** | 编排模式 + 人生/创业蒸馏 + 双维度扩展 | ✅ 已完成 |
| **v3.1.0** | P3 指标补完（蜈蚣图/牛绳理论/量比战法/沙漏 V9） | ✅ 已完成 |
| **v4.0.0** | 少妇模拟器完整版（自动择时+选股+买入+卖出闭环回测） | ✅ 已完成 |

---

## 下一迭代候选（v3.2.0 候选）

- CI 观察期 4 个 job 改为 required（lint / quality-gate / e2e-realdata / pre-commit）
- 真实数据 diff 阈值收紧到 2%
- SKILL.md 拆分（32K 字 → 6 心智模型独立文件 + 30 启发式索引）
- 活跃市值 +4%/-2.3% 量化层（需指南针数据源）
- P3 指标集成到 screener（蜈蚣图作为风险扣分项、沙漏评分作为选股加分项）
