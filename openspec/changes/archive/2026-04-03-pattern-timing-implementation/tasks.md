## 1. 环境准备与数据加载

- [x] 1.1 在 `timing/pattern_timing.py` 中初始化外部 `PatternPy` 路径 (sys.path)
- [x] 1.2 集成 `DataProvider` 并加载 `000985.CSI.xlsx` 的原始 OHLCV 数据
- [x] 1.3 调用core中的'DataManager', 实现 `_standardize_patternpy_input` 函数，确保 DataFrame 列名符合 `PatternPy` 要求（如小写化的 open, high, low, close, volume）

## 2. 形态识别逻辑集成

- [x] 2.1 集成 `head_and_shoulders` 及 `inverse_head_and_shoulders` 识别逻辑
- [x] 2.2 集成 `multiple_tops_bottoms` 及 `triangles` (Ascending/Descending) 识别逻辑
- [x] 2.3 集成 `wedges` 与 `channels` 识别逻辑
- [x] 2.4 实现统一的 `run_pattern_recognition` 循环，遍历并应用选定的模式识别函数

## 3. 结果打印与持久化

- [x] 3.1 实现择时信号触发点的控制台实时打印 (Filtered for non-NaN results)
- [x] 3.2 实现结果的并列分区存储：将每个模式列导出为独立的 `.parquet` 文件，路径指向 `timing/`
- [x] 3.3 验证输出文件命名格式：`<pattern_name>_000985(写为被识别的文件名).parquet`

## 4. 验证与测试

- [x] 4.1 执行 `pattern_timing.py` 脚本，检查是否有库缺失或路径报错
- [x] 4.2 检查 `timing/` 目录下 Parquet 文件的生成是否完整且数据列无误
- [x] 4.3 对比 000985 的历史关键高低点，验证识别结果的合理性
