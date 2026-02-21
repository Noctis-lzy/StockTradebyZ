import pandas as pd
from .base import SellStrategy


class StandardTopWindmillSellStrategy(SellStrategy):

    strategy_name = "standard_top_windmill"

    """
    标准顶部大风车卖出策略

    卖出条件：
    1）阴线
    2）上影线的幅度在1.5%以上
    3）下影线的幅度在0.5%以上
    4）今日成交量是成交量MA10的120%以上
    5）今日成交量是最近三天最高
    6）今日成交量大于等于MA5成交量
    7) J大于70
    """

    def check_signal(self):
        kdj_j = self.strategy.kdj.J[0]

        condition1 = self.strategy.dataclose[0] < self.strategy.dataopen[0]
        condition2 = (self.strategy.datahigh[0] - self.strategy.dataopen[0]) / self.strategy.dataclose[0] >= 0.015
        condition3 = (self.strategy.dataclose[0] - self.strategy.datalow[0]) / self.strategy.dataclose[0] >= 0.005
        condition4 = self.strategy.datavol[0] >= 1.2 * self.strategy.vol_ma10[0]
        vol_values = [self.strategy.datavol[-i] for i in range(3)]
        condition5 = self.strategy.datavol[0] == max(vol_values)
        condition6 = self.strategy.datavol[0] >= self.strategy.vol_ma5[0]
        condition7 = kdj_j > 50
        # # 如果是25年8月21号，则打印这些条件
        # if self.strategy.datetime.date() == pd.Timestamp('2025-08-21').date():
        #     print(f"StandardTopWindmillSellStrategy 检查条件:")
        #     print(f"1) 阴线: {condition1}")
        #     print(f"2) 上影线幅度 >= 1.5%: {condition2}")
        #     print(f"3) 下影线幅度 >= 0.5%: {condition3}")
        #     print(f"4) 今日成交量 >= 1.2 * 成交量MA10: {condition4}")
        #     print(f"5) 今日成交量是最近三天最高: {condition5}")
        #     print(f"6) 今日成交量 >= 成交量MA5: {condition6}")
        #     print(f"7) J > 70: {condition7}")

        if condition1 and condition2 and condition3 and condition4 and condition5 and condition6 and condition7:
            size = self.strategy.position.size
            signal_info = {
                'type': 'sell_full',
                'reason': 'standard_top_windmill',
                'price': self.strategy.dataclose[0],
                'duokong_line': self.strategy.double_line.duokong_line[0],
                'volume': self.strategy.datavol[0],
                'volume_ma10': self.strategy.vol_ma10[0],
                'kdj_j': kdj_j,
                'size': size,
                'conditions': {
                    'is_bearish': condition1,
                    'upper_shadow_ge_1.5pct': condition2,
                    'lower_shadow_ge_0.5pct': condition3,
                    'volume_ge_120pct_ma10': condition4,
                    'volume_is_max_3days': condition5,
                    'volume_ge_ma5': condition6,
                    'kdj_j_gt_70': condition7
                }
            }
            self.strategy.log(
                f"标准顶部大风车信号, 价格: {self.strategy.dataclose[0]:.2f}, "
                # f"多空线: {self.strategy.double_line.duokong_line[0]:.2f}, "
                # f"成交量: {self.strategy.datavol[0]:.2f}, "
                # f"成交量MA10: {self.strategy.vol_ma10[0]:.2f}, "
                # f"数量: {size}"
            )
            return True, size, signal_info

        return False, 0, None
