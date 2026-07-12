"""
选股与择时系统
实现 Z哥 的"三最原则"和每日五步工作流

包结构：
- _utils.py: 共享工具（K 线获取、量能/KDJ/BBI 计算、完美图形判断）
- criteria.py: 筛选条件注册表 + 硬过滤 + screen_by_criteria 分发
- b1_score.py: B1 买点评分
- trend_score.py: 趋势评分
- volume_score.py: 量价形态评分
- risk_score.py: 风险评分
- __init__.py: StockScore/MarketStatus 数据类 + score_stock + screen_stocks 编排
"""

import os
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from core.database import get_connection
from core.indicators import DailyData, calculate_ma

from core.screener._utils import (
    calculate_vol_ma,
    calculate_kdj,
    calculate_bbi,
    is_perfect_pattern,
    get_all_stocks,
    get_recent_klines,
)
from core.screener.criteria import (
    CriteriaFn,
    _CRITERIA_REGISTRY,
    _register,
    _check_centipede,
    _check_sandglass_min,
    screen_by_criteria,
)
from core.screener.b1_score import score_b1_opportunity
from core.screener.trend_score import score_trend
from core.screener.volume_score import score_volume_pattern
from core.screener.risk_score import score_risk

# 并行化阈值：小于此数量不启用多进程（启动开销不值得）
_PARALLEL_THRESHOLD = 50


@dataclass
class StockScore:
    """股票评分"""

    ts_code: str
    name: str = ""
    score: float = 0  # 综合评分 0-100
    b1_score: float = 0  # B1买点评分
    trend_score: float = 0  # 趋势评分
    volume_score: float = 0  # 量价评分
    risk_score: float = 0  # 风险评分
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def rating(self) -> str:
        """评级"""
        if self.score >= 80:
            return "★★★★★ 强烈推荐"
        elif self.score >= 65:
            return "★★★★☆ 推荐"
        elif self.score >= 50:
            return "★★★☆☆ 可关注"
        elif self.score >= 35:
            return "★★☆☆☆ 谨慎"
        else:
            return "★☆☆☆☆ 不推荐"


@dataclass
class MarketStatus:
    """大盘状态"""

    trade_date: str
    is_trading: bool = True  # 是否可交易
    market_direction: str = "NEUTRAL"  # LONG/NEUTRAL/SHORT
    market_strength: float = 0  # 0-100
    reasons: list[str] = field(default_factory=list)


