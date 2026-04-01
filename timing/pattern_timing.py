import pandas as pd
import numpy as np
import os
from pathlib import Path
from core.Logger import logger

def find_significant_pivots(df, window=5):
    """
    寻找显著的波峰和波谷 (Fractals)
    无未来函数版本：仅使用当前及过去的数据判断之前的点是否为极值
    """
    # 局部极大/极小值识别
    # center=False 意味着我们向后偏移确认。当 T 时刻发现 T-window 是极值时，信号才报出
    # 判定规则：如果 T-window 时刻的价格等于过去 2*window+1 天的最值
    roll_max = df['high'].rolling(window=window*2+1).max()
    roll_min = df['low'].rolling(window=window*2+1).min()
    
    is_peak = (df['high'].shift(window) == roll_max)
    is_trough = (df['low'].shift(window) == roll_min)
    
    # 提取极值点
    pivots_raw = df[is_peak | is_trough].copy()
    if pivots_raw.empty:
        return pd.DataFrame()
        
    pivots_raw['type'] = np.where(is_peak[is_peak | is_trough], 'Peak', 'Trough')
    # 价格取的是当时产生极值的那个真实价格
    pivots_raw['pivot_price'] = np.where(
        pivots_raw['type'] == 'Peak', 
        df['high'].shift(window).loc[pivots_raw.index], 
        df['low'].shift(window).loc[pivots_raw.index]
    )
    
    # 去噪逻辑：同类型极值合并
    refined_pivots = []
    if len(pivots_raw) > 0:
        last_p = pivots_raw.iloc[0]
        for i in range(1, len(pivots_raw)):
            curr_p = pivots_raw.iloc[i]
            if curr_p['type'] == last_p['type']:
                if (curr_p['type'] == 'Peak' and curr_p['pivot_price'] > last_p['pivot_price']) or \
                   (curr_p['type'] == 'Trough' and curr_p['pivot_price'] < last_p['pivot_price']):
                    last_p = curr_p
            else:
                refined_pivots.append(last_p)
                last_p = curr_p
        refined_pivots.append(last_p)
    
    return pd.DataFrame(refined_pivots)

def detect_head_shoulder(df, window=10):
    """
    基于极值点序列识别头肩形态 (放宽 window 限制以捕捉更长周期形态)
    """
    pivots = find_significant_pivots(df, window)
    pattern_ser = pd.Series(np.nan, index=df.index, dtype=object)
    
    if len(pivots) < 5: return pattern_ser
    
    # 滑动窗口遍历极值点序列 (寻找 峰-谷-峰-谷-峰)
    for i in range(4, len(pivots)):
        pts = pivots.iloc[i-4 : i+1]
        types = pts['type'].tolist()
        prices = pts['pivot_price'].tolist()
        
        # 头肩底特征: Trough - Peak - Trough - Peak - Trough
        if types == ['Trough', 'Peak', 'Trough', 'Peak', 'Trough']:
            t1, p1, t2, p2, t3 = prices
            # 放宽判定条件：头部(t2)低于两肩(t1, t3)，两肩差异在 5% 以内
            if t2 < t1 and t2 < t3 and abs(t1-t3)/max(t1,t3) < 0.05:
                pattern_ser.loc[pts.index[-1]] = 'Inverse Head and Shoulder'
                
    return pattern_ser

def detect_double_pattern(df, window=10, threshold=0.03):
    """
    识别双顶/双底 (M头/W底) (放宽 threshold 限制)
    """
    pivots = find_significant_pivots(df, window)
    pattern_ser = pd.Series(np.nan, index=df.index, dtype=object)
    
    if len(pivots) < 3: return pattern_ser
    
    for i in range(2, len(pivots)):
        pts = pivots.iloc[i-2 : i+1]
        types = pts['type'].tolist()
        prices = pts['pivot_price'].tolist()
        
        # 双底: Trough - Peak - Trough
        if types == ['Trough', 'Peak', 'Trough']:
            t1, p1, t2 = prices
            # 两个底高度接近，且中间有明显反弹
            if abs(t1-t2)/max(t1,t2) < threshold and p1 > max(t1, t2) * 1.02:
                pattern_ser.loc[pts.index[-1]] = 'Double Bottom'
                
    return pattern_ser

def detect_triangle_pattern(df, window=5):
    """
    识别三角形形态 (收敛三角形)
    需要最近 2 个波峰和 2 个波谷，且斜率绝对值在缩小
    """
    pivots = find_significant_pivots(df, window)
    pattern_ser = pd.Series(np.nan, index=df.index, dtype=object)
    
    if len(pivots) < 4: return pattern_ser
    
    for i in range(3, len(pivots)):
        pts = pivots.iloc[i-3 : i+1].copy()
        peaks = pts[pts['type'] == 'Peak']
        troughs = pts[pts['type'] == 'Trough']
        
        if len(peaks) == 2 and len(troughs) == 2:
            # 计算高点斜率和低点斜率
            p_slope = (peaks.iloc[1]['pivot_price'] - peaks.iloc[0]['pivot_price'])
            t_slope = (troughs.iloc[1]['pivot_price'] - troughs.iloc[0]['pivot_price'])
            
            # 收敛特征: 高点在降低 (p_slope < 0), 低点在抬高 (t_slope > 0)
            if p_slope < 0 and t_slope > 0:
                pattern_ser.loc[pts.index[-1]] = 'Ascending Triangle'
            elif p_slope < 0 and t_slope < 0 and abs(p_slope) > abs(t_slope):
                pattern_ser.loc[pts.index[-1]] = 'Descending Triangle'
                
    return pattern_ser

