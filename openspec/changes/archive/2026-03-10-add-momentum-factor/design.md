## Context

目前 `factors/technical_factors.py` 中实现了多种趋势和技术因子。本项目需要引入一个衡量“动量差值”的新指标，其逻辑简单但需要保证在不同数据情况下的稳定性。

## Goals / Non-Goals

**Goals:**
- 在 `TrendFactors` 类中实现 `calculate_momentum_factor` 静态方法。
- 使用 `pandas` 的 `pct_change()` 和 `rolling(window=20).mean()` 进行高效向量化计算。
- 方法返回包含结果的 `pd.DataFrame`，索引与输入一致。

**Non-Goals:**
- 不涉及数据库层面的改动（假设调用者负责数据加载）。
- 不对除动量因子外的现有因子进行逻辑重构。

## Decisions

- **计算公式选择**: 使用 `close.pct_change()` 计算日收益率，再减去其 20 日均值。
- **缺失值处理**: 由于 `rolling` 的特性，前 20 条数据自然会是 NaN，这符合量化因子的通用习惯。
- **性能**: 采用 Pandas 原生算子以支持整个股票序列的快速批处理。

## Risks / Trade-offs

- **数据完整性**: 若输入序列中间存在空洞，`pct_change` 可能会产生偏差。
  - **Mitigation**: 假设输入数据已经过预处理（如复权和插值）。
- **计算窗口**: 固定的 20 日窗口可能在极短序列上报错。
  - **Mitigation**: 在方法内部不强制截断，允许返回带 NaN 的序列。
