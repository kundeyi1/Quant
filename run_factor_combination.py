import pandas as pd
import numpy as np
import os
import sys
import traceback
from datetime import datetime
from core.DataManager import DataProvider
from core.FactorTester import FactorTester
from factors.combination import FactorCombiner
# ==============================================================================
# 1. 实验核心配置区域 (Centralized Dashboard)
# ==============================================================================
EXP_CONFIG = {
    "start_date": "2018-01-01",
    "end_date": "2025-12-31",
    "data_path": "D:/DATA/STOCK/all_stock_data_ts_20140102_20251231.csv",
    
    # 手动指定因子方向: 1(正向), -1(反向)
    "direction_map": {
        "Trend_Slope_Lag1": 1,
        "Position_Lag1": -1,
        "Pullback_Depth_Lag1": 1,
        "Volat_Ratio_5_20_Lag1": -1,
        "Volume_Ratio_5_20_Lag1": -1,
        "Volat_Compression_Lag1": -1,
        "Vol_Explosion_Today": 1,
        "Accel_Today": 1,
        "Body_Strength_Today": 1 
    },
    
    # 合成逻辑分组
    "env_cols": [
        "Trend_Slope_Lag1", "Position_Lag1", "Pullback_Depth_Lag1", 
        "Volat_Ratio_5_20_Lag1", "Volume_Ratio_5_20_Lag1", "Volat_Compression_Lag1"
    ],
    "trigger_cols": ["Vol_Explosion_Today", "Accel_Today", "Body_Strength_Today"],
    
    # 测试周期
    "horizons": ["W"], 
    }

# ==============================================================================

def load_real_data():
    """从本地 D:/DATA/FACTORS 加载预计算的因子 (严格模式：不进行实时计算)"""
    dp = DataProvider()
    start_date = EXP_CONFIG["start_date"]
    end_date = EXP_CONFIG["end_date"]
    direction_map = EXP_CONFIG["direction_map"]
    
    # 统一存放在 D:/DATA/FACTORS 根目录下
    base_save_path = "D:/DATA/FACTORS" 
    
    # 1. 初始化因子池
    factors_pool = pd.DataFrame()
    missing_factors = []
    
    # 获取所有需要加载的因子名
    factor_names = list(direction_map.keys())
    
    print(f"Syncing factors from {base_save_path} (Strict Mode)...")

    for name in factor_names:
        file_path = os.path.join(base_save_path, f"{name}.csv")
        direction = direction_map.get(name, 1)
        
        # 调用 DataProvider 中的新函数
        f_val, flag = dp.load_file_data(file_path)
        
        if flag == -1:
            # 兼容新版 load_file_data: 通用读取后需手动处理 Index 和日期过滤
            if f_val.index.nlevels < 2:
                # 转换日期并确保格式正确
                date_col = f_val.columns[0]
                stock_col = f_val.columns[1]
                
                # 显式解析日期，并确保 stock 是字符串
                f_val[date_col] = pd.to_datetime(f_val[date_col])
                f_val[stock_col] = f_val[stock_col].astype(str).str.zfill(6)
                
                # 设置 MultiIndex
                f_val.set_index([date_col, stock_col], inplace=True)
                f_val.index.names = ['date', 'stock']
            
            print(f"  > Loaded {name} from {base_save_path}.")
            # 过滤时间范围并确保排序
            f_val = f_val.sort_index()
            # 检查切片范围
            mask = (f_val.index.get_level_values('date') >= pd.to_datetime(start_date)) & \
                   (f_val.index.get_level_values('date') <= pd.to_datetime(end_date))
            f_val = f_val.loc[mask]
            
            # 取第一个数值列并应用方向
            val_col = f_val.columns[0]
            factors_pool[name] = f_val[val_col] * direction
        else:
            print(f"  > CRITICAL: {name} NOT FOUND at {file_path}")
            missing_factors.append(name)
    
    # 严格模式：如果有任何因子缺失，直接触发报错
    if missing_factors:
        raise FileNotFoundError(f"Experiment stopped. The following mandatory factors are missing from {base_save_path}: {missing_factors}. Please pre-calculate them using factor_validation.py first.")
    
    factors_pool.dropna(inplace=True)
    print(f"Factors pool ready. Shape: {factors_pool.shape}")
    
    # 价格数据路径仍从配置获取
    return factors_pool, EXP_CONFIG["data_path"]

