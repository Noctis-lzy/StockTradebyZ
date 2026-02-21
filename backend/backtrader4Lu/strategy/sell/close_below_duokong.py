from .base import SellStrategy


class CloseBelowDuokongSellStrategy(SellStrategy):

    strategy_name = "close_below_duokong"

    """
    收盘价低于多空线卖出策略

    卖出条件：
    - 今日收盘价低于今日duokong_line
    - 昨日收盘价低于昨日duokong_line
    """

    def check_signal(self):
        if len(self.strategy.dataclose) >= 2:
            condition_sell1 = self.strategy.dataclose[-1] < self.strategy.double_line.duokong_line[-1]
            condition_sell2 = self.strategy.dataclose[0] < self.strategy.double_line.duokong_line[0]

            if condition_sell1 and condition_sell2:
                size = self.strategy.position.size
                signal_info = {
                    'type': 'sell_full',
                    'reason': 'close_below_duokong',
                    'price': self.strategy.dataclose[0],
                    'duokong_line': self.strategy.double_line.duokong_line[0],
                    'size': size
                }
                self.strategy.log(
                    f"止盈止损信号, 价格: {self.strategy.dataclose[0]:.2f}, "
                    # f"多空线: {self.strategy.double_line.duokong_line[0]:.2f}, "
                    # f"数量: {size}"
                )
                return True, size, signal_info

        return False, 0, None
