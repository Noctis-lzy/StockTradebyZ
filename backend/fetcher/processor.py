import pandas as pd
from pathlib import Path
from typing import List, Set
import logging

from .utils import _filter_by_boards_stocklist

logger = logging.getLogger(__name__)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """验证数据有效性"""
    if df is None or df.empty:
        return df
    df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    if df["date"].isna().any():
        raise ValueError("存在缺失日期！")
    if (df["date"] > pd.Timestamp.today()).any():
        raise ValueError("数据包含未来日期，可能抓取错误！")
    return df


def load_codes_from_stocklist(stocklist_csv: Path, exclude_boards: Set[str]) -> List[str]:
    """从股票列表文件加载代码"""
    df = pd.read_csv(stocklist_csv)
    df = _filter_by_boards_stocklist(df, exclude_boards)
    codes = df["symbol"].astype(str).str.zfill(6).tolist()
    codes = list(dict.fromkeys(codes))  # 去重
    logger.info("从 %s 读取到 %d 只股票（排除板块：%s）",
                stocklist_csv, len(codes), ",".join(sorted(exclude_boards)) or "无")
    return codes


def process_kline_data(df: pd.DataFrame) -> pd.DataFrame:
    """处理K线数据"""
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])
    
    # 重命名列并选择需要的列
    df = df.rename(columns={"trade_date": "date", "vol": "volume"})[
        ["date", "open", "close", "high", "low", "volume"]
    ].copy()
    
    # 转换数据类型
    df["date"] = pd.to_datetime(df["date"])
    for c in ["open", "close", "high", "low", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    
    # 排序并重置索引
    return df.sort_values("date").reset_index(drop=True)
