## 1. 核心融合逻辑实现

- [x] 1.1 在 `core/NumericalOperators.py` 或 `core/DataManager.py` 中增加 Rank 转换工具函数。
- [x] 1.2 在 `core/SparseSignalTester.py` 中重构信号处理部分，支持 10 日滑动窗口内的多信号融合。
- [x] 1.3 实现半衰权重计算公式 $w = 2^{-n/H}$ ($H=10$) 及其应用逻辑。

## 2. 持仓与回测框架增强

- [x] 2.1 修改 `SparseSignalTester.run_backtest` 方法，支持动态持仓切换逻辑（20日内新信号触发则切换）。
- [x] 2.2 扩展 `SparseSignalTester` 的结果输出，包含多头、空头和多空（Long-Short）收益。

## 3. 可视化功能升级

- [x] 3.1 在 `core/SparseSignalTester.py` 的绘图方法中集成多空对比曲线展示。
- [x] 3.2 增加 `plot_excess_return_bar` 方法，用于绘制各分组相对于均值或基准的超额收益柱状图。
- [x] 3.3 优化时间轴拼接逻辑，确保多信号融合后的曲线绘图也支持“无信号段拼接”展示。

## 4. 验证与集成测试

- [x] 4.1 编写 `run_time_weighted_fusion_test.py` 脚本，整合 `triangle breakout`、`rebound` 和 `rotation` 三种信号。
- [x] 4.2 运行合并测试脚本并确认可视化的多空曲线、拼接效果和超额收益柱状图正确产出。
- [x] 4.3 验证输出结果的统计指标（IC/IR 等）是否符合预期。

## 5. 异构信号因子修正 (追加)

- [x] 5.1 修改 `SparseSignalTester` 以支持多种信号的不同因子输入 (通过 `signal_dict` 或 `factor_dict`)。
- [x] 5.2 在 `run_time_weighted_fusion_test.py` 中分别计算各信号特有的因子（如 Rebound 超额动量）。
- [x] 5.3 重新运行测试并验证可视化结果。
