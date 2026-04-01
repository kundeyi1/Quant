## 1. Core Logic Implementation

- [x] 1.1 在 `filters/signal_filters.py` 中新增 `calculate_triangle_breakout_filter` 静态方法。
- [x] 1.2 实现 T-5 到 T-1 的波动率压抑逻辑（绝对值 < 1%）。
- [x] 1.3 实现基于滚动 5 日最高/最低价的通道宽度计算及其收缩判定（T-1 宽度 < T-2 宽度）。
- [x] 1.4 实现 T 日涨幅突破判定（涨幅 > 1%）。
- [x] 1.5 编写代码静态检查，确保无语法错误。

## 2. Test Execution & Reporting

- [x] 2.1 创建 `run_triangle_breakout_test.py` 脚本，引用 `DataProvider` 加载数据。
- [x] 2.2 调用新实现的 `triangle_breakout_filter` 生成信号序列。
- [x] 2.3 使用 `SparseSignalTester` 类初始化回测，设置 T+20 窗口和 5 组分组。
- [x] 2.4 执行回测并生成可视化图表（信号触发图、年化频率图、分组收益图）。
- [x] 2.5 导出触发日志 `signal_trigger_dates.csv`。

## 3. Verification & Cleanup

- [x] 3.1 验证 2015-2025 年间是否有合理的触发点。
- [x] 3.2 确认输出图表保存在指定目录 `results/gx_pit_momentum/triangle_breakout/`。
- [ ] 3.3 提交并归档 OpenSpec 变更。
