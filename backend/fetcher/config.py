import os
from pathlib import Path
from typing import Set, Optional

# 配置默认值
DEFAULT_STOCKLIST_PATH = Path(r"C:\code\git\StockTradebyZ\data\stock_list\stocklist.csv")
DEFAULT_OUT_DIR = Path(r"C:\code\git\StockTradebyZ\data\stock_kline_data")
DEFAULT_EXCLUDE_BOARDS: Set[str] = set()
DEFAULT_WORKERS = 2
DEFAULT_BATCH_SIZE = 100
DEFAULT_TS_TOKEN = "93aaf58e14cf4ca7c60001d604f65a22767c21b3e769e778e77cd2f2"


class Config:
    """配置管理类"""
    
    def __init__(self):
        self.stocklist_path = DEFAULT_STOCKLIST_PATH
        self.out_dir = DEFAULT_OUT_DIR
        self.exclude_boards = DEFAULT_EXCLUDE_BOARDS
        self.workers = DEFAULT_WORKERS
        self.batch_size = DEFAULT_BATCH_SIZE
        self.ts_token = self._get_ts_token()
        self._setup_env()
    
    def _get_ts_token(self) -> str:
        """从环境变量获取Tushare token，如果不存在则使用默认值"""
        return os.environ.get("TUSHARE_TOKEN", DEFAULT_TS_TOKEN)
    
    def _setup_env(self) -> None:
        """设置环境变量"""
        os.environ["NO_PROXY"] = "api.waditu.com,.waditu.com,waditu.com"
        os.environ["no_proxy"] = os.environ["NO_PROXY"]


# 全局配置实例
config = Config()


# 向后兼容的配置变量
def get_stocklist_path() -> Path:
    return config.stocklist_path


def get_out_dir() -> Path:
    return config.out_dir


def get_exclude_boards() -> Set[str]:
    return config.exclude_boards


def get_workers() -> int:
    return config.workers


def get_batch_size() -> int:
    return config.batch_size


def get_ts_token() -> str:
    return config.ts_token
