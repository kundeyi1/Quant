<artifact id="specs" change="fix-gx-pit-factor-naming" schema="spec-driven"> 

## ADDED Requirements

### Requirement: Standardize factor file naming for GX PIT strategies
`run_gx_pit_` 系列脚本在保存因子数据时，必须（SHALL）使用统一的文件名格式：`gx_pit_mom_{type}.parquet`。

#### Scenario: Save breakout factor
- **WHEN** `run_gx_pit_breakout_test.py` 运行结束并保存因子时
- **THEN** 生成的文件名必须为 `gx_pit_mom_breakout.parquet`

#### Scenario: Save rebound factor
- **WHEN** `run_gx_pit_rebound_test.py` 运行结束并保存因子时
- **THEN** 生成的文件名必须为 `gx_pit_mom_rebound.parquet`

#### Scenario: Save rotation factor
- **WHEN** `run_gx_pit_rotation_test.py` 运行结束并保存因子时
- **THEN** 生成的文件名必须为 `gx_pit_mom_rotation.parquet`

### Requirement: Standardize internal factor column name
保存的因子 DataFrame 内部，代表因子的序列名称必须（SHALL）统一命名为 `factor`。

#### Scenario: Internal data alignment
- **WHEN** `SparseSignalTester` 加载 `gx_pit_mom_breakout.parquet` 时
- **THEN** 能够通过 `df['factor']` 或默认逻辑正确识别因子序列，而不会因找不到列名而报错

### Requirement: Factor storage directory consistency
所有的量化因子数据必须（SHALL）默认保存至 `D:/DATA/SPARSE_FACTOR` 目录，并确保脚本具备自动创建目录的能力。

#### Scenario: Missing directory auto-creation
- **WHEN** 目标目录 `D:/DATA/SPARSE_FACTOR` 不存在时
- **THEN** 脚本必须在保存前自动创建该目录，避免 IO 错误

</artifact>