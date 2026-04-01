import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from factors.technical_factors import HotspotFactors
from core.FactorTester import FactorTester

FACTOR_NAME = "gx_hotspot_v1"
OUTPUT_PATH = os.path.join(os.getcwd(), "results", FACTOR_NAME)
FACTOR_PATH = "D:/DATA/FACTORS"
DATA_PATH = r'D:\DATA\all_stock_data_ts_20140102_20251231.csv'
START_DATE = '2019-12-31'
END_DATE = '2025-12-31'

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_style("whitegrid")

def get_gx_hotspot_factor(data_path, window_len=20, drawdown_th=0.10):
    """
    因子获取整合函数：尝试从本地读取，不存在则加载行情数据进行计算并保存。
    """
    factor_save_path = os.path.join(FACTOR_PATH, f"{FACTOR_NAME}_{START_DATE}_{END_DATE}.csv")
    
    # 1. 尝试直接从本地读取因子
    if os.path.exists(factor_save_path):
        print(f"发现已存在的因子文件: {factor_save_path}，直接加载。")
        try:
            factor_df = pd.read_csv(factor_save_path)
            factor_df["date"] = pd.to_datetime(factor_df["date"])
            factor_df["code"] = factor_df["code"].astype(str).str.zfill(6)
            factor_df = factor_df.set_index(["date", "code"])
            return factor_df
        except Exception as e:
            print(f"加载因子文件失败: {e}，将重新计算。")

    # 2. 如果不存在，则加载行情数据并计算
    print(f"因子文件不存在，正在从 {data_path} 加载行情数据进行计算...")
    cols = ["date", "code", "close", "open", "high", "low", "volume"]
    try:
        full_df = pd.read_csv(data_path, usecols=cols)
        full_df["date"] = pd.to_datetime(full_df["date"])
        full_df = full_df[(full_df["date"] >= START_DATE) & (full_df["date"] <= END_DATE)]
        full_df["code"] = full_df["code"].astype(str).str.zfill(6)
        full_df = full_df.set_index(["date", "code"]).sort_index()

        print(f"行情数据加载完成，开始计算 {FACTOR_NAME} 因子...")
        hi = HotspotFactors()
        factor_results = hi.calculate_gx_hotspot(full_df, window_len=window_len, drawdown_th=drawdown_th)
        
        # 整合因子值
        full_df["gx_hotspot"] = factor_results["gx_hotspot"]
        
        # 保存因子原始结果 (CSV 格式)
        # 注意：这里保存 full_df 以便包含 close 等价格信息
        print(f"正在保存因子计算结果至: {factor_save_path}")
        full_df.to_csv(factor_save_path)
        
        return full_df
    except Exception as e:
        print(f"数据加载或计算失败: {e}")
        return None

