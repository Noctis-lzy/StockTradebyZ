import backtrader as bt
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from backtrader4Lu.strategy.DoubleLine import DoubleLineStrategy
from backtrader4Lu.strategy.buy import B1WithMA60BuyStrategy, B1BuyStrategy
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


def _run_single_backtest(
    stock_code,
    initial_cash,
    commission,
    start_date,
    end_date,
    strategy,
    buy_strategies,
    sell_strategies,
    min_data_rows,
    stock_industry_dict=None,
    skip_keywords=None,
):
    if stock_industry_dict and skip_keywords:
        industry = stock_industry_dict.get(stock_code, "")
        if industry and any(keyword in industry for keyword in skip_keywords):
            return {
                "stock_code": stock_code,
                "status": "skipped",
                "reason": f"板块包含关键词: {industry}",
            }
    
    data_path = f"data/{stock_code}.csv"
    
    if not os.path.exists(data_path):
        return {
            "stock_code": stock_code,
            "status": "skipped",
            "reason": "数据文件不存在",
        }
    
    try:
        df = pd.read_csv(data_path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
        
        if len(df) < min_data_rows:
            return {
                "stock_code": stock_code,
                "status": "skipped",
                "reason": f"数据行数不足 ({len(df)})",
            }
        
        cerebro = bt.Cerebro()
        cerebro.adddata(StockPandasData(dataname=df))
        cerebro.addstrategy(
            strategy,
            start_date=start_date,
            end_date=end_date,
            buy_strategies=buy_strategies,
            sell_strategies=sell_strategies,
        )
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.broker.set_coc(True)
        
        results_run = cerebro.run()
        final_value = cerebro.broker.getvalue()
        return_rate = (final_value / initial_cash - 1) * 100
        
        strategy_instance = results_run[0]
        all_signals = getattr(strategy_instance, "all_signals", [])
        
        return {
            "stock_code": stock_code,
            "status": "success",
            "initial_cash": initial_cash,
            "final_value": final_value,
            "return_rate": return_rate,
            "profit": final_value - initial_cash,
            "signal_count": len(all_signals),
            "data_rows": len(df),
        }
    except Exception as e:
        return {
            "stock_code": stock_code,
            "status": "error",
            "reason": str(e),
        }


def batch_backtest(
    stock_codes=None,
    initial_cash=500000,
    commission=0.0002,
    start_date="2024-09-24",
    end_date="2026-02-12",
    strategy=DoubleLineStrategy,
    buy_strategies=None,
    sell_strategies=None,
    exclude_extreme=True,
    min_data_rows=100,
    max_workers=None,
    skip_keywords=None,
):
    stock_industry_dict = {}
    stock_name_dict = {}
    if os.path.exists("stocklist.csv"):
        try:
            stocklist_df = pd.read_csv("stocklist.csv")
            stock_industry_dict = dict(zip(stocklist_df["symbol"], stocklist_df["industry"]))
            stock_name_dict = dict(zip(stocklist_df["symbol"], stocklist_df["name"]))
        except Exception as e:
            print(f"读取 stocklist.csv 失败: {e}")
    
    if stock_codes is None:
        stock_codes = []
        for file in os.listdir("data"):
            if file.endswith(".csv"):
                stock_codes.append(file.replace(".csv", ""))
        stock_codes.sort()
    
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 4)
    
    print(f"\n开始批量回测，共 {len(stock_codes)} 只股票")
    print(f"回测日期范围: {start_date} 到 {end_date}")
    print(f"并发线程数: {max_workers}")
    if skip_keywords:
        print(f"跳过板块关键词: {skip_keywords}")
    print("=" * 100)
    
    skipped_stocks = []
    results = []
    print_lock = threading.Lock()
    
    skip_reasons = {
        "板块跳过": 0,
        "数据文件不存在": 0,
        "数据行数不足": 0,
        "其他错误": 0,
    }
    
    skip_details = {
        "板块跳过": [],
        "数据文件不存在": [],
        "数据行数不足": [],
        "其他错误": [],
    }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for stock_code in stock_codes:
            future = executor.submit(
                _run_single_backtest,
                stock_code=stock_code,
                initial_cash=initial_cash,
                commission=commission,
                start_date=start_date,
                end_date=end_date,
                strategy=strategy,
                buy_strategies=buy_strategies,
                sell_strategies=sell_strategies,
                min_data_rows=min_data_rows,
                stock_industry_dict=stock_industry_dict,
                skip_keywords=skip_keywords,
            )
            futures[future] = stock_code
        
        completed = 0
        for future in as_completed(futures):
            stock_code = futures[future]
            completed += 1
            try:
                result = future.result()
                if result["status"] == "success":
                    results.append(result)
                    with print_lock:
                        print(f"[{completed}/{len(stock_codes)}] {result['stock_code']}: 初始资金={initial_cash:.2f}, 最终资金={result['final_value']:.2f}, 收益率={result['return_rate']:.2f}%")
                else:
                    skipped_stocks.append({
                        "stock_code": result["stock_code"],
                        "reason": result["reason"],
                    })
                    
                    with print_lock:
                        print(f"[{completed}/{len(stock_codes)}] {result['stock_code']}: 跳过 - {result['reason']}")
                    
                    reason = result["reason"]
                    stock_name = stock_name_dict.get(result["stock_code"], "")
                    stock_info = f"{result['stock_code']}"
                    if stock_name:
                        stock_info += f"[{stock_name}]"
                    
                    if "板块包含关键词" in reason:
                        skip_reasons["板块跳过"] += 1
                        skip_details["板块跳过"].append(stock_info)
                    elif "数据文件不存在" in reason:
                        skip_reasons["数据文件不存在"] += 1
                        skip_details["数据文件不存在"].append(stock_info)
                    elif "数据行数不足" in reason:
                        skip_reasons["数据行数不足"] += 1
                        skip_details["数据行数不足"].append(stock_info)
                    else:
                        skip_reasons["其他错误"] += 1
                        skip_details["其他错误"].append(stock_info)
            except Exception as e:
                skipped_stocks.append({
                    "stock_code": stock_code,
                    "reason": f"异常: {str(e)}",
                })
                skip_reasons["其他错误"] += 1
                stock_name = stock_name_dict.get(stock_code, "")
                stock_info = f"{stock_code}"
                if stock_name:
                    stock_info += f"[{stock_name}]"
                skip_details["其他错误"].append(stock_info)
                with print_lock:
                    print(f"[{completed}/{len(stock_codes)}] {stock_code}: 错误 - {str(e)}")
    
    if not results:
        print("\n警告: 没有有效的回测结果")
        return {
            "results": [],
            "skipped_stocks": skipped_stocks,
            "statistics": None,
        }
    
    df_results = pd.DataFrame(results)
    
    if exclude_extreme and len(df_results) > 2:
        max_return = df_results["return_rate"].max()
        min_return = df_results["return_rate"].min()
        
        max_stock = df_results[df_results["return_rate"] == max_return]["stock_code"].values[0]
        min_stock = df_results[df_results["return_rate"] == min_return]["stock_code"].values[0]
        
        print(f"\n过滤极端值:")
        print(f"  最高收益率: {max_return:.2f}% ({max_stock})")
        print(f"  最低收益率: {min_return:.2f}% ({min_stock})")
        
        df_results = df_results[df_results["return_rate"] != max_return]
        df_results = df_results[df_results["return_rate"] != min_return]
        
        skipped_stocks.extend([{"stock_code": max_stock, "reason": f"最高收益率 ({max_return:.2f}%)"}])
        skipped_stocks.extend([{"stock_code": min_stock, "reason": f"最低收益率 ({min_return:.2f}%)"}])
    
    avg_profit_amount = df_results["profit"].mean()
    avg_return_rate = df_results["return_rate"].mean()
    median_return_rate = df_results["return_rate"].median()
    std_return_rate = df_results["return_rate"].std()
    q25_return_rate = df_results["return_rate"].quantile(0.25)
    q75_return_rate = df_results["return_rate"].quantile(0.75)
    max_return_rate_actual = df_results["return_rate"].max() if len(df_results) > 0 else 0
    min_return_rate_actual = df_results["return_rate"].min() if len(df_results) > 0 else 0
    
    profit_stocks = len(df_results[df_results["return_rate"] > 0])
    loss_stocks = len(df_results[df_results["return_rate"] < 0])
    win_rate = (profit_stocks / len(df_results)) * 100 if len(df_results) > 0 else 0
    
    avg_profit = df_results[df_results["return_rate"] > 0]["return_rate"].mean() if profit_stocks > 0 else 0
    avg_loss = df_results[df_results["return_rate"] < 0]["return_rate"].mean() if loss_stocks > 0 else 0
    
    statistics = {
        "total_stocks": len(stock_codes),
        "valid_stocks": len(results),
        "skipped_stocks": len(skipped_stocks),
        "skip_reasons": skip_reasons,
        "skip_details": skip_details,
        "avg_profit_amount": avg_profit_amount,
        "avg_return_rate": avg_return_rate,
        "median_return_rate": median_return_rate,
        "std_return_rate": std_return_rate,
        "q25_return_rate": q25_return_rate,
        "q75_return_rate": q75_return_rate,
        "max_return_rate": max_return_rate_actual,
        "min_return_rate": min_return_rate_actual,
        "profit_stocks": profit_stocks,
        "loss_stocks": loss_stocks,
        "win_rate": win_rate,
        "avg_profit": avg_profit,
        "avg_loss": avg_loss,
    }
    
    print("\n" + "=" * 100)
    print("批量回测统计结果")
    print("=" * 100)
    print(f"总股票数: {statistics['total_stocks']}")
    print(f"有效股票数: {statistics['valid_stocks']}")
    print(f"跳过股票数: {statistics['skipped_stocks']}")
    print(f"  - 板块跳过: {skip_reasons['板块跳过']}")
    if skip_details["板块跳过"]:
        print(f"    {', '.join(skip_details['板块跳过'][:20])}")
        if len(skip_details["板块跳过"]) > 20:
            print(f"    ... 还有 {len(skip_details['板块跳过']) - 20} 只")
    print(f"  - 数据文件不存在: {skip_reasons['数据文件不存在']}")
    if skip_details["数据文件不存在"]:
        print(f"    {', '.join(skip_details['数据文件不存在'][:20])}")
        if len(skip_details["数据文件不存在"]) > 20:
            print(f"    ... 还有 {len(skip_details['数据文件不存在']) - 20} 只")
    print(f"  - 数据行数不足: {skip_reasons['数据行数不足']}")
    if skip_details["数据行数不足"]:
        print(f"    {', '.join(skip_details['数据行数不足'][:20])}")
        if len(skip_details["数据行数不足"]) > 20:
            print(f"    ... 还有 {len(skip_details['数据行数不足']) - 20} 只")
    print(f"  - 其他错误: {skip_reasons['其他错误']}")
    if skip_details["其他错误"]:
        print(f"    {', '.join(skip_details['其他错误'][:20])}")
        if len(skip_details["其他错误"]) > 20:
            print(f"    ... 还有 {len(skip_details['其他错误']) - 20} 只")
    print(f"平均收益额: {statistics['avg_profit_amount']:.2f}")
    print(f"平均收益率: {statistics['avg_return_rate']:.2f}%")
    print(f"中位数收益率: {statistics['median_return_rate']:.2f}%")
    print(f"收益率标准差: {statistics['std_return_rate']:.2f}%")
    print(f"25%分位数收益率: {statistics['q25_return_rate']:.2f}%")
    print(f"75%分位数收益率: {statistics['q75_return_rate']:.2f}%")
    print(f"最大收益率: {statistics['max_return_rate']:.2f}%")
    print(f"最小收益率: {statistics['min_return_rate']:.2f}%")
    print(f"盈利股票数: {statistics['profit_stocks']}")
    print(f"亏损股票数: {statistics['loss_stocks']}")
    print(f"胜率: {statistics['win_rate']:.2f}%")
    print(f"平均盈利: {statistics['avg_profit']:.2f}%")
    print(f"平均亏损: {statistics['avg_loss']:.2f}%")
    print("=" * 100)
    
    return {
        "results": results,
        "skipped_stocks": skipped_stocks,
        "statistics": statistics,
    }


