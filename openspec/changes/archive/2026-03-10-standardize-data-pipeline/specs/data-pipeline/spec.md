## ADDED Requirements

### Requirement: 统一路径管理规则
系统 SHALL 支持多级路径查找，以兼容不同的运行环境（本地磁盘 vs 相对路径）。

#### Scenario: 路径优先级
- **WHEN** 实例化 `DataProvider`
- **THEN** 系统 SHALL 优先检查输入路径。若为空，则 SHALL 检查 `D:/DATA`。若仍不存在，则 SHALL 回退到项目根目录。

### Requirement: 标准化字段映射 (Normalization)
数据加载后 SHALL 映射为统一的内部列名，以方便后续计算。

#### Scenario: 基本面列名映射
- **WHEN** 加载基本面 CSV 或 Excel 数据
- **THEN** 系统 SHALL 将变体列名（'secucode', '代码', '证券代码'）映射为 `code`，将日期变体（'enddate', '报告期', '截止日期'）映射为 `date`。

### Requirement: 核心数据清洗规则
所有资产数据在输出前 SHALL 经过标准化的清洗流程。

#### Scenario: 证券代码格式化
- **WHEN** 处理股票代码列
- **THEN** 系统 SHALL 确保代码为 6 位数字字符串（补 0），并移除可能存在的后缀（如 .SH/.SZ）。

#### Scenario: 日期解析
- **WHEN** 处理日期值
- **THEN** 系统 SHALL 使用 `pd.to_datetime` 进行解析，且日期列中 SHALL 不存在空值（NaN）。

### Requirement: 异常 Excel 处理逻辑
系统 SHALL 能够处理已损坏或带有复杂样式的 Excel 文件。

#### Scenario: Excel 加载降级
- **WHEN** 默认读取 Excel 失败（如由于 xl/styles.xml 错误）
- **THEN** 系统 SHALL 尝试通过 zip 操作移除样式定义或使用兼容引擎重新加载数据，并记录日志。
