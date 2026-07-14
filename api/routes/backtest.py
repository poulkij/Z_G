"""回测 + 调优路由"""

from fastapi import APIRouter
from pydantic import BaseModel
from api.schemas import (
    BacktestResultResponse, TuneResultResponse,
    ScreenResultResponse, StockScoreItem, TradeItem,
)

router = APIRouter(prefix="", tags=["回测"])


class BacktestRequest(BaseModel):
    ts_code: str
    days: int = 240
    stop_loss_pct: float = 0.07
    take_profit_pct: float = 0.15


class TuneRequest(BaseModel):
    ts_code: str
    param_grid: dict
    days: int = 240
    score_metric: str = "win_rate"


class HistoricalScreenRequest(BaseModel):
    date_range: dict
    criteria: dict = {}


@router.post("", response_model=BacktestResultResponse)
def run_backtest(req: BacktestRequest):
    """单次回测"""
    from core.backtest import backtest_strategy

    result = backtest_strategy(
        req.ts_code, days=req.days,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
    )
    return BacktestResultResponse(
        ts_code=result.ts_code,
        total_trades=result.total_trades,
        win_trades=result.win_trades,
        loss_trades=result.loss_trades,
        win_rate=result.win_rate,
        profit_factor=result.profit_factor,
        max_drawdown=result.max_drawdown,
        avg_return=result.avg_return,
        total_return=result.total_return,
        trades=[
            TradeItem(
                ts_code=t.ts_code, entry_date=t.entry_date,
                entry_price=t.entry_price,
                exit_date=t.exit_date, exit_price=t.exit_price,
                pnl=t.pnl, pnl_pct=t.pnl_pct,
                hold_days=t.hold_days, exit_reason=t.exit_reason,
            )
            for t in result.trades
        ],
    )


@router.post("/tune", response_model=TuneResultResponse)
def tune_backtest(req: TuneRequest):
    """参数调优（网格搜索）"""
    from core.backtest import tune_params

    result = tune_params(
        req.ts_code, req.param_grid,
        days=req.days, score_metric=req.score_metric,
    )
    return TuneResultResponse(
        best_params=result.best_params,
        best_score=result.best_score,
        all_results=result.all_results,
    )


@router.post("/screener", response_model=ScreenResultResponse)
def historical_screen(req: HistoricalScreenRequest):
    """历史选股筛选"""
    from core.backtest import screen_historical

    end_date = req.date_range.get("end", "")
    strategies = req.criteria.get("strategies", [])
    min_score = req.criteria.get("min_score", 0)

    result = screen_historical(
        date=end_date, strategies=strategies, min_score=min_score,
    )
    return ScreenResultResponse(
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
