from .registry import StrategyRegistry

class TradeSignalGenerator:
    """
    交易信号生成器类

    封装买入和卖出逻辑，支持单日测试
    使用注册机制动态选择买入和卖出策略
    """

    def __init__(self, strategy, buy_strategies=None, sell_strategies=None):
        """
        初始化交易信号生成器

        参数：
        - strategy: 策略实例
        - buy_strategies: 买入策略字典 {name: strategy_class}
        - sell_strategies: 卖出策略字典 {name: strategy_class}
        """
        
        self.strategy = strategy
        self.registry = StrategyRegistry()
        
        if buy_strategies:
            for name, strategy_class in buy_strategies.items():
                self.registry.register_buy_strategy(name, strategy_class)
        
        if sell_strategies:
            for name, strategy_class in sell_strategies.items():
                self.registry.register_sell_strategy(name, strategy_class)

        self.buy_strategy = self.registry.get_buy_strategy(list(buy_strategies.keys())[0], strategy)
        self.sell_strategies = [
            self.registry.get_sell_strategy(name, strategy)
            for name in sell_strategies.keys()
        ]

    def check_buy_signal(self):
        """
        检查买入信号

        返回：
        - (is_signal, size, signal_info)
          is_signal: 是否触发买入信号
          size: 买入数量
          signal_info: 信号信息字典
        """
        return self.buy_strategy.check_signal()

    def check_sell_signal(self):
        """
        检查卖出信号

        返回：
        - (is_signal, size, signal_info)
          is_signal: 是否触发卖出信号
          size: 卖出数量
          signal_info: 信号信息字典
        """
        for sell_strategy in self.sell_strategies:
            is_signal, size, signal_info = sell_strategy.check_signal()
            if is_signal:
                return is_signal, size, signal_info

        return False, 0, None
