## 1. ATR 动态阈值逻辑实现

- [x] 1.1 在 `calculate_rebound_signal_filter` 中计算 14 日 ATR
- [x] 1.2 实现 ATR 修正系数逻辑（$\sqrt{ATR/0.01}$ 等）
- [x] 1.3 引入计算 ATR 时需要的 `high`, `low`, `close` 列
- [x] 1.4 修改涨幅 $U'$ 和下跌 $D'$ 的有效值

## 2. 验证与归档

- [x] 2.1 检查 `filters/signal_filters.py` 语法并进行 py_compile 验证
- [x] 2.2 验证返回日期索引一致性
- [x] 2.3 完成任务后进行 OpenSpec 归档

