# Tasks: save-sparse-group-results

- [x] 初始化内部列表 `self._group_assignment_log = []` 于 `SparseSignalTester.__init__`。
- [x] 在 `run_backtest` 的循环中，记录每个触发点的资产/分组/收益明细。
- [x] 在 `SparseSignalTester` 中新增 `export_group_assignment_details` 方法。
- [x] 在 `run_backtest` 结束流程中，自动调用该方法导出明细为 CSV。
- [x] 运行 `run_gx_pit_breakout_test.py` 验证导出结果。
