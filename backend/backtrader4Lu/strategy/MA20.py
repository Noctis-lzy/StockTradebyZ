import backtrader as bt

# 20日均线策略
# 当收盘价上穿20日均线时，买入；当收盘价下穿20日均线时，卖出
class Ma20(bt.Strategy):
    params = (("ma_period", 20),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.ma = bt.indicators.MovingAverageSimple(
            self.datas[0], period=self.params.ma_period
        )
        self.buy_date = None

    def notify_order(self, order):
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
            else:
                self.log(
                    f"卖出执行, 价格: {order.executed.price:.2f}, "
                    f"成本: {order.executed.value:.2f}, "
                    f"手续费: {order.executed.comm:.2f}"
                )
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f"订单取消/拒绝/保证金不足, 状态: {order.getstatusname()}")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f"交易利润, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}")

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.dataclose[0] > self.ma[0] and self.dataclose[-1] < self.ma[-1]:
                available_cash = self.broker.getcash()
                price = self.dataclose[0]
                commission_rate = 0.0002
                max_cost = available_cash / (1 + commission_rate)
                size = int(max_cost / price / 100) * 100
                if size > 0:
                    self.log(
                        f"上穿20日均线买入, 价格: {price:.2f}, 均线: {self.ma[0]:.2f}, 数量: {size}"
                    )
                    self.order = self.buy(size=size)
        else:
            if len(self.dataclose) >= 2:
                if self.dataclose[0] < self.ma[0] and self.dataclose[-1] > self.ma[-1]:
                    size = self.position.size
                    self.log(
                        f"下穿20日均线卖出, 价格: {self.dataclose[0]:.2f}, 均线: {self.ma[0]:.2f}, 数量: {size}"
                    )
                    self.order = self.sell(size=size)
                else:
                    dt = self.datas[0].datetime.date(0)
                    if self.buy_date and (dt - self.buy_date).days % 30 == 0:
                        self.log(
                            f"持仓中, 价格: {self.dataclose[0]:.2f}, 均线: {self.ma[0]:.2f}, 差值: {self.dataclose[0] - self.ma[0]:.2f}"
                        )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f"{dt.isoformat()}, {txt}")