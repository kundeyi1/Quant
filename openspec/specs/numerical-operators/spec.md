# numerical-operators Specification

## Purpose
TBD - created by archiving change standardize-numerical-operators. Update Purpose after archive.
## Requirements
### Requirement: 时序回撤/偏移函数 (ts_delay, ts_delta)
系统 SHALL 支持对 Series 或 DataFrame 进行时间序列上的数值偏移和差分计算。

#### Scenario: 时序延迟
- **WHEN** 调用 `ts_delay` 传入 periods=1
- **THEN** 系统 SHALL 返回向下平移一个单位后的序列，首位补空 (NaN)

### Requirement: 滚动窗口聚合函数 (ts_sum, ts_min, ts_max, ts_std_dev)
系统 SHALL 支持指定窗口期的滚动聚合逻辑。

#### Scenario: 滚动累加
- **WHEN** 调用 `ts_sum` 且 window=20, min_periods=1
- **THEN** 系统 SHALL 返回过去20个交易日的累加值。若数据少于20个，只要有一个非空值则正常累加。

### Requirement: 截面排名函数 (cs_rank)
系统 SHALL 支持对同一截面上所有股票的因子值进行标准化排名。

#### Scenario: 截面百分比排名
- **WHEN** 输入一组因子值
- **THEN** 系统 SHALL 返回百分比排名（0 到 1 之间），并 SHALL 使用 'min' 方法处理同分排名。

### Requirement: 滚动线性回归 (ts_slope, ts_regression)
系统 SHALL 支持基于过去 N 日的滚动线性回归计算，以获得斜率或残差。

#### Scenario: 滚动回归残差
- **WHEN** 在时间窗口内存在有效数据点（至少两个非空值）
- **THEN** 系统 SHALL 使用普通最小二乘法 (OLS) 计算回归结果，并返回当前时点的预测偏差（残差）。

