## ADDED Requirements

### Requirement: Timing Analysis Function Migration
`TimingTester` 必须能够承载原属于 `SparseSignalTester` 的择时分析能力。

#### Scenario: Successful migration of plot functions
- **WHEN** user calls `TimingTester.plot_timing_distribution()`
- **THEN** system generates a distribution plot identical to the previous implementation in `SparseSignalTester`.

### Requirement: Multi-Source Signal Integration
`GXPITMomTester` 必须能够从 `report_timing.py` 和 `pattern_timing.py` 动态加载和调用信号函数。

#### Scenario: Registering new technical timing signal
- **WHEN** user configuration includes `ht_rsrs`
- **THEN** system successfully invokes `report_timing.ht_rsrs_timing()` and returns a binary 0/1 signal matrix.

### Requirement: Single-Point Signal Performance Evaluation
系统必须能够独立评价每一个时点信号的有效性。

#### Scenario: Evaluating HT-RSRS signal
- **WHEN** user requests evaluation for `ht_rsrs` on 000985
- **THEN** system outputs accuracy, profit-loss ratio, and holding period return distribution specifically for the HTRSRS trigger points.

### Requirement: Fused Signal Set Evaluation
系统必须能够评价所有信号融合（Logical OR 之后）构成的密集信号集的整体表现。

#### Scenario: Evaluating the expanded signal ensemble
- **WHEN** all selected signals are fused into a single trigger stream
- **THEN** system generates a collective performance report showing turnover, coverage frequency, and aggregated returns.
