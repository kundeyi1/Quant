## Why
引入基于 `PatternPy` 的外部模式识别择时逻辑，旨在利用先进的价格形态（如头肩顶、双重底等）来增强 000985 指数的择时准确性，并在本地环境中实现信号的自动化生产与持久化。

## What Changes
- 在 `timing/` 目录中创建 `pattern_timing.py` 脚本，负责集成外部 `PatternPy` 功能。
- 实现 000985 指数行情数据的标准化接入与清洗。
- 生成基于形态识别的择时信号，并实时打印关键触发点。
- 将识别出的每种模式特征分别导出为 Parquet 文件，保存于 `timing/` 目录下，文件命名格式为 `000985_<pattern_name>.parquet`。

## Capabilities

### New Capabilities
- pattern-timing: 提供基于形态识别（Head & Shoulders, Wedges, Channels 等）的指数择时数据生产能力。

### Modified Capabilities

## Impact
- **新文件**: `timing/pattern_timing.py`
- **对外依赖**: `D:\Dev\PatternPy` 需在 Python 路径中。
- **数据输出**: 在 `timing/` 下生成多个 `.parquet` 文件。