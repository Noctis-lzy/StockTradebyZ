from __future__ import annotations

import argparse
import datetime as dt
import logging
import random
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional
import os
import gc

import pandas as pd
import tushare as ts
from tqdm import tqdm

warnings.filterwarnings("ignore")

# --------------------------- 全局日志配置 --------------------------- #
LOG_FILE = Path("fetch.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("fetch_from_stocklist")

# --------------------------- 限流/封禁处理配置 --------------------------- #
COOLDOWN_SECS = 600
BAN_PATTERNS = (
    "访问频繁", "请稍后", "超过频率", "频繁访问",
    "too many requests", "429",
    "forbidden", "403",
    "max retries exceeded"
)


def _looks_like_ip_ban(exc: Exception) -> bool:
    msg = (str(exc) or "").lower()
    return any(pat in msg for pat in BAN_PATTERNS)


class RateLimitError(RuntimeError):
    """表示命中限流/封禁，需要长时间冷却后重试。"""
    pass


def _cool_sleep(base_seconds: int) -> None:
    jitter = random.uniform(0.9, 1.2)
    sleep_s = max(1, int(base_seconds * jitter))
    logger.warning("疑似被限流/封禁，进入冷却期 %d 秒...", sleep_s)
    time.sleep(sleep_s)


# --------------------------- 历史K线（Tushare 日线，固定qfq） --------------------------- #
pro: Optional[ts.pro_api] = None  # 模块级会话


def set_api(session) -> None:
    """由外部(比如GUI)注入已创建好的 ts.pro_api() 会话"""
    global pro
    pro = session


def _to_ts_code(code: str) -> str:
    """把6位code映射到标准 ts_code 后缀。"""
    code = str(code).zfill(6)
    if code.startswith(("60", "68", "9")):
        return f"{code}.SH"
    elif code.startswith(("4", "8")):
        return f"{code}.BJ"
    else:
        return f"{code}.SZ"


def _get_kline_tushare(code: str, start: str, end: str) -> pd.DataFrame:
    ts_code = _to_ts_code(code)
    try:
        df = ts.pro_bar(
            ts_code=ts_code,
            adj="qfq",
            start_date=start,
            end_date=end,
            freq="D",
            api=pro
        )
    except Exception as e:
        if _looks_like_ip_ban(e):
            raise RateLimitError(str(e)) from e
        raise

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.rename(columns={"trade_date": "date", "vol": "volume"})[
        ["date", "open", "close", "high", "low", "volume"]
    ].copy()
    df["date"] = pd.to_datetime(df["date"])
    for c in ["open", "close", "high", "low", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


def validate(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)
    if df["date"].isna().any():
        raise ValueError("存在缺失日期！")
    if (df["date"] > pd.Timestamp.today()).any():
        raise ValueError("数据包含未来日期，可能抓取错误！")
    return df


# --------------------------- 读取 stocklist.csv & 过滤板块 --------------------------- #

def _filter_by_boards_stocklist(df: pd.DataFrame, exclude_boards: set[str]) -> pd.DataFrame:
    """
    exclude_boards 子集：{'gem','star','bj'}
    - gem  : 创业板 300/301（.SZ）
    - star : 科创板 688（.SH）
    - bj   : 北交所（.BJ 或 4/8 开头）
    """
    code = df["symbol"].astype(str)
    ts_code = df["ts_code"].astype(str).str.upper()
    mask = pd.Series(True, index=df.index)

    if "gem" in exclude_boards:
        mask &= ~code.str.startswith(("300", "301"))
    if "star" in exclude_boards:
        mask &= ~code.str.startswith(("688",))
    if "bj" in exclude_boards:
        mask &= ~(ts_code.str.endswith(".BJ") | code.str.startswith(("4", "8")))

    return df[mask].copy()


def load_codes_from_stocklist(stocklist_csv: Path, exclude_boards: set[str]) -> List[str]:
    df = pd.read_csv(stocklist_csv)
    df = _filter_by_boards_stocklist(df, exclude_boards)
    codes = df["symbol"].astype(str).str.zfill(6).tolist()
    codes = list(dict.fromkeys(codes))  # 去重保持顺序
    logger.info("从 %s 读取到 %d 只股票（排除板块：%s）",
                stocklist_csv, len(codes), ",".join(sorted(exclude_boards)) or "无")
    return codes


# --------------------------- 单只抓取（全量覆盖保存） --------------------------- #
def fetch_one(
        code: str,
        start: str,
        end: str,
        out_dir: Path,
):
    csv_path = out_dir / f"{code}.csv"
    new_df = None

    for attempt in range(1, 4):
        try:
            new_df = _get_kline_tushare(code, start, end)
            if new_df.empty:
                logger.debug("%s 无数据，生成空表。", code)
                new_df = pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])
            new_df = validate(new_df)
            # new_df.to_csv(csv_path, index=False)  # 直接覆盖保存
            # 修改为：
            if csv_path.exists() and os.path.getsize(csv_path) > 0:
                new_df.to_csv(csv_path, index=False, mode='a', header=False)
            else:
                new_df.to_csv(csv_path, index=False)  # 首次写入时保留header
            break
        except Exception as e:
            if _looks_like_ip_ban(e):
                logger.error(f"{code} 第 {attempt} 次抓取疑似被封禁，沉睡 {COOLDOWN_SECS} 秒")
                _cool_sleep(COOLDOWN_SECS)
            else:
                silent_seconds = 15 * attempt
                logger.info(f"{code} 第 {attempt} 次抓取失败，{silent_seconds} 秒后重试：{e}")
                time.sleep(silent_seconds)
    else:
        logger.error("%s 三次抓取均失败，已跳过！", code)

    # 显式释放内存
    if new_df is not None:
        del new_df
    gc.collect()


