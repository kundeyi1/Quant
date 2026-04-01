# data-pipeline Specification

## Purpose
TBD - created by archiving change standardize-data-pipeline. Update Purpose after archive.
## Requirements
### Requirement: 统一路径管理规则
系统 SHALL 支持多级路径查找，以兼容不同的运行环境（本地磁盘 vs 相对路径）。

#### Scenario: 路径优先级
- **WHEN** 实例化 `DataProvider`
- **THEN** 系统 SHALL 优先检查输入路径。若为空，则 SHALL 检查 `D:/DATA`。若仍不存在，则 SHALL 回退到项目根目录。

### Requirement: 获取并整合所需数据
系统 MUST 支持通过项目默认路径 `D:/DATA`（或相对路径退路）读取华泰打分择时系统所需要的日线级基础行情数据（如 OHLCV），不再依赖原 `quant_timing_system/data_fetcher.py`。

#### Scenario: 加载市场基准及行业数据
- **WHEN** 用户或脚本调用执行回测流程时
- **THEN** 主框架的 `core` 中的 `DataManager` 成功加载目标时间段的日线行情 DataFrame，且包含所需的基础列如 open, high, low, close, volume。

### Requirement: 标准化字段映射 (Normalization)
数据加载后 SHALL 映射为统一的内部列名，以方便后续计算。

#### Scenario: 基本面列名映射
- **WHEN** 加载基本面 CSV 或 Excel 数据
- **THEN** 系统 SHALL 将变体列名（'secucode', '代码', '证券代码'）映射为 `code`，将日期变体（'enddate', '报告期', '截止日期'）映射为 `date`。

### Requirement: Wind Metadata & Footer Handling
系统 SHALL 支持自动识别和剔除 Wind/iFind 数据导出中的元数据行和页底备注。

#### Scenario: Header Identification
- **WHEN** 数据框的前 15 行包含关键词（指标名称, 频率, 单位, 指标id, 来源, 指标ID）
- **THEN** 这些行 SHALL 被认为是元数据并被剔除。

#### Scenario: Footer Identification
- **WHEN** 数据框的末尾行包含关键词（数据来源:Wind, 数据来源:iFind, 数据来源：w）
- **THEN** 这些行 SHALL 被认为是页底备注并被剔除。

#### Scenario: Date Column Identification
- **WHEN** 系统查找日期列时，SHALL 搜索以下关键字：`date`, `日期`, `time`, `时间`, `trade_date`, `trade_dt`, `s_info_date`, `s_info_tradedate`。
- **THEN** 系统 SHALL 优先使用匹配到的列名，若无匹配，则 SHALL 尝试第一列，并处理可能的 Excel 序列号格式。

### Requirement: 核心数据清洗规则
所有资产数据在输出前 SHALL 经过标准化的清洗流程。

#### Scenario: 证券代码格式化
- **WHEN** 处理股票代码列
- **THEN** 系统 SHALL 确保代码为 6 位数字字符串（补 0），并移除可能存在的后缀（如 .SH/.SZ）。

#### Scenario: 日期解析
- **WHEN** 处理日期值
- **THEN** 系统 SHALL 使用 `pd.to_datetime` 进行解析，且日期列中 SHALL 不存在空值（NaN）。

#### Scenario: 缺失值与零值区分 (NA vs Zero)
- **WHEN** 因子计算结果包含缺失值时
- **THEN** 系统 SHALL 严格保留 `NaN` 以表示“无数据”或“无信号”，禁绝在数据管道中进行无差别 `fillna(0)` 填充，除非 `0` 具有明确的业务含义。

### Requirement: 异常 Excel 处理逻辑
系统 SHALL 能够处理已损坏或带有复杂样式的 Excel 文件。

#### Scenario: Excel 加载降级
- **WHEN** 默认读取 Excel 失败（如由于 xl/styles.xml 错误）
- **THEN** 系统 SHALL 尝试通过 zip 操作移除样式定义或使用兼容引擎重新加载数据，并记录日志。

