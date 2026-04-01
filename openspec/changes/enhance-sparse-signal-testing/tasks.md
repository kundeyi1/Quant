## 1. 核心计算与绩效增强 (Core Metrics)

- [ ] 1.1 修改 `calculate_performance_stats` 增加 Calmar、波动率计算，移除持仓天数统计。
- [ ] 1.2 增加单次持仓/信号胜率、盈亏比逻辑。
- [ ] 1.3 实现年度 IC 计算逻辑。
- [ ] 1.4 实现报表生成逻辑：`performance_summary_report` (含超额夏普、累计超额) 和 `strategy_overview` (含年化与回撤)。

## 2. 净值曲线表现优化 (Equity Logic & Visualization)

- [ ] 2.1 重写 `_calculate_continuous_strategy_returns`，构造基于全时间轴的日度收益率序列（空仓期为 0）。
- [ ] 2.2 在 `SparseSignalTester` 中新增专用函数（如 `plot_full_timeline_nav`），提取完整收益率序列。
- [ ] 2.3 修改 `plot_equity_curve` 的 `continuous_real_timeline` 分支，由其调用上述专用函数，并集成 `NavAnalyzer`。
- [ ] 2.4 保持 `discrete` 模式的内部绘图逻辑独立，不使用 NavAnalyzer。

## 3. 批量评估与汇总工具 (Batch Evaluator)

- [ ] 3.1 创建新脚本 `run_batch_sparse_test.py` 或在 `SparseSignalTester` 中增加静态 Batch 方法。
- [ ] 3.2 循环遍历输入因子列表，运行测试并捕获绩效字典。
- [ ] 3.3 将汇总结果整理为带多级表头的 DataFrame，并支持导出 CSV。

## 4. 验证与美化 (Validation)

- [ ] 4.1 使用 20日创新高占比（择时）因子进行回归测试。
- [ ] 4.2 检查图表输出（与原型图片对比），确认无垂直跳变线。
- [ ] 4.3 确认汇总表格指标数值正确无误。
