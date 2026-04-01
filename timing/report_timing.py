import pandas as pd
import numpy as np
import os
from factors.technical_factors import PriceFactors, VolumeFactors, TrendFactors, VolatilityFactors, CrowdingFactors, Alpha101Factors
from core.NumericalOperators import FactorOperators

def _standardize_input(data):
    """
    统一处理输入数据：支持标准 OHLC DataFrame 或 行业收盘价宽表。
    返回包含 'close', 'high', 'low', 'volume' 的 DataFrame。
    """
    if isinstance(data, pd.DataFrame) and "close" in data.columns:
        # 标准模式
        df = data[["close"]].copy()
        df["high"] = data["high"] if "high" in data.columns else data["close"]
        df["low"] = data["low"] if "low" in data.columns else data["close"]
        df["volume"] = data["volume"] if "volume" in data.columns else (data["amount"] if "amount" in data.columns else np.nan)
    else:
        # 宽表模式：将输入视为 close，high/low/volume 同之或补空
        df = pd.DataFrame({"close": data, "high": data, "low": data, "volume": np.nan})
    return df

# --- 国信 时点动量 20230517 ---

def gx_pit_rebound(data, u=0.005, d=0.05):
    """
    大跌反弹信号
    """
    df = _standardize_input(data)
    close, returns = df["close"], df["close"].pct_change()
    atr = VolatilityFactors.gx_atr_factor(df, n=60)["atr_60"]
    scale = pd.Series(1.0, index=df.index)
    scale.loc[atr < 0.01] = np.sqrt(atr / 0.01)
    scale.loc[atr > 0.02] = np.sqrt(atr / 0.02)
    u_eff, d_eff = u * scale, d * scale
    rebound_trigger = returns > u_eff
    signal = pd.Series(0, index=data.index, name="gx_pit_rebound")
    trigger_indices = np.where(rebound_trigger)[0]
    for t_idx in trigger_indices:
        if t_idx < 4: 
            continue
        date = df.index[t_idx]
        current_u_eff = u_eff.iloc[t_idx]
        pre_returns = returns.iloc[:t_idx]
        current_d_eff = d_eff.iloc[t_idx]
        last_rebound = np.where(pre_returns > current_u_eff)[0]
        m_start_idx = last_rebound[-1] if len(last_rebound) > 0 else 0
        m_end_idx = t_idx - 1
        if m_start_idx >= m_end_idx: 
            continue
        m_close = close.iloc[m_start_idx : m_end_idx + 1]
        if len(m_close) <= 3: 
            continue
        c_high_idx = m_close.idxmax()
        m_close_after_high = m_close.loc[c_high_idx:].iloc[1:]
        if len(m_close_after_high) < 2: 
            continue
        c_low_idx = m_close_after_high.idxmin()
        if close.index.get_loc(c_low_idx) - close.index.get_loc(c_high_idx) >= 2:
            if (1 - m_close_after_high.min() / m_close.max()) > current_d_eff:
                signal.iloc[t_idx] = 1
    return signal

def gx_pit_breakout(data, threshold_pre=0.01, threshold_break=0.01, window=5):
    """
    三角形收缩突破信号
    """
    df = _standardize_input(data)
    close, high, low, returns = df["close"], df["high"], df["low"], df["close"].pct_change()
    vol_compression = (returns.abs() < threshold_pre).rolling(window).sum() == window
    vol_compression_mask = vol_compression.shift(1).fillna(False)
    roll_high, roll_low = high.rolling(window).max(), low.rolling(window).min()
    channel_width = roll_high - roll_low
    channel_squeeze_mask = (channel_width.shift(1) < channel_width.shift(2)).fillna(False)
    breakout_mask = returns > threshold_break
    signal = (vol_compression_mask & channel_squeeze_mask & breakout_mask).astype(int)
    return signal.rename("gx_pit_breakout")

