"""
FastAPI 应用入口
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Z哥量化分析平台",
    description="zettaranc-perspective Web API",
    version="4.0.0",
)

# 挂载静态文件
_static_dir = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}


# 注册 API 路由
from api.routes import stock, screener, backtest, training, portfolio  # noqa: E402

app.include_router(stock.router)
app.include_router(screener.router)
app.include_router(backtest.router)
app.include_router(training.router)
app.include_router(portfolio.router)

# 注册 Web 页面路由
from api.web_routes import router as web_router  # noqa: E402

app.include_router(web_router)
