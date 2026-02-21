# StandardTopWindmillSellStrategy 单元测试

本目录包含标准顶部大风车卖出策略的单元测试。

## 测试文件

### test_standard_top_windmill.py
完整的单元测试套件，包含以下测试用例：

1. **test_all_conditions_met** - 测试所有条件都满足时触发卖出信号
2. **test_not_bearish_candle** - 测试不是阴线时不触发卖出信号
3. **test_upper_shadow_too_small** - 测试上影线不足1.5%时不触发卖出信号
4. **test_lower_shadow_too_small** - 测试下影线不足0.5%时不触发卖出信号
5. **test_volume_not_enough** - 测试成交量不足MA10的120%时不触发卖出信号
6. **test_volume_not_max_3days** - 测试成交量不是最近三天最高时不触发卖出信号
7. **test_kdj_j_not_gt_70** - 测试KDJ J不大于70时不触发卖出信号
8. **test_volume_lt_ma5** - 测试成交量小于MA5时不触发卖出信号
9. **test_signal_info_details** - 测试信号信息的详细内容

### test_simple.py
简单的测试脚本，用于快速验证策略逻辑。

## 运行测试

### 运行完整测试套件
```bash
cd /Users/noctis/Documents/code/stock/StockTradebyZ/backtrader4Lu
python -m unittest strategy.sell.test_standard_top_windmill
```

### 运行简单测试
```bash
cd /Users/noctis/Documents/code/stock/StockTradebyZ/backtrader4Lu
python strategy.sell.test_simple.py
```

## 策略条件说明

标准顶部大风车卖出策略需要满足以下所有条件：

1. **阴线** - 收盘价 < 开盘价
2. **上影线 >= 1.5%** - (最高价 - 收盘价) / 收盘价 >= 0.015
3. **下影线 >= 0.5%** - (收盘价 - 最低价) / 收盘价 >= 0.005
4. **成交量 >= MA10的120%** - 今日成交量 >= 1.2 * MA10
5. **成交量是最近三天最高** - 今日成交量 == max(最近三天成交量)
6. **成交量 >= MA5** - 今日成交量 >= MA5
7. **KDJ J > 70** - KDJ指标J值大于70

## 测试数据示例

### 触发卖出信号的数据
- KDJ J: 70.5
- 收盘价: 100.0
- 开盘价: 102.0 (阴线)
- 最高价: 104.0 (上影线4%)
- 最低价: 99.0 (下影线1%)
- 今日成交量: 12000.0
- MA10: 10000.0 (成交量120%)
- 最近三天成交量: [12000.0, 10000.0, 11000.0]
- MA5: 11500.0
- 持仓数量: 1000

### 不触发卖出信号的数据示例
- 不是阴线：收盘价 102.0，开盘价 100.0
- 上影线不足：收盘价 100.0，最高价 101.0 (上影线1%)
- 下影线不足：收盘价 100.0，最低价 99.6 (下影线0.4%)
- 成交量不足：今日成交量 11000.0，MA10 10000.0 (成交量110%)
- 成交量不是最高：今日成交量 12000.0，最近三天 [12000.0, 13000.0, 11000.0]
- KDJ J不足：KDJ J 69.0
- 成交量小于MA5：今日成交量 12000.0，MA5 12500.0

## 扩展测试

如需添加新的测试用例，请遵循以下模式：

```python
def test_your_test_case(self):
    """
    测试描述
    """
    # 设置mock数据
    self.mock_strategy.kdj.J.__getitem__ = Mock(return_value=value)
    # ... 设置其他数据

    # 创建策略实例并测试
    strategy = StandardTopWindmillSellStrategy(self.mock_strategy)
    is_signal, size, signal_info = strategy.check_signal()

    # 断言结果
    self.assertTrue(is_signal, "应该触发信号")
    # ... 其他断言
```

## 注意事项

1. 使用Mock对象模拟策略依赖，避免依赖外部数据
2. 每个测试用例应该独立，不依赖其他测试
3. 测试边界条件，如刚好满足/不满足阈值的情况
4. 验证返回的signal_info包含所有必要字段
