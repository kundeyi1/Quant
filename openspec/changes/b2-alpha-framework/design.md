## Context
当前量化研究代号为 `b2_alpha`，致力于捕捉 A 股市场“启动 K 线”带来的超额收益。
核心在于建立“条件动量”体系：从全市场 (Universe=Full) 入手，识别趋势背景下的压缩爆发点。
代码库已有 `core/FactorTester.py` 和 `factors/technical_factors.py`，需整合 b2 专属因子。

## Goals / Non-Goals

**Goals:**
- **因子扩展**: 在 `PriceFactors` 等类中新增反映趋势、压缩、位置、启动强度的 12 个连续因子。
- **全市场视角**: 回测范围设置为全市场单日截面。
- **b2 研究脚本**: 建立 `strategy_b2.py` 脚本，演示包含预处理、计算、打分、回测的完整链路。
- **规范命名**: 因子命名直接映射数学逻辑（如 `amplitude_ratio`），禁止使用 `calculate_` 前缀。

**Non-Goals:**
- **选股逻辑**: 重点在于因子对收益的连续解释能力，而非简单的买入规则。
- **其他文件修改**: 仅限 artifact 修改及后续因子/脚本创建。

## Decisions

- **因子风格**: 全部向量化计算，使用 `pandas` 和 `core.NumericalOperators`。
- **回测引擎**: 沿用 `FactorTester` 全截面。
- **多因子合成**: 提供 z-score 标准化后的等权 (Equal-weighted) 合成逻辑。
- **标签对齐**: 必须显式处理 `shift(-1)` 计算未来收益，并确保回测时无未来函数。

## Risks / Trade-offs

- **[Risk] 全市场数据内存占用**: 计算全市场因子涉及大量股票。
  - **Mitigation**: 充分利用向量化操作，避免 for 循环。
- **[Trade-off] 灵活性 vs 封装性**: 
  - 选择在脚本/Notebook 中实现顶层流程而非全封装，以便灵活调整合成权重。
