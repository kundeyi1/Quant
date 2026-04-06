## Context

当前择时信号计算（`breakout`, `rebound`, `rotation`）与特定的策略回测脚本强耦合。每个脚本都重复加载数据、计算信号，并且没有标准化的信号持久化机制。这不仅导致计算资源浪费，也使得信号无法在不同策略间共享。

## Goals / Non-Goals

**Goals:**
- **解耦计算与应用**: 将择时信号计算逻辑移至专用模块，并支持独立保存。
- **标准化存储**: 使用 `D:\DATA\TIMING` 作为择时信号基准目录，文件名包含信号类型、参数及起止日期。
- **幂等性设计**: 实现“存在即跳过”的逻辑（计算前检查文件是否存在）。
- **统一接口**: `gx_pit_mom.py` 作为入口点，支持配置化批量运行。

**Non-Goals:**
- 修改 `timing/market_timing.py` 中的核心算法逻辑（除非为了适配新接口）。
- 重构 `core/SparseSignalTester.py` 的核心测试流程。

## Decisions

1. **持久化格式与路径**:
   - 路径: `D:\DATA\TIMING/{signal_type}_{params}_{start}_{end}.parquet`。
   - 格式: Parquet，保留时间序列索引。
   - Rationale: Parquet 读写高效且类型安全；文件名包含起止日期能有效管理不同时间窗口的实验。

2. **`gx_pit_mom.py` 架构**:
   - 实现一个类或函数集，接受 `signals_to_run` 列表（例如 `['breakout', 'rebound']`）。
   - 内部逻辑：检查存储 -> 若不存在则调用 `market_timing.<func>` -> 保存至 `TIMING` -> 衔接稀疏信号测试。
   - 行业配置：接受 `sector_type` (ejhy/yjhy) 参数。

3. **Sparse Signal 处理**:
   - 独立保存计算出的稀疏信号到 `D:/DATA/SPARSE_SIGNAL`，同样遵循“存在即跳过”原则。

## Risks / Trade-offs

- **[Risk] 文件名冲突**: 复杂的参数组合可能导致文件名过长或难以解析。
  - **Mitigation**: 使用标准化的命名模板，且日期格式固定为 `YYYYMMDD`。
- **[Trade-off] 数据冗余**: 如果起止日期略有重合，可能会生成多个文件。
  - **Mitigation**: 优先建议拉取最长的时间范围进行计算，或者在加载时检查包含关系。
