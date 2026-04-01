## ADDED Requirements

### Requirement: Single-file Distribution
The system SHALL bundle all required calculation logic, data loading, and utilities into a single, independent Python script named `standalone_gx_pit_mom.py`.

#### Scenario: Running the standalone script
- **WHEN** the user executes `python standalone_gx_pit_mom.py`
- **THEN** the script SHALL successfully import necessary libraries and run without requiring external local modules (e.g., `core`, `timing`, `factors`).

### Requirement: Outdated Data Check
The script SHALL check the existing output file (e.g., `gx_pit_mom_results.parquet` or equivalent) to determine if a re-calculation is necessary.

#### Scenario: Data is already up-to-date
- **WHEN** the latest date in the output file is greater than or equal to the specified `target_date`
- **THEN** the script SHALL exit gracefully with a message indicating no update is needed.

#### Scenario: Data is outdated
- **WHEN** the latest date in the output file is less than the specified `target_date`
- **THEN** the script SHALL proceed to re-calculate all factors up to the current available data and save the result.

### Requirement: Sorted Factor Export
The final output SHALL be sorted first by `date` in descending order, and secondarily by `factor_value` (or signal value) in descending order within each date.

#### Scenario: Exporting results
- **WHEN** the script saves the final calculation results
- **THEN** the output file SHALL contain rows where the most recent dates appear first, and within each date, the highest-ranking sector/asset appears at the top.

### Requirement: Feature Pruning
The standalone script SHALL NOT include any backtesting, plotting, or performance evaluation logic (e.g., `SparseSignalTester`, `matplotlib`, `plotly`).

#### Scenario: Verifying script content
- **WHEN** the script is inspected or executed
- **THEN** it SHALL NOT contain references to `SparseSignalTester` or any plotting libraries, ensuring a smaller footprint and fewer dependencies.
