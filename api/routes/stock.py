"""个股分析路由"""

from fastapi import APIRouter, Depends
from api.deps import get_data_access
from api.schemas import (
    StockAnalysisResponse,
    KLineItem,
    IndicatorSnapshot,
    SignalItem,
    StockScoreItem,
)
from core.data_access import DataAccess

router = APIRouter(prefix="/api/stock", tags=["个股分析"])


@router.get("/{ts_code}", response_model=StockAnalysisResponse)
def get_stock_analysis(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取个股完整分析（K线 + 指标 + 信号 + 评分）"""
    from core.indicators import analyze_stock
    from core.strategies import detect_all_strategies
    from core.screener import score_stock

    klines = da.get_klines(ts_code, days=days)
    kline_items = [
        KLineItem(
            date=k.trade_date,
            open=k.open, close=k.close,
            high=k.high, low=k.low,
            volume=k.vol, pct_chg=k.pct_chg,
        )
        for k in klines
    ]

    name = ts_code
    for s in da.get_stock_list():
        if s["ts_code"] == ts_code:
            name = s["name"]
            break

    indicators = IndicatorSnapshot()
    try:
        result = analyze_stock(ts_code, days=days)
        if result:
            indicators = IndicatorSnapshot(
                k=result.k, d=result.d, j=result.j,
                dif=result.dif, dea=result.dea, macd_hist=result.macd_hist,
                rsi6=result.rsi6,
                boll_mid=result.boll_mid, boll_upper=result.boll_upper, boll_lower=result.boll_lower,
                ma5=result.ma5, ma10=result.ma10, ma20=result.ma20, ma60=result.ma60,
                vol_ratio=result.vol_ratio,
                zg_white=result.zg_white, dg_yellow=result.dg_yellow, bbi=result.bbi,
            )
    except Exception:
        pass

    signals = []
    try:
        strategy_signals = detect_all_strategies(ts_code, days=days)
        for sig in strategy_signals:
            signals.append(SignalItem(
                trade_date=sig.trade_date,
                strategy=sig.strategy.value if hasattr(sig.strategy, "value") else str(sig.strategy),
                action=sig.action if isinstance(sig.action, str) else str(sig.action),
                confidence=sig.confidence,
                price=sig.price or 0.0,
                note=sig.reason or "",
            ))
    except Exception:
        pass

    score = None
    try:
        sc = score_stock(ts_code)
        score = StockScoreItem(
            ts_code=sc.ts_code, name=sc.name,
            score=sc.score, b1_score=sc.b1_score,
            trend_score=sc.trend_score, volume_score=sc.volume_score,
            risk_score=sc.risk_score,
            reasons=sc.reasons, warnings=sc.warnings, rating=sc.rating,
        )
    except Exception:
        pass

    return StockAnalysisResponse(
        ts_code=ts_code, name=name,
        klines=kline_items, indicators=indicators,
        signals=signals, score=score,
    )


@router.get("/{ts_code}/kline", response_model=list[KLineItem])
def get_stock_kline(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取 K 线数据"""
    klines = da.get_klines(ts_code, days=days)
    return [
        KLineItem(
            date=k.trade_date, open=k.open, close=k.close,
            high=k.high, low=k.low, volume=k.vol, pct_chg=k.pct_chg,
        )
        for k in klines
    ]


@router.get("/{ts_code}/signals", response_model=list[SignalItem])
def get_stock_signals(ts_code: str, days: int = 120, da: DataAccess = Depends(get_data_access)):
    """获取战法信号"""
    from core.strategies import detect_all_strategies

    signals = []
    try:
        strategy_signals = detect_all_strategies(ts_code, days=days)
        for sig in strategy_signals:
            signals.append(SignalItem(
                trade_date=sig.trade_date,
                strategy=sig.strategy.value if hasattr(sig.strategy, "value") else str(sig.strategy),
                action=sig.action if isinstance(sig.action, str) else str(sig.action),
                confidence=sig.confidence,
                price=sig.price or 0.0,
                note=sig.reason or "",
            ))
    except Exception:
        pass
    return signals
