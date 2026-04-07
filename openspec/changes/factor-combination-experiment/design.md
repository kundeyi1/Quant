## Context
当前研究中有一系列针对启动K线（ignition bar）的横截面因子（因子放在了factor_validation.py中），且已准备好未来收益（1d, 5d）数据。

## Goals / Non-Goals

**Goals:**
- 实现 **全栈因子合成与优化框架**，涵盖从线性到非线性、从静态到动态的多种方法。
- 实现 **顺序正交化 (Sequential Orthogonalization)**，提取因子间的独立信息。
- 构建 **Optimization 命名空间**，包含回归优化、IC权重优化等。
- 支持 1d, 5d, 20d 等多周期性能闭环评估。

**Non-Goals:**
- 实现新的底层因子（专注于合成逻辑）。
- 开发新的可视化工具（复用 `FactorVisualizer`）。

## Decisions

### 1. 因子合成方法矩阵 (Synthesis Matrix)

#### A. 基础线性类 (Linear Baseline)
- **Equal Weight**: 全因子 Z-score 后取均值。
- **Rank Fusion**: 分位数化（Rank）后再等权。
- **IC / IC_IR Weighting**: 基于长期 IC/IC_IR 期望值进行加权。

#### B. 结构化与非线性类 (Structural & Non-linear)
- **Sequential Orthogonalization**: 逐日 Gram-Schmidt 正交化，提取边际增量。
- **Hierarchical (Env x Trigger)**: 分层乘法结构 ($E \times T$)。
- **Sigmoid Gate Model**: 基于连续函数的软切换门控。

#### C. 权重优化类 (Optimization Namespace)
- **Cross-sectional Regression**: 逐日回归提取 $\beta$，并支持滚动窗口平均。
- **Rolling IC Optimization**: 基于动态滚动 IC 表现调整实时合成权重。

### 2. 代码组织与复用
- **逻辑层**: `factors/combination.py` 仅负责生成 `composite_alpha`（Series）。
- **评估层**: 直接调用 `FactorTester.backtest`，复用其 IC、分层回测及绘图逻辑。
- **数据层**: 使用 `FactorTester.get_forward_returns` 准备 1d/5d/20d 前瞻收益率。
