import datetime as dt
import logging
import os
import time
import gc
import warnings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
import pandas as pd
import tushare as ts
from tqdm import tqdm

from .config import config
from .utils import _to_ts_code, _looks_like_ip_ban, _cool_sleep, COOLDOWN_SECS, RateLimitError
from .processor import validate, load_codes_from_stocklist, process_kline_data

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

# 全局Tushare API实例
pro: Optional[ts.pro_api] = None


# 添加速率控制变量
from collections import deque

# 用于存储请求时间戳的队列
request_times = deque()
# 每分钟最大请求数
MAX_REQUESTS_PER_MINUTE = 500
# 时间窗口（60秒）
TIME_WINDOW = 60

def _get_kline_tushare(code: str, start: str, end: str) -> pd.DataFrame:
    """从Tushare获取K线数据"""
    # 速率控制：确保每分钟请求数不超过500次
    current_time = time.time()
    
    # 移除时间窗口外的请求记录
    while request_times and current_time - request_times[0] > TIME_WINDOW:
        request_times.popleft()
    
    # 如果请求数达到上限，等待
    if len(request_times) >= MAX_REQUESTS_PER_MINUTE:
        wait_time = TIME_WINDOW - (current_time - request_times[0])
        if wait_time > 0:
            logger.debug(f"请求速率达到上限，等待 {wait_time:.2f} 秒")
            time.sleep(wait_time)
            # 更新当前时间
            current_time = time.time()
    
    # 记录本次请求时间
    request_times.append(current_time)
    
    ts_code = _to_ts_code(code)
    try:
        logger.debug(f"请求Tushare API: ts_code={ts_code}, start_date={start}, end_date={end}")
        df = ts.pro_bar(
            ts_code=ts_code,
            adj="qfq",
            start_date=start,
            end_date=end,
            freq="D",
            api=pro
        )
        if df is None:
            logger.debug(f"Tushare API返回数据: None")
            return pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])
        logger.debug(f"Tushare API返回数据: {len(df)} 条")
    except Exception as e:
        logger.error(f"Tushare API请求失败: {type(e).__name__}: {str(e)}")
        if _looks_like_ip_ban(e):
            raise RateLimitError(str(e)) from e
        raise

    return process_kline_data(df)


def fetch_one(
    code: str,
    start: str,
    end: str,
    out_dir: Path,
):
    """抓取单个股票的数据"""
    csv_path = out_dir / f"{code}.csv"
    new_df = None

    for attempt in range(1, 4):
        try:
            new_df = _get_kline_tushare(code, start, end)
            if new_df.empty:
                logger.debug("%s 无数据，生成空表。", code)
                new_df = pd.DataFrame(columns=["date", "open", "close", "high", "low", "volume"])
            new_df = validate(new_df)
            if csv_path.exists() and os.path.getsize(csv_path) > 0:
                new_df.to_csv(csv_path, index=False, mode='a', header=False)
            else:
                new_df.to_csv(csv_path, index=False)
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

    if new_df is not None:
        del new_df
    gc.collect()


def _init_tushare() -> bool:
    """初始化Tushare API"""
    global pro
    
    if not config.ts_token:
        logger.error("TUSHARE_TOKEN 未设置")
        return False
    
    try:
        ts.set_token(config.ts_token)
        pro = ts.pro_api()
        return True
    except Exception as e:
        logger.error(f"初始化Tushare API失败: {e}")
        return False


def _get_start_date(out_dir: Path) -> str:
    """获取起始日期"""
    if not out_dir.exists():
        return "20190101"
    
    csv_files = list(out_dir.glob("*.csv"))
    if not csv_files:
        return "20190101"
    
    first_csv = csv_files[0]
    try:
        df_temp = pd.read_csv(first_csv)
        if not df_temp.empty and len(df_temp.columns) > 0:
            start = df_temp.iloc[-1, 0]
            start = dt.datetime.strptime(start, "%Y-%m-%d").strftime("%Y%m%d")
            logger.info(f"读取起始日期:{start}")
            
            today = dt.date.today()
            if today.weekday() == 5:
                nearest_workday = (today - dt.timedelta(days=1)).strftime("%Y%m%d")
            elif today.weekday() == 6:
                nearest_workday = (today - dt.timedelta(days=2)).strftime("%Y%m%d")
            else:
                nearest_workday = today.strftime("%Y%m%d")
            
            if str(start) == nearest_workday:
                logger.info("数据已是最新，无需更新")
                return None
            
            start = (dt.datetime.strptime(start, "%Y%m%d") + dt.timedelta(days=1)).strftime("%Y%m%d")
            return start
        else:
            return "20190101"
    except Exception as e:
        logger.warning(f"无法从 {first_csv} 读取起始日期: {e}")
        return "20190101"


def fetch_latest_kline():
    """获取最新股票K线的主函数"""
    global pro
    
    logger.info("开始执行定时任务：获取最新股票K线")
    
    # 初始化Tushare API
    if not _init_tushare():
        return
    
    # 创建输出目录
    out_dir = config.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 确定起始日期
    start = _get_start_date(out_dir)
    if start is None:
        return
    
    end = dt.date.today().strftime("%Y%m%d")
    
    # 加载股票列表
    stocklist_path = config.stocklist_path
    if not stocklist_path.exists():
        logger.error(f"股票列表文件不存在: {stocklist_path}")
        return
    
    codes = load_codes_from_stocklist(stocklist_path, config.exclude_boards)
    
    if not codes:
        logger.error("stocklist 为空或被过滤后无代码，请检查。")
        return
    
    logger.info(
        "开始抓取 %d 支股票 | 数据源:Tushare(日线,qfq) | 日期:%s → %s",
        len(codes), start, end,
    )
    
    # 分批处理
    total_batches = (len(codes) + config.batch_size - 1) // config.batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * config.batch_size
        end_idx = min((batch_num + 1) * config.batch_size, len(codes))
        batch_codes = codes[start_idx:end_idx]
        
        logger.info("正在处理批次 %d/%d (股票 %d-%d)",
                    batch_num + 1, total_batches, start_idx + 1, end_idx)
        time.sleep(1)
        
        with ThreadPoolExecutor(max_workers=config.workers) as executor:
            futures = [
                executor.submit(fetch_one, code, start, end, out_dir)
                for code in batch_codes
            ]
            
            with tqdm(as_completed(futures), total=len(futures),
                      desc=f"批次 {batch_num + 1}/{total_batches}") as pbar:
                for future in pbar:
                    try:
                        future.result()
                    except Exception as e:
                        pbar.write(f"任务执行出错: {e}")
                        logger.error(f"任务执行出错: {e}")
        
        gc.collect()
        # 批次之间添加延迟，更均匀地分布请求
        batch_delay = 2  # 每个批次后延迟2秒
        logger.debug(f"批次 {batch_num + 1} 完成，延迟 {batch_delay} 秒")
        time.sleep(batch_delay)
    
    logger.info("全部任务完成，数据已保存至 %s", out_dir.resolve())
    
    # 清理资源
    if pro is not None:
        try:
            pro.close()
        except:
            pass
    gc.collect()
