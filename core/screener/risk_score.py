"""
风险评分
"""

from core.indicators import DailyData
from core.screener._utils import calculate_bbi


def score_risk(klines: list) -> tuple[float, list[str]]:
    """
    评估风险
    """
    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)

    if len(klines) < 20:
        return 50, ["数据不足"]

    today = klines[-1]
    bbi = calculate_bbi(klines)

    score = 100  # 初始100分，越高越安全
    warnings = []

    # 高位风险
    max_high = max(k.high for k in klines[-60:])
    drop_ratio = (max_high - today.close) / max_high
    if drop_ratio < 0.1:
        score -= 30
        warnings.append("接近历史高位")
    elif drop_ratio < 0.2:
        score -= 15
        warnings.append("相对高位")

    # 跌破BBI风险
    if today.close < bbi:
        score -= 20
        warnings.append("跌破BBI")

    # 放量阴线风险
    for i in range(min(5, len(klines) - 1)):
        k = klines[-(i + 1)]
        prev = klines[-(i + 2)] if i < len(klines) - 2 else None
        if prev and k.close < prev.close and k.vol > prev.vol * 1.5:
            score -= 10
            warnings.append("近期有放量阴线")
            break

    # 连续下跌
    recent_3_drop = sum(1 for k in klines[-3:] if k.close < k.prev_close)
    if recent_3_drop >= 3:
        score -= 15
        warnings.append("连续3天下跌")

    # 蜈蚣图检测（呼吸紊乱 = 高风险）
    try:
        from core.indicators import detect_centipede_pattern

        centipede = detect_centipede_pattern(klines)
        if centipede.get("is_centipede"):
            score -= 30
            warnings.append(f"蜈蚣图({centipede['score']:.0f}分)")
            warnings.append("检测到蜈蚣图风险，建议观望")
    except Exception:
        pass

    return max(0, min(100, score)), warnings
