"""个股分析路由"""

import re

from fastapi import APIRouter, Depends, Query
from api.deps import get_data_access
from api.schemas import (
    StockAnalysisResponse,
    KLineItem,
    IndicatorSnapshot,
    SignalItem,
    StockScoreItem,
    StockSearchItem,
    StockSearchResponse,
)
from core.data_access import DataAccess

router = APIRouter(prefix="", tags=["个股分析"])


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


@router.get("/search/all", response_model=StockSearchResponse)
def search_stocks(
    q: str = Query("", description="股票代码或名称关键字（正则匹配，大小写不敏感）"),
    limit: int = Query(20, ge=1, le=100, description="最大返回数量"),
    da: DataAccess = Depends(get_data_access),
):
    """按代码或名称正则搜索股票（用于选股页搜索框）

    支持以下输入（均使用 re.search 正则匹配，大小写不敏感）：
    - 6 位数字代码：如 `000807` → 匹配 ts_code（前缀命中 000807.SZ）
    - 带后缀代码：如 `000807.SZ` 或 `sh` → 匹配 ts_code
    - 中文名称/简称：如 `云铝`、`茅台` → 匹配 name
    - 混合：如 `600` → 命中所有 600 开头的代码
    - 拼音/英文：暂不支持（DB 无拼音字段）
    """
    keyword = q.strip()
    if not keyword:
        return StockSearchResponse(results=[])

    # 构造正则：转义用户输入避免特殊字符破坏正则，IGNORECASE 便于匹配 SH/SZ
    # 代码部分去掉后缀（如 "000807.SZ" → "000807"），便于前缀命中
    code_prefix = keyword.split(".")[0]
    code_re = re.compile(re.escape(code_prefix), re.IGNORECASE)
    name_re = re.compile(re.escape(keyword), re.IGNORECASE)

    stocks = da.get_stock_list()
    matched = []

    for s in stocks:
        ts_code = s["ts_code"]
        name = s.get("name", "")
        # 代码或名称任一正则命中即收录
        if code_re.search(ts_code) or name_re.search(name):
            matched.append(s)
        if len(matched) >= limit:
            break

    return StockSearchResponse(
        results=[
            StockSearchItem(ts_code=m["ts_code"], name=m.get("name", ""), industry=m.get("industry", ""))
            for m in matched
        ]
    )


# ── 新前端路由（调 stock_service，返回完整分析数据） ──


@router.get("/analyze/{ts_code}")
def analyze_stock_full(ts_code: str, days: int = 120):
    """完整分析：指标 + 三波 + 麒麟会 + 战法信号 + 诊断 + 评分（对齐前端 StockAnalysis）"""
    from api.services import stock_service

    return stock_service.get_full_analysis(ts_code, days=days)


@router.get("/analyze/{ts_code}/klines")
def analyze_stock_klines(ts_code: str, days: int = 120):
    """K 线图表数据（ECharts 列式格式，对齐前端 KlineChart）"""
    from api.services import stock_service

    return stock_service.get_kline_chart_data(ts_code, days=days)


@router.get("/analyze/{ts_code}/signals")
def analyze_stock_signals(ts_code: str, days: int = 120):
    """战法信号列表（对齐前端 StrategySignal[]）"""
    from api.services import stock_service

    return stock_service.get_signals(ts_code, days=days)


@router.get("/score/{ts_code}")
def get_stock_score(ts_code: str):
    """综合评分（对齐前端 ScoreDetail）"""
    from api.services import stock_service

    return stock_service.get_score(ts_code)
