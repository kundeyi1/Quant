## Why

我们需要将独立的 `quant_timing_system` 目录下的华泰择时系统代码整合到项目主架构中，以复现《2025-12-26 华泰证券 金融工程 A股择时之技术打分体系》研报。目前的系统独立运行，存在代码冗余。通过整合，可以消除独立目录，并利用现有的 `core/SparseSignalTester.py` 进行时间轴上稀疏择时信号的标准化回测，提升代码的复用性和整个量化系统的统一性。

## What Changes

- 分析 `quant_timing_system` 下的代码（取数、指标、回测），将其功能拆解。
- 将取数、择时信号部分提取并适配到现有的量化框架（`quant` 文件夹对应模块，如 `timing/` 或 `factors/`）。
- 回测部分：放弃原有独立的 `backtest.py`，改为接入现有的 `core/SparseSignalTester.py` 来处理这种时间轴上的稀疏择时信号。
- 在 `quant` 主目录下创建一个全新的入口脚本（例如 `run_huatai_timing.py`），用于实现“取数 -> 择时信号生成 -> 回测”的全流程。
- 不修改 `core` 文件夹中除了 `SparseSignalTester` 以外的任何内容。

## Capabilities

### New Capabilities
- `huatai-timing-integration`: 将华泰技术打分体系的指标计算与 `SparseSignalTester` 回测链路整合。

### Modified Capabilities

## Impact

- 现有 `quant_timing_system` 目录的逻辑将被提取并整合，最终该目录可被弃用。
- 新增 `run_huatai_timing.py` 全流程运行脚本。
- 现有的 `core/SparseSignalTester.py` 将被用于执行最终的回测评估。