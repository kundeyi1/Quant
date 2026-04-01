import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from tqdm import tqdm
import re

# ==========================================
# CONFIGURATION (No parser interaction)
# ==========================================
DATA_FILE = r'D:\DATA\all_stock_data_ts_20140102_20251231.csv'
ROE_FILE = r'D:\DATA\FUNDAMENTAL\ROE（平均）.xlsx'
OUTPUT_DIR = r'./results/roe_test_annual'
STRATEGY_NAME = 'ROE_Daily_Backtest'
ROE_THRESHOLD = 15.0  # Used for screening

def load_annual_roe(file_path):
    """
    Load ROE data with only one ROE per year (Annual Report).
    """
    print(f"Loading ROE data from {file_path}...")
    df = pd.read_excel(file_path)
    
    # Identify code column
    code_col = None
    for col in ['证券代码', 'code', '代码']:
        if col in df.columns:
            code_col = col
            break
            
    if not code_col:
        raise ValueError(f"Could not find code column in {file_path}")
        
    # Filter for annual report columns only
    # Example: '净资产收益率ROE(平均)\n[单位]%\n[报告期]2020年报'
    annual_cols = [c for c in df.columns if '年报' in c]
    
    # Map column names to year integers
    col_map = {code_col: 'code'}
    for col in annual_cols:
        match = re.search(r'\[报告期\](\d{4})', col)
        if match:
            year = int(match.group(1))
            col_map[col] = year
            
    df = df[list(col_map.keys())].rename(columns=col_map)
    
    # Format code (e.g., 1 -> 000001)
    def format_code(c):
        if pd.isna(c): return None
        s = str(c).split('.')[0]
        return s.zfill(6)
    
    df['code'] = df['code'].apply(format_code)
    return df

def run_roe_backtest():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Load Fundamental Data (Annual Only)
    roe_df = load_annual_roe(ROE_FILE)
    roe_df = roe_df.set_index('code')
    print(f"Loaded {len(roe_df)} stocks and columns: {roe_df.columns.tolist()}")
    
    # 2. Load Price Data
    print(f"Loading price data from {DATA_FILE}...")
    # Load with selected columns to optimize speed
    price_df = pd.read_csv(DATA_FILE, usecols=['date', 'code', 'close'])
    price_df['date'] = pd.to_datetime(price_df['date'])
    # Ensure code format matches (e.g. "000001")
    price_df['code'] = price_df['code'].apply(lambda x: str(x).zfill(6))
    
    dates = sorted(price_df['date'].unique())
    daily_groups = price_df.groupby('date')
    
    # 3. Backtest Loop
    strategy_nav = []
    current_portfolio = []
    last_nav = 1.0
    
    for i in tqdm(range(1, len(dates)), desc="Backtesting ROE Strategy"):
        prev_date = dates[i-1]
        curr_date = dates[i]
        
        # Rebalancing Logic: Yearly on May 1st (publication of annual reports)
        if curr_date.month == 5 and prev_date.month == 4:
            # Rebalance!
            # Use ROE from the previous year's annual report
            # e.g., On 2015-05-01, we use 2014 ROE data
            report_year = curr_date.year - 1
            
            if report_year in roe_df.columns:
                year_roe = roe_df[report_year].dropna()
                # Apply filter: ROE > THRESHOLD
                current_portfolio = year_roe[year_roe > ROE_THRESHOLD].index.tolist()
                print(f"\nRebalanced on {curr_date.date()}, Used {report_year} ROE, Selected {len(current_portfolio)} stocks.")
            else:
                # If data not available, hold previous portfolio
                pass
        
        # Calculate returns
        if not current_portfolio:
            strategy_nav.append(last_nav)
            continue
            
        try:
            prev_day_data = daily_groups.get_group(prev_date).set_index('code')['close']
            curr_day_data = daily_groups.get_group(curr_date).set_index('code')['close']
            
            # Match current portfolio with available market data
            valid_stocks = list(set(current_portfolio) & set(prev_day_data.index) & set(curr_day_data.index))
            
            if valid_stocks:
                daily_pct = (curr_day_data.loc[valid_stocks] / prev_day_data.loc[valid_stocks] - 1).mean()
                last_nav *= (1 + daily_pct)
        except Exception:
            pass
            
        strategy_nav.append(last_nav)
        
    # 4. Result Processing
    results_df = pd.DataFrame({
        'Strategy_NAV': strategy_nav
    }, index=dates[1:])
    
    # Calculate performance metrics
    total_days = len(results_df)
    total_ret = results_df['Strategy_NAV'].iloc[-1] - 1
    annual_ret = (1 + total_ret) ** (252 / total_days) - 1
    mdd = (results_df['Strategy_NAV'] / results_df['Strategy_NAV'].cummax() - 1).min()
    
    daily_rets = results_df['Strategy_NAV'].pct_change().dropna()
    sharpe = (daily_rets.mean() / daily_rets.std() * np.sqrt(252)) if len(daily_rets) > 0 else 0
    
    print("\n--- PERFORMANCE SUMMARY ---")
    print(f"Total Return:   {total_ret:.2%}")
    print(f"Annual Return:  {annual_ret:.2%}")
    print(f"Max Drawdown:   {mdd:.2%}")
    print(f"Sharpe Ratio:   {sharpe:.2f}")
    
    # 5. Plotting (Fixed Formatting)
    plt.figure(figsize=(12, 7))
    plt.plot(pd.to_datetime(results_df.index), results_df['Strategy_NAV'], 
             label=f'ROE > {ROE_THRESHOLD}% (AnnRet: {annual_ret:.2%}, MDD: {mdd:.2%})', 
             linewidth=2)
    
    plt.title('ROE Based Annual Rebalance Strategy')
    plt.xlabel('Date')
    plt.ylabel('NAV')
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.gcf().autofmt_xdate()
    
    plt.savefig(os.path.join(OUTPUT_DIR, 'roe_strategy_nav.png'))
    results_df.to_csv(os.path.join(OUTPUT_DIR, 'nav_results.csv'))
    print(f"\nOutputs saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    run_roe_backtest()
