## RENAMED Requirements

FROM: `filters/signal_filters.py`
TO: `timing/market_timing.py`

## MODIFIED Requirements

### Requirement: 大跌反弹信号过滤器 (Rebound Signal Filter)
The system SHALL provide a flat function `gx_pit_rebound` to detect potential market reversals after significant drops.

#### Scenario: Rebound trigger (Atr-based)
- **WHEN** the daily return on day $T$ is greater than its dynamic threshold $U$ (where $U$ is adjusted by relative $ATR_{60}$)
- **AND** a significant drawdown of at least $D$ occurred within a rolling window $M$ prior to $T$
- **THEN** the system SHALL output a signal value of `1` for day $T$.

#### Scenario: No rebound trigger
- **WHEN** either the return threshold $U$ or the drawdown threshold $D$ is not met
- **THEN** the system SHALL output a signal value of `0` for that date.
