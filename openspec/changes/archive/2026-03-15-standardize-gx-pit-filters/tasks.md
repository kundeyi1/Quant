## 1. 重构基础辅助方法

- [x] 1.1 在 `SignalFilters` 类中实现私有方法 `_standardize_ohlc_input(data)` 用于统一处理 OHLC 和宽表输入。
- [x] 1.2 将通用的 ATR 阈值缩放逻辑直接植入需要使用的各 `calculate_gx_pit_*` 方法中。
- [x] 1.3 移除 `atr_volatility_filter` 独立函数，确保不再有独立的 ATR 过滤入口。

## 2. 标准化 GX PIT 过滤器实现

- [x] 2.1 重构 `calculate_gx_pit_rebound_filter`，改用 1.1 和 1.2 中定义的私有方法。
- [x] 2.2 重构 `calculate_gx_pit_breakout_filter`，确保其数据适配逻辑与 1.1 一致，并检查是否需要引入 ATR 缩放 (按 spec 要求保持一致性)。
- [x] 2.3 重构 `calculate_gx_pit_rotation_filter`，确保其 ATR 计算和数据对齐逻辑遵循统一标准。

## 3. 验证与清理

- [x] 3.1 运行静态检查，确保 `factors.technical_factors` 的引用正确且无语法错误。
- [x] 3.2 确认所有 GX PIT 过滤器函数的返回格式 (pd.Series, 0-1 掩码) 依然符合预期。
- [x] 3.3 (可选) 搜索工作区中显式调用 `atr_volatility_filter` 的地方并更新之。
