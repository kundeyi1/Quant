## 1. 结构与基础类重组

- [ ] 1.1 在 `factors/technical_factors.py` 中定义 6 个标准类：`PriceFactors`, `VolumeFactors`, `TrendFactors`, `VolatilityFactors`, `CrowdingFactors`, `Alpha101Factors`
- [ ] 1.2 迁移 `TrendFactors`: 包含 `symmetry`, `ma_compression`, `yellow_line`, `white_line`, `sma`, `ema`, `wma`, `ma_arrangement`, `macd`, `sar`, `adx`, `rsrs_norm` 并移除 `calculate_` 前缀
- [ ] 1.3 迁移 `PriceFactors`: 包含 `overhead_supply`, `price_percentile`, `price_bias` 并移除 `calculate_` 前缀
- [ ] 1.4 迁移 `VolumeFactors`: 包含 `obv`, `volume_bias`, `volume_volatility`, `volume_breakout`, `intraday_strength` 并移除 `calculate_` 前缀
- [ ] 1.5 迁移 `VolatilityFactors`: 包含 `bollinger_bands`, `bollinger_breakout`, `gx_atr_factor` 并移除 `calculate_` 前缀
- [ ] 1.6 迁移 `CrowdingFactors`: 包含 `high_pos_vol_risk`, `gx_hotspot` 并移除 `calculate_` 前缀
- [ ] 1.7 迁移 `Alpha101Factors`: 重命名所有 `alphaX` 函数移除 `calculate_`（如果存在），保持内部子集实现逻辑

## 2. 代码清理与优化

- [ ] 2.1 移除 `factors/technical_factors.py` 中重复的 `ma_arrangement` 逻辑
- [ ] 2.2 统一所有因子的 Docstrings 格式，确保不包含弃用的 `calculate_` 描述
- [ ] 2.3 检查并修复因移除 `calculate_` 前缀导致的内部调用冲突（如类静态方法间的互相调用）

## 3. 调用方同步与验证

- [ ] 3.1 全局搜索并定位所有引用 `factors/technical_factors.py` 的代码处（包括 `timing/market_timing.py` 和 `FactorTestAPI_new.py`）
- [ ] 3.2 批量更新调用方代码：将 `calculate_<name>` 替换为 `<name>` 并指定正确的类名
- [ ] 3.3 运行 `test_ht_timing.py` 验证择时功能在重构后是否依然正常
- [ ] 3.4 静态检查 `factors/technical_factors.py` 确保没有未定义的引用
