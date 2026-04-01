## MODIFIED Requirements

### Requirement: Multi-Metric Analysis
<!-- Content from original spec/sparse-signal-testing.md MODIFIED to include signal statistics -->
The testing engine SHALL provide a comprehensive view of factor performance, including group metrics and the distribution of trigger points.

#### Scenario: Visualizing Distribution alongside Results
- **WHEN** the user runs a backtest with `SparseSignalTester`
- **THEN** it SHALL be possible to call the reporting methods to gain insights into signal frequency.
