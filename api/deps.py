"""
依赖注入 — 提供 DataAccess 等服务实例
"""

from core.data_access import DataAccess


def get_data_access() -> DataAccess:
    """获取 DataAccess 实例（每次新建，确保 DB_PATH 正确）"""
    return DataAccess()