if __name__ == "__main__":
    import time
    stock_codes = None
    # stock_codes = ["000001", "000002", "600089", "600362"]
    initial_cash = 500000
    commission = 0.0002
    start_date = "2024-09-24"
    end_date = "2026-02-13"
    # buy_strategies = {"B1_with_ma60": B1WithMA60BuyStrategy}
    buy_strategies = {
        "B1": B1BuyStrategy,
    }
    
    sell_strategies = {
        "close_below_duokong": CloseBelowDuokongSellStrategy,
        "standard_top_windmill": StandardTopWindmillSellStrategy,
        "suspected_top_windmill": SuspectedTopWindmillSellStrategy,
    }
    
    max_workers = 12
    
    skip_keywords = ["地产"]
    
    start_time = time.time()
    
    batch_result = batch_backtest(
        stock_codes=stock_codes,
        initial_cash=initial_cash,
        commission=commission,
        start_date=start_date,
        end_date=end_date,
        strategy=DoubleLineStrategy,
        buy_strategies=buy_strategies,
        sell_strategies=sell_strategies,
        exclude_extreme=True,
        min_data_rows=100,
        max_workers=max_workers,
        skip_keywords=skip_keywords,
    )
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\n总耗时: {elapsed_time:.2f} 秒")
    
    if batch_result["results"]:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        results_df = pd.DataFrame(batch_result["results"])
        results_df.to_csv(f"batch_backtest_results_{timestamp}.csv", index=False, encoding="utf-8-sig")
        print(f"\n结果已保存到: batch_backtest_results_{timestamp}.csv")
        
        stats_df = pd.DataFrame([batch_result["statistics"]])
        stats_df.to_csv(f"batch_backtest_statistics_{timestamp}.csv", index=False, encoding="utf-8-sig")
        print(f"统计结果已保存到: batch_backtest_statistics_{timestamp}.csv")
