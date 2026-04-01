## Context

当前交易系统的信号测试分为两大类：**截面因子的数值评估** 和 **离散时点的择时评价**。过去这两个功能都勉强由 `core.SparseSignalTester` 承担，导致参数混杂，且由于底层逻辑（因子收益要求分层测试和截面 rank，而择时信号只要针对单标计算盈亏和胜负率并高亮持有区间）分化过大，`SparseSignalTester` 变得越来越庞大且难以维护。同时用户提出了绘制规范“择时净值（红线）与其回撤区间的双轴阴影图（叠加 Benchmark 如万得全A）”的直接需求，原有架构直接绘图存在较大困难。

## Goals / Non-Goals

**Goals:**
- 从 `core.SparseSignalTester` 中移除专门针对纯 0/1 离散点评价逻辑的代码。
- 新增独立的 `core.TimingTester` 专门进行择时（Timing）信号的回测，该类负责将输入的基准序和时点 0/1 序列转化为持有期的净值曲线。
- 新增双轴曲线绘制方法，分别画出择时净值的折线图与右轴的回撤浅灰色面积图。
- 确保调用逻辑将各类输出精准打入 `results/factor`（FactorTester专属）、`results/sparse_signal`（SparseSignalTester）和 `results/timing`（TimingTester专属）目录。

**Non-Goals:**
- 不涉及改变 `core.NumericalOperators` 算子逻辑或 `DataManager.DataProvider` 的核心获取功能。
- 不影响多空连续持仓回测引擎的发展（如果存在其他持续时间持仓如连续权重引擎）。

## Decisions

**分离测试器对象**
- 原有类 `SparseSignalTester` 将在入参进行收紧校验，更适用于如“事件驱动类数值预测（不同得分下的超额收益）”和常规因子评价的功能。它的 `output_dir` 主要指向 `results/sparse_signal`。
- 新建 `TimingTester` 类：
  - **Inputs**: `signal_series` (0/1 或 True/False 构成的 DataFrame 或 Series)，`benchmark_series`（如万得全A收盘价），以及持有期 `period`。
  - **Outputs**: 提供 `run_timing_analysis()` 函数，返回胜率特征。
  - **Plotting**: 提供 `plot_timing_nav_and_drawdown()` 函数，利用 `matplotlib.pyplot` 的 `fill_between` 画出带半透明浅灰区间的极大回撤右轴，并将左轴用来展示净值走向（参考示例图中样式：红色/暗红色择时净值，深蓝色基准归一化净值）。

**归一化处理**
- 为了能在同一数量级做对比，择时由于通常起始为 $1.0$，我们将 benchmark 在测试区间的首日净值强制除以该区间的初始值进行归一化。

## Risks / Trade-offs

- **重构风险**: 修改 `core.SparseSignalTester` 可能会影响当前正在依赖其 `n_groups=1` 单独计算分位分布的其他用例或脚本。
  - *缓冲策略*: 暂不对它进行毁灭式的删除核心计算，仅在它身上剥离并警告不推荐传入纯标量离散序列，同时鼓励向 `TimingTester` 迁移即可。
- **绘图格式兼容**: 用户的示图似乎存在复杂的刻度与中文字体显示支持。
  - *缓冲策略*: 在绘图逻辑中尝试加载 `plt.rcParams['font.sans-serif'] = ['SimHei']` 支持中文，同时容忍由于跨平台导致的缺字现象，如果缺少则使用默认字体。
