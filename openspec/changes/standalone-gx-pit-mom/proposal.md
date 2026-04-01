## Why

The current `gx_pit_mom.py` script and its associated logic (timing, data management, indicators) are spread across multiple files and directories. This makes it difficult to migrate or deploy the strategy to other environments without bringing the entire repository structure. A standalone, self-contained script is required for easier distribution and automated execution in production-like environments.

## What Changes

- **Consolidation**: Create `standalone_gx_pit_mom.py` by merging essential logic from `gx_pit_mom.py`, `core/DataManager.py`, `timing/report_timing.py`, `factors/technical_factors.py`, and `core/NumericalOperators.py`.
- **Feature Pruning**: Remove all backtesting, visualization, and performance reporting code (e.g., `SparseSignalTester`, `plot_signals`, `plot_group_returns`, `print_performance_report`).
- **Automation Logic**: Implement a check to compare the latest date in the existing factor data with a provided "current date". If the factor data is outdated, trigger a full re-calculation.
- **Output Optimization**: Ensure the final output is saved in a format where:
    - Results are sorted by date in descending order (newest first).
    - Within each date, factors are sorted by value in descending order.
- **Dependency Reduction**: Replace the custom `Logger` with a standard `logging` setup and simplify `DataProvider` to basic file operations.

## Capabilities

### New Capabilities
- `standalone-script-bundle`: High-level capability for the single-file distribution and execution logic.
- `automatic-outdated-check`: Logic to verify if re-calculation is needed based on the latest factor timestamp and target date.
- `sorted-data-export`: Specialized export functionality ensuring the double-sorting requirement (Date DESC, Factor DESC).

### Modified Capabilities
- `gx-pit-mom-refactor`: Adapting the existing calculation logic from the original `gx_pit_mom.py` and its dependencies into the new structure.

## Impact

- **New Files**: `standalone_gx_pit_mom.py` (the consolidated script).
- **APIs**: The standalone script will likely expose a simplified CLI or function interface for the migration environment.
- **Dependencies**: No new external dependencies; the script will rely only on standard scientific Python stack (pandas, numpy, etc.).
