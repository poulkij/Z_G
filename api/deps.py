"""
依赖注入 — 提供 DataAccess 等服务实例
"""

from functools import lru_cache
from core.data_access import DataAccess


@lru_cache(maxsize=1)
def get_data_access() -> DataAccess:
    """获取 DataAccess 单例"""
    return DataAccess()
