## ADDED Requirements

### Requirement: Huatai RSRS Normalization Timing
The system SHALL provide a method `ht_rsrs_norm` to calculate the Resistance Support Relative Strength (RSRS) normalized score (Z-Score) based on the Huatai methodology.

#### Scenario: RSRS continuous score output
- **WHEN** the 18-day rolling regression slope of High on Low prices (default params) is calculated
- **AND** normalized by its 600-day rolling mean and std
- **THEN** the system SHALL output the continuous Z-Score series.

### Requirement: Huatai Trend Regime Scoring
The system SHALL provide a method `ht_trend_regime` to calculate market trend strength based on the Huatai dual-MA crossover methodology (default 5/60 window).

#### Scenario: Huatai Trend Score calculation
- **WHEN** the short-term and long-term SMAs are calculated using default parameters
- **THEN** the system SHALL output a score representing the trend strength.

### Requirement: Huatai Volume Regime Scoring
The system SHALL provide a method `ht_volume_regime` to calculate volume-price scores as defined in the Huatai timing system.

#### Scenario: Huatai Volume score output
- **WHEN** current volume is compared to its historical moving average using relative expansion logic
- **THEN** the system SHALL output a relative volume score.
