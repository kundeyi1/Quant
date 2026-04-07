## 1. 核心库实现 (factors/combination.py)

- [x] 1.1 实现静态方法 `FactorCombiner.equal_weight` (Z-score + Mean)
- [x] 1.2 实现 `FactorCombiner.ic_ir_weight` (Normalize weight and synthesis)
- [x] 1.3 实现 `FactorCombiner.orthogonalize_factors` (Sequential Gram-Schmidt Orthogonalization)
- [x] 1.4 实现 `FactorCombiner.compute_multiplicative_alpha` (Environment * Trigger)
- [x] 1.5 实现 `FactorCombiner.compute_sigmoid_gate_alpha` (Sigmoid-based soft gating)
- [x] 1.6 实现 `FactorCombiner.optimization_regression` (Cross-sectional regression synthesis)

## 2. 调试与验证 (run_factor_combination.py - Initial Setup)

- [x] 2.1 整合数据加载逻辑 (DataProvider + FactorTester for returns)
- [x] 2.2 实现演示示例：加载因子 -> 正交化 -> 计算 Env/Trigger Score -> 生成 alpha_mul/alpha_gate
- [x] 2.3 验证输出结构：检查各合成方法的输出 Series 是否与 index (date, stock) 对齐

## 3. 实验脚本编写 (run_factor_combination.py - Full Pipeline)

- [ ] 3.1 编写 `run_all_methods` 核心循环，直接调用 `FactorTester.backtest` 进行评估
- [ ] 3.2 支持 1d/5d/20d 三种周期的对比验证
- [ ] 3.3 输出全栈合成方法对比表，汇总各方法的 ICIR 与分组收益曲线
