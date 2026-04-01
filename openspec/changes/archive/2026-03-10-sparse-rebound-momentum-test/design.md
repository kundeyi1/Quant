## Context

当前项目中已有大量的因子计算逻辑（`TrendFactors`, `MomentumFactors`）和信号生成逻辑（`SignalFilters`），但缺乏专门的回测模块。现有的 `FactorTester` 倾向于分析全样本（全时间段、全截面）的 IC 值，而**稀疏信号（Sparse Signal）**（如基于指数反弹触发的点位）需要对离散的时点进行针对性统计。

## Goals / Non-Goals

**Goals:**
- **解耦逻辑**: 将“触发信号生成”、“因子值提取”、“业绩统计”三个环节解耦。
- **支持多资产对齐**: 处理指数（作为 Mask）与行业（作为 Universe）之间的数据对齐。
- **稀疏统计**: 实现持有期（如 T+20）累积收益的离散聚合。

**Non-Goals:**
- **实时交易**: 不涉及实时高频订单接口。
- **参数调优**: 自动遍历上千组参数不在第一阶段 scope 内。

## Decisions

### 1. 核心回测类 `SparseSignalTester`
- **方案**: 在 `core/` 下新建 `SparseSignalTester` 类。
- **理由**: 独立于现有的 `FactorTester`。稀疏测试需要不同的 DataFrame 索引处理逻辑（如 `np.where(mask == 1)`），独立成类可保持代码简洁。

### 2. 行业数据加载 (DataManager 增强)
 - **补充**: 中信一级行业索引位于 `D:/DATA/INDEX/ZX/ZX_YJHY.csv`，该文件采用 Wind 导出格式（特定的列名与编码方式）。系统 MUST 使用 `core.DataManager` 的 Wind 解析器或等效接口来读取并返回标准化的 OHLC DataFrame（列名: `open, high, low, close, volume`, 索引为日期）。

### 3. 持有期收益计算方式
- **方案**: 采用日频收益率连乘法（$\prod (1+r_i) - 1$），持有期固定为 20 个交易日。
 **[Risk] 指数/行业数据格式差异 (Wind 格式 vs 其他)** → **Mitigation**: 在 `DataManager` 中提供针对 Wind 格式文件（例如 `D:/DATA/INDEX/ZX/ZX_YJHY.csv`）的专用读取方法或参数开关；读取过程必须校验并映射列名到统一格式，否则抛出可识别的错误以便快速修正输入数据。
## Risks / Trade-offs

- **[Risk] 样本量过小导致偏差** → **Mitigation**: 在统计结果中显著标示每一组的原始事件样本数（Sample Size），若样本数少于 5 个则发出警告。
- **[Risk] 指数数据格式不一 (Excel vs CSV)** → **Mitigation**: 在 `DataManager` 中提供针对特定指数文件（如 `000985.CSI.xlsx`）的专用读取方法或参数开关。
