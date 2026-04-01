## Context

目前的开发库中包含一个独立的 `quant_timing_system` 目录，最初用于研发和测试《2025-12-26 华泰证券 金融工程 A股择时之技术打分体系》。这部分代码独立于主 `quant` 研发架构。主架构依靠 `core` 模块中的组件（如 `DataManager` 取数、`SparseSignalTester` 信号回测、数值算子等）进行标准化研投。为避免重复造轮子和系统割裂，急需将 `quant_timing_system` 下的核心内容迁移至主研投框架。

## Goals / Non-Goals

**Goals:**
- 解析并拆分 `quant_timing_system` 的 `data_fetcher.py`、`indicators.py` 与 `backtest.py`。
- 将 `indicators.py` 中关于华泰择时的信号函数以静态方法 `ht_<name>` 的形式集成入主库的信号/因子模块（例如新建 `factors/huatai_timing_factors.py` 或复用现有结构）。
- 弃用单独构建的 `backtest.py` 回测逻辑，改用主仓库中专为稀疏信号设计的 `core/SparseSignalTester.py` 进行回测流程的搭建。
- 编写统一调用的集成脚本：`run_huatai_timing.py`，打通取数 -> 计算指标 -> 回测分析的全链路。

**Non-Goals:**
- 不对 `core` 模块的其他文件（除可能必需适度完善的 `SparseSignalTester` 以外）进行侵入式修改。
- 不重新设计信号逻辑，确保华泰研报的逻辑在此次迁移中达到 100% 同比例复现，仅做系统工程适配。

## Decisions

**决策 1: 回测引擎的替换**
- **方案:** 放弃 `quant_timing_system/backtest.py` 的手写回测框架，转而使用已存在于 `core/SparseSignalTester.py` 的处理逻辑。由于择时打分信号多属于在特定时间节点（如某几周一次的离散信号触发）触发，使用 Sparse 方案的回测评估（可能涉及区间持有/止损/多次触发等）更为准确和符合系统已有设计规范。

**决策 2: 数学算子统一化**
- **方案:** 强制替换 `quant_timing_system/indicators.py` 中的自定义滚动处理逻辑，转为调用 `core.NumericalOperators` 提供的基础算子，保证与系统其它因子的表现一致性；对于未覆盖到的滚动指标，通过 `pandas` 进行常规计算但使用 `min_periods=1` 的规范。

**决策 3: 指标模块合并与规范化**
- **方案:** 新信号的函数入口规范为 `calculate_<indicator_name>`，并且返回带有原始时间索引的 `pd.DataFrame` 格式格式的数据框，以便同 `SparseSignalTester.py` 进行对接。

## Risks / Trade-offs

- **Risk:** `SparseSignalTester` 可能在应对连续持有的具体仓位管理和止回盈/止损上与研报原 `backtest.py` 的实现存在细微差别。
  **Mitigation:** 在 `run_huatai_timing_reproduction.py` 脚本中进行严密的测试对齐，若必须支持原样逻辑，则在 `SparseSignalTester` 中通过增加扩展参数方式兼容，而非新写一个基类。
- **Risk:** 数据获取接口变更。 `quant_timing_system/data_fetcher.py` 可能是定制的脱机取数。
  **Mitigation:** 全面替换为项目中标准的 `DataManager` 的 `DataProvider`/`DataFetcher` 读取 D:/DATA（或兜底本地路径）数据流程。