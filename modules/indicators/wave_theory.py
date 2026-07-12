"""向后兼容 shim — 从 core.indicators.wave_theory re-export"""

from core.indicators.wave_theory import *  # noqa: F401, F403

# 私有名称（下划线开头）不会被 `import *` 导出，需显式 re-export 以兼容测试
from core.indicators.wave_theory import (  # noqa: F401
    _find_recent_low,
    _count_limit_up,
)
