import pandas as pd
import numpy as np
import talib
import os
import glob
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt
# 中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# ----------------- 1. Configuration -----------------
DATA_FILE = Path("D:/DATA/all_stock_data_ts_20140102_20251231.csv")
START_DATE = "2014-01-01"
END_DATE = "2025-12-31"
STRATEGY_NAME = "砖型图策略"
STOCK_POOL_NAME = "all_stocks"
RESULTS_DIR = Path("d:/Dev/Quant/results/zxt_strategy") / STOCK_POOL_NAME
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def calculate_zxt_indicators(df):
    """
    计算砖型图策略所需的指标
    """
    if len(df) < 120:  # 确保有足够数据计算114日均线
        return None
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # 1. 知行多空线逻辑 (在此重命名为 zxt_line)
    m1, m2, m3, m4 = 14, 28, 57, 114
    ma1 = talib.SMA(close, timeperiod=m1)
    ma2 = talib.SMA(close, timeperiod=m2)
    ma3 = talib.SMA(close, timeperiod=m3)
    ma4 = talib.SMA(close, timeperiod=m4)
    zxt_line = (ma1 + ma2 + ma3 + ma4) / 4
    yellow_line_ok = close > zxt_line
    
    # 2. 砖型图数据计算
    # VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90;
    hhv4 = talib.MAX(high, timeperiod=4)
    llv4 = talib.MIN(low, timeperiod=4)
    denom = hhv4 - llv4
    denom[denom == 0] = 1e-8 # 避免除以0
    var1a = (hhv4 - close) / denom * 100 - 90
    
    # VAR2A:=SMA(VAR1A,4,1)+100; (SMA in TDX is EMA with alpha=1/N)
    # SMA(X,N,M) = (M*X + (N-M)*Y') / N
    # SMA(X,4,1) = (1*X + 3*Y') / 4 -> EMA(alpha=1/4)
    var2a = pd.Series(var1a).ewm(alpha=1/4, adjust=False).mean().values + 100
    
    # VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100;
    var3a = (close - llv4) / denom * 100
    
    # VAR4A:=SMA(VAR3A,6,1);
    var4a = pd.Series(var3a).ewm(alpha=1/6, adjust=False).mean().values
    
    # VAR5A:=SMA(VAR4A,6,1)+100;
    var5a = pd.Series(var4a).ewm(alpha=1/6, adjust=False).mean().values + 100
    
    # VAR6A:=VAR5A-VAR2A;
    var6a = var5a - var2a
    
    # 砖型图:=IF(VAR6A>4,VAR6A-4,0);
    brick = np.where(var6a > 4, var6a - 4, 0)
    
    # 3. 柱体红绿与高度逻辑
    # 今天红柱:=砖型图 > REF(砖型图,1);
    ref_brick1 = np.roll(brick, 1)
    ref_brick1[0] = 0
    today_red = brick > ref_brick1
    
    # 昨天绿柱:=REF(砖型图,1) < REF(砖型图,2);
    ref_brick2 = np.roll(brick, 2)
    ref_brick2[0:2] = 0
    yesterday_green = ref_brick1 < ref_brick2
    
    # 红柱高度:=砖型图 - REF(砖型图,1);
    red_height = brick - ref_brick1
    # 绿柱高度:=REF(砖型图,2) - REF(砖型图,1);
    green_height = ref_brick2 - ref_brick1
    # 高度达标:=红柱高度 >= 绿柱高度 * 2 / 3;
    height_ok = red_height >= (green_height * 2 / 3)
    
    # 4. 最终选股条件输出
    signal = yesterday_green & today_red & height_ok & yellow_line_ok
    
    # 合并结果
    df['signal'] = signal
    # 辅助计算出场价格
    # T+1 开盘即买，收盘价格
    # T+2 根据逻辑出场
    df['next_open'] = df['open'].shift(-1)
    df['next_close'] = df['close'].shift(-1)
    
    df['n2_open'] = df['open'].shift(-2)
    df['n2_high'] = df['high'].shift(-2)
    df['n2_close'] = df['close'].shift(-2)
    
    return df

