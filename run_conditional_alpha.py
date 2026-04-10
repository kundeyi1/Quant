# 筛选trigger>0.8后检验env_factor的效果

import pandas as pd
import numpy as np
import os
import traceback
import matplotlib.pyplot as plt
from datetime import datetime
from core.DataManager import DataProvider
from core.FactorTester import FactorTester

# ==============================================================================
# 核心计算函数 (7步法条件因子分析)
# ==============================================================================

def compute_trigger_score(factors_df, trigger_list):
    """
    Step 1: 计算 trigger_score
    """
    triggers = factors_df[trigger_list]
    # 按日期进行横截面排名
    ranks = triggers.groupby("date").rank(pct=True)
    # 取均值作为综合 trigger 分数
    trigger_score = ranks.mean(axis=1)
    return trigger_score

def get_trigger_event(trigger_score, quantile=None, threshold=None):
    """
    Step 2: 定义 trigger_event
    支持两种模式：
    1. 分位数模式 (quantile): 例如 top 20% (quantile=0.8)
    2. 固定阈值模式 (threshold): 例如 score > 0.5
    """
    if quantile is not None:
        # 按日期分组计算分位数排名
        trigger_rank = trigger_score.groupby("date").rank(pct=True)
        return trigger_rank > quantile
    elif threshold is not None:
        # 固定阈值判断
        return trigger_score > threshold
    else:
        raise ValueError("Must provide either \"quantile\" or \"threshold\"")

def conditional_factor_test(factors_df, future_return, env_factor, trigger_event, min_samples=30):
    """
    Step 3-6: 筛选子样本并进行条件分层检验
    """
    # 确保索引名称正确
    factors_df.index.names = ["date", "stock"]
    
    # 合并数据：env_factor, trigger_event, future_return
    # 显式构造 DataFrame 以确保索引被正确继承
    data = pd.DataFrame({
        "factor": factors_df[env_factor],
        "trigger": trigger_event,
        "ret": future_return
    }).dropna()
    
    # 再次强制索引名称，防止 pd.DataFrame 初始化时丢失名称
    data.index.names = ["date", "stock"]

    # Step 3: 只保留 trigger_event == True 的样本
    df_trigger = data[data["trigger"] == True].copy()

    # Step 6: 稳定性控制 - 检查每日样本数
    sample_counts = df_trigger.groupby("date").size()
    valid_dates = sample_counts[sample_counts >= min_samples].index
    
    # 使用 .loc 过滤
    df_trigger = df_trigger.loc[df_trigger.index.get_level_values("date").isin(valid_dates)]

    if df_trigger.empty:
        return None, 0

    # Step 4: 对 env_factor 做条件分层 (在 trigger 子样本内进行)
    # 按日期对因子值进行重新排名 (rank)
    df_trigger["inner_rank"] = df_trigger.groupby("date")["factor"].rank(pct=True)
    
    # 将因子分成5组 (1-5)
    df_trigger["group"] = pd.cut(df_trigger["inner_rank"], 
                                bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0], 
                                labels=[1, 2, 3, 4, 5])

    # Step 5: 计算分层收益
    group_returns = df_trigger.groupby("group", observed=True)["ret"].mean()
    
    return group_returns, len(df_trigger)

def run_all_env_tests(factors_df, future_return, env_list, trigger_event, min_samples=30, output_dir=None):
    """
    Step 7: 结果汇总与通过 FactorTester 进行深度验证
    """
    results = []
    
    for env in env_list:
        try:
            print(f"  > Processing: {env} ...")
            # 1. 基础条件分组计算
            group_rets, total_samples = conditional_factor_test(
                factors_df, future_return, env, trigger_event, min_samples
            )
            
            if group_rets is not None:
                # 2. 构造 FactorTester 兼容数据并执行回测
                data_for_tester = pd.DataFrame({
                    "FDate": factors_df.index.get_level_values("date"),
                    "SecCode": factors_df.index.get_level_values("stock"),
                    "FValue": factors_df[env],
                    "trigger": trigger_event.values
                })
                # 核心步骤：只保留触发点的样本
                f_data_filtered = data_for_tester[data_for_tester["trigger"] == True][["FDate", "SecCode", "FValue"]]
                
                # 创建专题研究目录
                factor_report_dir = os.path.join(output_dir, env) if output_dir else f"./results/conditional_alpha/{env}"
                os.makedirs(factor_report_dir, exist_ok=True)
                
                # 初始化 FactorTester
                tester = FactorTester(
                    start_date=f_data_filtered["FDate"].min().strftime("%Y-%m-%d"),
                    end_date=f_data_filtered["FDate"].max().strftime("%Y-%m-%d"),
                    output_dir=factor_report_dir
                )
                
                # 注入收益数据
                tester.load_price_data("D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv")
                
                metrics, _ = tester.backtest(
                    factor_name=env,
                    factor_data=f_data_filtered,
                    interval_tag="D",
                    groups=5,
                    if_plot=True
                )
                
                m_dict = metrics.iloc[0].to_dict()
                results.append({
                    "factor_name": env,
                    "long_short": group_rets[5] - group_rets[1] if 5 in group_rets and 1 in group_rets else 0,
                    "RankIC": m_dict.get("RankIC", 0),
                    "RankICIR": m_dict.get("RankICIR", 0),
                    "samples": total_samples
                })
        except Exception as e:
            print(f"Error testing {env}: {e}")
            traceback.print_exc()
            
    # 转换为 DataFrame
    res_df = pd.DataFrame(results)
    if not res_df.empty:
        res_df = res_df.sort_values(by="long_short", ascending=False)
    return res_df

