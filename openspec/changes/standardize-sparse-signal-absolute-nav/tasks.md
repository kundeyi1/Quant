## 1. 核心计算逻辑统一 (Core Calculation)

- [x] 1.1 修改 `_calculate_continuous_strategy_returns`：将逐日等权再平衡改为期初等权持有的净值增量计算。
- [x] 1.2 修改 `_calculate_continuous_strategy_returns_spliced`：确保采用 `(P_end / P_start - 1).mean()` 进行区间绝对收益计算。
- [x] 1.3 移除收益计算中所有对 `benchmark_series` 的隐式扣除。

## 2. 绘图与可视化对齐 (Visualization)

- [x] 2.1 更新 `plot_l_s_ls_combined_curve`：使其 LS 线与 Spliced 逻辑完全同步。
- [x] 2.2 更新 `plot_discrete_equity_curve`：确保使用绝对收益而非超额收益。
- [x] 2.3 更新 `plot_excess_return_bar`：展示绝对收益分布并重命名。

## 3. 验证与测试 (Validation)

- [x] 3.1 运行 `run_gx_pit_rotation_test.py` 进行全市场覆盖测试。
- [x] 3.2 检查 `full_timeline` 与 `spliced` 图表在持仓区间的净值增长是否完全一致。
- [x] 3.3 验证 `nav_summary.csv` 中的年化收益是否回归合理区间（排除再平衡效应）。
