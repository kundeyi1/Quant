import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import traceback
from datetime import datetime
from core.DataManager import DataProvider
from core.FactorTester import FactorTester
from factors.technical_factors import PriceFactors, VolumeFactors, TrendFactors, VolatilityFactors

class FactorValidator:
    """
    通用因子检验与保存框架。
    升级版：为每个因子创建独立研究文件夹，并深度集成 FactorTester 的分组与多空分析功能。
    新增：自动导出每个因子的详细绩效 CSV 报告。
    """
    def __init__(self, start_date='2017-01-01', end_date='2025-12-31', 
                 interval_tag='D',
                 factor_save_path="D:/DATA/FACTORS", 
                 result_save_path="./results/factors"):
        self.dm = DataProvider()
        self.start_date = start_date
        self.end_date = end_date
        self.interval_tag = interval_tag
        
        # 路径配置：增加调仓频率子目录
        self.factor_save_path = os.path.join(factor_save_path)
        self.result_save_path = os.path.join(result_save_path, interval_tag)
        os.makedirs(self.factor_save_path, exist_ok=True)
        os.makedirs(self.result_save_path, exist_ok=True)
        
    def load_base_data(self, filename="STOCK/all_stock_data_ts_20140102_20251231.csv"):
        """加载基础行情数据进行因子计算"""
        print(f"Loading calculation base data ({self.start_date} to {self.end_date})...")
        self.data = self.dm.get_universe_data(
            filename=filename,
            universe=None, # 全市场
            start_date=self.start_date, 
            end_date=self.end_date
        )
        print(f"Data Loaded: {len(self.data)} records for factor calculation.")

    def run_pipeline(self, factor_map):
        """
        全自动化流水线：
        1. 因子计算并保存
        2. 为每个因子建立单独文件夹存储图表、分组净值、多空曲线和绩效统计报告
        """
        df = self.data.copy()
        price_data_path = "D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv"
        results = []

        for name, func in factor_map.items():
            try:
                # 1. 因子计算
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing: {name} ...")
                f_val = func(df)
                if isinstance(f_val, pd.Series):
                    f_val = f_val.to_frame(name)
                
                # 确保列名是因子名
                f_val.columns = [name] if len(f_val.columns) == 1 else f_val.columns

                # 2. 因子数据落盘
                f_save_filename = os.path.join(self.factor_save_path, f"{name}.csv")
                f_val.to_csv(f_save_filename)
                
                # 3. 创建因子的专属检验结果文件夹
                factor_report_dir = os.path.join(self.result_save_path, name)
                os.makedirs(factor_report_dir, exist_ok=True)
                
                # 4. 调用 FactorTester 进行深度分析
                # 传入 FactorTester 的 output_dir 会在其目录下生成 plots/ 等
                tester = FactorTester(
                    start_date=self.start_date, 
                    end_date=self.end_date, 
                    output_dir=factor_report_dir
                )
                
                # 准备 FactorTester 数据格式
                # 要求输入是 ['FDate', 'SecCode', 'FValue']
                f_data_for_tester = f_val.reset_index()
                f_data_for_tester.columns = ['FDate', 'SecCode', 'FValue']
                
                # FactorTester 内部加载价格宽表
                tester.load_price_data(price_data_path)
                
                # 执行回测：这里会自动计算 IC、分组收益、绘制累计净值图
                # if_plot=True 触发图表输出到 factor_report_dir/plots/
                metrics, nav_df = tester.backtest(
                    factor_name=name, 
                    factor_data=f_data_for_tester, 
                    interval_tag=self.interval_tag, # 使用实例定义的调仓频率
                    groups=5,
                    if_plot=True
                )
                
                # 保存绩效报告
                # 将 FactorTester 返回的 metrics (DataFrame) 和 nav_df (DataFrame) 保存为 CSV
                performance_csv = os.path.join(factor_report_dir, f"{name}_performance_summary.csv")
                nav_csv = os.path.join(factor_report_dir, f"{name}_group_nav.csv")
                metrics.to_csv(performance_csv)
                nav_df.to_csv(nav_csv)
                
                # 绩效指标提取
                # FactorTester.backtest 返回的 metrics 为 index=factor_name 的单行 DataFrame
                m_view = metrics.iloc[0].to_dict()
                
                rank_ic = m_view.get('RankIC', 0)
                icir = m_view.get('RankICIR', 0)
                long_ann = m_view.get('多头组年化收益', 0)
                max_dd = m_view.get('多头组最大回撤', 0)

                print("\n" + "="*110)
                print(f"{'Factor Name':<30} | {'RankIC':<10} | {'RankICIR':<10} | {'Long AnnRet':<12} | {'MaxDD':<10}")
                print("-" * 110)
                print(f"{name:<30} | {rank_ic:>10.4f} | {icir:>10.4f} | {long_ann:>12.2%} | {max_dd:>10.2%}")
                
                results.append({
                    "Factor": name,
                    "RankIC": rank_ic,
                    "RankICIR": icir,
                    "Long_AnnRet": long_ann,
                    "Long_MaxDD": max_dd,
                    "Report_Folder": factor_report_dir,
                    "Summary_CSV": performance_csv
                })
                
            except Exception as e:
                print(f"FAILED to process {name}: {e}")
                traceback.print_exc()

        # 5. 保存全局总表
        if results:
            res_df = pd.DataFrame(results)
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_summary_file = os.path.join(self.result_save_path, f"B2_Performance_Leaderboard_{now_str}.csv")
            res_df.to_csv(final_summary_file, index=False)
            print(f"\n[SUCCESS] Batch Validation Finished.")
            print(f"- Performance Metrics per Factor: {self.result_save_path}/{{Factor}}/*_performance_summary.csv")
            print(f"- Overall Leaderboard: {final_summary_file}")

if __name__ == "__main__":
    # ---------------------------------------------------------
    # 因子定义注册点
    # ---------------------------------------------------------
    factor_definitions = {
        # 1. 趋势与位置：衡量昨日及之前的结构状态 (Shift 1)
        "Trend_Slope_Lag1": lambda x: TrendFactors.trend_slope(x).shift(1),
        "Position_Lag1": lambda x: PriceFactors.position(x).shift(1),
        "Pullback_Depth_Lag1": lambda x: PriceFactors.pullback_depth(x).shift(1),
        
        # 2. 波动压缩类：衡量昨日的收敛程度 (Shift 1)
        "Volat_Ratio_5_20_Lag1": lambda x: VolatilityFactors.volatility_ratio(x, short_window=5, long_window=20).shift(1),
        "Volume_Ratio_5_20_Lag1": lambda x: VolumeFactors.volume_ratio(x, short_window=5, long_window=20).shift(1),

        "Volat_Compression_Lag1": lambda x: VolatilityFactors.volatility_compression(x, short_window=5, long_window=20).shift(1),

        # 3. 启动强度：衡量当日的爆发 (不 Shift)
        "Vol_Explosion_Today": lambda x: VolumeFactors.volume_ratio(x, short_window=1, long_window=5), 
        "Accel_Today": lambda x: PriceFactors.momentum_acceleration(x),
        "Body_Strength_Today": lambda x: PriceFactors.body_strength(x)
    }

    # ---------------------------------------------------------
    # 设置测试范围并运行
    # ---------------------------------------------------------
    start_date = '2017-01-01'
    end_date = '2025-12-31'
    interval = 'W'
    
    validator = FactorValidator(start_date=start_date, end_date=end_date, interval_tag=interval)
    validator.load_base_data()
    validator.run_pipeline(factor_definitions)
