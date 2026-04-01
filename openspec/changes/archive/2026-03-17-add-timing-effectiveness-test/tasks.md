## 1. 核心计算逻辑实现

- [ ] 1.1 在 `SparseSignalTester` 中增加 `run_timing_analysis` 公有方法，内部包含全样本（如 `000985.CSI`）的 $T+period$ 滚动收益计算。
- [ ] 1.2 实现 **Quantile Rank** 计算：将信号点的平均收益映射到 `000985.CSI` 的全样本滚动收益分布中。
- [ ] 1.3 实现 $T$ 检验，判断信号触发后的平均收益是否显著优于 `000985.CSI` 的背景平均水平。

## 2. 可视化与报告输出

- [ ] 2.1 在 `SparseSignalTester` 中集成 `plot_timing_distribution` 绘图方法，展示信号分布在基准背景中的位置。
- [ ] 2.2 择时分析报告将包含：信号点数量、平均收益、Quantile Rank、P-Value。

## 3. 验证与示例编写

- [ ] 3.1 编写新的独立检验脚本 `test_timing_effectiveness_000985.py`。
- [ ] 3.2 脚本结构参考 `run_time_weighted_fusion_test.py`：加载 `000985.CSI.xlsx` 数据，构造因子后调用 `run_timing_analysis`。
- [ ] 3.3 验证分析逻辑能正确识别出信号触发后的统计异常。
