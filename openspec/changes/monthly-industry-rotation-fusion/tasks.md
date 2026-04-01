# Tasks for Monthly Industry Rotation Fusion

## Phase 1: Monthly Factor Generation Implementation [priority: high]
- [ ] Implement `MonthlyIndustryRotationFactor` class in `factors/monthly_rotation_factors.py`. [task_id: 101]
- [ ] Connect existing `SignalFilters` to scan trigger logic within 10-day lookback window. [task_id: 102]
- [ ] Apply 10-day half-life weighting: $w = 2^{-n/10}$. [task_id: 103]
- [ ] Generate monthly cross-sectional dataframe of rank-fused factors. [task_id: 104]

## Phase 2: Factor Export and Integration [priority: medium]
- [ ] Implement `save_factor_csv` function to export to `D:/DATA/factors`. [task_id: 201]
- [ ] Set exact filenames: `zxyjhy_gx_pit_mom_factor.csv` and `zxejhy_gx_pit_mom.csv`. [task_id: 202]

## Phase 3: Factor Evaluation & Visualization [priority: medium]
- [ ] Create `run_monthly_factor_evaluation.py` test script. [task_id: 301]
- [ ] Execute standard IC/Group analysis (using existing FactorTester framework). [task_id: 302]
- [ ] Plot Grouping Excess Return Bar Chart for the monthly factor model. [task_id: 303]
- [ ] Compare monthly factor performance with the previous event-driven results. [task_id: 304]
