import pandas as pd
import numpy as np
import statsmodels.api as sm
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import os

# 设置绘图风格
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def load_parquet_with_dup_cols(path):
    """处理 Parquet 中重复的 date 列和 code 索引"""
    file = pq.ParquetFile(path)
    table = file.read()
    df = table.to_pandas()
    # 删除重复列
    df = df.loc[:, ~df.columns.duplicated()]
    # 重置 code 索引
    if 'code' not in df.columns and df.index.name == 'code':
        df = df.reset_index()
    df['date'] = pd.to_datetime(df['date'])
    df['code'] = df['code'].astype(str).str.zfill(6)
    return df

def run_barra_attribution(target_factor_path, barra_path, market_path):
    """
    使用 Barra 风格因子归因目标因子 (gx_hotspot)
    """
    print("正在加载数据进行归因分析...")
    
    # 1. 加载目标因子 (gx_hotspot)
    if not os.path.exists(target_factor_path):
        print(f"错误: 找不到目标因子文件 {target_factor_path}")
        return
        
    target_df = pd.read_csv(target_factor_path)
    target_df['date'] = pd.to_datetime(target_df['date'])
    target_df['code'] = target_df['code'].astype(str).str.zfill(6)
    
    # 2. 加载 Barra 因子
    barra_df = load_parquet_with_dup_cols(barra_path)
    
    # 3. 加载行情数据以计算下期收益率 (T+1)
    print(f"正在加载行情数据以计算收益率: {market_path}")
    market_df = pd.read_csv(market_path, usecols=['date', 'code', 'close'])
    market_df['date'] = pd.to_datetime(market_df['date'])
    market_df['code'] = market_df['code'].astype(str).str.zfill(6)
    
    # 转换为宽表计算收益率
    prices_wide = market_df.pivot(index='date', columns='code', values='close')
    returns_wide = prices_wide.pct_change().shift(-1)
    returns_stack = returns_wide.stack().reset_index()
    returns_stack.columns = ['date', 'code', 'next_ret']
    
    # 4. 合并数据 (因子暴露 + 下期收益率)
    print("正在合并因子暴露与收益率数据...")
    data = pd.merge(
        target_df[['date', 'code', 'gx_hotspot']], 
        barra_df, 
        on=['date', 'code'], 
        how='inner'
    )
    data = pd.merge(data, returns_stack, on=['date', 'code'], how='inner')
    data = data.dropna()
    
    # 5. 执行 Fama-MacBeth 归因回归
    # next_ret = gamma_0 + gamma_target * gx_hotspot + gamma_barra1 * Barra1 + ...
    barra_cols = ['Beta', 'Momentum', 'ResidualVolatility']
    all_factors =  barra_cols + ['gx_hotspot']
    
    print(f"执行 Fama-MacBeth 风格偏离回归：next_ret ~ constant + {' + '.join(all_factors)}")
    
    results = []
    dates = sorted(data['date'].unique())
    
    for d in dates:
        day_data = data[data['date'] == d]
        if len(day_data) < 50: continue
        
        X = day_data[all_factors]
        # 因子自变量进行截面标准化 (z-score)
        X = (X - X.mean()) / X.std()
        X = sm.add_constant(X)
        
        y = day_data['next_ret']
        
        try:
            model = sm.OLS(y, X).fit()
            params = model.params.to_dict()
            params['date'] = d
            params['rsquared'] = model.rsquared
            results.append(params)
        except:
            continue
            
    res_df = pd.DataFrame(results).set_index('date')
    
    # 6. 统计结果
    summary = []
    for col in all_factors:
        series = res_df[col].dropna()
        mean_premium = series.mean()
        t_stat = mean_premium / (series.std() / np.sqrt(len(series)))
        summary.append({
            'Factor': col,
            'Mean Premium (bps)': f"{mean_premium*10000:.4f}",
            'T-Stat': f"{t_stat:.4f}",
            'Win Rate': f"{(series > 0).mean()*100:.2f}%"
        })
    
    print("\n" + "="*50)
    print("Barra 风格因子归因与因子溢价检验 (Fama-MacBeth)")
    print("="*50)
    print(pd.DataFrame(summary).to_string(index=False))
    print("-" * 50)
    print(f"平均 R2: {res_df['rsquared'].mean():.4f}")
    print("="*50)

    # 7. 绘图：累积收益贡献
    plt.figure(figsize=(12, 7))
    for col in all_factors:
        label = f'gx_hotspot (Pure)' if col == 'gx_hotspot' else f'Barra: {col}'
        plt.plot(res_df.index, res_df[col].cumsum(), label=label, linewidth=2)
    
    plt.axhline(0, color='black', linestyle='--', alpha=0.5)
    plt.title('Hotspot 因子 vs Barra 风格因子：剥离风格后的累积多头收益', fontsize=14)
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('累积风险溢价', fontsize=12)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3, linestyle='--')
    output_img = "gx_hotspot_barra_attribution_fm.png"
    plt.savefig(output_img, dpi=300)
    print(f"\n归因图表已保存至: {output_img}")

if __name__ == "__main__":
    TARGET_PATH = r'D:\DATA\FACTORS\gx_hotspot_v1_2019-12-31_2025-12-31.csv'
    BARRA_PATH = r'D:\DATA\Barra\barra_pv_factors.parquet'
    MARKET_PATH = r'D:\DATA\all_stock_data_ts_20140102_20251231.csv'
    
    run_barra_attribution(TARGET_PATH, BARRA_PATH, MARKET_PATH)

    # 绘制暴露时间序列
    plt.figure(figsize=(12, 6))
    for col in barra_cols:
        plt.plot(daily_coeffs.index, daily_coeffs[col].rolling(20).mean(), label=f'{col} Exposure (20D MA)')
    
    plt.title('gx_hotspot 在 Barra 风格因子上的暴露演变')
    plt.axhline(0, color='black', lw=1, ls='--')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('gx_hotspot_barra_attribution.png')
    print("暴露演变图已保存至: gx_hotspot_barra_attribution.png")

if __name__ == "__main__":
    # 使用你之前生成的 gx_hotspot 因子文件
    GX_PATH = r'D:\DATA\FACTORS\gx_hotspot_v3_2020-01-01_2025-12-31.csv'
    BARRA_PATH = r'D:\DATA\Barra\barra_pv_factors.parquet'
    
    run_barra_attribution(GX_PATH, BARRA_PATH)
