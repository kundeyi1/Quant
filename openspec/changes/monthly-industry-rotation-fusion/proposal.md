## Why

当前时点动量融合因子主要用于稀疏信号触发时的短期持仓回测。为了进一步验证该逻辑在常规因子化研究中的价值，需要将其转化为月度截面因子，支持标准的行业轮动模型测试和因子评价体系。

## What Changes

- **因子化逻辑**: 将稀疏信号触发转换为月度固定频率因子。每个月末回看过去10个交易日，对窗口内的信号因子进行Rank转换和半衰加权。
- **因子存储**: 将计算出的因子保存为指定格式（zxyjhy_gx_pit_mom_factor/zxejhy_gx_pit_mom），存放于 `D:/DATA/factors` 目录。
- **评价体系**: 使用标准的因子检验方法（IC/IR、分组收益、换手率等）对月度融合因子进行检验。

## Capabilities

### New Capabilities
- `monthly-momentum-rotation`: 实现月度频率的信号回看、 Rank 融合及因子文件持久化。
- `industry-factor-evaluation`: 提供对月度频率行业因子的标准化检验接口和报告。

### Modified Capabilities
- `time-weighted-momentum-fusion`: 可能需要将时点融合逻辑抽象或提取出来供月度模型复用。

## Impact

- `factors/monthly_rotation_factors.py`: 新建模块用于计算和保存月度融合因子。
- `core/FactorTester.py`: 确保月度行业轮动因子的检验逻辑与之兼容。
- `run_monthly_rotation_test.py`: 新建集成测试脚本执行流程。
