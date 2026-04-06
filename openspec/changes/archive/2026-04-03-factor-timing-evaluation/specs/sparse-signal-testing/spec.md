## MODIFIED Requirements

### Requirement: Sparse Signal Handling and Input Restraints
The `SparseSignalTester` SHALL focus primarily on analyzing cross-sectional quantile distributions or raw continuous scalar outputs, evaluating numerical correlations with future returns across `n_groups`.

#### Scenario: Sparse Signal Separation
- **WHEN** the `SparseSignalTester` encounters continuous distributions or ranked factor vectors
- **THEN** it MUST perform standard rank-based slicing or numerical correlation checks instead of drawing net-liquidations for 0/1 discrete sequences.

### Requirement: Default Directory Handling
The `SparseSignalTester` MUST default its `output_dir` property or default behaviors to store standard numerical factor evaluation checks into `results/sparse_signal` instead of generic `results/`.

#### Scenario: Verify factor evaluation output location
- **WHEN** the user calls `tester.run_timing_analysis(period=20)` on numerical vectors
- **THEN** the plots (e.g. `timing_effectiveness_dist.png`) are saved safely within `results/sparse_signal/` unless an override is provided.