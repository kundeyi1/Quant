## 1. 核心逻辑实现 (Core Implementation)

- [x] 1.1 在 `filters/signal_filters.py` 中引入 `RiskFactors`。
- [x] 1.2 实现 `SignalFilters.calculate_market_turning_point` 方法框架。
- [x] 1.3 编写行业 250 日（52 周）新高数量的计算逻辑。
- [x] 1.4 计算每日新高数量的差值（T 日 vs T-1 日）。
- [x] 1.5 集成指数 ATR60 计算及跌幅突破判断。
- [x] 1.6 结合两个条件生成 0-1 信号 Series。

## 2. 验证与测试 (Validation & Testing)

- [x] 2.1 创建 `test_market_turning_point.py` 测试脚本。
- [x] 2.2 使用中证全指（000985.CSI）和中信一级行业数据进行实测。
- [x] 2.3 验证并在终端输出触发日期及其对应的指标值（新高数减少值、指数跌幅、ATR）。
- [x] 2.4 可视化信号点，确保逻辑符合需求描述。

## 3. 结果产出 (Results)

- [x] 3.1 导出触发日志至 `results/market_turning_point/` 目录。
