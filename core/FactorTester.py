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
    def __init__(self, start_date, end_date, output_dir="results/factors", factor_name="Factor"):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.output_dir = output_dir
        # 移除旧的 fig_path 初始化，改为动态生成
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.interval_mapping = {'D': 1, 'W': 5, 'M': 20}
        self.factors = {}
        self.prices = None

    def load_price_data(self, data_path, codes_list=None):
        """
        从 data_path 加载原始价格数据并进行初步清洗
        """
        print(f"正在从 {data_path} 加载行情数据...")
        try:
            # 预定义需要的列，根据实际文件内容动态调整
            df = pd.read_csv(data_path)
            
            # 检查列是否存在，支持 date/FDate, code/SecCode
            actual_cols = df.columns.tolist()
            date_col = "date" if "date" in actual_cols else "FDate"
            code_col = "code" if "code" in actual_cols else "SecCode"
            close_col = "close" if "close" in actual_cols else ("Close" if "Close" in actual_cols else None)
            
            if not close_col:
                close_matches = [c for c in actual_cols if 'close' in c.lower()]
                close_col = close_matches[0] if close_matches else None
            
            if not date_col or not code_col or not close_col:
                raise ValueError(f"列缺失: date={date_col}, code={code_col}, close={close_col}. 现有列: {actual_cols}")

            df = df.rename(columns={date_col: "date", code_col: "code", close_col: "close"})
            df["date"] = pd.to_datetime(df["date"])
            
            # 时间过滤
            df = df[(df["date"] >= self.start_date) & (df["date"] <= self.end_date)]
            df["code"] = df["code"].astype(str).str.zfill(6)
            
            if codes_list:
                df = df[df["code"].isin(codes_list)]
                
            # 去重
            df = df.drop_duplicates(subset=["date", "code"])
            
            # 优化: 只有在数据量较小时使用 pivot，大数据量使用更高效的方式
            if len(df) > 1000000:
                print("数据量较大，使用 set_index + unstack 进行透视...")
                self.prices = df.set_index(["date", "code"])["close"].unstack()
            else:
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

        # 计算各组净值 (处理因子值缺失导致的断档)
        # 如果某天全市场没有满足条件的成分股，该天的因子组合收益设为0，并在净值计算中通过 ffill 保持前一天水平
        factor_group_eval = factor_group_eval.shift(1).fillna(0)
        nav_df = (1 + factor_group_eval).cumprod().ffill()
        # 对于初始阶段(第一条数据前)进行填充，如果是全量回测起点，默认为1.0
        nav_df = nav_df.fillna(1.0)

        long_nav = nav_df[f'group{groups}']
        drawdown = long_nav / long_nav.cummax() - 1
        max_drawdown = drawdown.min()
        
        if len(nav_df) > 0:
            total_periods = len(nav_df)
            factor_annual_return = long_nav.iloc[-1] ** (1 / (interval * total_periods / 250)) - 1
        else:
            factor_annual_return = 0


        if if_plot:
            # self.plot_group_return_ic(factor_name, nav_df, rank_ic_series)
            self.plot_group_return(factor_name, nav_df)
            
            # 时序 IC + 累计 IC
            self.plot_ic_analysis(factor_name, rank_ic_series, f"{interval_tag} Forward")
            
        eval_metrics = pd.DataFrame({
            'IC': [ic_mean],
            'ICIR': [icir],
            'RankIC': [rank_ic_mean],
            'RankICIR': [rank_icir],
            '多头组最大回撤': [max_drawdown],
            '多头组年化收益': [factor_annual_return]
        }, index=[factor_name])

        return eval_metrics, nav_df, merged_data

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
        save_path = os.path.join(self.output_dir, f'{factor_name}_净值+因子IC.png')
        plt.savefig(save_path, dpi=300)
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
        
        save_path = os.path.join(self.output_dir, f'{factor_name}_分组累积收益.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"分组累积收益图已保存至: {save_path}")

    def calculate_hit_rate_table(self, df, groups=10):
        """
        分析并返回各分组在每日收益率排名前10%（即90%分位数以上）的概率表格
        :param df: DataFrame 包含 ['FRank', 'r', 'FDate']
        :return: pd.DataFrame hit_rate_table
        """
        df = df.copy()
        # 计算每一天收益率的前10%阈值
        df['is_top_return'] = df.groupby('FDate')['r'].transform(lambda x: x >= x.quantile(0.9) if len(x) > 0 else False)
        
        # 分组
        df['group'] = pd.cut(df['FRank'], bins=np.linspace(0, 1, groups + 1), labels=[f'G{i+1}' for i in range(groups)], include_lowest=True)
        
        # 计算每个分组进入收益率前10%的概率
        hit_rate = df.groupby('group', observed=True)['is_top_return'].mean().to_frame(name='Top10%_Hit_Rate')
        return hit_rate

    def plot_group_bar(self, factor_name, group_median_return):
        """
        分组收益柱状图
        """
        plt.figure(figsize=(10, 6))
        ax = group_median_return.plot(kind='bar', color='dodgerblue', edgecolor='black')
        ax.set_title(f'{factor_name}: 分组收益 (Median)')
        ax.set_ylabel('Return')
        plt.tight_layout()
        save_path = os.path.join(self.output_dir, f'{factor_name}_分组收益.png')
        plt.savefig(save_path, dpi=300)
        plt.close()

    def plot_return_boxplot(self, factor_name, df, ret_col, groups=5):
        """
        绘制不同分组下的未来n个交易日的累计收益率箱线图
        :param df: DataFrame 包含 ['FRank', ret_col]
        """
        plt.figure(figsize=(12, 7))
        df = df.copy()
        df['group'] = pd.cut(df['FRank'], bins=np.linspace(0, 1, groups + 1), labels=[f'G{i+1}' for i in range(groups)], include_lowest=True)
        
        # 截尾处理 (1%-99%) 以便观察箱线图主要部分
        lower = df[ret_col].quantile(0.01)
        upper = df[ret_col].quantile(0.99)
        df_plot = df[(df[ret_col] >= lower) & (df[ret_col] <= upper)]
        
        sns.boxplot(x='group', y=ret_col, data=df_plot, palette='viridis')
        plt.title(f'{factor_name} - Return Distribution by Group ({ret_col})')
        plt.xlabel('Factor Group')
        plt.ylabel('Forward Return')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, f'{factor_name}_分组箱线图.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"分组收益箱线图已保存至: {save_path}")

    def plot_return_distribution(self, factor_name, df, ret_col):
        """
        绘制收益率分布 (针对前10%和后10%分位数)
        """
        plt.figure(figsize=(10, 6))
        
        # 进行1%-99%截尾 (Winsorize)
        lower_bound = df[ret_col].quantile(0.01)
        upper_bound = df[ret_col].quantile(0.99)
        
        def trim(x):
            return x[(x >= lower_bound) & (x <= upper_bound)]

        all_data_trimmed = trim(df[ret_col].dropna())
        top_10 = df[df["FRank"] >= 0.9][ret_col].dropna()
        bottom_10 = df[df["FRank"] <= 0.1][ret_col].dropna()
        
        top_10_trimmed = trim(top_10)
        bottom_10_trimmed = trim(bottom_10)

        sns.kdeplot(all_data_trimmed, label="All Data", color="gray", linestyle="--")
        if not top_10_trimmed.empty:
            sns.kdeplot(top_10_trimmed, label=f"Top 10% {factor_name}", color="red", lw=2)
        if not bottom_10_trimmed.empty:
            sns.kdeplot(bottom_10_trimmed, label=f"Bottom 10% {factor_name}", color="green", lw=2)

        plt.title(f"Return Distribution: {factor_name}")
        plt.xlabel("Forward Return")
        plt.ylabel("Density")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        save_path = os.path.join(self.output_dir, f'{factor_name}_收益分布.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"收益分布图已保存至: {save_path}")

    def plot_ic_analysis(self, factor_name, daily_ic, ret_col):
        """
        绘制时序 IC 和累计 IC
        """
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 左轴：累计 IC
        cum_ic = daily_ic.cumsum()
        ax1.plot(cum_ic.index, cum_ic, color="tab:blue", label="Cumulative IC")
        ax1.set_ylabel("Cumulative IC", color="tab:blue")
        ax1.tick_params(axis='y', labelcolor="tab:blue")
        
        # 右轴：20日滚动 IC
        ax2 = ax1.twinx()
        rolling_ic = daily_ic.rolling(20).mean()
        ax2.bar(daily_ic.index, daily_ic, color="tab:gray", alpha=0.5, label="Single-Period IC")
        ax2.plot(rolling_ic.index, rolling_ic, color="tab:red", alpha=0.8, label="20-Period Rolling Mean")
        ax2.set_ylabel("Single-Period/20-Period Rolling IC", color="tab:red")
        ax2.tick_params(axis='y', labelcolor="tab:red")
        ax2.axhline(0, color='black', linestyle='--', linewidth=0.8)
        
        plt.title(f"Factor IC Analysis: {factor_name}")
        fig.tight_layout()
        
        save_path = os.path.join(self.output_dir, f'{factor_name}_IC分析.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"IC分析图已保存至: {save_path}")

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