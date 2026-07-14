"""选股筛选路由"""

from fastapi import APIRouter, HTTPException

from api.models.screen import ScreenRequest, ScreenResponse, StrategyInfo
from api.services import screen_service

router = APIRouter()


@router.get("/strategies", response_model=list[StrategyInfo])
def list_strategies():
    """列出所有可用选股策略"""
    return screen_service.get_strategies()


@router.post("/run", response_model=ScreenResponse)
def run_screen(req: ScreenRequest):
    """执行选股筛选（支持评分约束 + 基础约束过滤）"""
    try:
        return screen_service.run_screen(
            strategy=req.strategy,
            limit=req.limit,
            use_parallel=req.use_parallel,
            min_score=req.min_score,
            min_b1_score=req.min_b1_score,
            min_trend_score=req.min_trend_score,
            min_volume_score=req.min_volume_score,
            max_risk_score=req.max_risk_score,
            industry=req.industry,
            exclude_st=req.exclude_st,
            exclude_limit_up=req.exclude_limit_up,
            min_price=req.min_price,
            max_price=req.max_price,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选失败: {e}")
