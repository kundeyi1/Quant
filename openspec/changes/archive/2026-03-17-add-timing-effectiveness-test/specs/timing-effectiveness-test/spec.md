## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: 信号后向累积收益统计
系统必须（SHALL）跟踪每个信号日之后固定窗口（如 T+20）的标的或组合收益。该逻辑 SHALL 与 `run_backtest` 回测主逻辑解耦，直接供 `run_timing_analysis` 调用。

#### Scenario: T+20 累加收益与基准对比
- **WHEN** 信号在 T 日触发，基准集合包含 `000985.CSI` 所有有效 T 日的 $period$ 持有期收益。
- **THEN** 系统计算信号点的均值收益、Quantile Rank，并执行相对于 `000985.CSI` 总体分布的显著性检验。
