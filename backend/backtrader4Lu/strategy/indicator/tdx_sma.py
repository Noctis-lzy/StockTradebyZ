import backtrader as bt


class TDXSMA(bt.Indicator):
    """
    TDXSMA 指标类

    实现了通达信风格的简单移动平均线(SMA)计算

    功能说明：
    - 计算指定周期的简单移动平均线
    - 采用标准SMA计算公式：SMA = 最近N期价格之和 / N
    - 当数据长度不足周期时，使用实际可用的数据长度计算

    指标线：
    - sma: 简单移动平均线值

    参数：
    - period: SMA计算周期，默认值为14

    用法：
    - 通常作为其他指标的基础组件使用
    - 可用于趋势判断、支撑阻力位识别等场景
    """
    lines = ("sma",)
    params = (("period", 14),)
    plotinfo = dict(plot=False)

    def next(self):
        """
        每个K线周期调用一次

        计算当前K线的SMA值：
        - 获取当前数据长度
        - 当数据长度为0时，直接返回
        - 计算实际使用的数据长度（不超过设定周期）
        - 收集最近N期的数据值
        - 计算平均值作为SMA值
        """
        current_len = len(self)
        period = self.p.period

        if current_len == 0:
            return

        n = min(current_len, period)
        values = [self.data[-i] for i in range(1, n + 1)]
        self.lines.sma[0] = sum(values) / n
