"""
历史选股筛选器 — 扫描全市场历史数据，按 Z 哥评分体系筛选股票池

在指定历史日期，用评分体系对全市场股票评分并按战法/最低分筛选。
仅依赖只读 DataAccess 层，不写数据库，适合回测与训练场景。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

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
    days: int = 150,
    limit: int = 100,
) -> ScreenResult:
    """
    历史选股筛选：在指定日期，用评分体系筛选股票

    Args:
        date: 筛选日期（YYYYMMDD），只取该日及之前的 K 线
        strategies: 战法筛选条件列表（如 ["b1", "perfect"]），空列表表示不按战法筛选
        min_score: 最低综合评分
        days: 每只股票取多少交易日 K 线用于评分（按日历日 *2 估算回溯起点）
        limit: 最多返回多少只

    Returns:
        ScreenResult
    """
    strategies = list(strategies) if strategies else []
    da = DataAccess()
    stock_list = da.get_stock_list()

    if not stock_list:
        return ScreenResult(date=date, strategies=strategies)

    # 估算回溯起点：交易日 → 日历日（约 1:1.5~2，取 2 倍冗余）
    try:
        end_dt = datetime.strptime(date, "%Y%m%d")
    except ValueError:
        return ScreenResult(date=date, strategies=strategies)
    start_dt = end_dt - timedelta(days=days * 2)
    start_date = start_dt.strftime("%Y%m%d")

    results: list[StockScore] = []

    for stock in stock_list:
        ts_code = stock["ts_code"]

        # 只取 date 及之前的 K 线
        klines_before = da.get_klines_by_range(ts_code, start_date, date)
        if len(klines_before) < 30:
            continue

        # 评分（score_stock 接收 list[DailyData]）
        try:
            score = score_stock(ts_code, klines_before)
        except Exception:
            continue

        if score.score < min_score:
            continue

        # 战法筛选：screen_by_criteria 接收 (ts_code, klines, score) 元组
        if strategies:
            from core.screener.criteria import screen_by_criteria

            matched = False
            for s in strategies:
                try:
                    if screen_by_criteria((ts_code, klines_before, score), s):
                        matched = True
                        break
                except Exception:
                    continue
            if not matched:
                continue

        # 确保 name 与 stock_list 一致（score_stock 内部已查 DB，此处兜底）
        if not score.name:
            score.name = stock.get("name", "")
        results.append(score)

    # 按评分降序排序
    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:limit]

    return ScreenResult(
        date=date,
        total_scanned=len(stock_list),
        results=results,
        strategies=strategies,
    )
