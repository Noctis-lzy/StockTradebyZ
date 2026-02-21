class StrategyRegistry:
    """
    策略注册器

    用于注册和管理买入/卖出策略
    每个实例拥有独立的策略注册表
    """

    def __init__(self):
        """
        初始化策略注册器
        """
        self._buy_strategies = {}
        self._sell_strategies = {}

    def register_buy_strategy(self, name, strategy_class):
        """
        注册买入策略

        参数：
        - name: 策略名称
        - strategy_class: 策略类
        """
        self._buy_strategies[name] = strategy_class

    def register_sell_strategy(self, name, strategy_class):
        """
        注册卖出策略

        参数：
        - name: 策略名称
        - strategy_class: 策略类
        """
        self._sell_strategies[name] = strategy_class

    def get_buy_strategy(self, name, strategy):
        """
        获取买入策略实例

        参数：
        - name: 策略名称
        - strategy: 策略实例

        返回：
        - 买入策略实例
        """
        if name not in self._buy_strategies:
            raise ValueError(f"未找到买入策略: {name}")
        return self._buy_strategies[name](strategy)

    def get_sell_strategy(self, name, strategy):
        """
        获取卖出策略实例

        参数：
        - name: 策略名称
        - strategy: 策略实例

        返回：
        - 卖出策略实例
        """
        if name not in self._sell_strategies:
            raise ValueError(f"未找到卖出策略: {name}")
        return self._sell_strategies[name](strategy)

    def list_buy_strategies(self):
        """
        列出所有已注册的买入策略

        返回：
        - 买入策略名称列表
        """
        return list(self._buy_strategies.keys())

    def list_sell_strategies(self):
        """
        列出所有已注册的卖出策略

        返回：
        - 卖出策略名称列表
        """
        return list(self._sell_strategies.keys())

