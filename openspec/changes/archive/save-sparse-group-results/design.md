# Design: save-sparse-group-results

## Context
在 `SparseSignalTester.run_backtest` 中，程序会遍历所有触发日期。目前程序计算并缓存了汇总的 IC 和基准收益，但没有记录每个资产（行业）的详细信息。

## Architecture & Logic

### Data Structures
- **Internal Storage**: `self._group_assignment_log = []`
    - 在 `run_backtest` 的循环中，将每个触发点的资产详情存入此列表。
- **Schema**:
    - `date`: 信号触发日
    - `asset_code`: 资产 (例如: 850311)
    - `factor_value`: 因子原始值/百分位值
    - `group_id`: 分配到的分组 (1-N)
    - `excess_return`: 相对于基准的 T+20 累计收益

### Workflow Changes
1.  **分组捕获**:
    - 修改 `_extract_cross_section` 或在 `run_backtest` 中，在分组逻辑完成之后，立即提取每个 `asset_code` 的 `group_id`。
2.  **收益关联**:
    - 在 `calculate_group_returns` 或 `_cache_performance_metrics` 处，获取到资产级别的 `period_excess_rets` 后，将其与分组信息合并，汇总到 `_group_assignment_log` 中。
3.  **持久化导出**:
    - 实现 `export_group_assignment_details(self, filename="group_assignment_details.csv")`。
    - 将 `_group_assignment_log` 转换为 `pd.DataFrame`。
    - 保存到 `self.output_dir` 下的指定文件名。

## Decisions & Alternatives
- **Decision**: 采用扁平化的 CSV (One row per trigger-asset-combination)。
    - **Reason**: 方便用户直接通过 Excel/Pandas 进行透视分析，查看各日期、各分组下的行业分布。
- **Alternative**: 为每个触发点创建一个 CSV 文件。
    - **Reason**: 如果触发点多且资产多（如全 A 股），文件数量碎。行业级测试触发点在 30-150 个，资产 30-100 个，放在一个文件里总行数仅为数千行，极其紧凑。
