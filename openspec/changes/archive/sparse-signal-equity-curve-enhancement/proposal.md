## Why

当前 `SparseSignalTester` 的净值曲线（Equity Curve）仅支持离线离散点的简单累乘，无法模拟实际交易中的“信号触发即调仓”或“持有期重叠/空仓”等复杂情况。为了更真实地评估离散信号在连续时间序列上的表现，需要引入更贴近实盘逻辑的净值计算方式。

## What Changes

- **信号驱动调仓模式 (Signal-Driven Rebalancing)**: 在 $T$ 日持有期内若出现新信号 $T'$，则立即在 $T'$ 日进行仓位切换，不再持有原信号至 $T+20$。
- **连续时间净值计算 (Continuous Equity Curve)**: 
    - 模式 1: 信号衔接抹平。信号间的空白期视为不持仓（收益为 0），曲线保持平直。
    - 模式 2: 真实时间周期。不对中间空余时间进行抹平，保留真实的时间轴步进，信号触发时通过调仓逻辑衔接。
- **可视化增强**: 增加参数选项目前默认的离散累乘曲线与新增的两种连续曲线。

## Capabilities

### New Capabilities
- `continuous-equity-curve`: 实现基于信号触发动作的连续时间序列净值计算逻辑，支持调仓覆盖、空白期处理及对应的可视化绘图。

### Modified Capabilities
- `sparse-signal-testing`: 修改 `run_backtest` 或 `plot_equity_curve` 的接口，允许用户选择不同的净值生成逻辑。

## Impact

- `core/SparseSignalTester.py`: 核心修改文件，需重构或新增净值生成私有方法。
- 各 `run_gx_pit_*.py` 脚本: 可选更新，用于调用新的绘图模式。
