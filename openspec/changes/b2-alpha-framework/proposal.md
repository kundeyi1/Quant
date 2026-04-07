## Why
实现一个代号为 `b2_alpha` 的 Python 量化研究框架，专门用于捕捉 A 股市场的“启动 K 线（Ignition Bar）”。该策略的核心是识别在经历波动率与成交量双重压缩后的爆发性机会，预测未来 1-3 日的短期超额收益。

## What Changes
- **b2 因子库扩展**: 在 `factors/technical_factors.py` 中新增符合业务逻辑的连续型因子类，反映趋势、压缩、位置及启动强度。
- **全市场回测流**: 基于 `core/FactorTester.py` 实现全市场（Universe=Full）的因子 IC 评估与分层回测。
- **b2 研究流程**: 创建 `strategy_b2.py` 或相关脚本，整合数据获取、因子计算（向量化）、标签构建与绩效分析。

## Capabilities

### New Capabilities
- `b2-core-factors`: 包含趋势（trend_strength, trend_slope）、压缩（volatility_ratio, volume_ratio）、位置（pullback_depth, position）及强度（momentum_acceleration, body_strength）的因子集合。
- `b2-cross-sectional-analysis`: 全截面因子评估能力，支持全市场股票池的 IC/IR 计算与 5 分层回测。

### Modified Capabilities
- `technical-factors`: 扩展现有因子类，增加 b2 策略专属的指标函数。

## Impact
- **代码库**: 主要修改 `factors/technical_factors.py`，新增 `strategy_b2.py`。
- **API**: 因子计算函数采用功能性命名（如 `volatility_ratio`），不加 `calculate_` 前缀。
- **数据**: 使用全市场日线行情数据。

