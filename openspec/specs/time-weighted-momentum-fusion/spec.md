# time-weighted-momentum-fusion Specification

## Purpose
TBD - This specification defines the capability for fusing sparse signals using time-weighted momentum over a sliding window, typically used for combining multiple signals into a single actionable factor.

## Requirements

### Requirement: 时间加权因子融合算法
系统必须实现在一个10个交易日的滑动窗口内，对所有触发的信号进行时点动量的加权合成。

#### Scenario: 正常的信号融合过程
- **WHEN**: 在 $T-10$ 到 $T$ 日期间，有信号在 $D_1$ 和 $D_2$ 两个交易日触发。
- **THEN**: 系统 SHALL 计算 $D_1$ 和 $D_2$ 信号在 $T$ 日的权重 $w_1 = 2^{-(T-D_1)/10}$ 和 $w_2 = 2^{-(T-D_2)/10}$。
- **THEN**: 系统 SHALL 将这些信号对应的行业因子先转化为 Rank 值，再按权重 $w$ 加权合并。

### Requirement: 动态持仓逻辑
系统必须具备在 20 日持有期内处理新信号并自动切换持仓的能力。

#### Scenario: 持仓中出现新信号
- **WHEN**: 当前处于 $T$ 日触发信号 of 20 日持仓期。
- **THEN**: 如果在 $T+5$ 日出现新信号，系统 SHALL 将持仓期重置，并从 $T+6$ 日起基于新触发的融合因子进行持仓切换。

### Requirement: 增强收益曲线可视化
系统必须支持多头、空头和多空（Long-Short）收益曲线的绘制。

#### Scenario: 生成多空对比曲线
- **WHEN**: 用户调用回测绘图功能。
- **THEN**: 系统 SHALL 绘制 Top 分组（多头）、Bottom 分组（空头）以及两者之差（多空）的净值曲线。

### Requirement: 分组超额收益柱状图
系统必须在结果中输出各个分组相对于基准或均值的累积超额收益柱状图。

#### Scenario: 绘制超额收益分布
- **WHEN**: 进行 20 日持有期测试结束时。
- **THEN**: 系统 SHALL 生成一个柱状图，展示各分组（如 Group 1 到 Group 5）在持有期内的平均超额表现。
