import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
from core.DataManager import DataProvider
from factors.technical_factors import PriceFactors, VolumeFactors, TrendFactors, VolatilityFactors
from timing import pattern_timing
from core.Logger import logger

# 设置中文字体
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False

def generate_sensitivity_heatmap(csv_path):
    """
    基于CSV结果生成热力图
    """
    df = pd.read_csv(csv_path)
    # 提取平均收益率列 (AvgRet)
    ret_cols = [c for c in df.columns if 'AvgRet' in c]
    heatmap_df = df.set_index('Momentum_Threshold')[ret_cols]
    # 简化列名
    heatmap_df.columns = [c.replace('_AvgRet', '') for c in heatmap_df.columns]
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(heatmap_df, annot=True, fmt=".2%", cmap='OrRd', center=0)
    plt.title('择时因子 vs 动量阈值 敏感性测试 (T+20 平均收益率)')
    plt.xlabel('择时信号类型')
    plt.ylabel('动量确认阈值')
    
    output_img = csv_path.replace('.csv', '_heatmap.png')
    plt.savefig(output_img)
    logger.info(f"热力图已生成: {output_img}")

def run_momentum_filter_test(start_date="2014-01-01", end_date="2026-03-31", T=20):
    """
    对各个择时因子/形态进行动量过滤敏感度测试:
    1. 识别基础择时信号 (Candidate Points)
    2. 遍历动量阈值 (0.2% 到 5.0%, 步长 0.2%)
    3. 识别出在信号触发后 (T+1) 产生的反弹动量点
    4. 计算后 20 天的平均收益，生成参数敏感度表格
    """
    logger.info("开始动量过滤敏感度测试...")
    
    # --- 1. 数据准备 ---
    dp = DataProvider(base_data_path="D:/DATA")
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    df = dp.get_ohlc_data(index_file, name="000985")
    df = df.loc[:end_date]
    
    # --- 因子计算 (同步 test_new_timing_factors.py 的最新物理量逻辑) ---
    f_abs_pos = PriceFactors.price_abs_pos(df, window=250)['price_abs_pos']
    f_dist_high = PriceFactors.price_dist_high(df, window=60)['price_dist_high']
    f_price_rel_ma = PriceFactors.price_rel_ma(df, window=T)['price_rel_ma']
    
    f_vol_dry = VolumeFactors.volume_abs_dryness(df, window=T)['volume_abs_dryness']
    f_vol_std = VolumeFactors.volume_std_bias(df, window=T)['volume_std_score']
    
    f_plus_di = TrendFactors.plus_di(df, period=20)['plus_di']
    f_minus_di = TrendFactors.minus_di(df, period=20)['minus_di']
    f_nh_count = TrendFactors.new_high_count(df, window=20)['new_high_count']
    
    f_vola_comp = VolatilityFactors.volatility_compression(df, window=T)['volatility_compression']
    
    # 构造基础信号字典 (使用 test_new_timing_factors.py 中验证过的物理阈值作为 Baseline)
    base_signals = {
        "price_low_abs": (f_abs_pos < 0.05).astype(int),
        "price_near_high": (f_dist_high > -0.005).astype(int),
        "price_rel_ma": (f_price_rel_ma < -2.0).astype(int),
        "volume_extreme_dry": (f_vol_dry < 0.75).astype(int),
        "volume_std_score": (f_vol_std < -1.5).astype(int),
        "trend_bull_strength": ((f_plus_di - f_minus_di) > 15).astype(int),
        "trend_persistent_high": (f_nh_count > 10).astype(int),
        "vola_extreme_comp": (f_vola_comp < 0.75).astype(int)
    }

    # 持有期收益 (Forward 20D)
    forward_return = df['close'].shift(-T) / df['close'] - 1
    # 当日动量 (用于过滤)
    daily_ret = df['close'].pct_change()
    
    # --- 2. 循环搜索动量阈值 ---
    thresholds = np.arange(0.002, 0.051, 0.002) # 0.2% to 5% with 0.2% pace
    results_master = []

    for m_threshold in thresholds:
        logger.info(f"正在测试动量阈值: {m_threshold:.1%}")
        row_stats = {"Momentum_Threshold": f"{m_threshold:.1%}"}
        
        for name, sig_ser in base_signals.items():
            # 严格逻辑：择时信号触发后的 1-3 天内出现指定涨幅 (这里简化为信号发出当天或次日有反弹)
            # 用户要求：择时触发后出现反弹。我们定义为：择时符合 + 当日涨幅 > 阈值
            final_sig = (sig_ser == 1) & (daily_ret > m_threshold)
            
            # 计算对应的 T+20 收益
            sample_rets = forward_return[final_sig].dropna()
            
            if len(sample_rets) > 0:
                avg_perf = sample_rets.mean()
                count = len(sample_rets)
            else:
                avg_perf = np.nan
                count = 0
            
            row_stats[f"{name}_AvgRet"] = avg_perf
            row_stats[f"{name}_Count"] = count
            
        results_master.append(row_stats)

    # --- 3. 输出报表 ---
    perf_df = pd.DataFrame(results_master)
    output_dir = "results/momentum_filter_sensitivity"
    os.makedirs(output_dir, exist_ok=True)
    
    # 物理阈值版本已不再使用 quantile_threshold 变量，统一命名为 physical_threshold
    output_file = os.path.join(output_dir, "momentum_threshold_performance_physical.csv")
    perf_df.to_csv(output_file, index=False)
    
    # 打印简要结论
    logger.info(f"测试完成！敏感度表格已保存至: {output_file}")
    
    # --- 4. 生成热力图 ---
    generate_sensitivity_heatmap(output_file)
    
    # 选出每个因子表现最好的动量参数
    for name in base_signals.keys():
        col = f"{name}_AvgRet"
        if col in perf_df.columns:
            best_row = perf_df.loc[perf_df[col].idxmax()]
            logger.info(f"因子 [{name}] 最佳反弹阈值: {best_row['Momentum_Threshold']}, 对应T+20平均收益: {best_row[col]:.2%}")

if __name__ == "__main__":
    run_momentum_filter_test()
