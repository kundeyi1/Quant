## ADDED Requirements

### Requirement: Timing signal persistence
系统必须（MUST）支持将计算出的择时信号（0/1序列）持久化存储。文件名必须包含信号名称（gx_pit_breakout/gx_pit_rebound/gx_pit_rotation）、起止时间戳。

#### Scenario: Save breakout timing signal
- **WHEN** 计算完成 `gx_pit_breakout` 择时信号
- **THEN** 系统将其保存至 `D:\DATA\TIMING/gx_pit_breakout_20130101_20260320.parquet`

### Requirement: Idempotent signal calculation
在开始任何耗时的计算前，系统必须（SHALL）检查目标存储路径。若已存在完全匹配的信号文件，则应当跳过（SHALL skip）计算。

#### Scenario: Skip existing rebound signal
- **WHEN** 调用计算 `gx_pit_rebound` 且对应文件已存在于 `D:\DATA\TIMING`
- **THEN** 系统直接加载该文件并返回，不重新执行计算逻辑

### Requirement: Multi-strategy execution framework
系统必须（SHALL）允许在单个运行入口（`gx_pit_mom.py`）中配置并运行多个 PIT 动量信号组合。

#### Scenario: Run all signals with ejhy
- **WHEN** 用户在 `gx_pit_mom.py` 中选择运行 `['breakout', 'rebound', 'rotation']` 且行业设定为 `ejhy`
- **THEN** 系统按序处理三种信号的择时计算与稀疏因子测试
