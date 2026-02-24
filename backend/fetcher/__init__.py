"""股票数据抓取模块"""

# 重新导出功能以保持向后兼容性
from .client import fetch_latest_kline, fetch_one
from .processor import validate, load_codes_from_stocklist
from .config import (
    config,
    get_stocklist_path,
    get_out_dir,
    get_exclude_boards,
    get_workers,
    get_batch_size,
    get_ts_token
)
from .utils import (
    RateLimitError,
    _looks_like_ip_ban,
    _cool_sleep,
    _to_ts_code,
    _filter_by_boards_stocklist,
    COOLDOWN_SECS,
    BAN_PATTERNS
)

# 全局变量保持兼容
pro = None

# 版本信息
__version__ = "1.0.0"
__all__ = [
    "fetch_latest_kline",
    "fetch_one",
    "validate",
    "load_codes_from_stocklist",
    "RateLimitError",
    "config",
    "get_stocklist_path",
    "get_out_dir",
    "get_exclude_boards",
    "get_workers",
    "get_batch_size",
    "get_ts_token"
]
