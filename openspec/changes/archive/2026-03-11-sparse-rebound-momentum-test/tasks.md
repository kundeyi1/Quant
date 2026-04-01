## 1. 核心测试逻辑模块设计 (Core Implementation)

- [x] 1.1 在 `core` 目录下创建 `SparseSignalTester.py` 文件并引入基础依赖
- [x] 1.2 实现 `SparseSignalTester` 类，定义 `__init__` 以接收因子数据 and 信号数据
- [x] 1.3 编写 `_extract_cross_section` 内部方法，支持根据掩码日期提取因子向量
- [x] 1.4 实现 `calculate_group_returns` 方法，计算 T+1 到 T+20 的累积百分比收益

## 2. 因子计算与适配 (Factor & Data Alignment)

- [x] 2.1 修改 `DataManager.py` 或新建专用逻辑支持读取中证 500 (`000985.CSI.xlsx`) 价格数据
- [x] 2.2 在 `DataManager` 中开发自适应读取宽表 (`D:\DATA\INDEX\ZX\ZX_YJHY.csv`) 的逻辑，自动进行数据对齐
- [ ] 2.3 调用 `SignalFilters.calculate_rebound_signal_filter` 生成指数的 0-1 反弹掩码

## 3. 可视化与验证 (Visualization & Validation)

- [x] 3.1 在 `SparseSignalTester.py` 中实现信号位置可视化方法（画竖线显示触发点）
- [x] 3.2 实现分组收益直方图绘制，风格参考现有的 `FactorVisualizer` 模块
- [ ] 3.3 创建 `run_sparse_momentum_test.py` 主程序完成端到端测试，产出完整可视化结果
- [x] 3.4 进行 `py_compile` 语法校验并归档
