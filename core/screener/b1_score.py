"""
B1 买点机会评分
"""

from core.indicators import DailyData, calculate_ma
from core.screener._utils import calculate_kdj, calculate_bbi, calculate_vol_ma


def score_b1_opportunity(klines: list) -> tuple[float, list[str]]:
    """
    评估B1买点机会（P3：融入沙漏评分因子）

    返回: (评分0-100, 原因列表)
    """
    if klines and isinstance(klines[0], dict):
        klines = DailyData.from_dict(klines)

    if len(klines) < 20:
        return 0, ["数据不足"]

    today = klines[-1]
    k, d, j = calculate_kdj(klines)
    bbi = calculate_bbi(klines)
    closes = [k.close for k in klines]
    vols = [k.vol for k in klines]

    score = 0
    reasons = []

    # J值评分（核心）
    if j < -15:
        score += 35
        reasons.append(f"J值极低: {j:.2f}")
    elif j < -10:
        score += 25
        reasons.append(f"J值低位: {j:.2f}")
    elif j < 0:
        score += 15
        reasons.append(f"J值: {j:.2f}")

    # 缩量回调加分
    if today.vol < calculate_vol_ma(vols, 5) * 0.6:
        score += 20
        reasons.append("缩量回调")

    # BBI下方（低位）
    if today.close < bbi:
        score += 15
        reasons.append("BBI下方低位")

    # 价格在合理区间
    ma20 = calculate_ma(closes, 20)
    ma60 = calculate_ma(closes, 60)
    if ma20 < today.close < ma60:
        score += 15
        reasons.append("中期均线区间")

    # ========== P3 升级：沙漏因子融入 B1 评分 ==========
    try:
        from core.indicators import calculate_sandglass_score

        sg = calculate_sandglass_score(klines)
        sg_factors = sg.get("factors", {})
        sg_score = sg.get("score", 0)

        # 沙漏"缩量收敛"增强 B1 缩量回调确认
        contraction = sg_factors.get("缩量收敛", 0)
        if contraction >= 12:
            score += 10
            reasons.append(f"沙漏·缩量收敛({contraction}分)")
        elif contraction >= 8:
            score += 5
            reasons.append(f"沙漏·缩量收敛({contraction}分)")

        # 沙漏"枢轴邻近"确认低位支撑
        pivot = sg_factors.get("枢轴邻近", 0)
        if pivot >= 16:
            score += 8
            reasons.append(f"沙漏·枢轴邻近({pivot}分)")
        elif pivot >= 12:
            score += 4
            reasons.append(f"沙漏·枢轴邻近({pivot}分)")

        # 沙漏完美图形（≥80分）额外确认
        if sg.get("is_perfect"):
            score += 15
            reasons.append(f"沙漏完美图形({sg_score}分)")
        elif sg_score >= 65:
            score += 5
            reasons.append(f"沙漏良好({sg_score}分)")
    except Exception:
        pass

    # 风险提示
    if j > 0:
        score -= 10
    if today.close > bbi * 1.05:
        score -= 15

    return max(0, min(100, score)), reasons