# --------------------------- 主入口 --------------------------- #
def main():
    parser = argparse.ArgumentParser(
        description="从 stocklist.csv 读取股票池并用 Tushare 抓取日线K线（固定qfq，全量覆盖）")
    # 抓取范围
    parser.add_argument("--start", default="20190101", help="起始日期 YYYYMMDD 或 'today'")
    parser.add_argument("--end", default="today", help="结束日期 YYYYMMDD 或 'today'")
    # 股票清单与板块过滤
    parser.add_argument("--stocklist", type=Path, default=Path(r"C:\code\stockList\stocklist.csv"),
                        help="股票清单CSV路径（需含 ts_code 或 symbol）")
    parser.add_argument(
        "--exclude-boards",
        nargs="*",
        default=[],
        choices=["gem", "star", "bj"],
        help="排除板块，可多选：gem(创业板300/301) star(科创板688) bj(北交所.BJ/4/8)"
    )
    # 其它
    # parser.add_argument("--out", default="C:\code\stockData", help="输出目录")
    parser.add_argument("--out", default=r"C:\code\stockData", help="输出目录")
    parser.add_argument("--workers", type=int, default=2, help="并发线程数")
    parser.add_argument("--batch-size", type=int, default=100, help="每批处理的股票数量")
    args = parser.parse_args()

    # ---------- Tushare Token ---------- #
    os.environ["NO_PROXY"] = "api.waditu.com,.waditu.com,waditu.com"
    os.environ["no_proxy"] = os.environ["NO_PROXY"]
    ts_token = "93aaf58e14cf4ca7c60001d604f65a22767c21b3e769e778e77cd2f2"
    if not ts_token:
        raise ValueError("请先设置环境变量 TUSHARE_TOKEN，例如：export TUSHARE_TOKEN=你的token")
    ts.set_token(ts_token)
    global pro
    pro = ts.pro_api()


    # ---------- 写入路径解析 ---------- #

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 日期解析 ---------- #
    # start = dt.date.today().strftime("%Y%m%d") if str(args.start).lower() == "today" else args.start
    # 读取out目录下第一个csv文件的第一列的最后一行的第一列的值，作为start日期
    if not out_dir.exists():
        start = "20190101"
    else:
        csv_files = list(out_dir.glob("*.csv"))
        if csv_files:
            # 选取第一个 csv 文件进行
            first_csv = csv_files[0]
            try:
                # 读取最后一行
                df_temp = pd.read_csv(first_csv)
                if not df_temp.empty and len(df_temp.columns) > 0:
                    # 读取df_temp最后一行
                    start = df_temp.iloc[-1, 0]
                    # start 从'2025-12-19'转成YYYYMMDD
                    start = dt.datetime.strptime(start, "%Y-%m-%d").strftime("%Y%m%d")
                    logger.warning(f"读取起始日期:{start}")
                    # 如果start日期就是离今天最近的工作日，则中断运行
                    today = dt.date.today()
                    # 如果今天是周末，计算最近的工作日
                    if today.weekday() == 5:  # Saturday
                        nearest_workday = (today - dt.timedelta(days=1)).strftime("%Y%m%d")
                    elif today.weekday() == 6:  # Sunday
                        nearest_workday = (today - dt.timedelta(days=2)).strftime("%Y%m%d")
                    else:  # Weekday
                        nearest_workday = today.strftime("%Y%m%d")

                    if str(start) == nearest_workday:
                        logger.warning("数据已是最新，无需更新")
                        sys.exit(0)
                    #给start加一天
                    start = (dt.datetime.strptime(start, "%Y%m%d") + dt.timedelta(days=1)).strftime("%Y%m%d")
                else:
                    start = "20190101"
            except Exception as e:
                logger.warning(f"无法从 {first_csv} 读取起始日期: {e}")
                start = "20190101"
        else:
            start = "20190101"

    end = dt.date.today().strftime("%Y%m%d") if str(args.end).lower() == "today" else args.end



    # ---------- 从 stocklist.csv 读取股票池 ---------- #
    exclude_boards = set(args.exclude_boards or [])
    codes = load_codes_from_stocklist(args.stocklist, exclude_boards)

    if not codes:
        logger.error("stocklist 为空或被过滤后无代码，请检查。")
        sys.exit(1)

    logger.info(
        "开始抓取 %d 支股票 | 数据源:Tushare(日线,qfq) | 日期:%s → %s | 排除:%s",
        len(codes), start, end, ",".join(sorted(exclude_boards)) or "无",
    )

    # ---------- 分批处理以减少内存压力 ---------- #
    batch_size = args.batch_size
    total_batches = (len(codes) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(codes))
        batch_codes = codes[start_idx:end_idx]

        # 先打印批次信息，避免与进度条混合
        logger.info("正在处理批次 %d/%d (股票 %d-%d)",
                    batch_num + 1, total_batches, start_idx + 1, end_idx)
        time.sleep(1)  # 给系统一点时间释放资源
        # ---------- 多线程抓取（全量覆盖） ---------- #
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = [
                executor.submit(
                    fetch_one,
                    code,
                    start,
                    end,
                    out_dir,
                )
                for code in batch_codes
            ]

            # 使用 tqdm 的 write 功能来避免与日志冲突
            with tqdm(as_completed(futures), total=len(futures),
                      desc=f"批次 {batch_num + 1}/{total_batches}") as pbar:
                for future in pbar:
                    try:
                        future.result()  # 获取结果以触发可能的异常
                    except Exception as e:
                        # 使用 tqdm.write 来输出错误信息，避免破坏进度条
                        pbar.write(f"任务执行出错: {e}")
                        logger.error(f"任务执行出错: {e}")

        # 每批处理完成后释放内存
        gc.collect()
        time.sleep(1)  # 给系统一点时间释放资源

    logger.info("全部任务完成，数据已保存至 %s", out_dir.resolve())


if __name__ == "__main__":
    try:
        main()
    finally:
        # 确保程序结束时释放所有资源
        if pro is not None:
            try:
                pro.close()
            except:
                pass
        gc.collect()