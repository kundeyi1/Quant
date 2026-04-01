## Context

当前 `SparseSignalTester` 仅提供 `run_backtest` 返回各组平均收益率。为了满足用户对 IC、ICIR、IC 胜率及多空超额收益的计算需求，需要对 `core/SparseSignalTester.py` 进行逻辑增强。所有统计必须在触发点的截面（Cross-section）上计算。

## Goals / Non-Goals

**Goals:**
- 将 IC 和超额收益逻辑集成到 `SparseSignalTester` 类。
- 提供 `print_stats_report` 和 `export_stats_log` 方法以便在所有测试脚本中复用。
- 将原本独立的 `calculate_group_returns` (计算 T+period) 的数据中间状态用于 IC 计算。

**Non-Goals:**
- 不涉及传统时序 IC 计算（非触发点期间不计入结果）。
- 不涉及具体的因子平滑、去极值、标准化处理（应在策略代码中先完成，测试器仅作为度量工具）。

## Decisions

### 1. IC 计算逻辑适配
决定为每个触发日期执行截面相关性计算：
- **Pearson IC**: `df_factor.loc[date].corr(df_return_T20.loc[date])`
- **Spearman Rank IC**: 使用 `scipy.stats.spearmanr` 或 `factor.rank().corr(return.rank())`。
- ** ICIR**: 选取触发日 IC 序列的 `mean() / std()`。由于信号在时间上是稀疏的（并非逐日触发），因此不考虑 $T^{1/2}$ 年化校准。

### 2. 多空超额收益 (Excess Return) 定义
- `Group 5 Excess`: $R_{G5} - \text{Mean}(R_{all\_groups})$
- `Group 1 Excess`: $R_{G1} - \text{Mean}(R_{all\_groups})$

### 3. 保存计算状态 (Cached Data)
为了避免重复读取 `price_df` 计算 T+period 收益，将在 `run_backtest` 循环中同时维护一个 `_trigger_metrics_list` 内部存储每个触发点的：
- 日期
- 全截面收益列表
- 全截面因子列表
- 各组收益

## Risks / Trade-offs

- **[Risk] 数据不足 (Data Sparsity)**：若触发点过少（如只有 1 次），ICIR 和标准差无法计算。
  - **Mitigation**：增加异常捕捉，并在结果中返回 `np.nan` 或 `0.0`，不在报告中显示无法计算的项目。
- **[Risk] 复共线性问题**：如果因子值是动态掩码之后的，可能会有大量常量或全为 0。
  - **Mitigation**：IC 计算前检查因子值的标准差是否大于 0。
