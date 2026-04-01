## Context
在 `SparseSignalTester` 中，原先的 `Full Timeline` 回测逻辑是通过逐日累乘收益率（Daily Compounding）来生成净值。在股票数量较少且分布均匀时，这与期初等权持有的差异较小；但在全市场 5000+ 股票样本下，逐日等权再平衡（Daily Rebalancing）会显著放大尾部个股的贡献，导致年化收益虚高。

## Goals / Non-Goals

**Goals:**
- 将 `Full Timeline` 的收益计算逻辑从逐日累乘变更为“区间收益等权平均”。
- 确保所有绘图函数（Full Timeline, Spliced, Combined L-S-LS）在同一持仓区间内数值完全同步。
- 移除所有隐含的 Benchmark 收益扣除，统一使用绝对收益（Absolute Return）。

**Non-Goals:**
- 不涉及撮合交易模拟、手续费或滑点计算。
- 不修改底层 `DataManager` 的数据加载逻辑。

## Decisions

### 1. 统一采用区间收益算法
- **选择**: 在 `_calculate_continuous_strategy_returns` 中，对于每一个持仓区间 $[T, T+N]$，每日的价值变动不再计算当日截面均值，而是计算相对于 $T$ 日价格的价值增量。
- **原因**: 消除每日再平衡效应，更贴近真实的等权持仓逻辑（Buy and Hold during the period）。

### 2. 多空差值（L-S）逻辑
- **决策**: `daily_returns` 记录为 `Long_Period_Ret - Short_Period_Ret`。
- **公式**: `(Price_t / Price_start - 1).mean()` 的增量部分。

## Risks / Trade-offs

- **[Risk]**: 算力消耗略有增加。
- **[Mitigation]**: 仅在持仓区间内进行二次索引提取，对于稀疏信号而言，总计算量依然在可控范围内。
- **[Trade-off]**: 放弃了每日再平衡带来的“反转效应”红利，所得结果将更显平庸但更真实。
