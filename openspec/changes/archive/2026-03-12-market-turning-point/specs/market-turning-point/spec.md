## ADDED Requirements

### Requirement: Market Turning Point (Switch) Signal
The system SHALL provide a method `calculate_market_turning_point` to detect potential market tops based on a combination of cross-sectional sector exhaustion and benchmark volatility breakouts.

#### Scenario: Successful signal trigger
- **WHEN** the number of sectors reaching a 52-week high on day $T$ decreases by 3 or more compared to day $T-1$
- **AND** the benchmark index return on day $T$ is less than $-ATR_{60}$ (where $ATR$ is the relative Average True Range)
- **THEN** the system SHALL output a signal value of `1` for day $T$.

#### Scenario: No signal trigger on low sector decay
- **WHEN** the number of sectors reaching a 52-week high on day $T$ decreases by only 2 compared to day $T-1$
- **AND** the benchmark index return on day $T$ is less than $-ATR_{60}$
- **THEN** the system SHALL output a signal value of `0` for day $T$.

#### Scenario: No signal trigger on low volatility
- **WHEN** the number of sectors reaching a 52-week high on day $T$ decreases by 4 compared to day $T-1$
- **AND** the benchmark index return on day $T$ is greater than $-ATR_{60}$ (i.e., less of a drop than the volatility threshold)
- **THEN** the system SHALL output a signal value of `0` for day $T$.
