# 筛选trigger>0.8后检验env_factor的效果

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
import warnings
from tqdm import tqdm

warnings.filterwarnings('ignore')

plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class FactorTester:
    """
    因子测试框架
    包括数据加载、收益率计算、回测逻辑、绩效评估
    """
    def __init__(self, start_date, end_date, output_dir="results/factors"):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.output_dir = output_dir
        os.makedirs(self.fig_path, exist_ok=True)
        
        self.interval_mapping = {'D': 1, 'W': 5, 'M': 20}
        self.factors = {}
        self.prices = None

    def load_price_data(self, data_path, codes_list=None):
        """
        从 data_path 加载原始价格数据并进行初步清洗
        """
        print(f"正在从 {data_path} 加载行情数据...")
        cols = ["date", "code", "close"]
        try:
            df = pd.read_csv(data_path, usecols=cols)
            df["date"] = pd.to_datetime(df["date"])
            # 时间过滤
            df = df[(df["date"] >= self.start_date) & (df["date"] <= self.end_date)]
            df["code"] = df["code"].astype(str).str.zfill(6)
            
            if codes_list:
                df = df[df["code"].isin(codes_list)]
                
            # 去重
            df = df.drop_duplicates(subset=["date", "code"])
            
            # 透视成宽表: Index=Date, Columns=Code, Values=Close
            self.prices = df.pivot(index="date", columns="code", values="close")
            self.prices.index.name = "FDate"
            print(f"行情数据加载完成，涵盖 {len(self.prices)} 个交易日，{len(self.prices.columns)} 只股票")
        except Exception as e:
            print(f"加载价格数据失败: {e}")
            raise


    def get_forward_returns(self, interval_tag='D'):
        """
        计算周/月度采样点的前瞻收益率
        """
        interval = self.interval_mapping.get(interval_tag, 1)
        
        # 1. 获取全量的行情收益率
        stock_r_wide_all = self.prices.shift(-interval) / self.prices - 1
        
        # 2. 只保留采样点日期 (例如周一), 避免每日重叠计算
        # 使用 resample 或简单的切片来实现
        # 这里假设 interval = 5 (周), 20 (月), 1 (日)
        # 逻辑：从第一天开始，每隔 interval 天取一次采样
        sample_indices = np.arange(0, len(self.prices), interval)
        sample_dates = self.prices.index[sample_indices]
        
        stock_r_wide = stock_r_wide_all.loc[sample_dates]
        
        # 3. 转换成长表格式
        stock_r = stock_r_wide.stack().reset_index()
        stock_r.columns = ['FDate', 'SecCode', 'r']
        return stock_r

    def backtest(self, factor_name, factor_data, interval_tag='D', groups=5, if_plot=True):
        """
        核心回测逻辑
        :param factor_data: DataFrame 包含 ['FDate', 'SecCode', 'FValue']
        """
        interval = self.interval_mapping.get(interval_tag, 1)
        
        stock_r = self.get_forward_returns(interval_tag)
        
        factor_data['FDate'] = pd.to_datetime(factor_data['FDate'])
        stock_r['FDate'] = pd.to_datetime(stock_r['FDate'])
        
        merged_data = factor_data.merge(stock_r, on=['SecCode', 'FDate'], how='right')
        merged_data.dropna(subset=['FValue'], inplace=True)
        merged_data.sort_values(by=['FDate', 'SecCode'], inplace=True)
        
        merged_data['FRank'] = merged_data.groupby('FDate')['FValue'].rank(pct=True)
        factor_group = merged_data.groupby('FDate')

        ic_series = factor_group.apply(lambda x: x['r'].corr(x['FValue'], method='pearson'))
        rank_ic_series = factor_group.apply(lambda x: x['r'].corr(x['FRank'], method='spearman'))
        
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        rank_ic_mean = rank_ic_series.mean()
        rank_ic_std = rank_ic_series.std()
        
        annual_factor = (250 / interval) ** 0.5
        icir = annual_factor * ic_mean / ic_std if ic_std != 0 else 0
        rank_icir = annual_factor * rank_ic_mean / rank_ic_std if rank_ic_std != 0 else 0

        unique_dates = sorted(merged_data['FDate'].unique())
        factor_group_eval = pd.DataFrame(index=unique_dates)
        
        for i in range(groups):
            lower = i / groups
            upper = (i + 1) / groups
            group_mask = (merged_data['FRank'] >= lower) & (merged_data['FRank'] <= upper)
            factor_group_eval[f'group{i+1}'] = merged_data.loc[group_mask].groupby('FDate')['r'].mean()

        factor_group_eval = factor_group_eval.shift(1)
        nav_df = (1 + factor_group_eval).cumprod().fillna(1.0)

        long_nav = nav_df[f'group{groups}']
        drawdown = long_nav / long_nav.cummax() - 1
        max_drawdown = drawdown.min()
        
        if len(nav_df) > 0:
            total_periods = len(nav_df)
            factor_annual_return = long_nav.iloc[-1] ** (1 / (interval * total_periods / 250)) - 1
        else:
            factor_annual_return = 0


        if if_plot:
            self.plot_group_return_ic(factor_name, nav_df, rank_ic_series)
            self.plot_group_return(factor_name, nav_df)

        eval_metrics = pd.DataFrame({
            'IC': [ic_mean],
            'ICIR': [icir],
            'RankIC': [rank_ic_mean],
            'RankICIR': [rank_icir],
            '多头组最大回撤': [max_drawdown],
            '多头组年化收益': [factor_annual_return]
        }, index=[factor_name])

        return eval_metrics, nav_df

    def plot_group_return_ic(self, factor_name, nav_df, daily_rank_ic):
        """
        分组净值 + 因子 IC 双轴图
        """
        fig, ax1 = plt.subplots(figsize=(12, 7))
        nav_df.plot(ax=ax1)
        ax1.set_title(f'{factor_name}: 分组净值 + 因子 IC')
        ax1.set_ylabel('Cumulative Return')
        ax1.legend(loc='upper left', ncol=2)
        ax1.grid(True, alpha=0.3)

        ax2 = ax1.twinx()
        ax2.bar(daily_rank_ic.index, daily_rank_ic.values, width=2, color='dodgerblue', alpha=0.3, label='Daily Rank IC')
        ax2.set_ylabel('Rank IC')
        ax2.set_ylim(-1, 1)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.fig_path, f'{factor_name}_净值+因子IC.png'), dpi=300)
        plt.close()

    def plot_group_return(self, factor_name, nav_df):
        """
        绘制各分组累积收益图及多空组合曲线
        :param factor_name: 因子名称
        :param nav_df: 分组净值 DataFrame
        """
        plt.figure(figsize=(10, 6))
        
        # 绘制各分组净值
        for col in nav_df.columns:
            plt.plot(nav_df.index, nav_df[col], label=f'{col}')
        
        if len(nav_df.columns) >= 2:
            pass

        cols = nav_df.columns.tolist()
        long_col = cols[-1] 
        short_col = cols[0] 
        
        group_returns = nav_df.pct_change().fillna(0)
        ls_return = group_returns[long_col] - group_returns[short_col]
        ls_nav = (1 + ls_return).cumprod()
        
        plt.plot(ls_nav.index, ls_nav, label='Long-Short', linestyle='--', color='black', linewidth=2)
        
        plt.title(f'{factor_name} - Cumulative Returns by Quantile')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return')
        plt.legend(loc='upper left', ncol=2)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        save_path = os.path.join(self.fig_path, f'{factor_name}_分组累积收益.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"分组累积收益图已保存至: {save_path}")

    def plot_group_bar(self, factor_name, group_median_return):
        """
        分组收益柱状图
        """
        plt.figure(figsize=(10, 6))
        ax = group_median_return.plot(kind='bar', color='dodgerblue', edgecolor='black')
        ax.set_title(f'{factor_name}: 分组收益 (Median)')
        ax.set_ylabel('Return')
        plt.tight_layout()
        plt.savefig(os.path.join(self.fig_path, f'{factor_name}_分组收益.png'), dpi=300)
        plt.close()

    @staticmethod
    def analyze_factor_direction(factors, returns):
        """
        分析因子方向并返回方向调整系数 (1 或 -1)
        :param factors: pd.DataFrame [FDate, SecCode, FValue] 或 MultiIndex
        :param returns: pd.Series [FDate, SecCode] 次日收益
        :return: dict {factor_name: direction}
        """
        # 统一格式为 MultiIndex
        if not isinstance(factors.index, pd.MultiIndex):
            factors = factors.set_index(['FDate', 'SecCode'])
            
        directions = {}
        for col in factors.columns:
            combined = pd.concat([factors[col], returns], axis=1).dropna()
            combined.columns = ['factor', 'ret']
            
            if len(combined) > 100:
                ic = combined.corr(method='spearman').iloc[0, 1]
                directions[col] = 1 if ic >= 0 else -1
            else:
                directions[col] = 1
        return directions

    def preprocess_factors(self, factor_df, method="zscore", winsorize_limit=0.01):
        """
        可选的预处理功能
        """
        df = factor_df.pivot(index='FDate', columns='SecCode', values='FValue')
        
        # 截尾
        lower = df.quantile(winsorize_limit, axis=1)
        upper = df.quantile(1 - winsorize_limit, axis=1)
        clipped = df.clip(lower=lower, upper=upper, axis=0)
        
        if method == "zscore":
            mean = clipped.mean(axis=1)
            std = clipped.std(axis=1).replace(0, np.nan).fillna(1.0)
            processed = clipped.sub(mean, axis=0).div(std, axis=0)
        else:
            processed = clipped
            
        res = processed.stack().reset_index()
        res.columns = ['FDate', 'SecCode', 'FValue']
        return res