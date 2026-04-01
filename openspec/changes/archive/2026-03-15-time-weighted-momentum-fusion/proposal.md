## Why

当前回测框架主要针对单一信号触发的时点进行分析，缺乏处理多个信号叠加或连续触发时的融合逻辑。通过引入时间加权衰减（Time-Weighted Decay）和因子秩（Rank）转换，可以更科学地处理多信号共存的情况，捕捉更持久的动量效应。同时，现有的绘图功能需要增强，以支持分组超额收益的直观对比。

## What Changes

- **核心算法**: 实现时点动量融合逻辑。在 10 日窗口内对所有触发信号对应的时点因子进行 Rank 转换。
- **权重计算**: 引入基于半衰期 $H=10$ 的权重计算公式 $w = 2^{-n/H}$。
- **持仓策略**: 默认持有 20 个交易日，若中途出现新信号，则自动切换至新信号对应的持仓组合。
- **可视化增强**: 
  - 绘制多头、空头、多空（Long-Short）收益曲线。
  - **新需求**: 增加分组超额收益（Excess Return）的柱状图。
  - 继续保持非信号时间段的拼接展示方式。

## Capabilities

### New Capabilities
- `time-weighted-momentum-fusion`: 实现基于时间半衰权重的多信号因子融合算法及动态持仓逻辑。

### Modified Capabilities
- `sparse-signal-testing`: 增强 `SparseSignalTester` 的绘图能力，支持超额收益柱状图及长空收益曲线展示。

## Impact

- `core/SparseSignalTester.py`: 增加处理融合因子的特化回测逻辑或扩展现有方法。
- `filters/signal_filters.py`: 可能需要提供批量信号处理接口。
- 新建测试脚本（如 `run_time_weighted_fusion_test.py`）整合现有三个策略的信号。
