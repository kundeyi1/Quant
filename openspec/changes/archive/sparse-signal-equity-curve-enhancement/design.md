## Context

当前 `SparseSignalTester` 的净值计算是通过 `(1 + ls_rets).cumprod()` 完成的，其中 `ls_rets` 仅包含信号触发日的持有期总收益。这种方式简单，但无法反映时间轴上的连续表现，也无法处理信号重叠时的强制平仓。

## Goals / Non-Goals

**Goals:**
- 在 `SparseSignalTester` 中增加连续日度净值生成的私有方法。
- 支持“新信号覆盖旧信号”（Last-Signal-Priority）的调仓逻辑。
- 允许用户在绘图时选择离散、连续、真实时间轴三种模式。

**Non-Goals:**
- 不涉及多信号并行持时的复杂权重分配（始终保持单信号覆盖）。
- 不涉及交易佣金、滑点的计算（保持单纯的 Alpha 评估）。

## Decisions

### 1. 内部日度收益率对齐 (Daily Return Alignment)
- **决定**: 预先生成一个与 `price_df.index` 对齐的 `daily_strategy_returns` Series。
- **理由**: 通过填充该序列，可以自然地切换“空白期平滑”和“真实时间轴”模式。对于第 2 种需求（不抹平空白期），在绘图时只需剔除收益率为 0 的日期即可。

### 2. 调仓逻辑实现 (Rebalancing Logic)
- **决定**: 使用时间戳遍历或 `ffill` 结合 `limit` 来标记每个日期归属于哪个信号。
- **具体做法**:
    1. 创建一个 `signal_id` 序列。
    2. 当 $T$ 日出现新信号时，更新 `signal_id`。
    3. 每个信号的生命周期受限于 `period` 参数或下一个信号的出现。
    4. 计算每个日期对应的资产在当日的涨跌幅。

### 3. 可视化接口 (Plotting Interface)
- **决定**: 保持 `plot_equity_curve` 方法名，添加 `mode` 参数。
- **理由**: 兼容现有脚本，减少迁移成本。

## Risks / Trade-offs

- **[Risk] 内存消耗**: 对于极长时间序列的日度对齐计算，DataFrame 操作可能较慢。
- **[Mitigation]**: 仅在调用相应 Plot 功能时进行计算，不存储在对象初始化阶段。
