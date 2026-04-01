## 1. 结构迁移与重构

- [x] 1.1 创建 `timing/` 目录并初始化 `__init__.py`
- [x] 1.2 创建 `timing/market_timing.py` 并实现基础辅助函数 `_standardize_input`
- [x] 1.3 将 `filters/signal_filters.py` 中的 `calculate_gx_pit_breakout_filter` 迁移为平铺函数 `gx_pit_breakout`
- [x] 1.4 将 `filters/signal_filters.py` 中的 `calculate_gx_pit_rebound_filter` 迁移为平铺函数 `gx_pit_rebound`
- [x] 1.5 将 `filters/signal_filters.py` 中的 `calculate_gx_pit_rotation_filter` 迁移为平铺函数 `gx_pit_rotation`

## 2. 择时逻辑实现 (HT & GX-PIT Methods)

- [x] 2.1 实现 `ht_rsrs_norm` 函数：计算滚动回归斜率及其正态化 Z-Score（依据华泰参数）
- [x] 2.2 实现 `ht_trend_regime` 函数：计算华泰定义的双均线多头排列逻辑（使用默认 5/60 参数）
- [x] 2.3 实现 `ht_volume_regime` 函数：计算华泰体系下的量价突破评分逻辑
- [x] 2.4 实现 `ht_technical_score` 综合评分函数：整合各维度得分（连续信号）

## 3. 全局适配与验证

- [ ] 3.1 批量更新 `run_gx_pit_...` 系列脚本，将 `filters` 引用替换为 `timing.market_timing`
- [x] 3.2 运行 `run_gx_pit_breakout_test.py` 验证迁移后的逻辑是否与原结果一致
- [x] 3.3 运行 `run_gx_pit_rebound_test.py` 验证迁移后的逻辑一致性
- [x] 3.4 编写并运行 `test_ht_timing.py` 验证华泰择时指标的可视化合理性
- [x] 3.5 确认所有择时函数均通过 `core/NumericalOperators.py` 调用底层算子，无多余循环
- [x] 3.6 (清理) 自主迁移完成，旧逻辑已整合至 `timing/`
