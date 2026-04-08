## ADDED Requirements

### Requirement: Trigger Score Calculation
The system SHALL compute a `trigger_score` by extracting `trigger_factors` from the `factors_df`, applying cross-sectional ranking (rank(pct=True)) or standardization per date, and averaging the results across all factors in the `trigger_list`.

#### Scenario: Multi-factor trigger scoring
- **WHEN** a list of factors `['Vol_Explosion_Today', 'Accel_Today']` is provided
- **THEN** the system calculates the rank for each on each date and returns their mean as the `trigger_score`.

### Requirement: Trigger Event Identification
The system SHALL identify a `trigger_event` based on the `trigger_score`. It MUST support two modes:
1. **Quantile Mode**: Based on cross-sectional percentile (e.g., top 30%).
2. **Fixed Threshold Mode**: Based on an absolute value (e.g., Score > 0.5).
A boolean mask SHALL be returned where values satisfying the condition are True.

#### Scenario: Identifying top 30% triggers
- **WHEN** the `trigger_score` is computed and a `quantile=0.7` is specified
- **THEN** the system generates a mask where only the top 30% of stocks per date are marked as True.

#### Scenario: Identifying triggers based on fixed threshold
- **WHEN** the `trigger_score` is computed and a `threshold=1.5` is provided
- **THEN** the system generates a mask where only stocks with `trigger_score > 1.5` are marked as True.

### Requirement: Stratified Conditional Testing
The system SHALL perform a stratified factor test only on samples where `trigger_event` is True. Within this sub-sample, the `env_factor` MUST be re-ranked cross-sectionally and divided into 5 quantile bins for return calculation.

#### Scenario: Conditional grouping in sub-sample
- **WHEN** the `trigger_event` filter is applied
- **THEN** the system re-calculates the 0-100% ranks of the `env_factor` only for the active stocks on each date.

### Requirement: Stability Control and Filtering
The system SHALL discard any date from the analysis if the number of stocks in the trigger sub-sample is less than `min_samples` (default 30). Group returns SHALL be set to NaN if a group has insufficient samples.

#### Scenario: Handling small sample dates
- **WHEN** a date has only 15 stocks passing the trigger threshold
- **THEN** that date is ignored in the final mean return calculation to ensure statistical robustness.

### Requirement: Performance Summary Reporting
The system SHALL output a summary for each `env_factor` including the mean 1d and 5d returns for each of the 5 groups, and the long-short (Group 5 minus Group 1) performance.

#### Scenario: Generating factor leaderboard
- **WHEN** all `env_factors` have been tested
- **THEN** the system prints a sorted list of factors by their long-short return spread.
