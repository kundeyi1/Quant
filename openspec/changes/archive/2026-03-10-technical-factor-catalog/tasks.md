## 1. 核心趋势因子规范化

- [x] 1.1 在 [factors/technical_factors.py](factors/technical_factors.py) 中验证 `TrendFactors` 的各种 `calculate_` 方法命名规范
- [x] 1.2 确认 `calculate_ma_arrangement` 采用滚动均线偏离度之和逻辑
- [x] 1.3 确认 `calculate_short_term_trend` 与 `calculate_long_term_trend` 的计算逻辑一致性

## 2. 动量与对称因子规范化

- [x] 2.1 验证 `calculate_momentum_factor` 的 (Return0 - MeanReturn20) 算法
- [x] 2.2 验证 `calculate_symmetry` 的波峰波谷斜率比值计算正确性
- [x] 2.3 验证 `calculate_white_line` 的双重 EMA 算法一致性

## 3. 结果验证与文档归档

- [x] 3.1 确认所有因子返回格式均为 pd.DataFrame 且具有原始日期索引
- [x] 3.2 运行 `openspec archive` 将技术因子库归档

