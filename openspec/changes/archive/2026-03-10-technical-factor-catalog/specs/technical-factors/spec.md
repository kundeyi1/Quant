## ADDED Requirements

### Requirement: 均线排列因子 (MA Arrangement)
系统 SHALL 支持根据不同窗口期的均线（5, 10, 20, 60）计算均线排列的离散程度。
公式：$\text{score} = \sum \frac{MA_{short} - MA_{long}}{MA_{long}}$。

#### Scenario: 多头排列
- **WHEN** 给定收盘价序列
- **THEN** 系统计算所有指定窗口期的均线，并逐级计算相邻均线的相对偏离度之和

### Requirement: 趋势指数 (Trend Index)
系统 SHALL 提供统一的短/中/长期趋势指数逻辑。
公式：$100 \times \frac{Close - LLV(Low, N)}{HHV(Close, N) - LLV(Low, N)}$。

#### Scenario: 滚动趋势计算
- **WHEN** 指定 N 日窗口
- **THEN** 系统使用滚动最低价 (LLV) 和历史最高价 (HHV) 计算当前价格在区间内的分位水平

### Requirement: 对称因子 (Symmetry Factor)
系统 SHALL 能够衡量价格从波峰回调至波谷的速率比值。

#### Scenario: 波峰波谷斜率比
- **WHEN** 在给定的回看窗口内发现波峰及之后的波谷
- **THEN** 系统 SHALL 计算 `(波峰到当前斜率) / (波峰到波谷斜率)`

### Requirement: 平滑动量因子 (Momentum Factor)
系统 SHALL 支持基于过去平均收益率的动量差值计算。
公式：$Return_{0} - \text{rolling\_mean}(Return, 20)$。

#### Scenario: 动量因子计算
- **WHEN** 收益率序列可用
- **THEN** 系统由当前收益率减去过去 20 个交易日的平均收益率，以捕捉动能变化

### Requirement: 标准化输出
所有 `calculate_` 方法 SHALL 返回包含结果并具有原始日期索引的 `pd.DataFrame`。

#### Scenario: 因子 DataFrame 输出
- **WHEN** 调用任意因子计算函数
- **THEN** 返回对象的列名 SHALL 与因子函数名或其缩写对应，索引 SHALL 与输入数据对齐
