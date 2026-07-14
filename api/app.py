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
from api.routes import screen, watchlist, trade, diagnosis, system, commentary  # noqa: E402

# 旧路由（保留给原有测试 + 旧 web 前端，前缀 /api/xxx 自带）
app.include_router(stock.router, prefix="/api/v1/stock")  # stock.router 已无自身 prefix
app.include_router(screener.router, prefix="/api/screener")  # 旧路径兼容
app.include_router(backtest.router, prefix="/api/v1/backtest")  # backtest.router 已无自身 prefix
app.include_router(training.router, prefix="/api/training")  # 旧路径兼容
app.include_router(portfolio.router, prefix="/api/portfolio")  # 旧路径兼容

# 新路由（对齐前端 baseURL /api/v1）
app.include_router(screen.router, prefix="/api/v1/screen")
app.include_router(watchlist.router, prefix="/api/v1/watchlist")
app.include_router(trade.router, prefix="/api/v1/trade")
app.include_router(diagnosis.router, prefix="/api/v1/diagnosis")
app.include_router(system.router, prefix="/api/v1/system")
app.include_router(commentary.router, prefix="/api/v1")

# 注册 Web 页面路由
from api.web_routes import router as web_router  # noqa: E402

app.include_router(web_router)
