import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from core.NavAnalyzer import NAVAnalyzer
from core.DataManager import DataProvider, normalize_series

# 设置绘图字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class TSComparator:
    """
    时间序列对比工具类
    """
    @staticmethod
    def load_series(path: str, date_col: str = "date") -> pd.DataFrame:
        """
        利用 data_manager 加载并返回标准 OHLC DataFrame
        """
        dp = DataProvider()  # 使用默认配置
        df = dp.get_ohlc_data(path, Path(path).stem)
        
        if df is None or df.empty:
            raise ValueError(f"无法加载数据或数据为空: {path}")
        return df

    @staticmethod
    def plot_series(df: pd.DataFrame, title: str, out_path: Path):
        """
        绘制归一化后的时间序列图表
        """
        plt.figure(figsize=(12, 6))
        for col in df.columns:
            plt.plot(df.index, df[col], label=col)
        plt.title(title)
        plt.xlabel("日期")
        plt.ylabel("归一化净值 (起始=1)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=150)
        plt.close()

    @staticmethod
    def plot_rolling_returns(df: pd.DataFrame, years: int, out_path: Path):
        """
        绘制滚动 N 年收益率图表
        """
        # 假设一年 252 个交易日
        window = int(years * 252)
        if len(df) < window:
            print(f"警告: 数据长度不足 {years} 年，跳过滚动收益率绘制")
            return

        # 计算滚动收益率 (P_t / P_{t-window}) - 1
        # 使用 shift(window) 找到 N 年前对应的价格
        rolling_ret = (df / df.shift(window) - 1) * 100

        plt.figure(figsize=(12, 6))
        for col in rolling_ret.columns:
            plt.plot(rolling_ret.index, rolling_ret[col], label=col)
        
        plt.title(f"滚动 {years} 年收益率 (%)")
        plt.xlabel("日期")
        plt.ylabel("收益率 (%)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 设置百分比格式的 Y 轴标签
        from matplotlib.ticker import PercentFormatter
        # 由于已经乘以100，这里只需添加 % 符号
        plt.gca().yaxis.set_major_formatter(lambda x, pos: f'{x:.0f}%')
        
        plt.tight_layout()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, dpi=150)
        plt.close()

    @staticmethod
    def pairwise_corr(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算两两重叠部分的相关系数表
        """
        cols = df.columns
        corr_mat = pd.DataFrame(index=cols, columns=cols, dtype=float)
        for i, c1 in enumerate(cols):
            for c2 in cols:
                sub = df[[c1, c2]].dropna()
                if len(sub) > 1:
                    s1 = sub[c1].values
                    s2 = sub[c2].values
                    corr_mat.loc[c1, c2] = np.corrcoef(s1, s2)[0, 1]
                else:
                    corr_mat.loc[c1, c2] = pd.NA
        return corr_mat


    def run_comparison(self, 
                      files: list = None, 
                      file: str = None, 
                      date_col: str = "date", 
                      out_dir: str = "results/ts_compare", 
                      chart_name: str = "series_compare.png", 
                      rolling_name: str = "rolling_returns.png", 
                      rolling_years: int = 3, 
                      corr_name: str = "correlation_price.csv", 
                      corr_ret_name: str = "correlation_return.csv", 
                      perf_name: str = "performance_summary.csv"):
        """
        运行完整的对比流程
        """
        # 处理输入数据
        if files:
            series_map = {}
            for fp in files:
                file_path = Path(fp)
                if not file_path.exists():
                    print(f"警告: 文件不存在: {fp}")
                    continue

                df_one = self.load_series(fp, date_col)
                if 'close' in df_one.columns and not df_one['close'].isna().all():
                    series_map[file_path.stem] = df_one['close']
                else:
                    print(f"警告: {fp} 中未找到有效价格序列")
            
            if not series_map:
                print("错误: 未加载到任何有效数据序列")
                return
                
            df_combined = pd.DataFrame(series_map)
            norm_df = normalize_series(df_combined)
        elif file:
            df_one = self.load_series(file, date_col)
            price_df = df_one.select_dtypes(include=[np.number])
            if 'close' in price_df.columns:
                df_combined = price_df[['close']]
            else:
                df_combined = price_df
            norm_df = normalize_series(df_combined)
        else:
            print("错误: 未提供输入文件")
            return

        norm_df = norm_df.dropna(axis=1, how='all')
        if norm_df.empty:
            print("错误: 归一化后所有序列均为空")
            return

        # 输出结果
        out_dir_path = Path(out_dir)
        chart_path = out_dir_path / chart_name
        rolling_path = out_dir_path / rolling_name
        corr_path = out_dir_path / corr_name
        corr_ret_path = out_dir_path / corr_ret_name
        perf_path = out_dir_path / perf_name

        print(f"正在绘制对比图...")
        self.plot_series(norm_df, title="Normalized Time Series Comparison", out_path=chart_path)

        print(f"正在绘制滚动 {rolling_years} 年收益率图...")
        self.plot_rolling_returns(df_combined, years=rolling_years, out_path=rolling_path)

        print(f"正在计算相关性...")
        corr_price = self.pairwise_corr(df_combined)
        corr_path.parent.mkdir(parents=True, exist_ok=True)
        corr_price.to_csv(corr_path)

        df_returns = df_combined.pct_change().dropna(how='all')
        corr_return = self.pairwise_corr(df_returns)
        corr_ret_path.parent.mkdir(parents=True, exist_ok=True)
        corr_return.to_csv(corr_ret_path)

        print(f"正在计算绩效分析汇总...")
        perf_rows = []
        for col in df_combined.columns:
            rets = df_combined[col].pct_change().fillna(0)
            # 使用 NAVAnalyzer 进行指标计算
            analyzer = NAVAnalyzer(rets)
            stats = analyzer.compute_stats()
            perf_rows.append({
                '名称': col,
                '年化收益率': f"{stats['annual_return']:.2f}%",
                '年化波动率': f"{stats['annual_volatility']:.2f}%",
                '夏普比率': f"{stats['sharpe_ratio']:.2f}",
                '最大回撤': f"{stats['max_drawdown']:.2f}%"
            })
        perf_df = pd.DataFrame(perf_rows)
        perf_df.to_csv(perf_path, index=False, encoding='utf-8-sig')
        print(f"\n绩效对比汇总\n{perf_df.to_string(index=False)}")

        print("-" * 30)
        print(f"已保存对比图: {chart_path}")
        print(f"已保存滚动收益率图: {rolling_path}")
        print(f"已保存价格相关系数表: {corr_path}")
        print(f"已保存收益率相关系数表: {corr_ret_path}")
        print(f"已保存绩效汇总表: {perf_path}")
