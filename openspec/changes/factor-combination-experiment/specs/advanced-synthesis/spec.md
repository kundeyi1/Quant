## ADDED Requirements

### Requirement: 顺序正交化 (Sequential Orthogonalization)
系统必须支持在每一个交易日进行逐列回归取残差的横截面正交化。

#### Scenario: 提取独立 Alpha
- **WHEN** 输入因子矩阵与排序。
- **THEN** 输出正交后的 DataFrame。

### Requirement: 动态 IC 权重优化 (Rolling IC Optimization)
系统必须支持基于过去 $N$ 天的滚动 IC 值动态计算权重。

#### Scenario: 因子权重的动态衰减与增强
- **WHEN** 设置 `window=20`。
- **THEN** 系统根据过去 20 天的平均 IC 调整当前权数。

### Requirement: 分层与门控结构 (Hierarchical & Gating)
系统必须支持 $E \times T$ 乘法结构与 Sigmoid 连续软门控。

#### Scenario: 环境过滤逻辑验证
- **WHEN** 指定环境因子与触发因子。
- **THEN** 输出对应结构的 Composite Alpha。
