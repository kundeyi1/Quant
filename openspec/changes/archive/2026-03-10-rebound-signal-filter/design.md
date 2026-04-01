## Context

当前项目已有算子库 `NumericalOperators`，但尚未有专门处理复杂时变窗口（寻找特定反弹前区间 $M$）的信号过滤器。新功能需要在保证计算效率的同时，准确实现寻找区间 $M$ 的高低点对比逻辑。

## Goals / Non-Goals

**Goals:**
- 在 `filters/signal_filters.py` 中实现 `calculate_rebound_signal_filter`。
- 函数接受包含收盘价 `close` 和最高/最低价 `high/low` 的 DataFrame，并返回掩码。
- 逻辑上需要涵盖当日涨幅检查、区间 $M$ 的最长性定义、高低点对应关系和距离约束。

**Non-Goals:**
- 不涉及除 0/1 掩码外的收益率计算（这是回测引擎的任务）。
- 不对数据进行复权处理（假设输入已复权）。

## Decisions

- **实现机制**: 为保证向量化难以覆盖的部分（寻找区间 $M$ 和高低点对比）的性能，将采用 Pandas 的 `apply` 或局部迭代。如果数据量巨大，后续可考虑 Numba 优化。
- **区间 $M$ 的定义实现**: 区间 $M$ 定义为截至 $T-1$ 的最长连续区间，其中任意一天的涨幅均不大于 $U$。这可以通过计算 `pct_change <= U` 的连续 True 值来实现。
- **高低点约束**: $Close_{high}$ 出现必须早于 $Close_{low}$（即 $idx(high) < idx(low)$），且 $idx(low) - idx(high) > 2$。

## Risks / Trade-offs

- **计算开销**: 逐日寻找区间 $M$ 可能会有 $O(N^2)$ 的最坏情况。
  - **Mitigation**: 预计算全序列的当日收益率，通过前缀和或标记位快速定位区间 $M$。
- **数据不连续性**: 涨跌停、停牌导致的涨幅为 0 会被计入区间 $M$。
  - **Mitigation**: 逻辑上允许涨幅为 0 的天数计入，因为这本身代表了“未反弹”的震荡或下跌过程。
