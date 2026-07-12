"""Web 页面路由 — Jinja2 模板渲染"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["页面"])

_templates_dir = Path(__file__).parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))
# Python 3.14 兼容：禁用模板缓存（Jinja2 LRUCache 的 key 含 dict 在 3.14 不可哈希）
templates.env.cache = None


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """首页"""
    return templates.TemplateResponse(request, "index.html")


@router.get("/stock/{ts_code}", response_class=HTMLResponse)
def stock_page(request: Request, ts_code: str):
    """个股看板"""
    return templates.TemplateResponse(
        request,
        "stock/analysis.html",
        {"ts_code": ts_code},
    )
