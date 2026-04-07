## ADDED Requirements

### Requirement: b2 趋势类因子 (Trend & Structure)
系统必须在 actors/technical_factors.py 中提供刻画大周期趋势与均线结构的因子。
- 	rend_strength: (Close - MA60) / MA60，衡量相对于 60 日线的偏离度。
- 	rend_slope: 通过线性回归或差分计算 MA20 的斜率，衡量短期趋势动量。
- ma_structure: (MA20 - MA60) / MA60，衡量多头排列的紧密程度。

#### Scenario: 趋势强度计算
- **WHEN** 输入全市场收盘价数据。
- **THEN** 系统返回连续分值，值越大表示向上趋势越强。

### Requirement: b2 波动与能量压缩因子 (Compression)
系统必须提供衡量近期波动与量能相对于长周期收缩程度的因子，用于识别变盘前奏。
- olatility_ratio: 5日收益率标准差 / 20日收益率标准差。
- mplitude_ratio: 5日平均振幅 (High-Low) / 20日平均振幅。
- olume_ratio: 5日平均成交量 / 20日平均成交量。

#### Scenario: 波动率压缩识别
- **WHEN** 市场进入窄幅震荡。
- **THEN** olatility_ratio 应显著下降，反映能量压缩。

### Requirement: b2 结构位置因子 (Position & Supply)
系统必须提供衡量价格在历史区间位置及潜在套牢盘压力的因子。
- pullback_depth: (RollingMax20 - Close) / RollingMax20，衡量从近期高点的回调深度。
- position: (Close - RollingMin60) / (RollingMax60 - RollingMin60)，衡量在 60 日区间的位置。
- supply_pressure: 近期高点日期的成交量 / 20日均量。
- up_volume_ratio: 近期放量上涨日的成交量占总成交量的比例。

#### Scenario: 筹码压力判定
- **WHEN** 股价接近前期高点且 supply_pressure 较高。
- **THEN** 因子得分应反映出较大的潜在抛售压力。

### Requirement: b2 启动强度因子 (Ignition Momentum)
系统必须提供反映单日共振爆发特性的因子，捕捉启动 K 线。
- momentum_acceleration: 今日收益率 - 过去5日平均收益率。
- olume_zscore: (今日成交量 - MA20_Volume) / STD20_Volume。
- ody_strength: |Close - Open| / (High - Low)，衡量 K 线实体的饱满程度。

#### Scenario: 启动信号捕捉
- **WHEN** 出现放量大实体阳线。
- **THEN** ody_strength 和 olume_zscore 应同时处于高分段。

### Requirement: 全市场 IC 评估与分层回测
系统必须支持利用 core.FactorTester 对上述因子进行全市场的截面评估。

#### Scenario: 因子 IC 均值计算
- **WHEN** 评估 momentum_acceleration 对未来 1d 收益的解释力。
- **THEN** 系统输出 Pearson/Spearman IC 均值及 ICIR。

#### Scenario: 5 分层累积收益
- **WHEN** 按因子值对全市场股票分为 5 组。
- **THEN** 系统绘制 5 组的对冲（Long-Short）及各组独立的净值曲线。
