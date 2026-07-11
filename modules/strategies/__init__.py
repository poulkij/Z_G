"""
向后兼容 shim — 从 core.strategies re-export

实际实现已迁移至 core/strategies/，本包仅保留以兼容
现有的 `from modules.strategies import ...` 调用。

子模块访问（如 `from modules.strategies.core import ...`）通过
同目录下的 core.py 薄壳文件转发。
"""

from core.strategies import *  # noqa: F401, F403

# 关键名称显式 re-export（其他代码直接 import 这些名字，显式声明以提升可读性）
from core.strategies import (  # noqa: F401
    StrategyType,
    Priority,
    Action,
    StrategySignal,
    get_kline_data,
    get_db_connection,
    _klines_dict_to_daily,
    _calc_kdj,
    _calc_bbi,
    detect_all_strategies,
    get_latest_signal,
    format_signal,
    analyze_with_strategies,
    detect_b1,
    detect_b2,
    detect_b3,
    detect_sb1,
    detect_changan,
    detect_sifen_zhiyi_sanyin,
    detect_nana,
    detect_yidong_dilian,
    detect_pinghang,
    detect_kengqi,
    detect_duichen_va,
    detect_s1,
    detect_s2,
    detect_s3,
    detect_brick_signals,
    detect_buy_exhaustion,
    detect_green_fat_red_thin,
    detect_staircase_distribution,
    detect_top_pinwheel,
)
