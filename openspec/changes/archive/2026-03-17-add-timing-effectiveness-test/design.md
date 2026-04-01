## Context

`SparseSignalTester.py` 目前主要关注信号触发后的**横截面**（Cross-sectional）表现，即在信号触发那一刻，不同标的之间的相对强弱。然而，一个好的选股信号也应当是一个好的**择时**（Timing）信号，即信号出现的时点相对于该标的的其他时点应具有更高的预期收益。

通过对比“信号触发后的收益”与“全样本的收益分布”，可以验证该信号是否捕捉到了市场或标的的特殊状态。

## Goals / Non-Goals

**Goals:**
- 实现信号择时有效性的量化评估。
- 支持全样本收益分布的自动化计算（基准分布）。
- 提供可视化对比图（直方图/KDE）以直观展示信号收益是否显著偏离基准。
- 计算统计显著性指标（均值差异等）。

**Non-Goals:**
- 不涉及多因子融合逻辑的变更。
- 不修改现有的分组逻辑。
- 不涉及实时交易信号生成。

## Decisions

### 1. 基准分布的定义
- **决策**: 使用 `000985.CSI.xlsx` (中证全指) 的全样本滚动持有期收益作为基准。
- **理由**: 这代表了市场在相同周期内的平均收益潜力，是评估信号择时效果的最强背景基线。

### 2. 方法解耦方案
- **决策**: 将择时分析设计为 `public` 方法 `run_timing_analysis(self, period=None, benchmark_series=None)`。在该方法内，直接整合全样本收益（如 `000985.CSI`）的滚动持有期计算逻辑。
- **参数**: 
  - `period`: 默认为类实例的 `self.period`。
  - `benchmark_series`: 可传入外部基准序列（如 `000985.CSI`），若为空则使用默认基准。
- **理由**: 保持回测与分析逻辑的清晰解耦，且由于滚动收益计算逻辑较简单，直接集成进主方法以减少类私有方法冗余。

### 3. 可视化方案
- **决策**: 提供内置的 `plot_timing_distribution(self, stats)` 方法。
- **理由**: 分布对比（信号分布 vs. 全样本分布）是此类分析的核心价值，直观展示信号是否落在右侧厚尾。

### 4. 统计量选择
- **决策**: 重点输出信号收益在全样本分布中的 **Quantile Rank** 和由 $T$ 检验导出的显著性 $P$-Value。
- **理由**: 分位数能直观反映信号的“稀缺性”；T 检验用于判断是否显著优于随机入场。

## Implementation Sketch

```python
class SparseSignalTester:
    def run_backtest(self, ...):
        # 现有的分组、收益计算、绘图逻辑
        # 不在该流程末尾强制调用 run_timing_analysis
        pass

    def run_timing_analysis(self, period=None, benchmark_series=None):
        """
        独立的公有分析方法。
        1. 获取 benchmark 序列 (优先使用传入的 000985.CSI 数据)
        2. 计算 benchmark 的全样本 period 滚动持有期收益分布 (内部逻辑集成)
        3. 提取所有信号触发点后的 period 收益集合 (Sample distribution)
        4. 计算 Quantile Rank, T-Stat, P-Value
        5. 调用绘图逻辑并生成报告
        """
        pass
```

## Risks / Trade-offs

- **[Trade-off] 灵活性 vs. 便利性**：
  - **灵活性**: 择时分析可以对过滤后的信号、特定板块信号等子集进行分析。
  - **便利性**: 用户由于忘了手动调用可能漏掉此分析。
  - **Mitigation**: 在 `run_backtest` 后的文档和示例文件中，明确推荐用户使用该方法配合分析。
