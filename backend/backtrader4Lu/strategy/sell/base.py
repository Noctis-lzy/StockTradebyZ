class SellStrategy:
    """
    卖出策略基类

    所有卖出策略都需要继承此类并实现check_signal方法
    """

    strategy_name = "base"

    def __init__(self, strategy):
        self.strategy = strategy

    def check_signal(self):
        """
        检查卖出信号

        返回：
        - (is_signal, size, signal_info)
          is_signal: 是否触发卖出信号
          size: 卖出数量
          signal_info: 信号信息字典
        """
        raise NotImplementedError("子类必须实现check_signal方法")
