"""选股训练路由 — 历史筛选 + 行情数据供给"""

from fastapi import APIRouter, Depends
from api.deps import get_data_access
from api.schemas import (
    TrainingScreenRequest, TrainingScreenResponse,
    KLineRangeRequest, KLineRangeResponse,
    KLineItem, StockScoreItem,
)
from core.data_access import DataAccess

router = APIRouter(tags=["选股训练"])


@router.post("/screen", response_model=TrainingScreenResponse)
def training_screen(req: TrainingScreenRequest, da: DataAccess = Depends(get_data_access)):
    """当日战法筛选 — 选股训练 Step 2"""
    from core.backtest import screen_historical

    result = screen_historical(
        date=req.date,
        strategies=req.strategies,
        min_score=req.min_score,
        days=req.days,
    )
    return TrainingScreenResponse(
        date=result.date,
        total_scanned=result.total_scanned,
        results=[
            StockScoreItem(
                ts_code=s.ts_code, name=s.name, score=s.score,
                b1_score=s.b1_score, trend_score=s.trend_score,
                volume_score=s.volume_score, risk_score=s.risk_score,
                reasons=list(s.reasons), warnings=list(s.warnings),
                rating=s.rating,
            )
            for s in result.results
        ],
    )


@router.post("/kline", response_model=KLineRangeResponse)
def training_kline(req: KLineRangeRequest, da: DataAccess = Depends(get_data_access)):
    """按日期范围获取 K 线 — 选股训练 Step 3 行情供给"""
    klines = da.get_klines_by_range(req.ts_code, req.start_date, req.end_date)
    return KLineRangeResponse(
        ts_code=req.ts_code,
        klines=[
            KLineItem(
                date=k.trade_date, open=k.open, close=k.close,
                high=k.high, low=k.low, volume=k.vol, pct_chg=k.pct_chg,
            )
            for k in klines
        ],
    )
