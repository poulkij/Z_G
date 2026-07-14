#!/usr/bin/env python3
"""
宏观择时模块 — 活跃市值多空窗口

基于 Z 哥「活跃市值 +4% 多头 / -2.3% 空头」框架，提供日期级多空判断。
loop_engine 在入场前调用 should_trade() 做宏观择时过滤，
空头窗口内禁止开新仓，多头窗口内允许 B1 入场。

用法：
    from core.timing import MarketTiming

    timing = MarketTiming()                # 从默认 JSON 加载
    timing.is_bull("20240924")             # True
    timing.is_bear("20241115")             # True
    timing.should_trade("20240924")        # True（多头可交易）
    timing.should_trade("20241115")        # False（空头禁开仓）
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# 项目根目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATA_FILE = _PROJECT_ROOT / "data" / "market_timing_windows.json"


# ============================================================
# 工具函数
# ============================================================


def _normalize_date(d: str) -> str:
    """将日期统一归一化为 YYYYMMDD 格式

    接受:
        "20240924"      → "20240924"
        "2024-09-24"    → "20240924"
        "2024/09/24"    → "20240924"
    """
    s = d.strip().replace("-", "").replace("/", "")
    if len(s) == 8 and s.isdigit():
        return s
    # 尝试 ISO 解析
    try:
        dt = datetime.fromisoformat(d.strip())
        return dt.strftime("%Y%m%d")
    except (ValueError, TypeError):
        raise ValueError(f"无法解析日期: {d!r}，期望 YYYYMMDD 或 YYYY-MM-DD")


def _to_date(d: str) -> date:
    """归一化后转为 date 对象"""
    s = _normalize_date(d)
    return datetime.strptime(s, "%Y%m%d").date()


# ============================================================
# 数据结构
# ============================================================


@dataclass
class TimingWindow:
    """单个多空窗口"""

    start: date
    end: Optional[date]  # None 表示开放区间（至今）
    label: str  # "bull" | "bear"

    def contains(self, d: date) -> bool:
        if d < self.start:
            return False
        if self.end is None:
            return True
        return d <= self.end

    @property
    def days(self) -> int:
        if self.end is None:
            return -1  # 开放区间
        return (self.end - self.start).days + 1

    def __repr__(self) -> str:
        end_str = self.end.strftime("%Y%m%d") if self.end else "至今"
        return f"TimingWindow({self.label}: {self.start.strftime('%Y%m%d')} → {end_str}, {self.days}天)"


@dataclass
class TimingStats:
    """多空统计"""

    bull_windows: int = 0
    bear_windows: int = 0
    bull_days: int = 0
    bear_days: int = 0
    avg_bull_days: float = 0.0
    avg_bear_days: float = 0.0
    max_bull_days: int = 0
    max_bear_days: int = 0
    min_bull_days: int = 0
    min_bear_days: int = 0

    @property
    def bull_ratio(self) -> float:
        total = self.bull_days + self.bear_days
        return self.bull_days / total if total > 0 else 0.0


# ============================================================
# 核心类
# ============================================================


class MarketTiming:
    """活跃市值多空择时器

    从 JSON 文件加载多空窗口数据，提供日期级查询接口。

    数据格式（data/market_timing_windows.json）:
        {
            "windows": {
                "bull": [["2024-09-24", "2024-11-14"], ...],
                "bear": [["2024-11-15", "2025-02-05"], ...]
            }
        }

    每个窗口为 [start, end] 二元组，end 为 null 表示开放区间。
    """

    def __init__(self, data_file: str | Path | None = None):
        """初始化择时器

        Args:
            data_file: JSON 数据文件路径，None 使用默认路径
        """
        path = Path(data_file) if data_file else _DEFAULT_DATA_FILE
        self._windows: list[TimingWindow] = []
        self._stats: TimingStats = TimingStats()
        self._load(path)

    def _load(self, path: Path) -> None:
        """从 JSON 文件加载窗口数据"""
        if not path.exists():
            raise FileNotFoundError(f"择时数据文件不存在: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        windows_data = data.get("windows", {})
        bull_list = windows_data.get("bull", [])
        bear_list = windows_data.get("bear", [])

        bull_days: list[int] = []
        bear_days: list[int] = []

        for pair in bull_list:
            w = self._parse_window(pair, "bull")
            self._windows.append(w)
            if w.days > 0:
                bull_days.append(w.days)

        for pair in bear_list:
            w = self._parse_window(pair, "bear")
            self._windows.append(w)
            if w.days > 0:
                bear_days.append(w.days)

        # 排序，便于查询
        self._windows.sort(key=lambda w: w.start)

        # 统计
        self._stats.bull_windows = len(bull_list)
        self._stats.bear_windows = len(bear_list)
        self._stats.bull_days = sum(bull_days)
        self._stats.bear_days = sum(bear_days)
        self._stats.avg_bull_days = (
            self._stats.bull_days / len(bull_days) if bull_days else 0.0
        )
        self._stats.avg_bear_days = (
            self._stats.bear_days / len(bear_days) if bear_days else 0.0
        )
        self._stats.max_bull_days = max(bull_days) if bull_days else 0
        self._stats.max_bear_days = max(bear_days) if bear_days else 0
        self._stats.min_bull_days = min(bull_days) if bull_days else 0
        self._stats.min_bear_days = min(bear_days) if bear_days else 0

    @staticmethod
    def _parse_window(pair: list, label: str) -> TimingWindow:
        """解析单个窗口 [start, end]"""
        if not pair or len(pair) < 1:
            raise ValueError(f"窗口数据格式错误: {pair}")

        start = _to_date(pair[0])
        end = _to_date(pair[1]) if len(pair) > 1 and pair[1] is not None else None
        return TimingWindow(start=start, end=end, label=label)

    # ----------------------------------------------------------
    # 查询接口
    # ----------------------------------------------------------

    def is_bull(self, trade_date: str) -> bool:
        """判断某日是否在多头窗口内

        Args:
            trade_date: 日期字符串，支持 YYYYMMDD 或 YYYY-MM-DD

        Returns:
            True = 多头（活跃市值 +4% 以上，可开仓）
        """
        d = _to_date(trade_date)
        for w in self._windows:
            if w.label == "bull" and w.contains(d):
                return True
        return False

    def is_bear(self, trade_date: str) -> bool:
        """判断某日是否在空头窗口内

        Args:
            trade_date: 日期字符串

        Returns:
            True = 空头（活跃市值 -2.3% 以下，禁开仓）
        """
        d = _to_date(trade_date)
        for w in self._windows:
            if w.label == "bear" and w.contains(d):
                return True
        return False

    def should_trade(self, trade_date: str) -> bool:
        """判断某日是否允许交易

        多头窗口 = 允许开仓
        空头窗口 = 禁止开仓

        Args:
            trade_date: 日期字符串

        Returns:
            True = 可以交易（多头）
        """
        return self.is_bull(trade_date)

    def get_regime(self, trade_date: str) -> str:
        """获取某日的市场状态

        Args:
            trade_date: 日期字符串

        Returns:
            "bull" | "bear" | "unknown"
        """
        d = _to_date(trade_date)
        for w in self._windows:
            if w.contains(d):
                return w.label
        return "unknown"

    def get_current_window(self, trade_date: str) -> Optional[TimingWindow]:
        """获取某日所在的窗口对象

        Args:
            trade_date: 日期字符串

        Returns:
            TimingWindow 或 None（不在任何窗口内）
        """
        d = _to_date(trade_date)
        for w in self._windows:
            if w.contains(d):
                return w
        return None

    # ----------------------------------------------------------
    # 统计接口
    # ----------------------------------------------------------

    @property
    def stats(self) -> TimingStats:
        """返回多空统计"""
        return self._stats

    @property
    def windows(self) -> list[TimingWindow]:
        """返回所有窗口（按起始日期排序）"""
        return list(self._windows)

    def summary(self) -> str:
        """格式化择时统计摘要"""
        s = self._stats
        lines = [
            f"{'=' * 50}",
            f"活跃市值多空窗口统计",
            f"{'=' * 50}",
            f"多头窗口: {s.bull_windows} 段, 共 {s.bull_days} 天",
            f"  平均 {s.avg_bull_days:.1f} 天, 最长 {s.max_bull_days} 天, 最短 {s.min_bull_days} 天",
            f"空头窗口: {s.bear_windows} 段, 共 {s.bear_days} 天",
            f"  平均 {s.avg_bear_days:.1f} 天, 最长 {s.max_bear_days} 天, 最短 {s.min_bear_days} 天",
            f"多空比:   {s.bull_ratio:.1%} / {1 - s.bull_ratio:.1%}",
            f"{'=' * 50}",
            "窗口明细:",
        ]
        for i, w in enumerate(self._windows, 1):
            end_str = w.end.strftime("%Y%m%d") if w.end else "至今"
            tag = "🟢多头" if w.label == "bull" else "🔴空头"
            days_str = f"{w.days}天" if w.days > 0 else "开放"
            lines.append(f"  {tag} {w.start.strftime('%Y%m%d')} → {end_str}  ({days_str})")
        return "\n".join(lines)


# ============================================================
# 模块级单例（懒加载）
# ============================================================

_singleton: Optional[MarketTiming] = None


def get_timing() -> MarketTiming:
    """获取全局 MarketTiming 单例"""
    global _singleton
    if _singleton is None:
        _singleton = MarketTiming()
    return _singleton


def reset_timing(data_file: str | Path | None = None) -> MarketTiming:
    """重置单例（测试用）"""
    global _singleton
    _singleton = MarketTiming(data_file)
    return _singleton


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="活跃市值多空择时查询")
    parser.add_argument("date", nargs="?", help="查询日期（YYYYMMDD 或 YYYY-MM-DD）")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")
    args = parser.parse_args()

    timing = MarketTiming()

    if args.stats or not args.date:
        print(timing.summary())
    else:
        d = args.date
        regime = timing.get_regime(d)
        window = timing.get_current_window(d)
        can = timing.should_trade(d)

        print(f"日期: {d}")
        print(f"状态: {regime}")
        print(f"可交易: {'是' if can else '否'}")
        if window:
            end_str = window.end.strftime("%Y%m%d") if window.end else "至今"
            print(f"窗口: {window.start.strftime('%Y%m%d')} → {end_str}")
