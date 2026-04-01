## Why
目前 `SparseSignalTester` 在不同回测视角（全时段 Timeline、拼接 Spliced、离散 Discrete）下采用了不一致的收益计算方式（每日再平衡 vs. 期初等权持有），导致在全市场 5000+ 股票样本下年化收益产生巨大偏差。

## What Changes
- **统一计算逻辑**：所有回测模式统一采用“持仓周期内期初等权持有”逻辑，即直接计算 $T$ 到 $T+N$ 的截面平均收益，消除每日再平衡带来的虚高收益。
- **绝对净值视角**：移除所有隐含的 Benchmark 扣除逻辑，仅计算多头、空头及其绝对收益差值（L-S）。
- **图表同步更新**：确保 `L-S-LS` 绘图中的 `LS` 线与 `Spliced` 曲线在数值上完全一致。

## Capabilities

### New Capabilities
- 无

### Modified Capabilities
- `sparse-signal-testing`: 统一回测引擎的净值计算体系，从逐日再平衡切换为固定周期等权。

## Impact
- 修改 `core/SparseSignalTester.py` 中的关键计算私有方法：`_calculate_continuous_strategy_returns` 和 `_calculate_continuous_strategy_returns_spliced`。
- 更新绘图方法：`plot_l_s_ls_combined_curve` 和 `plot_discrete_equity_curve`。
