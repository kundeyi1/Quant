## 1. 核心算子逻辑实现

- [x] 1.1 在 [core/NumericalOperators.py](core/NumericalOperators.py) 中验证 `ts_delay` 和 `ts_delta` 的 Pandas 兼容性
- [x] 1.2 确认 `ts_sum`, `ts_min`, `ts_max` 使用 `min_periods=1` 以减少回测初期数据损失
- [x] 1.3 验证 `cs_rank` 函数采用的排名方法为 `method='min'`（标准百分比排名）

## 2. 线性回归算子实现

- [x] 2.1 实现基于 Numpy 的滚动斜率计算 `ts_slope_array`
- [x] 2.2 实现基于 Numpy 的滚动回归残差计算 `ts_regression_resi_array`
- [x] 2.3 验证 `FactorOperators` 类返回值的形状和索引一致性

## 3. 文档化与 OpenSpec 流程

- [x] 3.1 完成 `standardize-numerical-operators` 的所有任务列表
- [x] 3.2 运行 `openspec archive` 将算子规范归档至主 Spec

