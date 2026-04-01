## 1. 核心计算逻辑实现 (Core Calculation)

- [ ] 1.1 在 `SparseSignalTester` 中新增 `_calculate_continuous_strategy_returns` 方法，支持信号覆盖（Signal Overlap）逻辑。
- [ ] 1.2 实现日度收益率填充逻辑（Gap Filling），支持空白期置 0。
- [ ] 1.3 实现多空对冲（Long-Short）收益率计算。

## 2. 接口与可视化增强 (Interface & Plotting)

- [ ] 2.1 修改 `plot_equity_curve` 方法，添加 `mode` 参数：`discrete`（默认）、`continuous_gap_fill`、`continuous_real_timeline`。
- [ ] 2.2 实现 `continuous_real_timeline` 绘图逻辑，仅保留有信号周期的连续拼接。
- [ ] 2.3 在 `plot_group_returns` 中调用新的净值曲线生成方法。

## 3. 验证与回归测试 (Validation)

- [ ] 3.1 运行 `run_gx_pit_rebound_test.py` 验证不同 `mode` 下的净值曲线产出。
- [ ] 3.2 检查日志输出与 CSV 结果是否与图形对齐。
- [ ] 3.3 确认旧的离散累乘结果不受影响。
