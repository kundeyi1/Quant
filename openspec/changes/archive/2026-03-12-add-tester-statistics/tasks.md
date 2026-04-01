## 1. Core Logic Enhancement

- [x] 1.1 在 `core/SparseSignalTester.py` 的 `run_backtest` 中，添加对触发点因子值和 T+period 收益的截面缓存（IC 计算准备）。
- [x] 1.2 实现新方法 `calculate_performance_stats`：基于缓存的触发点截面数据，计算 IC、RankIC、ICIR、IC 胜率、组 5 超额和组 1 超额。

## 2. API Update & Reporting

- [x] 2.1 修改 `run_backtest` 的返回结果，除了 `group_returns_df` 之外，计算并缓存统计指标到 `self.performance_stats`。
- [x] 2.2 新增 `print_performance_report` 方法，输出包含 IC/IR 等详细汇总报表的文本块。
- [x] 2.3 新增 `export_performance_stats` 方法，将统计结果详情（每个触发点的 IC 和超额收益）导出为 CSV。

## 3. Reference Integration

- [x] 3.1 修改所有 `run_gx_pit_*.py` 脚本，在回测完成后调用 `tester.print_performance_report()`。
- [x] 3.2 验证各脚本运行输出是否包含 ICIR、IC 胜率及多空超额收益的统计。
- [x] 3.3 归档变更。
