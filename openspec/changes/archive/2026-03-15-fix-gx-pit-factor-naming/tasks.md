<artifact id="tasks" change="fix-gx-pit-factor-naming" schema="spec-driven"> 

## 1. Implement Factor Saving Logic in GX PIT Scripts

- [x] 1.1 Update `run_gx_pit_breakout_test.py`: Ensure signal Series name is `gx_pit_mom_breakout` and file is saved accordingly.
- [x] 1.2 Update `run_gx_pit_rebound_test.py`: Ensure signal Series name is `gx_pit_mom_rebound` and file is saved accordingly.
- [x] 1.3 Update `run_gx_pit_rotation_test.py`: Ensure signal Series name is `gx_pit_mom_rotation` and file is saved accordingly.
- [x] 1.4 Standardize internal column name to `factor` where applicable in the saved DataFrames.

## 2. Directory Management

- [x] 2.1 Ensure all 3 scripts use `os.makedirs("D:/DATA/SPARSE_FACTOR", exist_ok=True)` for absolute path or relevant relative path.

## 3. Validation and Regression

- [x] 3.1 Run `run_gx_pit_breakout_test.py` and verify `SparseSignalTester` loads the factor correctly without `FileNotFoundError`.
- [x] 3.2 Verify other 2 scripts follow the same success pattern.

</artifact>