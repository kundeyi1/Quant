import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from core.TimingTester import TimingTester
from timing import report_timing, pattern_timing
from core.Logger import logger

class TimingMomTester:
    """
    时点动量拓展测试框架 (集成了华泰技术信号与形态学择时)
    """
    def __init__(self, start_date="2013-01-01", end_date="2026-03-26", 
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
        
        if self.sector_type == "yjhy":
            sector_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
        elif self.sector_type == "ejhy":
            sector_path = r"D:\DATA\INDEX\ZX\ejhy_prices.csv"
        else:
            sector_path = f"INDEX/ZX/ZX_{self.sector_type.upper()}.xlsx"

        self.sector_prices = self.dp.get_wide_table(sector_path).loc[self.pre_start_date:self.end_date]
        self.yjhy_prices = self.dp.get_wide_table(r"D:\DATA\INDEX\ZX\yjhy_prices.csv").loc[self.pre_start_date:self.end_date]

    def calculate_timing(self, signal_type):
        logger.info(f"计算择时信号: {signal_type}...")
        
        # 1. 国信扩展
        if signal_type == "breakout":
            signal = report_timing.gx_pit_breakout(self.index_data)
        elif signal_type == "rebound":
            signal = report_timing.gx_pit_rebound(self.index_data)
        elif signal_type == "rotation":
            signal = report_timing.gx_pit_rotation(self.index_data, self.yjhy_prices)
            
        # 2. 华泰技术指标 (ht_)
        elif signal_type == "ht_rsrs":
            signal = report_timing.ht_rsrs_timing(self.index_data)
        elif signal_type == "ht_bollinger":
            signal = report_timing.ht_bollinger_timing(self.index_data)
        elif signal_type == "ht_volume_volatility":
            signal = report_timing.ht_volume_volatility_timing(self.index_data)
        elif signal_type == "ht_price_bias":
            signal = report_timing.ht_price_bias_timing(self.index_data)
            
        # 3. 形态学信号 (pattern_)
        elif signal_type == "double_bottom":
            # 调试：显式打印
            pattern_ser = pattern_timing.detect_double_pattern(self.index_data)
            cnt = (pattern_ser == "Double Bottom").sum()
            print(f"Double Bottom Detected: {cnt}")
            signal = (pattern_ser == "Double Bottom").astype(int)
        elif signal_type == "head_shoulder_bottom":
            pattern_ser = pattern_timing.detect_head_shoulder(self.index_data)
            cnt = (pattern_ser == "Inverse Head and Shoulder").sum()
            print(f"Head Shoulder Bottom Detected: {cnt}")
            signal = (pattern_ser == "Inverse Head and Shoulder").astype(int)
        elif signal_type == "triangle":
            pattern_ser = pattern_timing.detect_triangle_pattern(self.index_data)
            signal = pattern_ser.notna().astype(int)
        else:
            raise ValueError(f"Unknown signal: {signal_type}")
            
        return signal.rename(signal_type)

    def run_full_evaluation(self, signal_types=None):
        if signal_types is None:
            # 修改为仅执行形态学识别的检验：双底、头肩底
            signal_types = ["double_bottom", "head_shoulder_bottom"]

        logger.info(f"\n{'='*20} 开始择时信号绩效评估 {'='*20}")
        eval_output_dir = os.path.join("results", "timing_mom", "evaluation")
        os.makedirs(eval_output_dir, exist_ok=True)
        
        benchmark_close = self.index_data["close"]
        signals_map = {}
        
        for st in signal_types:
            try:
                sig = self.calculate_timing(st).reindex(benchmark_close.index).fillna(0).astype(int)
                if sig.sum() > 0:
                    signals_map[st] = sig
                    t_tester = TimingTester(signal_series=sig, benchmark_series=benchmark_close, output_dir=os.path.join(eval_output_dir, st))
                    t_tester.run_timing_analysis(period=20)
                    t_tester.plot_signals(asset_name="000985", title=f"{st} Signal Triggers")
                else:
                    logger.warning(f"信号 {st} 未触发。")
            except Exception as e:
                logger.error(f"信号 {st} 错误: {e}")

        if len(signals_map) > 1:
            combined_sig = pd.Series(0, index=benchmark_close.index)
            for s in signals_map.values(): combined_sig |= (s == 1)
            t_tester_comb = TimingTester(signal_series=combined_sig.astype(int), benchmark_series=benchmark_close, output_dir=os.path.join(eval_output_dir, "combined"))
            t_tester_comb.run_timing_analysis()
            t_tester_comb.plot_signals(title="Combined Signal Triggers")

if __name__ == "__main__":
    tester = TimingMomTester()
    tester.run_full_evaluation(signal_types=["double_bottom", "head_shoulder_bottom"])
