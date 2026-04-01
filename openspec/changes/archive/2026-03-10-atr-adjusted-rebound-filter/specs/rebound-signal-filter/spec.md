## MODIFIED Requirements

### Requirement: 大跌反弹信号逻辑实现
系统 SHALL 针对每个交易日 $T$ 判断是否触发反弹信号，且阈值 $U$ 和 $D$ SHALL 根据当日 ATR 水平动态调整。

#### Scenario: 动态阈值触发
- **WHEN** 
  - 计算 14 日 ATR（基于收盘价百分比或真实波幅）。
  - 如果 ATR < 1%，修正系数 $C = \sqrt{ATR / 1\%}$。
  - 如果 1% <= ATR <= 2%，修正系数 $C = 1.0$。
  - 如果 ATR > 2%，修正系数 $C = \sqrt{ATR / 2\%}$。
  - 有效阈值 $U' = U \times C$ 且 $D' = D \times C$。
  - $T$ 日当日涨跌幅 $> U'$。
  - 从 $T-1$ 日向前寻找包含任意一天涨幅 $\le U'$ 的最长区间 $M$。
  - 区间 $M$ 内最高收盘价 $Close_{high}$ 出现日期早于最低收盘价 $Close_{low}$。
  - $Close_{high}$ 与 $Close_{low}$ 的间隔 $> 2$ 个交易日。
  - 下跌幅度 $1 - Close_{low} / Close_{high} > D'$。
- **THEN** 系统在 $T$ 日输出为信号触发 (True/1)，否则为 False/0。
