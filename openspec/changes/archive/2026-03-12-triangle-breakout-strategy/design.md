## Context

本计划旨在实现一个融合波动率压抑（Volatility Compression）与价格通道收缩（Channel Squeeze）的爆发性策略。当前框架已有 `SignalFilters` 模块，新增逻辑应作为静态方法集成，以便后续在 `SparseSignalTester` 中进行回测。

## Goals / Non-Goals

**Goals:**
- 实现三角形收缩突破（Triangle Breakout）过滤算法。
- 确保算法能够处理多列（宽表）数据，支持指数和行业多标的回测。
- 集成进入 `SparseSignalTester` 以产出标准的可视化报告。

**Non-Goals:**
- 不涉及实时交易信号推送。
- 不修改现有的 `DataManager` 或 `NumericalOperators` 核心逻辑。

## Decisions

### 1. 算法实现路径 (Vectorized Implementation)
决定采用 Pandas 的矢量化计算以提高效率，而不是循环遍历日期。
- **前期波动控制**：使用 `rolling(5).apply(lambda x: (np.abs(x) < 0.01).all())` 进行 5 日绝对值判断。
- **通道收缩判定**：通过 `rolling(5).max()` 和 `rolling(5).min()` 构建 High/Low 序列，计算其差值（width），再通过 `diff() < 0` 判定 T-1 是否小于 T-2。
- **对齐与平移**：计算 T-1 的状态时，需使用 `.shift(1)` 将判定逻辑对齐到 T 日。

### 2. 回测脚本逻辑
沿用 `run_market_turning_point_test.py` 的结构：
- **Benchmark**: 中证 500 或全指。
- **Factor**: 触发当日行业涨幅。
- **Performance**: 统计 T+20 累积收益。

## Risks / Trade-offs

- **[Risk] 过度拟合 (Overfitting) → Mitigation**: 增加结果的可视化分析（年化分布），观察信号在不同市场环境下的表现是否稳定，而非仅看总收益。
- **[Risk] 数据延迟 (Look-ahead Bias) → Mitigation**: 严格核对 `shift` 参数，确保 T 日信号仅依赖 T-1 及以前的滚动窗口信息（除 T 日自身的突破幅度外）。
