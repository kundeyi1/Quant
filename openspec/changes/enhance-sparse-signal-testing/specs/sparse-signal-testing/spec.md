## MODIFIED Requirements

### Requirement: 增强收益展示逻辑
系统 SHALL 在原有的分组收益统计基础上，支持多空对冲收益及连续/非连续信号段的展示。

#### Scenario: 完整时间轴绘图调用 NavAnalyzer
- **WHEN**: 运行 `continuous_real_timeline` 模式且已生成基于全历史周期的日收益率序列。
- **THEN**: 系统 SHALL 实例化 `core.NavAnalyzer.NAVAnalyzer`，并利用其 `Visualizer` 绘制标准包含绩效看板的图表。
- **THEN**: 在空仓期间，该日收益率 SHALL 设为 0。

#### Scenario: 离散信号点绘图保留内部实现
- **WHEN**: 运行 `discrete`（离散点累乘）或其他非连续时间轴模式。
- **THEN**: 系统 SHALL 继续使用 `SparseSignalTester` 内部的 Matplotlib 绘图逻辑，仅标注信号触发日，不进行全时间轴插值。

### Requirement: 统计指标增强
系统 SHALL 包含 IC/IR、年化波动率、Calmar 比率、单笔胜率、盈亏比、各分组超额收益分布以及年度 IC 统计。

#### Scenario: 绩效指标汇总与报表整合
- **WHEN**: 回测结束并调用指标计算时。
- **THEN**: 系统 SHALL 计算以下指标：
    - **Calmar 比率**: 年化收益 / 最大回撤。
    - **胜率与盈亏比**: 针对单次信号/单次持仓的胜率及盈亏比统计。
    - **年度 IC**: 计算与信号持仓周期相匹配的年度聚合 IC 指标。
- **THEN**: 系统 SHALL 生成以下报表：
    - **performance_summary_report**: 整合胜率、盈亏比、年度 IC、超额夏普比率、累计超额等深度指标。
    - **strategy_overview_table**: 包含多头年化、多多空年化、多头最大回撤、多空最大回撤的核心指标表。

## ADDED Requirements

### Requirement: 批量因子评估器
系统 SHALL 提供一个批量评估能力，能够对一组因子进行统一测试并汇总结果。

#### Scenario: 批量生成汇总表格
- **WHEN**: 用户提供一个因子列表（或信号路径列表）及回测参数。
- **THEN**: 系统 SHALL 循环执行回测，并自动提取每个因子的关键评价指标，最终输出一个 DataFrame 格式的汇总表，方便横向对比。
