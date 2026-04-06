## Why

当前的 `gx_pit_mom.py` 择时逻辑虽然基于物理量（如 breakout, rebound, rotation），但指标维度仍相对有限，主要集中在趋势和反转的单一形态。为了更全面地捕捉市场状态，需要建立一套标准的、可扩展的物理择时因子库（Physical Metrics），并引入动量确认（Momentum Confirmation）机制，以解决单一技术形态在缺乏动量配合时可能出现的假信号问题，进一步提升行业轮动信号的确定性。

## What Changes

- **核心逻辑迁移**：新建测试入口文件 `pit_mom.py`，作为后续统一的时点动量测试框架。
- **物理因子集成**：引入基于价格位置（Price Dist）、量能偏离（Volume Bias）、趋势强度（Trend Strength）、波动率（Volatility）等更丰富的物理量化指标。
- **确认逻辑增强**：实现“技术准入信号（Setup） + 3% 当日指数涨幅确认（Confirmation）”的两阶段复合触发逻辑。
- **行业池扩展**：支持中信一级（yjhy）与二级（ejhy）行业的动态切换与轮动检验。
- **差异化检验逻辑**：**强调仅在信号触发的具体位置（Trigger Points）采用基于当日动量的分配逻辑，所有非信号触发位置的系统行为与原 `gx_pit_mom.py` 保持严格一致（如空仓或基准维持）**。
- **权重策略标准化**：统一采用择时信号触发当日（T日）全天各行业的涨跌幅作为获取超额收益的动量分配依据。

## Capabilities

### New Capabilities
- `physical-timing-metrics`: 提供一系列基于绝对比例、原始数值和物理形态（如地量、价格高位等）的择时指标库。
- `two-stage-trigger-engine`: 处理“预警信号 + 确认涨幅”的两阶段触发逻辑，确保择时信号具备动量配合。

### Modified Capabilities
- `market-timing`: 扩展对物理阈值判断的支持，不再局限于布林带或 RSRS 等单一指标。
- `sparse-signal-testing`: 优化对特定时点（触发日）截面动量的提取效率，并标准化 T+20 持有期的统计报表。

## Impact

- `core.DataManager`: 确保能够高效提供中信二级（ejhy）行业的宽表价格数据。
- `pit_mom.py`: 作为主测试脚本，调用上述新增能力。
- `results/timing`: 生成标准化的物理择时回测报告与净值曲线。
