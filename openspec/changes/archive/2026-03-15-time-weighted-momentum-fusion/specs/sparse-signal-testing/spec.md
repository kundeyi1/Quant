## MODIFIED Requirements

### Requirement: 增强收益展示逻辑
系统 SHALL 在原有的分组收益统计基础上，支持多空对冲收益及非连续信号段拼接。

#### Scenario: 自动拼接无信号时间
- **WHEN**: 策略在不同时间段触发信号，存在长达数月的无信号间隙。
- **THEN**: 系统 SHALL 在绘图时将无信号期间排除，通过索引重排实现 X 轴的无缝拼接。

### Requirement: 统计指标增强
系统 SHALL 包含 IC/IR、年化波动率和各分组超额收益分布。

#### Scenario: 分组超额收益可视化
- **WHEN**: 回测报告生成时。
- **THEN**: 系统 SHALL 增加一个柱状图（Bar Chart），显示 Group 1 到 Group N 的累积平均超额收益分布。
