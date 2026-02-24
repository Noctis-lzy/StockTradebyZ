import backtrader as bt
import pandas as pd
import os

from backtrader4Lu.strategy.double_line_b1_strategy import DoubleLineStrategy
from backtrader4Lu.strategy.buy import B1BuyStrategy

from backtrader4Lu.strategy.sell import (
    CloseBelowDuokongSellStrategy,
    StandardTopWindmillSellStrategy,
    SuspectedTopWindmillSellStrategy,
)


class StockPandasData(bt.feeds.PandasData):
    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("openinterest", None),
    )


def run_backtest(
    stock_code="000001",
    initial_cash=500000,
    commission=0.0002,
    start_date="2024-09-24",
    end_date="2026-02-12",
    execute_start_date=None,
    execute_end_date=None,
    strategy=DoubleLineStrategy,
    plot=False,
    buy_strategies=None,
    sell_strategies=None,
):
    data_path = f"data/stock_kline_data/{stock_code}.csv"
    if not os.path.exists(data_path):
        data_path = f"../data/stock_kline_data/{stock_code}.csv"

    if not os.path.exists(data_path):
        print(f"错误: 找不到股票数据文件 {data_path}")
        return None

    df = pd.read_csv(data_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    start_date_dt = pd.to_datetime(start_date)
    end_date_dt = pd.to_datetime(end_date)
    df = df.loc[start_date_dt:end_date_dt]

    cerebro = bt.Cerebro()

    cerebro.adddata(StockPandasData(dataname=df))

    cerebro.addstrategy(
        strategy,
        start_date=start_date,
        end_date=end_date,
        execute_start_date=execute_start_date,
        execute_end_date=execute_end_date,
        buy_strategies=buy_strategies,
        sell_strategies=sell_strategies,
    )

    cerebro.broker.setcash(initial_cash)

    cerebro.broker.setcommission(commission=commission)

    cerebro.broker.set_coc(True)

    results = cerebro.run()
    print(
        "==============================================================================================="
    )
    print(f"股票代码: {stock_code}")
    print(f"初始资金: {initial_cash:.2f}")
    print(f"数据行数: {len(df)}")
    print(f"回测日期范围: {start_date} 到 {end_date}")
    print(f"最终资金: {cerebro.broker.getvalue():.2f}")
    print(f"总收益率: {(cerebro.broker.getvalue() / initial_cash - 1) * 100:.2f}%")
    print(
        "==============================================================================================="
    )

    strategy_instance = results[0]
    all_signals = getattr(strategy_instance, "all_signals", [])

    result = {"all_signals": all_signals}

    if plot:
        try:
            cerebro.plot(style="candle", barup="red", bardown="green")
        except ImportError as e:
            print(f"警告: 无法绘图，缺少必要的库: {e}")
            print(f"提示: 如需绘图功能，请安装 matplotlib")
        except Exception as e:
            print(f"警告: 绘图时发生错误: {e}")

    return result


if __name__ == "__main__":
    stock_code = "600362"
    initial_cash = 500000
    commission = 0.0002
    start_date = "2024-09-24"
    end_date = "2026-02-13"
    buy_strategies = {"B1": B1BuyStrategy}
    
    sell_strategies = {
        "close_below_duokong": CloseBelowDuokongSellStrategy,
        "standard_top_windmill": StandardTopWindmillSellStrategy,
        "suspected_top_windmill": SuspectedTopWindmillSellStrategy,
    }
    
    run_backtest(
        stock_code=stock_code,
        initial_cash=initial_cash,
        commission=commission,
        start_date=start_date,
        end_date=end_date,
        strategy=DoubleLineStrategy,
        buy_strategies=buy_strategies,
        sell_strategies=sell_strategies,
        plot=True,
    )
