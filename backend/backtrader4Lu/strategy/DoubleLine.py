import backtrader as bt
import numpy as np
import pandas as pd

from .helper import *


class TDXEMA(bt.Indicator):
    lines = ("ema",)
    params = (("period", 10),)
    plotinfo = dict(plot=False)

    def __init__(self):
        self.alpha = 2.0 / (self.p.period + 1)

    def next(self):
        if len(self) == 1:
            self.lines.ema[0] = self.data[0]
        else:
            prev_ema = self.lines.ema[-1]
            if np.isnan(prev_ema):
                self.lines.ema[0] = self.data[0]
            else:
                self.lines.ema[0] = (
                    self.alpha * self.data[0] + (1 - self.alpha) * prev_ema
                )


class TDXSMA(bt.Indicator):
    lines = ("sma",)
    params = (("period", 14),)
    plotinfo = dict(plot=False)

    def next(self):
        current_len = len(self)
        period = self.p.period

        if current_len == 0:
            return

        n = min(current_len, period)
        values = [self.data[-i] for i in range(1, n + 1)]
        self.lines.sma[0] = sum(values) / n


class DoubleLineIndicator(bt.Indicator):
    """
    双线指标类

    包含三条指标线：
    1. trend_line (知行短期趋势线 ZXDQ): EMA(EMA(C,10),10) - 双重平滑的10日EMA
    2. duokong_line (知行多空线 ZXDKX): (MA14+MA28+MA57+MA114)/4 - 四条均线的平均值
    3. ma1 (MA60): MA(CLOSE,60) - 60日均线
    """

    lines = (
        "trend_line",
        "duokong_line",
        "ma1",
    )
    params = (
        ("ema_period", 10),
        ("ma1_period", 14),
        ("ma2_period", 28),
        ("ma3_period", 57),
        ("ma4_period", 114),
        ("ma60_period", 60),
        ("ema13_period", 13),
    )

    plotinfo = dict(subplot=False, plotname="DoubleLines")

    plotlines = dict(
        trend_line=dict(color="red", _name="ZXDQ", linewidth=1.5),
        duokong_line=dict(color="yellow", _name="ZXDKX", linewidth=1.5),
        ma1=dict(color="green", _name="MA60", linewidth=1.0),
    )

    def compute_zx_lines(
        df: pd.DataFrame, m1: int = 14, m2: int = 28, m3: int = 57, m4: int = 114
    ) -> tuple[pd.Series, pd.Series]:
        """返回 (ZXDQ, ZXDKX)
        ZXDQ = EMA(EMA(C,10),10)
        ZXDKX = (MA(C,14)+MA(C,28)+MA(C,57)+MA(C,114))/4
        """
        close = df["close"].astype(float)
        zxdq = close.ewm(span=10, adjust=False).mean().ewm(span=10, adjust=False).mean()

        ma1 = close.rolling(window=m1, min_periods=m1).mean()
        ma2 = close.rolling(window=m2, min_periods=m2).mean()
        ma3 = close.rolling(window=m3, min_periods=m3).mean()
        ma4 = close.rolling(window=m4, min_periods=m4).mean()
        zxdkx = (ma1 + ma2 + ma3 + ma4) / 4.0
        return zxdq, zxdkx

    def __init__(self):
        """
        trend_line:EMA(EMA(C,10),10),COLORFFFFFF,LINETHICK1;
        MA1:=MA(CLOSE,60);
        MA2:=EMA(CLOSE,13);

        Z1:=STRCAT(HYBLOCK,' ');
        Z2:=STRCAT(Z1,DYBLOCK);
        Z3:=STRCAT(Z2,' ');
        DRAWTEXT_FIX(ISLASTBAR,0,0,0,STRCAT(Z3,GNBLOCK)),COLOR00C0C0;

        duokong_line:(MA(CLOSE,M1)+MA(CLOSE,M2)+MA(CLOSE,M3)+MA(CLOSE,M4))/4;
        """
        ema1 = TDXEMA(self.data.close, period=self.p.ema_period)
        self.lines.trend_line = TDXEMA(ema1, period=self.p.ema_period)

        ma1 = TDXSMA(self.data.close, period=self.p.ma1_period)
        ma2 = TDXSMA(self.data.close, period=self.p.ma2_period)
        ma3 = TDXSMA(self.data.close, period=self.p.ma3_period)
        ma4 = TDXSMA(self.data.close, period=self.p.ma4_period)
        self.lines.duokong_line = (ma1 + ma2 + ma3 + ma4) / 4.0

        self.lines.ma1 = TDXSMA(self.data.close, period=self.p.ma60_period)


class KDJIndicator(bt.Indicator):
    lines = ("K", "D", "J")
    params = (
        ("period", 9),
        ("period_k", 3),
        ("period_d", 3),
    )

    plotinfo = dict(subplot=True, plotname="KDJ")

    plotlines = dict(
        K=dict(color="red", _name="K"),
        D=dict(color="green", _name="D"),
        J=dict(color="blue", _name="J"),
    )

    def __init__(self):
        self.low_n = bt.indicators.Lowest(self.data.low, period=self.p.period)
        self.high_n = bt.indicators.Highest(self.data.high, period=self.p.period)
        self.rsv = (
            (self.data.close - self.low_n) / (self.high_n - self.low_n + 1e-9) * 100
        )

    def next(self):
        if len(self) < self.p.period:
            return

        low_val = self.low_n[0]
        high_val = self.high_n[0]
        close_val = self.data.close[0]

        if high_val == low_val:
            rsv_val = 50.0
        else:
            rsv_val = (close_val - low_val) / (high_val - low_val) * 100

        if len(self) == self.p.period:
            self.lines.K[0] = rsv_val
            self.lines.D[0] = rsv_val
        else:
            self.lines.K[0] = (
                1 * rsv_val + (self.p.period_k - 1) * self.lines.K[-1]
            ) / self.p.period_k
            self.lines.D[0] = (
                1 * self.lines.K[0] + (self.p.period_d - 1) * self.lines.D[-1]
            ) / self.p.period_d

        self.lines.J[0] = 3 * self.lines.K[0] - 2 * self.lines.D[0]


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

    def calculate_kdj(df):
        low_list = df["low"].rolling(9, min_periods=9).min()
        high_list = df["high"].rolling(9, min_periods=9).max()
        low_list.fillna(value=0, inplace=True)
        high_list.fillna(value=0, inplace=True)
        rsv = (df["close"] - low_list) / (high_list - low_list) * 100
        # print(rsv.tail())
        df["K"] = pd.DataFrame(rsv).ewm(com=2).mean()
        df["D"] = df["K"].ewm(com=2).mean()
        df["J"] = 3 * df["K"] - 2 * df["D"]
        return df

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

        if len(self.kdj) > 0:
            kdj_k = self.kdj.K[0]
            kdj_d = self.kdj.D[0]
            kdj_j = self.kdj.J[0]
            # if len(self) % 10 == 0:
            #     self.log(f"KDJ - K: {kdj_k:.2f}, D: {kdj_d:.2f}, J: {kdj_j:.2f}")

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
