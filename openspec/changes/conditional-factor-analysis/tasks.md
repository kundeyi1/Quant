## 1. Research Script Setup

- [x] 1.1 Create `run_conditional_alpha_research.py` with necessary imports.
- [x] 1.2 Implement `compute_trigger_score(factors_df, trigger_list)` within the script.
- [x] 1.3 Implement `get_trigger_event(trigger_score, quantile=0.7)` within the script.

## 2. Core Analysis Logic

- [x] 2.1 Implement `conditional_factor_test(factors_df, future_return, env_factor, trigger_event)` to filter and re-rank.
- [x] 2.2 Implement `run_all_env_tests(factors_df, future_return, env_list, trigger_event)` to orchestrate the test loop.
- [x] 2.3 Integrate `FactorTester` for loading returns if needed or use pre-loaded data.

## 3. Integration and Reporting

- [ ] 3.1 Create a new test script `run_conditional_factor_analysis.py` to load data from `D:/DATA/FACTORS` and execute the pipeline.
- [ ] 3.2 Add formatting logic to print the long-short return leaderboard and detailed stratified tables for sample factors.
- [ ] 3.3 Validate results by comparing unconditional vs. conditional performance for a single factor (e.g., `Volat_Compression_Lag1`).

## 4. Documentation and Finalization

- [ ] 4.1 Add docstrings explaining the 7-step logic to all functions.
- [ ] 4.2 Record insights on which `env_factors` act as the best filters under specific conditions.
- [ ] 4.3 Clean up any temporary trial scripts.
