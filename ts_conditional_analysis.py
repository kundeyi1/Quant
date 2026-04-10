import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
from pathlib import Path

# 配置绘制参数
plt.rcParams['figure.figsize'] = [12, 7]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
warnings.filterwarnings('ignore')

class TimeSeriesConditionalAnalysis:
    """
    时序条件分析框架：针对单个指数/时间序列
    分析 Trigger 在不同 Env 条件下的表现、切割效果及甜点区域
    """
    def __init__(self, output_root="results/ts_conditional_momentum"):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def calculate_returns(self, df, price_col='close'):
        """计算未来多周期收益率"""
        df = df.sort_values('date')
        df['ret_1d'] = df[price_col].shift(-1) / df[price_col] - 1
        df['ret_5d'] = df[price_col].shift(-5) / df[price_col] - 1
        df['ret_20d'] = df[price_col].shift(-20) / df[price_col] - 1
        return df

    def get_time_series_rank(self, series, window=250):
        """计算时序分位数 (Rolling Rank)"""
        return series.rolling(window).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1])

    def analyze_ts_baseline(self, df, trigger_col):
        """Baseline 分析：Trigger 的时序预测能力"""
        trigger_dir = self.output_root / trigger_col
        trigger_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用 250 日滚动分位数作为信号
        df['trigger_signal'] = self.get_time_series_rank(df[trigger_col])
        
        for ret_col in ['ret_1d', 'ret_5d', 'ret_20d']:
            temp = df.dropna(subset=['trigger_signal', ret_col])
            
            # 1. IC 时间序列
            ic = temp['trigger_signal'].rolling(120).corr(temp[ret_col])
            plt.figure()
            ic.plot(title=f"TS IC (120D Rolling): {trigger_col} ({ret_col})", grid=True)
            plt.axhline(0, color='red', linestyle='--')
            plt.savefig(trigger_dir / f"ts_ic_{ret_col}.png"); plt.close()
            
            # 2. 收益率分布比较 (高分位 vs 全样本)
            plt.figure()
            v_min, v_max = temp[ret_col].quantile([0.01, 0.99])
            plot_df = temp[(temp[ret_col] >= v_min) & (temp[ret_col] <= v_max)]
            sns.kdeplot(plot_df[ret_col], label='Benchmark', shade=True)
            sns.kdeplot(plot_df[plot_df['trigger_signal'] > 0.8][ret_col], label='High Signal (>0.8)', shade=True)
            plt.title(f"TS Dist: {trigger_col} ({ret_col})")
            plt.legend(); plt.savefig(trigger_dir / f"ts_dist_{ret_col}.png"); plt.close()

            # 3. 分层收益统计
            temp['bin'] = pd.qcut(temp['trigger_signal'], 5, labels=False)
            stats = temp.groupby('bin')[ret_col].agg(['mean', 'std', 'count'])
            stats.to_csv(trigger_dir / f"ts_stats_{ret_col}.csv")

    def run_ts_segmentation(self, df, trigger_col, env_col):
        """环境切割与 Sweet Spot 扫描 (时序版)"""
        sub_dir = self.output_root / trigger_col / env_col
        sub_dir.mkdir(parents=True, exist_ok=True)
        
        df['env_signal'] = self.get_time_series_rank(df[env_col])
        df['trigger_signal'] = self.get_time_series_rank(df[trigger_col])
        
        for ret_col in ['ret_1d', 'ret_5d', 'ret_20d']:
            # --- 分环境验证 ---
            # 将环境分为 3 类：Low(0-33%), Mid(33-66%), High(66-100%)
            df['env_bin'] = pd.qcut(df['env_signal'], 3, labels=['Low', 'Mid', 'High'])
            
            plt.figure()
            for label in ['Low', 'Mid', 'High']:
                subset = df[df['env_bin'] == label].dropna(subset=['trigger_signal', ret_col])
                if subset.empty: continue
                # 计算信号分层收益
                subset['sig_bin'] = pd.qcut(subset['trigger_signal'], 5, labels=False)
                bin_means = subset.groupby('sig_bin')[ret_col].mean()
                plt.plot(bin_means.index, bin_means.values, marker='o', label=f"Env_{label}")
            
            plt.title(f"{trigger_col} Performance by {env_col} ({ret_col})")
            plt.xlabel("Trigger Signal Bin")
            plt.ylabel("Avg Return")
            plt.legend(); plt.grid(True)
            plt.savefig(sub_dir / f"ts_seg_{ret_col}.png"); plt.close()

            # --- Sweet Spot 扫描 ---
            spots = []
            steps = np.arange(0, 0.85, 0.05)
            for start in steps:
                end = start + 0.2
                subset = df[(df['env_signal'] >= start) & (df['env_signal'] <= end)].copy()
                if len(subset) < 100: continue
                
                # 计算该环境下的多头超额 (High - Low)
                subset['sig_bin'] = pd.qcut(subset['trigger_signal'], 5, labels=False, duplicates='drop')
                g_high = subset[subset['sig_bin'] == 4][ret_col].mean()
                g_low = subset[subset['sig_bin'] == 0][ret_col].mean()
                
                spots.append({
                    'env_start': start,
                    'ls_spread': g_high - g_low,
                    'count': len(subset)
                })
            
            if spots:
                spot_df = pd.DataFrame(spots)
                plt.figure()
                plt.plot(spot_df['env_start'], spot_df['ls_spread'], marker='s', color='darkorange')
                plt.title(f"TS Sweet Spot: {trigger_col} BY {env_col} ({ret_col})")
                plt.xlabel(f"{env_col} Percentile Start")
                plt.ylabel("Long-Short Spread")
                plt.grid(True); plt.savefig(sub_dir / f"ts_sweet_spot_{ret_col}.png"); plt.close()
                spot_df.to_csv(sub_dir / f"ts_sweet_spot_{ret_col}.csv", index=False)

