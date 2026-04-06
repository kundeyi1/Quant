## Why

现有代码中，三角形突破、大跌反弹和行情转折（切换）三种策略的择时逻辑与因子测试逻辑高度耦合，且散落在 `run_gx_pit_breakout_test.py`、`run_gx_pit_rebound_test.py` 和 `run_gx_pit_rotation_test.py` 三个文件中。这种结构导致了代码冗余、难以维护，且无法高效地进行综合策略回测。现在需要将择时逻辑独立出来，并对计算流程进行标准化。

## What Changes

- **择时信号分离**: 从现有文件中提取择时计算逻辑，将生成的 0/1 择时序列（带日期戳和开始结束时间）持久化至 `D:\DATA\TIMING` 目录。
- **模块整合**: 创建统一的 `gx_pit_mom.py` 文件，整合三种信号的计算与测试流程。
- **架构升级**:
  - 支持一次运行多种（或全部）信号。
  - 外部可配置行业定义（一级/二级）。
  - 实现“计算前检查”：若目标路径已存在对应的信号文件，则跳过计算以节省时间。
- **数据管理**: 所有保存的数据名称必须包含明确的 `start_date` 和 `end_date` 信息。

## Capabilities

### New Capabilities
- `gx-pit-mom-framework`: 统一的国信时点动量策略框架，支持多信号并发运行与行业中性配置。
- `timing-persistence`: 择时信号的标准化持久化与加载机制。

### Modified Capabilities
- `market-timing`: 增强现有的择时算子，确保输出符合新的持久化规范。
- `sparse-signal-testing`: 优化稀疏信号测试逻辑，适配整合后的框架。

## Impact

- **受影响代码**: `run_gx_pit_breakout_test.py`, `run_gx_pit_rebound_test.py`, `run_gx_pit_rotation_test.py` (将被替代或重构)。
- **新文件**: `gx_pit_mom.py`。
- **目录结构**: `D:\DATA\TIMING` (新存储路径)。
- **依赖关系**: 依赖 `core.DataManager`, `core.SparseSignalTester`, `timing.market_timing`。
