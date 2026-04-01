# Specification: add-signal-stats

## Signal Statistics & Distribution Capabilities

The system must provide detailed statistical views and logs for the signal triggers generated during a sparse momentum test.

### Requirement 1: Annual Frequency Visualization
- **Input**: List of signal trigger dates (`self.trigger_dates`).
- **Output**: A bar chart displaying the count of triggers per year.
- **Constraints**:
    - The chart should have a clear title (e.g., "Signal Trigger Frequency by Year").
    - X-axis should be chronological by year.
    - Y-axis should be the count of triggers.
    - The image must be saved to the `output_dir` as `annual_signal_frequency.png`.

### Requirement 2: Trigger Date Log Export
- **Input**: List of signal trigger dates (`self.trigger_dates`).
- **Output**: A CSV file containing all trigger dates.
- **Constraints**:
    - File name: `signal_trigger_dates.csv`.
    - Column name: `trigger_date`.
    - The file must be saved to the `output_dir`.

### Requirement 3: Tester Method Signatures
- `SparseSignalTester.plot_annual_frequency(self, title="Annual Signal Frequency")`
- `SparseSignalTester.export_trigger_log(self, filename="signal_trigger_dates.csv")`

## Delta Specification: sparse-signal-testing

Update the testing engine to include new reporting methods.

### Updated Requirements
- The testing engine MUST provide methods to quantitatively analyze the temporal distribution of signals.
- In addition to group performance, the engine SHOULD automatically output a log of all simulated events.
