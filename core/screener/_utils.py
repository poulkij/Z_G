"""
选股系统共享工具：K 线获取、量能/KDJ/BBI 计算、完美图形判断

本模块不依赖 core.screener 包内其他模块，避免循环导入。
"""

from core.indicators import DailyData, calculate_ma
from core.database import get_db_connection
from modules.bridge_client import get_all_stocks_bridge_first, get_daily_klines


def get_all_stocks() -> list[dict]:
    """
    获取所有股票基本信息

    优先从 bridge 获取，bridge 不可用时回退到本地 SQLite
    """
    stocks = get_all_stocks_bridge_first()
    if stocks:
        # bridge 返回的数据可能没有 market 字段，需要过滤主板/创业板/科创板
        return [s for s in stocks if s.get("market") in ("主板", "创业板", "科创板", None)]

    # 回退到本地
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ts_code, name, industry, market
        FROM stock_basic
        WHERE market IN ('主板', '创业板', '科创板')
        ORDER BY ts_code
    """)
    stocks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return stocks


def get_recent_klines(ts_code: str, days: int = 60) -> list[DailyData]:
    """
    获取近期 K 线数据

    优先从 bridge 获取，bridge 不可用时回退到本地 SQLite
    """
    rows = get_daily_klines(ts_code, days=days)
    if not rows:
        return []

    # 转换为 DailyData（升序）
    data_list = []
    for i, row in enumerate(rows):
        prev_close = rows[i - 1]["close"] if i > 0 else row["close"]
        data_list.append(
            DailyData(
                ts_code=row["ts_code"],
                trade_date=row["trade_date"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                vol=row["vol"],
                amount=row.get("amount", row["close"] * row["vol"]),
                pct_chg=row.get("pct_chg", 0.0),
                prev_close=prev_close,
            )
        )

    return data_list


def calculate_vol_ma(vols: list[float], period: int) -> float:
    """计算量能均线（复用 calculate_ma 逻辑）"""
    return calculate_ma(vols, period)


def calculate_kdj(klines: list, period: int = 9) -> tuple[float, float, float]:
    """计算 KDJ 指标，支持 DailyData 列表或 dict 列表"""
    from core.indicators import calculate_kdj as canonical_kdj

    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)
    return canonical_kdj(klines, period)


def calculate_bbi(klines: list) -> float:
    """计算 BBI 指标，支持 DailyData 列表或 dict 列表"""
    from core.indicators import calculate_bbi as canonical_bbi

    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)
    return canonical_bbi(klines)


def is_perfect_pattern(klines: list) -> tuple[bool, list[str]]:
    """
    判断是否完美图形

    完美图形条件:
    1. BBI之上
    2. 缩量整理
    3. 均线多头（可选）
    4. 非高位
    """
    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)

    if len(klines) < 30:
        return False, ["数据不足"]

    today = klines[-1]
    bbi = calculate_bbi(klines)
    closes = [k.close for k in klines]
    vols = [k.vol for k in klines]

    reasons = []
    warnings = []

    # 1. BBI之上
    if today.close > bbi:
        reasons.append("价格在BBI之上")
    else:
        warnings.append("价格在BBI下方")

    # 2. 缩量整理
    ma5_vol = calculate_vol_ma(vols, 5)
    today_vol = today.vol
    if today_vol < ma5_vol * 0.7:
        reasons.append("缩量整理")
    elif today_vol > ma5_vol * 1.5:
        warnings.append("放量突破，需观察")

    # 3. 均线多头
    ma5 = calculate_ma(closes, 5)
    ma10 = calculate_ma(closes, 10)
    ma20 = calculate_ma(closes, 20)
    if ma5 > ma10 > ma20:
        reasons.append("均线多头排列")
    elif ma5 < ma10:
        warnings.append("均线空头")

    # 4. 非高位（距历史高点跌幅充分）
    max_high = max(k.high for k in klines[-60:])
    drop_ratio = (max_high - today.close) / max_high
    if drop_ratio > 0.3:
        reasons.append(f"相对高点回调{drop_ratio * 100:.0f}%")
    elif drop_ratio < 0.1:
        warnings.append("接近历史高位")

    # 综合判断
    is_perfect = len(reasons) >= 2 and len(warnings) == 0

    return is_perfect, reasons


def _daily_to_dict(klines: list[DailyData]) -> list[dict]:
    """将 DailyData 列表转为符合战法检测需要的 dict 格式列表"""
    result = []
    for i, k in enumerate(klines):
        prev_close = klines[i - 1].close if i > 0 else k.close
        prev_vol = klines[i - 1].vol if i > 0 else k.vol

        result.append(
            {
                "ts_code": k.ts_code,
                "trade_date": k.trade_date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "vol": k.vol,
                "amount": k.amount,
                "pct_chg": k.pct_chg,
                "prev_close": prev_close,
                "prev_vol": prev_vol,
                "is_rise": k.close > prev_close,
                "is_beidou": k.vol >= prev_vol * 2,
                "is_suoliang": k.vol <= prev_vol * 0.5 if prev_vol > 0 else False,
                "is_yinxian": k.close < prev_close,
                "is_fangliang_yinxian": k.close < prev_close and k.vol > prev_vol * 1.5,
            }
        )
    return result
