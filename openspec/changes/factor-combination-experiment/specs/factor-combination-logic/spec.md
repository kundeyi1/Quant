## ADDED Requirements

### Requirement: 等权组合 (Equal Weight)
系统必须支持对输入的因子 DataFrame 进行横截面 Z-score 标准化，并在日期维度上取所有因子的算术平均值。

#### Scenario: 成功生成等权复合因子
- **WHEN** 输入包含多个因子列且索引为 (date, stock) 的 DataFrame
- **THEN** 系统返回一个 Series，其值为对应日期下标准化因子的平均值

### Requirement: IC_IR 加权组合
系统必须支持根据预设的 IC_IR 字典或 Series，对标准化后的因子进行加权求和，权重应归一化（权重绝对值之和为 1）。

#### Scenario: 按历史表现进行加权
- **WHEN** 提供因子 DataFrame 和 `ic_ir = {"FactorA": 0.5, "FactorB": 1.5}`
- **THEN** 系统计算归一化权重并返回加权后的复合 Series

### Requirement: 回归权重优化 (optimization)
系统必须支持对输入的因子与目标收益进行逐日横截面回归（Cross-sectional Regression），并将所得回归系数进行时间序列平均，以此作为全局静态合成权重。

#### Scenario: 提取全局平均回归系数
- **WHEN** 调用回归合成函数并输入 `factors` 与 `future_return`
- **THEN** 系统在内部执行逐日 `LinearRegression`，并输出按全局 $\bar{\beta}$ 加权后的 Series

### Requirement: 秩合成 (Rank-based Fusion)
系统必须支持将每个因子转换为横截面分位数（Percentile Rank），随后进行等权或 IC_IR 加权的线性组合。

#### Scenario: 消除异常值干扰的秩合成
- **WHEN** 设置合成模式为 "rank"
- **THEN** 系统先对原始因子执行 `rank(pct=True)`，再进行后续加权操作

### Requirement: 分层结构合成 (Hierarchical Structure)
系统必须支持将因子池划分为 `environment_factors`（环境/慢变量）和 `trigger_factors`（触发/快变量），分别合成后取乘积作为最终 Alpha。

#### Scenario: 环境与触发因子的联合作用
- **WHEN** 指定两组因子列表
- **THEN** 系统计算 `env_score` 和 `trigger_score` 的乘积

### Requirement: 门控模型 (Gate Model)
系统必须通过连续的 `sigmoid` 函数对环境评分进行转化，作为触发评分的增益开关。

#### Scenario: 基于 Sigmoid 的软门控
- **WHEN** 输入 `env_score` 与 `trigger_score`
- **THEN** 系统返回 `sigmoid(env_score) * trigger_score` 的计算结果
