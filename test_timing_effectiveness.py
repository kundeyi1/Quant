import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from core.Logger import logger

# 设置绘图风格
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def run_timing_test():
    """
    择时有效性评估脚本 (通用基准)
    1. 加载基准数据 (如 000985.CSI)。
    2. 加载示例稀疏信号。
    3. 调用 run_timing_analysis 验证择时效果。
    """
    dp = DataProvider(base_data_path="D:/DATA")
    
    # 1. 基础数据加载 (用户自定义基准)
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    start_date = "2013-01-01"
    end_date = "2026-12-31"

    logger.info(f"加载择时分析基准数据: {index_file}")
    target_index = dp.get_ohlc_data(index_file)
    if target_index is None:
        logger.error("基准数据加载失败")
        return
    
    # 限定测试时间范围
    target_index = target_index.loc[start_date:end_date]
    benchmark_close = target_index['close']

    # 2. 模拟/加载信号驱动
    # 默认加载 000985.CSI 作为示例，用户可替换为信号文件路径
    sparse_signal_path = "D:/DATA/SPARSE_SIGNAL"
    signal_file = "gx_pit_mom_fused_yjhy.parquet" 
    full_signal_path = os.path.join(sparse_signal_path, signal_file)

    if not os.path.exists(full_signal_path):
        logger.warning(f"信号文件 {full_signal_path} 不存在，构造示例 Dummy 信号进行逻辑测试。")
        trigger_dates = benchmark_close.pct_change().abs().sort_values(ascending=False).head(50).index
        fused_factor_df = pd.DataFrame(index=benchmark_close.index, columns=['000001.SZ'])
        fused_factor_df.loc[trigger_dates, '000001.SZ'] = 1.0
    else:
        logger.info(f"加载信号文件进行分析: {signal_file}")
        fused_factor_df = pd.read_parquet(full_signal_path)

    # 3. 运行 SparseSignalTester
    output_path = "results/timing_test_report"
    tester = SparseSignalTester(
        signal_series=fused_factor_df, 
        price_df=pd.DataFrame({'000001.SZ': benchmark_close}),
        benchmark_series=benchmark_close,
        period=20, 
        n_groups=5,
        output_dir=output_path
    )
    
    # 4. 核心：执行择时分析 (Timing Analysis)
    logger.info("开始执行基准择时显性检验...")
    timing_stats = tester.run_timing_analysis(period=20)
    
    if timing_stats:
        # 5. 可视化择时分布 (统一 bins)
        logger.info("生成分布对比图...")
        tester.plot_timing_distribution(title="Signal Timing Effectiveness Distribution")
        
        print("\n" + "="*50)
        print("择时有效性评估完成！")
        print(f"Quantile Rank: {timing_stats['quantile_rank']*100:.2f}%")
        print(f"P-Value:       {timing_stats['p_value']:.4f}")
        print(f"结果目录: {tester.output_dir}")
        print("="*50)
    else:
        logger.error("择时评估未产生有效结果。")

if __name__ == "__main__":
    run_timing_test()
