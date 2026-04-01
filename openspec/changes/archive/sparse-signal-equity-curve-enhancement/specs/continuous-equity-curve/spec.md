## ADDED Requirements

### Requirement: 信号驱动调仓逻辑 (Continuous Signal Rebalance)
`SparseSignalTester` MUST 提供一种连续时间的净值计算方法。当在当前信号的持有期（例如 20 天）内出现下一个触发信号时，系统 SHALL 立即结算当前持仓并切换至新信号所选的资产组合，而不是持有至原始到期日。

#### Scenario: 信号重叠时的自动调仓
- **WHEN**: 信号 A 在 $T$ 日触发，持有期为 20 天；信号 B 在 $T+5$ 日触发。
- **THEN**: 系统在 $T+5$ 日结算信号 A 的收益，并从 $T+5$ 日起开始计算信号 B 的收益。

### Requirement: 连续时间序列净值曲线生成
系统 MUST 支持生成完整的日度净值序列（Daily Net Value Series）。

- **模式 A (Gap Filling)**: 信号间的空白时段（无持仓）SHALL 填充为 0 收益，使得净值曲线保持平直。
- **模式 B (Real Timeline)**: 曲线 SHALL 基于原始价格索引的时间轴，在信号触发点进行净值衔接。

#### Scenario: 空白期平滑处理
- **WHEN**: 信号 A 结束于 $T+20$，下一个信号 C 触发于 $T+30$。
- **THEN**: 在 $T+21$ 到 $T+29$ 期间，每日收益率 SHALL 设为 0，累计净值保持不变。

## MODIFIED Requirements

### Requirement: 可视化接口扩展 (Enhanced Equity Curve Plotting)
`SparseSignalTester.plot_equity_curve` SHALL 增加参数支持，允许用户在原始离散累乘、连续调仓（空仓平滑）和连续调仓（真实时间轴）之间切换。

#### Scenario: 切换绘图模式
- **WHEN**: 用户调用 `plot_equity_curve(mode='continuous_rebalance')`。
- **THEN**: 图表 SHALL 展示基于日度调仓逻辑生成的连续净值曲线，而非离散触发点的累乘值。
