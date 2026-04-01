## Why

当前 `SparseSignalTester` 仅输出了分组的聚合收益（平均值）和汇总绩效指标（IC/IR）。为了支持对每次触发信号的具体行业配置进行复盘（例如：查看 2014 年底反弹时，哪些行业被分到了最强组，具体的因子值和超额收益是多少），需要持久化保存每次触发点的截面分组明细。

## What Changes

- **核心逻辑增强**：在 `SparseSignalTester` 的回测循环中，捕获每个触发日期的完整截面分配信息。
- **数据字段**：保存 `date`, `asset_code`, `factor_value`, `group_id`, `period_excess_return`。
- **导出功能**：新增 `export_group_assignment_details` 方法，将所有触发点的明细合并导出为一个 CSV 文件。
- **自动化集成**：默认在回测结束时自动调用导出方法。

## Capabilities

### Modified Capabilities
- `sparse-signal-testing`: 增加“触发点截面明细保存”的要求。其核心价值在于可追溯性。

## Impact

- `core/SparseSignalTester.py`: 
    - 增加 `self._group_assignment_log` 列表。
    - 修改 `_cache_performance_metrics` 或 `run_backtest` 以捕获明细。
    - 实现导出逻辑。
- `results/` 目录下将产生 `group_assignment_details.csv`。
