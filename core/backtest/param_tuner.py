#!/usr/bin/env python3
"""
参数调优器 — 对战法参数做网格搜索，输出最优参数 + 胜率报告
"""

import os
from dataclasses import dataclass, field
from itertools import product
from typing import Any

from .engine import backtest_signals
from core.strategies import detect_all_strategies, get_kline_data


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

    # 取消代理（与 backtest_strategy 保持一致）
    os.environ["HTTP_PROXY"] = ""
    os.environ["HTTPS_PROXY"] = ""

    # 一次性取数据 + 信号，避免网格内重复查询
    klines = get_kline_data(ts_code, days)
    if not klines:
        return TuneResult()
    signals = detect_all_strategies(ts_code, days)

    all_results: list[dict[str, Any]] = []
    best_score = -1.0
    best_params: dict = {}

    for combo in combinations:
        params = dict(zip(keys, combo))
        result = backtest_signals(signals, klines, ts_code, **params)

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="回测参数网格搜索")
    parser.add_argument("ts_code", help="股票代码")
    parser.add_argument("--days", type=int, default=240, help="回测天数")
    parser.add_argument(
        "--metric", default="win_rate", choices=["win_rate", "total_return", "profit_factor"], help="评分指标"
    )
    args = parser.parse_args()

    grid = {
        "stop_loss_pct": [0.05, 0.07, 0.10],
        "take_profit_pct": [0.10, 0.15, 0.20],
    }
    res = tune_params(args.ts_code, grid, days=args.days, score_metric=args.metric)
    print(f"最优参数: {res.best_params}")
    print(f"最优得分: {res.best_score}")
    print(f"组合数:   {len(res.all_results)}")
    for r in res.all_results:
        print(
            f"  {r['params']} -> score={r['score']:.4f} "
            f"win_rate={r['win_rate']:.1%} total_return={r['total_return']:.2%} "
            f"trades={r['total_trades']}"
        )
