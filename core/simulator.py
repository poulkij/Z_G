#!/usr/bin/env python3
"""
少妇模拟器 — V4 实时闭环引擎

继承 ShaofuLoopEngine，从「逐日回放」升级为「每日触发」模式：
  - 集成宏观择时（core.timing）
  - 集成自动选股（core.auto_screener）
  - 持仓全生命周期跟踪
  - 每日信号推送
  - 收盘后自动复盘

状态机：
  TIMING(择时) → SELECTING(选股) → WAITING_B1(等信号) →
  HOLDING(持仓) → EXITED(离场) → 循环

用法：
    from core.simulator import ShaofuSimulator, SimulatorConfig

    sim = ShaofuSimulator()
    sim.run_day("20260620")        # 处理单日
    sim.run_backtest("20240924", "20260707")  # 区间回测
    report = sim.report()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from core.timing import MarketTiming
from core.auto_screener import AutoScreener, ScreenResult
from core.screener._utils import get_recent_klines
from core.indicators import DailyData
from modules.loop_engine import (
    ShaofuLoopEngine,
    LoopConfig,
    LoopTrade,
    LoopState,
)


# ============================================================
# 数据结构
# ============================================================


@dataclass
class SimulatorConfig:
    """模拟器配置"""

    # 择时
    timing_enabled: bool = True
    # 选股
    screen_strategy: str = "b1"
    screen_max_per_day: int = 20
    sandglass_min: int = 60
    bull_rope_filter: bool = True
    # 引擎
    j_threshold: float = 12.0
    stop_loss_pct: float = -0.07
    min_holding_days: int = 3
    bbi_break_days: int = 2
    lu_half: bool = True
    # 组合
    max_concurrent: int = 5  # 最多同时持仓
    initial_capital: float = 1_000_000.0


@dataclass
class Position:
    """当前持仓"""

    ts_code: str
    name: str = ""
    entry_date: str = ""
    entry_price: float = 0.0
    current_price: float = 0.0
    stop_loss_price: float = 0.0
    holding_days: int = 0
    pnl_pct: float = 0.0
    partial_exits: list[dict] = field(default_factory=list)
    status: str = "OPEN"  # OPEN | CLOSED


@dataclass
class DailySignal:
    """每日信号"""

    trade_date: str
    signals: list[dict] = field(default_factory=list)  # 信号列表
    regime: str = ""  # bull | bear | unknown
    can_trade: bool = False
    new_entries: list[str] = field(default_factory=list)  # 新入场 ts_code
    exits: list[dict] = field(default_factory=list)  # 离场记录
    candidates_count: int = 0


@dataclass
class SimulatorReport:
    """模拟器报告"""

    start_date: str = ""
    end_date: str = ""
    total_days: int = 0
    trading_days: int = 0
    bull_days: int = 0
    bear_days: int = 0
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    avg_hold_days: float = 0.0
    all_trades: list[LoopTrade] = field(default_factory=list)
    daily_signals: list[DailySignal] = field(default_factory=list)
    final_capital: float = 0.0


# ============================================================
# 核心引擎
# ============================================================


class ShaofuSimulator:
    """少妇模拟器 — V4 实时闭环引擎

    状态机：
      TIMING → SELECTING → WAITING_B1 → HOLDING → EXITED → 循环

    与 ShaofuLoopEngine 的区别：
      - LoopEngine: 逐日回放单只股票的历史 K 线
      - Simulator:  每日触发，集成择时+选股+多股票持仓管理
    """

    def __init__(self, config: SimulatorConfig | None = None):
        self.config = config or SimulatorConfig()

        # 宏观择时
        self.timing = MarketTiming() if self.config.timing_enabled else None

        # 自动选股
        self.screener = AutoScreener(
            sandglass_min=self.config.sandglass_min,
            bull_rope_filter=self.config.bull_rope_filter,
            max_per_day=self.config.screen_max_per_day,
        )

        # 闭环引擎（共享配置）
        loop_cfg = LoopConfig(
            j_threshold=self.config.j_threshold,
            stop_loss_pct=self.config.stop_loss_pct,
            min_holding_days=self.config.min_holding_days,
            bbi_break_days=self.config.bbi_break_days,
            lu_half=self.config.lu_half,
            timing_enabled=self.config.timing_enabled,
        )
        self.engine = ShaofuLoopEngine(loop_cfg)

        # 持仓状态
        self.positions: dict[str, Position] = {}  # ts_code → Position
        self.completed_trades: list[LoopTrade] = []
        self.daily_signals: list[DailySignal] = []
        self.capital = self.config.initial_capital
        self.equity_curve: list[tuple[str, float]] = []

        # 候选池（每日刷新）
        self.candidate_pool: list[str] = []

    # ----------------------------------------------------------
    # 单日处理
    # ----------------------------------------------------------

    def run_day(self, trade_date: str) -> DailySignal:
        """处理单日数据

        Args:
            trade_date: 交易日期 YYYYMMDD

        Returns:
            DailySignal 当日信号汇总
        """
        signal = DailySignal(trade_date=trade_date)

        # Step 1: 宏观择时
        if self.timing:
            regime = self.timing.get_regime(trade_date)
            can = self.timing.should_trade(trade_date)
            signal.regime = regime
            signal.can_trade = can
        else:
            signal.regime = "unknown"
            signal.can_trade = True

        if not signal.can_trade:
            # 空头区间：只管理持仓，不开新仓
            signal.signals.append({"type": "TIMING", "msg": f"空头区间，禁止开仓"})
            self._manage_positions(trade_date, signal)
            self._update_equity(trade_date)
            self.daily_signals.append(signal)
            return signal

        # Step 2: 自动选股（多头窗口内）
        try:
            screen_result = self.screener.screen(
                strategy=self.config.screen_strategy,
                max_stocks=0,
                trade_date=trade_date,
            )
            signal.candidates_count = screen_result.total_candidates
            self.candidate_pool = [c.ts_code for c in screen_result.candidates]
        except Exception:
            signal.candidates_count = 0

        # Step 3: 检查候选池内的 B1 信号
        if (
            len(self.positions) < self.config.max_concurrent
            and self.candidate_pool
        ):
            slots = self.config.max_concurrent - len(self.positions)
            for ts_code in self.candidate_pool[:slots]:
                if ts_code in self.positions:
                    continue
                self._try_entry(ts_code, trade_date, signal)

        # Step 4: 管理持仓
        self._manage_positions(trade_date, signal)

        # Step 5: 更新资金曲线
        self._update_equity(trade_date)

        self.daily_signals.append(signal)
        return signal

    # ----------------------------------------------------------
    # 区间回测
    # ----------------------------------------------------------

    def run_backtest(self, start_date: str, end_date: str = "") -> SimulatorReport:
        """区间回测

        Args:
            start_date: 起始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD（空=今天）

        Returns:
            SimulatorReport
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")

        report = SimulatorReport(start_date=start_date, end_date=end_date)

        current = start_dt
        while current <= end_dt:
            d = current.strftime("%Y%m%d")
            # 跳过周末
            if current.weekday() < 5:
                sig = self.run_day(d)
                report.trading_days += 1
                if sig.regime == "bull":
                    report.bull_days += 1
                elif sig.regime == "bear":
                    report.bear_days += 1
            current += timedelta(days=1)

        report.total_days = (end_dt - start_dt).days + 1
        report.all_trades = list(self.completed_trades)
        report.total_trades = len(self.completed_trades)
        report.win_trades = sum(1 for t in self.completed_trades if t.pnl_pct > 0)
        report.loss_trades = sum(1 for t in self.completed_trades if t.pnl_pct < 0)
        report.win_rate = (
            report.win_trades / report.total_trades if report.total_trades > 0 else 0
        )
        report.avg_hold_days = (
            sum(t.holding_days for t in self.completed_trades) / report.total_trades
            if report.total_trades > 0
            else 0
        )

        # 资金曲线计算
        if self.equity_curve:
            report.final_capital = self.equity_curve[-1][1]
            report.total_return = (
                report.final_capital / self.config.initial_capital - 1
            )
            peak = self.config.initial_capital
            for _, val in self.equity_curve:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak if peak > 0 else 0
                if dd > report.max_drawdown:
                    report.max_drawdown = dd

        report.daily_signals = list(self.daily_signals)
        return report

    # ----------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------

    def _try_entry(self, ts_code: str, trade_date: str, signal: DailySignal) -> None:
        """尝试入场"""
        klines = get_recent_klines(ts_code, 150)
        if not klines or len(klines) < 30:
            return

        # 找到当天索引
        day_idx = None
        for i, k in enumerate(klines):
            if k.get("trade_date", "") == trade_date:
                day_idx = i
                break
        if day_idx is None or day_idx < 30:
            return

        # 转换为 DailyData
        daily_klines = self._to_daily_data(klines[: day_idx + 1], ts_code)
        if len(daily_klines) < 30:
            return

        # 检查 B1 入场
        entry_signal = self.engine._check_entry_internal(daily_klines, len(daily_klines) - 1)
        if entry_signal is None:
            return

        # 计算止损
        from modules.loop_engine import _calc_stop_loss_price

        stop_loss = _calc_stop_loss_price(
            daily_klines, len(daily_klines) - 1, self.engine.config.stop_loss_method
        )

        pos = Position(
            ts_code=ts_code,
            entry_date=trade_date,
            entry_price=entry_signal["entry_price"],
            current_price=entry_signal["entry_price"],
            stop_loss_price=stop_loss,
        )
        self.positions[ts_code] = pos
        signal.new_entries.append(ts_code)
        signal.signals.append(
            {
                "type": "ENTRY",
                "ts_code": ts_code,
                "price": entry_signal["entry_price"],
                "reason": entry_signal.get("reason", "B1信号"),
            }
        )

    def _manage_positions(self, trade_date: str, signal: DailySignal) -> None:
        """管理所有持仓的离场检查"""
        if not self.positions:
            return

        to_close: list[str] = []

        for ts_code, pos in list(self.positions.items()):
            klines = get_recent_klines(ts_code, 150)
            if not klines:
                continue

            # 找到当天索引
            day_idx = None
            for i, k in enumerate(klines):
                if k.get("trade_date", "") == trade_date:
                    day_idx = i
                    break
            if day_idx is None or day_idx < 30:
                continue

            daily_klines = self._to_daily_data(klines[: day_idx + 1], ts_code)

            # 构造 LoopTrade
            trade = LoopTrade(
                ts_code=ts_code,
                entry_date=pos.entry_date,
                entry_price=pos.entry_price,
                entry_reason="B1信号",
                stop_loss_price=pos.stop_loss_price,
            )
            trade.holding_days = pos.holding_days

            # 运行离场检查
            _, completed = self.engine._apply_exit_checks(daily_klines, len(daily_klines) - 1, trade)

            # 更新持仓状态
            current_price = daily_klines[-1].close
            pos.current_price = current_price
            pos.pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            pos.holding_days += 1

            if completed is not None:
                to_close.append(ts_code)
                self.completed_trades.append(completed)
                signal.exits.append(
                    {
                        "ts_code": ts_code,
                        "exit_price": completed.exit_price,
                        "reason": completed.exit_reason,
                        "pnl_pct": completed.pnl_pct,
                    }
                )
                signal.signals.append(
                    {
                        "type": "EXIT",
                        "ts_code": ts_code,
                        "price": completed.exit_price,
                        "reason": completed.exit_reason,
                        "pnl": completed.pnl_pct,
                    }
                )

        # 移除已平仓持仓
        for ts_code in to_close:
            self.positions[ts_code].status = "CLOSED"
            del self.positions[ts_code]

    def _update_equity(self, trade_date: str) -> None:
        """更新资金曲线"""
        equity = self.capital
        for pos in self.positions.values():
            equity += pos.pnl_pct / 100 * (self.config.initial_capital / self.config.max_concurrent)
        self.equity_curve.append((trade_date, equity))

    @staticmethod
    def _to_daily_data(klines: list[dict], ts_code: str) -> list[DailyData]:
        """转换 K 线字典为 DailyData 列表"""
        result = []
        for k in klines:
            result.append(
                DailyData(
                    ts_code=ts_code,
                    trade_date=k.get("trade_date", ""),
                    open=float(k.get("open", 0)),
                    high=float(k.get("high", 0)),
                    low=float(k.get("low", 0)),
                    close=float(k.get("close", 0)),
                    vol=float(k.get("vol", 0)),
                    amount=float(k.get("amount", 0)),
                    pct_chg=float(k.get("pct_chg", 0)),
                )
            )
        return result

    # ----------------------------------------------------------
    # 报告
    # ----------------------------------------------------------

    def report(self) -> str:
        """生成模拟器报告文本"""
        lines = [
            f"{'=' * 60}",
            f"V4 少妇模拟器报告",
            f"{'=' * 60}",
            f"当前持仓: {len(self.positions)} 只",
        ]
        for pos in self.positions.values():
            lines.append(
                f"  {pos.ts_code} 买入={pos.entry_price:.2f} "
                f"现价={pos.current_price:.2f} 盈亏={pos.pnl_pct:+.2f}% "
                f"持仓{pos.holding_days}天"
            )

        lines.append(f"已完成交易: {len(self.completed_trades)} 笔")
        if self.completed_trades:
            wins = sum(1 for t in self.completed_trades if t.pnl_pct > 0)
            wr = wins / len(self.completed_trades) * 100
            avg_pnl = sum(t.pnl_pct for t in self.completed_trades) / len(self.completed_trades)
            lines.append(f"  胜率: {wr:.1f}%")
            lines.append(f"  平均盈亏: {avg_pnl:+.2f}%")
            lines.append("  最近5笔:")
            for t in self.completed_trades[-5:]:
                lines.append(
                    f"    {t.entry_date}→{t.exit_date} {t.pnl_pct:+.2f}% ({t.exit_reason})"
                )

        if self.equity_curve:
            lines.append(f"资金曲线: 最新 {self.equity_curve[-1][1]:.0f}")

        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="V4 少妇模拟器")
    parser.add_argument("start", help="起始日期 YYYYMMDD")
    parser.add_argument("end", nargs="?", default="", help="结束日期")
    parser.add_argument("--strategy", default="b1", help="选股策略")
    parser.add_argument("--max-concurrent", type=int, default=5)
    args = parser.parse_args()

    cfg = SimulatorConfig(
        screen_strategy=args.strategy,
        max_concurrent=args.max_concurrent,
    )
    sim = ShaofuSimulator(cfg)
    report = sim.run_backtest(args.start, args.end)
    print(sim.report())
