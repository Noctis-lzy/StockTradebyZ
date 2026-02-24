import backtrader as bt
import numpy as np


class TDXEMA(bt.Indicator):
    """
    TDXEMA 指标类

    实现了通达信风格的指数移动平均线(EMA)计算

    功能说明：
    - 计算指定周期的指数移动平均线
    - 采用标准EMA计算公式：EMA = α * 当前价格 + (1-α) * 前一期EMA
    - 其中α = 2 / (周期 + 1)，为平滑系数

    指标线：
    - ema: 指数移动平均线值

    参数：
    - period: EMA计算周期，默认值为10

    用法：
    - 通常作为其他指标的基础组件使用
    - 可用于趋势判断、价格平滑等场景
    """
    lines = ("ema",)
    params = (("period", 10),)
    plotinfo = dict(plot=False)

    def __init__(self):
        """
        初始化方法

        计算EMA的平滑系数α
        """
        self.alpha = 2.0 / (self.p.period + 1)

    def next(self):
        """
        每个K线周期调用一次

        计算当前K线的EMA值：
        - 第一条K线时，EMA值等于当前价格
        - 后续K线时，使用标准EMA公式计算
        - 处理前一期EMA值为NaN的情况
        """
        if len(self) == 1:
            self.lines.ema[0] = self.data[0]
        else:
            prev_ema = self.lines.ema[-1]
            if np.isnan(prev_ema):
                self.lines.ema[0] = self.data[0]
            else:
                self.lines.ema[0] = (
                    self.alpha * self.data[0] + (1 - self.alpha) * prev_ema
                )
