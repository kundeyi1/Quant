<artifact id="design" change="fix-gx-pit-factor-naming" schema="spec-driven"> 

## Context
在 `run_gx_pit_breakout_test.py` 等脚本中，计算出的因子（如当日涨幅）被保存为 `.parquet` 文件。然而，`SparseSignalTester` 的数据读取逻辑要求：
1. **文件名**必须与信号名称（或默认的 `factor`）匹配。
2. **数据列名**在 `SparseSignalTester` 内部读取后，如果脚本没有显式指定，可能会因为 DataFrame 包含多列或列名不识别（如原本是行业名称列）导致无法正确提取截面。
3. 且目前的 `run_gx_pit_*.py` 脚本中，因子的保存路径和文件名存在不统一的情况，导致 `SparseSignalTester` 抛出 `FileNotFoundError`。

## Goals / Non-Goals

**Goals:**
- 统一 `run_gx_pit_*.py` 的因子保存规范（路径、文件名、内部格式）。
- 确保 `SparseSignalTester` 能无缝加载这些因子。
- 自动处理存储目录的创建。

**Non-Goals:**
- 修改 `SparseSignalTester` 的核心算法逻辑。
- 重构 `DataManager` 或 `DataProvider`。

## Decisions

### 1. 统一文件名与信号名的映射
为了让 `SparseSignalTester` 能够找到文件，我们将信号名称与文件名解耦或对齐。
- **方案**: 在调用 `SparseSignalTester` 时，如果 `signal_series` 是 Series，它默认寻找 `factor.parquet`。因此，最简单的修复是将文件名统一为 `gx_pit_mom_{type}.parquet`，并在脚本调用时显式指定 `signal_series` 的名称。
- **实施**: 
  - `run_gx_pit_breakout_test.py` -> 保存为 `gx_pit_mom_breakout.parquet`
  - 将信号 Series 赋予名称 `gx_pit_mom_breakout`。

### 2. 标准化内部数据格式
`SparseSignalTester` 加载 parquet 后会直接使用。如果 parquet 内部是多列（行业），则保持原样，但要确保日期索引正确。
- **注意**: `SparseSignalTester` 的 `_load_required_factors` 方法会根据 `signal_series` 的列名（如果是 DataFrame）或默认值 `factor`（如果是 Series）来寻找对应的文件名。
- **折中方案**: 
  - 如果 `signal_series` 是 Series，我们将其重命名为具体的文件名（不含后缀），例如 `signal.name = "gx_pit_mom_breakout"`。这样 `SparseSignalTester` 就会去寻找 `gx_pit_mom_breakout.parquet`。

### 3. 目录自动创建
- **决策**: 在所有涉及保存的脚本中使用 `os.makedirs(path, exist_ok=True)`。

## Risks / Trade-offs

- **[Risk]** 信号名与文件名重名可能导致混淆。 -> **Mitigation**: 采用 `gx_pit_mom_` 前缀清晰区分。
- **[Trade-off]** 强制重命名信号 Series 可能会影响后续的可视化标签。 -> **Mitigation**: 在绘图函数中允许通过参数指定 Title。

</artifact>