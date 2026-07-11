"""
Core 领域层 — 技术指标、战法识别、选股评分、回测引擎
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 全局一次性加载 .env（包首次 import 时执行）
_env_path = Path(os.getenv("ZETTARANC_ENV", Path(__file__).parent.parent / ".env"))
load_dotenv(_env_path, override=False)


def get_data_mode() -> str:
    """获取当前数据模式：jnb 或 websearch"""
    return os.getenv("DATA_MODE", "websearch")


def get_project_root() -> Path:
    """获取项目根目录（core/ 的上一级）"""
    return Path(__file__).parent.parent
