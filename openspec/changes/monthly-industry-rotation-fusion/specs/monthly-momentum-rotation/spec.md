# Monthly Industry Rotation Fusion Factor Spec

## Requirements

1. **月中信号捕获 (Signals to Factor Indexing)**:
   - 系统 MUST 扫描过去 10 个交易日内的所有触发信号（Breakout, Rebound, Rotation）。
   - 每个信号在触发日进行资产截面 Rank（0.0 到 1.0 的归一化，中性为 0.5）。
   - 对回看窗口内的所有 Rank 值，应用指数衰减权重 $w = 2^{-n/10}$。
   - 月度因子值 = $\sum (Rank_i \times w_i) / \sum w_i$。

2. **数据处理 (Data Processing)**:
   - 因子计算 SHALL 在每个自然月的最后一个交易日进行。
   - 若某行业在过去10日内没有任何信号，其因子值设为 NaN。
   - 因子 SHALL 应用行业中性化（由现有框架支持）。

3. **保存与输出 (Storage & Output)**:
   - 因子文件格式: CSV (index: date, columns: ticker)。
   - 文件路径 MUST 保存为: `D:/DATA/factors/zxyjhy_gx_pit_mom_factor.csv`。
   - 另一个因子文件（二级行业）: `D:/DATA/factors/zxejhy_gx_pit_mom.csv`。

4. **评价指标 (Evaluation Specs)**:
   - 运行标准因子分析：IC, Rank IC, ICIR。
   - 计算 5 层（Quintile）分组超额收益。
   - 绘制 Top 分组的累积超额收益图（相对于行业基准）。

## Success Criteria

1. 成功在 `D:/DATA/factors` 生成对应的 CSV 文件。
2. 因子分析报告显示 IC 为正，且 Top 分组年化收益优于 Benchmark。
3. 可视化报告中包含行业轮动的分组柱状图。
