## Why

实现“行情转折点（切换）”信号过滤器。该信号通过结合“新高行业数量锐减”和“指数跌破波动率阈值”两个维度，捕捉市场顶部的潜在切换契机，用于指导仓位管理或风格切换。

## What Changes

- **新增过滤器**: 在 `filters/signal_filters.py` 中新增 `calculate_market_turning_point` 静态方法。
- **行业分析逻辑**: 需要计算每日创出 52 周（250 交易日）新高的行业数量，并对比 T-1 日的变化。
- **指数突破逻辑**: 计算中证全指（或指定基准）的当日跌幅，并判断是否超过其自身的 ATR60 波动率水平。
- **指标融合**: 只有当行业新高数减少 3 个或更多，且指数跌幅大于 ATR60 时，才触发 1 信号。

## Capabilities

### New Capabilities
- `market-turning-point`: 实现基于截面新高热度衰减和纵向波动率突破的复合行情转折识别能力。

### Modified Capabilities
- `technical-factors`: 确保 ATR60 计算逻辑在 `RiskFactors` 中定义清晰且可复用。

## Impact

1. `filters/signal_filters.py`: 新增核心过滤函数。
2. `core/DataManager.py`: 需要通过 `get_wide_table` 加载行业价格数据进行截面分析。
3. `factors/technical_factors.py`: 调用 `calculate_gx_atr_factor` 获取波动率参考。
