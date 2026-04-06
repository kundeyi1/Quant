import pandas as pd
import os
from core.DataManager import DataProvider
from factors.technical_factors import PriceFactors, VolumeFactors, TrendFactors, VolatilityFactors
from core.TimingTester import TimingTester
from core.NavAnalyzer import Visualizer
from core.FactorVisualizer import FactorVisualizer
from core.Logger import logger

def test_new_timing_factors(start_date="2013-01-01", end_date="2025-03-31", T=20):
    """
    1. 检验重构后的原子因子 (价格、量能、趋势、波动)
    2. 采用绝对物理阈值 (Fixed Threshold) 定义其择时信号
    3. 集成 FactorVisualizer 进行对齐可视化
    """
    logger.info(f"开始原子因子/物理阈值检验, T={T}...")
    
    dp = DataProvider(base_data_path="D:/DATA")
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    df = dp.get_ohlc_data(index_file, name="000985")
    df = df.loc[:end_date] 
    
    # --- 因子计算 (全部基于物理度量) ---
    # 1. 价格维度
    f_abs_pos = PriceFactors.price_abs_pos(df, window=250)['price_abs_pos']
    f_dist_high = PriceFactors.price_dist_high(df, window=60)['price_dist_high']
    f_price_rel_ma = PriceFactors.price_rel_ma(df, window=T)['price_rel_ma']
    
    # 2. 量能维度
    f_vol_dry = VolumeFactors.volume_abs_dryness(df, window=T)['volume_abs_dryness']
    f_vol_std = VolumeFactors.volume_std_bias(df, window=T)['volume_std_score']
    
    # 3. 趋势维度
    f_adx = TrendFactors.adx(df, period=20)['adx']
    f_plus_di = TrendFactors.plus_di(df, period=20)['plus_di']
    f_minus_di = TrendFactors.minus_di(df, period=20)['minus_di']
    f_nh_count = TrendFactors.new_high_count(df, window=20)['new_high_count']
    
    # 4. 波动维度
    f_vola_comp = VolatilityFactors.volatility_compression(df, window=T)['volatility_compression']
    
    # --- 打印所有因子分位数并保存 ---
    all_metrics = pd.DataFrame({
        "abs_pos": f_abs_pos,
        "dist_high": f_dist_high,
        "rel_ma": f_price_rel_ma,
        "vol_dry": f_vol_dry,
        "vol_std": f_vol_std,
        "di_diff": f_plus_di - f_minus_di,
        "nh_count": f_nh_count,
        "vola_comp": f_vola_comp
    }).loc[start_date:end_date]
    
    quantiles = all_metrics.quantile([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    logger.info("\n=== 因子物理值分布 (分位数) ===\n" + quantiles.to_string())
    
    stats_output = "results/timing_factor_test"
    os.makedirs(stats_output, exist_ok=True)
    quantiles.to_csv(os.path.join(stats_output, "factor_quantiles.csv"))
    logger.info(f"分位数统计已保存至: {os.path.join(stats_output, 'factor_quantiles.csv')}")
                         
    # --- 指标字典与对应的绝对阈值定义 ---
    # 格式: { name: (series, threshold, operator) }
    # operator: 'gt' (大于), 'lt' (小于)
    configs = {
        "price_low_abs": (f_abs_pos, 0.05, 'lt'),              # 处于过去一年15%分位以下的相对低位点
        "price_near_high": (f_dist_high, -0.005, 'gt'),        # 处于近期高点5%以内的强势调整/突破前夕
        "price_rel_ma": (f_price_rel_ma, -2.0, 'lt'),         # 价格向下偏离均线超过1.5倍标准差 (超跌)
        "volume_extreme_dry": (f_vol_dry, 0.75, 'lt'),         # 成交量萎缩至40日平均值的80%以下 (地量)
        "volume_std_score": (f_vol_std, -1.5, 'lt'),          # 成交量低于均值1倍标准差以上 (缩量)
        "trend_bull_strength": (f_plus_di - f_minus_di, 15, 'gt'), # 多头能量比空头能量高出10个点以上
        "trend_persistent_high": (f_nh_count, 10, 'gt'),      # 过去20天内有7天以上在创新高 (趋势强劲)
        "vola_extreme_comp": (f_vola_comp, 0.75, 'lt')         # 波动率收缩至中期的60%以下 (寂静变盘)
    }

    base_output = "results/timing_factor_test"
    os.makedirs(base_output, exist_ok=True)
    
    master_df = pd.DataFrame({
        'open': df['open'], 'high': df['high'], 'low': df['low'], 
        'close': df['close'], 'volume': df['volume'],
        'ret': df['close'].pct_change()
    }).loc[start_date:end_date]
    
    benchmark_rets = master_df['ret']

    for name, (val_ser, thresh, op) in configs.items():
        logger.info(f"正在生成基础报告: {name} (Threshold: {thresh})")
        path = os.path.join(base_output, name)
        os.makedirs(path, exist_ok=True)
        
        # 信号逻辑
        score_ser = val_ser.loc[start_date:end_date]
        signal = (score_ser > thresh).astype(int) if op == 'gt' else (score_ser < thresh).astype(int)
        
        # 1. 择时绩效分布
        tester = TimingTester(signal_series=signal, benchmark_series=master_df['close'], output_dir=path)
        tester.run_timing_analysis(period=T)
        tester.plot_signals(asset_name="000985")
        
        # 2. 择时净值曲线
        daily_signal = signal.shift(1).fillna(0)
        strategy_rets = benchmark_rets * daily_signal
        bench_nav = (1 + benchmark_rets).cumprod()
        strat_nav = (1 + strategy_rets).cumprod()
        
        Visualizer.plot_performance_nav(
            nav_ser=strat_nav, 
            benchmark_nav=bench_nav, 
            title=f"Timing Strategy Fixed - {name}",
            output_path=os.path.join(path, f"nav_curve.png")
        )

    # 其次运行会干扰全局 Matplotlib 状态的 FactorVisualizer (mplfinance)
    logger.info("开始生成因子对齐可视化 (FactorVisualizer)...")
    for name, (val_ser, thresh, op) in configs.items():
        logger.info(f"绘制对齐图: {name}")
        path = os.path.join(base_output, name)
        score_ser = val_ser.loc[start_date:end_date]
        
        visualizer = FactorVisualizer(master_df[['open', 'high', 'low', 'close', 'volume']], score_ser, factor_name=name)
        visualizer.plot(title=f"{name} (Thresh:{thresh}) Alignment", 
                        save_path=os.path.join(path, "factor_alignment.png"), 
                        lookback=500)
        
    logger.info(f"所有物理阈值报告已输出至: {base_output}")


    logger.info(f"所有报告已更新至 (Rolling Threshold): {base_output}")

if __name__ == "__main__":
    test_new_timing_factors(T=20)
