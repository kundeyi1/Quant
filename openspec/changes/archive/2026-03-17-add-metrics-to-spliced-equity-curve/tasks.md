## 1. 核心计算方法实现

- [x] 1.1 在 `SparseSignalTester` 中增加 `_calculate_equity_metrics` 静态方法，处理年化收益、最大回撤、夏普。
- [x] 1.2 在 `calculate_performance_stats` 中增加对 Long 曲线和 LS 曲线的计算逻辑调用。
- [x] 2.1 更新 `print_performance_report` 和 `performance_summary_report.csv` 的导出逻辑，包含多头和多空的年化、回撤和夏普。
- [x] 2.2 将所有的绘图函数 (`plot_signals`, `plot_annual_frequency`, `plot_timing_distribution`, `plot_l_s_ls_combined_curve`, `plot_excess_return_bar`, `plot_equity_curve`) 的英文标题全部替换为中文翻译。
- [x] 2.3 在 `plot_equity_curve` (Spliced 模式) 中，将计算出的年化收益和最大回撤动态注入到图例 (Label) 中。
- [x] 2.4 在 `plot_l_s_ls_combined_curve` 中，仅执行中文化，相关多曲线指标输出至 summary 报表。

## 3. 验证与回归测试

- [x] 3.1 在 `test.ipynb` 中运行一个 `SparseSignalTester` 的典型回测任务，检查图片标题和 CSV 报表输出。
- [x] 3.2 验证错误处理逻辑（如交易日少于 252 或净值为 NaN 的情况）。
- [x] 完成所有流程：中文化 + 指标计算 + 图例注入 + 报表扩展。
