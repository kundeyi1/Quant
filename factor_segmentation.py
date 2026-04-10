import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from pathlib import Path
from tqdm import tqdm

from core.DataManager import DataProvider
from core.Logger import logger
from core.FactorTester import FactorTester

plt.rcParams["figure.figsize"] = [12, 7]
plt.rcParams["font.size"] = 10
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
warnings.filterwarnings("ignore")

class FactorSegmentationAnalysis:
    def __init__(self, data_root="D:/DATA", output_dir="results/factor_segmentation"):
        self.data_root = Path(data_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.provider = DataProvider(str(self.data_root))
        self.price_df = None
        self.factors_cache = {}

    def prepare_base_data(self, start_date, end_date):
        logger.info("Initializing high-performance data backbone...")
        price_path = self.data_root / "STOCK" / "all_stock_data_ts_20140102_20251231.csv"
        df = pd.read_csv(price_path, usecols=["date", "code", "close"])
        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]
        df["code"] = df["code"].astype(str).str.zfill(6)
        df = df.sort_values(["code", "date"])
        df["future_return_1d"] = df.groupby("code")["close"].shift(-1) / df["close"] - 1
        df["future_return_5d"] = df.groupby("code")["close"].shift(-5) / df["close"] - 1
        df["future_return_20d"] = df.groupby("code")["close"].shift(-20) / df["close"] - 1
        self.price_df = df.dropna(subset=["future_return_1d", "future_return_5d", "future_return_20d"])

    def calculate_rank_score(self, df, column):
        return df.groupby("date")[column].transform(lambda x: x.rank(pct=True))

    def load_and_preprocess_factors(self, factor_list):
        for factor_name in tqdm(factor_list, desc="Pre-Ranking Factors"):
            path = self.data_root / "FACTORS" / f"{factor_name}.csv"
            if not path.exists(): continue
            f_df = pd.read_csv(path)
            f_df["date"] = pd.to_datetime(f_df["date"])
            f_df["code"] = f_df["code"].astype(str).str.zfill(6)
            f_df[f"{factor_name}_score"] = self.calculate_rank_score(f_df, factor_name)
            self.factors_cache[factor_name] = f_df[["date", "code", factor_name, f"{factor_name}_score"]]

    def plot_nav_curves(self, df, target_col, tool_col, bin_id, ret_col, save_path):
        """调用 FactorTester 实现标准分组绘图 (解决非重叠采样 & 杠杆问题)"""
        # 结果存放在特定的子目录下
        temp_output_dir = os.path.dirname(save_path)
        
        # 1. 模拟一个 FactorTester 实例
        # 注意：这里我们避开 load_price_data，因为 self.price_df 已经在内存中
        tester = FactorTester(df["date"].min(), df["date"].max(), output_dir=temp_output_dir)
        
        # 2. 注入价格数据 (FactorTester 需要宽表格式进行采样)
        # 我们直接使用预计算好的收益率来绕过 FactorTester 内部的 get_forward_returns 逻辑
        # 或者更简单的：直接传递格式化好的 factor_data 给 backtest
        
        # 准备格式：FDate, SecCode, FValue
        factor_data = df[["date", "code", "target_score"]].rename(
            columns={"date": "FDate", "code": "SecCode", "target_score": "FValue"}
        )
        
        # 确定调仓周期
        freq_tag = "W" if "5d" in ret_col else "D"
        
        # 3. 构建临时价格宽表供 tester 使用 (主要是为了让 tester 能跑通内部逻辑)
        # 如果 self.price_df 很大，这里我们只取当前子集的 code
        codes = df["code"].unique()
        tester.prices = self.price_df[self.price_df["code"].isin(codes)].pivot(index="date", columns="code", values="close")
        tester.prices.index.name = "FDate"
        
        # 4. 执行标准回测绘图    
        # 设置 tester 的输出路径为当前目录
        tester.output_dir = temp_output_dir
        
        # 运行 backtest，仅用于计算净值，不在此处生成全量图表（以免产生 IC/分布/箱线图等）
        eval_metrics, nav_df, merged_data = tester.backtest(
            factor_name=f"group_{bin_id+1}_{freq_tag}", 
            factor_data=factor_data, 
            interval_tag=freq_tag, 
            groups=10, 
            if_plot=False
        )
        # 仅生成分组收益曲线图
        tester.plot_group_return(f"group_{bin_id+1}_{freq_tag}", nav_df)
        
        # 由于我们注释了 plot_group_return_ic，这里直接对生成的 分组累积收益.png 进行操作
        generated_fig = os.path.join(temp_output_dir, f"group_{bin_id+1}_{freq_tag}_分组累积收益.png")
        if os.path.exists(generated_fig):
            if os.path.exists(save_path): os.remove(save_path)
            os.rename(generated_fig, save_path)

    def run_segmentation(self, df, target_col, tool_col, n_groups=5):
        segment_dir = self.output_dir / target_col / tool_col
        segment_dir.mkdir(parents=True, exist_ok=True)
        df["tool_score"] = df[f"{tool_col}_score"]
        df["target_score"] = df[f"{target_col}_score"]
        df["tool_group"] = df.groupby("date")["tool_score"].transform(lambda x: pd.qcut(x, n_groups, labels=False, duplicates="drop"))
        all_stats = []
        for ret_col in ["future_return_1d", "future_return_5d"]:
            for bin_id in range(n_groups):
                df_bin = df[df["tool_group"] == bin_id].copy()
                if df_bin.empty: continue
                fig_name = f"nav_{ret_col}_tool_group_{bin_id+1}.png"
                self.plot_nav_curves(df_bin, target_col, tool_col, bin_id, ret_col, segment_dir / fig_name)
        pd.DataFrame(all_stats).to_csv(segment_dir / "segmentation_summary.csv", index=False)

    def run_full_pipeline(self, target_list, tool_list, start_date, end_date, n_groups=5):
        self.prepare_base_data(start_date, end_date)
        all_factors = list(set(target_list + tool_list))
        self.load_and_preprocess_factors(all_factors)
        for target in target_list:
            if target not in self.factors_cache: continue
            
            # 合并对象因子数据
            target_df = pd.merge(self.price_df, self.factors_cache[target], on=["date", "code"], how="inner")
            
            for tool in tool_list:
                if tool not in self.factors_cache: continue
                combined = pd.merge(target_df, self.factors_cache[tool], on=["date", "code"], how="inner")
                logger.info(f"Analyzing Segmentation: Target={target} | Tool={tool} ...")
                self.run_segmentation(combined, target, tool, n_groups=n_groups)

if __name__ == "__main__":
    targets =["Trend_Slope_Lag1", "Position_Lag1", "Pullback_Depth_Lag1", "J_lag1", "Volat_Ratio_5_20_Lag1", 
             "Volume_Ratio_5_20_Lag1", "Volat_Compression_Lag1", "PV_Consistency_Lag1", 
             "Bullish_Alignment_Lag1"] 
    tools = ["Momentum_1D_Today", "Vol_Explosion_Today", "Accel_Today", 'Body_Strength_Today', 'Displacement_Ratio_Today']
    analysis = FactorSegmentationAnalysis()
    analysis.run_full_pipeline(targets, tools, "2020-01-01", "2025-12-31", n_groups=3)
