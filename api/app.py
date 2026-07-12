"""
FastAPI 应用入口
"""

from fastapi import FastAPI

app = FastAPI(
    title="Z哥量化分析平台",
    description="zettaranc-perspective Web API",
    version="4.0.0",
)


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}


# 注册路由
from api.routes import stock, screener, backtest, training, portfolio  # noqa: E402

app.include_router(stock.router)
app.include_router(screener.router)
app.include_router(backtest.router)
app.include_router(training.router)
app.include_router(portfolio.router)
