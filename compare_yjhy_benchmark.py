import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
from core.DataManager import DataProvider

# 中文字体配置
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_yjhy_prices():
    """读取 yjhy_prices.csv 并计算等权平均"""
    yjhy_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
    
    if not os.path.exists(yjhy_path):
        print(f"Error: File not found: {yjhy_path}")
        return None
    
    df = pd.read_csv(yjhy_path, index_col=0, parse_dates=True)
    print(f"yjhy_prices shape: {df.shape}")
    print(f"yjhy_prices columns: {df.columns.tolist()[:10]}...")
    
    # 等权平均每一行（每个日期）的所有列
    yjhy_avg = df.mean(axis=1)
    yjhy_avg.name = 'yjhy_avg'
    
    print(f"yjhy_avg shape: {yjhy_avg.shape}")
    print(f"yjhy_avg first few values:\n{yjhy_avg.head()}")
    
    return yjhy_avg

def load_benchmark():
    """读取 000985 中证全指数据"""
    dp = DataProvider(base_data_path="D:/DATA")
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    
    try:
        index_data = dp.get_ohlc_data(index_file, name="target_index")
        print(f"Benchmark shape: {index_data.shape}")
        print(f"Benchmark first few values:\n{index_data['close'].head()}")
        return index_data['close']
    except Exception as e:
        print(f"Error loading benchmark: {e}")
        return None

def calculate_equity_curve(price_series, name):
    """
    计算净值曲线
    :param price_series: 价格序列（pd.Series）
    :param name: 序列名称
    :return: 净值曲线（pd.Series）
    """
    # 计算日收益率
    returns = price_series.pct_change()
    # 计算累积收益（净值）
    equity_curve = (1 + returns).cumprod()
    equity_curve.name = name
    
    return equity_curve

def plot_comparison(yjhy_equity, benchmark_equity):
    """绘制等权平均yjhy与中证全指的净值曲线对比图"""
    
    # 对齐日期
    common_dates = yjhy_equity.index.intersection(benchmark_equity.index)
    yjhy_aligned = yjhy_equity[common_dates]
    benchmark_aligned = benchmark_equity[common_dates]
    
    # 归一化到相同起点
    yjhy_normalized = yjhy_aligned / yjhy_aligned.iloc[0]
    benchmark_normalized = benchmark_aligned / benchmark_aligned.iloc[0]
    
    # 绘图
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # 第一个图：净值曲线对比
    ax1.plot(yjhy_normalized.index, yjhy_normalized.values, label='一级行业等权平均', linewidth=2, color='blue')
    ax1.plot(benchmark_normalized.index, benchmark_normalized.values, label='000985中证全指', linewidth=2, color='red')
    ax1.set_title('等权平均一级行业 vs 中证全指净值曲线对比', fontsize=14, fontweight='bold')
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('净值（相对）', fontsize=12)
    ax1.legend(fontsize=11, loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 第二个图：相对表现（超额收益曲线）
    excess_returns = yjhy_normalized - benchmark_normalized
    ax2.plot(excess_returns.index, excess_returns.values, label='超额收益（一级行业平均 - 中证全指）', 
             linewidth=2, color='green')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_title('超额收益曲线', fontsize=14, fontweight='bold')
    ax2.set_xlabel('日期', fontsize=12)
    ax2.set_ylabel('超额收益', fontsize=12)
    ax2.legend(fontsize=11, loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = 'results/yjhy_vs_benchmark_comparison.png'
    os.makedirs('results', exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ 对比图已保存: {output_path}")
    plt.close()

def print_statistics(yjhy_prices, yjhy_equity, benchmark_equity):
    """打印统计指标"""
    
    common_dates = yjhy_equity.index.intersection(benchmark_equity.index)
    yjhy_aligned = yjhy_equity[common_dates]
    benchmark_aligned = benchmark_equity[common_dates]
    
    # 计算收益率
    yjhy_total_return = (yjhy_aligned.iloc[-1] - yjhy_aligned.iloc[0]) / yjhy_aligned.iloc[0]
    benchmark_total_return = (benchmark_aligned.iloc[-1] - benchmark_aligned.iloc[0]) / benchmark_aligned.iloc[0]
    
    # 计算年化收益率
    days = (common_dates[-1] - common_dates[0]).days
    years = days / 365.25
    yjhy_annual = (yjhy_aligned.iloc[-1] / yjhy_aligned.iloc[0]) ** (1/years) - 1
    benchmark_annual = (benchmark_aligned.iloc[-1] / benchmark_aligned.iloc[0]) ** (1/years) - 1
    
    # 计算波动率
    yjhy_returns = yjhy_prices[common_dates].pct_change().dropna()
    benchmark_returns = benchmark_equity[common_dates].pct_change().dropna()
    
    yjhy_vol = yjhy_returns.std() * np.sqrt(252)
    benchmark_vol = benchmark_returns.std() * np.sqrt(252)
    
    # 计算夏普比率（假设无风险利率为2%）
    risk_free_rate = 0.02
    yjhy_sharpe = (yjhy_annual - risk_free_rate) / yjhy_vol if yjhy_vol > 0 else 0
    benchmark_sharpe = (benchmark_annual - risk_free_rate) / benchmark_vol if benchmark_vol > 0 else 0
    
    # 计算最大回撤
    def max_drawdown(returns_series):
        cumsum = (1 + returns_series).cumprod()
        running_max = cumsum.expanding().max()
        drawdown = (cumsum - running_max) / running_max
        return drawdown.min()
    
    yjhy_mdd = max_drawdown(yjhy_returns)
    benchmark_mdd = max_drawdown(benchmark_returns)
    
    print("\n" + "="*70)
    print(f" 统计指标对比 (起始日期: {common_dates[0].date()}, 结束日期: {common_dates[-1].date()}) ")
    print("="*70)
    print(f"{'指标':<20} | {'一级行业等权平均':<20} | {'000985中证全指':<20}")
    print("-"*70)
    print(f"{'累计收益率':<20} | {yjhy_total_return*100:>18.2f}% | {benchmark_total_return*100:>18.2f}%")
    print(f"{'年化收益率':<20} | {yjhy_annual*100:>18.2f}% | {benchmark_annual*100:>18.2f}%")
    print(f"{'年化波动率':<20} | {yjhy_vol*100:>18.2f}% | {benchmark_vol*100:>18.2f}%")
    print(f"{'夏普比率':<20} | {yjhy_sharpe:>20.4f} | {benchmark_sharpe:>20.4f}")
    print(f"{'最大回撤':<20} | {yjhy_mdd*100:>18.2f}% | {benchmark_mdd*100:>18.2f}%")
    print("="*70)

if __name__ == "__main__":
    print("Loading data...")
    
    # 读取 yjhy 数据
    yjhy_prices = load_yjhy_prices()
    if yjhy_prices is None:
        exit(1)
    
    # 读取基准指数
    benchmark_prices = load_benchmark()
    if benchmark_prices is None:
        exit(1)
    
    # 计算净值曲线
    print("\nCalculating equity curves...")
    yjhy_equity = calculate_equity_curve(yjhy_prices, 'yjhy_avg')
    benchmark_equity = calculate_equity_curve(benchmark_prices, 'benchmark')
    
    # 打印统计
    print_statistics(yjhy_prices, yjhy_equity, benchmark_equity)
    
    # 绘制对比图
    print("\nGenerating comparison chart...")
    plot_comparison(yjhy_equity, benchmark_equity)
    
    print("\n✓ 完成!")
