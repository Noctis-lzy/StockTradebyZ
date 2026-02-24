import backtrader as bt
import pandas as pd
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from back_test_lu import run_backtest, StockPandasData
from backtrader4Lu.strategy.double_line_b1_strategy import DoubleLineStrategy
from backtrader4Lu.strategy.buy import B1BuyStrategy
from backtrader4Lu.strategy.sell import (
    CloseBelowDuokongSellStrategy,
    StandardTopWindmillSellStrategy,
    SuspectedTopWindmillSellStrategy,
)

def single_stock_test():
    stock_code = "300863"
    start_date = "2025-02-13"
    end_date = "2026-02-13"
    execute_start_date = "2026-02-13"
    execute_end_date = "2026-02-13"
    buy_strategies = {"B1": B1BuyStrategy}
    sell_strategies = {
        "close_below_duokong": CloseBelowDuokongSellStrategy,
        "standard_top_windmill": StandardTopWindmillSellStrategy,
        "suspected_top_windmill": SuspectedTopWindmillSellStrategy,
    }
    result = run_backtest(
        stock_code=stock_code,
        initial_cash=500000,
        commission=0.0002,
        start_date=start_date,
        end_date=end_date,
        execute_start_date=execute_start_date,
        execute_end_date=execute_end_date,
        strategy=DoubleLineStrategy,
        buy_strategies=buy_strategies,
        sell_strategies=sell_strategies,
        plot=False,
    )
    # todo 检查是出现过买入信号


    print("\n===============================================================================================")
    print(f"股票代码: {stock_code}")
    print(f"检查日期范围: {start_date} 到 {end_date}")
    
    all_signals = result.get('all_signals', [])
    
    if all_signals:
        print(f"买入信号: 是")
        print(f"共发现 {len(all_signals)} 个买入点")        
        for idx, signal_info in enumerate(all_signals, 1):
            print(f"买入点 #{idx}")
            print(f"  日期: {signal_info['date']}")
            # print(f"  买入价格: {signal_info['price']:.2f}")
            # print(f"  KDJ_J: {signal_info['kdj_j']:.2f}")
            # print(f"  多空线: {signal_info['duokong_line']:.2f}")
            # print(f"  MA60斜率: {signal_info['ma60_slope']:.4f}")
            # print(f"  买入数量: {signal_info['size']}")
            
            # conditions = signal_info.get('conditions', {})
            # print(f"  买入条件:")
            # print(f"    KDJ_J <= 14: {conditions.get('kdj_j_le_13', False)}")
            # print(f"    收盘价 > 多空线: {conditions.get('close_above_duokong', False)}")
            # print(f"    历史收盘价 > 趋势线: {conditions.get('close_above_trend_history', False)}")
            # print(f"    成交量MA5斜率 < 0: {conditions.get('vol_ma5_slope_lt_0', False)}")
            # print(f"    MA60斜率 > 0: {conditions.get('ma60_slope_gt_0', False)}")
            # print(f"    趋势线 > 多空线: {conditions.get('trend_above_duokong', False)}")
    else:
        print(f"买入信号: 否")
    print("===============================================================================================")

def process_stock(stock_code, start_date, end_date, execute_start_date, execute_end_date, 
                  buy_strategies, sell_strategies, result_list, lock):
    result = run_backtest(
        stock_code=stock_code,
        initial_cash=500000,
        commission=0.0002,
        start_date=start_date,
        end_date=end_date,
        execute_start_date=execute_start_date,
        execute_end_date=execute_end_date,
        strategy=DoubleLineStrategy,
        buy_strategies=buy_strategies,
        sell_strategies=sell_strategies,
        plot=False,
    )
    
    if result is None:
        return
    
    all_signals = result.get('all_signals', [])
    
    execute_start_dt = pd.to_datetime(execute_start_date).date()
    execute_end_dt = pd.to_datetime(execute_end_date).date()
    
    for signal_info in all_signals:
        signal_date = signal_info.get('date')
        if signal_date and isinstance(signal_date, pd.Timestamp):
            signal_date = signal_date.date()
        
        if signal_date and execute_start_dt <= signal_date <= execute_end_dt:
            with lock:
                result_list.append({
                    "stock_code": stock_code,
                    "buy_point": {
                        "strategy_type": signal_info.get('type', 'buy'),
                        "strategy": signal_info.get('strategy_name', 'B1'),
                        "date": str(signal_date)
                    }
                })

def multi_stock_test():
    start_date = "2025-02-13"
    end_date = "2026-02-13"
    execute_start_date = "2026-02-13"
    execute_end_date = "2026-02-13"
    buy_strategies = {"B1": B1BuyStrategy}
    sell_strategies = {
        "close_below_duokong": CloseBelowDuokongSellStrategy,
        "standard_top_windmill": StandardTopWindmillSellStrategy,
        "suspected_top_windmill": SuspectedTopWindmillSellStrategy,
    }
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        data_dir = "../data"
    
    if not os.path.exists(data_dir):
        print(f"错误: 找不到数据目录")
        return
    
    stock_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    stock_codes = [f.replace('.csv', '') for f in stock_files]
    
    result_list = []
    lock = Lock()
    
    total_stocks = len(stock_codes)
    completed_count = 0
    
    print(f"开始处理 {total_stocks} 只股票...")
    print("=" * 90)
    
    max_workers = min(8, total_stocks)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                process_stock, 
                stock_code, 
                start_date, 
                end_date, 
                execute_start_date, 
                execute_end_date, 
                buy_strategies, 
                sell_strategies, 
                result_list, 
                lock
            ): stock_code for stock_code in stock_codes
        }
        
        for future in as_completed(futures):
            stock_code = futures[future]
            try:
                future.result()
                completed_count += 1
                progress = (completed_count / total_stocks) * 100
                print(f"\r进度: {completed_count}/{total_stocks} ({progress:.1f}%) - 已完成: {stock_code}", end='', flush=True)
            except Exception as e:
                completed_count += 1
                progress = (completed_count / total_stocks) * 100
                print(f"\r进度: {completed_count}/{total_stocks} ({progress:.1f}%) - {stock_code} 处理失败: {e}", end='', flush=True)
    
    print(f"\n{'=' * 90}")
    print(f"处理完成! 共发现 {len(result_list)} 个买入点")
    
    import json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"buy_points_result_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_list, f, ensure_ascii=False, indent=2)
    print(f"结果已保存到: {output_file}")


if __name__ == "__main__":
    # single_stock_test()
    multi_stock_test()

