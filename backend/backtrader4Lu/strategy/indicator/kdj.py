import backtrader as bt


class KDJIndicator(bt.Indicator):
    """
    KDJ指标类

    功能说明：
    - 实现了经典的KDJ技术分析指标
    - 用于判断股票的超买超卖状态和价格走势
    - 包含三条指标线，分别反映不同时间周期的价格动量

    指标线：
    1. K线：快速确认线，反应敏捷，但容易出错
    2. D线：慢速主干线，稳重可靠
    3. J线：方向敏感线，穿透力最强，能领先于K、D线发现价格的转势

    参数：
    - period: RSV计算周期，默认值为9
    - period_k: K线平滑周期，默认值为3
    - period_d: D线平滑周期，默认值为3

    用法：
    - K值在20以下，D值在30以下，J值由负转正上穿K、D值时，视为买入信号
    - K值在80以上，D值在70以上，J值由正转负下穿K、D值时，视为卖出信号
    - K线向上突破D线时，形成金叉，视为买入信号
    - K线向下突破D线时，形成死叉，视为卖出信号
    - J线超过100时，股价可能出现超买，有回调风险
    - J线低于0时，股价可能出现超卖，有反弹机会
    """

    lines = ("K", "D", "J")
    params = (
        ("period", 9),
        ("period_k", 3),
        ("period_d", 3),
    )

    plotinfo = dict(subplot=True, plotname="KDJ")

    plotlines = dict(
        K=dict(color="red", _name="K"),
        D=dict(color="green", _name="D"),
        J=dict(color="blue", _name="J"),
    )

    def __init__(self):
        """
        初始化方法

        设置KDJ指标的计算基础：
        1. 计算指定周期内的最低价
        2. 计算指定周期内的最高价
        3. 计算RSV值（未成熟随机值）

        RSV计算公式：
        RSV = (收盘价 - 周期内最低价) / (周期内最高价 - 周期内最低价) * 100
        """
        self.low_n = bt.indicators.Lowest(self.data.low, period=self.p.period)
        self.high_n = bt.indicators.Highest(self.data.high, period=self.p.period)
        self.rsv = (
            (self.data.close - self.low_n) / (self.high_n - self.low_n + 1e-9) * 100
        )

    def next(self):
        """
        每个K线周期调用一次

        计算当前K线的KDJ值：
        1. 计算RSV值，处理最高价等于最低价的特殊情况
        2. 计算K值：K = (1/period_k)*RSV + ((period_k-1)/period_k)*前一期K值
        3. 计算D值：D = (1/period_d)*K + ((period_d-1)/period_d)*前一期D值
        4. 计算J值：J = 3*K - 2*D

        特殊处理：
        - 当数据长度不足计算周期时，不进行计算
        - 当首次计算时，K、D值都设为RSV值
        """
        if len(self) < self.p.period:
            return

        low_val = self.low_n[0]
        high_val = self.high_n[0]
        close_val = self.data.close[0]

        if high_val == low_val:
            rsv_val = 50.0
        else:
            rsv_val = (close_val - low_val) / (high_val - low_val) * 100

        if len(self) == self.p.period:
            self.lines.K[0] = rsv_val
            self.lines.D[0] = rsv_val
        else:
            self.lines.K[0] = (
                1 * rsv_val + (self.p.period_k - 1) * self.lines.K[-1]
            ) / self.p.period_k
            self.lines.D[0] = (
                1 * self.lines.K[0] + (self.p.period_d - 1) * self.lines.D[-1]
            ) / self.p.period_d

        self.lines.J[0] = 3 * self.lines.K[0] - 2 * self.lines.D[0]
