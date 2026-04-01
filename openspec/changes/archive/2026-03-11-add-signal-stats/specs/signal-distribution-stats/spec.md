## ADDED Requirements

### Requirement: Annual Signal Frequency Visualization
The `SparseSignalTester` SHALL provide a method to calculate and plot the annual frequency of signal triggers as a bar chart.

#### Scenario: Generate Annual Frequency Plot
- **WHEN** the method `plot_annual_frequency` is called
- **THEN** it SHALL extract years from `trigger_dates`, count occurrences per year, and save a bar chart to the specified output directory.

### Requirement: Trigger Log Export
The `SparseSignalTester` SHALL provide a method to export all signal trigger dates to a CSV file.

#### Scenario: Export Trigger Dates to CSV
- **WHEN** the method `export_trigger_log` is called
- **THEN** it SHALL create a CSV file containing a single column labeled `trigger_date` with all items in `self.trigger_dates`.
