## 1. 核心信号逻辑实现

- [x] 1.1 在 `filters/signal_filters.py` 中定义 `calculate_rebound_signal_filter`
- [x] 1.2 实现 $T$ 日收盘涨幅判断逻辑
- [x] 1.3 实现寻找 $T-1$ 往前最长连续低涨幅区间 $M$ 的逻辑
- [x] 1.4 实现区间 $M$ 内最高点早于最低点且距离 $>2$ 的约束检查
- [x] 1.5 实现下跌幅度 $(1 - Close_{low} / Close_{high}) > D$ 的过滤

## 2. 验证与文档


- [x] 2.1 检查 `filters/signal_filters.py` 语法并进行 py_compile 验证
- [x] 2.2 验证返回为具有相同日期索引的 Series 或 DataFrame
- [x] 2.3 完成任务后进行 OpenSpec 归档


