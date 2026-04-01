import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from timing import report_timing
from core.Logger import logger

class GXPITMomTester:
    """
    国信时点动量策略测试框架
    """
    def __init__(self, start_date="2013-01-01", end_date="2026-03-26", 
                 sector_type='yjhy', base_data_path="D:/DATA"):
        self.dp = DataProvider(base_data_path=base_data_path)
        self.start_date = start_date
        self.end_date = end_date
        self.sector_type = sector_type
        self.base_data_path = base_data_path
        self.timing_path = os.path.join(base_data_path, "TIMING")
        self.sparse_path = os.path.join(base_data_path, "SPARSE_SIGNAL")
        
        self.pre_start_date = (pd.to_datetime(start_date) - pd.DateOffset(years=1)).strftime("%Y-%m-%d")
        self._load_base_data()

    def _load_base_data(self):
        index_file = "INDEX/STOCK/000985.CSI.xlsx" # 中证全指
        self.index_data = self.dp.get_ohlc_data(index_file, name="target_index").loc[self.pre_start_date:self.end_date]
        
        if self.sector_type == 'all':
            sector_path = "STOCK/all_stock_data_ts_20140102_20251231.csv"
            raw_data = pd.read_csv(Path(self.base_data_path) / sector_path, parse_dates=['date'])
            # 长表转宽表，并确保代码列为字符串格式，避免 parquet 导出由于整数列名报错
            raw_data['code'] = raw_data['code'].astype(str).str.zfill(6)
            self.sector_prices = raw_data.pivot(index='date', columns='code', values='close').loc[self.pre_start_date:self.end_date]
        else:
            if self.sector_type == 'ejhy':
                sector_path = r"D:\DATA\INDEX\ZX\ejhy_prices.csv"
            elif self.sector_type == 'yjhy':
                sector_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
            else:
                sector_path = f"INDEX/ZX/ZX_{self.sector_type.upper()}.xlsx"

            self.sector_prices = self.dp.get_wide_table(sector_path).loc[self.pre_start_date:self.end_date]
        
        # 针对轮动信号的一级行业数据 (Rotation 无论一二级行业都用一级测试行业多样性)
        yjhy_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
        self.yjhy_prices = self.dp.get_wide_table(yjhy_path).loc[self.pre_start_date:self.end_date]

    def save_timing_signal(self, signal, full_name):
        """
        保存择时信号到 D:/DATA/TIMING
        """
        os.makedirs(self.timing_path, exist_ok=True)
        filepath = os.path.join(self.timing_path, f"{full_name}.parquet")
        signal.to_frame().to_parquet(filepath)
        return filepath

    def load_timing_signal(self, full_name):
        """
        从 D:/DATA/TIMING 加载择时信号
        """
        filepath = os.path.join(self.timing_path, f"{full_name}.parquet")
        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            return df.iloc[:, 0]
        return None

    def check_timing_exists(self, full_name):
        """
        检查择时信号是否已存在
        """
        filepath = os.path.join(self.timing_path, f"{full_name}.parquet")
        return os.path.exists(filepath)

    def calculate_timing(self, signal_type):
        """
        计算择时信号
        """
        start_str = pd.to_datetime(self.start_date).strftime("%Y%m%d")
        end_str = pd.to_datetime(self.end_date).strftime("%Y%m%d")
        full_name = f"gx_pit_{signal_type}_{self.sector_type}_{start_str}_{end_str}"
        
        if self.check_timing_exists(full_name):
            return self.load_timing_signal(full_name)
        
        logger.info(f"计算择时信号: {full_name}...")
        if signal_type == "breakout":
            signal = report_timing.gx_pit_breakout(self.index_data, threshold_pre=0.01, threshold_break=0.01, window=5)
        elif signal_type == "rebound":
            signal = report_timing.gx_pit_rebound(self.index_data, u=0.005, d=0.05)
        elif signal_type == "rotation":
            signal = report_timing.gx_pit_rotation(self.index_data, self.yjhy_prices, n_decrease=3, window_atr=60)
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")
            
        self.save_timing_signal(signal, full_name)
        return signal

    def calculate_sparse_factor(self, signal_type, timing_series):
        """
        基于择时信号计算触发当日的行业因子值。
        """
        factor_name = f"gx_pit_mom_{signal_type}_{self.sector_type}"
        sparse_file = os.path.join(self.sparse_path, f"{factor_name}_{self.start_date.replace('-','')}_{self.end_date.replace('-','')}.parquet")
        
        if os.path.exists(sparse_file):
            cached_df = pd.read_parquet(sparse_file)
            # 校验列名一致性，防止数据源变更导致缓存失效
            if list(cached_df.columns) == list(self.sector_prices.columns):
                return cached_df
            logger.info(f"缓存列名不匹配，重新计算稀疏因子: {factor_name}")

        logger.info(f"计算稀疏因子: {factor_name}...")
        rets = self.sector_prices.pct_change()
        
        if signal_type == "breakout":
            # 突破当日涨幅
            sparse_val = rets
        elif signal_type == "rebound":
            # 反弹当日涨跌幅 - 前20日日均
            avg_prev_rets = rets.shift(1).rolling(20).mean()
            sparse_val = rets - avg_prev_rets
        elif signal_type == "rotation":
            # 切换当日涨幅
            sparse_val = rets
            
        # 裁剪到回测区间
        backtest_dates = timing_series.index[timing_series.index >= self.start_date]
        sparse_df = pd.DataFrame(index=backtest_dates, columns=self.sector_prices.columns)
        
        # 提取触发日期坐标
        triggered = timing_series.loc[backtest_dates]
        trigger_dates = triggered[triggered == 1].index
        
        # 关键：确保触发日期在收益率矩阵中存在
        valid_trigger_dates = trigger_dates.intersection(sparse_val.index)
        
        if not valid_trigger_dates.empty:
            sparse_df.loc[valid_trigger_dates] = sparse_val.loc[valid_trigger_dates]
        
        sparse_df.to_parquet(sparse_file)
        return sparse_df

    def run_strategy(self, signal_type):
        """
        运行单个策略流程
        """
        logger.info(f"\n>>>> 正在处理策略: {signal_type} ({self.sector_type}) <<<<")
        
        # 1. 择时
        timing_series = self.calculate_timing(signal_type)
        
        # 2. 稀疏因子
        sparse_signal_df = self.calculate_sparse_factor(signal_type, timing_series)
        
        # 3. 运行测试
        output_dir = f"results/gx_pit_mom/gx_pit_{signal_type}/zx_{self.sector_type}"
        
        # 排除掉价格数据中不存在的日期 (避免 KeyError)
        common_dates = sparse_signal_df.index.intersection(self.sector_prices.index)
        if len(common_dates) == 0:
            logger.warning(f"{signal_type} 无重合的可回测日期。")
            return
            
        tester = SparseSignalTester(
            signal_series=sparse_signal_df.loc[common_dates],
            price_df=self.sector_prices.loc[common_dates],
            benchmark_series=self.index_data['close'].loc[common_dates],
            period=20,
            n_groups=5 if self.sector_type == 'yjhy' else 10,
            output_dir=output_dir,
            data_folder=self.sparse_path
        )
        
        results = tester.run_backtest()
        if results.empty:
            logger.warning(f"{signal_type} 回测结束，未捕捉到触发事件。")
            return
        
        # 绘图输出
        tester.plot_signals(self.index_data['close'], asset_name='中证全指', title=f"{signal_type} 信号触发情况")
        tester.plot_annual_frequency(title=f"{signal_type} 分年度信号数量")
        tester.plot_group_returns(results)
        tester.print_performance_report()

def run_all(sector_type='ejhy', signals=['breakout', 'rebound', 'rotation']):
    tester = GXPITMomTester(sector_type=sector_type)
    for sig in signals:
        tester.run_strategy(sig)
# 
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GX PIT Momentum Strategy Framework")
    parser.add_argument("--sector", type=str, default="yjhy", choices=["yjhy", "ejhy", "all"], help="Sector definition")
    parser.add_argument("--signals", type=str, nargs="+", default=['rotation', 'breakout', 'rebound'], help="Signals to run")
    args = parser.parse_args()
    
    run_all(sector_type=args.sector, signals=args.signals)
