import pandas as pd
from .base import BuyStrategy


class B1BuyStrategy(BuyStrategy):

    strategy_name = "反者B1买点"

    """
    B1买入策略

    买入条件：
    1) KDJ的 J <= 14
    2) 股价收盘价在duokong_line上方
    3) 最近 lookback_n 内，存在一次收盘价大于trend_line
    4) 最近 lookback_n 内,最大成交量日记为T从[today-T, today]内，成交量MA5 回归斜率 < 0
    5) 近 ma60_slope_days（默认 5）个交易日的 MA60 回归斜率 > 0
    6) trend_line的价格大于duokong_line的价格
    """
    def check_signal(self):
        kdj_j = self.strategy.kdj.J[0]
        condition1 = kdj_j <= 14
        # 先屏蔽
        condition2 = self.strategy.dataclose[0] > self.strategy.double_line.duokong_line[0]
        # condition2 = True
        lookback_n = self.strategy.params.lookback_n
        if len(self.strategy.dataclose) >= lookback_n:
            condition3 = any(
                self.strategy.dataclose[-i] > self.strategy.double_line.trend_line[-i]
                for i in range(1, lookback_n + 1)
            )

            volumes = [self.strategy.datavol[-i] for i in range(1, lookback_n + 1)]
            max_vol_idx = volumes.index(max(volumes)) + 1
            t = max_vol_idx

            if len(self.strategy.vol_ma5) >= t + 4:
                vol_ma5_values = [self.strategy.vol_ma5[-i] for i in range(1, t + 1)]
                vol_ma5_values = vol_ma5_values[::-1]
                vol_slope = self.calculate_slope(
                    vol_ma5_values, len(vol_ma5_values)
                )
                condition4 = vol_slope < 0
            else:
                condition4 = False
        else:
            condition3 = False
            condition4 = False

        if len(self.strategy.double_line.ma1) >= self.strategy.params.ma60_slope_days:
            ma60_values = [
                self.strategy.double_line.ma1[-i] for i in range(0, self.strategy.params.ma60_slope_days)
            ]
            ma60_values = ma60_values[::-1]
            # if len(self) % 50 == 0:
            #     dates = [self.datas[0].datetime.date(-i) for i in range(0, self.params.ma60_slope_days)]
            #     pairs = list(zip(dates, ma60_values))
            #     log_str = "MA1计算: " + ", ".join([f"{d.isoformat()}:{v:.2f}" for d, v in pairs])
            #     self.log(log_str)
            ma60_slope = self.calculate_slope(ma60_values, len(ma60_values))
            condition5 = ma60_slope > 0
        else:
            condition5 = False

        condition6 = self.strategy.double_line.trend_line[0] > self.strategy.double_line.duokong_line[0]

        target_date = pd.to_datetime('2026-02-13').date()
        current_date = self.strategy.datas[0].datetime.date(0)
        if current_date == target_date:
            self.strategy.log(
                f"条件检查 - "
                f"KDJ_J={kdj_j:.2f}(<=14:{condition1}), "
                f"收盘价={self.strategy.dataclose[0]:.2f}>多空线={self.strategy.double_line.duokong_line[0]:.2f}({condition2}), "
                f"condition3={condition3}, "
                f"condition4={condition4}, "
                f"trend_line={self.strategy.double_line.trend_line[0]:.2f}>duokong_line={self.strategy.double_line.duokong_line[0]:.2f}({condition6}), "
                f"MA60斜率={ma60_slope if 'ma60_slope' in locals() else 'N/A':.4f}(>0:{condition5})"
            )

        if condition1 and condition2 and condition3 and condition4 and condition5 and condition6:
            available_cash = self.strategy.broker.getcash()
            price = self.strategy.dataclose[0]
            commission_rate = 0.0002
            max_cost = available_cash / (1 + commission_rate)
            size = int(max_cost / price / 100) * 100

            if size > 0:
                signal_info = {
                    'type': 'buy',
                    'strategy_name': self.strategy_name,
                    'price': price,
                    'kdj_j': kdj_j,
                    'duokong_line': self.strategy.double_line.duokong_line[0],
                    'ma60_slope': ma60_slope,
                    'size': size,
                    'conditions': {
                        'kdj_j_le_13': condition1,
                        'close_above_duokong': condition2,
                        'close_above_trend_history': condition3,
                        'vol_ma5_slope_lt_0': condition4,
                        'ma60_slope_gt_0': condition5,
                        'trend_above_duokong': condition6
                    }
                }
                self.strategy.log(
                    f"买入信号, 价格: {price:.2f}, "
                    # f"KDJ_J: {kdj_j:.2f}, "
                    # f"多空线: {self.strategy.double_line.duokong_line[0]:.2f}, "
                    # f"MA60斜率: {ma60_slope:.4f}, "
                    # f"数量: {size}"
                )
                return True, size, signal_info

        return False, 0, None
