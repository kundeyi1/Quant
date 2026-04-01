"""
核心分析引擎 - 净值曲线分析工具
提供净值序列的统计分析、可视化等功能，采用面向对象的设计
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 设置绘图中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

TRADING_DAYS_PER_YEAR = 252

class NAVAnalyzer:
    """
    资产净值分析器类
    封装了净值计算、绩效评估和恢复分析的核心逻辑
    """
    def __init__(self, returns_ser, name="Asset", trading_days=TRADING_DAYS_PER_YEAR):
        """
        初始化分析器
        :param returns_ser: 日收益率序列 (pd.Series)
        :param name: 资产名称
        :param trading_days: 每年交易日数
        """
        self.returns = returns_ser.dropna()
        self.name = name
        self.trading_days = trading_days
        self._nav = None
        self._stats = None

    @property
    def nav(self):
        """计算并缓存净值曲线"""
        if self._nav is None:
            self._nav = (1 + self.returns).cumprod()
        return self._nav

    def compute_performance(self, rf_ser=None):
        """
        计算全量核心绩效指标
        """
        nav = self.nav
        days = len(self.returns)
        
        # 1. 年化收益率
        ann_ret = (nav.iloc[-1] ** (self.trading_days / days) - 1) * 100 if days > 0 else np.nan
        
        # 2. 无风险收益对比
        ann_rf = 0
        if rf_ser is not None:
            rf_aligned = rf_ser.reindex(self.returns.index).fillna(0)
            nav_rf = (1 + rf_aligned).cumprod()
            ann_rf = (nav_rf.iloc[-1] ** (self.trading_days / days) - 1) * 100 if days > 0 else 0
        
        # 3. 年化波动率
        vol = self.returns.std() * np.sqrt(self.trading_days) * 100 if days > 1 else np.nan
        
        # 4. 夏普比率
        sharpe = ((ann_ret - ann_rf) / vol) if vol and vol != 0 else np.nan
        
        # 5. 最大回撤
        max_dd = (nav / nav.cummax() - 1).min() * 100 if len(nav) > 0 else np.nan
        
        self._stats = {
            'annual_return': ann_ret,
            'volatility': vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd
        }
        return self._stats

    def get_yearly_stats(self):
        """计算分年度表现指标"""
        df_y = pd.Series(self.returns.values, index=pd.to_datetime(self.returns.index))
        years = sorted(df_y.index.year.unique())
        rows = []
        for y in years:
            y_ret = df_y[df_y.index.year == y]
            if len(y_ret) < 2: continue
            y_nav = (1 + y_ret).cumprod()
            days_y = len(y_ret)
            ann_ret = (y_nav.iloc[-1] ** (self.trading_days / days_y) - 1) * 100 if days_y > 0 else np.nan
            mdd = (y_nav / y_nav.cummax() - 1).min() * 100 if len(y_nav) > 0 else np.nan
            rows.append({
                '年度': int(y),
                f'{self.name}_收益率': f"{ann_ret:.1f}%",
                f'{self.name}_最大回撤': f"{mdd:.1f}%"
            })
        return pd.DataFrame(rows).set_index('年度')

    def compute_max_dd_recovery(self):
        """计算最大回撤恢复天数与日期"""
        nav_ser = self.nav
        if len(nav_ser) == 0: return np.nan, None, None, None
        roll_max = nav_ser.cummax()
        dd = nav_ser / roll_max - 1
        trough_date = dd.idxmin()
        peak_value = roll_max.loc[trough_date]
        pre = roll_max.loc[:trough_date]
        peak_date = pre.index[np.isclose(pre.values, peak_value)][-1]
        post = nav_ser.loc[trough_date:]
        recov = post[post >= peak_value * (1 - 1e-12)]
        if len(recov) == 0: return np.nan, peak_date, trough_date, None
        recovery_date = recov.index[0]
        recovery_days = int((pd.to_datetime(recovery_date) - pd.to_datetime(peak_date)).days)
        return recovery_days, peak_date, trough_date, recovery_date

    def get_winning_year_ratio(self):
        """计算盈利年份占比"""
        yr = pd.Series(self.returns.values, index=pd.to_datetime(self.returns.index))
        yearly_returns = yr.groupby(yr.index.year).apply(lambda r: (1 + r).prod() - 1)
        if yearly_returns.size == 0: return np.nan
        return float(((yearly_returns > 0).sum() / yearly_returns.size) * 100)

    def compute_stats(self):
        """
        计算并返回基础绩效统计数据
        :return: dict 包含 nav, annual_return, annual_volatility, sharpe_ratio, max_drawdown
        """
        perf = self.compute_performance()
        return {
            'nav': self.nav,
            'annual_return': perf['annual_return'],
            'annual_volatility': perf['volatility'],
            'sharpe_ratio': perf['sharpe_ratio'],
            'max_drawdown': perf['max_drawdown']
        }


    @staticmethod
    def plot_timing_nav_with_drawdown(nav_ser, benchmark_nav=None, title="择时净值", output_path=None):
        """
        核心绘图逻辑：绘制净值曲线与动态回撤阴影
        :param nav_ser: 策略净值 (pd.Series)
        :param benchmark_nav: 基准净值 (pd.Series, 可选)
        :param title: 图表标题
        :param output_path: 保存路径
        """
        fig, ax1 = plt.subplots(figsize=(12, 6))
        dates = pd.to_datetime(nav_ser.index)
        
        # 1. 绘制净值曲线 (左轴)
        ax1.plot(dates, nav_ser, color='firebrick', label='策略净值', linewidth=1.5)
        if benchmark_nav is not None:
            # 对齐基准与策略日期
            bench_aligned = benchmark_nav.reindex(nav_ser.index).ffill()
            ax1.plot(dates, bench_aligned, color='midnightblue', label='基准净值', linewidth=1.2, linestyle='--')
        
        ax1.set_ylabel('累计净值')
        ax1.set_xlabel('日期')
        ax1.grid(True, linestyle=':', alpha=0.6)
        
        # 2. 绘制回撤阴影 (右轴)
        ax2 = ax1.twinx()
        roll_max = nav_ser.cummax()
        drawdown = (nav_ser / roll_max - 1.0)
        
        ax2.fill_between(dates, drawdown, 0, color='lightgrey', alpha=0.5, label='回撤 (右)')
        ax2.set_ylabel('回撤')
        ax2.set_ylim(-0.6, 0) # 统一设置回撤轴范围
        
        plt.title(title)
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            plt.close()
            return output_path
        else:
            return fig

class Visualizer:
    """
    绘图可视化中心类
    """
    @staticmethod
    def plot_performance_nav(nav_ser, title, stats, output_dir, filename):
        """绘制带绩效看板和回撤阴影的净值图"""
        fig, ax = plt.subplots(figsize=(10, 4.5))
        dates = pd.to_datetime(nav_ser.index)
        
        # 1. 绘制回撤阴影 (Top-down) 并添加右侧标尺
        ax_dd = ax.twinx()  # 创建共享x轴的次坐标轴
        roll_max = nav_ser.cummax()
        drawdown = 1 - (nav_ser / roll_max)
        
        # 填充灰色阴影，并设置 label 用于图例
        fill_coll = ax_dd.fill_between(dates, drawdown.values, 0, color='gray', alpha=0.2, label='回撤 (右)')
        ax_dd.set_ylim(0.6, 0)  # 回撤轴范围从0%到-100%
        
        # 设置右轴标尺
        ax_dd.set_ylabel('回撤')
        ax_dd.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x*100:.0f}%'))
        
        # 2. 绘制净值曲线
        line_nav = ax.plot(dates, nav_ser.values, linewidth=1, color='#004488', label='净值 (左)')
        ax.set_ylabel('净值')
        
        # 3. 合并图例
        # 由于使用了 twinx，需要手动合并两个 axis 的图例
        lines = line_nav + [plt.Rectangle((0, 0), 1, 1, fc="gray", alpha=0.2)]
        labels = [l.get_label() for l in line_nav] + ['动态回撤']
        ax.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
        
        # 4. 添加绩效统计
        ann_ret, vol, sr, mdd = stats
        text = (f"年化收益: {ann_ret:.2f}%\n波动率: {vol:.2f}%\n夏普比: {sr:.2f}\n最大回撤: {mdd:.2f}%")
        ax.text(0.01, 0.97, text, transform=ax.transAxes, va='top', bbox=dict(facecolor='white', alpha=0.8), fontsize=9)
        
        ax.set_title(title)
        ax.grid(False)
        plt.tight_layout()
        
        if output_dir: 
            plt.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close()

    @staticmethod
    def plot_rolling_returns(series_dict, windows_years=[1, 3, 5], output_dir=None, filename="rolling_returns.png"):
        num_windows = len(windows_years)
        fig, axes = plt.subplots(num_windows, 1, figsize=(12, 4 * num_windows), sharex=True)
        if num_windows == 1: axes = [axes]
        for i, years in enumerate(windows_years):
            ax = axes[i]; window = int(years * 252)
            for label, nav in series_dict.items():
                if len(nav) < window: continue
                rolling_ret = (nav / nav.shift(window)) ** (1/years) - 1
                ax.plot(rolling_ret.index, rolling_ret * 100, label=label)
            ax.set_title(f"滚动 {years} 年年化收益率 (%)"); ax.legend()
        plt.tight_layout()
        if output_dir: plt.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close()

    @staticmethod
    def plot_drawdown_curve(series_dict, output_dir=None, filename="drawdown_curve.png"):
        plt.figure(figsize=(12, 6))
        for label, nav in series_dict.items():
            dd = (nav / nav.cummax() - 1) * 100
            plt.plot(dd.index, dd.values, label=label)
        plt.title("动态回撤曲线 (%)"); plt.legend()
        if output_dir: plt.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close()

    @staticmethod
    def plot_rolling_boxplot(series_dict, windows_years=[1, 3, 5, 10], output_dir=None, filename="rolling_boxplot.png"):
        import seaborn as sns
        data_list = []
        for label, nav in series_dict.items():
            for years in windows_years:
                window = int(years * 252)
                if len(nav) < window: continue
                rolling_ret = ((nav / nav.shift(window)) ** (1/years) - 1) * 100
                for val in rolling_ret.dropna().sample(min(5000, len(rolling_ret.dropna()))):
                    data_list.append({'周期': f"{years}Y", '年化收益率(%)': val, '资产': label})
        df_plot = pd.DataFrame(data_list)
        if df_plot.empty: return
        plt.figure(figsize=(12, 6)); sns.boxplot(x='周期', y='年化收益率(%)', hue='资产', data=df_plot)
        plt.title("滚动年化收益率分布"); plt.tight_layout()
        if output_dir: plt.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close()


    @staticmethod
    def plot_portfolio_vs_benchmark(port_nav, bench_nav, bench_label, output_dir, filename):
        common_idx = port_nav.index.intersection(bench_nav.index)
        bench = bench_nav.loc[common_idx].dropna(); port = port_nav.loc[common_idx]
        x = pd.to_datetime(common_idx)
        
        def get_label(name, nav_ser):
            analyzer = NAVAnalyzer(nav_ser.pct_change().fillna(0))
            s = analyzer.compute_performance()
            return f"{name} (收益:{s['annual_return']:.1f}% 夏普:{s['sharpe_ratio']:.2f} 回撤:{s['max_drawdown']:.1f}%)"

        fig, ax1 = plt.subplots(figsize=(12, 5))
        if len(bench) > 0:
            bench_norm = bench / bench.iloc[0]
            ax1.plot(x, port.values, label=get_label('组合', port), color='#1f77b4')
            ax1.plot(x, bench_norm.values, label=get_label(bench_label, bench_norm), color='#ff7f0e')
        ax1.set_title('Portfolio vs Benchmark'); ax1.legend(); plt.tight_layout()
        if output_dir: plt.savefig(os.path.join(output_dir, filename), dpi=150)
        plt.close()


class PerformanceReport:
    """
    绩效报告自动化生成类
    """
    @staticmethod
    def run_full_report(portfolio_returns, asset_df, results_dir, benchmark_name=None):
        os.makedirs(results_dir, exist_ok=True)
        analyzer = NAVAnalyzer(portfolio_returns, name="Portfolio")
        stats = analyzer.compute_performance()
        
        # 1. 绘图
        Visualizer.plot_performance_nav(analyzer.nav, 'Portfolio NAV', 
                                      (stats['annual_return'], stats['volatility'], stats['sharpe_ratio'], stats['max_drawdown']), 
                                      results_dir, 'portfolio_nav.png')
        
        # 2. 年度统计
        analyzer.get_yearly_stats().to_csv(os.path.join(results_dir, "yearly_stats.csv"), encoding='utf-8-sig')
        
        # 3. 基准对比
        if benchmark_name and benchmark_name in asset_df.columns:
            Visualizer.plot_portfolio_vs_benchmark(analyzer.nav, asset_df[benchmark_name], benchmark_name, results_dir, 'vs_benchmark.png')
            
        print(f"绩效报告生成完毕: {results_dir}")


    @staticmethod
    def analyze_nav_from_csv(nav_csv_path, output_dir, name="Portfolio"):
        """从CSV载入并分析"""
        nav_df = pd.read_csv(nav_csv_path, index_col=0, parse_dates=True)
        nav_ser = nav_df.iloc[:, 0] if len(nav_df.columns) == 1 else nav_df['nav']
        analyzer = NAVAnalyzer(nav_ser.pct_change().fillna(0), name=name)
        stats = analyzer.compute_performance()
        
        # 结果汇总
        return {
            'name': name,
            'annualized_return': stats['annual_return'],
            'sharpe_ratio': stats['sharpe_ratio'],
            'max_drawdown': stats['max_drawdown']
        }


    @staticmethod
    def compare_multiple_navs(nav_dict, output_dir, title="Comparison"):
        """对比多个净值曲线"""
        os.makedirs(output_dir, exist_ok=True)
        plt.figure(figsize=(14, 6))
        for name, nav_ser in nav_dict.items():
            plt.plot(pd.to_datetime(nav_ser.index), nav_ser.values, label=name)
        plt.title(title); plt.legend(); plt.tight_layout()
        if output_dir: plt.savefig(os.path.join(output_dir, 'comparison_nav.png'), dpi=150)
        plt.close()


    @staticmethod
    def perform_sub_asset_analysis(asset_df, results_dir):
        """分资产绩效分析"""
        asset_rets = asset_df.pct_change().fillna(0)
        for col in asset_df.columns:
            analyzer = NAVAnalyzer(asset_rets[col], name=col)
            s = analyzer.compute_performance()
            Visualizer.plot_performance_nav(analyzer.nav, f"{col} NAV", 
                                          (s['annual_return'], s['volatility'], s['sharpe_ratio'], s['max_drawdown']), 
                                          results_dir, f"asset_{col}.png")
