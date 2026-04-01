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
    稀疏信号 + 动量因子行业中性分组测试
    1. 使用中证 500 生成反弹掩码 (使用 D:/DATA 目录)
    2. 使用中信一级/二级行业计算动量因子
    3. 在反弹触发日，基于动量因子对行业进行分组
    4. 统计 T+20 累积收益
    """
    dp = DataProvider(base_data_path="D:/DATA")
    
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    start_date = "2013-01-01"
    end_date = "2026-03-18"

    # 计算前置数据开始日期 (前推1年)
    pre_start_date = (pd.to_datetime(start_date) - pd.DateOffset(years=1)).strftime("%Y-%m-%d")

    sector = 'ejhy'
    sector_path = f"INDEX/ZX/ZX_{sector}.csv"
    output_path = f"results/gx_pit_mom/gx_pit_rebound/zx_{sector}"
    factor_name = f"gx_pit_mom_rebound_{sector}"
    n_groups = 5 if sector == 'yjhy' else 10

    logger.info(f"正在加载基准数据: {index_file}")
    target_index = dp.get_ohlc_data(index_file, name="index_500")
    target_index = target_index.loc[pre_start_date:end_date]
    
    if target_index is None:
        logger.error(f"无法在 {index_file} 找到指数数据")
        return

    sector_prices = dp.get_wide_table(sector_path)
    sector_prices = sector_prices.loc[pre_start_date:end_date]

    sparse_folder = "D:/DATA/SPARSE_SIGNAL"
    os.makedirs(sparse_folder, exist_ok=True)
    
    signal_path = os.path.join(sparse_folder, factor_name + ".parquet")

    if os.path.exists(signal_path):
        logger.info(f"检测到存在数据，跳过计算: {signal_path}")
        sparse_signal_df = pd.read_parquet(signal_path)
        sparse_signal_df.index = pd.to_datetime(sparse_signal_df.index)
        sparse_signal_df = sparse_signal_df[start_date : end_date]
        backtest_dates = sparse_signal_df.index
    else:
        mask = market_timing.gx_pit_rebound(target_index, u=0.005, d=0.05)
        
        # 计算稀疏信号因子 (反弹当日减前20日日均涨跌幅)
        logger.info("计算反弹当日的稀疏因子因子...")
        
        # 确保索引对齐
        common_dates = mask.index.intersection(sector_prices.index)

        # 反弹因子：反弹当日涨跌幅 - 反弹前20日日均涨跌幅
        rets = sector_prices.pct_change()
        avg_prev_rets = rets.shift(1).rolling(20).mean()
        rebound_factor = rets - avg_prev_rets
        
        backtest_dates = common_dates[common_dates >= start_date]

        sparse_signal_df = pd.DataFrame(index=backtest_dates, columns=sector_prices.columns)
        trigger_dates = mask.loc[backtest_dates][mask.loc[backtest_dates] == 1].index
        sparse_signal_df.loc[trigger_dates] = rebound_factor.loc[trigger_dates]
        sparse_signal_df.name = factor_name

        sparse_signal_df.to_parquet(signal_path)
        logger.info(f"已保存稀疏信号到: {signal_path}")

    
    sparse_signal_df = sparse_signal_df.loc[backtest_dates]

    sector_prices_test = sector_prices.loc[backtest_dates]
    target_index_test = target_index.loc[backtest_dates]

    # 运行稀疏测试
    tester = SparseSignalTester(
        signal_series=sparse_signal_df, 
        price_df=sector_prices_test, 
        data_folder=sparse_folder,
        benchmark_series=target_index_test['close'],
        period=20, 
        n_groups=n_groups,
        output_dir=output_path
    )
    
    logger.info("开始稀疏信号回测...")
    results = tester.run_backtest()
    
    if results.empty:
        logger.warning("回测结束，未捕捉到有效触发事件。")
        return
        

    logger.info("正在产出可视化图表及性能指标...")
    tester.plot_signals(target_index["close"], asset_name="中证全指", title="大跌反弹信号触发情况")
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