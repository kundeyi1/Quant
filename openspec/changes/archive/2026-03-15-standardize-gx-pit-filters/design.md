## Context

目前 [filters/signal_filters.py](filters/signal_filters.py) 中的 GX PIT 过滤器实现分散，导致维护困难和逻辑不统一。特别是 ATR 动态阈值调整逻辑在多个方法中重复，且输入数据的适配（OHLC vs 宽表）缺乏统一标准。

## Goals / Non-Goals

**Goals:**
- **消除冗余 ATR 过滤器**: 移除单独的 `atr_volatility_filter` 公共静态方法，将其逻辑按需植入到各 PIT 过滤器内部实现中。
- **抽象数据适配器**: 引入 `_standardize_ohlc_input` 处理不同数据格式。
- **统一阈值缩放算法**: 所有的 GX PIT 过滤器必须通过同一个缩放函数 `_calculate_atr_scale` 来获取系数。

**Non-Goals:**
- 不涉及 `RiskFactors` 内部逻辑的修改。

## Decisions

### 1. 移除独立 ATR 过滤器
- **Rationale**: 作为一个“Signal Filter”库，ATR 的原始数值计算应主要由 `RiskFactors` 处理，而 `SignalFilters` 中的 ATR 过滤器应当是作为 PIT 信号的一个逻辑子集或前置依赖，不应作为顶级入口暴露以避免混淆。
- **Decision**: 完全移除 `atr_volatility_filter` 外部接口，逻辑整合进具体过滤器中。

### 2. 标准化输入处理器
- **Rationale**: GX PIT 信号有时基于个股 OHLC，有时基于行业指数（仅有收盘价）。为了保持逻辑复用，需要一种对齐方式。
- **Decision**: 统一检查 DataFrame 的列名，如果缺失 'high'/'low'，则回退到 'close'。

### 3. 使用统一的计算方法对齐逻辑
- **Refactoring Requirement**: 修改 `calculate_gx_pit_breakout_filter` 和 `calculate_gx_pit_rotation_filter`，确保它们也具备与 `calculate_gx_pit_rebound_filter` 一致的 ATR 比例调整（如果适用且符合原算法定义）。

## Risks / Trade-offs

- **[Risk]** → 可能导致现有的、显式调用了 `atr_volatility_filter` 的脚本报错。
- **[Mitigation]** → 在重构初期保留旧方法名但标记为 `@deprecated`，或在 `design.md` 中记录需要清理的调用链。
