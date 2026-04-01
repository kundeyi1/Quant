## Why

由于项目中技术因子的实现散落在 `factors/technical_factors.py` 中，需要一套统一的因子目录（Factor Catalog）来规范化这些因子的算法逻辑、输入要求和预期行为。这将便于后续批量测试和策略调用。

## What Changes

- 在 `openspec/specs/` 下建立 `technical-factors` 目录。
- 整合现有的趋势因子（EMA、MA 排列、对称性因子、动量因子等）到统一的 Spec。

## Capabilities

### New Capabilities
- `technical-factors`: 包含所有现有技术因子的标准算法定义。

## Impact

- [factors/technical_factors.py](factors/technical_factors.py) 中的代码实现必须符合本规范。
- 所有的因子回测必须引用本规范中定义的逻辑。
