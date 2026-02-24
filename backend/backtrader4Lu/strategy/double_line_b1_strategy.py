import backtrader as bt
import numpy as np
import pandas as pd

from .helper import *
from .indicator import DoubleLineIndicator, KDJIndicator



class DoubleLineStrategy(bt.Strategy):
    """
    双线交易策略

    基于双线指标、KDJ、成交量、MA60的综合交易策略

    参数说明：
    - lookback_n: 回溯周期，用于判断历史条件和最大成交量，默认25
    - ma60_slope_days: MA60斜率计算周期，默认10
    """

    params = (
        ("lookback_n", 25),
        ("ma60_slope_days", 10),
        ("start_date", None),
        ("end_date", None),
        ("execute_start_date", None),
        ("execute_end_date", None),
        ("buy_strategies", None),
        ("sell_strategies", None),
    )


    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low

        self.datavol = self.datas[0].volume
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.start_date = pd.to_datetime(self.p.start_date).date() if self.p.start_date else None
        self.end_date = pd.to_datetime(self.p.end_date).date() if self.p.end_date else None

        self.execute_start_date = pd.to_datetime(self.p.execute_start_date).date() if self.p.execute_start_date else self.start_date
        self.execute_end_date = pd.to_datetime(self.p.execute_end_date).date() if self.p.execute_end_date else self.end_date

        self.double_line = DoubleLineIndicator(self.datas[0])

        self.vol_ma5 = bt.indicators.SMA(self.datas[0].volume, period=5)
        self.vol_ma5.plotinfo.plot = False
        self.vol_ma10 = bt.indicators.SMA(self.datas[0].volume, period=10)
        self.vol_ma10.plotinfo.plot = False

        self.kdj = KDJIndicator(self.datas[0])
        self.buy_date = None

        self.signal_generator = TradeSignalGenerator(
            self,
            buy_strategies=self.p.buy_strategies,
            sell_strategies=self.p.sell_strategies
        )
        
        self.all_signals = []

    def notify_order(self, order):
        """
        订单状态变化回调函数

        处理订单的提交、接受、完成、取消等状态
        """
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f"买入执行, 价格: {order.executed.price:.2f}, "
                    f"成本: {order.executed.value:.2f}, "
                    f"手续费: {order.executed.comm:.2f}"
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.buy_date = self.datas[0].datetime.date(0)
                self.signal_generator.buy_strategy.current_trade_commission = order.executed.comm
            else:
                sell_date = self.datas[0].datetime.date(0)
                self.log(
                    f"卖出执行, 价格: {order.executed.price:.2f}, "
                    f"成本: {order.executed.value:.2f}, "
                    f"手续费: {order.executed.comm:.2f}, "
                    f"执行日期: {sell_date}"
                )
                self.signal_generator.buy_strategy.current_trade_commission += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"订单取消/拒绝/保证金不足, 状态: {order.getstatusname()}")

        self.order = None

    def notify_trade(self, trade):
        """
        交易完成回调函数

        在交易完全平仓后触发，计算并记录交易盈亏
        """
        if not trade.isclosed:
            return

        self.log(f"交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}")

        self.signal_generator.buy_strategy.total_commission += self.signal_generator.buy_strategy.current_trade_commission
        self.signal_generator.buy_strategy.current_trade_commission = 0
        self.signal_generator.buy_strategy.update_trade_stats(trade.pnlcomm, self.buy_date)

    def next(self):
        """
        每个K线触发的核心策略逻辑

        包含买入和卖出条件的判断与执行
        """
        if self.order:
            return

        if self.execute_start_date is not None:
            current_date = self.datas[0].datetime.date(0)
            if current_date < self.execute_start_date:
                return

        if self.execute_end_date is not None:
            current_date = self.datas[0].datetime.date(0)
            if current_date > self.execute_end_date:
                return


        is_buy_signal, size, signal_info = self.signal_generator.check_buy_signal()

        if not self.position and is_buy_signal:
            signal_info['date'] = self.datas[0].datetime.date(0)
            self.all_signals.append(signal_info)
            self.order = self.buy(size=size)
        elif self.position:
            is_sell_signal, size, signal_info = self.signal_generator.check_sell_signal()
            if is_sell_signal:
                sell_price = self.dataclose[0]
                self.log(f"卖出信号, 将以收盘价 {sell_price:.2f} 执行")
                self.order = self.close(size=size)

    def log(self, txt, dt=None):
        """
        日志输出函数

        参数：
        - txt: 日志内容
        - dt: 日期时间，默认使用当前K线的日期
        """
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")

    def stop(self):
        """
        回测结束时调用

        输出买入策略的统计信息
        """
        if self.position and self.buy_date:
            self.signal_generator.buy_strategy.buy_dates.append(self.buy_date)
        
        self.signal_generator.buy_strategy.print_stats()
        
        if self.position:
            print(f"\n注意: 回测结束时仍有持仓，数量: {self.position.size}, 当前价格: {self.dataclose[0]:.2f}")
