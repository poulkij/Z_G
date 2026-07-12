"""
只读 SQLite 数据访问层 — Web/回测/训练共用
所有方法只读，不写数据库
"""

import sqlite3
from contextlib import contextmanager

from core.database import get_db_path
from core.indicators import DailyData


class DataAccess:
    """只读数据访问层"""

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or get_db_path()

    @contextmanager
    def _connect(self):
        """获取只读连接，用完即关（Windows 下避免文件锁残留）"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_klines(self, ts_code: str, days: int = 120) -> list[DailyData]:
        """获取最近 N 天 K 线数据（按日期升序）"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, trade_date, open, high, low, close,
                       vol, amount, pct_chg
                FROM daily_kline
                WHERE ts_code = ?
                ORDER BY trade_date DESC
                LIMIT ?
                """,
                (ts_code, days),
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        rows = list(reversed(rows))
        result = []
        prev_close = None
        for r in rows:
            result.append(
                DailyData(
                    ts_code=r["ts_code"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    vol=r["vol"],
                    amount=r["amount"],
                    pct_chg=r["pct_chg"],
                    prev_close=prev_close if prev_close is not None else r["open"],
                )
            )
            prev_close = r["close"]
        return result

    def get_klines_by_range(
        self, ts_code: str, start_date: str, end_date: str
    ) -> list[DailyData]:
        """按日期范围获取 K 线数据（按日期升序）"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, trade_date, open, high, low, close,
                       vol, amount, pct_chg
                FROM daily_kline
                WHERE ts_code = ? AND trade_date >= ? AND trade_date <= ?
                ORDER BY trade_date ASC
                """,
                (ts_code, start_date, end_date),
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        result = []
        prev_close = None
        for r in rows:
            result.append(
                DailyData(
                    ts_code=r["ts_code"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    vol=r["vol"],
                    amount=r["amount"],
                    pct_chg=r["pct_chg"],
                    prev_close=prev_close if prev_close is not None else r["open"],
                )
            )
            prev_close = r["close"]
        return result

    def get_stock_list(self) -> list[dict]:
        """获取股票基本信息列表"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT ts_code, name, industry, market
                FROM stock_basic
                ORDER BY ts_code
                """
            )
            rows = cursor.fetchall()

        return [
            {
                "ts_code": r["ts_code"],
                "name": r["name"],
                "industry": r["industry"],
                "market": r["market"],
            }
            for r in rows
        ]

    def get_indicator_cache(self, ts_code: str, date: str) -> dict | None:
        """获取某日指标缓存"""
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM indicator_cache
                WHERE ts_code = ? AND trade_date = ?
                """,
                (ts_code, date),
            )
            row = cursor.fetchone()

        return dict(row) if row else None

    def get_signals_by_date(self, date: str, strategy: str | None = None) -> list[dict]:
        """获取某日交易信号"""
        if strategy:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM trade_signals
                    WHERE signal_date = ? AND signal_type = ?
                    """,
                    (date, strategy),
                )
                rows = cursor.fetchall()
        else:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM trade_signals
                    WHERE signal_date = ?
                    """,
                    (date,),
                )
                rows = cursor.fetchall()

        return [dict(r) for r in rows]