def calculate_t2_exit_val(row):
    """
    计算 T+2 出场平均价格
    3%涨幅卖1/2, 5%再卖1/2 (即卖1/4), 7%或收盘清仓 (即卖1/4)
    """
    p_open = row['n2_open']
    p_high = row['n2_high']
    p_close = row['n2_close']
    
    if pd.isna(p_open) or pd.isna(p_high):
        return np.nan
        
    t3 = p_open * 1.03
    t5 = p_open * 1.05
    t7 = p_open * 1.07
    
    if p_high >= t7:
        # 合计: 1/2*t3 + 1/4*t5 + 1/4*t7
        return 0.5 * t3 + 0.25 * t5 + 0.25 * t7
    elif p_high >= t5:
        # 合计: 1/2*t3 + 1/4*t5 + 1/4*p_close
        return 0.5 * t3 + 0.25 * t5 + 0.25 * p_close
    elif p_high >= t3:
        # 合计: 1/2*t3 + 1/2*p_close
        return 0.5 * t3 + 0.5 * p_close
    else:
        return p_close

# ----------------- 2. Load and Process Full Market Data -----------------
if __name__ == '__main__':
    print(f'Loading full market data from {DATA_FILE}...')
    full_df = pd.read_csv(DATA_FILE)
    full_df['date'] = pd.to_datetime(full_df['date'])

    codes = full_df['code'].unique()
    all_signals = []
    ic_list = []

    print(f'Processing {len(codes)} stocks...')
    for code, group in tqdm(full_df.groupby('code')):
        group = group.sort_values('date')
        processed = calculate_zxt_indicators(group)
        
        if processed is None:
            continue
            
        # 计算持仓期收益 (用于 IC)
        processed['ret_combined'] = (processed.apply(calculate_t2_exit_val, axis=1) - processed['next_open']) / processed['next_open']
        
        # 记录 IC 数据
        ic_data = processed[['date', 'signal', 'ret_combined']].dropna()
        if not ic_data.empty:
            ic_list.append(ic_data)
            
        # 提取信号行用于回测
        signals = processed[processed['signal'] == True].copy()
        if not signals.empty:
            # 计算 T+1、T+2 收益及胜率基础
            signals['ret_t1'] = (signals['next_close'] - signals['next_open']) / signals['next_open']
            signals['exit_val_t2'] = signals.apply(calculate_t2_exit_val, axis=1)
            signals['ret_t2'] = (signals['exit_val_t2'] - signals['next_close']) / signals['next_close']
            signals['ret_combined'] = (signals['exit_val_t2'] - signals['next_open']) / signals['next_open']
            all_signals.append(signals[['date', 'code', 'ret_t1', 'ret_t2', 'ret_combined']])

    if not all_signals:
        print('No signals found.')
        exit()

    all_signals_df = pd.concat(all_signals)
    full_ic_data = pd.concat(ic_list)
    
    # 清洗数据：移除 inf 和极值
    full_ic_data = full_ic_data.replace([np.inf, -np.inf], np.nan).dropna(subset=['ret_combined'])
    # 过滤掉可能的错误数据 (如单日收益超过 100% 或低于 -50%)
    full_ic_data = full_ic_data[(full_ic_data['ret_combined'] < 0.5) & (full_ic_data['ret_combined'] > -0.5)]

    # 计算分组均值以核对 IC 方向
    mean_ret_true = full_ic_data[full_ic_data['signal'] == True]['ret_combined'].mean()
    mean_ret_all = full_ic_data['ret_combined'].mean()
    print(f"\nMean Return (Signal=True): {mean_ret_true:.6f}")
    print(f"Mean Return (All Market): {mean_ret_all:.6f}")
    
    daily_ic = full_ic_data.groupby('date').apply(lambda x: x['signal'].corr(x['ret_combined']))
    daily_ic.name = 'IC'

    # ----------------- 3. 保存年度 IC 统计结果 -----------------
    ic_df_for_stats = daily_ic.to_frame()
    ic_df_for_stats['year'] = pd.to_datetime(ic_df_for_stats.index).year
    
    annual_ic_stats = ic_df_for_stats.groupby('year')['IC'].agg([
        ('IC Mean', 'mean'),
        ('IC Std', 'std'),
        ('ICIR', lambda x: (x.mean() / x.std() * np.sqrt(252)) if x.std() != 0 else 0),
        ('Positive_IC_Ratio', lambda x: (x > 0).mean())
    ])
    
    annual_ic_stats.to_csv(RESULTS_DIR / "annual_ic_analysis.csv")
    print("\n--- Annual IC Analysis ---")
    print(annual_ic_stats)

    # ----------------- 3. Aggregation and Backtest -----------------
    # 按照日期汇总

    # 获取所有交易日历
    all_market_dates = sorted(full_df['date'].unique())
    date_to_idx = {d: i for i, d in enumerate(all_market_dates)}

    strategy_daily_returns = pd.Series(0.0, index=all_market_dates)

    for date, group in all_signals_df.groupby('date'):
        if date not in date_to_idx:
            continue
        idx = date_to_idx[date]
        
        if idx + 1 < len(all_market_dates):
            t1_date = all_market_dates[idx + 1]
            strategy_daily_returns[t1_date] += 0.5 * group['ret_t1'].mean()
            
        if idx + 2 < len(all_market_dates):
            t2_date = all_market_dates[idx + 2]
            strategy_daily_returns[t2_date] += 0.5 * group['ret_t2'].mean()

    # 筛选回测时段
    strategy_daily_returns = strategy_daily_returns[
        (strategy_daily_returns.index >= START_DATE) & (strategy_daily_returns.index <= END_DATE)
    ]

    # 筛选回测时段
    strategy_daily_returns = strategy_daily_returns[
        (strategy_daily_returns.index >= START_DATE) & (strategy_daily_returns.index <= END_DATE)
    ]

    # ----------------- 4. 基准对比与超额收益分析 -----------------
    benchmark_path = r'D:\DATA\INDEX\STOCK\csi300_index_20140102_20251231.csv'
    if os.path.exists(benchmark_path):
        print(f"\nLoading benchmark from {benchmark_path}...")
        bm_df = pd.read_csv(benchmark_path)
        # 强制转换日期格式为 YYYY-MM-DD 字符串
        bm_df['date'] = pd.to_datetime(bm_df['date']).dt.strftime('%Y-%m-%d')
        bm_df.set_index('date', inplace=True)
        # 只保留收盘价并计算收益率
        bm_returns = bm_df['close'].sort_index().pct_change().fillna(0)
        
        # 统一日期索引类型为字符串
        strategy_daily_returns.index = pd.to_datetime(strategy_daily_returns.index).strftime('%Y-%m-%d')
        
        common_dates = strategy_daily_returns.index.intersection(bm_returns.index)
        print(f"Intersection dates count: {len(common_dates)}")
        
        if len(common_dates) > 0:
            strat_rets_aligned = strategy_daily_returns.loc[common_dates]
            bm_rets_aligned = bm_returns.loc[common_dates]
            
            # 计算对比指标
            years = sorted(pd.to_datetime(common_dates).year.unique())
            perf_records = []
            for year in years:
                mask = pd.to_datetime(strat_rets_aligned.index).year == year
                y_strat = strat_rets_aligned[mask]
                y_bm = bm_rets_aligned[mask]
                
                if len(y_strat) > 0 and len(y_bm) > 0:
                    y_strat_ret = (1 + y_strat).prod() - 1
                    y_bm_ret = (1 + y_bm).prod() - 1
                    y_excess = y_strat_ret - y_bm_ret
                    
                    perf_records.append({
                        'Year': year,
                        'Strat_Ret': f"{y_strat_ret:.2%}",
                        'BM_Ret': f"{y_bm_ret:.2%}",
                        'Excess_Ret': f"{y_excess:.2%}",
                        'Strat_Sharpe': f"{np.sqrt(252) * y_strat.mean() / (y_strat.std() + 1e-9):.2f}"
                    })
            
            perf_df = pd.DataFrame(perf_records)
            perf_df.to_csv(RESULTS_DIR / "annual_performance_vs_csi300.csv", index=False)
            print("\n--- Annual Performance (Strategy vs CSI300) ---")
            print(perf_df.to_string(index=False))

            # 画超额对比图
            plt.figure(figsize=(10, 6))
            plt.plot(pd.to_datetime(strat_rets_aligned.index), (1+strat_rets_aligned).cumprod(), label=f'{STRATEGY_NAME}')
            plt.plot(pd.to_datetime(bm_rets_aligned.index), (1+bm_rets_aligned).cumprod(), label='CSI300')
            plt.plot(pd.to_datetime(strat_rets_aligned.index), (1 + (strat_rets_aligned - bm_rets_aligned)).cumprod(), label='Excess (Long-Short)', linestyle='--')
            plt.title(f'{STRATEGY_NAME} Performance vs CSI300')
            plt.legend()
            plt.grid(True)
            plt.savefig(RESULTS_DIR / "performance_vs_csi300.png")
            print(f"Performance chart saved to {RESULTS_DIR / 'performance_vs_csi300.png'}")
        else:
            print("Warning: No common dates found between strategy and benchmark.")
    else:
        print(f"Benchmark file not found: {benchmark_path}")

    # 保存每日选股
    daily_selection = all_signals_df.groupby('date')['code'].apply(lambda x: ','.join([str(i) for i in x])).reset_index()
    daily_selection.to_csv(RESULTS_DIR / "daily_selection.csv", index=False)
    print(f"Daily selection saved to {RESULTS_DIR / 'daily_selection.csv'}")

    net_value = (1 + strategy_daily_returns).cumprod()

    # ----------------- 5. 整体回测结果打印与绘图 -----------------
    print(f"\n--- {STRATEGY_NAME} Full Market Backtest Total Results ---")
    total_return = net_value.iloc[-1] - 1
    annual_return = (1 + total_return) ** (252 / len(net_value)) - 1
    sharpe = np.sqrt(252) * strategy_daily_returns.mean() / (strategy_daily_returns.std() + 1e-9)
    max_drawdown = (net_value / net_value.cummax() - 1).min()

    # 计算最多连续亏损日期
    is_loss = strategy_daily_returns < 0
    consecutive_loss = is_loss.groupby((is_loss != is_loss.shift()).cumsum()).cumsum()
    max_consecutive_loss_days = consecutive_loss.max()

    # 计算胜率
    win_rate_t1 = (all_signals_df['ret_t1'] > 0).mean()
    win_rate_combined = (all_signals_df['ret_combined'] > 0).mean()

    print(f"Total Return: {total_return:.2%}")
    print(f"Annual Return: {annual_return:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"T+1 Win Rate: {win_rate_t1:.2%}")
    print(f"Combined T+1&T+2 Win Rate: {win_rate_combined:.2%}")
    print(f"Max Drawdown: {max_drawdown:.2%}")
    print(f"Max Consecutive Loss Days: {max_consecutive_loss_days} days")
    print(f"IC Mean: {daily_ic.mean():.4f}")
    print(f"IC Std: {daily_ic.std():.4f}")
    print(f"ICIR: {(daily_ic.mean() / daily_ic.std() * np.sqrt(252)):.2f}")

    # 保存结果
    net_value.to_csv(RESULTS_DIR / f"{STRATEGY_NAME}_net_value.csv")
    daily_ic.to_csv(RESULTS_DIR / f"{STRATEGY_NAME}_daily_ic.csv")
    print(f"Results saved to {RESULTS_DIR}")

    # 画图
    plt.figure(figsize=(12, 10))
    
    # 转换索引为 datetime 以便正确绘制时间轴
    net_value_plot = net_value.copy()
    net_value_plot.index = pd.to_datetime(net_value_plot.index)
    
    # 净值图
    plt.subplot(2, 1, 1)
    
    # 构建包含指标的标签
    res_label = (f'{STRATEGY_NAME} Net Value\n'
                f'Annual Ret: {annual_return:.2%}, '
                f'Sharpe: {sharpe:.2f}, '
                f'MDD: {max_drawdown:.2%}')
    
    plt.plot(net_value_plot.index, net_value_plot.values, label=res_label)
    plt.title(f'{STRATEGY_NAME} Full Market Backtest')
    plt.xlabel('Date')
    plt.ylabel('Net Value')
    plt.legend(loc='upper left', fontsize='small')
    plt.grid(True, alpha=0.3)
    
    # IC 时序图
    plt.subplot(2, 1, 2)
    daily_ic_plot = daily_ic.copy()
    daily_ic_plot.index = pd.to_datetime(daily_ic_plot.index)
    
    plt.bar(daily_ic_plot.index, daily_ic_plot.values, alpha=0.3, label='Daily IC', color='gray', width=2)
    plt.plot(daily_ic_plot.rolling(20, min_periods=1).mean(), label='IC 20D MA', color='blue')
    plt.plot(daily_ic_plot.rolling(120, min_periods=1).mean(), label='IC 120D MA', color='red')
    plt.axhline(0, color='black', linestyle='--')
    plt.title('Strategy Signal IC (Correlation with Fwd Return)')
    plt.xlabel('Date')
    plt.ylabel('IC')
    plt.ylim(-0.2, 0.2) # 设置合理的IC展示范围
    plt.legend(loc='upper left', fontsize='small')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / f"{STRATEGY_NAME}_backtest_chart_with_ic.png")
    # plt.show()