def score_stock(ts_code: str, klines: list[DailyData] | None = None) -> StockScore:
    """
    综合评分单只股票
    """
    if klines is None:
        klines = get_recent_klines(ts_code, 150)

    if not klines:
        return StockScore(ts_code=ts_code)

    klines[-1]

    # 获取股票名称
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM stock_basic WHERE ts_code = ?", (ts_code,))
        row = cursor.fetchone()
    name = row["name"] if row else ts_code

    # 计算各项评分
    b1_score, b1_reasons = score_b1_opportunity(klines)
    trend_score, trend_dir = score_trend(klines)
    volume_score, volume_reasons = score_volume_pattern(klines)
    risk_score, risk_warnings = score_risk(klines)

    # ========== P2 指标：三波理论 + 麒麟会 ==========
    wave_stage = "未知"
    kirin_stage = "未知"
    try:
        from core.indicators import detect_three_waves, detect_kirin_stage

        wave = detect_three_waves(klines)
        wave_stage = wave["wave"]
        if wave_stage == "建仓波" and wave["confidence"] >= 0.5:
            b1_reasons.append(f"三波·建仓波(conf={wave['confidence']})")
        elif wave_stage == "拉升波":
            b1_reasons.append(f"三波·拉升波(conf={wave['confidence']})→等回调")
        elif wave_stage == "冲刺波":
            risk_warnings.append(f"三波·冲刺波(conf={wave['confidence']})→不看")
            risk_score = max(0, risk_score - 20)

        kirin = detect_kirin_stage(klines)
        kirin_stage = kirin["stage"]
        if kirin_stage == "吸筹" and kirin["confidence"] >= 0.5:
            b1_reasons.append(f"麒麟会·吸筹({kirin['sub_type']}, conf={kirin['confidence']})")
        elif kirin_stage == "拉升":
            b1_reasons.append(f"麒麟会·拉升({kirin['sub_type']})→不追")
        elif kirin_stage == "派发":
            risk_warnings.append(f"麒麟会·派发({kirin['sub_type']})→准备走人")
            risk_score = max(0, risk_score - 30)
        elif kirin_stage == "回落":
            risk_warnings.append(f"麒麟会·回落({kirin['sub_type']})→不抄底")
            risk_score = max(0, risk_score - 15)
    except Exception:
        pass

    # ========== P3 指标：沙漏评分 ==========
    sandglass_score = 0
    sandglass_is_perfect = False
    try:
        from core.indicators import calculate_sandglass_score

        sg = calculate_sandglass_score(klines)
        sandglass_score = sg.get("score", 0)
        sandglass_is_perfect = sg.get("is_perfect", False)
        if sandglass_is_perfect:
            b1_reasons.append(f"沙漏完美图形({sandglass_score:.0f}分)")
    except Exception:
        pass

    # 综合评分（加权平均）
    # B1机会 30% + 趋势 25% + 量价 25% + 风险 20%
    total_score = b1_score * 0.3 + trend_score * 0.25 + volume_score * 0.25 + risk_score * 0.2

    # 完美图形额外加分
    is_perfect, perfect_reasons = is_perfect_pattern(klines)
    if is_perfect:
        total_score = min(100, total_score * 1.1)
        b1_reasons.extend(perfect_reasons)

    # 三波/麒麟会加权调整
    if wave_stage == "建仓波":
        total_score = min(100, total_score * 1.05)
    elif wave_stage == "冲刺波" or kirin_stage == "派发":
        total_score = max(0, total_score * 0.7)
    elif kirin_stage == "吸筹":
        total_score = min(100, total_score * 1.08)

    # 沙漏完美图形加分
    if sandglass_is_perfect:
        total_score = min(100, total_score + 10)

    score = StockScore(
        ts_code=ts_code,
        name=name,
        score=round(total_score, 1),
        b1_score=round(b1_score, 1),
        trend_score=round(trend_score, 1),
        volume_score=round(volume_score, 1),
        risk_score=round(risk_score, 1),
        reasons=b1_reasons + volume_reasons,
        warnings=risk_warnings,
    )

    return score


# ==================== 并行化 Worker ====================


def _analyze_worker(ts_code: str) -> tuple[str, list[DailyData], StockScore] | None:
    """
    并行 worker：评分单只股票
    必须在模块顶层定义，以便 ProcessPoolExecutor 可以 pickle
    返回: (ts_code, klines, score) 或 None
    """
    klines = get_recent_klines(ts_code, 150)
    if not klines or len(klines) < 30:
        return None
    score = score_stock(ts_code, klines)
    return ts_code, klines, score


def screen_stocks(
    criteria: str = "b1", max_stocks: int = 0, max_workers: int = 0, use_parallel: bool = True
) -> list[StockScore]:
    """
    选股筛选（支持多进程并行）

    criteria:
    - "b1": B1买点机会
    - "perfect": 完美图形
    - "breakout": 突破形态
    - "oversold": 超跌反弹
    - "super_b1": 超级B1（放量下跌+缩量企稳+J负值）
    - "changan": 长安战法（B1+放量长阳+缩半量）
    - "b2_breakout": B2突破（涨幅≥4%+放量+J<55+无上影线）
    - "b3_consensus": B3分歧转一致
    - "build_wave": 建仓波（三波理论·建仓波）
    - "xishou": 吸筹阶段（麒麟会·吸筹）
    - "safe": 安全选股（非冲刺波 + 非派发/回落）
    - "bull_rope": 牛绳牵牛形态（白在黄上，且白线向上）
    - "sandglass_perfect": 沙漏完美图形（评分>=80）
    - "volume_ratio_super": 量比战法（立即买或强势攻击场景）

    max_stocks: 最大扫描数量，0=全量（默认500只性能保护）
    max_workers: 并行进程数，0=自动（CPU核心数）
    use_parallel: 是否启用多进程并行（<50只时自动关闭）

    返回：满足条件的 StockScore 列表（按评分降序）
    """
    stocks = get_all_stocks()
    limit = max_stocks if max_stocks > 0 else 500
    stocks = stocks[:limit]

    results: list[StockScore] = []

    # 小数据量时禁用并行（启动开销不值得）
    if not use_parallel or len(stocks) < _PARALLEL_THRESHOLD:
        # 串行模式
        for stock in stocks:
            result = _analyze_worker(stock["ts_code"])
            if result and screen_by_criteria(result, criteria):
                results.append(result[2])
    else:
        # 并行模式：只并行 score_stock，筛选在主进程串行
        workers = max_workers or os.cpu_count() or 4
        try:
            from concurrent.futures import ProcessPoolExecutor, as_completed

            ts_codes = [s["ts_code"] for s in stocks]

            with ProcessPoolExecutor(max_workers=workers) as executor:
                future_map = {executor.submit(_analyze_worker, ts_code): ts_code for ts_code in ts_codes}
                for future in as_completed(future_map):
                    result = future.result()
                    if result and screen_by_criteria(result, criteria):
                        results.append(result[2])
        except Exception:
            # 并行失败回退到串行
            for stock in stocks:
                result = _analyze_worker(stock["ts_code"])
                if result and screen_by_criteria(result, criteria):
                    results.append(result[2])

    # 按评分排序
    results.sort(key=lambda x: x.score, reverse=True)
    return results


