## 1. Setup & Utilities

- [x] 1.1 Create `standalone_gx_pit_mom.py` with standard library imports (`os`, `sys`, `pandas`, `numpy`, `logging`, `pathlib`).
- [x] 1.2 Implement a simplified `DataProvider` class or equivalent directly into the script to handle `D:/DATA` pathing and file reading (Excel/Parquet).
- [x] 1.3 Port necessary numerical operators (`ts_rank`, `ts_corr`, etc.) from `core/NumericalOperators.py` into the script as private methods or a helper class.

## 2. Core Indicator & Timing Logic

- [x] 2.1 Port `gx_atr_factor` logic from `factors/technical_factors.py` into the standalone script.
- [x] 2.2 Port `gx_pit_breakout`, `gx_pit_rebound`, `gx_pit_rotation`, and `_standardize_input` from `timing/report_timing.py`.
- [x] 2.3 Consolidate the `GXPITMomTester` logic into a single class or set of functions, focusing only on the data loading and factor calculation.

## 3. Automation & Export Logic

- [x] 3.1 Implement the `check_outdated_data` logic to verify the latest date in the target output file against a given "current date".
- [x] 3.2 Implement a `prepare_and_save_results` function that sorts data by date (DESC) and factor value (DESC) before exporting to Parquet/CSV.
- [x] 3.3 Add a CLI interface using `argparse` to allow users to specify `--target_date`, `--sector`, and `--output_path`.

## 4. Verification & Validation

- [x] 4.1 Validate the logic by running the standalone script against the local `D:/DATA` environment and comparing outputs with the original `gx_pit_mom.py` results.
- [x] 4.2 Run static code analysis (pylint/flake8) on the new single-file script to ensure there are no lingering dependencies or syntax errors.
