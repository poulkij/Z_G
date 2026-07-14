"""screen_service 约束过滤单元测试

验证 run_screen 的评分约束 + 基础约束（ST/行业/价格/涨停）过滤逻辑。
不经过 HTTP 层，直接调 service 函数，用临时 DB 造数据。
"""

from tests.conftest import write_stock_basic, write_klines_to_db, generate_uptrend_klines


def _make_score(ts_code, name, score=80, b1=60, trend=70, volume=65, risk=30):
    """构造一个 StockScore 对象"""
    from core.screener import StockScore

    return StockScore(
        ts_code=ts_code,
        name=name,
        score=score,
        b1_score=b1,
        trend_score=trend,
        volume_score=volume,
        risk_score=risk,
    )


def test_apply_base_filters_exclude_st(temp_db):
    """ST 股票应被排除"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600001.SH", "正常股票", "白酒")
        write_stock_basic(conn, "600002.SH", "ST烂股", "白酒")

    scores = [_make_score("600001.SH", "正常股票"), _make_score("600002.SH", "ST烂股")]
    result = _apply_base_filters(scores, exclude_st=True, exclude_limit_up=False)

    codes = [s.ts_code for s in result]
    assert "600001.SH" in codes
    assert "600002.SH" not in codes


def test_apply_base_filters_keep_st_when_disabled(temp_db):
    """exclude_st=False 时 ST 股票应保留"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600002.SH", "ST烂股", "白酒")

    scores = [_make_score("600002.SH", "ST烂股")]
    result = _apply_base_filters(scores, exclude_st=False, exclude_limit_up=False)

    assert len(result) == 1
    assert result[0].ts_code == "600002.SH"


def test_apply_base_filters_industry(temp_db):
    """行业过滤：只保留指定行业的股票"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600001.SH", "茅台", "白酒")
        write_stock_basic(conn, "600002.SH", "云铝", "有色金属")

    scores = [
        _make_score("600001.SH", "茅台"),
        _make_score("600002.SH", "云铝"),
    ]
    result = _apply_base_filters(scores, industry="有色金属", exclude_st=False, exclude_limit_up=False)

    assert len(result) == 1
    assert result[0].ts_code == "600002.SH"


def test_apply_base_filters_industry_multi(temp_db):
    """多行业逗号分隔过滤"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600001.SH", "茅台", "白酒")
        write_stock_basic(conn, "600002.SH", "云铝", "有色金属")
        write_stock_basic(conn, "600003.SH", "银行A", "银行")

    scores = [
        _make_score("600001.SH", "茅台"),
        _make_score("600002.SH", "云铝"),
        _make_score("600003.SH", "银行A"),
    ]
    result = _apply_base_filters(
        scores, industry="白酒,有色金属", exclude_st=False, exclude_limit_up=False
    )

    codes = {s.ts_code for s in result}
    assert codes == {"600001.SH", "600002.SH"}


def test_apply_base_filters_price_range(temp_db):
    """价格范围过滤"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600001.SH", "低价股", "白酒")
        write_stock_basic(conn, "600002.SH", "高价股", "白酒")
        write_klines_to_db(conn, generate_uptrend_klines(n=5, ts_code="600001.SH", start_price=5.0))
        write_klines_to_db(conn, generate_uptrend_klines(n=5, ts_code="600002.SH", start_price=200.0))

    scores = [
        _make_score("600001.SH", "低价股"),
        _make_score("600002.SH", "高价股"),
    ]
    # 只保留 10-100 元的
    result = _apply_base_filters(
        scores, exclude_st=False, exclude_limit_up=False, min_price=10, max_price=100
    )

    # 低价股 5 元 < 10 应排除；高价股 200 元 > 100 应排除
    assert len(result) == 0

    # 放宽到 1-300
    result2 = _apply_base_filters(
        scores, exclude_st=False, exclude_limit_up=False, min_price=1, max_price=300
    )
    assert len(result2) == 2


def test_apply_base_filters_exclude_limit_up(temp_db):
    """涨停股应被排除"""
    from api.services.screen_service import _apply_base_filters
    from core.database import get_connection

    with get_connection() as conn:
        write_stock_basic(conn, "600001.SH", "正常", "白酒")
        write_stock_basic(conn, "600002.SH", "涨停股", "白酒")
        # 正常股
        normal = generate_uptrend_klines(n=5, ts_code="600001.SH", start_price=10.0)
        write_klines_to_db(conn, normal)
        # 涨停股：pct_chg = 10
        limit_rows = generate_uptrend_klines(n=5, ts_code="600002.SH", start_price=10.0)
        for r in limit_rows:
            r["pct_chg"] = 10.0
        write_klines_to_db(conn, limit_rows)

    scores = [
        _make_score("600001.SH", "正常"),
        _make_score("600002.SH", "涨停股"),
    ]
    result = _apply_base_filters(scores, exclude_st=False, exclude_limit_up=True)

    codes = [s.ts_code for s in result]
    assert "600001.SH" in codes
    assert "600002.SH" not in codes


def test_get_strategies_returns_formula():
    """get_strategies 应返回每个战法的选股公式"""
    from api.services.screen_service import get_strategies

    strategies = get_strategies()
    assert len(strategies) == 11
    for s in strategies:
        assert "alias" in s
        assert "criteria" in s
        assert "description" in s
        assert "formula" in s
        assert len(s["formula"]) > 0, f"战法 {s['alias']} 缺少公式"


def test_get_strategies_formula_contains_key_conditions():
    """公式文本应包含关键条件标识"""
    from api.services.screen_service import get_strategies

    strategies = {s["alias"]: s for s in get_strategies()}

    # B1 应提到 b1_score
    assert "b1_score" in strategies["B1"]["formula"]
    # 完美图形 应提到综合评分
    assert "综合评分" in strategies["完美图形"]["formula"] or "score" in strategies["完美图形"]["formula"]
    # 超跌 应提到 trend_score
    assert "trend_score" in strategies["超跌"]["formula"]
    # 突破 应提到 volume_score
    assert "volume_score" in strategies["突破"]["formula"]
