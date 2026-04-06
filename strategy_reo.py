import pandas as pd
import numpy as np
import talib
import os
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt

# ----------------- 1. Configuration -----------------
DATA_FILE = Path("D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv")
START_DATE = "2014-01-01"
END_DATE = "2025-12-31"
STRATEGY_NAME = "Brick_PrevLT40_GreenToRed_SizeGE1"
RESULTS_DIR = Path("d:/Dev/Quant/results/strategy_reo")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

HOLD_DAYS_MAX = 4

def is_standard_stock(code):
    s = str(code).zfill(6)
    # 沪主板(60), 深主板/中小板(00), 创业板(30), 科创板(68)
    return s.startswith(('60', '00', '30', '68'))

# 中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def calculate_brick(df):
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # VAR1A:=(HHV(HIGH,4)-CLOSE)/(HHV(HIGH,4)-LLV(LOW,4))*100-90;
    hhv4 = talib.MAX(high, timeperiod=4)
    llv4 = talib.MIN(low, timeperiod=4)
    denom = hhv4 - llv4
    denom[denom == 0] = 1e-8
    
    var1a = (hhv4 - close) / denom * 100 - 90
    # VAR2A:=SMA(VAR1A,4,1)+100; (Note: SMA(X,N,1) in TongDaxin is exponential moving average with alpha=1/N)
    var2a = pd.Series(var1a).ewm(alpha=1/4, adjust=False).mean().values + 100
    
    # VAR3A:=(CLOSE-LLV(LOW,4))/(HHV(HIGH,4)-LLV(LOW,4))*100;
    var3a = (close - llv4) / denom * 100
    # VAR4A:=SMA(VAR3A,6,1);
    var4a = pd.Series(var3a).ewm(alpha=1/6, adjust=False).mean().values
    # VAR5A:=SMA(VAR4A,6,1)+100;
    var5a = pd.Series(var4a).ewm(alpha=1/6, adjust=False).mean().values + 100
    
    # VAR6A:=VAR5A-VAR2A;
    # 砖型图:=IF(VAR6A>4,VAR6A-4,0)
    var6a = var5a - var2a
    brick = np.where(var6a > 4, var6a - 4, 0)
    
    # 砖型图的具体数值即为柱子的“收盘值”
    # AA:=(REF(砖型图,1)<砖型图); (红柱判定: 今天比昨天大)
    ref_brick = np.roll(brick, 1)
    ref_brick[0] = 0
    red_bar = (brick > ref_brick).astype(int)
    
    # BB:=(REF(砖型图,1)>砖型图); (绿柱判定: 今天比昨天小)
    green_bar = (brick < ref_brick).astype(int)
    
    # 柱体长度定义：ABS(砖型图 - REF(砖型图, 1))
    bar_size = np.abs(brick - ref_brick)
    ref_bar_size = np.roll(bar_size, 1)
    ref_bar_size[0] = 0
    
    # 用户要求：
    # 1. 前一天砖型图数值 (REF(brick, 1)) < 40
    # 2. 前一天是绿柱 (REF(green_bar, 1) == 1)
    # 3. 当天是红柱 (red_bar == 1)
    # 4. 当天红柱长度 > 前一天绿柱长度的 2/3
    ref_green_bar = np.roll(green_bar, 1)
    ref_green_bar[0] = 0
    
    brick_buy_signal = (ref_brick < 40) & (ref_green_bar == 1) & (red_bar == 1) & (bar_size > (ref_bar_size))
    
    return red_bar, green_bar, brick, bar_size, brick_buy_signal

def calculate_reo_indicators(df):
    if len(df) < 120: return None
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # KDJ Calculation (Standard KDJ: RSV=(C-LLV(L,9))/(HHV(H,9)-LLV(L,9))*100, K=SMA(RSV,3,1), D=SMA(K,3,1), J=3*K-2*D)
    df['k'], df['d'] = talib.STOCH(high, low, close, 
                                  fastk_period=9, slowk_period=3, slowk_matype=0, 
                                  slowd_period=3, slowd_matype=0)
    df['j'] = 3 * df['k'] - 2 * df['d']
    
    # Re-calculate brick with new logic
    red_bar, green_bar, brick, bar_size, brick_buy_signal = calculate_brick(df)
    df['brick'] = brick
    df['bar_size'] = bar_size
    df['green_bar'] = green_bar
    df['brick_buy_signal'] = brick_buy_signal
    
    # 4. Logic judgment: KDJ J < 13 & Brick Buy Signal
    df['signal'] = (df['j'] < 13) & df['brick_buy_signal']
    
    return df

def simulate_trade_for_stock(group):
    # 尾盘买入，最多持有4天，且如果砖型图翻绿就卖出
    signals = group[group['signal'] == True].copy()
    all_trade_daily_rets = []
    all_trade_outcomes = []
    trade_durations = []
    
    for idx in signals.index:
        start_pos = group.index.get_loc(idx)
        if start_pos + 1 >= len(group): continue
        
        buy_price = group.iloc[start_pos]['close']
        hold_days = 0
        exit_pos = start_pos + 1
        
        # Hold max 4 days
        for day in range(1, 5):
            curr_pos = start_pos + day
            if curr_pos >= len(group):
                exit_pos = len(group) - 1
                break
            
            # Condition: If brick turns green (green_bar == 1)
            if group.iloc[curr_pos]['green_bar'] == 1:
                exit_pos = curr_pos
                break
            
            # Max hold 4 days
            if day == 4:
                exit_pos = curr_pos
                break
        
        exit_price = group.iloc[exit_pos]['close']
        hold_days = exit_pos - start_pos
        
        # Calculation: total return for this trade
        total_ret = (exit_price / buy_price) - 1
        total_ret = max(-0.2, min(0.2, total_ret))
        
        # Every day of holding gets a segment of total_ret for simplicity
        for d in range(1, hold_days + 1):
            if start_pos + d < len(group):
                all_trade_daily_rets.append({
                    'date': group.iloc[start_pos + d]['date'], 
                    'start_date': group.iloc[start_pos]['date'], # Signal day for weighting
                    'ret': total_ret / hold_days 
                })
        
        all_trade_outcomes.append(total_ret)
        trade_durations.append(hold_days)
                
    return all_trade_daily_rets, all_trade_outcomes, trade_durations

