"""
向后兼容 shim — 从 core.indicators re-export

实际实现已迁移至 core/indicators/，本包仅保留以兼容
现有的 `from modules.indicators import ...` 调用。

子模块访问（如 `from modules.indicators.core import ...`、
`from modules.indicators.data_layer import ...`）通过同目录下的
core.py / data_layer.py / kirin_detector.py / wave_theory.py /
volume_patterns.py 以及 price_patterns/__init__.py 薄壳文件转发。
"""

from core.indicators import *  # noqa: F401, F403
from core.indicators import __all__  # noqa: F401  保持 __all__ 可被外部引用

# 关键名称显式 re-export（其他代码直接 import 这些名字，显式声明以提升可读性）
from core.indicators import (  # noqa: F401
    DailyData,
    IndicatorResult,
    TradeSignal,
    analyze_stock,
    get_kline_data,
    calculate_ma,
    calculate_kdj,
    calculate_macd,
    calculate_rsi,
    calculate_bollinger,
    calculate_vol_ratio,
)
