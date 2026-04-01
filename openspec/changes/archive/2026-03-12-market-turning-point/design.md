## Context

当前系统已具备基础的过滤器架构和 `RiskFactors.calculate_gx_atr_factor` 波动率计算能力。用户需要一种能够捕捉市场顶部过热后的“转折点”信号，该信号通过观察行业层面高位个股/行业的“拥挤度”消退（体现为新高行业数量减少）以及指数层面的波动率向下突破来确认。

## Goals / Non-Goals

**Goals:**
- 在 `filters/signal_filters.py` 中实现 `calculate_market_turning_point` 方法。
- 正确计算行业层面的 52 周新高数量，并识别其变动逻辑。
- 集成 ATR 波动率作为指数跌幅的动态阈值。
- 确保在大规模数据集（全行业、长周期）下计算效率。

**Non-Goals:**
- 不涉及交易执行逻辑。
- 不在此变更中修改现有的 `DataManager` 加载逻辑。

## Decisions

- **Decision 1: 行业新高计算方案**
  - **Choice**: 使用 `rolling(250).max()` 处理行业价格宽表，判断 `price == rolling_max`。
  - **Rationale**: 52 周约为 250 个交易日。使用矩阵运算比循环遍历每个行业快得多。
  - **Alternatives**: 逐一行业判断，但效率极低。

- **Decision 2: 信号触发阈值参数化**
  - **Choice**: 默认 `n_decrease=3` 和 `window_atr=60`。
  - **Rationale**: 用户明确指出“减少 3 个或更多”，且使用 `ATR60`。
  - **Alternatives**: 硬编码，但不便于后续调参优化。

- **Decision 3: ATR 引用**
  - **Choice**: 直接调用 `factors.technical_factors.RiskFactors.calculate_gx_atr_factor`。
  - **Rationale**: 保持公式一致性，避免重复实现 TR/ATR 逻辑。

## Risks / Trade-offs

- **[Risk] 数据对齐缺陷** → **Mitigation**: 在计算前对行业宽表和指数数据进行 `intersection` 索引对齐，确保 $T$ 日在两个数据集中是同一天。
- **[Risk] 行业数据缺失** → **Mitigation**: 如果某日行业价格缺失，计算出的新高数量可能会出现大幅波动导致误触发。通过 `dropna` 排除包含过多缺失值的列。
- **[Risk] ATR 初始化期** → **Mitigation**: ATR 前 60 天为 NaN，此时应不输出信号（保持 0）。
