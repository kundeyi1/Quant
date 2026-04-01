## Why

当前 `SparseSignalTester.py` 仅提供了基于分组回测的收益统计（均值、胜率、IC 等），缺乏对信号择时（Timing）效果的直接验证。通过对比“信号触发后的收益分布”与“全样本收益分布”，可以量化信号在挑选“特殊时点”上的有效性，而不仅仅是标的间的相对强弱。

## What Changes

- 为 `SparseSignalTester.py` 增加独立的公有方法 `run_timing_analysis`，用于执行择时有效性检验。
- 择时分析将作为 `run_backtest` 之后的**可选独立步骤**，由用户手动调用。
- 使用 `D:/DATA/INDEX/STOCK/000985.CSI.xlsx` (中证全指) 作为背景基准数据集，计算其全样本收益分布（All-sample returns）。
- 计算所有信号触发点收益在 `000985.CSI` 背景分布中的 **Quantile Rank**。
- 输出 $T$ 检验结果，量化信号触发点收益与背景分布的显著性差异。
- 编写一个新的、参考 `run_time_weighted_fusion_test.py` 结构的独立检验脚本 `test_timing_effectiveness_000985.py`。
- 提供可视化的分布对比图（直方图/KDE），标出信号收益在基准分布中的位置。

## Capabilities

### New Capabilities
- `timing-effectiveness-test`: 提供独立的信号择时效果分析能力。支持以 `000985.CSI` 等指数作为基座分布，计算信号触发点的分位数排名和显著性。

### Modified Capabilities
- `sparse-signal-testing`: 扩展 `SparseSignalTester`，支持传入外部基准序列进行择时背景建模。

## Impact

- `core/SparseSignalTester.py`: 增加测试逻辑、绘图逻辑及性能指标计算。
- 结果输出：在 `results/` 目录下增加择时测试相关的图表和 CSV 文件。
