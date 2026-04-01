import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from timing import market_timing
from core.DataManager import DataProvider
from core.Logger import logger

def test_ht_timing_visual():
    """
    可视化测试华泰技术择时指标
    """
    dp = DataProvider(base_data_path="D:/DATA")
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    
    logger.info(f"加载测试数据: {index_file}")
    df = dp.get_ohlc_data(index_file)
    
    if df is None:
        logger.error("无法加载数据")
        return

    # 计算指标
    logger.info("计算华泰择时信号...")
    df['rsrs_sig'] = market_timing.ht_rsrs_timing(df)
    df['trend_sig'] = market_timing.ht_trend_strength_timing(df)
    df['integrated_sig'] = market_timing.ht_integrated_timing(df)
    
    # 绘图可视化
    fig, axes = plt.subplots(4, 1, figsize=(15, 20), sharex=True)
    
    # 1. 价格曲线
    axes[0].plot(df['close'], label='Close Price', color='black')
    axes[0].set_title('Market Price (000985.CSI)')
    axes[0].legend()
    
    # 2. RSRS Signal
    axes[1].fill_between(df.index, 0, df['rsrs_sig'], color='red', alpha=0.3, label='RSRS Buy Signal')
    axes[1].set_title('HT RSRS Timing Signal (Binary)')
    axes[1].legend()
    
    # 3. Trend Signal
    axes[2].fill_between(df.index, 0, df['trend_sig'], color='orange', alpha=0.3, label='ADX Trend Signal')
    axes[2].set_title('HT ADX Trend Timing Signal')
    axes[2].legend()
    
    # 4. Integrated Signal
    axes[3].fill_between(df.index, 0, df['integrated_sig'], color='purple', alpha=0.3, label='Integrated Buy Signal')
    axes[3].set_title('HT Integrated Technical Timing (Multi-Factor Voting)')
    axes[3].legend()
    
    plt.tight_layout()
    output_fig = "results/factor_analysis/ht_technical_timing_test.png"
    plt.savefig(output_fig)
    logger.info(f"可视化结果已保存至: {output_fig}")

if __name__ == "__main__":
    test_ht_timing_visual()
