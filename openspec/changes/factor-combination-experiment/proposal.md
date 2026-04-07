## Why
建立一套系统性的因子合成（Combination）实验框架，对比不同合成算法（等权、IC_IR、回归、分层、门控等）在相同因子池下的性能表现。此举旨在通过科学的合成方法提高复合因子的 IC 稳定性及多头组收益。

## What Changes
- 创建 `factors/combination.py`：核心库，包含 6 种因子合成算法（新增顺序正交、分层乘法结构、Sigmoid 门控）。
- 创建 `run_factor_combination.py`：主实验脚本，负责加载数据、调用合成函数、处理 1d/5d 未来收益率并对接 `FactorTester`。
- 将涉及优化权重的逻辑（如回归或潜在的协方差优化）命名为 `optimization` 模块。

## Capabilities

### New Capabilities
- `factor-orthogonalization`: 实现顺序正交化（Sequential Orthogonalization），提取因子间的独立信息。
- `factor-combination-logic`: 提供 Equal Weight, IC_IR, Regression, Hierarchical (Env x Trigger), Gating (Sigmoid) 等合成算子。
- `factor-weight-optimization`: 处理基于历史表现或横截面回归的权重优化逻辑。
- `performance-benchmark-1d-5d`: 自动化对比不同合成方法在 1d 和 5d 预测周期下的表现。

### Modified Capabilities
- 无（完全复用现有 `FactorTester` 的 backtest 功能）。

## Impact
- **库依赖**: 添加 `sklearn.linear_model`。
- **项目结构**: 在 `factors/` 下新增 `combination.py`。
- **工作流**: 以后验证新因子时，可以快速将其放入实验框架评估对整体合成结果的贡献。
