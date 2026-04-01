## 1. 核心加载逻辑实现

- [x] 1.1 确认 `DataProvider` 中的 `base_path` 指向逻辑（优先 D:/DATA）
- [x] 1.2 确认 `load_and_preprocess` 中的 `encoding='gbk'` 兼容中国行情数据 CSV
- [x] 1.3 验证 `code` 字段的 `zfill(6)` 实现并移除后缀

## 2. 字段映射与清洗验证

- [x] 2.1 修改 `get_fundamental_data` 以包含完整的映射关键字（'secucode', '报告期' 等）
- [x] 2.2 确认 `date` 字段通过 `pd.to_datetime` 进行解析
- [x] 2.3 验证基本面数据的 `value` 字段自动探测逻辑

## 3. 标准化文档与归档

- [x] 3.1 完成 `standardize-data-pipeline` 变更下的各项任务
- [x] 3.2 运行 `openspec archive` 将数据流水线规范持久化

