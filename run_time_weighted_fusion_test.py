import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path
from core.DataManager import DataProvider
from core.SparseSignalTester import SparseSignalTester
from core.NumericalOperators import cs_rank
from core.Logger import logger

# 设置绘图风格
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 10
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def run_fusion_test(sector='ejhy'):
    """
    时点动量融合因子测试脚本
    1. 整合三种信号：三角形突破、反弹信号、行情转折点信号
    2. 使用 SparseSignalTester 的融合逻辑进行加权合成
    3. 绘制增强的可视化报表（多空曲线、超额收益柱状图、拼接绘图）
    """
    dp = DataProvider(base_data_path="D:/DATA")
    
    # 1. 基础数据加载
    index_file = "INDEX/STOCK/000985.CSI.xlsx"
    output_path = f"results/gx_pit_mom/time_weighted_fusion/zx_{sector}"
    sparse_signal_path = f"D:/DATA/SPARSE_SIGNAL"
    start_date = "2013-01-01"
    end_date = "2026-03-25"
    n_groups = 5 if sector == 'yjhy' else 10

    logger.info(f"加载基准数据: {index_file}")
    target_index = dp.get_ohlc_data(index_file)
    if target_index is None:
        logger.error("基准数据加载失败")
        return
    
    # 限定测试时间范围
    target_index = target_index.loc[start_date:end_date]
    
    logger.info(f"加载资产价格数据 (池子: {sector})...")
    if sector == 'all':
        sector_path = "STOCK/all_stock_data_ts_20140102_20251231.csv"
        raw_data = pd.read_csv(Path("D:/DATA") / sector_path, parse_dates=['date'])
        raw_data['code'] = raw_data['code'].astype(str).str.zfill(6)
        sector_prices = raw_data.pivot(index='date', columns='code', values='close').loc[start_date:end_date]
    else:
        sector_path = f"INDEX/ZX/ZX_{sector.upper()}.xlsx"
        sector_prices = dp.get_wide_table(sector_path)
        sector_prices = sector_prices.loc[start_date:end_date]

    if sector_prices is None or sector_prices.empty:
        logger.error(f"资产价格数据加载失败: {sector}")
        return
    
    # 2. 构造信号并配置因子目录
    if not os.path.exists(sparse_signal_path):
        logger.error(f"信号目录 {sparse_signal_path} 不存在")
        return

    # 自动识别目录下符合条件的 .parquet 文件：以 gx_pit_mom 开头，且包含策略类型和板块标识
    all_files = os.listdir(sparse_signal_path)
    signal_files = [f for f in all_files 
                    if f.startswith('gx_pit_mom_') and f.endswith('.parquet') and f'_{sector}_' in f]
    
    if not signal_files:
        logger.error(f"在指定目录下未找到匹配 (gx_pit_mom*_{sector}*.parquet) 的信号文件")
        return

    # 直接从信号文件加载稀疏矩阵
    logger.info("从磁盘信号文件直接提取稀疏因子数据...")
    signals_dict = {}
    
    for f in signal_files:
        signal_name = f.replace('.parquet', '')
        f_path = os.path.join(sparse_signal_path, f)
        
        # 读取稀疏信号数据
        s_df = pd.read_parquet(f_path)
        signals_dict[signal_name] = s_df
        logger.info(f"已加载信号: {signal_name}")

    combined_trigger_df = pd.concat([df.reindex(sector_prices.index).notna().any(axis=1).astype(int) for df in signals_dict.values()], axis=1)
    combined_trigger_df.columns = signals_dict.keys()

    # 索引对齐（以行业价格数据的日期为准）
    sector_prices = sector_prices.loc[combined_trigger_df.index]
    benchmark_series = target_index['close'].reindex(combined_trigger_df.index)

    # 3. 融合因子计算 (Time-Weighted Fusion with Rank)
    logger.info("开始计算时间加权融合因子...")
    half_life = 10
    
    # 所有涉及日期（对齐到 index 的时间范围）
    all_dates = sector_prices.index
    potential_trigger_dates = combined_trigger_df[combined_trigger_df.any(axis=1)].index
    
    # 筛选在测试时间范围内的触发日
    potential_trigger_dates = potential_trigger_dates[(potential_trigger_dates >= start_date) & (potential_trigger_dates <= end_date)]
    
    # 预计算所有触发点的 Rank 因子
    rank_cache = {}
    for name, s_df in signals_dict.items():
        # 对齐日期到行业价格索引
        s_df = s_df.reindex(all_dates)
        for d in potential_trigger_dates:
            row_data = s_df.loc[d]
            valid_mask = row_data.notna()
            if valid_mask.any():
                rank_cache[(d, name)] = cs_rank(row_data)

    # 遍历触发日，计算融合因子
    fused_records = {}
    for d in potential_trigger_dates:
        d_idx = all_dates.get_loc(d)
        start_idx = max(0, d_idx - half_life + 1)
        window_dates = all_dates[start_idx : d_idx + 1]
        
        # 使用 Series 方便处理截面数据，初始化为全 0
        combined_factor = pd.Series(0.0, index=sector_prices.columns)
        total_weight = 0.0
        
        found_any_signal = False
        # 检查窗口内所有信号
        for t in window_dates:
            n = d_idx - all_dates.get_loc(t)
            weight = 2 ** (-n / half_life)
            
            for name in signals_dict.keys():
                if (t, name) in rank_cache:
                    f_rank = rank_cache[(t, name)]
                    combined_factor += f_rank * weight
                    total_weight += weight
                    found_any_signal = True
        
        if found_any_signal and total_weight > 0:
            fused_records[d] = combined_factor / total_weight

    fused_factor_df = pd.DataFrame(fused_records).T.reindex(all_dates)
    
    # 确保列名是字符串，避免 parquet 导出错误
    fused_factor_df.columns = fused_factor_df.columns.astype(str)
    
    # 保存融合后的信号
    fused_file = os.path.join(sparse_signal_path, f"gx_pit_mom_fused_{sector}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.parquet")
    fused_factor_df.to_parquet(fused_file)
    logger.info(f"融合因子已保存至: {fused_file}")

    # 4. 运行 SparseSignalTester
    # 现在的 Tester 直接使用 fused_factor_df 作为输入，它既是信号也是因子
    tester = SparseSignalTester(
        signal_series=fused_factor_df, 
        price_df=sector_prices, 
        benchmark_series=benchmark_series,
        period=20, 
        n_groups=n_groups,
        output_dir=output_path
    )
    
    logger.info(f"开始时点动量融合回测... 触发总天数: {len(fused_records)}")
    results = tester.run_backtest()
    
    if results.empty:
        logger.warning("未捕捉到有效触发事件。")
        return
        
    # 5. 可视化与报告
    logger.info("生成可视化报表...")
    tester.plot_signals(benchmark_series, title="时点动量融合信号触发情况")
    tester.plot_annual_frequency(title="时点动量融合信号分年度频率")
    tester.plot_group_returns(results, title="时点动量融合信号分组表现")
    
    tester.print_performance_report()
    
    print("\n" + "="*50)
    print("时点动量融合回测完成！")
    print(f"结果目录: {tester.output_dir}")
    print("="*50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GX PIT Momentum Fusion Test")
    parser.add_argument("--sector", type=str, default="yjhy", choices=["yjhy", "ejhy", "all"], help="Sector definition")
    args = parser.parse_args()
    
    run_fusion_test(sector=args.sector)
