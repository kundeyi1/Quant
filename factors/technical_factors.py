import talib
import numpy as np
import pandas as pd
from core.NumericalOperators import (
    ts_delay, ts_delta, ts_sum, ts_min, ts_max,
    ts_std_dev, ts_corr, ts_cov, ts_rank, cs_rank, sign
)


class PriceFactors:
    @staticmethod
    def price_abs_pos(data, window=120):
        """
        绝对价格位置 (Absolute Price Position)
        逻辑: 当前价格在过去 N 日内的分位数 (0-1)
        """
        return pd.DataFrame({"price_abs_pos": ts_rank(data["close"], window)}, index=data.index)

    @staticmethod
    def price_rel_ma(data, window=20):
        """
        相对均线位置 (Relative Position to MA)
        逻辑: (Price - MA) / Std
        衡量价格相对于均线的偏离标准差个数，偏差越小分数越高
        """
        close = data["close"]
        ma = close.rolling(window=window).mean()
        std = close.rolling(window=window).std()
        z_score = - abs(close - ma) / (std + 1e-9)
        return pd.DataFrame({"price_rel_ma": z_score}, index=data.index)

    @staticmethod
    def price_dist_high(data, window=20):
        """
        相对于前期关键高点的距离 (Distance to Historic High)
        逻辑: (Price / HHV - 1)
        衡量回撤程度，识别平台回踩或突破边缘
        """
        high = data["high"]
        hhv = high.rolling(window=window).max()
        dist = (data["close"] / hhv - 1)
        return pd.DataFrame({"price_dist_high": dist}, index=data.index)

    @staticmethod
    def overhead_supply(data, window=20):
        high = data["high"]
        low = data["low"]
        close = data["close"]
        volume = data["volume"]
        range_hl = (high - low).replace(0, np.nan)
        supply_weight = (high - close) / range_hl
        supply_vol = volume * supply_weight
        sum_supply = supply_vol.rolling(window=window, min_periods=1).sum()
        sum_total = volume.rolling(window=window, min_periods=1).sum()
        overhead_supply = sum_supply / sum_total
        return pd.DataFrame({"overhead_supply": overhead_supply}, index=data.index)

    @staticmethod
    def price_bias(data, window=20):
        """
        价格乖离率 (Price Bias / Deviation)
        逻辑: Price / MA(Price, N) - 1
        """
        close = data["close"]
        ma = close.rolling(window=window).mean()
        return (close / ma - 1)