def get_market_status() -> MarketStatus:
    """
    获取大盘状态（简化版，用主要指数代替）
    """
    today = datetime.now().strftime("%Y%m%d")

    # 获取沪深300成分股简单评估
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ts_code FROM stock_basic
            WHERE market IN ('主板')
            LIMIT 100
        """)
        stocks = [row["ts_code"] for row in cursor.fetchall()]

        rise_count = 0
        total_count = 0

        for ts_code in stocks[:20]:
            cursor.execute(
                """
                SELECT pct_chg FROM daily_kline
                WHERE ts_code = ?
                ORDER BY trade_date DESC
                LIMIT 1
            """,
                (ts_code,),
            )
            row = cursor.fetchone()
            if row:
                total_count += 1
                if row["pct_chg"] > 0:
                    rise_count += 1

    # 计算涨跌家数比
    if total_count > 0:
        rise_ratio = rise_count / total_count
    else:
        rise_ratio = 0.5

    # 大盘状态判断
    if rise_ratio >= 0.6:
        direction = "LONG"
        strength = 75
        reasons = ["上涨家数占优", "市场活跃"]
    elif rise_ratio <= 0.4:
        direction = "SHORT"
        strength = 25
        reasons = ["下跌家数较多", "注意风险"]
    else:
        direction = "NEUTRAL"
        strength = 50
        reasons = ["多空均衡", "观望为主"]

    return MarketStatus(
        trade_date=today, is_trading=True, market_direction=direction, market_strength=strength, reasons=reasons
    )


def format_stock_score(score: StockScore) -> str:
    """格式化股票评分"""
    return f"""
{score.ts_code} {score.name}
{"=" * 50}
综合评分: {score.score:.1f}/100 {score.rating}
{"=" * 50}
B1买点评分: {score.b1_score:.1f}
趋势评分: {score.trend_score:.1f}
量价评分: {score.volume_score:.1f}
风险评分: {score.risk_score:.1f}

利好因素:
{chr(10).join(f"  + {r}" for r in score.reasons) if score.reasons else "  无"}