def detect_wedge(df, window=5):
    # 为保持兼容，当前返回空，建议主要观察双顶底和头肩
    return pd.Series(np.nan, index=df.index, dtype=object)

def detect_channel(df, window=5):
    return pd.Series(np.nan, index=df.index, dtype=object)

def detect_multiple_tops_bottoms(df, window=5):
    # 逻辑类似于 Double Pattern 但更持久，当前由 Double Pattern 覆盖
    return pd.Series(np.nan, index=df.index, dtype=object)

def get_support_resistance(df, window=20):
    """
    计算基于极值点的水平支撑位/阻力位 (比标准差更有意义)
    """
    pivots = find_significant_pivots(df, window=10) # 使用更宽的窗口找强支撑
    res = pd.DataFrame(index=df.index)
    
    # 动态获取最近一个有效 Peak/Trough 的价格
    res['resistance'] = pivots[pivots['type']=='Peak']['pivot_price'].reindex(df.index).ffill()
    res['support'] = pivots[pivots['type']=='Trough']['pivot_price'].reindex(df.index).ffill()
    return res

def detect_pivots(df):
    """
    这里的信号现在是经过‘显著性’过滤后的
    """
    pivots = find_significant_pivots(df, window=5)
    ser = pd.Series('', index=df.index)
    for idx, row in pivots.iterrows():
        ser.loc[idx] = 'HH' if row['type'] == 'Peak' else 'LL'
    return ser


def run_pattern_recognition(df, window=20):
    logger.info("Starting Pattern Recognition...")
    results = {
        'head_shoulder_pattern': detect_head_shoulder(df, window),
        'multiple_top_bottom_pattern': detect_multiple_tops_bottoms(df, window),
        'triangle_pattern': detect_triangle_pattern(df, window),
        'wedge_pattern': detect_wedge(df, window),
        'channel_pattern': detect_channel(df, window),
        'double_pattern': detect_double_pattern(df, window),
        'signal': detect_pivots(df)
    }
    sr = get_support_resistance(df, window)
    results['support'] = sr['support']
    results['resistance'] = sr['resistance']
    return pd.DataFrame(results, index=df.index)



def save_pattern_results(results_df, base_filename="000985"):
    """
    将模式识别结果保存为 Parquet 格式
    """
    output_dir = Path("D:/DATA/TIMING")
    os.makedirs(output_dir, exist_ok=True)
    
    pattern_cols = results_df.columns
    
    # 针对 FactorTester 习惯，我们将字符串映射为数值信号
    signal_map = {
        'Head and Shoulder': 1,
        'Inverse Head and Shoulder': -1,
        'Multiple Top': 1,
        'Multiple Bottom': -1,
        'Ascending Triangle': 1,
        'Descending Triangle': -1,
        'Wedge Up': 1,
        'Wedge Down': -1,
        'Channel Up': 1,
        'Channel Down': -1
    }
    
    for col in results_df.columns:
        if col in ['support', 'resistance']: 
            # 支撑阻力单独保存，或直接作为指标 DataFrame
            save_path = output_dir / f"{col}_{base_filename}.parquet"
            # 指标通常不需要映射数值信号
            save_df = pd.DataFrame({base_filename + '.CSI': results_df[col]}, index=results_df.index)
            save_df.to_parquet(save_path)
            continue

        # 提取单因子
        pattern_ser = results_df[col]
        # 3.3 验证输出文件命名格式： <pattern_name>_000985.parquet
        file_name = f"{col}_{base_filename}.parquet"
        save_path = output_dir / file_name
        
        # 转换为单列 DataFrame，列名为指数代码以便于 FactorTester 识别
        # 同时进行信号数值化映射
        numeric_signal = pattern_ser.map(signal_map)
        # 对于 Pivots 等其他字符串信号，如果没有在 map 中定义，也会变成 NaN
        # 如果是 Pivots (HH/LL)，可以额外定义映射
        if col == 'signal':
            pivot_map = {'HH': 1, 'LL': -1, 'LH': 0.5, 'HL': -0.5}
            numeric_signal = pattern_ser.map(pivot_map)
        
        save_df = pd.DataFrame({base_filename + '.CSI': numeric_signal}, index=results_df.index)
        save_df.to_parquet(save_path)
        logger.info(f"Saved factor to: {save_path}")
