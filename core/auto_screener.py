#!/usr/bin/env python3
"""
自动选股层 — Screener → LoopEngine 热插拔

V4 Phase 2：每日收盘后自动跑选股策略，生成候选池，
供 ShaofuSimulator / ShaofuLoopEngine 在多头窗口内自动取票入场。

核心逻辑：
  1. 调用 core.screener.screen_stocks() 按策略筛选
  2. 沙漏评分 ≥ 阈值的优先（已验证最有效过滤器）
  3. 牛绳趋势预筛：白线在黄线之上才入候选
  4. 输出候选池 list[StockScore]，按综合评分降序

用法：
    from core.auto_screener import AutoScreener, ScreenResult

    screener = AutoScreener()
    candidates = screener.screen("b1", max_stocks=20)
    for c in candidates:
        print(f"{c.ts_code} {c.name} 评分={c.score} {c.rating}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.screener import StockScore, screen_stocks, score_stock
from core.screener._utils import get_recent_klines


# ============================================================
# 数据结构
# ============================================================


@dataclass
class ScreenResult:
    """单次选股结果"""

    trade_date: str = ""
    strategy: str = ""
    total_scanned: int = 0
    total_candidates: int = 0
    candidates: list[StockScore] = field(default_factory=list)
    skipped_reasons: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.candidates) == 0

    def top(self, n: int = 5) -> list[StockScore]:
        """返回前 N 个候选"""
        return self.candidates[:n]


# ============================================================
# 自动选股器
# ============================================================


class AutoScreener:
    """自动选股层

    封装 core.screener.screen_stocks，增加：
    - 沙漏评分过滤（默认 ≥60 分，最有效过滤器）
    - 牛绳趋势预筛（白线在黄线之上）
    - 候选池排序与截断
    """

    def __init__(
        self,
        sandglass_min: int = 60,
        bull_rope_filter: bool = True,
        max_per_day: int = 20,
    ):
        """初始化

        Args:
            sandglass_min: 沙漏评分最低阈值（0=不过滤，默认60）
            bull_rope_filter: 是否启用牛绳趋势预筛
            max_per_day: 每日最多输出候选数
        """
        self.sandglass_min = sandglass_min
        self.bull_rope_filter = bull_rope_filter
        self.max_per_day = max_per_day

    def screen(
        self,
        strategy: str = "b1",
        max_stocks: int = 0,
        trade_date: str = "",
    ) -> ScreenResult:
        """执行选股

        Args:
            strategy: 选股策略（b1/perfect/breakout/超跌/安全...）
            max_stocks: 最多扫描多少只（0=全部）
            trade_date: 指定日期（用于记录，空=今天）

        Returns:
            ScreenResult
        """
        if not trade_date:
            trade_date = datetime.now().strftime("%Y%m%d")

        result = ScreenResult(
            trade_date=trade_date,
            strategy=strategy,
        )

        # Step 1: 调用核心选股
        try:
            raw_candidates = screen_stocks(criteria=strategy, max_stocks=max_stocks)
        except Exception as e:
            result.skipped_reasons.append(f"选股引擎异常: {e}")
            return result

        result.total_scanned = len(raw_candidates)

        if not raw_candidates:
            result.skipped_reasons.append("无候选股票")
            return result

        # Step 2: 沙漏评分过滤
        filtered = []
        if self.sandglass_min > 0:
            for sc in raw_candidates:
                sg_score = self._get_sandglass(sc.ts_code)
                if sg_score >= self.sandglass_min:
                    filtered.append(sc)
                else:
                    result.skipped_reasons.append(
                        f"{sc.ts_code} 沙漏={sg_score}<{self.sandglass_min} 跳过"
                    )
        else:
            filtered = list(raw_candidates)

        # Step 3: 牛绳趋势预筛
        if self.bull_rope_filter:
            bull_filtered = []
            for sc in filtered:
                if self._check_bull_rope(sc.ts_code):
                    bull_filtered.append(sc)
                else:
                    result.skipped_reasons.append(
                        f"{sc.ts_code} 白线<黄线 跳过"
                    )
            filtered = bull_filtered

        # Step 4: 排序 + 截断
        filtered.sort(key=lambda x: x.score, reverse=True)
        if self.max_per_day > 0:
            filtered = filtered[: self.max_per_day]

        result.candidates = filtered
        result.total_candidates = len(filtered)
        return result

    def screen_single(self, ts_code: str) -> Optional[StockScore]:
        """对单只股票评分

        Args:
            ts_code: 股票代码

        Returns:
            StockScore 或 None
        """
        try:
            return score_stock(ts_code)
        except Exception:
            return None

    # ----------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------

    @staticmethod
    def _get_sandglass(ts_code: str) -> int:
        """获取沙漏评分（容错）"""
        try:
            from core.indicators import calculate_sandglass_score

            klines = get_recent_klines(ts_code, 150)
            if not klines:
                return 0
            sg = calculate_sandglass_score(klines)
            return sg.get("score", 0)
        except Exception:
            return 0

    @staticmethod
    def _check_bull_rope(ts_code: str) -> bool:
        """检查牛绳：白线在黄线之上

        Returns:
            True = 白线 >= 黄线（主力牵牛）
        """
        try:
            from core.indicators import calculate_zg_white, calculate_dg_yellow

            klines = get_recent_klines(ts_code, 150)
            if not klines or len(klines) < 20:
                return False
            white = calculate_zg_white(klines)
            yellow = calculate_dg_yellow(klines)
            return white >= yellow
        except Exception:
            return False


# ============================================================
# 模块级单例
# ============================================================

_singleton: Optional[AutoScreener] = None


def get_screener() -> AutoScreener:
    """获取全局 AutoScreener 单例"""
    global _singleton
    if _singleton is None:
        _singleton = AutoScreener()
    return _singleton


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="V4 自动选股")
    parser.add_argument("strategy", nargs="?", default="b1", help="选股策略")
    parser.add_argument("--max", type=int, default=20, help="最多输出")
    parser.add_argument("--no-sandglass", action="store_true", help="关闭沙漏过滤")
    parser.add_argument("--no-bullrope", action="store_true", help="关闭牛绳预筛")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    screener = AutoScreener(
        sandglass_min=0 if args.no_sandglass else 60,
        bull_rope_filter=not args.no_bullrope,
        max_per_day=args.max,
    )
    result = screener.screen(strategy=args.strategy, max_stocks=0)

    if args.json:
        data = {
            "trade_date": result.trade_date,
            "strategy": result.strategy,
            "total_scanned": result.total_scanned,
            "total_candidates": result.total_candidates,
            "candidates": [
                {
                    "ts_code": c.ts_code,
                    "name": c.name,
                    "score": c.score,
                    "rating": c.rating,
                    "reasons": c.reasons,
                }
                for c in result.candidates
            ],
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"{'=' * 50}")
        print(f"V4 自动选股: {result.strategy} @ {result.trade_date}")
        print(f"扫描 {result.total_scanned} 只 → 候选 {result.total_candidates} 只")
        print(f"{'=' * 50}")
        for i, c in enumerate(result.candidates, 1):
            print(f"  {i}. {c.ts_code} {c.name:<8} 评分={c.score} {c.rating}")
        if result.skipped_reasons:
            print(f"\n跳过原因 ({len(result.skipped_reasons)}):")
            for r in result.skipped_reasons[:10]:
                print(f"  - {r}")
