## Context

当前实现为静态阈值。由于市场波动率 (ATR) 的变化，固定的 5% 下跌或 0.5% 反弹在不同时点所代表的显著性水平不同。

## Goals / Non-Goals

**Goals:**
- 在 `calculate_rebound_signal_filter` 内部计算 14 日 ATR（以价格百分比形式）。
- 实现 $\sqrt{x}$ 形式的动态阈值倍数。
- 保证历史区间 $M$ 的搜索逻辑兼容动态变化。

**Non-Goals:**
- 不改变函数的输入参数签名 (保持 $u=0.005, d=0.05$)。

## Decisions

- **ATR实现**: 使用 `talib.ATR(high, low, close, timeperiod=14) / close` 来获得相对波动率。
- **阈值修正**: 
  - $ATR < 0.01 \Rightarrow scale = \sqrt{ATR / 0.01}$
  - $0.01 \le ATR \le 0.02 \Rightarrow scale = 1.0$
  - $ATR > 0.02 \Rightarrow scale = \sqrt{ATR / 0.02}$
- **性能**: ATR 只在一开始计算一次，不影响后续遍历。

## Risks / Trade-offs

- **ATR计算依赖**: 依赖 TA-Lib 的 `ATR` 函数。
  - **Mitigation**: 确保 `signal_filters.py` 中已导入 `talib`。
