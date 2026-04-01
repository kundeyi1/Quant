# Delta Spec: save-sparse-group-results (Schema: spec-driven)

### Requirement: save-sparse-group-results

#### Description
在稀疏信号回测过程中，系统必须保存并导出每个触发日期（Trigger Date）下所有资产（行业）的分组分配明细及业绩详情，以支持离线归因。

#### Requirement: 1. `self._group_assignment_log` 内部存储
- 在 `SparseSignalTester` 类中，必须初始化一个专门用于存储触发点截面明细的列表。
- 该列表须记录每个触发点的全部资产、对应的分组 ID、因子值及该持有期内的超额收益。

#### Requirement: 2. 截面分配捕获逻辑
- 在回测每个触发日期时，获取该资产列表的分组结果。
- 在 `period_excess_rets` 计算完成后，将其与 `groups` 映射关系合并。

#### Requirement: 3. 数据持久化 (CSV 导出)
- 新增 `export_group_assignment_details` 方法。
- 导出的 CSV 文件必须包含以下字段：`date`, `asset_code`, `factor_value`, `group_id`, `excess_return`。
- 该导出操作需默认被集成在 `run_backtest` 的最终产出步骤中。

#### Scenario: 验证导出的明细数据
- **Given**: 反弹策略触发了 125 个信号点。
- **When**: 运行 `run_backtest` 结束后。
- **Then**: `results/` 目录下应存在 `group_assignment_details.csv`，文件行数为 `125 * 行业数量`。
