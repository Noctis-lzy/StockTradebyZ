from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import datetime as dt
import pandas as pd

# ---------- 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # 将日志写入文件
        logging.FileHandler("select_results.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("select")


# ---------- 工具 ----------

# 定义函数：加载数据
def load_data(data_dir: Path, codes: Iterable[str]) -> Dict[str, pd.DataFrame]:
    # 初始化空字典，用于存储数据框
    frames: Dict[str, pd.DataFrame] = {}

    # 遍历每个股票/产品代码
    for code in codes:
        # 构建文件路径：数据目录/代码.csv
        fp = data_dir / f"{code}.csv"

        # 检查文件是否存在
        if not fp.exists():
            # 如果文件不存在，记录警告日志并跳过
            logger.warning("%s 不存在，跳过", fp.name)
            continue

        # 读取CSV文件，将"date"列解析为日期格式，并按日期排序
        df = pd.read_csv(fp, parse_dates=["date"]).sort_values("date")

        # 将数据框存入字典，键为代码
        frames[code] = df

    # 返回包含所有数据框的字典
    return frames


def load_config(cfg_path: Path) -> List[Dict[str, Any]]:
    if not cfg_path.exists():
        logger.error("配置文件 %s 不存在", cfg_path)
        sys.exit(1)
    with cfg_path.open(encoding="utf-8") as f:
        cfg_raw = json.load(f)

    # 兼容三种结构：单对象、对象数组、或带 selectors 键
    if isinstance(cfg_raw, list):
        cfgs = cfg_raw
    elif isinstance(cfg_raw, dict) and "selectors" in cfg_raw:
        cfgs = cfg_raw["selectors"]
    else:
        cfgs = [cfg_raw]

    if not cfgs:
        logger.error("configs.json 未定义任何 Selector")
        sys.exit(1)

    return cfgs


def instantiate_selector(cfg: Dict[str, Any]):
    """动态加载 Selector 类并实例化"""
    cls_name: str = cfg.get("class")
    if not cls_name:
        raise ValueError("缺少 class 字段")

    try:
        module = importlib.import_module("Selector")
        cls = getattr(module, cls_name)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"无法加载 Selector.{cls_name}: {e}") from e

    params = cfg.get("params", {})
    return cfg.get("alias", cls_name), cls(**params)


# ---------- 主函数 ----------

def main():
    p = argparse.ArgumentParser(description="Run selectors defined in configs.json")
    p.add_argument("--data-dir", default=r"C:\code\stockData", help="CSV 行情目录")
    p.add_argument("--config", default="./configs.json", help="Selector 配置文件")
    # p.add_argument("--config", default="./debugConfigs.json", help="Selector 配置文件")
    p.add_argument("--date", help="交易日 YYYY-MM-DD；缺省=数据最新日期")
    p.add_argument("--tickers", default="all", help="'all' 或逗号分隔股票代码列表")
    args = p.parse_args()

    # --- 加载行情 ---
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error("数据目录 %s 不存在", data_dir)
        sys.exit(1)

    codes = (
        [f.stem for f in data_dir.glob("*.csv") if f.stem.isdigit() and int(f.stem) < 698000]
        if args.tickers.lower() == "all"
        else [c.strip() for c in args.tickers.split(",") if c.strip()]
    )
    if not codes:
        logger.error("股票池为空！")
        sys.exit(1)

    data = load_data(data_dir, codes)
    if not data:
        logger.error("未能加载任何行情数据")
        sys.exit(1)

    try:
        # trade_date = (
        #     pd.to_datetime(args.date)
        #     if args.date
        #     else max(pd.to_datetime(df["date"]).max() for df in data.values())
        # )
        csv_files = list(data_dir.glob("*.csv"))
        trade_date_srt = pd.read_csv(csv_files[0]).iloc[-1, 0]
        trade_date = dt.datetime.strptime(trade_date_srt, "%Y-%m-%d")
        # trade_date = datetime.date.today()
    except Exception as e:
        # 收集所有date列的类型信息
        type_info = []
        for code, df in data.items():
            if "date" in df.columns:
                sample_value = df["date"].iloc[0] if len(df) > 0 else None
                type_info.append(f"{code}: {type(sample_value)}")

        logger.error(f"日期处理出错: {str(e)}")
        logger.error("各股票date列类型信息:")
        for info in type_info:
            logger.error(info)
        sys.exit(1)

    if not args.date:
        logger.info("未指定 --date，使用最近日期 %s", trade_date.date())

    # --- 加载 Selector 配置 ---
    selector_cfgs = load_config(Path(args.config))

    # --- 逐个 Selector 运行 ---
    for cfg in selector_cfgs:
        if cfg.get("activate", True) is False:
            continue
        try:
            alias, selector = instantiate_selector(cfg)
        except Exception as e:
            logger.error("跳过配置 %s：%s", cfg, e)
            continue

        picks = selector.select(trade_date, data)

        # 将结果写入日志，同时输出到控制台
        logger.info("")
        logger.info("============== 选股结果 [%s] ==============", alias)
        logger.info("交易日: %s", trade_date.date())
        logger.info("符合条件股票数: %d", len(picks))
        logger.info("%s", ", ".join(picks) if picks else "无符合条件股票")


if __name__ == "__main__":
    main()
