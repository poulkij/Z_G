"""
Pydantic 响应模型 — 所有 API 路由共用
"""

from pydantic import BaseModel
from typing import Optional


class KLineItem(BaseModel):
    """单根 K 线"""
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    pct_chg: float = 0.0


class IndicatorSnapshot(BaseModel):
    """指标快照"""
    k: float = 0
    d: float = 0
    j: float = 0
    dif: float = 0
    dea: float = 0
    macd_hist: float = 0
    rsi6: float = 0
    boll_mid: float = 0
    boll_upper: float = 0
    boll_lower: float = 0
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    ma60: float = 0
    vol_ratio: float = 0
    zg_white: float = 0
    dg_yellow: float = 0
    bbi: float = 0


class SignalItem(BaseModel):
    """战法信号"""
    trade_date: str
    strategy: str
    action: str
    confidence: float = 0.0
    price: float = 0.0
    note: str = ""


class StockScoreItem(BaseModel):
    """股票评分"""
    ts_code: str
    name: str = ""
    score: float = 0
    b1_score: float = 0
    trend_score: float = 0
    volume_score: float = 0
    risk_score: float = 0
    reasons: list[str] = []
    warnings: list[str] = []
    rating: str = ""


class StockSearchItem(BaseModel):
    """股票搜索结果项"""
    ts_code: str
    name: str = ""
    industry: str = ""


class StockSearchResponse(BaseModel):
    """股票搜索响应"""
    results: list[StockSearchItem] = []


class StockAnalysisResponse(BaseModel):
    """个股分析完整响应"""
    ts_code: str
    name: str = ""
    klines: list[KLineItem] = []
    indicators: IndicatorSnapshot = IndicatorSnapshot()
    signals: list[SignalItem] = []
    score: Optional[StockScoreItem] = None


class ScreenerResponse(BaseModel):
    """选股结果"""
    total: int = 0
    results: list[StockScoreItem] = []


class TradeItem(BaseModel):
    """单笔交易"""
    ts_code: str
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    hold_days: int = 0
    exit_reason: str = ""


class BacktestResultResponse(BaseModel):
    """回测结果"""
    ts_code: str
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    avg_return: float = 0.0
    total_return: float = 0.0
    trades: list[TradeItem] = []


class TuneResultResponse(BaseModel):
    """参数调优结果"""
    best_params: dict = {}
    best_score: float = 0.0
    all_results: list[dict] = []


class ScreenResultResponse(BaseModel):
    """历史筛选结果"""
    date: str = ""
    total_scanned: int = 0
    results: list[StockScoreItem] = []


class TrainingScreenRequest(BaseModel):
    """选股训练 - 当日筛选请求"""
    date: str
    strategies: list[str] = []
    min_score: float = 0
    days: int = 120


class TrainingScreenResponse(BaseModel):
    """选股训练 - 当日筛选响应"""
    date: str
    total_scanned: int = 0
    results: list[StockScoreItem] = []


class KLineRangeRequest(BaseModel):
    """按日期范围获取 K 线"""
    ts_code: str
    start_date: str
    end_date: str


class KLineRangeResponse(BaseModel):
    """按日期范围获取 K 线响应"""
    ts_code: str
    klines: list[KLineItem] = []


class DiagnosisResponse(BaseModel):
    """持仓诊断响应"""
    ts_code: str
    name: str = ""
    price: float = 0
    price_position: str = ""
    trend_status: str = ""
    kdj_j: float = 0
    macd_veto: bool = False
    bbi: float = 0
    white_line: float = 0
    yellow_line: float = 0
    sell_score: int = 0
    sell_score_desc: str = ""
    exit_signals: list[dict] = []
    buy_signals: list[dict] = []
    kirin_phase: str = "UNKNOWN"
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    recommendation: str = ""
    risk_level: str = "UNKNOWN"


class PortfolioDiagnoseRequest(BaseModel):
    """持仓诊断请求"""
    holdings: list[str]
    days: int = 100


class PortfolioDiagnoseResponse(BaseModel):
    """持仓诊断响应"""
    results: list[DiagnosisResponse] = []
