import pandas as pd
import numpy as np
import os
from core import logger, DataProvider, NavAnalyzer
from factors.technical_factors import TrendFactors

def run_b1_strategy(start_date='2023-01-01', end_date='2024-01-01'):
    logger.info(f"开始运行 B1 趋势挤压策略: {start_date} -> {end_date}")
    
    # 1. 数据准备
    provider = DataProvider()
    # 假设默认加载 CSI300 或全市场数据
    data = provider.load_data("all_stock_data.csv") 
    if data is None:
        logger.error("未能加载行情数据，请检查 D:/DATA 路径")
        return

    # 2. 因子计算
    tech_factors = TrendFactors()
    logger.info("正在计算技术指标: MA Compression & Symmetry...")
    
    # 计算均线挤压度
    data = tech_factors.calculate_ma_compression(data, windows=[5, 10, 20, 60])
    # 计算对称性因子
    data = tech_factors.calculate_symmetry(data, window_len=50)

    # 3. 策略逻辑：筛选挤压突破且对称因子较高的标的
    # 逻辑：ma_compression 越小代表均线越粘合，即将爆发
    # symmetry 越大代表波段上涨潜力越强
    data['signal'] = (data['ma_compression'] < 0.05) & (data['symmetry'] > 1.2)
    
    # 4. 生成持仓 (简单逻辑：每日等权持有信号股)
    # 此处仅为代码框架示例
    portfolio_daily_return = data[data['signal']].groupby('date')['close'].pct_change().mean()
    
    # 5. 回测分析
    analyzer = NavAnalyzer(portfolio_daily_return.dropna().cumsum())
    report = analyzer.generate_report()
    
    logger.info("B1 策略回测完成")
    print(report)
    
    # 保存结果
    output_dir = "results/strategy_b1"
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    portfolio_daily_return.to_csv(f"{output_dir}/strategy_b1_returns.csv")

if __name__ == "__main__":
    run_b1_strategy()
