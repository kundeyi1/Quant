## ADDED Requirements

### Requirement: Sparse Signal Day Momentum Alignment
The system MUST allow using the historical return of assets on the EXACT date of the timing trigger as the cross-sectional momentum metric.

#### Scenario: Signal Day Weight Assignment
- **WHEN** a timing trigger is identified on date T
- **THEN** the sector rotation engine SHALL extract the daily returns of all industries on date T and use them for rank-based grouping (Long/Short)

### Requirement: Standardized Performance Export
The system SHALL automate the generation of evaluation reports for sparse timing-momentum signals.

#### Scenario: Report Generation in results/timing
- **WHEN** the backtest is complete
- **THEN** it SHALL export a CSV summary and a dual-axis NAV/Drawdown chart to the specified directory
