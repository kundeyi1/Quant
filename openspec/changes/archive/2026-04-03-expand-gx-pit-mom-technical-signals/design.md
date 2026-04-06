## Context

当前的 `gx_pit_mom.py` 择时逻辑主要基于单一的时间窗口形态。目前的测试脚本 `run_momentum_sensitivity_test.py` 已经验证了“物理形态 setup + 3% 动量反转”的两步法（Two-Stage）具备更高的信号质量。需要将这些散落在脚本中的逻辑整合进一个正式的库，并创建统一的测试入口 `pit_mom.py`。

## Goals / Non-Goals

**Goals:**
- **解耦计算逻辑**：将 `PriceFactors`, `VolumeFactors`, `TrendFactors` 的静态方法作为底层计算库。
- **标准化两阶段引擎**：实现一个通用的 `calculate_two_stage_timing(setup_df, confirm_threshold=0.03)` 系统。
- **行业动态权重**：支持以信号触发日（Day T）的各行业全天收益率作为动量权重进行排序。
- **中信一级/二级支持**：通过 `sector_type` 参数无缝切换数据源。

**Non-Goals:**
- **分钟级支持**：本设计仅限于日线级别择时。
- **机器学习集成**：暂不引入复杂的模型，仅基于硬阈值（Hard Thresholds）进行物理择时。

## Decisions

### 1. 物理因子 vs 分位数排名
**Decision**: 统一采用绝对物理数值。
**Rationale**: `gx_pit_mom` 回测在不同震荡幅度下，分位数会失效。物理指标（如缩缩量到均量的 0.7 倍）对市场强度的描述更本质且在不同市况下更具通用性。
**Constraint**: 为了保持库文件的纯净，所有新增的物理指标逻辑、两阶段触发引擎及行业权重分配逻辑**必须完全内建于 `pit_mom.py` 文件中**，严禁修改 `core/`, `factors/` 或 `timing/` 文件夹下的任何现有代码。

### 2. 两阶段确认逻辑 (Setup + Confirmation)
**Decision**: 择时信号 = `(Physical Setup == 1) & (Index_Daily_Return > 0.03)`。
**Rationale**: 防止由于极端的“惯性下跌”或“假突破”造成的地量或价格形态失效，确认涨幅代表市场合力的转向。
**Implementation**: `pit_mom.py` 将包含一个私有方法或内部类来定义这些因子计算逻辑，它将直接从 `DataManager` 获取原始数据进行计算。

### 3. 系统等效性 (Equivalence)
**Decision**: 仅修改触发点处的标的选择逻辑。
**Rationale**: 确保 `pit_mom.py` 的测试框架在回测架构上与 `gx_pit_mom.py` 完全对标。除触发点产生的动量排序及行业分配外，其余时间轴上的状态处理（如基准对齐、手续费处理、空仓逻辑）必须与原文件保持 100% 一致。

## Risks / Trade-offs

- **[Risk] 信号稀疏性**：3% 的确认门槛可能导致信号很少。
- **[Mitigation]**: 支持在 `pit_mom.py` 中通过参数动态调整动量确认阈值。
- **[Risk] 中信二级行业计算时间**：二级行业文件较大。
- **[Mitigation]**: 沿用现有 `DataManager` 的宽表加载机制，确保持久化 Parquet 格式以加快读取。
