import random
import time
from typing import Set

# 常量定义
COOLDOWN_SECS = 600
BAN_PATTERNS = (
    "访问频繁", "请稍后", "超过频率", "频繁访问",
    "too many requests", "429",
    "forbidden", "403",
    "max retries exceeded"
)


class RateLimitError(RuntimeError):
    """表示命中限流/封禁，需要长时间冷却后重试。"""
    pass


def _looks_like_ip_ban(exc: Exception) -> bool:
    """检测是否为IP封禁异常"""
    msg = (str(exc) or "").lower()
    return any(pat in msg for pat in BAN_PATTERNS)


def _cool_sleep(base_seconds: int) -> None:
    """冷却睡眠，添加随机抖动"""
    jitter = random.uniform(0.9, 1.2)
    sleep_s = max(1, int(base_seconds * jitter))
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("疑似被限流/封禁，进入冷却期 %d 秒...", sleep_s)
    time.sleep(sleep_s)


def _to_ts_code(code: str) -> str:
    """把6位code映射到标准 ts_code 后缀。"""
    code = str(code).zfill(6)
    if code.startswith(("60", "68", "9")):
        return f"{code}.SH"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    else:
        return f"{code}.SZ"


def _filter_by_boards_stocklist(df, exclude_boards: Set[str]):
    """
    exclude_boards 子集：{'gem','star','bj'}
    - gem  : 创业板 300/301（.SZ）
    - star : 科创板 688（.SH）
    - bj   : 北交所（.BJ 或 4/8 开头）
    """
    code = df["symbol"].astype(str)
    ts_code = df["ts_code"].astype(str).str.upper()
    mask = df.index.to_series().apply(lambda x: True)

    if "gem" in exclude_boards:
        mask &= ~code.str.startswith(("300", "301"))
    if "star" in exclude_boards:
        mask &= ~code.str.startswith(("688",))
    if "bj" in exclude_boards:
        mask &= ~(ts_code.str.endswith(".BJ") | code.str.startswith(("4", "8")))

    return df[mask].copy()
