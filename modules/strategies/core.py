"""向后兼容 shim — 从 core.strategies.core re-export"""

from core.strategies.core import *  # noqa: F401, F403

# 显式 re-export 下划线开头的名称（star import 不会导出）
from core.strategies.core import (  # noqa: F401
    _klines_dict_to_daily,
    _ensure_daily_klines,
    _calc_kdj,
    _calc_bbi,
    _get_kdj,
    _get_bbi,
    _get_macd_dif,
)
