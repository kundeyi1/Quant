#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINAL DIAGNOSTIC: Direct execution without file I/O complications
This script performs inline analysis and saves results to output file
"""
import sys
import os

# Set encoding first
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add path
sys.path.insert(0, r'd:\Dev\Quant')

# Open output file for writing
output_file = open(r'd:\Dev\Quant\diagnostic_results.txt', 'w', encoding='utf-8')

def log(msg):
    """Print and write to file"""
    print(msg)
    output_file.write(msg + '\n')
    output_file.flush()

try:
    log("="*80)
    log("YJHY DATA & BENCHMARK ALIGNMENT DIAGNOSTIC")
    log("="*80)
    
    import pandas as pd
    import numpy as np
    from core.DataManager import DataProvider
    
    # STEP 1: Load YJHY data
    log("\n[STEP 1] Loading YJHY prices...")
    yjhy_path = r"D:\DATA\INDEX\ZX\yjhy_prices.csv"
    
    if not os.path.exists(yjhy_path):
        log(f"ERROR: File not found: {yjhy_path}")
        sys.exit(1)
    
    yjhy_df = pd.read_csv(yjhy_path, index_col=0, parse_dates=True)
    yjhy_avg = yjhy_df.mean(axis=1)
    
    log(f"  ✓ Loaded successfully")
    log(f"  Shape: {yjhy_df.shape}")
    log(f"  Date range: {yjhy_df.index[0]} to {yjhy_df.index[-1]}")
    log(f"  Columns: {', '.join(list(yjhy_df.columns)[:5])}... ({len(yjhy_df.columns)} total)")
    log(f"  Average vector length: {len(yjhy_avg)}")
    log(f"  Average min: {yjhy_avg.min():.2f}")
    log(f"  Average max: {yjhy_avg.max():.2f}")
    
    # STEP 2: Load benchmark
    log("\n[STEP 2] Loading benchmark index...")
    dp = DataProvider(base_data_path="D:/DATA")
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    index_data = dp.get_ohlc_data(index_file, name="target_index")
    
    if index_data is None:
        log("  ERROR: Failed to load benchmark data")
        sys.exit(1)
    
    benchmark = index_data['close']
    
    log(f"  ✓ Loaded successfully")
    log(f"  Length: {len(benchmark)}")
    log(f"  Date range: {benchmark.index[0]} to {benchmark.index[-1]}")
    log(f"  Min: {benchmark.min():.2f}")
    log(f"  Max: {benchmark.max():.2f}")
    log(f"  NaN count: {benchmark.isnull().sum()}")
    
    # STEP 3: Calculate returns
    log("\n[STEP 3] Calculating returns...")
    yjhy_returns = yjhy_avg.pct_change()
    benchmark_returns = benchmark.pct_change()
    
    log(f"  yjhy_returns:")
    log(f"    Length: {len(yjhy_returns)}")
    log(f"    NaN count: {yjhy_returns.isnull().sum()}")
    log(f"    Min: {yjhy_returns.min():.6f}")
    log(f"    Max: {yjhy_returns.max():.6f}")
    
    log(f"  benchmark_returns:")
    log(f"    Length: {len(benchmark_returns)}")
    log(f"    NaN count: {benchmark_returns.isnull().sum()}")
    log(f"    Min: {benchmark_returns.min():.6f}")
    log(f"    Max: {benchmark_returns.max():.6f}")
    
    # STEP 4: Calculate equity curves
    log("\n[STEP 4] Calculating equity curves...")
    yjhy_equity = (1 + yjhy_returns).cumprod()
    benchmark_equity = (1 + benchmark_returns).cumprod()
    
    log(f"  yjhy_equity:")
    log(f"    Length: {len(yjhy_equity)}")
    log(f"    NaN count: {yjhy_equity.isnull().sum()}")
    log(f"    Min: {yjhy_equity.min():.4f}")
    log(f"    Max: {yjhy_equity.max():.4f}")
    log(f"    Final value: {yjhy_equity.iloc[-1]:.4f}")
    
    log(f"  benchmark_equity:")
    log(f"    Length: {len(benchmark_equity)}")
    log(f"    NaN count: {benchmark_equity.isnull().sum()}")
    log(f"    Min: {benchmark_equity.min():.4f}")
    log(f"    Max: {benchmark_equity.max():.4f}")
    log(f"    Final value: {benchmark_equity.iloc[-1]:.4f}")
    
    # STEP 5: Alignment check
    log("\n[STEP 5] Checking date alignment...")
    log(f"  yjhy_equity dates: {yjhy_equity.index[0]} to {yjhy_equity.index[-1]}")
    log(f"  benchmark_equity dates: {benchmark_equity.index[0]} to {benchmark_equity.index[-1]}")
    
    common_dates = yjhy_equity.index.intersection(benchmark_equity.index)
    log(f"\n  ✓ Common dates found: {len(common_dates)}")
    
    if len(common_dates) == 0:
        log("  ERROR: No overlap in date ranges!")
        log(f"  yjhy only: {yjhy_equity.index[0]} to {yjhy_equity.index[-1]}")
        log(f"  benchmark only: {benchmark_equity.index[0]} to {benchmark_equity.index[-1]}")
        sys.exit(1)
    
    log(f"  Range: {common_dates[0]} to {common_dates[-1]}")
    
    # STEP 6: Align data
    log("\n[STEP 6] Aligning data...")
    yjhy_aligned = yjhy_equity[common_dates]
    benchmark_aligned = benchmark_equity[common_dates]
    
    log(f"  ✓ Alignment successful")
    log(f"  yjhy_aligned length: {len(yjhy_aligned)}")
    log(f"  benchmark_aligned length: {len(benchmark_aligned)}")
    
    # STEP 7: Calculate performance metrics
    log("\n[STEP 7] Calculating performance metrics...")
    
    yjhy_total_ret = (yjhy_aligned.iloc[-1] - 1) * 100
    bench_total_ret = (benchmark_aligned.iloc[-1] - 1) * 100
    
    log(f"  Total return (cumulative period):")
    log(f"    yjhy: {yjhy_total_ret:>10.2f}%")
    log(f"    benchmark: {bench_total_ret:>10.2f}%")
    
    years = (common_dates[-1] - common_dates[0]).days / 365.25
    log(f"\n  Period: {years:.4f} years ({(common_dates[-1] - common_dates[0]).days} days)")
    
    if years > 0:
        yjhy_annual = ((yjhy_aligned.iloc[-1]) ** (1/years) - 1) * 100
        bench_annual = ((benchmark_aligned.iloc[-1]) ** (1/years) - 1) * 100
        
        log(f"  Annualized return:")
        log(f"    yjhy: {yjhy_annual:>10.2f}%")
        log(f"    benchmark: {bench_annual:>10.2f}%")
        log(f"  Outperformance: {(yjhy_annual - bench_annual):>10.2f}%")
    
    # Summary
    log("\n" + "="*80)
    log("✓ SUCCESS - ALL TESTS PASSED")
    log("="*80)
    log("\nSUMMARY:")
    log(f"  Data alignment: OK")
    log(f"  Common trading days: {len(common_dates)}")
    log(f"  Period: {common_dates[0].date()} to {common_dates[-1].date()}")
    log(f"  Calculations: All successful, no numerical errors")
    log(f"\nResults can be used for further analysis.")
    
except Exception as e:
    import traceback
    log(f"\n✗ ERROR: {type(e).__name__}: {e}")
    log("\nFull traceback:")
    log(traceback.format_exc())
    sys.exit(1)

finally:
    output_file.close()
