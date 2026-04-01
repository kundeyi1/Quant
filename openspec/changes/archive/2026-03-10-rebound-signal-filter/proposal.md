## Why

在量化交易中，识别大跌后的强力反弹信号是极佳的入场机会。本项目需要引入一个“大跌反弹信号掩码”（Rebound Signal Filter），通过结合当日涨幅和历史下跌深度，自动化地识别出这类高胜率的交易时机。

## What Changes

- 在 `filters/signal_filters.py` 中新增 `calculate_rebound_signal_filter` 函数。
- 实现基于特定涨幅阈值 $U$ 和下跌深度阈值 $D$ 的逻辑判断。
- 支持处理变长的历史区间 $M$ 以寻找阶段性高低点。

## Capabilities

### New Capabilities
- `rebound-signal-filter`: 能够根据当日反弹幅度、区间高低点位置关系及下跌幅度，生成时间序列上的 0/1 掩码信号。

## Impact

- `filters/signal_filters.py`: 代码新增。
- 策略脚本：可调用该 filter 进行信号过滤或策略组合。
