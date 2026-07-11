"""
量价形态评分
"""

from core.indicators import DailyData
from core.screener._utils import calculate_vol_ma


def score_volume_pattern(klines: list) -> tuple[float, list[str]]:
    """
    评估量价形态（P3：接入量比战法 6 场景判定）
    """
    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)

    if len(klines) < 10:
        return 50, ["数据不足"]

    today = klines[-1]
    vols = [k.vol for k in klines]
    vol_ma5 = calculate_vol_ma(vols, 5)
    vol_ratio = today.vol / vol_ma5 if vol_ma5 > 0 else 1.0

    score = 50
    reasons = []

    # ========== P3 升级：量比战法 6 场景判定（优先于简单量比计算）==========
    try:
        from core.indicators import detect_volume_ratio_strategy

        vr = detect_volume_ratio_strategy(klines)
        scenario = vr.get("scenario", "")
        action = vr.get("action", "")

        if scenario == "超级攻击":
            score += 30
            reasons.append(f"量比战法·超级攻击(量比{vr['vol_ratio']})")
        elif scenario == "攻击日":
            score += 25
            reasons.append(f"量比战法·攻击日(量比{vr['vol_ratio']})")
        elif scenario == "单向拉升":
            score += 18
            reasons.append(f"量比战法·单向拉升(量比{vr['vol_ratio']})")
        elif scenario == "出货日":
            score -= 25
            reasons.append(f"量比战法·出货日(量比{vr['vol_ratio']})→出货嫌疑")
        elif scenario == "弱势日":
            score -= 15
            reasons.append(f"量比战法·弱势日(量比{vr['vol_ratio']})")
        elif scenario == "正常震荡":
            if action == "慢买逢低吸纳":
                score += 5
                reasons.append(f"量比战法·震荡吸筹(量比{vr['vol_ratio']})")
            else:
                reasons.append("量比战法·观望")
    except Exception:
        # 降级到简单量比计算
        if vol_ratio >= 2:
            score += 20
            reasons.append(f"倍量(量比{vol_ratio:.1f}x)")
        elif vol_ratio >= 1.5:
            score += 10
            reasons.append("放量")
        elif vol_ratio <= 0.5:
            score += 10
            reasons.append("缩量")
        else:
            score -= 5
            reasons.append("量能正常")

    # 涨跌配合（保留，作为量比战法的补充验证）
    if today.pct_chg > 3 and vol_ratio > 1.2:
        score += 15
        reasons.append("价涨量增(攻击形态)")
    elif today.pct_chg < -3 and vol_ratio > 1.2:
        score -= 15
        reasons.append("价跌量增(出货嫌疑)")

    return max(0, min(100, score)), reasons
