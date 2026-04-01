import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
import os
import sys

# 设置支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_barra_factors(parquet_path):
    """
    由于 Parquet 文件中存在重复的 'date' 列名，需要特殊处理读取。
    """
    print(f"正在读取 Barra 因子文件: {parquet_path}")
    file = pq.ParquetFile(parquet_path)
    table = file.read()
    df = table.to_pandas()
    
    # 清理重复列名：Pandas 可能会将重复的 date 命名为 date 和 date.1
    # 我们保留第一个，删除多余的
    if 'date.1' in df.columns:
        df = df.drop(columns=['date.1'])
    elif df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated()]
    
    # 将 code 从索引重置为列
    if 'code' not in df.columns and df.index.name == 'code':
        df = df.reset_index()
        
    df['date'] = pd.to_datetime(df['date'])
    df['code'] = df['code'].astype(str).str.zfill(6)
    return df

def run_barra_fama_macbeth(parquet_path, data_path, factor_cols=['Beta', 'Momentum', 'ResidualVolatility']):
    """
    使用 Barra 因子和真实价格数据进行 Fama-MacBeth 检验
    """
    # 1. 加载 Barra 因子
    factors_df = load_barra_factors(parquet_path)
    
    # 2. 加载价格数据以计算收益率 (t+1)
    print(f"加载行情数据以计算收益率: {data_path}")
    prices_raw = pd.read_csv(data_path, usecols=['date', 'code', 'close'])
    prices_raw['date'] = pd.to_datetime(prices_raw['date'])
    prices_raw['code'] = prices_raw['code'].astype(str).str.zfill(6)
    
    # 准备宽表价格计算收益率
    prices_wide = prices_raw.pivot(index='date', columns='code', values='close')
    # 计算下期收益率 (Shift -1)
    returns_wide = prices_wide.pct_change().shift(-1)
    returns_df = returns_wide.stack().reset_index()
    returns_df.columns = ['date', 'code', 'next_ret']
    
    # 3. 合并因子和收益率
    print("合并因子与收益率数据...")
    analysis_df = pd.merge(factors_df, returns_df, on=['date', 'code'], how='inner')
    
    # 4. 执行 Fama-MacBeth 回归 (逐个因子测试)
    results_summary = []
    
    for factor in factor_cols:
        print(f"\n正在分析因子: {factor}")
        
        # 第一阶段：逐日回归
        def daily_reg(group):
            valid = group[[factor, 'next_ret']].dropna()
            if len(valid) < 30: return None
            X = sm.add_constant(valid[factor])
            y = valid['next_ret']
            model = sm.OLS(y, X).fit()
            return model.params[1] # 返回因子的系数 (Risk Premium)

        gammas = analysis_df.groupby('date').apply(daily_reg).dropna()
        
        if len(gammas) == 0:
            print(f"警告: 因子 {factor} 无有效回归结果。")
            continue
            
        # 第二阶段：统计推断
        mean_premium = gammas.mean()
        t_stat = mean_premium / (gammas.std() / np.sqrt(len(gammas)))
        p_val = sm.stats.ztest(gammas)[1]
        
        results_summary.append({
            'Factor': factor,
            'Mean Premium': mean_premium,
            'T-Stat': t_stat,
            'P-Value': p_val,
            'Count': len(gammas)
        })
        
        # 绘图：累积风险溢价
        plt.figure(figsize=(10, 5))
        plt.plot(gammas.index, gammas.cumsum(), label='累积风险溢价 (Cumulative Premium)')
        plt.axhline(0, color='black', linestyle='--', alpha=0.5)
        plt.title(f'Barra 因子 Fama-MacBeth 检验: {factor}')
        plt.xlabel('日期')
        plt.ylabel('累积溢价')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f"fama_macbeth_{factor}.png")

    # 输出结果报告
    summary_df = pd.DataFrame(results_summary)
    print("\n" + "="*50)
    print("Fama-MacBeth 因子检验最终汇总报告")
    print("="*50)
    print(summary_df.to_string(index=False))
    print("="*50)
    return summary_df

if __name__ == "__main__":
    BARRA_FILE = r'D:\DATA\Barra\barra_pv_factors.parquet'
    MARKET_FILE = r'D:\DATA\all_stock_data_ts_20140102_20251231.csv'
    
    if os.path.exists(BARRA_FILE) and os.path.exists(MARKET_FILE):
        run_barra_fama_macbeth(BARRA_FILE, MARKET_FILE)
    else:
        print("错误: 找不到必要的路径，请确认数据文件存在。")
