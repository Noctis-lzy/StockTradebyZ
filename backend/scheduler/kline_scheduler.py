import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from fetcher import fetch_latest_kline

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    """启动定时任务调度器"""
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        logger.warning("调度器已经在运行中")
        return
    
    _scheduler = BackgroundScheduler()
    
    # todo  添加每天20点执行的任务
    # _scheduler.add_job(
    #     fetch_latest_kline,
    #     trigger=CronTrigger(hour=20, minute=0),
    #     id="fetch_kline_daily",
    #     name="每日获取最新股票K线",
    #     replace_existing=True,
    #     misfire_grace_time=3600,  # 1小时的容错时间
    # )
    
    _scheduler.start()
    logger.info("定时任务调度器已启动，每天20:00执行K线获取任务")


def stop_scheduler():
    """停止定时任务调度器"""
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")
    _scheduler = None
