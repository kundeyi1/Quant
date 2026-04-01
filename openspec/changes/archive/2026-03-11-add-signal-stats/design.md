## Context

The `SparseSignalTester` currently performs group performance analysis on discrete signal trigger points. While it can plot signals against a benchmark, it lacks quantitative summaries of signal frequency (e.g., how many signals occur each year) and a portable record of trigger events (e.g., a CSV log).

## Goals / Non-Goals

**Goals:**
- Provide a clear visualization of signal distribution across years.
- Generate a machine-readable log of all signal trigger dates.
- Ensure these features are modular and easily accessible from the main testing scripts.

**Non-Goals:**
- Modifying the core backtesting logic or performance calculation.
- Changing the existing visualization for group returns.

## Decisions

- **Decision 1: Annual Frequency Calculation**: Use `signal_series` or `trigger_dates` to group by `year`. 
    - *Rationale*: Pandas `resample` or `groupby(dt.year)` is efficient and standard for this task.
- **Decision 2: Visualization**: Implement `plot_annual_frequency` using a bar chart.
    - *Rationale*: A bar chart is the most intuitive way to show count per year.
- **Decision 3: Data Export**: Implement `export_trigger_log` to save trigger dates to a CSV file.
    - *Rationale*: CSV is universal and allows researchers to perform external validation or audits.
- **Decision 4: Integration**: Add these calls to `run_sparse_momentum_test.py` after the backtest execution.

## Risks / Trade-offs

- **[Risk]** Large number of signals → **[Mitigation]** The table output is a simple CSV which handles many rows easily; the bar chart naturally aggregates counts.
- **[Risk]** Alignment issues → **[Mitigation]** Ensure `self.trigger_dates` is strictly derived from the validated `signal_series` date index.
