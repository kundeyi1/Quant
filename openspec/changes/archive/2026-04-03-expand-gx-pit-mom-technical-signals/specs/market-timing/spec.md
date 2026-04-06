## ADDED Requirements

### Requirement: Index Physical Factor Calculation
The system MUST provide objective, absolute metrics based on raw data to describe index states across multiple dimensions (Price, Volume, Trend).

#### Scenario: Price Distance Calculation
- **WHEN** the `PriceFactors.price_dist_high` logic is invoked
- **THEN** it SHALL return raw percentage distance `(Price / HHV - 1)` instead of quantile rank

#### Scenario: Volume Dryness Calculation
- **WHEN** the `VolumeFactors.volume_abs_dryness` logic is invoked
- **THEN** it SHALL return a value representing `Volume / MA(Volume)` to detect absolute liquidity exhaustion

### Requirement: Two-Stage Momentum Filter
The system SHALL implement a multi-step logic where a technical setup is only activated if it is followed by a confirmed price momentum on the same day.

#### Scenario: Positive Confirmation
- **WHEN** a technical signal (e.g., volume_dry < 0.7) is triggered AND the index daily return is >= 3%
- **THEN** the composite signal SHALL be marked as 1; otherwise, it SHALL be 0

## MODIFIED Requirements

### Requirement: Timing Signal Integration
<!-- FROM: market-timing spec -->
The system SHALL support the aggregation of multiple technical timing triggers into a unified entry matrix.

#### Scenario: Physical Trigger Execution
- **WHEN** the `market_timing` module is called with specific physical thresholds
- **THEN** it MUST correctly apply filters like `f_vola < 0.75` or `f_dist_high > -0.005` to generate the 0/1 binary series
