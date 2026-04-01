## MODIFIED Requirements

### Requirement: 标准化输出
Factor methods within the standardized classes SHALL NOT include the `calculate_` prefix. All factor methods SHALL return results with the same date index as the input `pd.DataFrame`, and methods returning multiple columns SHALL return a `pd.DataFrame`.

#### Scenario: 因子 API 调用
- **WHEN** 调用任意因子方法 (e.g., `TrendFactors.ma_arrangement(data)`)
- **THEN** 返回对象的索引 SHALL 与输入数据对齐，且方法名不再包含 `calculate_` 格式

## RENAMED Requirements

### Requirement: 均线排列因子 (MA Arrangement)
FROM: `calculate_ma_arrangement`
TO: `ma_arrangement`

### Requirement: 对称因子 (Symmetry Factor)
FROM: `calculate_symmetry`
TO: `symmetry`
Note: This requirement MUST be moved to `TrendFactors` based on the standardized catalog.

### Requirement: 趋势指数 (Trend Index)
FROM: `calculate_short_term_trend` / `calculate_long_term_trend`
TO: `short_term_trend` / `long_term_trend`

### Requirement: 平滑动量因子 (Momentum Factor)
FROM: `calculate_gx_momentum_factor`
TO: `gx_momentum_factor`
Note: This requirement MUST be moved to `MomentumFactors` (or `TrendFactors` based on refined logic).
