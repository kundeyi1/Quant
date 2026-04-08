## Why
Standard factor evaluation often ignores structural context, leading to "diluted" alpha signals. This change introduces a conditional testing framework to evaluate if `env_factors` (structural) exhibit stronger predictive power specifically when `trigger_factors` (momentum/event) are active.

## What Changes
- New `ConditionalTester` utility functions to implement the 7-step stratified testing logic.
- Support for cross-sectional standardization (z-score/rank) and quantile-based event triggering.
- Stability controls for minimum sample sizes per date and per group.
- Automated reporting for conditional long-short returns and stratified performance tables.

## Capabilities
### New Capabilities
- `conditional-alpha-testing`: Framework for E[return | trigger, factor] analysis.

## Impact
- `factors/combination.py`: Potential location for the new logic or a new dedicated module.
- `run_factor_combination.py`: Integration point for the new experiments.
