# Backtest Metrics Calculation Spec

## Requirement

在 `SparseSignalTester` 中，必须能够从生成的净值序列中计算出标准的量化指标。

### Metrics Definitions

- **Annualized Return**: `(1 + TotalReturn) ^ (252 / Days) - 1`
- **Sharpe Ratio**: `(AnnualizedReturn - RiskFree) / (StandardDeviation * sqrt(252))`
- **Max Drawdown**: `max(1 - CumulativeReturn / RunningMax)`

### Scope

- 需要支持对 `pd.Series` (净值曲线) 的直接计算。
- 特别针对 `Spliced Equity Curve` 进行计算。

# Visual Localization Spec

## Requirement

为了符合本土研究习惯，所有生成的图表必须使用中文标题。

### Mapping Table

- `Signal Trigger Points` -> `信号触发位置 (上证指数背景)`
- `Annual Signal Frequency` -> `年度信号触发频率`
- `Avg Group Excess Performance` -> `各分组平均超额表现 (T+20)`
- `Equity Curve (Daily Signal Return Cumprod)` -> `信号触发点累乘净值 (Alpha)`
- `Continuous (Time-Spliced) Equity Curve` -> `多空组合连续净值 (Alpha)`
- `L/S/LS Combined Equity Curve` -> `多头/空头/对冲组合表现对比`
- `Signal Timing Effectiveness Distribution` -> `信号时点收益分布 (择时有效性)`
