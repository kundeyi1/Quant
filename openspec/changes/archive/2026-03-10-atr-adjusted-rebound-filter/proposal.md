## Why

固定的反弹阈值（0.5%）和下跌阈值（5%）在不同波动率的市场环境下表现不一。在低波动环境下，5% 的下跌难以达到；而在高波动环境下，0.5% 的反弹可能只是噪音。通过引入基于 ATR（平均真实波幅）的动态调整机制，可以使信号过滤器更具适应性。

## What Changes

- 修改 `calculate_rebound_signal_filter` 函数，引入 ATR 计算及其对应的阈值修正系数。
- **ATR < 1%**: 修正系数 = $\sqrt{ATR / 0.01}$
- **1% <= ATR <= 2%**: 修正系数 = 1.0
- **ATR > 2%**: 修正系数 = $\sqrt{ATR / 0.02}$
- 最终阈值 = 初始阈值 $\times$ 修正系数。

## Capabilities

### Modified Capabilities
- `rebound-signal-filter`: 增加基于 ATR 的动态阈值调整逻辑。

## Impact

- `filters/signal_filters.py`: 函数逻辑更新。
- 依赖项：需要 ATR 计算（通常使用 TA-Lib）。
