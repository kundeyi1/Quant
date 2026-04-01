# system-cleanup Specification

## Purpose
This specification tracks the deprecation and removal of legacy components and directories from the workspace to ensure a clean and integrated codebase.

## Requirements

### Requirement: 删除或隔离独立子系统
系统 MUST 在新的适配全流程落地后，在主目录提供完整链路实现（即新增的 `run_huatai_timing_reproduction.py` 统一入口），并且逐步清除（或移除到废弃区）原来的 `quant_timing_system` 目录资源。

#### Scenario: 统一入口取代老式工程
- **WHEN** 所有的 `data_fetcher.py`, `indicators.py`, `backtest.py`, `main.py` 代码均已被集成并利用主线库机制完成对接时
- **THEN** `quant_timing_system` 内的执行及实现可被安全删除而不影响项目主流程。
