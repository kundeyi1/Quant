import talib
import numpy as np
import pandas as pd
from core.NumericalOperators import (
    ts_delay, ts_delta, ts_sum, ts_min, ts_max,
    ts_std_dev, ts_corr, ts_cov, ts_rank, cs_rank, sign
)


class PriceFactors:
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
    def price_percentile(data, window=120):
        """
        计算价格在过去x天内的分位点
        :param data: pandas DataFrame, 包含 'close' 列
        :param window: int, 回溯周期
        :return: DataFrame with 'price_percentile'
        """
        # 使用 ts_rank 函数计算滚动分位数
        percentile = ts_rank(data["close"], window)
        return pd.DataFrame({"price_percentile": percentile}, index=data.index)

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
    def volume_bias(data, window=20):
        """
        成交量乖离率 (Volume Bias)
        逻辑: Volume / MA(Volume, N) - 1
        """
        volume = data["volume"]
        ma = volume.rolling(window=window).mean()
        return (volume / ma - 1)

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
    def adx(data, period=14):
        """
        平均趋向指数 (ADX)
        """
        return pd.Series(talib.ADX(data["high"].values, data["low"].values, data["close"].values, period), index=data.index)

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

