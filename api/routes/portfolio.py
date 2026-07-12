"""持仓诊断路由"""

from fastapi import APIRouter
from api.schemas import (
    PortfolioDiagnoseRequest, PortfolioDiagnoseResponse, DiagnosisResponse,
)

router = APIRouter(prefix="/api/portfolio", tags=["持仓诊断"])


@router.post("/diagnose", response_model=PortfolioDiagnoseResponse)
def diagnose_holdings(req: PortfolioDiagnoseRequest):
    """持仓诊断"""
    from modules.portfolio_diagnosis import diagnose_stock

    results = []
    for ts_code in req.holdings:
        try:
            r = diagnose_stock(ts_code, days=req.days)
            results.append(DiagnosisResponse(
                ts_code=r.ts_code, name=r.name,
                price=r.price, price_position=r.price_position,
                trend_status=r.trend_status,
                kdj_j=r.kdj_j, macd_veto=r.macd_veto,
                bbi=r.bbi, white_line=r.white_line, yellow_line=r.yellow_line,
                sell_score=r.sell_score, sell_score_desc=r.sell_score_desc,
                exit_signals=list(r.exit_signals), buy_signals=list(r.buy_signals),
                kirin_phase=r.kirin_phase,
                stop_loss=r.stop_loss, target_price=r.target_price,
                recommendation=r.recommendation, risk_level=r.risk_level,
            ))
        except Exception as e:
            results.append(DiagnosisResponse(
                ts_code=ts_code, recommendation=f"诊断失败: {e}", risk_level="UNKNOWN",
            ))

    return PortfolioDiagnoseResponse(results=results)
