## Why

旨在验证动量类因子（Trigger）在不同市场环境因子（Env）约束下的非线性收益特征。通过“因子切割（Factor Segmentation）”逻辑，探究 Trigger 因子在不同 Env 分层下的表现差异，并以此寻找 Alpha 收益的“甜点区域（Sweet Spot）”。

## What Changes

- **实现因子切割逻辑**：按照环境因子（Env）的分位值，将全市场样本切分为不同的子环境（Env Bins）。
- **非线性触发器分析**：在每个 Env Bin 内部，对 Trigger 因子进行横截面标准化、IC 计算、分层检验及右尾概率（P(r > 90%)）统计。
- **Sweet Spot 搜索**：引入滑动窗口（Rolling Window）环境扫描，从连续分位角度寻找 Trigger 因子表现最优的 Env 区间。
- **可视化输出**：生成分层净值曲线、收益分布对比图及 Sweet Spot Alpha 曲线。

## Capabilities

### New Capabilities
- `factor-segmentation-analysis`: 实现基于环境因子的基准样本切割。
- `sweet-spot-discovery`: 实现对环境连续分位空间的扫描与最优区间识别。
- `distribution-tail-stats`: 新增对收益率分布尾部（如 P(r > 90%)）的常态化统计能力。

### Modified Capabilities
- `tester-advanced-stats`: 扩展常规因子测试指标，集成右尾概率等分布测度。

## Impact

- `core/FactorTester.py`: 适配条件分层测试。
- `results/conditional_alpha/`: 存储切割后的分层结果。
- `results/factors/trigger`: 存储 Trigger 因子的检验结果