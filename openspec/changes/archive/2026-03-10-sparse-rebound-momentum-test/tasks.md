## 1. 核心测试逻辑模块设计 (Core Implementation)

- [x] 1.1 在 `core` 目录下创建 `SparseSignalTester.py` 文件并引入基础依赖
- [x] 1.2 实现 `SparseSignalTester` 类，定义 `__init__` 以接收因子数据和信号数据
- [x] 1.3 编写 `_extract_cross_section` 内部方法，支持根据掩码日期提取因子向量
- [x] 1.4 实现 `calculate_group_returns` 方法，计算 T+1 到 T+20 的累积百分比收益

## 2. 因子计算与适配 (Factor & Data Alignment)

- [x] 2.1 修改 `core/DataManager.py` 或新增适配器以支持读取中信一级行业索引文件 `D:/DATA/INDEX/ZX/ZX_YJHY.csv`（Wind 格式），并将数据映射为标准 OHLCV DataFrame 和日期索引。该功能 MUST 提供列名映射和格式校验。
- [x] 2.2 调用 `SignalFilters.calculate_rebound_signal_filter` 生成指数的 0-1 反弹掩码
- [x] 2.3 对所有中信一级行业加载日频数据，并调用 `MomentumFactors.calculate_gx_momentum_factor`

## 3. 测试与验证 (Testing & Validation)

- [x] 3.1 创建 `run_sparse_momentum_test.py` 作为主运行入口
- [x] 3.2 实现结果聚合函数，统计各分组（动量最强至最弱）在所有触发日的平均均值
- [x] 3.3 进行 `py_compile` 语法校验并打印初步回测表格 (HTML/Markdown 格式)
