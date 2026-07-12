"""
回测包 — 引擎 + 参数调优 + 历史筛选
"""

from .engine import (
    Trade,
    BacktestResult,
    PortfolioBacktestResult,
    backtest_signals,
    backtest_strategy,
    backtest_multi_strategy,
    backtest_portfolio,
    _calc_shares,
    _calc_stats,
)
from .param_tuner import tune_params, TuneResult
from .historical_screener import screen_historical, ScreenResult

__all__ = [
    "Trade",
    "BacktestResult",
    "PortfolioBacktestResult",
    "backtest_signals",
    "backtest_strategy",
    "backtest_multi_strategy",
    "backtest_portfolio",
    "tune_params",
    "TuneResult",
    "screen_historical",
    "ScreenResult",
]
