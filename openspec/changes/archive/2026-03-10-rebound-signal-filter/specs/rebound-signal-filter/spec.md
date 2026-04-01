## ADDED Requirements

### Requirement: 大跌反弹信号逻辑实现
系统 SHALL 针对每个交易日 $T$ 判断是否触发反弹信号。

#### Scenario: 触发反弹信号
- **WHEN** 
  - $T$ 日当日涨跌幅 $> U$。
  - 从 $T-1$ 日向前寻找包含任意一天涨幅 $\le U$ 的最长区间 $M$。
  - 区间 $M$ 内最高收盘价 $Close_{high}$ 出现日期早于最低收盘价 $Close_{low}$。
  - $Close_{high}$ 与 $Close_{low}$ 的间隔 $> 2$ 个交易日。
  - 下跌幅度 $1 - Close_{low} / Close_{high} > D$。
- **THEN** 系统在 $T$ 日输出为信号触发 (True/1)，否则为 False/0。

### Requirement: 参数可配置性
计算函数 SHALL 支持用户自定义阈值 $U$ 和 $D$。

#### Scenario: 不同阈值设置
- **WHEN** 用户在调用接口时指定 $U=0.03$ 且 $D=0.10$。
- **THEN** 系统 SHALL 基于输入的 $0.03$ 作为反弹标准和 $10\%$ 作为下跌标准进行逻辑过滤。

### Requirement: 时间序列对齐
所得掩码序列 SHALL 与输入数据保持一致的日期索引。

#### Scenario: 索引一致性
- **WHEN** 计算完成。
- **THEN** 返回的 Series 或 DataFrame 索引 MUST 对应输入数据的 DataFrame 索引，且无日期偏移偏移。
