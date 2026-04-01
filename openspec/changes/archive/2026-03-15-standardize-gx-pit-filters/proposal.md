## Why

[signal_filters.py](filters/signal_filters.py) 中的 `calculate_gx_pit` 系列方法目前存在实现逻辑不统一、数据读取方式多样（如 `calculate_gx_pit_breakout_filter` 对宽表和 OHLC 的处理逻辑与 `calculate_gx_pit_rebound_filter` 不同）以及内部辅助函数（如 ATR）调用管理不规范的问题。这些不一致性可能导致策略在不同资产类别上的表现出现非预期偏差，并增加了维护成本。

## What Changes

- **统一计算逻辑**：对 `calculate_gx_pit_rebound_filter`、`calculate_gx_pit_breakout_filter` 和 `calculate_gx_pit_rotation_filter` 进行一致性检查，确保它们遵循相同的底层计算范式，特别是在处理数据输入和基础因子引用上。
- **重构 ATR 逻辑**：取消 `atr_volatility_filter` 作为独立公共函数的地位，将其逻辑整合或转为内部辅助逻辑，不再推荐作为顶层 Filter 直接调用，以减少 API 冗余。
- **标准化数据输入处理**：建立统一的内部数据解析机制，确保所有 GX PIT 过滤器能够以一致的方式识别和处理 OHLC DataFrame 或行业价格宽表。

## Capabilities

### New Capabilities
- `gx-pit-standard`: 制定并实现 GX PIT 系列过滤器的统一计算标准，包括数据适配器和通用的动态阈值调整逻辑。

### Modified Capabilities
- (暂无)

## Impact

- 核心受影响文件：[filters/signal_filters.py](filters/signal_filters.py)。
- 涉及方法：`calculate_gx_pit_rebound_filter`, `calculate_gx_pit_breakout_filter`, `calculate_gx_pit_rotation_filter` 以及 `atr_volatility_filter`。
- 依赖项：引用自 `factors.technical_factors` 的 `RiskFactors.calculate_gx_atr_factor`。
