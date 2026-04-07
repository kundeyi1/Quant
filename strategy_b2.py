import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Import framework components
from core.DataManager import DataProvider
from core.FactorTester import FactorTester
from core.NavAnalyzer import NavAnalyzer, Visualizer
from factors.technical_factors import PriceFactors, VolumeFactors, TrendFactors, VolatilityFactors

class B2AlphaResearcher:
    """
    Experimental Researcher for b2_alpha (Structural Ignition Alpha).
    Focus: Energy compression -> Momentum breakout -> Pullback -> Re-ignition.
    """
    def __init__(self, start_date='2017-01-01', end_date=None, universe='all'):
        self.dm = DataProvider()
        self.start_date = start_date
        self.end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        self.universe = universe
        self.data = None
        self.factors = pd.DataFrame()
        self.labels = pd.DataFrame()
        
    def load_data(self):
        """Load OHLCV data for all stocks in the universe."""
        print(f"Loading data from {self.start_date} to {self.end_date}...")
        self.data = self.dm.get_universe_data(
            filename="STOCK/all_stock_data_ts_20140102_20251231.csv",
            universe=None, 
            start_date=self.start_date, 
            end_date=self.end_date
        )
        if self.data is not None:
            print(f"Data loaded: {len(self.data)} records.")
        else:
            print("ERROR: Failed to load data.")

    def build_factors(self):
        """Construct the 12 b2_alpha factors with staggered timing (Lagged Features)."""
        print("Calculating b2_alpha factors (Lagged 1d for structural context)...")
        df = self.data.copy()
        
        # 核心逻辑：波动率收敛 (Compression) 和 趋势结构 (Structure) 衡量的是“蓄势”过程
        # 本地逻辑：所有结构性/波动率类因子均取前一天 (Shift 1) 的结果，避免与今日动量冲突
        
        # 1. Trend & Structure (Lagged 1d)
        f_strength = TrendFactors.trend_strength(df).iloc[:, 0].shift(1).rename('trend_strength')
        f_slope = TrendFactors.trend_slope(df).iloc[:, 0].shift(1).rename('trend_slope')
        f_ma_structure = TrendFactors.ma_structure(df).iloc[:, 0].shift(1).rename('ma_structure')
        f_supply = TrendFactors.supply_pressure(df).iloc[:, 0].shift(1).rename('supply_pressure')
        
        # 2. Volatility & Compression (Lagged 1d)
        f_vol_ratio = VolatilityFactors.volatility_ratio(df).iloc[:, 0].shift(1).rename('volatility_ratio')
        f_amp_ratio = VolatilityFactors.amplitude_ratio(df).iloc[:, 0].shift(1).rename('amplitude_ratio')
        
        # 3. Volume Characteristics (Lagged 1d)
        f_vol_dryness = VolumeFactors.volume_abs_dryness(df).iloc[:, 0].shift(1).rename('volume_abs_dryness')
        f_vol_zscore = VolumeFactors.volume_zscore(df).iloc[:, 0].shift(1).rename('volume_zscore')
        
        # 4. Position & Momentum (混合：位置取前一天，动量取今日)
        f_pullback = PriceFactors.pullback_depth(df).iloc[:, 0].shift(1).rename('pullback_depth')
        f_pos = PriceFactors.position(df).iloc[:, 0].shift(1).rename('position')
        
        # 动量加速度和 K 线强度保留今日 (衡量突破瞬间)
        f_accel = PriceFactors.momentum_acceleration(df).iloc[:, 0].rename('momentum_acceleration')
        f_body = PriceFactors.body_strength(df).iloc[:, 0].rename('body_strength')
        
        factor_list = [
            f_strength, f_slope, f_ma_structure, f_supply,
            f_vol_ratio, f_amp_ratio,
            f_vol_dryness, f_vol_zscore,
            f_pullback, f_pos, f_accel, f_body
        ]
        
        self.factors = pd.concat(factor_list, axis=1)
        self.factors = self.factors.dropna(how='all')
        print(f"Factors built: {self.factors.columns.tolist()}")

    def build_labels(self, target_horizon=1):
        """Construct future returns as labels."""
        print(f"Building {target_horizon}d labels...")
        close = self.data['close']
        ret_future = close.groupby(level=1).shift(-target_horizon) / close - 1
        self.labels = pd.DataFrame({f'ret_{target_horizon}d': ret_future}, index=self.data.index)

    def synthesize_alpha(self):
        """
        Combine multiple factors into a single b2_alpha signal.
        Automatically adjusts for factor direction using the logic now in FactorTester.
        """
        print("Synthesizing multi-factor alpha with direction adjustment...")
        
        if self.factors.empty or self.labels.empty:
            print("ERROR: Factors or Labels are empty.")
            return

        # 1. 判定说明：使用 FactorTester 中新增的 analyze_factor_direction 函数
        ret_next = self.labels.iloc[:, 0]
        directions = FactorTester.analyze_factor_direction(self.factors, ret_next)
        
        # 2. 对每个因子进行截面标准化并按判定方向重构
        z_factors = self.factors.groupby(level=0).transform(lambda x: (x - x.mean()) / (x.std() + 1e-9))
        
        adjusted_factors_list = []
        for col in z_factors.columns:
            direction = directions.get(col, 1)
            print(f"  Factor {col:<20} | Direction: {direction:>2}")
            adjusted_factors_list.append(z_factors[col] * direction)
        
        # 3. 等权合成
        self.factors['b2_alpha_combined'] = pd.concat(adjusted_factors_list, axis=1).mean(axis=1)
        print("Synthesis complete (All factors aligned to positive alpha).")

    def run_comprehensive_backtest(self, output_dir='results/strategy_b2'):
        """
        使用 NavAnalyzer 提供深度绩效分析及多空、多头对比。
        """
        print("\n" + "="*80)
        print("Executing COMPREHENSIVE BACKTEST...")
        
        os.makedirs(output_dir, exist_ok=True)
        tester = FactorTester(start_date=self.start_date, end_date=self.end_date, output_dir=output_dir)
        
        alpha_data = self.factors[['b2_alpha_combined']].reset_index()
        alpha_data.columns = ['FDate', 'SecCode', 'FValue']
        tester.load_price_data("D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv")
        
        groups = 10
        metrics, nav_df = tester.backtest(
            factor_name='B2_Alpha_Synthetic', 
            factor_data=alpha_data, 
            interval_tag='D', 
            groups=groups,
            if_plot=True
        )
        
        # 保存每期 Top 100 选股结果
        print("Saving periodic Top 100 stock selections...")
        os.makedirs(os.path.join(output_dir, "top_stocks"), exist_ok=True)
        # 按日期分组，每组取 FValue 最大的 100 只
        top100_df = alpha_data.sort_values(['FDate', 'FValue'], ascending=[True, False]) \
                             .groupby('FDate') \
                             .head(100)
        top100_df.to_csv(os.path.join(output_dir, "b2_top100_daily.csv"), index=False)
        
        if nav_df is None or nav_df.empty:
            print("ERROR: Backtest failed to generate NAV data.")
            return

        # 4. 获取日度收益率用于 NavAnalyzer 深度分析
        group_returns = nav_df.pct_change().dropna()
        long_ret = group_returns[f'group{groups}']
        short_ret = group_returns['group1']
        ls_ret = long_ret - short_ret
        
        # 5. 使用 NavAnalyzer 分析
        print("\nRunning PERF-ANALYSIS via NavAnalyzer...")
        long_analyzer = NavAnalyzer(long_ret, name="B2_Long_Group")
        ls_analyzer = NavAnalyzer(ls_ret, name="B2_LongShort_Spread")
        
        long_perf = long_analyzer.compute_performance()
        ls_perf = ls_analyzer.compute_performance()
        long_yearly = long_analyzer.get_yearly_stats()
        
        perf_summary = pd.DataFrame({
            "Long_Only (Group 10)": long_perf,
            "Long_Short_Spread": ls_perf
        }).T
        perf_summary.to_csv(os.path.join(output_dir, "b2_alpha_detailed_performance.csv"))
        long_yearly.to_csv(os.path.join(output_dir, "b2_long_yearly_stats.csv"))
               
        # 绘制多头净值图
        Visualizer.plot_performance_nav(
            nav_ser=long_analyzer.nav,
            title='B2 Alpha Research: Long Only (Group 10) Performance',
            stats=(long_perf['annual_return'], long_perf['volatility'], long_perf['sharpe_ratio'], long_perf['max_drawdown']),
            output_path=os.path.join(output_dir, "b2_long_only_performance.png")
        )
        
        # 绘制多空净值图
        Visualizer.plot_performance_nav(
            nav_ser=ls_analyzer.nav,
            title='B2 Alpha Research: Long-Short Spread Performance',
            stats=(ls_perf['annual_return'], ls_perf['volatility'], ls_perf['sharpe_ratio'], ls_perf['max_drawdown']),
            output_path=os.path.join(output_dir, "b2_long_short_performance.png")
        )
        
        print(f"\n[DONE] Reports generated in: {output_dir}")
        print("\nDetailed Performance Table:")
        print(perf_summary)

if __name__ == "__main__":
    analysis_start = '2017-01-01'
    analysis_end = '2025-12-31'
    
    researcher = B2AlphaResearcher(start_date=analysis_start, end_date=analysis_end)
    researcher.load_data() 
    researcher.build_factors()
    researcher.build_labels(target_horizon=1)
    researcher.synthesize_alpha()
    
    if not researcher.factors.empty:
        researcher.run_comprehensive_backtest(output_dir='results/strategy_b2')
    else:
        print("ERROR: Calculated factors are empty.")
