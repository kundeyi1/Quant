## RENAMED Requirements

FROM: `SignalFilters.calculate_gx_pit_breakout_filter`
TO: `timing.market_timing.gx_pit_breakout`

## MODIFIED Requirements

### Requirement: 三角形收缩突破信号过滤器 (Triangle Breakout Filter)
The system SHALL provide a flat function `gx_pit_breakout` for identifying potential trend breakouts after a period of price consolidation.

#### Scenario: Breakout confirmation
- **WHEN** the 5-day rolling volatility (Standard Deviation) is decreasing relative to its 20-day average
- **AND** the current close price is greater than the previous $N$-day high by at least 1%
- **THEN** the system SHALL output a signal value of `1` for the breakout date.

#### Scenario: No breakout
- **WHEN** price remains within the existing range or volatility has not contracted
- **THEN** the system SHALL output a signal value of `0` for that date.
