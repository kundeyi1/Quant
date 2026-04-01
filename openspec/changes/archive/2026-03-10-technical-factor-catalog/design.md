## Context

[factors/technical_factors.py](factors/technical_factors.py) 中的因子目前统一组织在 `TrendFactors` 类下，大部分方法通过 `staticmethod` 暴露。设计目标是确保每一个因子方法都是自包含的、逻辑清晰的，并且容易被 `FactorTester` 调用。

## Goals / Non-Goals

**Goals:**
- 实现一致的静态方法接口 `calculate_XXX(data, **kwargs)`。
- 确保所有的 `data` 参数为包含 OHLC 的 DataFrame。
- 使用 `talib` 进行基础波动率和均线计算。

**Non-Goals:**
- 不涉及除技术面以外的其他类型因子的规范。
- 不提供因子的动态组合框架。

## Decisions

- **实现机制**: 利用 Python 的装饰器或特殊的函数命名约定 (`calculate_`) 方便通过元编程管理所有因子。
- **因子返回格式**: 为了方便合并 (concat)，所有因子函数均 SHALL 返回具有相同 index 的 DataFrame。
- **动量算法**: 明确不采用收盘价差值，而是使用 `pct_change` 后的差值作为动量量化标准。

## Risks / Trade-offs

- **算子重复**: 有些复杂的因子计算内部会包含简单的算子。
  - **Mitigation**: 尽量在因子内部直接调用现有的 `NumericalOperators` 模块中的函数，以减少冗余逻辑。
- **处理窗口**: 各因子的默认回看周期 (Window) 存在差异。
  - **Mitigation**: 建议通过函数参数显式控制窗口期，而非硬编码。
