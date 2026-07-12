"""
向后兼容 shim — 从 core.database re-export

实际实现已迁移至 core/database.py，本文件仅保留以兼容
现有的 `from modules.database import ...` 调用。
"""

from core.database import *  # noqa: F401, F403
from core.database import (  # noqa: F401
    DB_PATH,
    StockInfo,
    TradeRecord,
    add_watchlist_item,
    delete_trade_record,
    drop_all_tables,
    get_connection,
    get_db_connection,
    get_db_path,
    get_llm_response_log,
    get_llm_response_stats,
    get_trade_record_by_id,
    get_trade_records,
    get_trade_summary,
    get_watchlist,
    init_database,
    init_tracking_tables,
    record_llm_response,
    remove_watchlist_item,
    save_trade_record,
    update_trade_record,
    update_watchlist_item,
)


if __name__ == "__main__":
    init_database()
