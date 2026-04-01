import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from timing import market_timing
from core.Logger import logger

def run_test():
    """
    三角形收缩突破信号 + 当日涨幅分组测试
    1. 计算三角形收缩突破信号 (前5日波动控制 + 通道收缩判定 + T日突破)
    2. 使用中信一级/二级行业计算当日涨幅作为分组因子
    3. 在信号触发日，基于当日涨幅对行业进行分组
    4. 统计 T+20 累积收益
    """
    dp = DataProvider(base_data_path="D:/DATA")
    
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    start_date = "2013-01-01"
    end_date = "2026-03-20"

    # 计算前置数据开始日期 (前推1年)
    pre_start_date = (pd.to_datetime(start_date) - pd.DateOffset(years=1)).strftime("%Y-%m-%d")

    sector = 'ejhy'
    sector_path = f"INDEX/ZX/ZX_{sector}.csv"
    factor_name = f"gx_pit_mom_breakout_{sector}"
    output_path = f"results/gx_pit_mom/gx_pit_breakout/zx_{sector}"
    n_groups = 5 if sector == 'yjhy' else 10

    logger.info(f"正在加载基准数据: {index_file}")
    target_index = dp.get_ohlc_data(index_file, name="index_500")
    
    # 使用前置日期截取数据
    target_index = target_index.loc[pre_start_date:end_date]

    
    logger.info(f"正在加载行业价格数据: {sector_path}")
    sector_prices = dp.get_wide_table(sector_path)
    sector_prices = sector_prices.loc[pre_start_date:end_date]
    
    if target_index is None or sector_prices is None:
        logger.error("数据加载失败，请检查路径。")
        return

    sparse_data_path = "D:/DATA/SPARSE_SIGNAL"
    os.makedirs(sparse_data_path, exist_ok=True)
    
    signal_file = os.path.join(sparse_data_path, factor_name + ".parquet")

    if os.path.exists(signal_file):
        logger.info(f"检测到存在数据，跳过计算: {signal_file}")
        sparse_signal_df = pd.read_parquet(signal_file)
        # 确保索引是日期类型且对齐 backtest_dates
        sparse_signal_df.index = pd.to_datetime(sparse_signal_df.index)
        sparse_signal_df = sparse_signal_df[start_date : end_date]
        backtest_dates = sparse_signal_df.index
    else:
        logger.info("开始计算三角形收缩突破信号 (threshold=1%, window=5)...")
        # 对指数计算突破信号
        signal = market_timing.gx_pit_breakout(
            target_index, 
            threshold_pre=0.01, 
            threshold_break=0.01, 
            window=5
        )
        
        # 计算稀疏信号因子 (触发当日的行业涨幅)
        logger.info("计算触发当日的行业涨幅作为稀疏因子...")
        # 这里使用百分位收益率矩阵
        factor_df = sector_prices.pct_change()

        # 确保索引对齐
        common_dates = signal.index.intersection(sector_prices.index).intersection(factor_df.index)
        
        # 构造稀疏信号矩阵：只有在信号触发日，才保留因子值，其余为 NaN
        # 过滤掉 start_date 之前的数据，确保回测和保存从 start_date 开始
        backtest_dates = common_dates[common_dates >= start_date]
        
        sparse_signal_df = pd.DataFrame(index=backtest_dates, columns=sector_prices.columns)
        trigger_dates = signal.loc[backtest_dates][signal.loc[backtest_dates] == 1].index
        sparse_signal_df.loc[trigger_dates] = factor_df.loc[trigger_dates]
        sparse_signal_df.name = factor_name

        sparse_signal_df.to_parquet(signal_file)
        logger.info(f"稀疏信号已保存至: {signal_file}")
    
    sparse_signal_df = sparse_signal_df.loc[backtest_dates]
    
    sector_prices_test = sector_prices.loc[backtest_dates]
    target_index_test = target_index.loc[backtest_dates]

    # 运行稀疏测试
    tester = SparseSignalTester(
        signal_series=sparse_signal_df, 
        price_df=sector_prices_test, 
        benchmark_series=target_index_test['close'],
        period=20, 
        n_groups=n_groups,
        output_dir=output_path,
        data_folder=sparse_data_path
    )
    
    logger.info("开始三角形突破策略稀疏回测...")
    results = tester.run_backtest()
    
    if results.empty:
        logger.warning("回测结束，未捕捉到有效触发事件。")
        return
        
    logger.info("正在产出可视化图表及性能指标...")
    tester.plot_signals(target_index['close'],  asset_name='中证全指', title="三角形突破信号触发情况")
    tester.plot_annual_frequency(title="分年度信号数量")
    tester.export_trigger_log(filename="signal_trigger_dates.csv")
    tester.plot_group_returns(results, title="因子分组表现")
    
    tester.print_performance_report()

    print("\n" + "="*50)
    print("回测完成！分组平均收益摘要 (百分比):")
    summary = results.mean() * 100
    print(summary.to_string())
    print("="*50)
    print(f"结果已保存至目录: {tester.output_dir}")

if __name__ == "__main__":
    run_test()
