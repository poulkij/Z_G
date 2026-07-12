"""
向后兼容 shim — 从 core.screener re-export

原 modules/screener.py（1139 行）已拆分为 core/screener/ 包：
- core/screener/__init__.py: StockScore/MarketStatus + score_stock + screen_stocks
- core/screener/_utils.py: K 线获取、量能/KDJ/BBI 计算、完美图形判断
- core/screener/criteria.py: 筛选条件注册表 + 硬过滤 + screen_by_criteria
- core/screener/b1_score.py: B1 买点评分
- core/screener/trend_score.py: 趋势评分
- core/screener/volume_score.py: 量价形态评分
- core/screener/risk_score.py: 风险评分
"""

from core.screener import (
    StockScore,
    MarketStatus,
    calculate_ma,
    calculate_vol_ma,
    calculate_kdj,
    calculate_bbi,
    is_perfect_pattern,
    score_b1_opportunity,
    score_trend,
    score_volume_pattern,
    score_risk,
    score_stock,
    analyze_stock,
    screen_stocks,
    format_stock_score,
    daily_workflow,
    get_market_status,
    _CRITERIA_REGISTRY,
    _register,
    _check_centipede,
    _check_sandglass_min,
    screen_by_criteria,
    _PARALLEL_THRESHOLD,
)

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
    "_CRITERIA_REGISTRY",
    "_register",
    "_check_centipede",
    "_check_sandglass_min",
    "screen_by_criteria",
    "_PARALLEL_THRESHOLD",
]


if __name__ == "__main__":
    from core.screener import main

    main()