if __name__ == "__main__":
    # 使用指定的 Excel 指数文件进行检验
    try:
        # 1. 加载指数数据
        # INDEX_PATH = "D:/DATA/INDEX/STOCK/000985.CSI.xlsx"
        INDEX_PATH = "D:/DATA/INDEX/STOCK/000300.SH.xlsx"
        
        # skiprows=1 因为第0行是中文表头，第1行是英文列名
        df_index = pd.read_excel(INDEX_PATH, skiprows=1)
        df_index.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        df_index['date'] = pd.to_datetime(df_index['date'])
        
        # 提取 code (从文件名中提取)
        target_code = Path(INDEX_PATH).name.split('.')[0] # e.g., '000300'
        df_index['code_str'] = target_code.zfill(6)
        
        print(f"Index data loaded: {len(df_index)} rows for {target_code}")
        
        # 2. 加载因子 (Trigger & Env)
        # 注意：这里的因子文件通常包含全市场股票，我们需要将其聚合为指数级别的信号
        # 如果您的因子已经是指数级别的，则直接合并；如果是全市场的，我们需要做一个简单的聚合（如均值）
        def load_index_level_factor(fact_name):
            path = f"D:/DATA/FACTORS/{fact_name}.csv"
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'])
            # 若因子文件中没有该指数的代码，则取全市场的均值作为“市场环境”或“市场情绪”
            # 这里先尝试匹配指数代码，不行则取均值
            df['code_str'] = df['code'].astype(str).str.split('.').str[0].str.zfill(6)
            df_target = df[df['code_str'] == target_code.zfill(6)]
            
            if df_target.empty:
                print(f"Warning: {target_code} not in {fact_name}.csv. Using market mean as proxy.")
                return df.groupby('date')[fact_name].mean().reset_index()
            else:
                return df_target[['date', fact_name]]

        df_trigger = load_index_level_factor("Vol_Explosion_Today")
        df_env = load_index_level_factor("Volat_Ratio_5_20_Lag1")
        
        # 3. 合并数据
        df_merged = pd.merge(df_index, df_trigger, on='date', how='inner')
        df_merged = pd.merge(df_merged, df_env, on='date', how='inner')
        
        print(f"Merged Data: {len(df_merged)} rows from {df_merged['date'].min()} to {df_merged['date'].max()}")

        if df_merged.empty:
            print("Final merged dataframe is empty. Please check date alignment between Index and Factors.")
            exit(1)

        # 4. 执行分析
        analyzer = TimeSeriesConditionalAnalysis()
        df_merged = analyzer.calculate_returns(df_merged)
        
        trigger_col = "Vol_Explosion_Today"
        env_col = "Volat_Ratio_5_20_Lag1"
        
        print(f"Starting TS analysis for {trigger_col} by {env_col} on {target_code}...")
        analyzer.analyze_ts_baseline(df_merged, trigger_col)
        analyzer.run_ts_segmentation(df_merged, trigger_col, env_col)
        print(f"Done. Results saved in results/ts_conditional_momentum/{trigger_col}/{env_col}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