if __name__ == "__main__":
    print("Loading data...")
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    # 过滤标准 A 股代码
    df['code_str'] = df['code'].astype(str).str.zfill(6)
    df = df[df['code_str'].str.startswith(('60', '00', '30', '68'))]
    unique_codes = df['code'].unique()
    print(f"Standard A-shares found: {len(unique_codes)}")
    
    all_rets = []
    all_outcomes = []
    all_durations = []
    all_signals = [] # 用于记录每日选股结果
    
    print("Processing stocks...")
    for code, group in tqdm(df.groupby('code')):
        group = group.sort_values('date').reset_index(drop=True)
        processed = calculate_reo_indicators(group)
        if processed is not None:
            # 记录选股信号 (signal == True 的行)
            sigs = processed[processed['signal'] == True][['date', 'code', 'close']].copy()
            if not sigs.empty:
                all_signals.append(sigs)

            stock_rets, stock_outcomes, stock_durations = simulate_trade_for_stock(processed)
            all_rets.extend(stock_rets)
            all_outcomes.extend(stock_outcomes)
            all_durations.extend(stock_durations)
            
    if not all_rets:
        print("No signals found.")
    else:
        # 保存每日选股结果
        if all_signals:
            signals_df = pd.concat(all_signals).sort_values(['date', 'code'])
            signals_df.to_csv(RESULTS_DIR / "daily_stock_selections.csv", index=False, encoding='utf-8-sig')
            print(f"Daily selections saved to {RESULTS_DIR / 'daily_stock_selections.csv'}")

        results_df = pd.DataFrame(all_rets)
        
        # 1. Count signals per day for weight allocation (1/4 total daily allocation)
        daily_signal_counts = signals_df.groupby('date').size().rename('n_start')
        
        # 2. Merge n_start onto results_df to know how to weight each stock's contribution
        # We merge on 'start_date' which is the day the signal was generated
        results_df = results_df.merge(daily_signal_counts, left_on='start_date', right_index=True, how='left')
        
        # 3. Calculate daily contribution: ret * (0.25 / n_start)
        # This assumes each day's selection set gets 1/4 of total capital, split equally among n stocks.
        results_df['weighted_ret'] = results_df['ret'] * (0.25 / results_df['n_start'])
        
        # 4. Aggregate daily returns (sum weighted_ret for each 'date' which is the return date)
        strat_returns = results_df.groupby('date')['weighted_ret'].sum()
        
        # 获取回测周期内的完整交易日序列
        all_dates = sorted(df['date'].unique())
        strat_series = strat_returns.reindex(all_dates).fillna(0)
        
        # 计算净值
        net_value = (1 + strat_series).cumprod()
        
        # 统计每日持仓个股数
        daily_stock_counts = results_df.groupby('date').size()
        avg_daily_stocks = daily_stock_counts.mean() if not daily_stock_counts.empty else 0

        # 指标计算
        total_ret = net_value.iloc[-1] - 1
        ann_ret = (1 + total_ret)**(252/len(net_value)) - 1
        sharpe = np.sqrt(252) * strat_series.mean() / (strat_series.std() + 1e-9)
        mdd = (net_value / net_value.cummax() - 1).min()
        
        # 计算胜率
        win_rate = np.mean(np.array(all_outcomes) > 0) if all_outcomes else 0
        
        # 计算平均持股周期
        avg_hold_days = np.mean(all_durations) if all_durations else 0
        
        # 保存指标到表格
        metrics = {
            "指标名称": ["年化收益", "夏普比率", "最大回撤", "开仓胜率", "平均持股周期", "平均每日持仓个数"],
            "数值": [f"{ann_ret:.2%}", f"{sharpe:.2f}", f"{mdd:.2%}", f"{win_rate:.2%}", f"{avg_hold_days:.2f}天", f"{avg_daily_stocks:.2f}个"]
        }
        metrics_df = pd.DataFrame(metrics)
        metrics_df.to_csv(RESULTS_DIR / "strategy_metrics.csv", index=False, encoding='utf-8-sig')
        print(f"Metrics saved to {RESULTS_DIR / 'strategy_metrics.csv'}")

        print(f"\n--- {STRATEGY_NAME} ---")
        print(f"年化收益: {ann_ret:.2%}")
        print(f"夏普比率: {sharpe:.2f}")
        print(f"最大回撤: {mdd:.2%}")
        print(f"开仓胜率: {win_rate:.2%}")
        print(f"平均持股周期: {avg_hold_days:.2f} 天")
        print(f"平均每日持仓个数: {avg_daily_stocks:.2f} 个")
        
        # 画图
        plt.figure(figsize=(12, 6))
        # 图例仅保留曲线名称，详细指标已记录在 metrics.csv
        plt.plot(net_value, label=f"{STRATEGY_NAME}净值曲线")
        plt.title(f"{STRATEGY_NAME} (个股收益累计)")
        plt.legend(loc='upper left', fontsize='medium')
        plt.grid(True, alpha=0.3)
        plt.xlabel('日期')
        plt.ylabel('累计净值')
        plt.savefig(RESULTS_DIR / "reo_nv_chart.png")
        print(f"Chart saved to {RESULTS_DIR}")
