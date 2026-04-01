# Tasks: add-signal-stats

## Phase 1: Update Core Tester
- [ ] Add `plot_annual_frequency` method to `core/SparseSignalTester.py`.
- [ ] Add `export_trigger_log` method to `core/SparseSignalTester.py`.

## Phase 2: Update Entry Point
- [ ] Add calls to `plot_annual_frequency` and `export_trigger_log` in `run_sparse_momentum_test.py`.
- [ ] Ensure `results/sparse_momentum_rebound` contains the new artifacts.

## Phase 3: Verification
- [ ] Run the test script and confirm the creation of `annual_signal_frequency.png`.
- [ ] Run the test script and confirm the creation of `signal_trigger_dates.csv`.
- [ ] Verify that the CSV contains all trigger dates and the plot correctly groups them.
