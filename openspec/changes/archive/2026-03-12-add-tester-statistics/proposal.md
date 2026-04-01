## Why

增强 `SparseSignalTester` 的统计评价能力。目前测试器仅输出简单的分组平均收益，缺乏对信号质量（IC/IR、胜率）以及极端组（多头/空头）超额收益的深度分析。增加这些指标有助于更全面地评估因子的选股能力和稳定性。

## What Changes

- 修改 `core/SparseSignalTester.py`：
    - 新增 `calculate_performance_stats` 方法，计算：
        - **IC / Rank IC 均值**：各触发日截面因子值与 T+period 收益的相关性。
        - **ICIR**：IC 均值 / IC 标准差。
        - **IC 胜率**：IC > 0 的比例。
        - **多头/空头未来 T+period 超额收益**：Group 5 和 Group 1 相对于截面平均值的超额收益。
- 更新所有 `run_gx_pit_*.py` 脚本：
    - 在运行完成后打印详细的统计报表。
    - 将统计结果保存到 `results/` 目录下的 CSV 文件中。

## Capabilities

### New Capabilities
- `tester-advanced-stats`: 在稀疏信号测试中集成 IC、ICIR、胜率及多空超额收益的计算与展示功能。

## Impact

- `core/SparseSignalTester.py`: 核心工具类升级。
- 所有使用该 Tester 的回测脚本：将获得更丰富的量化评价指标。
