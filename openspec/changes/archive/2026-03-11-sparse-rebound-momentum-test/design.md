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
- **方案**: 在 `DataManager` 中添加对 `D:\DATA\INDEX\ZX\ZX_YJHY.csv` 的自适应支持。
- **架构建议**: 识别宽表（Wide-form）格式，即每一列代表一个行业、每一行代表一个日期。在加载时自动通过 `transpose` 或 `stack/unstack` 转换为计算兼容的长表格式。

### 3. 持有期收益计算方式
- **方案**: 采用日频收益率连乘法（$\prod (1+r_i) - 1$），持有期固定为 20 个交易日。
- **理由**: 复用 `TrendFactors.calculate_gx_momentum_factor` 的输出。动量因子通常在 20 日（一月左右）具有最好的选股效果。

### 4. 可视化设计 (Visualization)
- **技术**: 使用 `Matplotlib` 或 `Plotly` 在 `FactorVisualizer` 风格之上扩展。
- **模块集成**: 为 `SparseSignalTester` 提供独立的 `plot_signals` 接口，用 `ax.axvline` 绘制信号位。
- **直方图风格**: 柱状图配色与样式与现有 `FactorTester` 及其可视化工具类保持一致，便于分析师视觉统觉。

## Risks / Trade-offs

- **[Risk] 样本量过小导致偏差** → **Mitigation**: 在统计结果中显著标示每一组的原始事件样本数（Sample Size），若样本数少于 5 个则发出警告。
- **[Risk] 指数数据格式不一 (Excel vs CSV)** → **Mitigation**: 在 `DataManager` 中提供针对特定指数文件（如 `000985.CSI.xlsx`）的专用读取方法或参数开关。
