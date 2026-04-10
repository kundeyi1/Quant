## Context

在量化研究中，许多因子（如动量 Trigger）在全样本下表现出非线性或微弱的线性关系。通过引入环境因子（Env）进行“因子切割”，可以识别出在该 Trigger 有效的特定“甜点区域（Sweet Spot）”。本设计旨在提供一套标准化的工具集，用于执行条件因子分析、样本空间切割及最优环境区间搜索。

## Goals / Non-Goals

**Goals:**
- 实现基于 Env 因子的横截面分层能力（Factor Segmentation）。
- 支持在子样本空间内进行完整的因子评价（IC、分层收益、右尾概率 P(r > 90%)）。
- 实现自动化的 Sweet Spot 扫描算法，寻找使得 Trigger 效果最优的连续 Env 分位区间。
- 采用向量化计算逻辑，确保在处理大规模 D:\DATA\FACTORS 数据时的性能。
- 能使用 FactorTester、 NavAnalyzer 实现的功能就不要重复写。

**Non-Goals:**
- 不涉及多因子组合优化（仅关注单因子在条件约束下的表现）。
- 不涉及实盘执行逻辑。
- 不修改底层 DataManager 的读取协议。
- 不修改 FactorTester 的回测逻辑。
  
## Decisions

### 1. 因子标准化逻辑
- **Decision**: 强制使用横截面 Rank 标准化 `rank(pct=True)`。
- **Rationale**: 动量类因子往往存在量纲差异和极端值，Rank 标准化能有效处理非线性并确保不同日期间的可比性。

### 2. 因子切割（Segmentation）实现
- **Decision**: 采用 `pd.qcut` 或自定义分位函数对 Env 进行日期维度的横截面分组。
- **Rationale**: 确保每个 Env Bin 在每个时间点都有相近的样本量，避免因时间序列波动导致的样本偏差。

### 3. Sweet Spot 搜索算法
- **Decision**: 使用滑动窗口（Rolling Bracket）扫描。
- **Argument**:
  - 窗口宽度默认为 20%（0.2）。
  - 步长默认为 10%。
  - 指标评价：计算每个窗口内的 `mean_return` 或 `tail_probability`。
- **Alternatives**: 树模型分割（Decision Tree）。由于树模型易过拟合且解释性不直观，暂不采用，首选分位点滑动。

### 4. 分层测试器复用
- **Decision**: 复用 `core/FactorTester.py` 的核心逻辑，但需通过子集过滤（Masking）实现。
- **Rationale**: 保持统计指标（如单调性、ICIR）计算的一致性。

## Risks / Trade-offs

- **[Risk] 样本量不足** → **Mitigation**: 在计算分布指标（特别是右尾概率）时，若窗口内样本数低于阈值（如 30 只股票），则标记为无效数据或跳过。
- **[Risk] 未来数据泄露** → **Mitigation**: 严格确保 `future_return` 仅作为 Label，所有排序（Rank）和分组（Bin）仅基于 T 时点数据。
- **[Risk] 计算压力** → **Mitigation**: 使用 NumPy 广播机制处理分位桶分配，避免 Python 层面的循环。
