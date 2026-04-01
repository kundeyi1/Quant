## 1. 结构与迁移准备

- [x] 1.1 在 `factors` 目录下新建 `huatai_timing_factors.py` 或将原有指标整合至最相关的因子文件内。
- [x] 1.2 在 `quant` 根目录创建全流程脚本文件 `run_huatai_timing_reproduction.py`。
- [x] 1.3 通过 `core/DataManager.py` 获取或封装研报指定的历史行情数据集引用，废弃 `quant_timing_system/data_fetcher.py`。

## 2. 指标重构与整合

- [x] 2.1 分析并重构原 `indicators.py` 内的 `ht_rsrs_norm(Z-Score)` 逻辑，在目标因子文件实现静态方法 `ht_rsrs_norm(df, N, M)`，使用 `core.NumericalOperators`。
- [x] 2.2 实现静态方法 `ht_price_bias(df, window)` 对应原 `ht_price_bias_timing` 乖离率。
- [x] 2.3 实现静态方法 `ht_bollinger(df, window)` 对应原布林线上界突破买入逻辑。
- [x] 2.4 实现静态方法 `ht_volume_bias(df, window)` 记录成交量乖离逻辑。
- [x] 2.5 实现静态方法 `ht_trend_strength(df, window)` 计算 ADX 阈值买入。
- [x] 2.6 实现静态方法 `ht_new_high(df, window)` 计算新高天数占比阈值。
- [x] 2.7 实现静态方法 `ht_volume_volatility(df, window)` 计算量能波动放大信号。
- [x] 2.8 整合打分器 `ht_integrated_timing(df)` 计算最终得分为 0~5 及最终 `3分做多` 离散信号。返回值必须是含日期索引的 `pd.DataFrame`。

## 3. 回测引擎对接

- [x] 3.1 阅读 `core/SparseSignalTester.py` 确保其输入接口签名（如事件触发日志、稀疏对齐机制等）适配第 2 步的输出 DataFrame。
- [x] 3.2 如果目前 `SparseSignalTester` 数据结构不支持仅在 `1` 时生成稀疏仓码的逻辑，在不破坏其他功能的前提下，对其进行微调适配（如有必要）。
- [x] 3.3 在 `run_huatai_timing.py` 导入 `SparseSignalTester`，向其注入历史价格列与第 2.8 步得到的择时信号源。

## 4. 全流程脚本与输出展示

- [x] 4.1 在 `run_huatai_timing.py` 中组装完整的运行管线：取数 -> 算因子 -> 输入打分 -> `backtest` 回测评价。
- [x] 4.2 接入可视化打印（若 SparseSignalTester 有 `plot`，直接调用 `plot` 生成基准与择时策略的净值曲线及回撤对比图）。
- [x] 4.3 在主线程运行一遍脚本抓取执行中产生的性能警报或运行期异常，确保运行通过。

## 5. 验证与清理

- [x] 5.1 数据校验：手动对比 `quant_timing_system/main.py` 原本的策略胜率与最大回撤，对比新脚本运行所计算出的指标偏差。
- [x] 5.2 清理阶段：确认逻辑闭环且运行稳定后，删除 `quant_timing_system` 目录及依赖清单，并更新项目主线 README 增加运行 `run_huatai_timing.py` 的介绍。