## Why

由于量化模型对底层计算算子的实现细节（如窗口期处理、空值逻辑）非常敏感，项目需要一套统一的数值算子规范（Numerical Operators Spec）。这将确保在跨模块计算或未来系统迁移时，算法逻辑的一致性和可验证性。

## What Changes

- 在 `openspec/specs/` 下建立 `numerical-operators` 目录。
- 详细规范化 [core/NumericalOperators.py](core/NumericalOperators.py) 中的常用算子逻辑。
- 明确时间序列（TS）和截面（CS）算子的行为边界。

## Capabilities

### New Capabilities
- `numerical-operators`: 定义核心数值计算函数（ts_delay, ts_delta, ts_sum, cs_rank 等）的行为标准。

## Impact

- 所有的因子实现类（如 `TrendFactors`）都将受此规范约束。
- 涉及 [core/NumericalOperators.py](core/NumericalOperators.py) 的维护和后续扩展。
