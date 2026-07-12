"""选股筛选路由"""

from fastapi import APIRouter, Depends, Query
from api.deps import get_data_access
from api.schemas import ScreenerResponse, StockScoreItem
from core.data_access import DataAccess

router = APIRouter(prefix="/api/screener", tags=["选股筛选"])


def _to_item(s):
    return StockScoreItem(
        ts_code=s.ts_code, name=s.name,
        score=s.score, b1_score=s.b1_score,
        trend_score=s.trend_score, volume_score=s.volume_score,
        risk_score=s.risk_score,
        reasons=list(s.reasons), warnings=list(s.warnings),
        rating=s.rating,
    )


@router.get("", response_model=ScreenerResponse)
def screen_stocks(
    strategy: str = Query("b1", description="筛选策略"),
    max_stocks: int = Query(500, description="最大扫描数量"),
    da: DataAccess = Depends(get_data_access),
):
    """选股筛选"""
    from core.screener import screen_stocks as do_screen

    try:
        scores = do_screen(criteria=strategy, max_stocks=max_stocks)
    except Exception:
        scores = []

    results = [_to_item(s) for s in scores]
    return ScreenerResponse(total=len(results), results=results)


@router.get("/score/{ts_code}", response_model=StockScoreItem)
def get_stock_score(ts_code: str, da: DataAccess = Depends(get_data_access)):
    """获取单只股票评分"""
    from core.screener import score_stock

    sc = score_stock(ts_code)
    return _to_item(sc)