class VolumeFactors:
    """
    交易量因子类
    """
    def __dict__(self):
        return {name: func for name, func in VolumeFactors.__dict__.items() if name.startswith('calculate_')}

    @staticmethod
    def obv(data):
        """
        计算能量潮 (On Balance Volume)
        :param data: pandas DataFrame, 包含 'close', 'volume' 列
        :return: OBV 值
        """
        close = data["close"].astype("float64").values
        volume = data["volume"].astype("float64").values
        obv = talib.OBV(close, volume)
        return pd.DataFrame({"obv": obv}, index=data.index)

    @staticmethod
    def volume_abs_dryness(data, window=20):
        """
        绝对缩量程度 (Absolute Volume Dryness)
        逻辑: Volume / MA(Volume, 2 * T)
        衡量今日成交量相对于长周期均值的比例。值越小代表缩量越极致。
        """
        volume = data["volume"]
        long_vol_ma = volume.rolling(window=window * 2).mean()
        dryness_ratio = volume / (long_vol_ma + 1e-9)
        return pd.DataFrame({"volume_abs_dryness": dryness_ratio}, index=data.index)

    @staticmethod
    def volume_yes_rel_dryness(data, window=5):
        """
        相对缩量比例 (Yesterday's Relative Volume Dryness)
        逻辑: Volume / Volume.shift(1)
        衡量今日相对于昨日的缩量比例 (例如：0.5 代表缩量一半)
        """
        volume = data["volume"]
        ratio = volume / (volume.shift(1) + 1e-9)
        return pd.DataFrame({"volume_yes_rel_dryness": ratio}, index=data.index)

    @staticmethod
    def volume_std_bias(data, window=20):
        """
        成交量乖离标准差 (Volume Std Score)
        逻辑: (Volume - MA) / Std
        衡量成交量偏离常态的程度。极致缩量通常对应极负值，放量对应极正值。
        """
        volume = data["volume"]
        ma = volume.rolling(window=window).mean()
        std = volume.rolling(window=window).std()
        v_score = (volume - ma) / (std + 1e-9)
        return pd.DataFrame({"volume_std_score": v_score}, index=data.index)

    @staticmethod
    def volume_volatility(data, window=60):
        """
        成交量波动率 (Volume Volatility)
        逻辑: Stdev(Volume Change, N)
        """
        volume = data["volume"]
        vol_pct = volume.pct_change()
        return vol_pct.rolling(window=window).std()

    @staticmethod
    def volume_breakout(data, window=120, multiplier=1.5):
        """
        计算放量信号
        定义: 成交量 > x天内的平均值 + n倍标准差
        :param data: pandas DataFrame, 包含 'volume' 列
        :param window: int, 回溯周期
        :param multiplier: float, 标准差倍数
        :return: DataFrame with 'volume_breakout' (1 for True, 0 for False)
        """
        volume = data["volume"]
        vol_ma = volume.rolling(window=window).mean()
        vol_std = volume.rolling(window=window).std()
        
        # 信号判定
        signal = (volume > (vol_ma + multiplier * vol_std)).astype(int)
        
        return pd.DataFrame({"volume_breakout": signal}, index=data.index)

    @staticmethod
    def intraday_strength(data):
        """
        当日强度因子
        逻辑: (Return - UpperShadowRatio) * VolumeRatio
        """
        close = data["close"]
        high = data["high"]
        volume = data["volume"]
        
        ret = close.pct_change()
        upper_shadow_ratio = (high - close) / close.replace(0, np.nan)
        vol_ma5 = volume.rolling(window=5).mean()
        vol_ratio = volume / vol_ma5.replace(0, np.nan)
        
        strength = (ret - upper_shadow_ratio) * vol_ratio
        strength = strength.replace([np.inf, -np.inf], np.nan)
        
        return pd.DataFrame({"intraday_strength": strength}, index=data.index)