def gx_pit_rotation(benchmark_data, sector_prices, n_decrease=3, window_atr=60):
    """
    顶部切换信号
    """
    common_dates = benchmark_data.index.intersection(sector_prices.index)
    bench_orig, sectors = benchmark_data.loc[common_dates], sector_prices.loc[common_dates]
    bench_df = _standardize_input(bench_orig)
    bench_close, bench_returns = bench_df["close"], bench_df["close"].pct_change()
    # 1. 计算行业 52 周新高
    high_52w = sectors.rolling(window=252, min_periods=100).max()
    is_new_high = (sectors >= high_52w).astype(int)
    new_high_count = is_new_high.sum(axis=1)

    # 2. 新高行业数量减少
    count_diff = new_high_count.diff()
    exhaustion_mask = count_diff <= -n_decrease

    # 3. 指数下跌超过 ATR
    atr = VolatilityFactors.gx_atr_factor(bench_df, n=window_atr)[f"atr_{window_atr}"]
    vola_breakout = bench_returns < -atr

    signal = (exhaustion_mask & vola_breakout).astype(int)
    return signal.rename("gx_pit_rotation")

# --- 华泰 A股择时之技术打分体系 20251226 ---

def ht_rsrs_timing(data, N=18, M=600, buy_threshold=0.7, sell_threshold=-0.7):
    """
    RSRS 择时信号 (Z-Score > 0.7 为买入信号)
    依据：华泰证券《A股择时之技术打分体系》(20251228)
    1. 调用底层因子 ht_rsrs_norm (Z-Score)
    2. 基于阈值输出离散信号
    """
    df = _standardize_input(data)
    score = TrendFactors.rsrs_norm(df, N, M)
    signal = pd.Series(0, index=df.index)
    signal.loc[score > buy_threshold] = 1
    signal.loc[score < sell_threshold] = 0
    return signal.rename("ht_rsrs_timing")

def ht_price_bias_timing(data, window=20, threshold=0):
    """
    20日价格乖离率越过均值买入，跟从价格趋势
    """
    df = _standardize_input(data)
    bias = PriceFactors.price_bias(df, window)
    return (bias > threshold).astype(int).rename("ht_price_bias_timing")

def ht_bollinger_timing(data, window=20, d_std=2):
    """
    华泰布林带择时：
    当日收盘价突破过去 20 日均值 + 2 倍标准差则买入 (1)
    向下突破过去 20 日均值 - 2 倍标准差则卖出 (-1)
    其余时间维持前一日观点
    """
    df = _standardize_input(data)
    close = df["close"]
    ma = close.rolling(window).mean()
    std = close.rolling(window).std()
    
    upper = ma + d_std * std
    lower = ma - d_std * std
    
    # 初始化信号序列
    signal = pd.Series(0, index=df.index)
    
    # 状态持久化逻辑
    last_sig = 0
    for i in range(len(df)):
        if close.iloc[i] > upper.iloc[i]:
            last_sig = 1
        elif close.iloc[i] < lower.iloc[i]:
            last_sig = -1
        signal.iloc[i] = last_sig
        
    return signal.rename("ht_bollinger_timing")

def ht_new_high_timing(data, window=20, threshold=0.1):
    """
    1个月内（20日）创新高天数占比择时：
    采用正向趋势策略，占比升高买入 (1)，占比下降卖出 (-1)
    """
    df = _standardize_input(data)
    ratio = TrendFactors.new_high_ratio(df, window)
    
    # 计算变化趋势
    # 升高买入，下降卖出
    slope = ratio.diff()
    
    signal = pd.Series(0, index=df.index)
    # 状态持久化
    last_sig = 0
    for i in range(len(df)):
        if slope.iloc[i] > 0:
            last_sig = 1
        elif slope.iloc[i] < 0:
            last_sig = -1
        signal.iloc[i] = last_sig
        
    return signal.rename("ht_new_high_timing")


def ht_volume_volatility_timing(data, window=60):
    """
    量能波动放大则买入，捕捉后期行情启动
    """
    df = _standardize_input(data)
    v_vol = VolumeFactors.volume_volatility(df, window)
    v_vol_ma = v_vol.rolling(window=20).mean()
    return (v_vol > v_vol_ma).astype(int).rename("ht_volume_volatility_timing")