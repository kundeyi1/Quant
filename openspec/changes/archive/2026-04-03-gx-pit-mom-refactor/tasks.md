## 1. 基础设施与数据层

- [x] 1.1 创建 `D:\DATA\TIMING` 目录。
- [x] 1.2 在 `timing/market_timing.py` 中新增持久化工具函数，支持 Parquet 读写及文件名生成逻辑。
- [x] 1.3 实现 `check_signal_exists` 工具逻辑，基于信号类型、起止日期和参数进行路径校验。

## 2. 核心模块整合

- [x] 2.1 创建 `gx_pit_mom.py` 文件框架，引入 `DataManager`, `SparseSignalTester`, `market_timing`。
- [x] 2.2 实现 `calculate_and_save_timing` 逻辑，封装 `breakout`, `rebound`, `rotation` 的调用并实现幂等检查。
- [x] 2.3 实现 `calculate_and_save_sparse_factor` 逻辑，计算反弹当日收益/突破当日收益等并持久化。

## 3. 运行入口与接口

- [x] 3.1 在 `gx_pit_mom.py` 中增加参数解析逻辑，支持指定 `sector_type` (yjhy/ejhy) 及 `signals_to_run`。
- [x] 3.2 封装批量回测循环，遍历所选信号，加载择时信号 -> 计算稀疏因子 -> 调用 `SparseSignalTester`。
- [x] 3.3 将原有三个测试脚本中的特有逻辑（如 breakout 的波动控制、rebound 的 20 日日均对比）整合进函数内部。

## 4. 验证与清理

- [x] 4.1 运行测试脚本，确认择时信号已正确保存至 `D:\DATA\TIMING`。
- [x] 4.2 验证当文件已存在时，系统是否确实跳过了计算。
- [x] 4.3 确认二级/一级行业切换无误。
- [ ] 4.4 可选：移除冗余的旧测试文件，保留新入口作为唯一标准。
