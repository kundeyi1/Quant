## Why

当前 `SparseSignalTester` 的回测输出仅包含基本的净值曲线和简单的 IC 统计，缺乏量化评价的核心指标（年化收益、最大回撤、夏普比率）。此外，现有的绘图标题为英文，不便于本地研究员直接查阅。

增加这些指标能更直观地衡量策略风险调整后的收益表现，提升框架的专业性和易用性。

## What Changes

- **新增回测指标**: 在 `SparseSignalTester` 的 Spliced Equity Curve 计算逻辑中加入年化收益率、最大回撤、夏普比率的计算。
- **扩展汇总报表**: 在生成的 `performance_summary_report.csv` 中，不仅保留原有的 IC 统计，还需增加多头 (Long) 和多空 (L-S) 组合的专项风险收益统计。
- **UI 中文可视化**: 将 `SparseSignalTester` 中所有的绘图函数 (`plot_signals`, `plot_group_returns`, `plot_equity_curve` 等) 的标题统一改为中文。

## Capabilities

### New Capabilities
- `backtest-metrics-calculation`: 提供标准化的量化绩效指标计算引擎（Annualized Return, Max Drawdown, Sharpe Ratio）。
- `sparse-tester-reporting-enhancement`: 扩展 `SparseSignalTester` 的报表输出格式，包含多头和对冲组合的明细。

### Modified Capabilities
- `visual-localization`: 修改绘图模块，支持中文标题显示。

## Impact

- `core/SparseSignalTester.py`: 核心代码逻辑修改，包括 `calculate_performance_stats` 和绘图函数。
- `results/sparse_signal_test/`: 生成的 CSV 报表和 PNG 图片格式会有所变动。
