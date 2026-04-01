## 1. 核心类与逻辑迁移 (Architectural Refactor)

- [x] 1.1 在 `core/TimingTester.py` 中建立基础结构，并从 `SparseSignalTester.py` 迁移 `plot_timing_distribution`, `plot_signals`, `plot_annual_frequency`, `export_trigger_log`。
- [x] 1.2 重构 `SparseSignalTester.py`，移除冗余的择时分析代码，并添加指向 `TimingTester` 的兼容性包装（Wrapper）。
- [x] 1.3 验证 `TimingTester` 能够对 0/1 择时信号矩阵进行独立绩效评价。

## 2. GXPITMomTester 信号引擎扩展 (Engine Expansion)

- [ ] 2.1 修改 `gx_pit_mom.py` 中的 `calculate_timing` 方法，接入 `report_timing.py` 中的华泰择时指标 (`ht_rsrs`, `ht_bollinger`, `ht_volume_volatility` 等)。
- [ ] 2.2 在 `gx_pit_mom.py` 中引入对 `pattern_timing.py` 的调用，接入 `double_bottom` (W底) 和 `head_shoulder_pattern` (头肩底) 等形态信号。
- [ ] 2.3 统一各新信号的输出格式，确保其为标准的二进制 (0/1) 触发矩阵。

## 3. 绩效评价与回测集成 (Evaluation & Backtest)

- [ ] 3.1 在 `gx_pit_mom.py` 中增加对单单时点信号（Single-Point）的评价调用逻辑。
- [ ] 3.2 实现对融合后密集信号集（Fused-Point）的整体绩效评价，并使用 `TimingTester` 生成报告。
- [ ] 3.3 运行 000985（中证全指）的完整测试流程，生成包含多维度择时性能指标的最终报告。

## 4. 验证与清理 (Validation)

- [ ] 4.1 静态检查代码变更，确保无 `FutureWarning` 或循环引用。
- [ ] 4.2 验证 `SparseSignalTester` 仍能正常运行其核心的分组回测功能。
