## Why

原有的 `core.SparseSignalTester` 肩负了包含具体预测数值（如回归收益预测率、树模型得分等）特征的稀疏信号测试，同时还要兼容离散的 0/1 择时信号计算。两者的绘图需求、评估指标（胜负率、分布）以及组合分组逻辑差异很大。为了保证测试类的强内聚与专用性，需要分离这两套逻辑：让 `SparseSignalTester` 专精于带有横向截面或数值分布的稀疏信号评估，同时新增独立的 `core.TimingTester` 专门用于检验纯 0/1 择时信号的时点有效性，并按要求输出胜率分布与净值回撤等图形。

## What Changes

- 修改 `core/SparseSignalTester.py`，移除或剥离其中专门针对 0/1 分布绘图和择时收益的相关业务代码，使其专注于数值型信号（如具有 quantile、不同 n_groups）的分组评价。
- 新增 `core/TimingTester.py`，提供专用的 `TimingTester` 类，支持输入 0/1 序列信号、底层价格/净值序列，输出包含万得全A（或 Benchmark）归一化净值以及信号回撤区域阴影展示的双轴对比图。
- 保证测试流程的闭环：普通因子数值检验保存至 `results/factor`，包含数值预测的稀疏信号检验保存至 `results/sparse_signal`，而基于0/1离散点的抛物线绘图等定性择时检验结果图表保存至 `results/timing`。

## Capabilities

### New Capabilities
- `discrete-timing-evaluation`: 定义纯 0/1 择时信号评价标准与专属的图形输出范式（双轴折线+阴影绘图）。

### Modified Capabilities
- `sparse-signal-testing`: 剥离 0/1 评价逻辑，修正并明确其处理带数值/截面分布稀疏信号的核心业务。

## Impact

- `core/SparseSignalTester.py`: 精简原有方法，剥离绘图与纯择时逻辑。
- `core/TimingTester.py`: 全新文件。
- `core/__init__.py`: 导出新的 `TimingTester` 类。
- `results/`: 新增规范的输出落盘行为，分别指向 `factor_analysis` 和 `timing_analysis` 目录。
