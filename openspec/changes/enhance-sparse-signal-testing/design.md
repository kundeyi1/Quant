## Context

当前 `SparseSignalTester` 在 `continuous_real_timeline` 模式下的实现存在严重逻辑缺陷：它仅记录了信号区间端点（信号触发日和持有结束日）的净值，而非真实的日度波动。
这导致了两个核心问题：
1. **信息缺失**: 信号持有期间真实的日度回撤和收益波动没有在曲线上体现。
2. **绘图异常**: 由于只选取了少量离散端点，Matplotlib 在两点间直接连线，无法表现出空仓期间的“水平横盘”以及持仓期间的“曲线波动”。

## Goals / Non-Goals

**Goals:**
- **重构净值生成算法**: 确保 `continuous_real_timeline` 模式生成覆盖全历史交易日的真实日收益率序列（空仓日=0，持仓日=真实日收益）。
- **专业可视化集成**: 调用 `NavAnalyzer` 对重构后的完整收益率序列进行绘图。
- **完善绩效评估**: 整合超额夏普、累计超额、年度 IC 等指标到指定报表。

**Non-Goals:**
- 不涉及稀疏信号测试中其余绘图代码的重构（如 `discrete` 模式）。

## Decisions

### 1. 绘图策略与 NavAnalyzer 集成 (解耦设计)
- **方案**: 解耦“连续净值图”与“离散信号图”。
- **连续图 (continuous_real_timeline)**: 在 `_calculate_continuous_strategy_returns` 中构造全量日收益率序列（空仓补0），完成后调用 `core.NavAnalyzer` 的专业绘图接口。
- **离散图 (discrete/others)**: 用于观察信号触发点的即时效果，保持在 Tester 内部使用 Matplotlib 绘制，不使用 NavAnalyzer，因为这些数据点不构成连续时间序列。

### 2. 统计汇报与报表结构 (Reporting & Tables)
- **新功能**: 实现一个专用函数封装“完整时间轴收益率生成 + NavAnalyzer 调用”逻辑。
- **报表结构**:
    - `performance_summary_report.csv`: 整合胜率、盈亏比、年度 IC、超额夏普比率、累计超额。
    - `nav_report.csv`: 专注于多头/多空组合的核心回撤与年化指标。

### 3. 指数汇总表计算逻辑 (Metrics Calculation)
- **胜率**: `count(p_end > p_start) / count(signals)`
- **年度 IC**: 按年度的方式计算其 IC 表现。

### 4. 可视化美化 (Visual Improvements)
- 去除 `markers='o'` 的硬连线，改为纯线段。
- 增加背景阴影 (Fill Between) 以标注信号活跃区（可选）。

## Risks / Trade-offs

- **[Risk]**: 信号重叠处理风险。
- **Mitigation**: 保持现有逻辑——新信号触发时强行截断旧信号持仓，并根据新信号调仓。
- **[Trade-off]**: 全时间计算量增加。
- **Mitigation**: 稀疏信号通常频率极低（每年数十次），Pandas 全时间轴操作（数千行）性能开销极低，可忽略。
