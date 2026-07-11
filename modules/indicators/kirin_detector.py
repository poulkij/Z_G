"""向后兼容 shim — 从 core.indicators.kirin_detector re-export"""

from core.indicators.kirin_detector import *  # noqa: F401, F403

# 私有名称（下划线开头）不会被 `import *` 导出，需显式 re-export 以兼容测试
from core.indicators.kirin_detector import (  # noqa: F401
    _calculate_red_green_ratio,
    _detect_n_shape_raise,
    _detect_healthy_breathing,
    _calculate_position_ratio,
)
