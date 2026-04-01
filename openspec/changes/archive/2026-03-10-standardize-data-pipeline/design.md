## Context

[core/DataManager.py](core/DataManager.py) 主要由 `DataProvider` 类和 `load_and_preprocess` 顶层函数组成。当前的实现试图通过复杂的 `try-except` 和 `if-else` 分支来覆盖多种数据源，但缺乏统一的行为标准，特别是多级查找路径和降级机制的实现细节。

## Goals / Non-Goals

**Goals:**
- 实现健壮的 `load_and_preprocess` 函数，支持 GBK 编码（适配中国行情数据）。
- 标准化基本面数据获取方法 `get_fundamental_data` 的列提取逻辑。
- 确保所有的 `date` 被解析为 `datetime` 对象，所有的 `code` 为 Zfill(6)。

**Non-Goals:**
- 不支持流式实时数据接入（仅限固态文件读取）。
- 不对数据进行大规模 SQL 存储，仅保留在内存（DataFrame）。

## Decisions

- **实现机制**: 利用 Python 的 `pathlib` 改进路径拼接的跨平台兼容性。
- **缺失处理**: 在 `get_fundamental_data` 中，若未找到显式的 `value` 列，则系统将按位置探测首个可能的数值列。
- **错误降级**: 引入自定义的 Excel 修复逻辑（通过二进制读取重构 zip 包），以解决一些量化数据导出文件的样式冲突问题。

## Risks / Trade-offs

- **解析开销**: 复杂的列名模糊匹配和数值探测可能增加启动时的 CPU 开销。
  - **Mitigation**: 建议在生产环境中通过预定义的配置文件（Config）明确定义列映射。
- **硬编码路径**: 默认的 `D:/DATA` 具有平台依赖性。
  - **Mitigation**: 已加入 `project_root` 回退方案。
