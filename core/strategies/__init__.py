"""
战法检测模块 — 公开 API 重导出

核心编排逻辑已在 orchestrator.py 中，本文件仅做重导出以保持向后兼容。
"""

from .orchestrator import (
    detect_all_strategies,
    get_latest_signal,
    format_signal,
    analyze_with_strategies,
)

from .core import (
    StrategyType,
    Priority,
    Action,
    StrategySignal,
    get_kline_data,
    _klines_dict_to_daily,
    _calc_kdj,
    _calc_bbi,
)
from core.database import get_db_connection, get_connection  # noqa: F401  向后兼容重导出

from .base_strategies import detect_b1, detect_b2, detect_b3, detect_sb1
from .compound_strategies import (
    detect_changan,
    detect_sifen_zhiyi_sanyin,
    detect_nana,
    detect_yidong_dilian,
    detect_pinghang,
    detect_kengqi,
    detect_duichen_va,
)
from .sell_signals import (
    detect_s1,
    detect_s2,
    detect_s3,
    detect_brick_signals,
    detect_buy_exhaustion,
    detect_green_fat_red_thin,
    detect_staircase_distribution,
    detect_top_pinwheel,
)
