import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from core.Logger import logger
from core.NavAnalyzer import Visualizer, NAVAnalyzer
from core.NumericalOperators import cs_rank

warnings.filterwarnings('ignore')

# 设置绘图风格 (参考 FactorTester)
plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class SparseSignalTester:
    """
    稀疏信号测试类：专门用于基于非连续时间点的稀疏信号（因子）进行截面分组回测。
    主要流程：
    1. 接收稀疏信号 DataFrame (Index: Date, Columns: Assets)，其中非空/非零值视为触发点，且该值即为因子值。
    2. 计算触发日后 T+1 到 T+N 的累积收益率。
    3. 对所有触发点进行聚合统计（均值、胜率、分组单调性）。
    """
    def __init__(self, signal_series, price_df, benchmark_series=None, period=20, n_groups=5, output_dir="results/sparse_signal", data_folder="sparse_signal"):
        """
        :param signal_series: pd.Series or pd.DataFrame, 稀疏信号序列。
                             若是 DataFrame，且某一格不为 NaN/0，则视为该标在该日触发。
                             该值即直接作为回测的分组因子值。
        :param price_df: pd.DataFrame, 价格矩阵
        :param benchmark_series: pd.Series, 基准价格序列
        :param period: int, 持有期
        :param n_groups: int, 分组数
        :param output_dir: str, 输出目录
        :param data_folder: str, 存放外部稀疏信号的数据文件夹 (当 signal_series 仅包含名称时使用)
        """
        self.signal_series = signal_series
        self.price_df = price_df
        self.benchmark_series = benchmark_series
        self.period = period
        self.n_groups = n_groups
        self.output_dir = output_dir
        self.data_folder = data_folder
        self.factor_cache = {} # 缓存读取的信号数据 (signal_name -> df)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 缓存信号分组结果，用于连续净值计算
        self._signal_groups_cache = {}

        # 确保日期索引对齐
        common_dates = self.price_df.index
        if isinstance(self.signal_series, (pd.Series, pd.DataFrame)):
            common_dates = common_dates.intersection(self.signal_series.index)
        
        if self.benchmark_series is not None:
            common_dates = common_dates.intersection(self.benchmark_series.index)
            self.benchmark_series = self.benchmark_series.loc[common_dates]

        self.price_df = self.price_df.loc[common_dates]
        if isinstance(self.signal_series, (pd.Series, pd.DataFrame)):
            self.signal_series = self.signal_series.loc[common_dates]
        
        # 内部缓存用于性能统计
        self.performance_stats = {}
        self._trigger_metrics = [] # 记录每个触发点的 IC 和 超额收益
        self._group_assignment_log = [] # 记录触发点的截面分配明细

        # 提取触发日期列表：只要信号矩阵中有非空的值，就视为该日有触发
        if isinstance(self.signal_series, pd.DataFrame):
            self.combined_signal = self.signal_series.notna().any(axis=1).astype(int)
            # 记录用于分组的最终因子矩阵
            self.final_factor_df = self.signal_series
        else:
            self.combined_signal = self.signal_series.notna().astype(int)
            self.final_factor_df = self.signal_series.to_frame()

        self.trigger_dates = self.combined_signal[self.combined_signal == 1].index.tolist()        

    def run_timing_analysis(self, period=None, benchmark_series=None):
        """
        独立的公有分析方法：验证信号触发时点的择时有效性。
        对比信号点的平均收益与全样本基准分布。
        :param period: 持有期，默认为 self.period
        :param benchmark_series: 基准价格序列，默认为 self.benchmark_series
        :return: dict, 择时统计指标
        """
        from scipy import stats as scipy_stats
        
        test_period = period if period is not None else self.period
        test_bench = benchmark_series if benchmark_series is not None else self.benchmark_series
        
        if test_bench is None:
            logger.error("No benchmark series provided for timing analysis.")
            return None

        # 1. 计算全样本收益
        bench_rets_all = test_bench.shift(-test_period) / test_bench - 1
        bench_rets_all = bench_rets_all.dropna()
        
        # 2. 计算信号触发点的收益
        trigger_bench_rets = test_bench.shift(-test_period) / test_bench - 1
        sample_rets = trigger_bench_rets.loc[self.trigger_dates].dropna()
        
        if sample_rets.empty:
            logger.warning("No valid sample returns found for timing analysis.")
            return None

        # 3. 计算统计指标
        sample_mean = sample_rets.mean()
        base_mean = bench_rets_all.mean()
        base_std = bench_rets_all.std()
        
        # Quantile Rank: 样本均值在总体分布中的位置
        quantile_rank = (bench_rets_all < sample_mean).mean()
        
        # T-test (单样本 T 检验：样本均值 vs 总体均值)
        t_stat, p_value = scipy_stats.ttest_1samp(sample_rets, base_mean)
        
        timing_stats = {
            'period': test_period,
            'sample_count': len(sample_rets),
            'sample_mean': sample_mean,
            'base_mean': base_mean,
            'base_std': base_std,
            'quantile_rank': quantile_rank,
            't_stat': t_stat,
            'p_value': p_value
        }
        
        # 缓存结果供绘图使用
        self._last_timing_stats = {
            'stats': timing_stats,
            'sample_rets': sample_rets,
            'base_dist': bench_rets_all
        }
        
        # 打印简要报告
        print("\n" + "-"*40)
        print(f" TIMING EFFECTIVENESS REPORT (T+{test_period}) ")
        print("-" * 40)
        print(f"Signal Triggers: {timing_stats['sample_count']}")
        print(f"Sample Avg Ret:  {sample_mean*100:.2f}%")
        print(f"Base Avg Ret:    {base_mean*100:.2f}%")
        print(f"Quantile Rank:   {quantile_rank*100:.2f}%")
        print(f"P-Value:         {p_value:.4f}")
        print("-" * 40 + "\n")
        
        return timing_stats

    def plot_timing_distribution(self, title="信号时点收益分布 (择时有效性)"):
        """
        绘制信号收益分布与基准背景分布的对比图
        """
        if not hasattr(self, '_last_timing_stats'):
            logger.warning("No timing stats found. Run run_timing_analysis first.")
            return

        import seaborn as sns
        
        data = self._last_timing_stats
        stats_val = data['stats']
        sample_rets = data['sample_rets']
        base_dist = data['base_dist']
        
        plt.figure(figsize=(10, 6))
        
        # 统一直方图的 bins，确保分割数量一致且对齐
        # 计算全局的 min/max 以确定统一的 bins 范围
        combined_data = np.concatenate([base_dist.values, sample_rets.values])
        bins = np.linspace(np.min(combined_data), np.max(combined_data), 50)
        
        # 绘制背景分布 (KDE + Hist)
        sns.histplot(base_dist, bins=bins, kde=True, color='gray', alpha=0.3, label='全样本基准分布', stat="density")
        
        # 绘制信号点分布
        sns.histplot(sample_rets, bins=bins, kde=True, color='red', alpha=0.5, label='信号触发时点收益', stat="density")
        
        # 标注均值线
        plt.axvline(x=stats_val['base_mean'], color='black', linestyle='--', label=f'基准均值 ({stats_val["base_mean"]*100:.2f}%)')
        plt.axvline(x=stats_val['sample_mean'], color='red', linestyle='-', linewidth=2, label=f'信号均值 ({stats_val["sample_mean"]*100:.2f}%)')
        
        plt.title(f"{title}\n(分位数分值: {stats_val['quantile_rank']*100:.2f}%, P-Value: {stats_val['p_value']:.4f})")
        plt.xlabel("持有期收益率")
        plt.ylabel("密度")
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        
        save_path = os.path.join(self.output_dir, "timing_effectiveness_dist.png")
        plt.savefig(save_path)
        plt.close()

    def run_backtest(self):
        """
        主回测入口，遍历所有触发日期并聚合结果
        """
        all_results = []
        self._trigger_metrics = [] # 重置缓存
        self._group_assignment_log = [] # 重置明细缓存
        
        # 预计算 benchmark 收益率
        bench_ret_series = None
        if self.benchmark_series is not None:
            bench_ret_series = self.benchmark_series.pct_change()

        for date in self.trigger_dates:
            # 1. 提取因子截面并分组
            # 注意：此处 extract_cross_section 需要使用融合后的因子
            groups = self._extract_cross_section(date)
            if groups is None:
                continue
            
            # 缓存分组结果供连续净值使用
            self._signal_groups_cache[date] = groups

            # 2. 计算各组收益率 (T+1 到 T+period)
            group_rets = self.calculate_group_returns(date, groups)
            if group_rets.empty:
                continue
            
            # 记录触发日期
            group_rets.name = date
            all_results.append(group_rets)

            # 3. 计算 IC 和 超额收益 (存入缓存用于性能统计)
            self._cache_performance_metrics(date, bench_ret_series)
        
        if not all_results:
            logger.warning("No valid results collected during backtest.")
            return pd.DataFrame()
            
        # 结果汇总: Rows 为触发日期, Columns 为 Group ID
        final_df = pd.concat(all_results, axis=1).T
        
        # 4. 计算最终性能指标
        self.calculate_performance_stats(final_df)

        # 5. 自动导出明细 (Task 集成)
        self.export_group_assignment_details()
        
        return final_df

    def _cache_performance_metrics(self, date, bench_ret_series):
        """
        内部方法：计算并缓存单个触发点的 IC 和 超额收益
        """
        all_dates = self.price_df.index
        curr_idx = all_dates.get_loc(date)
        
        if curr_idx + self.period >= len(all_dates):
            return

        # 计算 T+1 到 T+period 的标的收益率，相对于 T 日的收盘价
        p_t = self.price_df.iloc[curr_idx]
        p_future = self.price_df.iloc[curr_idx + self.period]
        period_rets = p_future / p_t - 1
        
        # 确保收益率和基准均对齐
        bench_excess_base = 0.0
        if bench_ret_series is not None:
            # Benchmark 在 T 日后的累积收益
            b_t = self.benchmark_series.iloc[curr_idx]
            b_future = self.benchmark_series.iloc[curr_idx + self.period]
            bench_excess_base = b_future / b_t - 1
        else:
            bench_excess_base = period_rets.mean()

        # 使用传入的因子截面计算 IC
        fused_section = self.final_factor_df.loc[date].reindex(period_rets.index).dropna()
        period_rets_fused = period_rets.loc[fused_section.index]

        if fused_section.empty or len(fused_section) < 2:
            return

        # 计算 IC / Rank IC
        ic = fused_section.corr(period_rets_fused)
        rank_ic = fused_section.rank().corr(period_rets_fused.rank())

        self._trigger_metrics.append({
            'date': date,
            'ic': ic,
            'rank_ic': rank_ic,
            'bench_ret': bench_excess_base
        })

    def calculate_performance_stats(self, group_results):
        """
        计算综合性能指标：IC/IR, 胜率, 多空超额收益, Calmar, 盈亏比等
        """
        if not self._trigger_metrics or group_results.empty:
            return

        metrics_df = pd.DataFrame(self._trigger_metrics).set_index('date')
        
        # 确保日期对齐
        common_dates = metrics_df.index.intersection(group_results.index)
        metrics_df = metrics_df.loc[common_dates]
        group_results = group_results.loc[common_dates]

        # 1. IC 相关统计
        ic_series = metrics_df['ic'].dropna()
        rank_ic_series = metrics_df['rank_ic'].dropna()
        
        ic_mean = ic_series.mean()
        rank_ic_mean = rank_ic_series.mean()
        ic_std = ic_series.std()
        
        icir = ic_mean / ic_std if ic_std > 0 else np.nan
        ic_win_rate = (rank_ic_series > 0).mean()

        # 2. 收益统计 (基于触发点)
        long_col = f'group_{self.n_groups}'
        short_col = 'group_1'
        
        long_returns = group_results[long_col]
        short_returns = group_results[short_col]
        bench_returns = metrics_df['bench_ret']

        # 触发点层面的超额
        long_excess_series = long_returns - bench_returns
        short_excess_series = short_returns - bench_returns
        ls_excess_series = long_returns - short_returns
        
        long_excess = long_excess_series.mean()
        short_excess = short_excess_series.mean()

        # 计算单次持仓/信号胜率与盈亏比 (针对多空组合收益)
        ls_win_rate = (ls_excess_series > 0).mean()
        ls_profit_avg = ls_excess_series[ls_excess_series > 0].mean() if (ls_excess_series > 0).any() else 0
        ls_loss_avg = abs(ls_excess_series[ls_excess_series < 0].mean()) if (ls_excess_series < 0).any() else 1e-6
        ls_profit_loss_ratio = ls_profit_avg / ls_loss_avg

        # 3. 年度 IC 统计
        metrics_df['year'] = metrics_df.index.year
        yearly_ic = metrics_df.groupby('year')['rank_ic'].mean()

        # 4. 计算连续净值指标 (Spliced 逻辑)
        # 获取多空组合 (LS) 净值
        ls_equity = self._calculate_continuous_strategy_returns()
        ls_analyzer = NAVAnalyzer(ls_equity.pct_change().dropna())
        ls_perf = ls_analyzer.compute_performance()

        # 计算累积超额收益 (相对于基准)
        cumulative_excess = 0.0
        if self.benchmark_series is not None:
            ls_returns = ls_equity.pct_change().dropna()
            bench_returns = self.benchmark_series.pct_change().fillna(0)
            excess_nav = (1 + ls_returns).cumprod() / (1 + bench_returns).cumprod()
            cumulative_excess = excess_nav.iloc[-1] - 1
        else:
            cumulative_excess = ls_equity.iloc[-1] - 1
        
        # 获取纯多头净值
        all_dates = self.price_df.index
        long_equity = {all_dates[0]: 1.0}
        curr_l = 1.0
        
        sorted_trig = sorted(self.trigger_dates)
        for i, sd in enumerate(sorted_trig):
            idx = all_dates.get_loc(sd)
            e_idx = min(idx + self.period, len(all_dates)-1)
            if i+1 < len(sorted_trig):
                e_idx = min(e_idx, all_dates.get_loc(sorted_trig[i+1]))
            
            groups = self._signal_groups_cache.get(sd)
            if groups:
                l_assets = groups.get(self.n_groups, [])
                if l_assets:
                    l_ret = self.price_df.iloc[e_idx].reindex(l_assets).div(self.price_df.iloc[idx].reindex(l_assets)).mean() - 1
                    curr_l *= (1 + (0 if pd.isna(l_ret) else l_ret))
                    long_equity[all_dates[e_idx]] = curr_l
        
        long_equity_ser = pd.Series(long_equity).sort_index()
        long_analyzer = NAVAnalyzer(long_equity_ser.pct_change().dropna())
        long_perf = long_analyzer.compute_performance()

        # 5. 汇总指标字典
        self.performance_stats = {
            'IC Mean': ic_mean,
            'Rank IC Mean': rank_ic_mean,
            'ICIR': icir,
            'IC Winning Rate': ic_win_rate,
            'Long Excess (vs Bench)': long_excess,
            'Short Excess (vs Bench)': short_excess,
            'Total Triggers': len(common_dates),
            'LS_Win_Rate': ls_win_rate,
            'LS_Profit_Loss_Ratio': ls_profit_loss_ratio,
            'Cumulative_Excess': cumulative_excess,
            'Excess_Sharpe': ls_perf['sharpe_ratio'],
            'Long_Ann_Ret': long_perf['annual_return'] / 100.0,
            'Long_Max_DD': long_perf['max_drawdown'] / 100.0,
            'Long_Sharpe': long_perf['sharpe_ratio'],
            'LS_Ann_Ret': ls_perf['annual_return'] / 100.0,
            'LS_Max_DD': ls_perf['max_drawdown'] / 100.0,
            'LS_Sharpe': ls_perf['sharpe_ratio'],
            'Long_Calmar': (long_perf['annual_return'] / abs(long_perf['max_drawdown'])) if long_perf['max_drawdown'] != 0 else 0,
            'LS_Calmar': (ls_perf['annual_return'] / abs(ls_perf['max_drawdown'])) if ls_perf['max_drawdown'] != 0 else 0,
            'Yearly_Rank_IC': yearly_ic.to_dict()
        }

    def print_performance_report(self):
        """
        打印并导出详细的绩效评价统计报表
        1. performance_summary_report.csv: 仅保留 IC 相关内容
        2. nav_summary.csv: 包含多头、多空的所有绩效指标 (由 strategy_overview 改名并整合)
        """
        if not self.performance_stats:
            logger.warning("Performance stats not calculated. Run run_backtest first.")
            return

        stats = self.performance_stats
        
        # 1. 生成 performance_summary_report (仅保留 IC 相关内容)
        summary_rows = [
            ['Total Triggers', f"{int(stats['Total Triggers'])}"],
            ['IC Mean', f"{stats['IC Mean']:.4f}"],
            ['Rank IC Mean', f"{stats['Rank IC Mean']:.4f}"],
            ['ICIR', f"{stats['ICIR']:.4f}"],
            ['IC Winning Rate', f"{stats['IC Winning Rate']*100:.2f}%"]
        ]
                 
        summary_df = pd.DataFrame(summary_rows, columns=['Metric', 'Value'])
        summary_path = os.path.join(self.output_dir, "performance_summary_report.csv")
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')

        # 2. 生成 nav_summary (包含多头、多空的所有绩效指标)
        # 转为纵向表格 (Metric, Value)
        nav_summary_rows = [
            ['Long_Annual_Return', f"{stats['Long_Ann_Ret']*100:.2f}%"],
            ['Long_Max_Drawdown', f"{stats['Long_Max_DD']*100:.2f}%"],
            ['Long_Sharpe', f"{stats['Long_Sharpe']:.2f}"],
            ['Long_Calmar', f"{stats['Long_Calmar']:.2f}"],
            ['LS_Annual_Return', f"{stats['LS_Ann_Ret']*100:.2f}%"],
            ['LS_Max_Drawdown', f"{stats['LS_Max_DD']*100:.2f}%"],
            ['LS_Sharpe', f"{stats['LS_Sharpe']:.2f}"],
            ['LS_Calmar', f"{stats['LS_Calmar']:.2f}"],
            ['Cumulative_Excess', f"{stats['Cumulative_Excess']*100:.2f}%"],
            ['Excess_Sharpe', f"{stats['Excess_Sharpe']:.4f}"],
            ['LS_Win_Rate_Signal', f"{stats['LS_Win_Rate']*100:.2f}%"],
            ['LS_Profit_Loss_Ratio', f"{stats['LS_Profit_Loss_Ratio']:.2f}"]
        ]
        nav_summary_df = pd.DataFrame(nav_summary_rows, columns=['Metric', 'Value'])
        nav_summary_path = os.path.join(self.output_dir, "nav_summary.csv")
        nav_summary_df.to_csv(nav_summary_path, index=False, encoding='utf-8-sig')

        # 3. 屏幕输出 (保持简洁)
        print("\n" + "="*60)
        print(f" 绩效评价统计报表 (持有期: T+{self.period}) ")
        print("-" * 60)
        print(f"{'指标名称':<25} | {'数值':<20}")
        print("-" * 60)
        # 屏幕输出仅显示 IC 总计和核心多空结果
        display_rows = summary_rows[:5] + [
            ['Long Annual Return', f"{stats['Long_Ann_Ret']*100:.2f}%"],
            ['LS Annual Return', f"{stats['LS_Ann_Ret']*100:.2f}%"],
            ['Cumulative Excess', f"{stats['Cumulative_Excess']*100:.2f}%"],
            ['Excess Sharpe', f"{stats['Excess_Sharpe']:.4f}"]
        ]
        for name, val in display_rows:
            print(f"{name:<25} | {val:<20}")
        print("="*60 + "\n")
        
        logger.info(f"IC performance report saved to {summary_path}")
        logger.info(f"NAV summary report saved to {nav_summary_path}")

    def _extract_cross_section(self, date):
        """
        提取指定日期的因子截面，并根据分位数分组
        :param date: 触发日期
        :return: dict, {group_id: [stock_list]}
        """
        # 使用最终因子矩阵进行截面分组
        if date not in self.final_factor_df.index:
            return None
            
        factor_section = self.final_factor_df.loc[date].dropna()
        if factor_section.empty or len(factor_section) < self.n_groups:
            return None

        f_rank = cs_rank(factor_section, pct=True)
        
        groups = {}
        for i in range(self.n_groups):
            lower = i / self.n_groups
            upper = (i + 1) / self.n_groups
            
            mask = (f_rank >= lower) & (f_rank <= upper)
            groups[i + 1] = f_rank[mask].index.tolist()
            
        return groups


    def calculate_group_returns(self, date, groups):
        """
        计算指定触发日后 T+1 到 T+period 的各组累积超额收益率
        并在内部记录每个资产的分组分配明细
        :return: pd.Series, Index 为 Group ID, Value 为该组平均累积超额收益
        """
        all_dates = self.price_df.index
        curr_idx = all_dates.get_loc(date)
        
        if curr_idx + self.period >= len(all_dates):
            return pd.Series()
            
        p_t = self.price_df.iloc[curr_idx]
        p_future = self.price_df.iloc[curr_idx + self.period]
        period_rets = p_future / p_t - 1

        bench_ret = 0.0
        if self.benchmark_series is not None:
            b_t = self.benchmark_series.iloc[curr_idx]
            b_future = self.benchmark_series.iloc[curr_idx + self.period]
            bench_ret = b_future / b_t - 1
       
        # bench_ret = period_rets.mean()
        
        period_excess_rets = period_rets - bench_ret
        
        # 提取因子值以供记录
        factor_section = self.final_factor_df.loc[date]
        
        group_means = {}
        group_excess_means = {}

        if not hasattr(self, '_group_excess_results_cache'):
            self._group_excess_results_cache = []

        for g_id, codes in groups.items():
            valid_codes = [c for c in codes if c in period_rets.index]
            if not valid_codes:
                group_means[f'group_{g_id}'] = np.nan
                group_excess_means[f'group_{g_id}'] = np.nan
                continue
            
            # 记录组内明细
            for code in valid_codes:
                self._group_assignment_log.append({
                    'date': date,
                    'asset_code': code,
                    'factor_value': factor_section.get(code, np.nan),
                    'group_id': g_id,
                    'period_return': period_rets.get(code, np.nan),
                    'excess_return': period_excess_rets.get(code, np.nan)
                })
                
            group_means[f'group_{g_id}'] = period_rets.loc[valid_codes].mean()
            group_excess_means[f'group_{g_id}'] = period_excess_rets.loc[valid_codes].mean()
            
        self._group_excess_results_cache.append({'date': date, **group_excess_means})
        return pd.Series(group_means)

    def export_group_assignment_details(self, filename="group_assignment_details.csv"):
        """
        导出所有触发点的截面分配及超额收益明细
        """
        if not self._group_assignment_log:
            logger.warning("No group assignment data to export.")
            return

        df_details = pd.DataFrame(self._group_assignment_log).sort_values(by=['date', 'factor_value'], ascending=[False, False])
        save_path = os.path.join(self.output_dir, filename)
            
        df_details.to_csv(save_path, index=False, encoding='utf-8-sig')

    def plot_signals(self, benchmark_series, asset_name="基准指数", title="信号触发位置"):
        """
        可视化信号触发位置
        :param benchmark_series: pd.Series, 用于背景显示的指数序列 (如基准指数)
        :param asset_name: str, 资产名称
        :param title: str, 图表标题
        """
        plt.figure(figsize=(12, 6))
        plt.plot(benchmark_series, label=asset_name, color='#004488', alpha=0.6)
        
        # 在触发日期画竖线
        for i, d in enumerate(self.trigger_dates):
            if d in benchmark_series.index:
                plt.axvline(x=d, color="#D80000", linestyle='--', alpha=0.3)
            
        plt.title(title)
        plt.xlabel("日期")
        plt.legend()
        plt.grid(False)
        
        save_path = os.path.join(self.output_dir, "signal_triggers.png")
        plt.savefig(save_path)
        logger.info(f"Signal trigger plot saved to: {save_path}")
        
    def plot_annual_frequency(self, title="年度信号触发频率"):
        """
        统计每年信号触发的次数并绘制柱状图
        """
        if not self.trigger_dates:
            logger.warning("No trigger dates found to plot annual frequency.")
            return

        # 获取数据全时间段的年份范围
        all_years = self.price_df.index.year.unique().sort_values()
        
        # 统计触发年份
        trigger_dates_dt = pd.to_datetime(self.trigger_dates)
        trigger_years = trigger_dates_dt.year
        actual_counts = pd.Series(trigger_years).value_counts()
        
        # 构建完整的年份序列，缺失年份填充为 0
        yearly_counts = pd.Series(0, index=all_years).add(actual_counts, fill_value=0).astype(int)

        plt.figure(figsize=(12, 6))
        # 使用原生 matplotlib 绘制以更好控制 x 轴
        x = range(len(yearly_counts))
        plt.bar(x, yearly_counts.values, color="#004488")
        
        # 添加数值标签
        for i, count in enumerate(yearly_counts):
            if count > 0:
                plt.text(i, count + 0.1, str(count), ha='center', fontweight='bold', color='darkblue')

        plt.title(title)
        plt.xlabel("日期")
        plt.ylabel("触发次数")
        plt.xticks(x, yearly_counts.index, rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        save_path = os.path.join(self.output_dir, "annual_signal_frequency.png")
        plt.savefig(save_path)
        logger.info(f"Annual signal frequency plot saved to {save_path}")
        
    def export_trigger_log(self, filename="signal_trigger_dates.csv"):
        """
        导出所有信号触发的时间到表格
        """
        if not self.trigger_dates:
            logger.warning("No trigger dates found to export trigger log.")
            return

        df = pd.DataFrame({"trigger_date": self.trigger_dates})
        save_path = os.path.join(self.output_dir, filename)
        df.to_csv(save_path, index=False)
        logger.info(f"Signal trigger log exported to {save_path}")

    def plot_group_returns(self, group_results, title="分组平均超额收益"):
        """
        可视化
        :param group_results: pd.DataFrame, 回测产出的原始分组收益结果 (绝对收益)
        :param title: str, 图表标题
        """
        if group_results.empty:
            logger.warning("No data to plot for group returns.")
            return
            
        # 1. 绘制分组平均超额柱状图
        self.plot_excess_return_bar(title=title)
        
        # 2. 绘制离散累乘净值曲线
        self.plot_discrete_equity_curve(group_results, title="信号触发点累乘净值")

        # 3. 绘制信号拼接净值曲线 (去掉空仓时间)
        self.plot_spliced_equity_curve(title="多空组合拼接净值曲线")
        
        # 4. 绘制多头、空头、多空组合曲线
        self.plot_l_s_ls_combined_curve(title="多头/空头/对冲组合表现对比")
        
        # 5. 绘制全时段连续净值曲线 (含空仓横盘)
        self.plot_full_timeline_equity_curve(group_results, title="全时段多空组合净值")

    def plot_excess_return_bar(self, title="分组平均超额表现"):
        """
        绘制各分组相对于均值或基准的超额收益柱状图
        """
        if not hasattr(self, '_group_excess_results_cache') or not self._group_excess_results_cache:
            logger.warning("No excess return cache found to plot bar chart.")
            return

        excess_df = pd.DataFrame(self._group_excess_results_cache).set_index('date')
        avg_rets = excess_df.mean() * 100
        
        plt.figure(figsize=(10, 6))
        # 统一颜色：蓝色
        colors = ['#004488'] * len(avg_rets)
        bars = plt.bar(avg_rets.index, avg_rets.values, color=colors)
        
        # 添加数值标签
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval * 1.05, 
                     f"{yval:.2f}%", ha='center', va='bottom' if yval >= 0 else 'top', fontweight='bold')
            
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        y_min, y_max = plt.ylim()
        plt.ylim(y_min * 1.25 if y_min < 0 else y_min, y_max * 1.25 if y_max > 0 else y_max)
        
        plt.title(title)
        plt.ylabel("平均累积超额收益 (%)")
        plt.xlabel("分组")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        save_path = os.path.join(self.output_dir, "group_excess_return_bar.png")
        plt.savefig(save_path)
        plt.close()

    def _calculate_continuous_strategy_returns(self):
        """
        计算连续日度真实时间轴的策略收益率
        不持仓的时候收益率为0，净值曲线为横线
        """
        all_dates = self.price_df.index
        # 初始化每日收益率为 0
        daily_returns = pd.Series(0.0, index=all_dates)
        
        # 1. 识别持仓区间 (多空组合: Group N - Group 1)
        sorted_trig = sorted(self.trigger_dates)
        for i, sd in enumerate(sorted_trig):
            start_idx = all_dates.get_loc(sd)
            # 默认结束位置或下一个信号开始位置
            if i + 1 < len(sorted_trig):
                next_sd = sorted_trig[i + 1]
                next_start_idx = all_dates.get_loc(next_sd)
                end_idx = min(start_idx + self.period, next_start_idx)
            else:
                end_idx = min(start_idx + self.period, len(all_dates) - 1)
            
            if start_idx >= end_idx:
                continue
                
            groups = self._signal_groups_cache.get(sd)
            if not groups:
                continue
            
            l_assets = [c for c in groups.get(self.n_groups, []) if c in self.price_df.columns]
            s_assets = [c for c in groups.get(1, []) if c in self.price_df.columns]
            
            if not l_assets or not s_assets:
                continue
            
            # 填补区间内的每日收益率 (Close_t / Close_{t-1} - 1)
            # 修改为：持有到 end_date，仅在 end_date 产生该时段的累积收益
            d1 = all_dates[start_idx]
            d2 = all_dates[end_idx]
            
            # 计算全时段多头绝对收益
            l_ret = (self.price_df.loc[d2, l_assets] / self.price_df.loc[d1, l_assets] - 1).mean()
            # 计算全时段空头绝对收益
            s_ret = (self.price_df.loc[d2, s_assets] / self.price_df.loc[d1, s_assets] - 1).mean()
            
            # 多空总收益 = L - S
            total_ls_ret = (0 if pd.isna(l_ret) else l_ret) - (0 if pd.isna(s_ret) else s_ret)
            
            # 将总收益均匀分配到持仓期间的每一天，使得净值曲线呈现斜线
            num_days = end_idx - start_idx
            if num_days > 0:
                # 使用复利分配：(1 + daily_ret)^num_days = 1 + total_ls_ret
                daily_ls_ret = (1 + total_ls_ret)**(1/num_days) - 1
                for j in range(start_idx + 1, end_idx + 1):
                    daily_returns.iloc[j] = daily_ls_ret
        
        # 2. 计算累计净值
        equity_series = (1 + daily_returns).cumprod()
        return equity_series

    def _calculate_continuous_strategy_returns_spliced(self):
        """
        计算拼接后的策略收益率 (多空组合: Group N - Group 1)
        """
        all_dates = self.price_df.index
        spliced_equity = {all_dates[0]: 1.0}
        curr_val = 1.0
        
        sorted_trig = sorted(self.trigger_dates)
        for i, sd in enumerate(sorted_trig):
            start_idx = all_dates.get_loc(sd)
            if i + 1 < len(sorted_trig):
                next_sd = sorted_trig[i + 1]
                end_idx = min(start_idx + self.period, all_dates.get_loc(next_sd))
            else:
                end_idx = min(start_idx + self.period, len(all_dates) - 1)
            
            if start_idx >= end_idx: continue
                
            groups = self._signal_groups_cache.get(sd)
            if not groups: continue
            
            l_assets = groups.get(self.n_groups, [])
            s_assets = groups.get(1, [])
            if not l_assets or not s_assets: continue
            
            # 同样采用 (P_end / P_start - 1).mean() 进行等权绝对收益计算
            l_ret = (self.price_df.iloc[end_idx].reindex(l_assets) / self.price_df.iloc[start_idx].reindex(l_assets) - 1).mean()
            s_ret = (self.price_df.iloc[end_idx].reindex(s_assets) / self.price_df.iloc[start_idx].reindex(s_assets) - 1).mean()
            
            l_ret = 0 if pd.isna(l_ret) else l_ret
            s_ret = 0 if pd.isna(s_ret) else s_ret
            
            # 使用多头减空头收益进行拼接
            period_ls_ret = l_ret - s_ret
            curr_val *= (1 + period_ls_ret)
            spliced_equity[all_dates[end_idx]] = curr_val
            
        return pd.Series(spliced_equity).sort_index()

    def plot_discrete_equity_curve(self, group_results, title="信号触发点累乘净值"):
        """
        绘制离散点累乘净值曲线 (仅包含触发点产生的收益)
        """
        if group_results.empty or group_results.shape[1] < 2:
            logger.warning("Insufficient data for discrete equity curve.")
            return

        plt.figure(figsize=(12, 6))
        ls_rets = group_results.iloc[:, -1] - group_results.iloc[:, 0]
        equity_curve = (1 + ls_rets).cumprod()
        x_labels = [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d) for d in equity_curve.index]
        
        # 稀疏信号年化收益应根据实际持有时长计算
        if len(equity_curve) > 1:
            total_days = (equity_curve.index[-1] - equity_curve.index[0]).days
            years = total_days / 252
            ann_ret = (equity_curve.iloc[-1] ** (1 / years) - 1) * 100 if years > 0 else 0
        else:
            ann_ret = 0
            
        ls_analyzer = NAVAnalyzer(ls_rets)
        perf = ls_analyzer.compute_performance()
        label_text = f"多空净值 (年化: {ann_ret:.1f}%, 回撤: {perf['max_drawdown']:.1f}%)"
        
        plt.plot(x_labels, equity_curve.values, marker='o', color="#004488", linewidth=2, markersize=6, label=label_text)
        if len(x_labels) > 20:
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(15))
        plt.xlabel("日期 (持有到期不提前调仓)")
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
        plt.title(title)
        plt.ylabel("累积超额收益 (净值)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, "equity_curve_per_signal_cumprod.png")
        plt.savefig(save_path)
        logger.info(f"Discrete equity curve saved to: {save_path}")
        plt.close()

    def plot_spliced_equity_curve(self, title="多空组合拼接净值曲线 (Spliced)"):
        """
        将信号活跃期首尾相连进行拼接的净值曲线
        """
        spliced_curve = self._calculate_continuous_strategy_returns_spliced()
        if spliced_curve.empty:
            logger.warning("No data to plot for spliced equity curve.")
            return

        plt.figure(figsize=(12, 6))
        x_labels = [d.strftime('%Y-%m-%d') for d in spliced_curve.index]
        
        # 拼接净值年化收益应根据实际持有时长计算
        if len(spliced_curve) > 1:
            total_days = (spliced_curve.index[-1] - spliced_curve.index[0]).days
            years = total_days / 365.25
            ann_ret_spliced = (spliced_curve.iloc[-1] ** (1 / years) - 1) * 100 if years > 0 else 0
        else:
            ann_ret_spliced = 0

        spliced_analyzer = NAVAnalyzer(spliced_curve.pct_change().dropna())
        perf_spliced = spliced_analyzer.compute_performance()
        label_text = f"拼接净值 (年化: {ann_ret_spliced:.1f}%, 回撤: {perf_spliced['max_drawdown']:.1f}%)"
        
        plt.plot(x_labels, spliced_curve.values, color="#004488", linewidth=1.5, label=label_text)
        if len(x_labels) > 20:
            plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))
        
        plt.xlabel("日期 (信号覆盖时期拼接)")
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, "equity_curve_time_spliced.png")
        plt.savefig(save_path)
        logger.info(f"Spliced equity curve saved to: {save_path}")
        plt.close()

    def plot_l_s_ls_combined_curve(self, title="多头/空头/对冲组合表现对比"):
        """
        绘制多头、空头、多空对冲三位一体的净值曲线 (Time-Spliced 模式)
        """
        all_dates = self.price_df.index
        if not self.trigger_dates:
            return

        # 记录每日收益
        daily_l = []
        daily_s = []
        daily_ls = []
        dates_spliced = []
        
        sorted_triggers = sorted(self.trigger_dates)
        for i, start_date in enumerate(sorted_triggers):
            curr_idx = all_dates.get_loc(start_date)
            if i + 1 < len(sorted_triggers):
                next_start_date = sorted_triggers[i+1]
                end_idx = min(curr_idx + self.period, all_dates.get_loc(next_start_date))
            else:
                end_idx = min(curr_idx + self.period, len(all_dates) - 1)
            
            if end_idx <= curr_idx: continue
                
            groups = self._signal_groups_cache.get(start_date)
            if not groups: continue
            long_assets = groups.get(self.n_groups, [])
            short_assets = groups.get(1, [])
            if not long_assets or not short_assets: continue
            
            # 修改为点对点分配计算 (对齐 spliced 逻辑，支持斜线显示)
            l_total_ret = (self.price_df.iloc[end_idx].reindex(long_assets) / self.price_df.iloc[curr_idx].reindex(long_assets) - 1).mean()
            s_total_ret = (self.price_df.iloc[end_idx].reindex(short_assets) / self.price_df.iloc[curr_idx].reindex(short_assets) - 1).mean()
            
            l_total_ret = 0 if pd.isna(l_total_ret) else l_total_ret
            s_total_ret = 0 if pd.isna(s_total_ret) else s_total_ret
            ls_total_ret = l_total_ret - s_total_ret
            
            num_days = end_idx - curr_idx
            # 计算日均复利收益
            l_daily = (1 + l_total_ret)**(1/num_days) - 1
            s_daily = (1 + s_total_ret)**(1/num_days) - 1
            ls_daily = (1 + ls_total_ret)**(1/num_days) - 1
            
            for j in range(curr_idx, end_idx):
                daily_l.append(l_daily)
                daily_s.append(s_daily)
                daily_ls.append(ls_daily)
                dates_spliced.append(all_dates[j+1])

        if not daily_l: return

        # 计算净值
        equity_l = (1 + pd.Series(daily_l)).cumprod()
        equity_s = (1 + pd.Series(daily_s)).cumprod()
        equity_ls = (1 + pd.Series(daily_ls)).cumprod()
        
        # 加上初始点
        first_date = all_dates[all_dates.get_loc(sorted_triggers[0])]
        
        # 2. 绘图
        plt.figure(figsize=(12, 6))
        x_indices = range(len(dates_spliced))
        
        plt.plot(x_indices, equity_l, color='#D80000', label='多头组合')
        plt.plot(x_indices, equity_s, color='#008800', label='空头组合')
        plt.plot(x_indices, equity_ls, color='#004488', linewidth=2, label='多空对冲')
        
        plt.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
        plt.title(title)
        plt.ylabel("累积净值")
        plt.xlabel("日期 (仅包含信号活跃期拼接)")
        
        # 稀疏显示 x 轴日期
        if len(dates_spliced) > 10:
            step = len(dates_spliced) // 10
            plt.xticks(x_indices[::step], [d.strftime('%Y-%m-%d') for d in dates_spliced[::step]], rotation=45)
        else:
            plt.xticks(x_indices, [d.strftime('%Y-%m-%d') for d in dates_spliced], rotation=45)
            
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        save_path = os.path.join(self.output_dir, "equity_curve_combined_l_s_ls.png")
        plt.savefig(save_path)
        logger.info(f"Combined L/S/LS equity curve saved to: {save_path}")
        plt.close()


    def plot_full_timeline_equity_curve(self, group_results, title="全时段多空对冲净值曲线"):
        """
        绘制连续日度真实时间轴净值曲线 (包含空仓横盘时期)
        """
        if group_results.empty or group_results.shape[1] < 2:
            logger.warning("Insufficient data for full timeline equity curve.")
            return

        equity_curve_full = self._calculate_continuous_strategy_returns()
        if not self.performance_stats:
            self.calculate_performance_stats(group_results)
        
        ls_returns = equity_curve_full.pct_change().dropna()
        vol = ls_returns.std() * np.sqrt(252) * 100
        stats_tuple = (
            self.performance_stats.get('LS_Ann_Ret', 0) * 100,
            vol,
            self.performance_stats.get('LS_Sharpe', 0),
            abs(self.performance_stats.get('LS_Max_DD', 0)) * 100
        )
        
        Visualizer.plot_performance_nav(
            equity_curve_full, 
            title, 
            stats_tuple, 
            self.output_dir, 
            "equity_curve_full_timeline.png"
        )
        logger.info(f"Full timeline equity curve saved to: {os.path.join(self.output_dir, 'equity_curve_full_timeline.png')}")
