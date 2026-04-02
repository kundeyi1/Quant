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
    def __init__(self, start_date="2013-01-01", end_date="2026-03-20", 
                 sector_type="yjhy", base_data_path="D:/DATA"):
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
        index_file = "INDEX/STOCK/000985.CSI.xlsx" 
        self.index_data = self.dp.get_ohlc_data(index_file, name="target_index").loc[self.pre_start_date:self.end_date]
        
        if self.sector_type == "ejhy":
            sector_path = r"D:\DATA\INDEX\ZX\ejhy_prices.csv"
        elif self.sector_type == "yjhy":
            sector_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
        else:
            sector_path = f"INDEX/ZX/ZX_{self.sector_type.upper()}.xlsx"

        self.sector_prices = self.dp.get_wide_table(sector_path).loc[self.pre_start_date:self.end_date]
        yjhy_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
        self.yjhy_prices = self.dp.get_wide_table(yjhy_path).loc[self.pre_start_date:self.end_date]

    def save_timing_signal(self, signal, full_name):
        os.makedirs(self.timing_path, exist_ok=True)
        filepath = os.path.join(self.timing_path, f"{full_name}.parquet")
        signal.to_frame().to_parquet(filepath)
        return filepath

    def calculate_timing(self, signal_type):
        start_str = pd.to_datetime(self.start_date).strftime("%Y%m%d")
        end_str = pd.to_datetime(self.end_date).strftime("%Y%m%d")
        full_name = f"gx_pit_{signal_type}_{self.sector_type}_{start_str}_{end_str}"
        
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
        rets = self.sector_prices.pct_change()
        
        if signal_type == "breakout" or signal_type == "rotation":
            sparse_val = rets
        elif signal_type == "rebound":
            avg_prev_rets = rets.shift(1).rolling(20).mean()
            sparse_val = rets - avg_prev_rets
            
        backtest_dates = timing_series.index[timing_series.index >= self.start_date]
        sparse_df = pd.DataFrame(index=backtest_dates, columns=self.sector_prices.columns)
        trigger_dates = timing_series[timing_series == 1].index
        valid_trigger_dates = trigger_dates.intersection(sparse_val.index)
        
        if not valid_trigger_dates.empty:
            sparse_df.loc[valid_trigger_dates] = sparse_val.loc[valid_trigger_dates]
        
        return sparse_df

    def run_strategy(self, signal_type):
        timing_series = self.calculate_timing(signal_type)
        sparse_signal_df = self.calculate_sparse_factor(signal_type, timing_series)
        output_dir = f"results/gx_pit_mom/gx_pit_{signal_type}/zx_{self.sector_type}"
        
        tester = SparseSignalTester(
            signal_series=sparse_signal_df,
            price_df=self.sector_prices,
            benchmark_series=self.index_data["close"],
            period=20,
            n_groups=5 if self.sector_type == "yjhy" else 10,
            output_dir=output_dir
        )
        
        results = tester.run_backtest()
        # 原始可视化 (利用 SparseSignalTester 内部包装)
        tester.plot_signals(self.index_data["close"], title=f"{signal_type} Signal Triggers")
        tester.plot_annual_frequency(title=f"{signal_type} Annual Distribution")
        tester.plot_group_returns(results)
        tester.print_performance_report()

def run_all(sector_type="ejhy", signals=["breakout", "rebound", "rotation"]):
    tester = GXPITMomTester(sector_type=sector_type)
    for sig in signals:
        tester.run_strategy(sig)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GX PIT Momentum Strategy Framework")
    parser.add_argument("--sector", type=str, default="yjhy", choices=["yjhy", "ejhy", "all"], help="Sector definition")
    parser.add_argument("--signals", type=str, nargs="+", default=["rotation", "breakout", "rebound"], help="Signals to run")
    args = parser.parse_args()
    
    run_all(sector_type=args.sector, signals=args.signals)
