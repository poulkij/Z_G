#!/usr/bin/env python3
"""
自我改进系统测试用例

测试跟踪池管理、数据同步、复盘报告生成、Harness 层集成
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.tracking_manager import TrackingManager
from modules.tracking_syncer import TrackingSyncer
from modules.review_generator import ReviewGenerator
from modules.harness_updater import HarnessUpdater


class TestTrackingManager:
    """测试跟踪池管理器"""

    def __init__(self):
        """初始化测试"""
        self.db_path = None
        self.manager = None

    def setup(self):
        """设置测试环境"""
        # 使用真实的数据库
        self.db_path = Path("data/stock_data.db")

        # 清理所有测试数据
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracking_pool_self")
        cursor.execute("DELETE FROM tracking_records_self")
        cursor.execute("DELETE FROM monthly_reviews_self")
        cursor.execute("DELETE FROM strategy_performance_self")
        conn.commit()
        conn.close()

        # 初始化管理器
        self.manager = TrackingManager()

    def teardown(self):
        """清理测试环境"""
        # 清理所有测试数据
        if self.db_path and self.db_path.exists():
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracking_pool_self")
            cursor.execute("DELETE FROM tracking_records_self")
            cursor.execute("DELETE FROM monthly_reviews_self")
            cursor.execute("DELETE FROM strategy_performance_self")
            conn.commit()
            conn.close()

    def test_add_stock(self):
        """测试添加股票"""
        print("测试添加股票...")

        # 添加股票
        result = self.manager.add_stock(
            ts_code="600519.SH", name="贵州茅台", reason="B1买点出现", strategy_tags=["B1"], notes="测试股票"
        )

        assert result, "添加股票失败"

        # 验证股票已添加
        stock = self.manager.get_stock_info("600519.SH")
        assert stock is not None, "股票不存在"
        assert stock["ts_code"] == "600519.SH", "股票代码不匹配"
        assert stock["name"] == "贵州茅台", "股票名称不匹配"
        assert stock["status"] == "active", "股票状态不匹配"

        print("  ✅ 添加股票成功")

    def test_remove_stock(self):
        """测试移除股票"""
        print("测试移除股票...")

        # 先添加股票
        self.manager.add_stock("600519.SH", "贵州茅台", "测试")

        # 移除股票
        result = self.manager.remove_stock("600519.SH", "测试完成")
        assert result, "移除股票失败"

        # 验证股票已移除
        stock = self.manager.get_stock_info("600519.SH")
        assert stock is not None, "股票不存在"
        assert stock["status"] == "removed", "股票状态不是 removed"

        print("  ✅ 移除股票成功")

    def test_list_stocks(self):
        """测试列出股票"""
        print("测试列出股票...")

        # 先清理测试数据（删除所有相关的股票）
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracking_pool_self WHERE ts_code IN ('600519.SH', '000858.SZ')")
        conn.commit()
        conn.close()

        # 添加多只股票
        self.manager.add_stock("600519.SH", "贵州茅台", "测试1", ["B1"])
        self.manager.add_stock("000858.SZ", "五粮液", "测试2", ["B2"])

        # 列出活跃股票
        stocks = self.manager.list_stocks(status="active")
        assert len(stocks) == 2, f"活跃股票数量不正确: {len(stocks)}"

        # 按策略筛选
        stocks = self.manager.list_stocks(strategy_tag="B1")
        assert len(stocks) == 1, f"B1 策略股票数量不正确: {len(stocks)}"
        assert stocks[0]["ts_code"] == "600519.SH", "B1 策略股票不正确"

        print("  ✅ 列出股票成功")

    def test_get_stats(self):
        """测试获取统计信息"""
        print("测试获取统计信息...")

        # 先清理测试数据（删除所有相关的股票）
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracking_pool_self WHERE ts_code IN ('600519.SH', '000858.SZ')")
        conn.commit()
        conn.close()

        # 添加股票
        self.manager.add_stock("600519.SH", "贵州茅台", "测试1", ["B1"])
        self.manager.add_stock("000858.SZ", "五粮液", "测试2", ["B2"])

        # 获取统计信息
        stats = self.manager.get_tracking_stats()
        assert stats.get("total", 0) == 2, f"总数量不正确: {stats.get('total')}"
        assert stats.get("active", 0) == 2, f"活跃数量不正确: {stats.get('active')}"

        # 获取策略分布
        distribution = self.manager.get_strategy_distribution()
        assert distribution.get("B1") == 1, f"B1 策略数量不正确: {distribution.get('B1')}"
        assert distribution.get("B2") == 1, f"B2 策略数量不正确: {distribution.get('B2')}"

        print("  ✅ 获取统计信息成功")

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("运行 TrackingManager 测试")
        print("=" * 50)

        self.setup()

        try:
            self.test_add_stock()
            self.test_remove_stock()
            self.test_list_stocks()
            self.test_get_stats()
            print("\n✅ 所有 TrackingManager 测试通过")
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
        finally:
            self.teardown()


class TestReviewGenerator:
    """测试复盘报告生成器"""

    def __init__(self):
        """初始化测试"""
        self.generator = None

    def setup(self):
        """设置测试环境"""
        self.generator = ReviewGenerator()

    def test_generate_review(self):
        """测试生成复盘报告"""
        print("测试生成复盘报告...")

        # 生成复盘报告
        result = self.generator.generate_monthly_review("202605")

        assert result.get("success"), f"生成复盘报告失败: {result.get('message')}"
        assert result.get("total_stocks", 0) > 0, "复盘股票数量为 0"

        # 检查复盘数据
        reviews = result.get("reviews", [])
        assert len(reviews) > 0, "复盘数据为空"

        # 检查第一只股票的复盘数据
        first_review = reviews[0]
        assert "ts_code" in first_review, "缺少 ts_code"
        assert "monthly_return" in first_review, "缺少 monthly_return"
        assert "max_drawdown" in first_review, "缺少 max_drawdown"

        print(f"  ✅ 生成复盘报告成功，共 {result.get('total_stocks')} 只股票")

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("运行 ReviewGenerator 测试")
        print("=" * 50)

        self.setup()

        try:
            self.test_generate_review()
            print("\n✅ 所有 ReviewGenerator 测试通过")
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")


class TestHarnessUpdater:
    """测试 Harness 层更新器"""

    def __init__(self):
        """初始化测试"""
        self.updater = None

    def setup(self):
        """设置测试环境"""
        self.updater = HarnessUpdater()

    def test_analyze_strategy_performance(self):
        """测试分析策略表现"""
        print("测试分析策略表现...")

        # 分析策略表现
        result = self.updater.analyze_strategy_performance("202605")

        assert result.get("success"), f"分析策略表现失败: {result.get('message')}"
        assert result.get("review_month") == "202605", "复盘月份不正确"

        # 检查策略统计
        strategy_stats = result.get("strategy_stats", [])
        assert len(strategy_stats) > 0, "策略统计数据为空"

        print(f"  ✅ 分析策略表现成功，共 {len(strategy_stats)} 个策略")

    def test_generate_guardrails_update(self):
        """测试生成 Guardrails 更新建议"""
        print("测试生成 Guardrails 更新建议...")

        # 先分析策略表现
        analysis_result = self.updater.analyze_strategy_performance("202605")

        # 生成更新建议
        result = self.updater.generate_guardrails_update(analysis_result)

        assert result.get("success"), f"生成更新建议失败: {result.get('message')}"

        # 检查更新建议
        result.get("updates", [])
        total_updates = result.get("total_updates", 0)

        print(f"  ✅ 生成 Guardrails 更新建议成功，共 {total_updates} 条建议")

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("运行 HarnessUpdater 测试")
        print("=" * 50)

        self.setup()

        try:
            self.test_analyze_strategy_performance()
            self.test_generate_guardrails_update()
            print("\n✅ 所有 HarnessUpdater 测试通过")
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")


def main():
    """主函数"""
    print("自我改进系统测试")
    print("=" * 50)

    # 运行 TrackingManager 测试
    tracking_test = TestTrackingManager()
    tracking_test.run_all_tests()

    print()

    # 运行 ReviewGenerator 测试
    review_test = TestReviewGenerator()
    review_test.run_all_tests()

    print()

    # 运行 HarnessUpdater 测试
    harness_test = TestHarnessUpdater()
    harness_test.run_all_tests()

    print()
    print("=" * 50)
    print("所有测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
