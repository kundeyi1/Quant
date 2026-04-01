import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings
from core.Logger import logger
from core.NavAnalyzer import NAVAnalyzer

warnings.filterwarnings('ignore')

# 设置绘图风格
plt.rcParams['figure.figsize'] = [12, 7]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class TimingTester:
    """
    TimingTester: 专门用于检验 0/1/-1 择时信号的有效性。
    支持使用 NAVAnalyzer 进行性能分析，并输出择时净值与基准对比图。
    """
    def __init__(self, signal_series, benchmark_series, output_dir="results/timing"):
        """
        :param signal_series: pd.Series, 择时信号 (1: 多头, 0: 空仓, -1: 空头)。
        :param benchmark_series: pd.Series, 基准价格序列（如指数收盘价）。
        :param output_dir: str, 结果保存目录。
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.benchmark = benchmark_series.sort_index()
        # 对齐信号与基准
        self.signal = signal_series.reindex(self.benchmark.index).fillna(0)
        
        self.nav_analyzer = None
        self.results_df = None

    def backtest(self):
        """
        执行回测逻辑。
        修正逻辑：
        1. 计算基准 T 日收益率 (r_t = P_t / P_{t-1} - 1)
        2. T 日收盘产生的信号 s_t，只能作用于 T+1 日的收益 r_{t+1}
        3. 策略收益 r_strat_{t+1} = s_t * r_{t+1}
        """
        # 计算基准收益率 (收盘价对收盘价)
        bench_ret = self.benchmark.pct_change().fillna(0)
        
        # 信号右移一位：T日的信号作用于T+1日的收益
        # shift(1) 后，原本在 T 的位置现在是 T-1 的信号
        executed_signal = self.signal.shift(1).fillna(0)
        
        # 策略收益 = 执行时刻的信号 * 当日基准收益
        strat_ret = executed_signal * bench_ret
        
        # 使用 NAVAnalyzer 进行分析
        self.nav_analyzer = NAVAnalyzer(strat_ret, name="TimingStrategy")
        stats = self.nav_analyzer.compute_performance()
        
        # 构造结果 DataFrame 用于绘图
        self.results_df = pd.DataFrame({
            'strategy_nav': self.nav_analyzer.nav,
            'benchmark_nav': (1 + bench_ret).cumprod(),
            'signal': self.signal,
            'executed_signal': executed_signal,
            'daily_ret': strat_ret
        }, index=self.benchmark.index)

        # 自动保存计算结果到数据目录
        self.save_results()
        
        return stats

    def save_results(self):
        """
        将回测过程中的详细数据保存为 CSV / Parquet 文件。
        并额外保存因子值和择时值到特定目录。
        """
        if self.results_df is not None:
            # 1. 默认保存到当前输出目录
            csv_path = os.path.join(self.output_dir, "backtest_results.csv")
            self.results_df.to_csv(csv_path, encoding='utf-8-sig')
            
            # 2. 额外保存到 D:\DATA\FACTORS 和 D:\DATA\TIMING (保存为 Parquet 文件)
            factor_name = os.path.basename(self.output_dir.rstrip('\\/'))
            
            try:
                timing_dir = r"D:\DATA\TIMING"
                factor_dir = r"D:\DATA\FACTORS"
                
                os.makedirs(timing_dir, exist_ok=True)
                os.makedirs(factor_dir, exist_ok=True)
                
                # 保存择时值 (Signal) 为 Parquet
                timing_path = os.path.join(timing_dir, f"{factor_name}_timing.parquet")
                self.results_df[['signal']].to_parquet(timing_path)
                
                # 保存因子值/净值序列为 Parquet
                factor_path = os.path.join(factor_dir, f"{factor_name}_values.parquet")
                self.results_df.to_parquet(factor_path)
                
                logger.info(f"数据已同步至 D:\\DATA (Parquet): {timing_path}, {factor_path}")
            except Exception as e:
                logger.warning(f"由于权限或库缺失，无法保存 Parquet 至 D:\\DATA: {e}")

            logger.info(f"回测详细结果已保存至: {csv_path}")

    def plot_nav(self, title="择时策略净值表现", filename=None):
        """
        绘制双轴图：左轴净值(红线/深蓝线)，右轴回撤(浅灰阴影)。
        """
        if self.results_df is None:
            self.backtest()
            
        df = self.results_df.copy()
        save_path = os.path.join(self.output_dir, f"{filename or title}_NAV.png")
        
        # 调用 NAVAnalyzer 的统一绘图接口
        NAVAnalyzer.plot_timing_nav_with_drawdown(
            nav_ser=df['strategy_nav'],
            benchmark_nav=df['benchmark_nav'],
            title=title,
            output_path=save_path
        )
        
        return save_path


    def plot_signals(self, title="择时信号分布图", filename=None):
        """
        绘制信号分布图：
        左轴：基准收盘价曲线。
        右轴：择时信号（1, 0, -1）对应的阶梯阴影。
        """
        if self.results_df is None:
            self.backtest()
            
        df = self.results_df.copy()
        bench_price = self.benchmark
        sig = df['signal']
        
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 1. 绘制基准价格曲线 (左轴)
        ax1.plot(df.index, bench_price, color='midnightblue', linewidth=1.2, label='基准价格')
        ax1.set_ylabel('指数价格')
        ax1.set_xlabel('日期')
        ax1.grid(True, linestyle=':', alpha=0.4)
        
        # 2. 绘制信号阴影 (右轴)
        ax2 = ax1.twinx()
        
        # 绘制背景阴影：因子值和 0 轴形成的区间绘制为灰色，彻底移除边框
        # 设置 linewidth=0, edgecolor='none' 以及 antialiased=False 以防止渲染残留线
        ax2.fill_between(df.index, 0, sig, where=(sig != 0), 
                         color='grey', alpha=0.3, step='post', 
                         linewidth=0, edgecolor='none', antialiased=False,
                         label='择时信号')
        
        # 绘制信号阶梯线（保留 1, 0, -1 的可视化确认）
        ax2.step(df.index, sig, where='post', color='black', linewidth=0.5, alpha=0.4)
      
        ax2.axhline(0, color='black', linewidth=0.5, alpha=0.3)
        ax2.set_ylabel('择时信号')

        ax2.set_yticks([1, 0, -1])
        ax2.set_yticklabels(['1', '0', '-1'])
        ax2.set_ylim(-1, 1)
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.title(title)
        save_path = os.path.join(self.output_dir, f"{filename or title}_Signal.png")
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()
        return save_path