# ==============================================================================
# 数据加载与主流程
# ==============================================================================

def load_data(start_date, end_date, price_path, factor_path, factor_list):
    """加载因子数据和价格数据，并计算未来收益"""
    dp = DataProvider()
    
    # 1. 加载因子
    factors_pool = pd.DataFrame()
    for name in factor_list:
        file_path = os.path.join(factor_path, f"{name}.csv")
        f_val, flag = dp.load_file_data(file_path)
        
        # 处理索引
        if f_val.index.nlevels < 2:
            date_col, stock_col = f_val.columns[0], f_val.columns[1]
            f_val[date_col] = pd.to_datetime(f_val[date_col])
            f_val[stock_col] = f_val[stock_col].astype(str).str.zfill(6)
            f_val.set_index([date_col, stock_col], inplace=True)
        
        # 强制统一索引名称为 ["date", "stock"]
        f_val.index.names = ["date", "stock"]
        
        # 统一过滤时间
        mask = (f_val.index.get_level_values("date") >= pd.to_datetime(start_date)) & \
               (f_val.index.get_level_values("date") <= pd.to_datetime(end_date))
        factors_pool[name] = f_val.loc[mask].iloc[:, 0]
    
    factors_pool.dropna(inplace=True)
    
    # 2. 计算未来收益 (1d & 5d)
    tester = FactorTester(start_date, end_date)
    tester.load_price_data(price_path)
    
    f_ret_1d = tester.get_forward_returns(interval_tag="D").set_index(["FDate", "SecCode"])["r"]
    f_ret_5d = tester.get_forward_returns(interval_tag="5D").set_index(["FDate", "SecCode"])["r"]
    
    return factors_pool, f_ret_1d, f_ret_5d

if __name__ == "__main__":
    # 配置
    START_DATE = "2020-01-01"
    END_DATE = "2025-12-31"
    DATA_PATH = "D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv"
    FACTOR_PATH = "D:/DATA/FACTORS"
    
    TRIGGER_COLS = ["Vol_Explosion_Today", "Accel_Today", "Body_Strength_Today"]

    ENV_COLS = [
        "Trend_Slope_Lag1", "Position_Lag1", "Pullback_Depth_Lag1", 
        "Volat_Ratio_5_20_Lag1", "Volume_Ratio_5_20_Lag1", "Volat_Compression_Lag1"
    ]
    
    ALL_FACTORS = TRIGGER_COLS + ENV_COLS
    
    print(f"--- Loading Data ({START_DATE} to {END_DATE}) ---")
    try:
        factors_df, ret1, ret5 = load_data(START_DATE, END_DATE, DATA_PATH, FACTOR_PATH, ALL_FACTORS)
        
        # 计算 Trigger
        print("\n--- Calculating Triggers ---")
        trigger_score = compute_trigger_score(factors_df, TRIGGER_COLS)
        trigger_event_q = get_trigger_event(trigger_score, quantile=0.8)
        
        # 运行所有环境因子测试 (1d)
        print("\n--- Testing ENV factors (Condition: Trigger Quantile > 0.8, Return: 1d) ---")
        output_path_1d = "./results/conditional_alpha/1d"
        results_1d = run_all_env_tests(factors_df, ret1, ENV_COLS, trigger_event_q, output_dir=output_path_1d)
        
        print("\n[Return 1d Leaderboard (FactorTester Verified)]")
        if not results_1d.empty:
            print(results_1d[["factor_name", "long_short", "RankIC", "RankICIR", "samples"]].to_string(index=False))
        
        # 运行所有环境因子测试 (5d)
        print("\n--- Testing ENV factors (Condition: Trigger Quantile > 0.8, Return: 5d) ---")
        output_path_5d = "./results/conditional_alpha/5d"
        results_5d = run_all_env_tests(factors_df, ret5, ENV_COLS, trigger_event_q, output_dir=output_path_5d)
        
        print("\n[Return 5d Leaderboard (FactorTester Verified)]")
        if not results_5d.empty:
            print(results_5d[["factor_name", "long_short", "RankIC", "RankICIR", "samples"]].to_string(index=False))

    except Exception as e:
        print(f"Error in main loop: {e}")
        traceback.print_exc()