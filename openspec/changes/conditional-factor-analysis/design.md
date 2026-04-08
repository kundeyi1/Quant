## Context
Current factor research in `FactorTester.py` and `FactorValidator.py` focuses on unconditional performance (all-market). To capture regime-specific alpha, we need a "Conditional Layer" that filters the universe based on `trigger_factors` (event/momentum) before evaluating `env_factors` (structural/context).

## Goals / Non-Goals

**Goals:**
- Implement a 7-step stratified testing pipeline: Score -> Event -> Filter -> Conditional Grouping -> Return Calculation -> Stability Control -> Summary.
- Support both 1d and 5d future returns for sensitivity analysis.
- Ensure cross-sectional consistency by calculating ranks/quantiles within the filtered sub-sample (not the full market).
- Provide stability guards (minimum samples per date/group).

**Non-Goals:**
- Real-time trading engine integration.
- Non-linear conditional modeling (e.g., machine learning trees); focusing on stratified linear analysis first.
- Automated parameter optimization (e.g., searching for the best trigger quantile).

## Decisions

- **Standalone Research Script**: Implement as a standalone research file `run_conditional_alpha_research.py` instead of a core module. Rationale: The methodology is specific to this research session, keeps the core cleaner, and allows for easier debugging.
- **Cross-sectional Logic**: Use `groupby(level='date')` for all ranking and quantile operations to ensure zero look-ahead bias and capture relative strength within the filtered universe.
- **Stability Guard**: Drop dates with `< 30` samples. Rationale: Prevents noise from small samples (e.g., extreme market conditions or data gaps) from skewing the mean return.
- **Return Handling**: Pass `future_return` as pre-aligned Series or DataFrames to maintain consistency with `FactorTester`.

## Risks / Trade-offs

- **[Risk] Sample Size → Mitigation**: As we filter by top 30% triggers and then split into 5 env bins, the final bin size could be very small (e.g., ~6 stocks in a 100-stock universe). Mitigation: Implement the `min_samples` guard and report sample counts.
- **[Risk] Survival Bias → Mitigation**: Ensure filtering is done using lagged or "Today" triggers relative to the trading window, and returns are truly forward-looking.
