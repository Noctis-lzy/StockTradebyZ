import numpy as np


class BuyStrategy:
    """
    买入策略基类

    所有买入策略都需要继承此类并实现check_signal方法
    """

    strategy_name = "base"

    def __init__(self, strategy):
        self.strategy = strategy
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0
        self.buy_dates = []
        self.total_commission = 0
        self.current_trade_commission = 0

    def check_signal(self):
        """
        检查买入信号

        返回：
        - (is_signal, size, signal_info)
          is_signal: 是否触发买入信号
          size: 买入数量
          signal_info: 信号信息字典
        """
        raise NotImplementedError("子类必须实现check_signal方法")

    def calculate_slope(self, data_array, n):
        """
        计算数据序列的线性回归斜率

        参数：
        - data_array: 数据序列
        - n: 计算斜率的数据点数量

        返回：
        - 斜率值，正数表示上升趋势，负数表示下降趋势
        """
        if len(data_array) < n:
            return 0
        if n < 2:
            return 0
        x = np.arange(n)
        y = np.array(data_array[-n:])
        if np.any(np.isnan(y)):
            return 0
        try:
            slope = np.polyfit(x, y, 1)[0]
        except (np.linalg.LinAlgError, ValueError):
            slope = 0
        return slope

    def update_trade_stats(self, pnlcomm, buy_date=None):
        """
        更新交易统计数据

        参数：
        - pnlcomm: 净利润
        - buy_date: 买入日期
        """
        self.total_trades += 1
        if buy_date:
            self.buy_dates.append(buy_date)
        if pnlcomm > 0:
            self.winning_trades += 1
            self.total_profit += pnlcomm
        else:
            self.losing_trades += 1
            self.total_loss += abs(pnlcomm)

    def get_stats(self):
        """
        获取交易统计信息

        返回：
        - 包含胜率和盈亏比的字典
        """
        if self.total_trades == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_loss': 0,
                'profit_loss_ratio': 0
            }

        win_rate = (self.winning_trades / self.total_trades) * 100
        profit_loss_ratio = (self.total_profit / self.total_loss) if self.total_loss > 0 else float('inf')

        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'profit_loss_ratio': profit_loss_ratio
        }

    def print_stats(self):
        """
        打印交易统计信息
        """
        stats = self.get_stats()
        print("\n===============================================================================================")
        print(f"买入策略统计:")
        print(f"完全平仓的交易次数: {stats['total_trades']}")
        if self.buy_dates:
            print(f"买入时间: {', '.join([str(d) for d in self.buy_dates])}")
        print(f"盈利次数: {stats['winning_trades']}")
        print(f"亏损次数: {stats['losing_trades']}")
        print(f"胜率: {stats['win_rate']:.2f}%")
        if stats['profit_loss_ratio'] == float('inf'):
            print(f"盈亏比: ∞ (无亏损)")
        else:
            print(f"盈亏比: {stats['profit_loss_ratio']:.2f}")
        print(f"总盈利: {stats['total_profit']:.2f}")
        print(f"总亏损: {stats['total_loss']:.2f}")
        print(f"总手续费: {self.total_commission:.2f}")
        
        print("===============================================================================================")
