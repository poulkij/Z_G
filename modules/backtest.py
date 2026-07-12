"""
向后兼容 shim — 从 core.backtest re-export
"""

from core.backtest import (
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

__all__ = [
    "Trade",
    "BacktestResult",
    "PortfolioBacktestResult",
    "backtest_signals",
    "backtest_strategy",
    "backtest_multi_strategy",
    "backtest_portfolio",
]
