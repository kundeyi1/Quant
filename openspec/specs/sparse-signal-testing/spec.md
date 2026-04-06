# sparse-signal-testing Specification

## Purpose
TBD - created by archiving change sparse-rebound-momentum-test. Update Purpose after archive.
## Requirements
### Requirement: 稀疏信号对齐与提取
系统必须（SHALL）能够读取外部指数数据（如中证 500）生成的 0-1 掩码序列，并根据该序列的触发时点（值为 1 的日期），精准提取所有行业标在该日期的截面因子值。

#### Scenario: 跨资产日期对齐
- **WHEN** 指数数据在 2024-01-05 触发反弹信号，但某行业在该日停牌或缺少数据。
- **THEN** 系统必须通过 `reindex` 或 `merge` 确保信号日期与行业数据完全对齐，缺失行业在统计中应被标记为 NaN 或排除。

#### Scenario: 稀疏因子强度保留
- **WHEN** 从外部加载以 `.parquet` 格式存储的稀疏因子时
- **THEN** 系统 SHALL 严格保留原始 `NaN` 分数，不得将其误识别为 `0` 或进行任何自动填补。

### Requirement: Sparse Signal Handling and Input Restraints
The `SparseSignalTester` SHALL focus primarily on analyzing cross-sectional quantile distributions or raw continuous scalar outputs, evaluating numerical correlations with future returns across `n_groups`.

#### Scenario: Sparse Signal Separation
- **WHEN** the `SparseSignalTester` encounters continuous distributions or ranked factor vectors
- **THEN** it MUST perform standard rank-based slicing or numerical correlation checks instead of drawing net-liquidations for 0/1 discrete sequences.

### Requirement: 使用 SparseSignalTester 执行回测评估
系统 MUST 支持以生成的信号 DataFrame 输入给现有的 `core/SparseSignalTester.py` 进行信号触发回测，而不需要也不使用之前独立在 `quant_timing_system` 中分离实现的回溯循环代码。

#### Scenario: 执行稀疏时间轴回测
- **WHEN** `run_huatai_timing_reproduction.py` 传入生成的华泰综合打分信号向量并执行 `SparseSignalTester.backtest()`（或相关功能函数）时
- **THEN** 系统正常运算，考虑稀疏离散的入场/出场或多空信号状态，统计出回测的核心业务绩效（多头年化、空头表现、最大回撤等），且无执行崩溃。

### Requirement: Default Directory Handling
The `SparseSignalTester` MUST default its `output_dir` property or default behaviors to store standard numerical factor evaluation checks into `results/sparse_signal` instead of generic `results/`.

#### Scenario: Verify factor evaluation output location
- **WHEN** the user calls `tester.run_timing_analysis(period=20)` on numerical vectors
- **THEN** the plots (e.g. `timing_effectiveness_dist.png`) are saved safely within `results/sparse_signal/` unless an override is provided.

### Requirement: Wind 格式索引文件读取
系统必须（SHALL）能够读取位于 `D:/DATA/INDEX/ZX/ZX_YJHY.csv` 的中信一级行业指数，该文件采用 Wind 导出格式。读取时系统 MUST 使用 `core.DataManager` 的 Wind 解析器或等效接口将原始字段映射到统一的 OHLCV 列 (`open, high, low, close, volume`) 并以日期为索引返回。

#### Scenario: Wind 文件解析
- **WHEN** 输入文件 `D:/DATA/INDEX/ZX/ZX_YJHY.csv` 包含 Wind 风格列名（例如 `TRADE_DT`, `S_INFO_WINDCODE`, `S_DQ_CLOSE` 等）
- **THEN** `core.DataManager` MUST 成功映射并返回标准 DataFrame；若关键列缺失或格式错误，系统 MUST 抛出描述性错误并记录该文件路径以便运维修正。

### Requirement: 阶梯式分组动量计算
系统必须（SHALL）计算触发日各行业的 `calculate_gx_momentum_factor`，并根据该因子值由高到低将行业划分为 N 个组别（默认 3-5 组）。

#### Scenario: 行业分组逻辑验证
- **WHEN** 触发日共有 30 个中信一级行业，设定分组数为 5。
- **THEN** 系统必须将这 30 个行业按动量因子排序，每 6 个行业分配到一组（Group 1 为动量最强组）。

### Requirement: Multi-Metric Analysis
The testing engine SHALL provide a comprehensive view of factor performance, including group metrics and the distribution of trigger points.

#### Scenario: Visualizing Distribution alongside Results
- **WHEN** the user runs a backtest with `SparseSignalTester`
- **THEN** it SHALL be possible to call the reporting methods to gain insights into signal frequency.

### Requirement: 信号后向累积收益统计
系统必须（SHALL）跟踪每个信号日之后固定窗口（如 T+20）的标的或组合收益。该逻辑 SHALL 与 `run_backtest` 回测主逻辑解耦，直接供 `run_timing_analysis` 调用。

