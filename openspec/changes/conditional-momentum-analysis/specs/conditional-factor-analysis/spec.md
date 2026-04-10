## ADDED Requirements

### Requirement: 因子切割分析能力
系统必须支持基于一个或多个环境因子（Env）对目标因子（Trigger）进行条件样本切割的能力。

#### Scenario: 成功按 Env 分位切割
- **WHEN** 用户提供 `trigger_factor` 和 `env_factor`
- **THEN** 系统应按日期对 `env_factor` 进行横截面分层（默认为 5 组），并针对每个分层（Env Bin）输出 `trigger_factor` 的表现统计。

### Requirement: 右尾分布概率统计
系统必须提供计算收益率分布尾部（右尾）概率的功能，用于量化不规则分布的“爆发力”。

#### Scenario: 计算 90% 分位右尾概率
- **WHEN** 计算 `future_return_1d` 或 `future_return_5d`
- **THEN** 系统应计算并返回在特定因子组内 `future_return > quantile(0.9, all_market)` 的概率 P(r > 90%)。

### Requirement: Sweet Spot 滑动窗口搜索
系统必须支持对环境因子空间的连续分位进行滑动窗口扫描，以发现 Trigger 因子最有效的“甜点区间”。

#### Scenario: 自动搜索最优 Env 区间
- **WHEN** 设置滑动窗口宽度为 0.2（20% 分位），步长为 0.05
- **THEN** 系统应遍历 [0, 0.2], [0.05, 0.25], ..., [0.8, 1.0]，并计算每个区间内 Trigger 的多空收益或 IC，输出表现随 Env 变化的 Alpha 曲线。

## MODIFIED Requirements

### Requirement: FactorTester 指标扩展
<!-- FROM: core/specs/tester-advanced-stats/spec.md -->
系统应扩展现有的因子测试能力，支持条件约束下的分布统计指标。

#### Scenario: 通用测试器集成右尾概率
- **WHEN** 调用 `FactorTester` 进行常规因子分析
- **THEN** 系统除了输出常规的 Mean Return、ICIR 外，还必须输出各组的 `Right-Tail-Freq`（右尾频率）指标。
