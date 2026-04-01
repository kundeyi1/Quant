## 1. Directory & Tester Initialization

- [x] 1.1 Create `results/factor`, `results/sparse_signal` and `results/timing` directories if they do not exist.
- [x] 1.2 Modify `core.SparseSignalTester.__init__` to route default output logs/plots to `results/sparse_signal` rather than generic `results/` or current `.`.
- [x] 1.3 Modify `core.FactorTester.__init__` (if applicable) to route generic continuous factor evaluations/metrics into `results/factor`.
- [x] 1.4 Create `core/TimingTester.py` containing the `TimingTester` class.
- [x] 1.5 Add `TimingTester` export to `core/__init__.py`.

## 2. Core Implementation: TimingTester

- [x] 2.1 Implement `TimingTester.__init__` accepting `signal_series` (or `signal_matrix`), `benchmark_series`, and `output_dir="results/timing"`. 
- [x] 2.2 Implement net-NAV calculation logic `calculate_timing_nav()` returning cumulative portfolio net value driven by discrete 0/1 signals compared to a normalized benchmark.
- [x] 2.3 Implement the `plot_timing_nav_and_drawdown` function. Extract normalized NAV arrays and plot NAV (red/darkred), Benchmark (darkblue), and plot drawdowns on a secondary y-axis using `fill_between` (lightgrey area).
- [x] 2.4 Handle Chinese font support (`plt.rcParams['font.sans-serif'] = ['SimHei']` or similar fallback) within the plot function.

## 3. Script Migration and Clean up

- [x] 3.1 Update `run_ht_timing.py` to import and utilize `core.TimingTester` for analyzing `calculate_ht_integrated_timing` discrete 0/1 predictions.
- [x] 3.2 Guarantee `run_ht_timing.py` generates output plots via `plot_timing_nav_and_drawdown` seamlessly into `results/timing`.
- [x] 3.3 Identify and strip out exclusively 0/1 timing drawing/business functions from `SparseSignalTester` if they severely conflict with numerical feature testing, or wrap them gently.

## 4. Verification

- [x] 4.1 Run `run_ht_timing.py` completely and verify it places a dual-axis line/shadow chart (`布林带_择时净值.png` or named accordingly) in `results/timing`.
- [x] 4.2 Verify other regular standard Factor tests implicitly route through `SparseSignalTester` to `results/sparse_signal`.