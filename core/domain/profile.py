"""
共享数据模型 — StockProfile 基类
"""

from dataclasses import dataclass


@dataclass
class StockProfile:
    """股票定量画像基类，所有评分/诊断/评估模块共享"""

    ts_code: str = ""
    name: str = ""
    trade_date: str = ""
    close: float = 0
    pct_chg: float = 0

    k: float = 0
    d: float = 0
    j: float = 0

    dif: float = 0
    dea: float = 0
    macd_hist: float = 0

    rsi6: float = 0

    boll_mid: float = 0

    ma5: float = 0
    ma20: float = 0

    vol_ratio: float = 0
