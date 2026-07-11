"""
趋势评分
"""

from core.indicators import DailyData, calculate_ma
from core.screener._utils import calculate_bbi


def score_trend(klines: list) -> tuple[float, str]:
    """
    评估趋势

    返回: (评分0-100, 趋势方向)
    """
    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)

    if len(klines) < 20:
        return 50, "震荡"

    closes = [k.close for k in klines]
    today = klines[-1]
    bbi = calculate_bbi(klines)

    ma5 = calculate_ma(closes, 5)
    ma20 = calculate_ma(closes, 20)
    ma60 = calculate_ma(closes, 60)

    # 趋势判断
    if ma5 > ma20 > ma60 and today.close > bbi:
        direction = "上升"
        score = 80 if today.pct_chg > 0 else 70
    elif ma5 < ma20 < ma60 and today.close < bbi:
        direction = "下降"
        score = 30
    else:
        direction = "震荡"
        score = 50

    # 短期动能
    if len(klines) >= 5:
        recent_pct = sum(k.pct_chg for k in klines[-5:])
        if recent_pct > 10:
            score += 10
        elif recent_pct < -10:
            score -= 10

    # 牛绳理论
    try:
        from core.indicators import detect_bull_rope

        rope = detect_bull_rope(klines)
        if rope.get("status") == "牵牛":
            score = min(100, score + 10)
            direction += " 牵牛"
        elif rope.get("status") == "牛绳断":
            score = max(0, score - 20)
            direction += " 牛绳断"
        elif rope.get("status") == "金叉":
            score = min(100, score + 15)
            direction += " 牛绳金叉"
        elif rope.get("status") == "死叉":
            score = max(0, score - 25)
            direction += " 牛绳死叉"
    except Exception:
        pass

    return max(0, min(100, score)), direction
