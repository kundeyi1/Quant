# triangle-breakout-filter

## Purpose
The `triangle-breakout-filter` provides signal identification and validation criteria for identifying price convergence and breakout patterns, specifically for equity index and sector rotation strategies. It is implemented as `gx_pit_breakout` within the `timing.market_timing` framework.

## Requirements

### Requirement: 三角形收缩突破信号过滤器 (Triangle Breakout Filter)
The system SHALL provide a flat function `gx_pit_breakout` for identifying potential trend breakouts after a period of price consolidation (migrated from `SignalFilters.calculate_gx_pit_breakout_filter`).

#### Scenario: Breakout confirmation
- **WHEN** the 5-day rolling volatility (Standard Deviation) is decreasing relative to its 20-day average
- **AND** the current close price is greater than the previous $N$-day high by at least 1%
- **THEN** the system SHALL output a signal value of `1` for the breakout date.

#### Scenario: No breakout
- **WHEN** price remains within the existing range or volatility has not contracted
- **THEN** the system SHALL output a signal value of `0` for that date.

### Requirement: Triangle Breakout Signal Identification
系统必须能够识别基于价格收敛和波动率压抑的三角形突破信号。
该信号在 T 日触发必须满足以下四个条件：
1. **突破幅度**：T 日的价格变动率（Return_T）必须大于 1.0%。
2. **前期波动压抑**：在 T-5 到 T-1 的 5 个交易日内，每日的价格变动率绝对值（|Return_i|）必须均小于 1.0%。
3. **通道宽度收窄**：使用滚动 5 日最高价（High_5） and 最低价（Low_5）构建价格通道。T-1 日的通道宽度（High_5 - Low_5）必须小于 T-2 日。
4. **数据完整性**：所有计算必须确保有足够的 5 日历史窗口数据，且在数据不足时不应产生虚假信号。

#### Scenario: Successful Signal Trigger
- **WHEN** 指数在 T-5 至 T-1 期间日跌幅分别为 0.2%, -0.5%, 0.8%, -0.1%, 0.3%，且 T-1 日 5 日通道跨度从 50 点缩小至 45 点，而 T 日大涨 1.5%
- **THEN** 系统在 T 日生成一个值为 1 的触发信号

#### Scenario: Blocked by High Volatility Pre-Trigger
- **WHEN** T-3 日价格变动为 1.2%（超过 1% 限制）
- **THEN** 系统在 T 日不应触发三角形突破信号

#### Scenario: Blocked by Expanding Channel
- **WHEN** T-1 日的 5 日通道宽度大于 T-2 日
- **THEN** 系统在 T 日不应触发三角形突破信号
