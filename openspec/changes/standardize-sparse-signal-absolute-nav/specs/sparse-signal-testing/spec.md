## MODIFIED Requirements

### Requirement: 增强收益展示逻辑
系统 SHALL 在原有的分组收益统计基础上，支持多空对冲收益及非连续信号段拼接。所有回测视角的收益率计算 SHALL 统一采用“持仓周期内期初等权持有”逻辑，即直接计算从触发日 $T$ 到期末 $T+N$ 之间的截面平均收益，不得采用每日再平衡（Daily Compounding）逻辑，以确保全市场大样本下的年化收益真实性。

#### Scenario: 自动拼接无信号时间
- **WHEN**: 策略在不同时间段触发信号，存在长达数月的无信号间隙。
- **THEN**: 系统 SHALL 在绘图时将无信号期间排除，通过索引重排实现 X 轴的无缝拼接。此时拼接后的净值曲线 SHALL 与 L-S-LS 组合图中的 LS 线在数值上完全对齐。

#### Scenario: 期初等权收益一致性验证
- **WHEN**: 系统在全市场 5000+ 股票样本上运行，某信号周期为 20 天。
- **THEN**: `Full Timeline` 图表与 `Spliced` 图表在对应的持仓期间内 SHALL 表现出相同的资产价值增量，且计算逻辑均基于 `(P_end / P_start - 1).mean()`，而非 `cumprod(mean(P_t / P_{t-1} - 1))`。

### Requirement: 统计指标增强
系统 SHALL 包含 IC/IR、年化波动率和各分组超额收益分布。所有统计指标及净值曲线 SHALL 以“绝对收益”为基准展示，移除隐含的 Benchmark 扣除逻辑。

#### Scenario: 分组绝对收益可视化
- **WHEN**: 回测报告生成时。
- **THEN**: 系统 SHALL 增加一个柱状图（Bar Chart），显示 Group 1 到 Group N 的累积平均绝对收益分布（Absolute Mean Return），而非超额收益。
