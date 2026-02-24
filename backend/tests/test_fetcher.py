"""测试股票数据抓取模块"""

import logging
import sys
from pathlib import Path

# 添加backend目录到Python搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetcher import fetch_latest_kline, config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_fetch_latest_kline():
    """测试抓取最新K线数据"""
    logger.info("开始测试抓取最新K线数据")
    logger.info(f"股票列表路径: {config.stocklist_path}")
    logger.info(f"输出目录: {config.out_dir}")
    
    # 确保输出目录存在
    config.out_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查股票列表文件是否存在
    if not config.stocklist_path.exists():
        logger.error(f"股票列表文件不存在: {config.stocklist_path}")
        return False
    
    try:
        # 调用fetcher模块的主函数抓取数据
        fetch_latest_kline()
        logger.info("抓取完成")
        return True
    except Exception as e:
        logger.error(f"抓取过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    success = test_fetch_latest_kline()
    if success:
        logger.info("测试成功")
    else:
        logger.info("测试失败")
