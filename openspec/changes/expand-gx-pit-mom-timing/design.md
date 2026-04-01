## Context
当前量化研究框架中，择时系统（Timing）和稀疏信号因子系统（Sparse Signal）的分析逻辑存在耦合。`SparseSignalTester` 目前承担了过多的择时验证职责，而 `TimingTester` 功能相对薄弱。通过本次重构，我们将实现“择时归择时，因子归因子”的可扩展架构，并提升信号搜索的广度。

## Goals / Non-Goals

**Goals:**
- **职责解耦**: 将 `SparseSignalTester` 中关于择时（0/1 信号）的评价函数迁移至 `TimingTester`。
- **信号矩阵扩展**: 扩展 `GXPITMomTester`，使其能够支持接入华泰技术指标库和形态学逻辑。
- **性能评价体系**: 在 `TimingTester` 中建立标准化的“单点信号”与“组合信号”绩效评价体系（胜率、盈亏比、持有期分布等）。
- **回测基准**: 统一在 000985（中证全指）上进行所有择时信号的检验。

**Non-Goals:**
- 不调整现有的 `half_life` 衰减参数。
- 不修改 `SparseSignalTester` 的截面分组回测核心逻辑（仅迁移函数）。
- 不处理非稀疏的连续因子。

## Decisions

### 1. 架构重构：分析逻辑迁移
- **决策**: 将 `plot_timing_distribution`, `plot_signals`, `plot_annual_frequency`, `export_trigger_log` 从 `SparseSignalTester` 迁移至 `core/TimingTester.py`。
- **理由**: 提高代码内聚性。择时分析关注的是“什么时候买（When）”，而稀疏因子分析关注的是“在触发时买什么（What）”。

### 2. GXPITMomTester 信号接入方式
- **决策**: 采用 Registry 模式或动态分发逻辑，参考 `gx_pit_mom` 的函数结构，自动加载 `timing/report_timing.py` 和 `timing/pattern_timing.py` 中的函数。
- **理由**: 方便后续持续增加新的择时因子，无需频繁修改主类逻辑。

### 3. 持久化与缓存
- **决策**: 维持现有的 `.parquet` 缓存机制。
- **理由**: 避免大样本量下的重复计算，兼容现有 DataProvider 体系。

## Risks / Trade-offs

- **[Risk] 迁移导致回溯兼容性问题** → **Mitigation**: 在 `SparseSignalTester` 中保留对原函数的包装（Wrapper）或导入指向，直到所有调用方完成迁移。
- **[Risk] 信号量过大导致内存压力** → **Mitigation**: 采用生成器加载或按需计算，不一次性加载所有 Sector 的所有信号。
- **[Risk] 绩效评价指标不统一** → **Mitigation**: 在 `TimingTester` 中定义标准的 `PerformanceReport` 数据结构。