#### Scenario: T+20 累加收益与基准对比
- **WHEN** 信号在 T 日触发，基准集合包含 `000985.CSI` 所有有效 T 日的 $period$ 持有期收益。
- **THEN** 系统计算信号点的均值收益、Quantile Rank，并执行相对于 `000985.CSI` 总体分布的显著性检验。

### Requirement: 信号发生时点可视化
系统必须（SHALL）能够将原始时间序列（如中证500净值或收盘价轨迹）与生成的掩码信号叠加显示。对于每一个触发日，图表中必须以垂直虚线（VLine）的形式标识出具体的信号触发位置。

#### Scenario: 掩码触发位标记
- **WHEN** 在 2024 年内共有三次反弹信号触发。
- **THEN** 生成s的折线图中必须显示 2024 全年价格曲线，并在这三个触发点所在的日期轴位置绘制明显的红色虚线。

### Requirement: 动量分组收益分布可视化
系统必须（SHALL）生成一个柱状图（Bar Chart），参考 `FactorTester` 风格，展示不同动量分组在持有期（T+20）内的平均累积收益率。

#### Scenario: 分组条形图绘制
- **WHEN** 行业被分为 5 组进行动量测试。
- **THEN** 系统必须生成一张包含 5 个柱子的直方图，横轴表示 Group 1-5，纵轴表示各组的平均百分比收益，用于直观评估因子的单调性。

### Requirement: 增强收益展示逻辑
系统 SHALL 在原有的分组收益统计基础上，支持多空对冲收益及非连续信号段拼接。

#### Scenario: 自动拼接无信号时间
- **WHEN**: 策略在不同时间段触发信号，存在长达数月的无信号间隙。
- **THEN**: 系统 SHALL 在绘图时将无信号期间排除，通过索引重排实现 X 轴的无缝拼接。

### Requirement: 统计指标增强
系统 SHALL 包含 IC/IR、年化波动率和各分组超额收益分布。

#### Scenario: 分组超额收益可视化
- **WHEN**: 回测报告生成时。
- **THEN**: 系统 SHALL 增加一个柱状图（Bar Chart），显示 Group 1 到 Group N 的累积平均超额收益分布。

### Requirement: 稀疏样本绩效聚合
系统必须（SHALL）对所有历史触发点的测试结果进行聚合统计，包括各组的平均持有期收益、胜率（收益 > 0 的比例）以及相对于基准（指数平均水平）的超额收益。

#### Scenario: 聚合结果展示
- **WHEN** 历史上一共出现了 10 次反弹触发信号。
- **THEN** 系统必须输出各分组在 10 次事件中的平均表现，并生成包含累计收益曲线（多头对比空头或基准）的可视化报告。

### Requirement: Multi-strategy execution framework
系统必须（SHALL）允许在单个运行入口（`gx_pit_mom.py`）中配置并运行多个 PIT 动量信号组合。

#### Scenario: Run all signals with ejhy
- **WHEN** 用户在 `gx_pit_mom.py` 中选择运行 `['breakout', 'rebound', 'rotation']` 且行业设定为 `ejhy`
- **THEN** 系统按序处理三种信号的择时计算与稀疏因子测试

### Requirement: 独立择时分析接口
系统必须（SHALL）提供独立的公有方法，接受基准序列（如 `000985.CSI`）和持有期，返回择时显著性统计汇报。

#### Scenario: 独立调用分析
- **WHEN** 用户在完成 `run_backtest` 之后。
- **THEN** 用户手动调用 `run_timing_analysis(period=20, benchmark_series=index_000985)`，系统将在方法内部直接计算 `000985.CSI` 的全样本滚动持有期收益，并对比信号点的表现。

### Requirement: 基于 000985.CSI 的全样本基准分布
系统必须（SHALL）以 `D:/DATA/INDEX/STOCK/000985.CSI.xlsx` 的全样本滚动持有期收益作为背景分布基准。

#### Scenario: 分布对比图表绘制
- **WHEN** 调用 `SparseSignalTester` 的择时分析接口。
- **THEN** 生成一张分布密度图，展示信号触发收益在 `000985.CSI` 全样本分布中的相对位置（Quantile Rank）。

### Requirement: Sparse Signal Day Momentum Alignment
The system MUST allow using the historical return of assets on the EXACT date of the timing trigger as the cross-sectional momentum metric.

#### Scenario: Signal Day Weight Assignment
- **WHEN** a timing trigger is identified on date T
- **THEN** the sector rotation engine SHALL extract the daily returns of all industries on date T and use them for rank-based grouping (Long/Short)

### Requirement: Standardized Performance Export
The system SHALL automate the generation of evaluation reports for sparse timing-momentum signals.

#### Scenario: Report Generation in results/timing
- **WHEN** the backtest is complete
- **THEN** it SHALL export a CSV summary and a dual-axis NAV/Drawdown chart to the specified directory

