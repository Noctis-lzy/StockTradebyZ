from .base import SellStrategy


class SuspectedTopWindmillSellStrategy(SellStrategy):

    strategy_name = "suspected_top_windmill"

    """
    疑似顶部大风车卖出策略

    卖出条件：
    1）阴线
    2）今日成交量是成交量MA10的130%以上
    3) J大于70

    卖出数量：持仓数量的一半
    """

    def check_signal(self):
        kdj_j = self.strategy.kdj.J[0]

        condition1 = self.strategy.dataclose[0] < self.strategy.dataopen[0]
        condition2 = self.strategy.datavol[0] >= 1.3 * self.strategy.vol_ma10[0]
        condition3 = kdj_j > 70

        if condition1 and condition2 and condition3:
            size = self.strategy.position.size // 2
            signal_info = {
                'type': 'sell_half',
                'reason': 'suspected_top_windmill',
                'price': self.strategy.dataclose[0],
                'duokong_line': self.strategy.double_line.duokong_line[0],
                'volume': self.strategy.datavol[0],
                'volume_ma10': self.strategy.vol_ma10[0],
                'kdj_j': kdj_j,
                'size': size,
                'conditions': {
                    'is_bearish': condition1,
                    'volume_ge_130pct_ma10': condition2,
                    'kdj_j_gt_70': condition3
                }
            }
            self.strategy.log(
                f"疑似顶部大风车信号, 价格: {self.strategy.dataclose[0]:.2f}, "
                # f"多空线: {self.strategy.double_line.duokong_line[0]:.2f}, "
                # f"成交量: {self.strategy.datavol[0]:.2f}, "
                # f"成交量MA10: {self.strategy.vol_ma10[0]:.2f}, "
                # f"数量: {size}"
            )
            return True, size, signal_info

        return False, 0, None
