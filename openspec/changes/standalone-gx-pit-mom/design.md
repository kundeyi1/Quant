## Context

- The currently exists `gx_pit_mom.py` is part of a larger project and relies on `core/DataManager.py`, `timing/report_timing.py`, `factors/technical_factors.py`, and `core/NumericalOperators.py`.
- Users want to use the factor calculation and signal generation logic in a standalone environment without maintaining the original repository structure.
- The target environment might not have access to specific local modules but will have common data libraries (pandas, numpy).

## Goals / Non-Goals

**Goals:**
- Single-file execution: All required logic (data loading, indicator calculation, signal generation) bundled into `standalone_gx_pit_mom.py`.
- Automated update: The script checks the latest file date vs. a given "current date" and decides whether to re-run.
- Data ordering: Final output must be sorted by `date` (DESC) and then `factor_value` (DESC).
- Zero-backtest: Completely strip out `SparseSignalTester` and visualization components.

**Non-Goals:**
- Generic framework: Not building a generalized bundling tool, only supporting this specific strategy.
- Web or DB integration: The output stays as local files (e.g., CSV or Parquet).

## Decisions

- **Indicator Logic Porting**: Move the necessary logic from `NumericalOperators` (e.g., `ts_rank`, `ts_corr`) and `technical_factors` (specifically `gx_atr_factor`) directly into private methods or a helper class within the standalone script.
- **Timing Logic Porting**: Extract `gx_pit_breakout`, `gx_pit_rebound`, and `gx_pit_rotation` from `timing/report_timing.py` into the standalone file.
- **Conditional Run Check**: The script will take a `--target_date` (or use system date) and a `--output_path`. Before calculating, it loads the existing output and compares `max(date)` with `target_date`.
- **Data Pruning/Loading**: Hardcode or provide parameters for `D:/DATA` as the base directory, but make it easier to point elsewhere if the migration environment uses a different structure.

## Risks / Trade-offs

- **[Risk] Code Duplication**: Duplicating logic into a standalone file means any bug fix in the core repo needs to be manually ported to the standalone version. → *Mitigation*: Clearly mark the origin of the logic and keep it as simple as possible.
- **[Risk] Library Versions**: The migration environment may have different versions of pandas/numpy. → *Mitigation*: Stick to stable, widely-used pandas indexing and slicing APIs.
- **[Risk] Large File Size**: Bundling everything could lead to a very large script. → *Mitigation*: Only include *exactly* what is needed for the calculation and skip large, unused parts of the source modules.
