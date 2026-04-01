# rebound-signal-filter Specification

## Purpose
The rebound-signal-filter defines the logic for detecting potential market reversals after significant price drops, now integrated into the `timing.market_timing` framework as `gx_pit_rebound`.

## Requirements
### Requirement: 大跌反弹信号过滤器 (Rebound Signal Filter)
The system SHALL provide a flat function `gx_pit_rebound` to detect potential market reversals after significant drops (previously implemented as a signal filter).

#### Scenario: Rebound trigger (Atr-based)
- **WHEN** the daily return on day $T$ is greater than its dynamic threshold $U$ (where $U$ is adjusted by relative $ATR_{60}$)
- **AND** a significant drawdown of at least $D$ occurred within a rolling window $M$ prior to $T$
- **THEN** the system SHALL output a signal value of `1` for day $T$.

#### Scenario: No rebound trigger
- **WHEN** either the return threshold $U$ or the drawdown threshold $D$ is not met
- **THEN** the system SHALL output a signal value of `0` for that date.

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

