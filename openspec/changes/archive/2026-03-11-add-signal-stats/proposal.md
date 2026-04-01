## Why

Currently, the sparse signal testing framework provides group performance following a trigger but lacks higher-level statistics on the signal's distribution and specific timing. Adding annual frequency analysis and a detailed trigger log helps researchers understand the reliability and seasonal clustering of the signals.

## What Changes

- **New Visualization**: Add a bar chart showing the count of signal triggers per year.
- **Detailed Export**: Export a full list of all signal trigger dates to a CSV/Excel file in the results directory.
- **Enhanced Reporting**: Ensure these artifacts are automatically generated during the backtest run and saved alongside existing performance plots.

## Capabilities

### New Capabilities
- `signal-distribution-stats`: Capability to aggregate signal triggers by year and produce frequency distributions and timestamp logs.

### Modified Capabilities
- `sparse-signal-testing`: Update the requirement for the testing engine to include supplementary signal statistics in its output pipeline.

## Impact

- `core/SparseSignalTester.py`: Main class to be updated with new plotting and exporting methods.
- `run_sparse_momentum_test.py`: Update the entry point to invoke these new reporting capabilities.
- `results/`: New files (plots and tables) will be generated here.
