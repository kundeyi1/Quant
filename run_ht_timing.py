import os
import sys
import pandas as pd
import numpy as np
import warnings

# 避免相对路径导入问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.DataManager import DataProvider
from timing.report_timing import (
    ht_rsrs_timing, 
    ht_price_bias_timing, 
    ht_bollinger_timing, 
    ht_new_high_timing
)
from core.TimingTester import TimingTester

warnings.filterwarnings('ignore')

def run_factor_backtest(factor_name, signal_series, benchmark_series):
    """
    通用因子/信号回测函数
    """
    factor_output_dir = os.path.join("results/timing", factor_name)
    print(f"\n正在回测: {factor_name} -> {factor_output_dir}")
    
    tester = TimingTester(
        signal_series=signal_series, 
        benchmark_series=benchmark_series, 
        output_dir=factor_output_dir
    )
    
    stats = tester.backtest()
    tester.plot_nav(title=f"{factor_name} 择时净值表现", filename=factor_name)
    tester.plot_signals(title=f"{factor_name} 择时信号分布", filename=factor_name)
    
    ann_ret = stats.get('annual_return', 0)
    sharpe = stats.get('sharpe_ratio', 0)
    max_dd = stats.get('max_drawdown', 0)
    
    print(f"[{factor_name}] 年化: {ann_ret:.2f}%, 夏普: {sharpe:.2f}, 最大回撤: {max_dd:.2f}%")

def main():
    print("="*60)
    print("华泰技术择时体系 - 逻辑修正版 (Boll/新高占比/阴影修正)")
    print("="*60)

    # 1. 加载数据
    file_path = r"D:\DATA\INDEX\STOCK\000300.SH.xlsx"
    dp = DataProvider()
    df = dp.get_ohlc_data(file_path)
    if df is None or df.empty:
        raise ValueError("数据加载失败")
    
    benchmark_series = df['close']
    
    # 2. 调用逻辑修正后的择时信号 (来自 report_timing.py)
    print("\n--- 生成择时信号 ---")
    
    signals = {}
    # RSRS
    signals["HT_RSRS"] = ht_rsrs_timing(df)
    # 价格乖离
    signals["HT_PriceBias"] = ht_price_bias_timing(df)
    # 布林带 (修正后：突破2倍标准差买入/卖出，维持观点)
    signals["HT_BollBreak"] = ht_bollinger_timing(df)
    # 新高占比 (修正后：升高买入，下降卖出)
    signals["HT_NewHighRatio"] = ht_new_high_timing(df)
    
    # 综合信号 (简单打分，仅供参考)
    total_score = signals["HT_RSRS"] + signals["HT_PriceBias"] + \
                  (signals["HT_BollBreak"] == 1).astype(int) + \
                  (signals["HT_NewHighRatio"] == 1).astype(int)
    signals["Integrated_HT"] = (total_score >= 3).astype(int)

    # 3. 批量执行
    for name, sig in signals.items():
        run_factor_backtest(name, sig, benchmark_series)
         
    print("\n" + "="*60)
    print("择时回测全部完成。")
    print("="*60)

if __name__ == '__main__':
    main()
