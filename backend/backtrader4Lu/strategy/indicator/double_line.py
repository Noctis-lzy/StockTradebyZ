import backtrader as bt
import pandas as pd
from .tdx_ema import TDXEMA
from .tdx_sma import TDXSMA


class DoubleLineIndicator(bt.Indicator):
    """
    双线指标类

    包含三条指标线：
    1. trend_line (知行短期趋势线 ZXDQ): EMA(EMA(C,10),10) - 双重平滑的10日EMA
    2. duokong_line (知行多空线 ZXDKX): (MA14+MA28+MA57+MA114)/4 - 四条均线的平均值
    3. ma1 (MA60): MA(CLOSE,60) - 60日均线
    """

    lines = (
        "trend_line",
        "duokong_line",
        "ma1",
    )
    params = (
        ("ema_period", 10),
        ("ma1_period", 14),
        ("ma2_period", 28),
        ("ma3_period", 57),
        ("ma4_period", 114),
        ("ma60_period", 60),
        ("ema13_period", 13),
    )

    plotinfo = dict(subplot=False, plotname="DoubleLines")

    plotlines = dict(
        trend_line=dict(color="red", _name="ZXDQ", linewidth=1.5),
        duokong_line=dict(color="yellow", _name="ZXDKX", linewidth=1.5),
        ma1=dict(color="green", _name="MA60", linewidth=1.0),
    )

    def compute_zx_lines(
        df: pd.DataFrame, m1: int = 14, m2: int = 28, m3: int = 57, m4: int = 114
    ) -> tuple[pd.Series, pd.Series]:
        """返回 (ZXDQ, ZXDKX)
        ZXDQ = EMA(EMA(C,10),10)
        ZXDKX = (MA(C,14)+MA(C,28)+MA(C,57)+MA(C,114))/4
        """
        close = df["close"].astype(float)
        zxdq = close.ewm(span=10, adjust=False).mean().ewm(span=10, adjust=False).mean()

        ma1 = close.rolling(window=m1, min_periods=m1).mean()
        ma2 = close.rolling(window=m2, min_periods=m2).mean()
        ma3 = close.rolling(window=m3, min_periods=m3).mean()
        ma4 = close.rolling(window=m4, min_periods=m4).mean()
        zxdkx = (ma1 + ma2 + ma3 + ma4) / 4.0
        return zxdq, zxdkx

    def __init__(self):
        """
        trend_line:EMA(EMA(C,10),10),COLORFFFFFF,LINETHICK1;
        MA1:=MA(CLOSE,60);
        MA2:=EMA(CLOSE,13);

        Z1:=STRCAT(HYBLOCK,' ');
        Z2:=STRCAT(Z1,DYBLOCK);
        Z3:=STRCAT(Z2,' ');
        DRAWTEXT_FIX(ISLASTBAR,0,0,0,STRCAT(Z3,GNBLOCK)),COLOR00C0C0;

        duokong_line:(MA(CLOSE,M1)+MA(CLOSE,M2)+MA(CLOSE,M3)+MA(CLOSE,M4))/4;
        """
        ema1 = TDXEMA(self.data.close, period=self.p.ema_period)
        self.lines.trend_line = TDXEMA(ema1, period=self.p.ema_period)

        ma1 = TDXSMA(self.data.close, period=self.p.ma1_period)
        ma2 = TDXSMA(self.data.close, period=self.p.ma2_period)
        ma3 = TDXSMA(self.data.close, period=self.p.ma3_period)
        ma4 = TDXSMA(self.data.close, period=self.p.ma4_period)
        self.lines.duokong_line = (ma1 + ma2 + ma3 + ma4) / 4.0

        self.lines.ma1 = TDXSMA(self.data.close, period=self.p.ma60_period)
