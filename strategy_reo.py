import pandas as pd
import numpy as np
import talib
import os
from pathlib import Path
from tqdm import tqdm
import matplotlib.pyplot as plt

# ----------------- 1. Configuration -----------------
DATA_FILE = Path("D:/DATA/all_stock_data_ts_20140102_20251231.csv")
START_DATE = "2014-01-01"
END_DATE = "2025-12-31"
STRATEGY_NAME = "REO 前一天红brick、long_term>85；当天白线在黄线上，long_term>=70，short_term<=30"
RESULTS_DIR = Path("d:/Dev/Quant/results/strategy_reo")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

HOLD_DAYS_MAX = 2

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
    
    # AA:=(REF(砖型图,1)<砖型图); (红柱判定)
    ref_brick = np.roll(brick, 1)
    ref_brick[0] = 0
    red_bar = (brick > ref_brick).astype(int)
    return red_bar, brick

def calculate_reo_indicators(df):
    if len(df) < 120: return None
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # 1. zxt_line (多空线 - 黄线) 和 white_line (双重EMA - 白线)
    ma14 = talib.SMA(close, 14)
    ma28 = talib.SMA(close, 28)
    ma57 = talib.SMA(close, 57)
    ma114 = talib.SMA(close, 114)
    df['yellow_line'] = (ma14 + ma28 + ma57 + ma114) / 4
    
    ema_inner = talib.EMA(close, 10)
    df['white_line'] = talib.EMA(ema_inner, 10)
    
    # 2. Reversal Factors (short_term, long_term)
    # 逻辑: 100*(C-LLV(L,N))/(HHV(C,N)-LLV(L,N))
    def calc_rev(c, l, n):
        llv_l = pd.Series(l).rolling(n, min_periods=1).min()
        hhv_c = pd.Series(c).rolling(n, min_periods=1).max()
        return 100 * (pd.Series(c) - llv_l) / (hhv_c - llv_l)

    df['short_term'] = calc_rev(close, low, 3)
    df['long_term'] = calc_rev(close, low, 21)
    
    # 3. brick (红绿柱) - 使用新参数
    red_long, brick_long = calculate_brick(df)
    df['red_long'] = red_long
    
    # 4. 逻辑判断
    # 当天白线在黄线上: df['white_line'] > df['yellow_line']
    # 前一天为红brick: df['red_long'].shift(1) == 1
    # 前一天long_term > 85: df['long_term'].shift(1) > 85
    # 当天long_term >= 70: df['long_term'] >= 70
    # 当天short_term <= 30: df['short_term'] <= 30
    
    cond_white_above_yellow = df['white_line'] > df['yellow_line']
    cond_prev_red_brick = df['red_long'].shift(1) == 1
    cond_prev_long_term_gt_85 = df['long_term'].shift(1) > 85
    cond_curr_long_term_ge_70 = df['long_term'] >= 70
    cond_curr_short_term_le_30 = df['short_term'] <= 30

    df['signal'] = (cond_white_above_yellow & 
                    cond_prev_red_brick & 
                    cond_prev_long_term_gt_85 & 
                    cond_curr_long_term_ge_70 & 
                    cond_curr_short_term_le_30)
    
    return df

def simulate_trade_for_stock(group):
    # 尾盘买入，次日尾盘卖出
    signals = group[group['signal'] == True].copy()
    all_trade_daily_rets = []
    all_trade_outcomes = []
    trade_durations = []
    
    for idx in signals.index:
        start_pos = group.index.get_loc(idx)
        # 次日尾盘卖出，所以至少需要 start_pos + 1
        if start_pos + 1 >= len(group): continue
        
        buy_price = group.iloc[start_pos]['close']
        
        exit_price = group.iloc[start_pos + 1]['close']
        
        # 计算单笔交易收益率（限制涨跌停）
        day_ret = (exit_price / buy_price) - 1
        day_ret = max(-0.2, min(0.2, day_ret))
        
        # 由于是 T+1 尾盘卖，收益计入次日
        all_trade_daily_rets.append({'date': group.iloc[start_pos + 1]['date'], 'ret': day_ret})
        all_trade_outcomes.append(day_ret)
        trade_durations.append(1)
                
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
        # 统计每日持仓个股数
        daily_stock_counts = results_df.groupby('date').size()
        avg_daily_stocks = daily_stock_counts.mean()
        
        # 统计每日平均收益
        # 资金分两份仓位（T日1份，T+1日1份），每次买入占用总资金的 1/2
        # 当天买入的权重是当天选股数量 n 的 1/(2n)
        # 每天单边换手 50%
        daily_perf = results_df.groupby('date')['ret'].mean()
        
        # 策略汇总：由于每天只卖出昨天的 50% 仓位并买入新的 50%
        # 这里的 daily_perf 是当天持有股票的平均收益，乘以 0.5 权重即为对总资产的贡献
        strat_returns = daily_perf * 0.5
        
        # 获取回测周期内的完整交易日序列
        all_dates = sorted(df['date'].unique())
        strat_series = strat_returns.reindex(all_dates).fillna(0)
        
        # 计算净值
        net_value = (1 + strat_series).cumprod()
        
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
            "指标名称": ["年化收益", "夏普比率", "最大回撤", "开仓胜率", "平均持股周期", "平均每日选股个数"],
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
        print(f"平均每日选股个数: {avg_daily_stocks:.2f} 个")
        
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