def run_gx_hotspot_analysis(data_path, window_len=20, drawdown_th=0.10, interval=20):
    """
    整合并执行 GX_hotspot 因子的全流程分析
    """
    output_dir = OUTPUT_PATH

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 1. 获取因子数据 (整合了读取与计算)
    factor_df = get_gx_hotspot_factor(data_path, window_len=window_len, drawdown_th=drawdown_th)
    if factor_df is None:
        print("因子获取失败，退出。")
        return
    
    # 2. 获取行情数据 (prices) 用于回测
    print(f"因子加载完成，正在从 {data_path} 加载价格数据用于回测...")
    try:
        # 只读取必要的列
        price_df = pd.read_csv(data_path, usecols=["date", "code", "close"])
        price_df["date"] = pd.to_datetime(price_df["date"])
        price_df = price_df[(price_df["date"] >= START_DATE) & (price_df["date"] <= END_DATE)]
        price_df["code"] = price_df["code"].astype(str).str.zfill(6)
        
        # 准备 FactorTester 数据
        print("准备 FactorTester 标准化检验...")
        
        # 因子数据对齐
        factor_data_for_test = factor_df.reset_index().copy()
        factor_data_for_test["FDate"] = pd.to_datetime(factor_data_for_test["date"])
        factor_data_for_test["SecCode"] = factor_data_for_test["code"]
        
        # 价格数据清洗与透视
        price_df = price_df.drop_duplicates(subset=["date", "code"])
        
        # 修复 Alphalens 频率报错：确保索引具有频率或在测试前进行重采样/填充
        # 这里我们通过 reindex 补齐所有交易日，但这可能导致大量空值，Alphalens 更倾向于索引有明确的 Freq
        prices = price_df.pivot(index="date", columns="code", values="close")
        prices.index.name = "FDate"
        # 尝试让 pandas 识别频率，如果不能自动识别（存在节假日），Alphalens 可能会报错
        # 另一个方案是在调用 run_alphalens_test 时传入特定的 freq，但 FactorTester.py 目前是硬编码调用
        
        # 为了绕过 Alphalens 的频率校验报错，我们可以通过 reset_index 后重新设置索引并手动指定 freq
        # 如果是 A 股，通常使用 'C' (Custom Business Day) 或直接不去设置它
        # 报错原因是 df.index.levels[0].freq = freq 这一步，我们可以尝试在传入前清理索引
        
        # 4. 初始化分析器 (实例化以避免 AttributeError)
        print("开始计算因子绩效...")
        tester = FactorTester(START_DATE, END_DATE, output_dir=output_dir)
        df_test = factor_data_for_test[["FDate", "SecCode", "gx_hotspot"]].copy()
    except Exception as e:
        print(f"数据处理失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # A. 因子预处理 (手动 zscore)
    print("正在进行截面标准化...")
    # 修正致命错误：NaN 应该保持为 NaN，只对有效值进行标准化，避免 NaN 变成 0 误导排序
    factor_data_for_test['gx_hotspot'] = factor_data_for_test.groupby('FDate')['gx_hotspot'].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() != 0 else np.nan
    )

    # B. 计算前瞻收益率 (调仓频率 D=1, W=5, M=20)
    
    print(f"正在计算前瞻收益率 (Period={interval}D - 降采样至月度调仓)...")
    
    # 模拟月度调仓：只保留每个月最后一个交易日的信号，并计算未来 20D 的持有收益
    # 1. 计算所有日期的持有期收益 (forward returns)
    returns_wide = prices.shift(-interval) / prices - 1
    
    # 2. 采样：只保留每个月最后一个交易日进行“调仓”
    # 寻找每个月的最后一天
    monthly_last_days = prices.index.to_series().groupby(prices.index.to_period('M')).max()
    
    # 3. 过滤信号日期
    # 在 T 日获取信号，并在 T+1 后的 20 个交易日内持有
    # 我们将 factor_data_for_test 限制在这些结算日
    factor_data_for_test = factor_data_for_test[factor_data_for_test['FDate'].isin(monthly_last_days)]
    
    returns_stack = returns_wide.reindex(monthly_last_days).stack().reset_index()
    returns_stack.columns = ['FDate', 'SecCode', 'r']
    
    # 合并因子与收益
    final_test_df = factor_data_for_test.merge(returns_stack, on=['FDate', 'SecCode'], how='inner')
    final_test_df.dropna(subset=['gx_hotspot', 'r'], inplace=True)

    # C. 使用 FactorTester 执行回测
    print("正在通过 FactorTester 执行回测...")
    
    # 将价格数据注入 tester (因为 backtest 内部需要 get_forward_returns)
    tester.prices = prices
    
    # 修改列名以符合 FactorTester 的 ['FDate', 'SecCode', 'FValue']
    test_factors = factor_data_for_test[["FDate", "SecCode", "gx_hotspot"]].rename(columns={"gx_hotspot": "FValue"})
    
    # 注意：这里的 factor_data_for_test 已经过滤为月频信号，
    # 而 backtest 内部会根据 interval_tag 再调一次 shift(-20)，为了避免双重采样，
    # 我们直接将 test_factors 传入即可。
    metrics, nav_df = tester.backtest(
        factor_name=FACTOR_NAME,
        factor_data=test_factors,
        interval_tag='M', # 持有 20D，对应 M
        groups=5,
        if_plot=True
    )

    # D. 额外 IC 绘图 (IC 时间序列与累计 Rank IC)
    print("生成 IC 分析图...")
    daily_ic = metrics.at[FACTOR_NAME, 'RankIC'] # 只是为了兼容后续代码逻辑，从 metrics 获取均值或重算
    
    # 重新计算一次每日 IC 用于自定义绘图
    daily_ic = final_test_df.groupby('FDate').apply(
        lambda x: x['gx_hotspot'].corr(x['r'], method='spearman')
    )
    
    # 获取净值结果
    quantile_ret = nav_df.pct_change().fillna(0)
    cum_ret = nav_df
    fig, ax1 = plt.subplots(figsize=(15, 6))
    
    # 绘制当日 IC (柱状图)
    ax1.bar(daily_ic.index, daily_ic.values, color='#1f4e79', alpha=0.6, label='Daily Rank IC')
    ax1.set_ylabel('Daily IC', fontsize=12)
    ax1.axhline(0, color='black', lw=0.5)
    
    # 计算并绘制累计 Rank IC (折线图)
    cum_ic = daily_ic.cumsum()
    ax2 = ax1.twinx()
    ax2.plot(cum_ic.index, cum_ic.values, color='#c00000', linewidth=2, label='Cumulative Rank IC')
    ax2.set_ylabel('Cumulative IC', fontsize=12)
    
    # 标题与图例
    plt.title(f"{FACTOR_NAME} {interval}D Rank IC & Cumulative IC", fontsize=14)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax1.grid(True, axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"ic_analysis_{interval}D.png"), dpi=300)
    plt.close()

    # E. 保存结果
    daily_ic.to_csv(os.path.join(output_dir, "daily_rank_ic.csv"))
    nav_df.to_csv(os.path.join(output_dir, "quantile_cum_returns.csv"))
    
    # 保存分组选股结果 (从 final_test_df 中重新计算分位数标签)
    final_test_df['quantile'] = final_test_df.groupby('FDate')['gx_hotspot'].rank(pct=True).apply(
        lambda x: int(np.ceil(x * 5)) if pd.notnull(x) else np.nan
    )
    selection_results = final_test_df[['FDate', 'SecCode', 'quantile', 'gx_hotspot']].sort_values(['FDate', 'quantile'])
    selection_results.to_csv(os.path.join(output_dir, "daily_quantile_selections.csv"), index=False)
    
    print(f"\n分析完成！IC 均值: {daily_ic.mean():.4f}, ICIR: {(daily_ic.mean()/daily_ic.std() if daily_ic.std() != 0 else 0):.4f}")
    print(f"结果已保存至: {output_dir}")

if __name__ == "__main__":
    run_gx_hotspot_analysis(DATA_PATH)
