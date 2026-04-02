import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats as scipy_stats
from core.Logger import logger
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class TimingTester:
    def __init__(self, signal_series, benchmark_series, output_dir="results/timing"):
        self.signal = signal_series
        self.benchmark = benchmark_series
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._last_timing_stats = None

    def run_timing_analysis(self, period=20, trigger_dates=None):
        if self.benchmark is None:
            logger.error("No benchmark")
            return None
        if trigger_dates is None:
            if isinstance(self.signal, pd.DataFrame):
                trigger_dates = self.signal[self.signal.iloc[:, 0].abs() == 1].index
            else:
                trigger_dates = self.signal[self.signal.abs() == 1].index
        else:
            trigger_dates = pd.to_datetime(trigger_dates)
        bench_rets_all = self.benchmark.shift(-period) / self.benchmark - 1
        bench_rets_all = bench_rets_all.dropna()
        valid_trigger_dates = trigger_dates.intersection(self.benchmark.index)
        sample_rets = bench_rets_all.reindex(valid_trigger_dates).dropna()
        if sample_rets.empty:
            logger.warning("No triggers")
            return {}
        sample_mean = sample_rets.mean()
        base_mean = bench_rets_all.mean()
        base_std = bench_rets_all.std()
        hit_rate = (sample_rets > 0).mean()
        quantile_rank = (bench_rets_all < sample_mean).mean()
        t_stat, p_value = scipy_stats.ttest_1samp(sample_rets, base_mean)
        timing_stats = {
            "period": period, "n_triggers": len(sample_rets),
            "sample_avg": sample_mean, "universe_avg": base_mean,
            "hit_rate": hit_rate, "base_std": base_std,
            "quantile_rank": quantile_rank, "t_stat": t_stat, "p_val": p_value
        }
        self._last_timing_stats = {"stats": timing_stats, "sample_rets": sample_rets, "base_dist": bench_rets_all}
        logger.info(f"T+{period} Triggers: {len(sample_rets)}, Avg: {sample_mean:.2%}, Hit: {hit_rate:.2%}")
        self.plot_timing_distribution()
        return timing_stats

    def plot_timing_distribution(self, title="Timing Dist"):
        if self._last_timing_stats is None: return
        import seaborn as sns
        data = self._last_timing_stats
        stats_val = data["stats"]
        p = stats_val["period"]
        sample_rets = data["sample_rets"]
        base_dist = data["base_dist"]
        
        plt.figure(figsize=(10, 6))
        # 基准分布 (灰色) 
        sns.histplot(base_dist, kde=True, color="gray", alpha=0.3, 
                     label=f"Base (Avg: {stats_val['universe_avg']:.2%})", stat="density", zorder=1)
        # 信号分布 (红色) 
        sns.histplot(sample_rets, kde=True, color="salmon", alpha=0.4, 
                     label=f"Signal (Avg: {stats_val['sample_avg']:.2%})", stat="density", zorder=2, edgecolor='none')
        
        # 均线位置
        plt.axvline(stats_val["sample_avg"], color="red", linestyle="--", linewidth=1.5, zorder=3)
        plt.axvline(stats_val["universe_avg"], color="blue", linestyle="--", linewidth=1.5, zorder=3)
        
        plt.title(f"{title} (Forward {p} Days)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f"timing_dist_T{p}.png"))
        plt.close()

    def plot_signals(self, asset_name="Bench", title="Signals"):
        if self.benchmark is None: return
        plt.figure(figsize=(15, 7))
        plt.plot(self.benchmark.index, self.benchmark, label=asset_name, color="blue", alpha=0.4)
        trigger_dates = self.signal[self.signal.abs() == 1].index
        if len(trigger_dates) > 0:
            # 修改为竖着的浅红色虚线
            for dt in trigger_dates:
                plt.axvline(dt, color="lightcoral", linestyle="--", linewidth=0.8, alpha=0.7)
            
            # 同时保留一些标记以便识别
            plt.scatter(trigger_dates, self.benchmark.loc[trigger_dates], 
                       color="red", marker="^", s=30, alpha=0.8, label="Signals")
        
        plt.title(title)
        plt.legend()
        plt.savefig(os.path.join(self.output_dir, "signal_triggers.png"))
        plt.close()

    def plot_annual_frequency(self, title="Annual Counts"):
        trigger_dates = self.signal[self.signal.abs() == 1].index
        if len(trigger_dates) == 0: return
        
        # 计算每年信号触发次数
        counts = pd.Series(1, index=trigger_dates).resample("YE").sum()
        counts.index = counts.index.year
        
        # 绘图
        plt.figure(figsize=(12, 6))
        ax = counts.plot(kind="bar", color="skyblue", rot=45)
        plt.title(f"{title} - Annual Distribution")
        plt.ylabel("Trigger Count")
        
        # 在柱状图上方添加数值标签
        for i, v in enumerate(counts):
            ax.text(i, v + 0.1, str(int(v)), ha="center")
            
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "annual_count.png"))
        plt.close()
        
        # 添加每年信号触发次数的统计表格 (CSV格式)
        counts_df = counts.to_frame(name="Trigger_Count")
        counts_df.index.name = "Year"
        counts_df.to_csv(os.path.join(self.output_dir, "annual_statistics.csv"))
        logger.info(f"Annual statistics saved to {self.output_dir}/annual_statistics.csv")

    def export_trigger_log(self, filename="signal_trigger_dates.csv"):
        trigger_dates = self.signal[self.signal.abs() == 1].index
        if len(trigger_dates) == 0: return
        pd.DataFrame({"trigger_date": trigger_dates}).to_csv(os.path.join(self.output_dir, filename), index=False)

    def run_full_report(self, periods=[5, 10, 20, 60]):
        self.plot_signals()
        self.plot_annual_frequency()
        self.export_trigger_log()
        for p in periods:
            self.run_timing_analysis(period=p)

