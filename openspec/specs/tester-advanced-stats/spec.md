## Purpose
This capability provides advanced performance statistics for event-driven (sparse signal) backtests, including IC, ICIR, IC Winning Rate, and Group-based Excess Returns.

## Requirements

### Requirement: Advanced Statistics Calculation
系统必须能够在稀疏信号回测（Event-based Backtest）完成后，针对触发日计算综合性能指标。这些指标包括：
1. **IC / Rank IC**：计算每个触发日因子值（Factor Value）与 T+period 收益的 Pearson 和 Spearman 相关系数，并输出均值。
2. **ICIR**：计算触发日 IC 序列的均值与标准差之比（按 $\sqrt{N}$ 年化处理，若信号点较少则仅输出原始比率）。
3. **IC 胜率 (IC Winning Rate)**：IC 值大于 0 的触发点占比。
4. **多空超额收益 (Long/Short Excess Return)**：
    - 多头超额 (Group 5 - Group 平均)：Group 5 在 T+period 的收益减去所有组在当期的截面平均收益。
    - 空头超额 (Group 1 - Group 平均)：Group 1 在 T+period 的收益减去所有组在当期的截面平均收益。
    - 多头超额均值：所有触发点多头超额收益的均值。

#### Scenario: Verify Statistics Output
- **WHEN** 脚本运行完成，共 30 个触发点
- **Then** 控制台输出 "Performance Metrics" 表格，包含 IC=0.15, RankIC=0.12, ICIR=1.5, WinningRate=65%, LongExcess=2.1%, ShortExcess=-1.8% 等内容

#### Scenario: Empty Signal Performance Handling
- **WHEN** 无触发信号或触发点数量少于 2 个（无法计算 ICIR）
- **THEN** 系统应以 NaN 或具体提示信息展示统计指标，而不应报错中断。
