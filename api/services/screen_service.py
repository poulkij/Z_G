"""选股筛选服务"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 策略别名映射（与 cli.py 保持一致）
STRATEGY_ALIAS = {
    "B1": "b1",
    "B2": "b2_breakout",
    "B3": "b3_consensus",
    "完美图形": "perfect",
    "超级B1": "super_b1",
    "长安战法": "changan",
    "建仓波": "build_wave",
    "吸筹": "xishou",
    "安全": "safe",
    "超跌": "oversold",
    "突破": "breakout",
}

STRATEGY_DESCRIPTIONS = {
    "B1": "B1 买点 — J 值超卖 + 缩量回调至 BBI 附近",
    "B2": "B2 确认 — B1 后放量长阳突破",
    "B3": "B3 共识 — B2 后小阳线确认",
    "完美图形": "完美图形 — BBI 之上 + 缩量整理 + 均线多头",
    "超级B1": "超级 B1 — 多条件叠加的极强 B1",
    "长安战法": "长安战法 — B1 + 放量长阳 + 缩量分歧转一致",
    "建仓波": "建仓波 — 三波理论中的建仓阶段",
    "吸筹": "吸筹 — 麒麟会吸筹阶段特征",
    "安全": "安全 — 低风险综合筛选",
    "超跌": "超跌 — RSI/WR 超卖 + 偏离均线",
    "突破": "突破 — 放量突破关键阻力位",
}

# 每个战法的选股公式（与 core/screener/criteria.py 实现一致）
# 用 → 标注关键条件，| 分隔备选，硬过滤单独列出
STRATEGY_FORMULAS = {
    "B1": "b1_score ≥ 50\n  · J 值超卖区（J < 20）\n  · 缩量回调至 BBI 附近\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "B2": "最近 5 日内命中 detect_b2\n  · 涨幅 ≥ 4%\n  · 放量（量比 > 1.5）\n  · J < 55\n  · 无上影线或上影极短\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "B3": "最近 5 日内命中 detect_b3\n  · B2 后小阳线确认\n  · 分歧转一致（均线收敛后同向）\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "完美图形": "综合评分 ≥ 65\n  · 股价在 BBI 之上\n  · 缩量整理（量比 < 0.8）\n  · 均线多头排列（MA5 > MA10 > MA20）\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "超级B1": "最近 5 日内命中 detect_sb1\n  · 前段放量下跌\n  · 缩量企稳\n  · J 值出现负值（J < 0）\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "长安战法": "最近 5 日内命中 detect_changan\n  · B1 买点成立\n  · 放量长阳（涨幅 > 3%，量比 > 2）\n  · 缩半量分歧转一致\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "建仓波": "detect_three_waves → 建仓波\n  · confidence ≥ 0.5\n  · 三波理论第一阶段\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "吸筹": "detect_kirin_stage → 吸筹\n  · confidence ≥ 0.5\n  · 麒麟会第一阶段\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "安全": "三波 ≠ 冲刺波\n  · 麒麟会 ∉ {派发, 回落}\n  · 低风险综合筛选\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "超跌": "trend_score ≤ 40\n  · RSI6 < 20 或 WR5 > 80\n  · 偏离 MA20 过远\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
    "突破": "volume_score ≥ 70\n  · 放量突破关键阻力位\n  · 量比 > 2\n  · 非蜈蚣图 · 沙漏分 ≥ 50",
}

# 全局硬过滤（所有战法共用）
HARD_FILTER_DESC = "硬过滤：蜈蚣图排除 · 沙漏分 < 50 排除"


def get_strategies() -> list[dict]:
    """列出所有可用策略（含选股公式）"""
    return [
        {
            "alias": alias,
            "criteria": criteria,
            "description": STRATEGY_DESCRIPTIONS.get(alias, ""),
            "formula": STRATEGY_FORMULAS.get(alias, ""),
        }
        for alias, criteria in STRATEGY_ALIAS.items()
    ]


def run_screen(
    strategy: str,
    limit: int = 20,
    use_parallel: bool = True,
    *,
    min_score: float = 0,
    min_b1_score: float = 0,
    min_trend_score: float = 0,
    min_volume_score: float = 0,
    max_risk_score: float = 100,
    industry: str = "",
    exclude_st: bool = True,
    exclude_limit_up: bool = False,
    min_price: float = 0,
    max_price: float = 0,
) -> dict:
    """执行选股筛选（带约束过滤）"""
    from core.screener import screen_stocks

    criteria = STRATEGY_ALIAS.get(strategy, strategy.lower())
    scores = screen_stocks(
        criteria=criteria,
        max_stocks=limit * 5 if limit > 0 else 0,  # 多取以抵消约束过滤
        use_parallel=use_parallel,
    )

    # ── 评分约束过滤 ──
    filtered = []
    for s in scores:
        if s.score < min_score:
            continue
        if s.b1_score < min_b1_score:
            continue
        if s.trend_score < min_trend_score:
            continue
        if s.volume_score < min_volume_score:
            continue
        if s.risk_score > max_risk_score:
            continue
        filtered.append(s)

    # ── 基础约束过滤（需查 stock_basic + 最近 K 线） ──
    has_base_filter = bool(industry) or exclude_st or exclude_limit_up or min_price > 0 or max_price > 0
    if has_base_filter:
        filtered = _apply_base_filters(
            filtered,
            industry=industry,
            exclude_st=exclude_st,
            exclude_limit_up=exclude_limit_up,
            min_price=min_price,
            max_price=max_price,
        )

    # 截取 limit
    filtered = filtered[:limit]

    stocks = []
    for s in filtered:
        stocks.append({
            "ts_code": s.ts_code,
            "name": s.name,
            "score": round(s.score, 1),
            "b1_score": round(s.b1_score, 1),
            "trend_score": round(s.trend_score, 1),
            "volume_score": round(s.volume_score, 1),
            "risk_score": round(s.risk_score, 1),
            "rating": s.rating,
            "reasons": s.reasons,
            "warnings": s.warnings,
        })

    return {
        "strategy": strategy,
        "criteria": criteria,
        "count": len(stocks),
        "stocks": stocks,
    }


def _apply_base_filters(
    scores: list,
    *,
    industry: str = "",
    exclude_st: bool = True,
    exclude_limit_up: bool = False,
    min_price: float = 0,
    max_price: float = 0,
) -> list:
    """对评分结果应用基础约束（行业 / ST / 涨停 / 价格）"""
    from core.database import get_connection

    industries = {x.strip() for x in industry.split(",") if x.strip()} if industry else set()

    # 一次性查 stock_basic 和最近 K 线
    info_map: dict[str, dict[str, Any]] = {}
    latest_map: dict[str, dict[str, Any]] = {}
    try:
        with get_connection() as conn:
            if industries or exclude_st:
                ts_codes = [s.ts_code for s in scores]
                placeholders = ",".join("?" * len(ts_codes)) if ts_codes else ""
                if placeholders:
                    rows = conn.execute(
                        f"SELECT ts_code, name, industry FROM stock_basic WHERE ts_code IN ({placeholders})",
                        ts_codes,
                    ).fetchall()
                    info_map = {r["ts_code"]: dict(r) for r in rows}

            if exclude_limit_up or min_price > 0 or max_price > 0:
                ts_codes = [s.ts_code for s in scores]
                placeholders = ",".join("?" * len(ts_codes)) if ts_codes else ""
                if placeholders:
                    rows = conn.execute(
                        f"""SELECT k.ts_code, k.close, k.pct_chg, k.is_limit_up
                            FROM daily_kline k
                            WHERE k.id IN (
                                SELECT MAX(id) FROM daily_kline WHERE ts_code IN ({placeholders}) GROUP BY ts_code
                            )""",
                        ts_codes,
                    ).fetchall()
                    latest_map = {r["ts_code"]: dict(r) for r in rows}
    except Exception:
        logger.warning("基础约束查询失败，跳过基础过滤", exc_info=True)
        return scores

    result = []
    for s in scores:
        info = info_map.get(s.ts_code, {})
        latest = latest_map.get(s.ts_code, {})
        name = info.get("name", s.name) or s.name

        # ST 排除
        if exclude_st and ("ST" in name.upper() or "*ST" in name.upper()):
            continue

        # 行业过滤
        if industries:
            stock_industry = info.get("industry", "") or ""
            if stock_industry not in industries:
                continue

        # 涨停排除
        if exclude_limit_up:
            if latest.get("is_limit_up") in (1, True) or (latest.get("pct_chg", 0) or 0) >= 9.8:
                continue

        # 价格范围
        price = latest.get("close", 0) or 0
        if min_price > 0 and price < min_price:
            continue
        if max_price > 0 and price > max_price:
            continue

        result.append(s)

    return result