风险提示:
{chr(10).join(f"  ! {w}" for w in score.warnings) if score.warnings else "  无"}
"""


def daily_workflow() -> dict[str, Any]:
    """
    每日五步工作流

    返回分析结果
    """
    print("=" * 60)
    print("Z哥 每日五步工作流")
    print("=" * 60)

    # Step 1: 择时（1分钟）
    print("\n[Step 1] 择时判断")
    market = get_market_status()
    print(f"大盘状态: {market.market_direction}")
    print(f"市场强度: {market.market_strength}/100")
    for reason in market.reasons:
        print(f"  - {reason}")

    if market.market_direction == "SHORT":
        print("  => 建议: 轻仓或空仓观望")

    # Step 2: 定策略（2分钟）
    print("\n[Step 2] 策略制定")
    if market.market_direction == "LONG":
        print("  => 多头策略: 主攻")
    elif market.market_direction == "SHORT":
        print("  => 空头策略: 防守")
    else:
        print("  => 中性策略: 观望/底仓不动")

    # Step 3: 选股（5分钟）
    print("\n[Step 3] 选股")
    b1_stocks = screen_stocks("b1")[:5]
    perfect_stocks = screen_stocks("perfect")[:5]

    print("B1买点机会 (TOP 5):")
    for i, s in enumerate(b1_stocks[:5], 1):
        print(f"  {i}. {s.ts_code} {s.name} 评分:{s.score:.0f}")

    print("\n完美图形 (TOP 5):")
    for i, s in enumerate(perfect_stocks[:5], 1):
        print(f"  {i}. {s.ts_code} {s.name} 评分:{s.score:.0f}")

    # Step 4: 执行计划
    print("\n[Step 4] 执行计划")
    print("  - 严格按条件执行，不临时改变")
    print("  - 量比战法/B1/滴滴战法对应触发条件")

    # Step 5: 复盘准备
    print("\n[Step 5] 复盘准备")
    print("  - 记录今日操作")
    print("  - 明日重点关注股票")

    return {
        "market": market,
        "b1_opportunities": b1_stocks[:5],
        "perfect_patterns": perfect_stocks[:5],
    }


# ==================== 命令行工具 ====================


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Z哥 选股系统")
    parser.add_argument(
        "action", choices=["score", "screen", "workflow"], help="操作: score=单股评分, screen=选股, workflow=每日工作流"
    )
    parser.add_argument("--ts_code", help="股票代码")
    parser.add_argument(
        "--criteria",
        default="b1",
        choices=[
            "b1",
            "perfect",
            "breakout",
            "oversold",
            "super_b1",
            "changan",
            "b2_breakout",
            "b3_consensus",
            "build_wave",
            "xishou",
            "safe",
            "bull_rope",
            "sandglass_perfect",
            "volume_ratio_super",
        ],
        help="选股条件",
    )
    parser.add_argument("--limit", type=int, default=10, help="返回数量")
    parser.add_argument("--max-stocks", type=int, default=0, help="最大扫描数量(0=全量)")
    parser.add_argument("--workers", type=int, default=0, help="并行进程数，0=自动（CPU核心数）")
    parser.add_argument("--no-parallel", action="store_true", help="禁用多进程并行")

    args = parser.parse_args()

    if args.action == "score":
        if not args.ts_code:
            print("请指定股票代码: --ts_code 000001.SZ")
            return
        score = score_stock(args.ts_code)
        print(format_stock_score(score))

    elif args.action == "screen":
        import time

        start = time.time()
        results = screen_stocks(
            criteria=args.criteria,
            max_stocks=args.max_stocks,
            max_workers=args.workers,
            use_parallel=not args.no_parallel,
        )
        elapsed = time.time() - start
        mode = "并行" if not args.no_parallel and len(results) >= _PARALLEL_THRESHOLD else "串行"
        print(f"\n{'=' * 60}")
        print(f"选股结果 ({args.criteria}) 共{len(results)}只 | {mode}模式 | 耗时{elapsed:.1f}s")
        print(f"{'=' * 60}")
        for i, s in enumerate(results[: args.limit], 1):
            print(f"{i:2}. {s.ts_code} {s.name:<8} 评分:{s.score:5.1f}  B1:{s.b1_score:5.1f}")
            if s.reasons:
                print(f"    利好: {', '.join(s.reasons[:2])}")
            if s.warnings:
                print(f"    风险: {', '.join(s.warnings[:1])}")

    elif args.action == "workflow":
        daily_workflow()


# 向后兼容别名：原 analyze_stock 已重命名为 score_stock
analyze_stock = score_stock


__all__ = [
    "StockScore",
    "MarketStatus",
    "calculate_ma",
    "calculate_vol_ma",
    "calculate_kdj",
    "calculate_bbi",
    "is_perfect_pattern",
    "score_b1_opportunity",
    "score_trend",
    "score_volume_pattern",
    "score_risk",
    "score_stock",
    "analyze_stock",
    "screen_stocks",
    "format_stock_score",
    "daily_workflow",
    "get_market_status",
    "CriteriaFn",
    "_CRITERIA_REGISTRY",
    "_register",
    "_check_centipede",
    "_check_sandglass_min",
    "screen_by_criteria",
    "_PARALLEL_THRESHOLD",
]


if __name__ == "__main__":
    main()
