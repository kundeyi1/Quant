# Pattern Recognition for Market Timing

## Purpose
The purpose of the `pattern-timing` capability is to recognize complex technical patterns (e.g., Head and Shoulders, Triangles) using specialized libraries like `PatternPy` and evaluate their effectiveness as market timing signals.

## Requirements

### Requirement: 集成 PatternPy 择时功能
系统 SHALL 在 `timing/pattern_timing.py` 脚本中成功调用 `PatternPy` 包。

#### Scenario: 成功调用 PatternPy 识别头肩顶
- **WHEN** 脚本启动并添加 `D:\Dev\PatternPy` 到 Python 路径
- **THEN** 能够正常执行 `from patternpy.tradingpatterns import head_and_shoulders` 且不报错

### Requirement: 000985.CSI 指数数据加载
系统 SHALL 使用 `DataProvider` 加载并标准化 000985.CSI.xlsx 的行情数据。

#### Scenario: 加载指数数据列一致性
- **WHEN** 调用 `dp.get_ohlc_data` 加载 000985 价格数据
- **THEN** 返回的 DataFrame 包含 `open, high, low, close, volume` 五个核心字段

### Requirement: 单因子 Parquet 文件保存
系统 SHALL 将识别出的每种交易模式（Pattern）分别保存为独立的 Parquet 文件。

#### Scenario: 持久化头肩顶形态因子
- **WHEN** `head_and_shoulders` 计算完成后返回形态标记 DataFrame
- **THEN** 对应的 `000985_head_and_shoulders.parquet` 文件生成在 `timing/` 目录下

### Requirement: 择时结果实时打印
系统 SHALL 在每种模式计算完成后，将非空（即识别出模式）的触发日期及对应形态打印输出。

#### Scenario: 自动报告触发点
- **WHEN** 脚本在某一历史日期识别 out `Inverse Head and Shoulder` 形态
- **THEN** 在控制台实时打印该触发讯息，方便研究员即时核对