def run_all_combination_experiments():
    """
    全流程因子合成实验：
    基于 EXP_CONFIG 进行参数化运行
    """
    start_date = EXP_CONFIG["start_date"]
    end_date = EXP_CONFIG["end_date"]
    env_cols = EXP_CONFIG["env_cols"]
    trigger_cols = EXP_CONFIG["trigger_cols"]
    
    # 1. 准备数据
    try:
        factors_df, price_path = load_real_data()
    except Exception as e:
        print(f"Data loading failed: {e}. Synthesis Pipeline stopped.")
        return

    # 2. 定义合成实验任务 (基于 EXP_CONFIG 动态提取)
    env_cols = EXP_CONFIG["env_cols"]
    trigger_cols = EXP_CONFIG["trigger_cols"]
    
    # 提取回归需要的未来回报 (1d)
    tester_temp = FactorTester(start_date, end_date)
    tester_temp.load_price_data(price_path)
    forward_ret_1d = tester_temp.get_forward_returns(interval_tag="D")
    forward_ret_1d_series = forward_ret_1d.set_index(["FDate", "SecCode"])["r"]

    # 定义合成方法
    methods = {
        "Equal_Weight": lambda df: FactorCombiner.equal_weight(df),
        "Orthogonalized_Mean": lambda df: FactorCombiner.equal_weight(FactorCombiner.orthogonalize_factors(df)),
        "Mul_Alpha_Raw": lambda df: FactorCombiner.compute_multiplicative_alpha(df, env_cols, trigger_cols),
        "Mul_Alpha_Adjusted": lambda df: FactorCombiner.compute_adjusted_alpha(df, env_cols, trigger_cols),
        "Sigmoid_Gate": lambda df: FactorCombiner.compute_sigmoid_gate_alpha(df, env_cols, trigger_cols, k=3),
        "Regression_Opt": lambda df: FactorCombiner.optimization_regression(df, forward_ret_1d_series)
    }

    # 3. 运行回测循环
    results_summary = []
    for horizon in EXP_CONFIG["horizons"]:
        horizon_label = "1d" if horizon == "D" else ("5d" if horizon == "W" else "20d")
        print(f"\n[HORIZON: {horizon_label}] Running synthesis evaluation...")
        
        output_base = f"./results/factor_combination/{horizon_label}"
        os.makedirs(output_base, exist_ok=True)

        for name, func in methods.items():
            try:
                print(f"  > Processing Strategy: {name} ...")
                composite_alpha = func(factors_df)
                
                f_data = composite_alpha.reset_index()
                f_data.columns = ["FDate", "SecCode", "FValue"]
                
                tester = FactorTester(start_date, end_date, output_dir=os.path.join(output_base, name))
                tester.load_price_data(price_path)
                
                metrics, _ = tester.backtest(
                    factor_name=name,
                    factor_data=f_data,
                    interval_tag=horizon,
                    groups=5,
                    if_plot=True
                )
                
                res = metrics.iloc[0].to_dict()
                res["Method"] = name
                res["Horizon"] = horizon_label
                results_summary.append(res)
            except Exception as e:
                print(f"  FAILED {name} at {horizon}: {e}")
                traceback.print_exc()

    # 4. 横向对比汇总结果
    if results_summary:
        summary_df = pd.DataFrame(results_summary)
        summary_df = summary_df[["Method", "Horizon", "RankIC", "RankICIR", "多头组年化收益", "多头组最大回撤"]]
        
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_csv = f"./results/factor_combination/Full_Synthesis_Comparison_{now_str}.csv"
        summary_df.sort_values(by=["Horizon", "RankICIR"], ascending=[True, False], inplace=True)
        summary_df.to_csv(final_csv, index=False)
        
        print("\n" + "="*100)
        print(f"EXPERIMENT COMPLETE! Overall Leaderboard:\n")
        print(summary_df.to_string(index=False))
        print(f"\nSaved to: {final_csv}")
        print("="*100)

if __name__ == "__main__":
    # run_debug_demo()
    run_all_combination_experiments()  # 开启全市场真实数据实验
