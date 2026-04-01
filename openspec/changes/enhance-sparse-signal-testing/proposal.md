## Why

当前 `SparseSignalTester` 的绩效评估体系不够完善，缺乏 Calmar 比率、胜率、盈亏比及详细的持仓统计（如平均持仓天数、中位数等）。此外，`continuous_real_timeline` 绘图模式在空仓期间的逻辑不清晰，导致净值曲线在无信号时表现异常（如垂直连线或日期缺失），未能直观反映“空仓即横盘”的策略特性。

## What Changes

- **绩效指标增强**: 在 `calculate_performance_stats` 中引入 Calmar 比率、单笔胜率、多头/空头盈亏比。新增年度 IC（与持仓时间挂钩的年度聚合 IC）。
- **指标报告整合**: 
    - 将深度绩效分析（含单笔胜率、盈亏比、超额夏普比率、累计超额等）整合到 `performance_summary_report` 表中。
    - 汇总表包含：多头年化、多空年化、多头最大回撤、多空最大回撤。
- **绘图逻辑重构**: 
    - 改造 `_calculate_continuous_strategy_returns`，使其在完整的时间轴上运行。
    - 确保在“信号活跃期”展示真实的价格波动，而“无信号期”净值保持恒定（横线）。
    - 消除绘图中的垂直跳变感。
    - **集成 NavAnalyzer (仅限完整时间轴)**: 仅针对 `continuous_real_timeline`（完整时间轴净值）调用 `core.NavAnalyzer`。其他基于稀疏信号点的离散绘图（如 `discrete` 模式）仍保留在 Tester 内部实现，因为它们不具备连续时间序列特征。
- **批量汇总导出**: 新增功能支持批量输入因子列表，并生成类似图中所示的汇总汇总对比表。

## Capabilities

### New Capabilities
- `advanced-backtest-metrics`: 提供 Calmar、胜率、盈亏比等深度绩效分析。
- `batch-factor-evaluator`: 支持对多个因子进行并行/顺序测试，并输出统一格式的汇总对比报表。

### Modified Capabilities
- `sparse-signal-testing`: 修改连续净值计算逻辑，生成真实的持仓净值曲线（空仓期为横盘）。改用 `NavAnalyzer` 进行绘图。

## Impact

- **Affected Code**: `core/SparseSignalTester.py` (核心计算与绘图逻辑), `core/FactorTester.py` (可能影响绩效展示组件)。
- **APIs**: `SparseSignalTester.run_backtest` 及其内部统计方法。
- **Dependencies**: 保持现有的 Pandas/Matplotlib 环境。
