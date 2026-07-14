"""选股筛选模型"""

from pydantic import BaseModel, Field


class ScreenRequest(BaseModel):
    strategy: str = Field(default="B1", description="策略名称（B1/B2/B3/完美图形/超级B1/长安战法/建仓波/吸筹/安全/超跌/突破）")
    limit: int = Field(default=20, ge=1, le=500, description="返回数量上限")
    use_parallel: bool = Field(default=True, description="是否启用多进程")
    # ── 评分约束 ──
    min_score: float = Field(default=0, ge=0, le=100, description="最低综合分")
    min_b1_score: float = Field(default=0, ge=0, le=100, description="最低 B1 分")
    min_trend_score: float = Field(default=0, ge=0, le=100, description="最低趋势分")
    min_volume_score: float = Field(default=0, ge=0, le=100, description="最低量价分")
    max_risk_score: float = Field(default=100, ge=0, le=100, description="最高风险分（含）")
    # ── 基础约束 ──
    industry: str = Field(default="", description="行业过滤，逗号分隔，如 有色金属,白酒")
    exclude_st: bool = Field(default=True, description="排除 ST/*ST 股票")
    exclude_limit_up: bool = Field(default=False, description="排除当日涨停股")
    min_price: float = Field(default=0, ge=0, description="最低股价（含）")
    max_price: float = Field(default=0, ge=0, description="最高股价（含），0=不限")


class StockScoreItem(BaseModel):
    ts_code: str
    name: str = ""
    score: float = 0
    b1_score: float = 0
    trend_score: float = 0
    volume_score: float = 0
    risk_score: float = 0
    rating: str = ""
    reasons: list[str] = []
    warnings: list[str] = []


class ScreenResponse(BaseModel):
    strategy: str
    criteria: str
    count: int
    stocks: list[StockScoreItem] = []


class StrategyInfo(BaseModel):
    alias: str
    criteria: str
    description: str = ""
    formula: str = ""

