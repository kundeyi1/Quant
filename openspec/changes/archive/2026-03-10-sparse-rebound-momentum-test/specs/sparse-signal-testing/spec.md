## ADDED Requirements

### Requirement: 稀疏信号对齐与提取
系统必须（SHALL）能够读取外部指数数据（如中证 500）生成的 0-1 掩码序列，并根据该序列的触发时点（值为 1 的日期），精准提取所有行业标在该日期的截面因子值。

#### Scenario: 跨资产日期对齐
- **WHEN** 指数数据在 2024-01-05 触发反弹信号，但某行业在该日停牌或缺少数据。
- **THEN** 系统必须通过 `reindex` 或 `merge` 确保信号日期与行业数据完全对齐，缺失行业在统计中应被标记为 NaN 或排除。

### Requirement: Wind 格式索引文件读取
系统必须（SHALL）能够读取位于 `D:/DATA/INDEX/ZX/ZX_YJHY.csv` 的中信一级行业指数，该文件采用 Wind 导出格式。读取时系统 MUST 使用 `core.DataManager` 的 Wind 解析器或等效接口将原始字段映射到统一的 OHLCV 列 (`open, high, low, close, volume`) 并以日期为索引返回。

#### Scenario: Wind 文件解析
- **WHEN** 输入文件 `D:/DATA/INDEX/ZX/ZX_YJHY.csv` 包含 Wind 风格列名（例如 `TRADE_DT`, `S_INFO_WINDCODE`, `S_DQ_CLOSE` 等）
- **THEN** `core.DataManager` MUST 成功映射并返回标准 DataFrame；若关键列缺失或格式错误，系统 MUST 抛出描述性错误并记录该文件路径以便运维修正。

### Requirement: 阶梯式分组动量计算
系统必须（SHALL）计算触发日各行业的 `calculate_gx_momentum_factor`，并根据该因子值由高到低将行业划分为 N 个组别（默认 3-5 组）。

#### Scenario: 行业分组逻辑验证
- **WHEN** 触发日共有 30 个中信一级行业，设定分组数为 5。
- **THEN** 系统必须将这 30 个行业按动量因子排序，每 6 个行业分配到一组（Group 1 为动量最强组）。

### Requirement: 信号后向累积收益统计
系统必须（SHALL）跟踪每个信号日之后固定窗口（如 T+20）的行业累积收益。统计逻辑必须排除信号触发当日的涨幅，仅计算信号次日起的超额或绝对收益。

#### Scenario: T+20 累加收益计算
- **WHEN** 信号在 T 日触发，行业在 T+1 到 T+20 的日收益率为 $r_1, r_2, ..., r_{20}$。
- **THEN** 系统必须计算 $\prod (1+r_i) - 1$ 作为该信号点的持有期收益。

### Requirement: 稀疏样本绩效聚合
系统必须（SHALL）对所有历史触发点的测试结果进行聚合统计，包括各组的平均持有期收益、胜率（收益 > 0 的比例）以及相对于基准（指数平均水平）的超额收益。

#### Scenario: 聚合结果展示
- **WHEN** 历史上一共出现了 10 次反弹触发信号。
- **THEN** 系统必须输出各分组在 10 次事件中的平均表现，并生成包含累计收益曲线（多头对比空头或基准）的可视化报告。
