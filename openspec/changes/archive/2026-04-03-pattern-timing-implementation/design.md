## Context
当前框架包含基础的择时逻辑（如 RSRS），但缺乏基于价格形态识别的高级择时因子。`D:\Dev\PatternPy` 提供了高效的形態识别算法，需要将其集成到现有框架中。

## Goals / Non-Goals

**Goals:**
- 集成 `PatternPy` 的头肩顶、三角形、隧道等经典形态识别。
- 为 000985 指数生成择时信号。
- 支持单因子单 Parquet 文件的导出格式。

**Non-Goals:**
- 不涉及 `PatternPy` 本身算法的重写。
- 不在此阶段进行全自动回测集成，仅负责信号生产与持久化。

## Decisions

- **外部路径注入**: 采用 `sys.path.append('D:/Dev/PatternPy')` 方式动态引入，避免复杂的包安装过程。
- **数据加载**: 使用 `core.DataManager.DataProvider` 加载 `000985.CSI.xlsx`，确保与现有回测数据一致。
- **并行因子存储**: 将 `PatternPy` 返回的 DataFrame 拆分为单列，每列（每种形态）保存为一个独立的 Parquet 文件，方便后续按需加载。
- **输出路径**: 统一存放在 `D:\Dev\Quant\timing\` 目录下。

## Risks / Trade-offs

- [Risk] → `PatternPy` 依赖可能缺失（如 TA-Lib 等）。
- [Mitigation] → 在 `pattern_timing.py` 启动时进行依赖检查。
- [Risk] → 数据列名不匹配导致形态识别失败。
- [Mitigation] → 脚本中包含 `_standardize_input` 逻辑，确保包含 `open, high, low, close, volume`。
