import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from factors.technical_factors import HotspotFactors
from core.FactorTester import FactorTester
from core.DataManager import DataProvider

FACTOR_NAME = "gx_hotspot_v1"
FACTOR_PATH = "D:/DATA/FACTORS"
DATA_PATH = r'D:\DATA\all_stock_data_ts_20140102_20251231.csv'
START_DATE = '2024-01-01'
END_DATE = '2024-06-30'
UNIVERSE = '000852'

# 设置绘图风格
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_style("whitegrid")

def run_gx_hotspot_analysis(data_path, start_date="2020-01-01", end_date="2025-12-31", universe=None, window_len=20, drawdown_th=0.10):
    """
    整合并执行 GX_hotspot 因子的全流程分析
    1. 加载真实行情数据 (支持 Universe 过滤)
    2. 计算因子并保存结果
    3. 执行标准化 FactorTester 检验
    4. 生成并保存可视化图表
    """
    universe_tag = universe if universe else "ALL"
    output_dir = os.path.join(os.getcwd(), "results", f"gx_hotspot_{universe_tag}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 1. 加载数据
    print(f"正在从 {data_path} 加载数据 (Universe: {universe_tag})...")
    loader = DataProvider()
    try:
        full_df = loader.get_universe_data(
            filename=data_path, 
            universe=universe, 
            start_date=start_date, 
            end_date=end_date
        )
        
        if full_df.empty:
            print("警告：加载的数据为空，请检查路径或 Universe 设置。")
            return
            
        print(f"数据加载完成。交易日数: {full_df.index.get_level_values('date').nunique()}, 股票数: {full_df.index.get_level_values('code').nunique()}")
    except Exception as e:
        print(f"数据加载失败: {e}")
        return

    # 2. 计算因子
    print(f"开始计算 GX_hotspot 因子 (窗口长度={window_len}, 回撤阈值={drawdown_th})...")
    hi = HotspotFactors()
    factor_results = hi.calculate_gx_hotspot(full_df, window_len=window_len, drawdown_th=drawdown_th)
    full_df["gx_hotspot"] = factor_results["gx_hotspot"]

    # 保存因子原始结果 (CSV 格式)
    factor_save_path = os.path.join(output_dir, "gx_hotspot_factor_values.csv")
    print(f"正在保存因子计算结果至: {factor_save_path}")
    full_df["gx_hotspot"].to_csv(factor_save_path)

    # 3. 准备标准化检验数据
    print("准备 FactorTester 标准化检验...")
    df_test = full_df.reset_index().copy()
    
    # 确保没有重复索引
    df_test = df_test.drop_duplicates(subset=["date", "code"])
    
    df_test["FDate"] = pd.to_datetime(df_test["date"])
    df_test["SecCode"] = df_test["code"]
    
    # 为了解决 Alphalens 分箱失败的问题（因子值过于集中），加入极小扰动
    df_test["gx_hotspot"] += np.random.normal(0, 1e-9, size=len(df_test))
    
    prices = df_test.pivot(index="FDate", columns="SecCode", values="close")

    # 4. 初始化 FactorTester 并运行
    tester = FactorTester(
        factor_data=df_test[["FDate", "SecCode", "gx_hotspot"]], 
        prices=prices, 
        output_dir=output_dir
    )

    # A. 数据质量分析
    tester.analyze_data_quality()

    # B. 因子预处理
    tester.preprocess_factors(method="zscore")

    # C. Alphalens 深度测试
    print("执行 Alphalens 统计分析...")
    try:
        # 使用 max_loss=1.0 确保即使有部分缺失也能尽可能输出结果
        results, summary = tester.run_alphalens_test(
            periods=(5, 20, 40), 
            quantiles=5, 
            save_tearsheets=True,
            max_loss=1.0
        )
        print("\n=== Alphalens 测试概览 ===")
        print(summary)
        
        # 保存汇总统计到 CSV
        summary.to_csv(os.path.join(output_dir, "alphalens_summary_stats.csv"))
        
        # D. 生成分组多空收益图
        print("生成分组收益分析图...")
        for factor_name, data in results.items():
            mean_ret_quantile = data["mean_ret_quantile"]
            for p in (5, 20, 40):
                col = f"{p}D" if f"{p}D" in mean_ret_quantile.columns else p
                if col in mean_ret_quantile.columns:
                    ret_q = mean_ret_quantile[col].unstack("factor_quantile")
                    ret_q.index = pd.to_datetime(ret_q.index)
                    
                    cum_ret_q = (1 + ret_q).cumprod()
                    long_short = ret_q[ret_q.columns[-1]] - ret_q[ret_q.columns[0]]
                    cum_ls = (1 + long_short).cumprod()
                    
                    plt.figure(figsize=(12, 6))
                    for q in cum_ret_q.columns:
                        plt.plot(cum_ret_q.index, cum_ret_q[q], label=f"Quantile {q}", alpha=0.7)
                    plt.plot(cum_ls.index, cum_ls, label="Long-Short (Top-Bottom)", 
                             linestyle="--", color="black", linewidth=2)
                    
                    plt.title(f"{factor_name} Cumulative Returns - {p}D Period")
                    plt.legend(loc="upper left")
                    plt.grid(True, alpha=0.3)
                    save_path = os.path.join(output_dir, f"{factor_name}_cum_ret_{p}d.png")
                    plt.savefig(save_path, dpi=300)
                    plt.close()
                    print(f"已保存收益图: {save_path}")

    except Exception as e:
        print(f"Alphalens 过程出错: {e}")

    print(f"\n全流程分析完成！\n所有结果及图表已保存至: {output_dir}")

if __name__ == "__main__":
    run_gx_hotspot_analysis(DATA_PATH, start_date=START_DATE, end_date=END_DATE, universe=UNIVERSE)