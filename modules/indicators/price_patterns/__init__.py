"""向后兼容 shim — 从 core.indicators.price_patterns re-export"""

from core.indicators.price_patterns import *  # noqa: F401, F403
from core.indicators.price_patterns import __all__  # noqa: F401  保持 __all__ 可被外部引用
