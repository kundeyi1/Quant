## Why
当前 `gx_pit_mom` 框架仅支持 3 种择时信号，不足以匹配市场全部的关键形态，存在寻参（Parameter Hunting）和过拟合的风险。通过接入多维度的择时信号源，可以提高系统对多样化市场环境的捕捉能力，减少对单一参数逻辑的依赖。

## What Changes
- **信号库扩展**: 将原来的 `gx_pit_mom` 功能迁移并扩展，接入 `ht_rsrs`, `ht_bollinger`, `w_bottom`, `hs_bottom` 等新增择时指标。
- **验证流程优化**: 
    - 针对 **000985 (中证全指)** 进行回测实验。
    - **单点检验**: 对所有单个时点信号进行绩效评价。
    - **组合检验**: 对多信号组合后的时点进行整体绩效评价。
- **架构解耦**: 允许 `GXPITMomTester` 动态调用 `report_timing.py` 和 `pattern_timing.py` 中的函数。

## Capabilities

### New Capabilities
- `comprehensive-timing-signals`: 整合趋势、量能、形态等多种异构信号源。
- `single-point-evaluation`: 对每一个触发的时点信号进行客观绩效评价。
- `fused-timing-evaluation`: 对组合后的密集信号集进行系统性绩效评价。

### Modified Capabilities
- `timing-engine`: 扩展原有调度逻辑以支持更多类型的信号分发。

## Impact
- `gx_pit_mom.py`: 核心执行逻辑将重构，以支持多信号并行计算与评价。
- `timing/`: 统一各择时函数在宽表和标准 OHLC 数据下的输入输出规范。
