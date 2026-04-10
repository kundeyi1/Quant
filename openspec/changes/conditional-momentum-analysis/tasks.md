## 1. 核心计算模块与环境准备

- [x] 1.1 创建核心分析脚本 `conditional_momentum_analysis.py` 并导入 `DataManager` 与 `FactorTester`。
- [x] 1.2 实现 `calculate_rank_score(df)` 工具函数，用于日期维度的横截面 Rank 标准化。
- [x] 1.3 实现 `calculate_tail_probability(returns, threshold_quantile=0.9)`，计算右尾爆发概率。

## 2. Part 1：Trigger 因子基础分析（Baseline）

- [x] 2.1 编写 Trigger 因子 IC 时序计算逻辑（Rolling Mean 绘图）。
- [x] 2.2 实现全市场 vs Trigger Top/Bottom 收益分布对比绘图逻辑。
- [x] 2.3 完成 Trigger 因子的 5 组分层检验，输出各组平均收益与右尾概率（验证非线性）。

## 3. Part 2：因子切割（Factor Segmentation）逻辑

- [x] 3.1 实现 Env 因子的横截面 5 分位切割逻辑（Env Bins）。
- [x] 3.2 编写嵌套循环/向量化逻辑：在每个 Env Bin 内部评估 Trigger 的分层表现向。
- [x] 3.3 汇总输出各 Env Bin 下 Trigger 的 IC、ICIR、平均收益及右尾概率对比表。

## 4. Part 3：Sweet Spot 连续分位扫描

- [x] 4.1 实现滑动窗口环境扫描算法（窗口宽度 0.2，步长 0.05）。
- [x] 4.2 计算每个滑动窗口内的 Trigger 多空收益率及 P(r > 90%) 爆发指标。
- [x] 4.3 绘制 Sweet Spot Alpha 曲线，识别 Trigger 表现最优的环境区间。

## 5. 结果集成与验证

- [x] 5.1 封装所有 Part 为模块化函数，确保可通过参数指定 `trigger_name` 和 `env_name`。
- [x] 5.2 运行全流程测试，确保不使用未来数据且无性能瓶颈。
- [x] 5.3 按照用户要求输出结论解释的基础数据（非线性验证、切割有效性、Sweet Spot 定位）。
