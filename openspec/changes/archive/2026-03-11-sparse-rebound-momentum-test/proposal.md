## Why

在大跌行情后的反弹时点，市场往往存在显著的风格切换或行业轮动。传统的因子检验工具（如 `FactorTester`）通常基于全时段的连续截面数据进行回测，无法直接处理由“反弹掩码（Rebound Mask）”生成的稀疏触发信号。

本变更旨在建立一套标准的“稀疏信号测试逻辑”，专门用于验证在中证 500 等指数触发大跌反弹信号时，中信一级行业的动量因子表现，从而捕捉超跌反弹中的强势行业。

## What Changes

- **核心库扩展**: 在 `core/` 目录下新建 `SparseSignalTester.py`，实现非连续时间序列的截面回测逻辑。
- **因子接入**: 接入 `MomentumFactors.calculate_gx_momentum_factor` 作为核心检验指标。
- **数据适配**: 开发脚本支持读取中证 500 指数（Excel 格式）作为信号源，并自适应读取中信一级行业指数宽表（`D:\DATA\INDEX\ZX\ZX_YJHY.csv`）。
- **结果统计与可视化**: 
    - 计算信号触发后 T+1 至 T+20 的行业累积收益。
    - 针对信号触发源进行时序可视化，在信号位绘制竖虚线。
    - 针对动量因子检验结果，绘制分组持有期平均收益率直方图（参考 `FactorTester` 风格）。

## Capabilities

### New Capabilities
- `sparse-signal-testing`: 提供一套标准的 API 和流程，用于测试不连续（稀疏）事件触发后的因子表现及分组收益统计。

### Modified Capabilities
- 无

## Impact

- **core/SparseSignalTester.py** (New): 核心回测逻辑实现类。
- **run_sparse_momentum_test.py** (New): 入口运行脚本。
- **core/DataManager.py**: 可能需要微调以支持跨资产（指数 vs 行业）的数据对齐和缓存逻辑。
