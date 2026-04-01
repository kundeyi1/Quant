## Why

计算并提供一个新的技术指标：动量因子。该因子旨在通过比较当日收益率与过去20个交易日的平均收益率，捕捉个股超额收益的动能特征，辅助量化策略进行选股或择时。

## What Changes

- 在 `factors/technical_factors.py` 中新增 `calculate_momentum_factor` 函数。
- 动量计算公式：`当日涨跌幅 - 前20日日均涨跌幅`。
- 支持处理数据缺失和边界情况。

## Capabilities

### New Capabilities
- `momentum-factor`: 计算基于当日与历史均值差值的动量因子。

### Modified Capabilities
<!-- 无现有 Spec 受影响 -->

## Impact

- `factors/technical_factors.py`: 代码新增。
- 依赖项：需要 `pandas` 或 `numpy` 进行序列计算（假设项目已有）。
