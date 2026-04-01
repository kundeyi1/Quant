## Context

[core/NumericalOperators.py](core/NumericalOperators.py) 目前包含一系列直接作用于 Pandas Series 的函数和基于 Numpy 的 `FactorOperators` 类。设计目标是将底层计算逻辑与策略实现解耦，并确保在多股票数据集（DataFrame）和单序列数据集（Series）上的行为一致。

## Goals / Non-Goals

**Goals:**
- 将 `ts_delay` 等时序算子设计为对 Pandas 友好，保留索引。
- `FactorOperators` 处理 numpy 数组以追求性能。
- `min_periods=1` 被选为默认行为，以防止因子序列在回测初段出现大面积 NaN。

**Non-Goals:**
- 不对 pandas 或 numpy 进行封装改动。
- 不引入第三方非标准计算库（除了已有的 `talib`）。

## Decisions

- **实现机制**: 利用 Pandas 的 `.rolling()` 和 `.shift()` 作为主要实现算子。
- **缺失值容忍**: `min_periods` 统一设为 1（或由方法参数显式定义）。
- **线性回归实现**: 在 `FactorOperators` 内部使用 `np.linalg.lstsq`（OLS）而非法定。

## Risks / Trade-offs

- **性能瓶颈**: `rolling().apply()` 可能较慢。
  - **Mitigation**: 后续可考虑针对高频场景使用 `numba` 加速。
- **数据对齐**: `cs_rank` 假设输入是一组截面数据。
  - **Mitigation**: 文档中 SHALL 明确调用时机为截面计算。
