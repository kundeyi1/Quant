## Why

由于项目涉及多种资产类型（股票、指数、基本面数据）和多种存储格式（CSV, Excel），需要一套统一的数据加载和预处理规范。这不仅能减少重复代码，还能确保因子的输入数据质量一致，特别是在处理证券代码格式化、日期解析和列名映射方面。

## What Changes

- 在 `openspec/specs/` 下建立 `data-pipeline` 目录。
- 规范化 `DataProvider` 类的数据查找逻辑和核心路径管理。
- 建立基本面数据的字段映射标准（code, date, value）。
- 明确 Excel 文件损坏或样式异常时的降级处理机制。

## Capabilities

### New Capabilities
- `data-pipeline`: 详细定义数据加载器的行为，包括路径优先级、数据清洗规则和标准输出格式。

## Impact

- 核心模块 [core/DataManager.py](core/DataManager.py) 的逻辑实现将以此为准。
- 所有的策略脚本在调用数据时需遵循规范化的列名约定。