class TrendFactors:
    """
    趋势性因子类，包含跟随价格趋势的因子
    """
    def __dict__(self):
        return {name: func for name, func in TrendFactors.__dict__.items() if name.startswith('calculate_')}

    @staticmethod
    def symmetry(data, window_len=50):
        """
        计算对称因子 (Symmetry Factor)
        逻辑:
        1. 寻找过去50天内的波峰 (最高价)。
        2. 寻找波峰之后的波谷 (最低价)。
        3. 计算 Slope1 (波峰 -> 当前) 和 Slope2 (波峰 -> 波谷)。
        4. Ratio = Slope1 / Slope2。
        """
        highs, lows, closes = data["high"].values, data["low"].values, data["close"].values
        symmetry = np.full(len(data), np.nan)
        for i in range(window_len, len(data)):
            w_high = highs[i-window_len : i]
            if len(w_high) < 2: continue
            peak_offset = np.argmax(w_high)
            peak_idx = i - window_len + peak_offset
            if peak_idx >= i - 1: continue
            w_low_after = lows[peak_idx+1 : i]
            if len(w_low_after) == 0: continue
            valley_offset = np.argmin(w_low_after)
            valley_idx = peak_idx + 1 + valley_offset
            P_peak, P_valley, P_curr = highs[peak_idx], lows[valley_idx], closes[i]
            dist_pv, dist_pc = valley_idx - peak_idx, i - peak_idx
            if dist_pv == 0: continue
            slope_pv, slope_pc = (P_valley - P_peak) / dist_pv, (P_curr - P_peak) / dist_pc
            if slope_pv == 0: continue
            symmetry[i] = slope_pc / slope_pv
        return pd.DataFrame({"symmetry": symmetry}, index=data.index)

    @staticmethod
    def ma_compression(data, windows=[10, 20, 50]):
        """
        均线压缩因子
        逻辑: 不同周期均线的离散程度 (均线标准差 / 收盘价)
        """
        close = data["close"]
        mas = [talib.SMA(close.values, timeperiod=w) for w in windows]
        mas_df = pd.DataFrame(np.array(mas).T, index=data.index)
        compression = mas_df.std(axis=1) / close
        return pd.DataFrame({"ma_compression": compression}, index=data.index)

    @staticmethod
    def yellow_line(data):
        """
        多空线 (黄线)
        逻辑: (MA14 + MA28 + MA57 + MA114) / 4
        """
        c = data["close"].values
        zxt = (talib.SMA(c, 14) + talib.SMA(c, 28) + talib.SMA(c, 57) + talib.SMA(c, 114)) / 4
        return pd.DataFrame({"yellow_line": zxt}, index=data.index)

    @staticmethod
    def white_line(data, period=10):
        """
        双重EMA (白线)
        逻辑: EMA(EMA(Close, 10), 10)
        """
        c = data["close"].values
        ema2 = talib.EMA(talib.EMA(c, timeperiod=period), timeperiod=period)
        return pd.DataFrame({"white_line": ema2}, index=data.index)

    @staticmethod
    def sma(data, period=14):
        """
        简单移动平均线 (SMA)
        """
        return pd.DataFrame({"sma": talib.SMA(data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def adx(data, period=20):
        """
        ADX 趋势强度
        逻辑: 衡量趋势强弱，不分方向。
        """
        return pd.DataFrame({"adx": talib.ADX(data["high"].values, data["low"].values, data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def plus_di(data, period=20):
        """
        正向趋向指标 (+DI)
        逻辑: 衡量上升趋势强度
        """
        return pd.DataFrame({"plus_di": talib.PLUS_DI(data["high"].values, data["low"].values, data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def minus_di(data, period=20):
        """
        负向趋向指标 (-DI)
        逻辑: 衡量下跌趋势强度
        """
        return pd.DataFrame({"minus_di": talib.MINUS_DI(data["high"].values, data["low"].values, data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def new_high_count(data, window=20):
        """
        过去20天创20日新高的天数
        逻辑: 衡量趋势的持续性和创新高的频率
        """
        high = data["high"]
        is_new_high = (high == high.rolling(window).max()).astype(int)
        count = is_new_high.rolling(window).sum()
        return pd.DataFrame({"new_high_count": count}, index=data.index)

    @staticmethod
    def trend_inertia(data, window=20):
        """
        趋势惯性 (Trend Inertia)
        逻辑: Close / MA(4*T) - 1
        直接返回百分比，不再取排名
        """
        close = data["close"]
        long_window = window * 3
        trend = close / close.rolling(window=long_window).mean() - 1
        return pd.DataFrame({"trend_inertia": trend}, index=data.index)

    @staticmethod
    def ema(data, period=14):
        """
        指数移动平均线 (EMA)
        """
        return pd.DataFrame({"ema": talib.EMA(data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def wma(data, period=14):
        """
        加权移动平均线 (WMA)
        """
        return pd.DataFrame({"wma": talib.WMA(data["close"].values, timeperiod=period)}, index=data.index)

    @staticmethod
    def ma_arrangement(data, windows=[5, 10, 20, 60]):
        """
        多头排列因子
        逻辑: Sum((MA_short - MA_long) / MA_long) 对于相邻均线对
        """
        close = data["close"]
        mas = [talib.SMA(close.values, timeperiod=w) for w in windows]
        score = sum((mas[i] - mas[i+1]) / mas[i+1] for i in range(len(mas) - 1))
        return pd.DataFrame({"ma_arrangement": score}, index=data.index)

    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """
        MACD 指标
        """
        macd, s, h = talib.MACD(data["close"].values, fast, slow, signal)
        return pd.DataFrame({"macd": macd, "macd_signal": s, "macd_hist": h}, index=data.index)

    @staticmethod
    def sar(data, acc=0.02, max=0.2):
        """
        抛物线转向指标 (SAR)
        """
        return pd.DataFrame({"sar": talib.SAR(data["high"].values, data["low"].values, acc, max)}, index=data.index)

    @staticmethod
    def rsrs_norm(data, N=18, M=600):
        """
        华泰 RSRS 正态化因子 (阻力支撑相对强度)
        """
        from core.NumericalOperators import FactorOperators
        beta = pd.Series(FactorOperators.ts_regression_slope_array(data["low"].values, data["high"].values, N), index=data.index)
        return (beta - beta.rolling(M, min_periods=M//2).mean()) / beta.rolling(M, min_periods=M//2).std()

    @staticmethod
    def short_term_trend(data, n1=3):
        """
        短期趋势因子
        逻辑: 100 * (Close - LLV(Low, N1)) / (HHV(Close, N1) - LLV(Low, N1))
        """
        c, l = data["close"], data["low"]
        f = 100 * (c - l.rolling(n1, min_periods=1).min()) / (c.rolling(n1, min_periods=1).max() - l.rolling(n1, min_periods=1).min())
        return pd.DataFrame({"short_term_trend": f}, index=data.index)

    @staticmethod
    def long_term_trend(data, n2=21):
        """
        长期趋势因子
        逻辑: 100 * (Close - LLV(Low, N2)) / (HHV(Close, N2) - LLV(Low, N2))
        """
        c, l = data["close"], data["low"]
        f = 100 * (c - l.rolling(n2, min_periods=1).min()) / (c.rolling(n2, min_periods=1).max() - l.rolling(n2, min_periods=1).min())
        return pd.DataFrame({"long_term_trend": f}, index=data.index)

    @staticmethod
    def new_high_ratio(data, window=20):
        """
        创新高天数占比因子
        逻辑: 过去N日内创N日新高的天数占比
        """
        h = data["high"]
        return (h == h.rolling(window).max()).rolling(window).mean()

    @staticmethod
    def ht_trend_score(data, s=5, l=60):
        """
        华泰趋势打分因子 (双均线多头形态)
        """
        c = data["close"]
        diff = (c.rolling(s).mean() / c.rolling(l).mean() - 1)
        vol = c.pct_change().rolling(l).std()
        return diff / (vol * np.sqrt(l))

class VolatilityFactors:
    @staticmethod
    def bollinger_bands(data, p=20, u=2, d=2):
        """
        布林带 (Bollinger Bands)
        """
        up, mid, low = talib.BBANDS(data["close"].values, p, u, d, 0)
        return pd.DataFrame({"bb_upper": up, "bb_middle": mid, "bb_lower": low}, index=data.index)

    @staticmethod
    def bollinger_breakout(data, w=20, d=2):
        """
        布林带突破因子
        逻辑: (Price - Middle) / (Upper - Lower)
        """
        up, mid, low = talib.BBANDS(data["close"].values, w, d, d)
        return pd.Series((data["close"].values - mid) / (up - low + 1e-9), index=data.index)

    @staticmethod
    def volatility_compression(data, window=20):
        """
        绝对波动收敛度 (Absolute Volatility Compression)
        逻辑: ATR(5) / ATR(T)
        衡量短期波动相对于中期波动的比例。
        物理意义: 值越小代表波动越极端收敛。
        """
        high, low, close = data["high"], data["low"], data["close"]
        p_close = close.shift(1).replace(0, np.nan)
        tr = pd.concat([(high - low) / p_close, (high - p_close).abs() / p_close, (p_close - low).abs() / p_close], axis=1).max(axis=1)
        atr_5 = tr.rolling(5).mean()
        atr_t = tr.rolling(window).mean()
        compression_ratio = atr_5 / (atr_t + 1e-9)
        return pd.DataFrame({"volatility_compression": compression_ratio}, index=data.index)

    @staticmethod
    def atr_std_bias(data, window=20):
        """
        波动率乖离标准差 (ATR Std Bias)
        逻辑: (ATR(5) - MA(ATR, T)) / Std(ATR, T)
        衡量当前波动率偏离常态的程度。
        物理意义: 极负值(如 < -1.5)代表进入了极度寂静期。
        """
        high, low, close = data["high"], data["low"], data["close"]
        p_close = close.shift(1).replace(0, np.nan)
        tr = pd.concat([(high - low) / p_close, (high - p_close).abs() / p_close, (p_close - low).abs() / p_close], axis=1).max(axis=1)
        atr = tr.rolling(5).mean()
        ma = atr.rolling(window=window).mean()
        std = atr.rolling(window=window).std()
        score = (atr - ma) / (std + 1e-9)
        return pd.DataFrame({"atr_std_bias": score}, index=data.index)

    @staticmethod
    def gx_atr_factor(data, n=60):
        p_close = data["close"].shift(1).replace(0, np.nan)
        tr = pd.concat([(data["high"]-data["low"])/p_close, (data["high"]-p_close).abs()/p_close, (p_close-data["low"]).abs()/p_close], axis=1).max(axis=1)
        return pd.DataFrame({f"atr_{n}": tr.rolling(n, min_periods=1).mean()}, index=data.index)

class CrowdingFactors:
    @staticmethod
    def high_pos_vol_risk(data, w=120, m=1.5, t=0.9):
        is_hp = ts_rank(data["close"], w) >= t
        v = data["volume"]
        is_hv = v > (v.rolling(w).mean() + m * v.rolling(w).std())
        s = (is_hp & is_hv & (data["close"] < data["open"])).astype(int)
        return pd.DataFrame({"high_pos_vol_risk": s}, index=data.index)

    @staticmethod
    def gx_hotspot(data, w=120, d=0.10):
        c, v, r = data["close"], data["volume"], data["close"].pct_change()
        res = np.full(len(c), np.nan)
        lfi = -1
        cv, rv = c.values, r.values
        for t in range(1, len(c)):
            if cv[t] / np.max(cv[max(0, t-w):t]) - 1 <= -d: lfi = t
            if lfi != -1 and t >= lfi + 6:
                wr = rv[lfi : t]
                if len(wr) > 0 and np.sum(np.abs(wr)) != 0: res[t] = np.sum(wr) / np.sum(np.abs(wr))
        return pd.DataFrame({"gx_hotspot": res}, index=data.index)

class Alpha101Factors:
    @staticmethod
    def alpha3(data): return pd.DataFrame({"alpha3": -ts_corr(cs_rank(data["open"]), cs_rank(data["volume"]), 10)}, index=data.index)
    @staticmethod
    def alpha4(data): return pd.DataFrame({"alpha4": -ts_rank(cs_rank(data["low"]), 9)}, index=data.index)
    @staticmethod
    def alpha6(data): return pd.DataFrame({"alpha6": -ts_corr(data["open"], data["volume"], 10)}, index=data.index)
    @staticmethod
    def alpha12(data): return pd.DataFrame({"alpha12": sign(ts_delta(data["volume"], 1)) * (-ts_delta(data["close"], 1))}, index=data.index)
    @staticmethod
    def alpha15(data): return pd.DataFrame({"alpha15": -ts_sum(cs_rank(ts_corr(cs_rank(data["high"]), cs_rank(data["volume"]), 3)), 3)}, index=data.index)
    @staticmethod
    def alpha16(data): return pd.DataFrame({"alpha16": -cs_rank(ts_cov(cs_rank(data["high"]), cs_rank(data["volume"]), 5))}, index=data.index)

