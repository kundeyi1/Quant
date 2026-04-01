## Context

目前 `SparseSignalTester` 已实现的 Spliced Equity Curve 仅展示了净值，未给出关键数值指标。本设计旨在通过扩展类内相关方法及报表生成逻辑，集成常见的量化评价标准，并实施多语言（中文）可视化。

## Goals / Non-Goals

**Goals:**
- 在 `SparseSignalTester` 内部增加一个通用的性能指标计算静态方法。
- 重构 `calculate_performance_stats` 以包含全组合（Long-Short, Long-Only）指标。
- 更新绘图逻辑，包括中文标题和在图面上标注关键指标（如 Sharpe）。

**Non-Goals:**
- 不改变现有的信号触发逻辑和调仓逻辑。
- 不引入外部专门的绩效分析库（如 pyfolio），保持库的独立性。

## Decisions

### 1. 绩效计算引擎
- **决策**: 在 `SparseSignalTester` 中通过增加静态方法 `_calculate_metrics(equity_series)` 来实现。
- **依据**: 离散信号的净值曲线本身是不等间距的（Signal-based），但 `_calculate_continuous_strategy_returns` 已经将其对齐到了时间轴或端点。我们将基于这些生成的净值序列进行指标提取。

### 2. 年化基准 (Annualization Factor)
- **决策**: 默认交易日计数仍使用 252。
- **计算逻辑**:
  - `Annualized Return = (Final / Start) ^ (252 / TotalDays) - 1`
  - `Sharpe = Annualized Return / Annualized Std`

### 3. 可视化统一
- **决策**: 所有的绘图标题（Title）硬编码为精简中文。
- **动态图例**: 对于 `plot_equity_curve` (Spliced 模式)，将该曲线的年化收益和最大回撤实时计算并注入到图例 (Legend) 中。
- **汇总报表**: 对于 `plot_l_s_ls_combined_curve` 涉及的多头、多空曲线指标，仅记录在 `performance_summary_report.csv` 报表中，保持图面整洁。
- **示例**: `Signal Trigger Points` -> `信号触发位置`, `Equity Curve` -> `多空组合净值曲线`。

## Risks / Trade-offs

- [Risk] 稀疏信号的净值曲线日期不连续，计算夏普比率可能存在偏差。 -> [Mitigation] 使用生成后的连续净值序列（即使包含 Gap Fill）进行计算，能更贴近实际持有体验。
- [Risk] 中文字体设置。 -> [Mitigation] 使用 `SimHei` 确保在 Windows 环境下能正常渲染标题。
