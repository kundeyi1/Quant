## ADDED Requirements

### Requirement: 获取并整合研报所需数据
系统 MUST 支持通过项目默认路径 `D:/DATA`（或相对路径退路）读取华泰打分择时系统所需要的日线级基础行情数据（如 OHLCV），不再依赖原 `quant_timing_system/data_fetcher.py`。

#### Scenario: 加载市场基准及行业数据
- **WHEN** 用户或脚本调用执行回测流程时
- **THEN** 主框架的 `core` 中的 `DataManager` 成功加载目标时间段的日线行情 DataFrame，且包含所需的基础列如 open, high, low, close, volume。

### Requirement: 技术打分复合因子的计算适配
系统 MUST 在 `factors`（例如 `huatai_timing_factors.py` 或由现有机理承接）模块中提供一整套择时信号对应的静态方法（签名形式务必为 `calculate_<indicator_name>`），用来复现华泰研报（RSRS, 价乖离、量乖离、布林带突破、趋势强度、新高比例等）。

#### Scenario: 华泰技术择时信号生成
- **WHEN** 传入合规的 OHLCV DataFrame 并且调用如 `calculate_ht_rsrs(...)` 或 `calculate_ht_integrated_timing(...)` 等类函数
- **THEN** 函数按照 `core.NumericalOperators` 和 `min_periods=1` 规范计算指标，并返回一个索引为原始时间的 `pd.DataFrame` 格式，其中的值为离散的择时打分信号（例如0, 1）。

### Requirement: 使用 SparseSignalTester 执行回测评估
系统 MUST 支持以生成的信号 DataFrame 输入给现有的 `core/SparseSignalTester.py` 进行信号触发回测，而不需要也不使用之前独立在 `quant_timing_system` 中分离实现的回溯循环代码。

#### Scenario: 执行稀疏时间轴回测
- **WHEN** `run_huatai_timing_reproduction.py` 传入生成的华泰综合打分信号向量并执行 `SparseSignalTester.backtest()`（或相关功能函数）时
- **THEN** 系统正常运算，考虑稀疏离散的入场/出场或多空信号状态，统计出回测的核心业务绩效（多头年化、空头表现、最大回撤等），且无执行崩溃。

### Requirement: 删除或隔离独立子系统
系统 MUST 在新的适配全流程落地后，在主目录提供完整链路实现（即新增的 `run_huatai_timing_reproduction.py` 统一入口），并且逐步清除（或移除到废弃区）原来的 `quant_timing_system` 目录资源。

#### Scenario: 统一入口取代老式工程
- **WHEN** 所有的 `data_fetcher.py`, `indicators.py`, `backtest.py`, `main.py` 代码均已被集成并利用主线库机制完成对接时
- **THEN** `quant_timing_system` 内的执行及实现可被安全删除而不影响项目主流程。