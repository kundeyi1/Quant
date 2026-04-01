## Why

当前回测框架中的信号过滤逻辑（`filters`）仅作为简单的二元掩码（Mask），缺乏系统性的“市场择时”（Market Timing）评估维度。华泰证券的技术打分体系（2025-12-28）提供了一种更全面的市场状态评估方法。将原本离散的过滤器与连续的打分逻辑整合进统一的择时系统，能更好地评估市场可交易性。

## What Changes

- **代码重构**：将 `filters/` 文件夹整体更名为 `timing/`，并将所有择时相关逻辑整合至 `timing/market_timing.py` 之中。
- **命名规范**：统一所有择时函数为平铺结构，取消类封装和不必要的私有化。原子化、普适的数学择时方法直接以逻辑名命名；带有研究机构特定定义的方案（如华泰均线系统、华泰量价体系）保留 `ht_` 前缀，并使用具有语义的名称而非参数命名；原有特定逻辑使用 `gx_pit_` 前缀。
- **功能新增**：实现华泰证券技术打分体系的原子函数（RSRS、均线趋势、动能、成交量能等）。
- **逻辑转换**：原有择时指标（gx_pit系列）继续输出 0/1 离散信号；华泰指标暂时按研报实现连续得分/打分输出，暂不强制离散化。

## Capabilities

### New Capabilities
- `ht-technical-timing`: 实现华泰证券（2025-12-28）研报中的技术择时打分体系，包含 RSRS、趋势、波动、成交量能等维度。
- `timing-integration-framework`: 建立统一的择时函数调用规范，支持将连续指标阈值化为 0/1 信号。

### Modified Capabilities
- `rebound-signal-filter`: 从 `filters` 迁移至 `timing`，重新实现为平铺函数 `gx_pit_rebound`。
- `triangle-breakout-filter`: 从 `filters` 迁移至 `timing`，重新实现为平铺函数 `gx_pit_breakout`。
- `rotation_filter`: 从 `filters` 迁移至 `timing`，重新实现为平铺函数 `gx_pit_rotation`。

## Impact

- **核心库**：`filters/` 目录将被移除，`timing/` 目录及其下的 `market_timing.py` 成为唯一的择时逻辑中心。
- **策略脚本**：`run_gx_pit_...` 等所有依赖原有过滤器的脚本需要更新 `import` 路径及调用方式。
- **依赖关系**：择时函数将更加依赖 `core/NumericalOperators.py` 进行复杂数值计算（如 RSRS 的滚动回归）。
