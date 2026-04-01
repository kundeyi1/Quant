## Why

捕捉市场在窄幅波动（三角形收缩）后的方向性突破机会。通过严格限定前 5 日的价格波动范围（绝对值 < 1%）并叠加通道收窄（T-1 通道宽度 < T-2 通道宽度）的逻辑，识别出波动率极端压抑后的爆发性上涨点。

## What Changes

- 在 `filters/signal_filters.py` 中实现 `calculate_triangle_breakout_filter`：
    - 判定 T-5 到 T-1 每日收益率绝对值均 < 1%。
    - 构建滚动 5 日最高/最低价通道（High/Low 5-day channel）。
    - 验证 T-1 日通道宽度（High-Low）小于 T-2 日。
    - 判定 T 日收益率 > 1%（向上突破）。
- 创建 `run_triangle_breakout_test.py` 脚本：
    - 加载中证全指及行业数据。
    - 计算上述信号。
    - 使用 `SparseSignalTester` 进行因子分组（T日涨幅分5组）并输出可视化报告。

## Capabilities

### New Capabilities
- `triangle-breakout-filter`: 提供基于历史低波动及通道收敛状态判定 T 日爆发性上涨的信号过滤器。

### Modified Capabilities
- 无

## Impact

- `filters/signal_filters.py`: 新增静态方法。
- `run_triangle_breakout_test.py`: 全新测试入口。
- 不影响现有 API。
