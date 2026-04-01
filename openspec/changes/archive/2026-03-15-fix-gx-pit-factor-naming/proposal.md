<artifact id="proposal" change="fix-gx-pit-factor-naming" schema="spec-driven"> 

## Why
目前 `run_gx_pit_` 系列脚本在保存因子数据时，文件名或内部列名与 `SparseSignalTester` 的加载逻辑不匹配（例如 `SparseSignalTester` 默认寻找 `factor` 列或特定命名的文件），导致运行时抛出 `FileNotFoundError: Missing required factor file for signal 'factor'`。需要统一保存规范，确保自动化测试流程正常运行。

## What Changes
- 修改 `run_gx_pit_breakout_test.py`、`run_gx_pit_rebound_test.py` 和 `run_gx_pit_rotation_test.py` 中的因子保存逻辑。
- **文件名规范**: 统一保存为 `gx_pit_mom_{type}.parquet` 形式（例如 `gx_pit_mom_breakout.parquet`）。
- **数据结构规范**: 确保 DataFrame 内部作为因子的序列名称统一为 `factor`。
- **配置同步**: 检查并更新 `SparseSignalTester` 或其调用逻辑，确保 `data_folder` 指向正确的 `D:/DATA/SPARSE_FACTOR`（或配置中的路径）。

## Capabilities

### New Capabilities
- `gx-pit-factor-storage-standard`: 规范 GX PIT 策略因子的文件名、内部列名及存储路径约定。

### Modified Capabilities
- (None)

## Impact
- 脚本: `run_gx_pit_breakout_test.py`, `run_gx_pit_rebound_test.py`, `run_gx_pit_rotation_test.py`
- 模块: `core/SparseSignalTester.py` (数据加载部分)
- 数据目录: `D:/DATA/SPARSE_FACTOR` 及其相关相对路径

</artifact>