import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from core.Logger import logger
from gx_pit_mom import GXPITMomTester

class PitMomTester(GXPITMomTester):
    """
    时点动量拓展测试框架 (基于物理择时指标 + 两阶段确认)
    强调：仅在扩展信号触发点采用当日动量分配，
    若 signal_type 为 'breakout', 'rebound', 'rotation'，则完全还原 GXPITMomTester 逻辑。
    """
    def __init__(self, start_date="2013-01-01", end_date="2026-03-31", 
                 sector_type="yjhy", base_data_path="D:/DATA"):
        super().__init__(start_date, end_date, sector_type, base_data_path)
        # 更新输出路径，区分于原始 gx_pit_mom
        self.output_base = "results/pit_mom"
        os.makedirs(self.output_base, exist_ok=True)

    def _calc_physical_metrics(self):
        """
        [内建逻辑] 计算物理择时指标库 (同步 run_momentum_sensitivity_test.py)
        返回包含各指标的 DataFrame
        """
        df = self.index_data.copy()
        metrics = pd.DataFrame(index=df.index)
        T = 20 # 默认周期
        
        # --- 价格类因子 ---
        # 1. 价格分位数 (250日)
        window_250 = 250
        min_250 = df['low'].rolling(window_250).min()
        max_250 = df['high'].rolling(window_250).max()
        metrics['price_abs_pos'] = (df['close'] - min_250) / (max_250 - min_250)
        
        # 2. 价格距离 60日高点
        window_p = 60
        hhv = df['high'].rolling(window_p).max()
        metrics['price_dist_high'] = df['close'] / hhv - 1

        # 3. 价格相对于 20日均线
        metrics['price_rel_ma'] = (df['close'] / df['close'].rolling(T).mean() - 1) * 100
        
        # --- 成交量类因子 ---
        # 4. 量能干涸度 (Volume Dryness): Volume / MA20
        v_ma = df['volume'].rolling(T).mean()
        metrics['volume_abs_dryness'] = df['volume'] / v_ma
        
        # 5. 成交量标准分 (Z-Score)
        metrics['volume_std_score'] = (df['volume'] - v_ma) / df['volume'].rolling(T).std()
        
        # --- 趋势与波动类因子 ---
        # 6. DMI 趋势强度
        up_move = df['high'].diff()
        down_move = -df['low'].diff()
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        p_dm_sum = pd.Series(plus_dm, index=df.index).rolling(T).sum()
        m_dm_sum = pd.Series(minus_dm, index=df.index).rolling(T).sum()
        tr = pd.concat([df['high'] - df['low'], 
                        (df['high'] - df['close'].shift(1)).abs(), 
                        (df['low'] - df['close'].shift(1)).abs()], axis=1).max(axis=1)
        tr_sum = tr.rolling(T).sum()
        metrics['plus_di'] = 100 * (p_dm_sum / tr_sum)
        metrics['minus_di'] = 100 * (m_dm_sum / tr_sum)
        metrics['trend_strength'] = metrics['plus_di'] - metrics['minus_di']

        # 7. 20日新高行业数量 (模拟)
        # 注意：此处用指数自身的 20日最高价作为简化实现，或反映指数强势感
        metrics['new_high_count'] = (df['close'] >= df['close'].rolling(20).max()).astype(int).rolling(20).sum()
        
        # 8. 波动压缩 (Vola Compression)
        metrics['volatility_compression'] = df['close'].pct_change().rolling(T).std() / \
                                          df['close'].pct_change().rolling(100).std()
        
        return metrics

    def calculate_two_stage_signals(self, setup_type="price_near_high", confirm_thresh=0.03):
        """
        [择时引擎]
        """
        # 兼容性检查：如果是原有的 gx_pit 信号
        if setup_type in ["breakout", "rebound", "rotation"]:
            return super().calculate_timing(setup_type)

        metrics = self._calc_physical_metrics()
        daily_ret = self.index_data['close'].pct_change()
        
        # 映射 run_momentum_sensitivity_test.py 中的物理阈值
        if setup_type == "price_near_high":
            setup_mask = metrics['price_dist_high'] > -0.005
        elif setup_type == "price_low_abs":
            setup_mask = metrics['price_abs_pos'] < 0.05
        elif setup_type == "price_rel_ma":
            setup_mask = metrics['price_rel_ma'] < -2.0
        elif setup_type == "volume_extreme_dry":
            setup_mask = metrics['volume_abs_dryness'] < 0.75
        elif setup_type == "volume_std_score":
            setup_mask = metrics['volume_std_score'] < -1.5
        elif setup_type == "trend_bull_strength":
            setup_mask = metrics['trend_strength'] > 15
        elif setup_type == "trend_persistent_high":
            setup_mask = metrics['new_high_count'] > 10
        elif setup_type == "vola_extreme_comp":
            setup_mask = metrics['volatility_compression'] < 0.75
        else:
            raise ValueError(f"Unknown setup type: {setup_type}")
            
        # 2. 应用动量确认 (当日涨幅 > 阈值)
        final_signal = setup_mask & (daily_ret > confirm_thresh)
        
        return final_signal.astype(int)

    def generate_signal_day_weights(self, setup_type, timing_series):
        """
        [行业权重分配逻辑] 
        - 原始型号 (breakout/rebound/rotation): 还原父类逻辑
        - 新物理型号: 采用信号触发当日的 1D 收益率作为动量因子
        """
        if setup_type in ["breakout", "rebound", "rotation"]:
            return super().calculate_sparse_factor(setup_type, timing_series)

        sector_rets = self.sector_prices.pct_change()
        trigger_dates = timing_series[timing_series == 1].index
        sparse_mom = pd.DataFrame(index=timing_series.index, columns=self.sector_prices.columns)
        
        valid_dates = trigger_dates.intersection(sector_rets.index)
        if not valid_dates.empty:
            sparse_mom.loc[valid_dates] = sector_rets.loc[valid_dates]
            
        return sparse_mom

    def plot_annual_trigger_count(self, timing_series, setup_type, output_dir):
        """
        [新增统计项] 统计并保存每年的信号触发次数
        """
        trigger_dates = timing_series[timing_series == 1].index
        if len(trigger_dates) == 0:
            return
            
        annual_counts = pd.Series(1, index=trigger_dates).resample('YE').sum()
        annual_counts.index = annual_counts.index.year
        
        logger.info(f"\n信号年度分布 ({setup_type}):\n{annual_counts}")
        
        save_path = os.path.join(output_dir, "annual_trigger_distribution.csv")
        annual_counts.to_frame(name='trigger_count').to_csv(save_path)
        return annual_counts

    def run_strategy(self, setup_type="price_near_high", confirm_thresh=0.03):
        """
        执行完整的回测流: 统一还原 gx_pit_mom 的检验和输出逻辑
        """
        logger.info(f"--- 开启 PitMom 策略测试/还原: {setup_type} ---")
        
        # 1. 信号生成
        timing_series = self.calculate_two_stage_signals(setup_type, confirm_thresh)
        logger.info(f"信号触发总次数: {timing_series.sum()}")
        
        # 2. 动量分配
        sparse_signal_df = self.generate_signal_day_weights(setup_type, timing_series)
        
        # 3. 输出路径调整：一级目录为动量阈值，二级目录为信号类型
        mom_folder = f"m{int(confirm_thresh*1000):03d}" # e.g., m005, m015, m030
        if setup_type in ["breakout", "rebound", "rotation"]:
            output_dir = os.path.join(self.output_base, mom_folder, f"gx_pit_{setup_type}")
        else:
            output_dir = os.path.join(self.output_base, mom_folder, setup_type)
        os.makedirs(output_dir, exist_ok=True)
        
        # 4. 年度触发频率统计 (针对 2.2 的补充)
        self.plot_annual_trigger_count(timing_series, setup_type, output_dir)
        
        # 5. 调用 SparseSignalTester 进行统一评价
        tester = SparseSignalTester(
            signal_series=sparse_signal_df,
            price_df=self.sector_prices,
            benchmark_series=self.index_data["close"],
            period=20,  
            n_groups=5 if self.sector_type == "yjhy" else 10,
            output_dir=output_dir
        )
        
        results = tester.run_backtest()
        
        # 6. 完全还原 gx_pit_mom 的绘图与报告输出
        logger.info(f"正在生成 {setup_type} 的标准回测报告...")
        try:
            # 还原 plot_group_returns (内部包含多条曲线和柱状图)
            tester.plot_group_returns(results, title=f"{setup_type} Group Returns")
        except Exception as e:
            logger.warning(f"绘图过程部分跳过: {e}")
            
        tester.print_performance_report()
        logger.info(f"回测报告已完整存至: {output_dir}")

def main():
    # 动量阈值循环测试: 0.5% 到 3.0%, 步长 0.5%
    momentum_thresholds = [0.005, 0.010, 0.015, 0.020, 0.025, 0.030]
    physical_setups = [
        "price_low_abs", "price_near_high", "price_rel_ma", 
        "volume_extreme_dry", "volume_std_score", 
        "trend_bull_strength", "trend_persistent_high", 
        "vola_extreme_comp"
    ]
    
    sector = "yjhy"
    tester = PitMomTester(sector_type=sector)
    
    for m_thresh in momentum_thresholds:
        logger.info(f"\n{'='*20} 正在测试动量确认阈值: {m_thresh:.1%} {'='*20}")
        for setup in physical_setups:
            tester.run_strategy(setup_type=setup, confirm_thresh=m_thresh)

if __name__ == "__main__":
    main()
