import numpy as np
import talib
import pandas as pd
from core.NumericalOperators import (
    ts_delay, ts_delta, ts_sum, ts_min, ts_max,
    ts_std_dev, ts_corr, ts_cov, ts_rank, cs_rank, sign,
    FactorOperators
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
    def ice_bias(data, window=20):
        """
        价格乖离率 (Price Bias / Deviation)
        逻辑: Price / MA(Price, N) - 1
        """
        close = data["close"]
        ma = close.rolling(window=window).mean()
        return (close / ma - 1)

    @staticmethod
    def pullback_depth(data, window=20):
        """
        回调深度 (Pullback Depth)
        逻辑: (rolling_max_20 - close) / rolling_max_20
        """
        hhv = data["high"].rolling(window=window).max()
        depth = (hhv - data["close"]) / (hhv + 1e-9)
        return pd.DataFrame({"pullback_depth": depth}, index=data.index)

    @staticmethod
    def position(data, window=60):
        """
        结构位置 (Position)
        逻辑: (close - rolling_min_60) / (rolling_max_60 - rolling_min_60)
        用60日最高最低价格衡量其处于60日区间的什么位置
        """
        llv = data["low"].rolling(window=window).min()
        hhv = data["high"].rolling(window=window).max()
        pos = (data["close"] - llv) / (hhv - llv + 1e-9)
        return pd.DataFrame({"position": pos}, index=data.index)

    @staticmethod
    def momentum_acceleration(data, window=5):
        """
        当日动量加速度 (Momentum Acceleration)
        逻辑: return_today - mean(return_last_5)
        """
        ret = data["close"].pct_change()
        mean_ret = ret.rolling(window=window).mean().shift(1)
        acc = ret - mean_ret
        return pd.DataFrame({"momentum_acceleration": acc}, index=data.index)

    @staticmethod
    def body_strength(data):
        """
        K线实体强度 (Body Strength)
        逻辑: abs(close-open)/(high-low)
        """
        body = (data["close"] - data["open"]).abs()
        range_hl = (data["high"] - data["low"])
        strength = body / (range_hl + 1e-9)
        return pd.DataFrame({"body_strength": strength}, index=data.index)

    @staticmethod
    def kdj(data, n=9, m1=3, m2=3):
        """
        KDJ 指标
        逻辑: 
        RSV = (Close - LLV(Low, N)) / (HHV(High, N) - LLV(Low, N)) * 100
        K = EMA(RSV, M1), D = EMA(K, M2), J = 3*K - 2*D
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]
        
        low_n = low.rolling(window=n).min()
        high_n = high.rolling(window=n).max()
        
        rsv = (close - low_n) / (high_n - low_n + 1e-9) * 100
        
        # 严格按照国内常用的 KDJ 指数平滑算法 (通常是 ewm)
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return pd.DataFrame({"kdj_k": k, "kdj_d": d, "kdj_j": j}, index=data.index)


class VolumeFactors:
    """
    交易量因子类
    """
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
        逻辑: Volume / MA(Volume, T)
        衡量今日成交量相对于长周期均值的比例。值越小代表缩量越极致。
        """
        volume = data["volume"]
        long_vol_ma = volume.rolling(window=window).mean()
        dryness_ratio = volume / (long_vol_ma + 1e-9)
        return pd.DataFrame({"volume_abs_dryness": dryness_ratio}, index=data.index)

    @staticmethod
    def volume_ratio(data, short_window=1, long_window=20):
        """
        量比 (Volume Ratio)
        逻辑: 过去 short_window 日均量 / 过去 long_window 日均量
        通过调整参数可以实现：
        - short=1, long=1: 今日 / 昨日
        - short=5, long=20: 过去 5 日均量 / 过去 20 日均量 (衡量近期缩量/放量趋势)
        """
        volume = data["volume"]
        v_short = volume.rolling(window=short_window).mean()
        v_long = volume.rolling(window=long_window).mean().shift(short_window)
        return pd.DataFrame({f"vol_{short_window}d_{long_window}d_ratio": v_short / (v_long + 1e-9)}, index=data.index)

    @staticmethod
    def directional_volume_ratio(data, short_window=1, long_window=20):
        """
        带方向的量比 (Directional Volume Ratio)
        逻辑: (V_short / V_long) * sign(Close - Previous_Close)
        上涨放量为正，下跌放量为负。用于区分攻击性放量与恐慌性抛盘。
        """
        volume = data["volume"]
        close = data["close"]
        v_short = volume.rolling(window=short_window).mean()
        v_long = volume.rolling(window=long_window).mean().shift(short_window)
        ratio = v_short / (v_long + 1e-9)
        
        # 获取涨跌方向
        direction = np.sign(close.diff().fillna(0))
        return pd.DataFrame({"directional_volume_ratio": ratio * direction}, index=data.index)

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
    def up_volume_ratio(data, window=20):
        """
        上涨成交量占比 (Up Volume Ratio)
        逻辑: up_volume / total_volume
        """
        is_up = (data["close"] > data["close"].shift(1)).astype(int)
        up_vol = data["volume"] * is_up
        sum_up_vol = up_vol.rolling(window=window).sum()
        sum_total_vol = data["volume"].rolling(window=window).sum()
        return pd.DataFrame({"up_volume_ratio": sum_up_vol / (sum_total_vol + 1e-9)}, index=data.index)

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

    @staticmethod
    def pv_consistency(data, window=20):
        """
        量价一致性 (Price-Volume Consistency)
        逻辑: N日内量价秩相关系数 (Spearman Rank Correlation)
        衡量价格变化与成交量变动是否正向一致。
        """
        ret = data["close"].pct_change()
        vol_change = data["volume"].pct_change()
        corr = ret.rolling(window=window * 2).corr(vol_change)
        return pd.DataFrame({"pv_consistency": corr}, index=data.index)


class TrendFactors:
    """
    趋势性因子类，包含跟随价格趋势的因子
    """
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

    @staticmethod
    def trend_strength(data, window=60):
        """
        趋势强度 (Trend Strength)
        逻辑: (Close - MA60) / MA60
        """
        close = data["close"]
        ma = close.rolling(window=window).mean()
        return pd.DataFrame({"trend_strength": (close / ma - 1)}, index=data.index)

    @staticmethod
    def trend_slope(data, window=20):
        """
        趋势斜率 (Trend Slope)
        逻辑: 对过去 N 日的均线进行线性回归，提取其斜率 (Slope)
        相比于单日变动，线性回归斜率更具平滑性和趋势代表性
        这里定义为20日均线的20日回归斜率
        """
        ma = data["close"].rolling(window=window).mean()
        # 使用线性回归计算 ma 在 window 周期内的斜率
        slope = pd.Series(FactorOperators.ts_regression_slope_array(ma.values, np.arange(len(ma)), window), index=data.index)
        return pd.DataFrame({"trend_slope": slope}, index=data.index)

    @staticmethod
    def ma_structure(data, short_window=20, long_window=60):
        """
        均线结构 (MA Structure)
        逻辑: (MA20 - MA60) / MA60
        """
        close = data["close"]
        ma_short = close.rolling(window=short_window).mean()
        ma_long = close.rolling(window=long_window).mean()
        return pd.DataFrame({"ma_structure": (ma_short / ma_long - 1)}, index=data.index)

    @staticmethod
    def supply_pressure(data, window=20):
        """
        筹码压力 (Supply Pressure)
        逻辑: volume_at_recent_high / mean(volume, 20)
        """
        high = data["high"]
        volume = data["volume"]
        hhv = high.rolling(window=window).max()
        # 修复 Pandas 2.1+ 中 fillna(method='ffill') 弃用导致的 TypeError
        vol_at_high = volume.where(high == hhv).ffill(limit=window-1)
        v_ma = volume.rolling(window=window).mean()
        return pd.DataFrame({"supply_pressure": vol_at_high / (v_ma + 1e-9)}, index=data.index)

    @staticmethod
    def displacement_ratio(data, window=5):
        """
        位移路程比 (Displacement to Distance Ratio / Efficiency Ratio)
        逻辑: (Close - Close[N]) / Sum(Abs(Close - Close[1]), N)
        衡量趋势的效率，1代表直线运动，0代表无位移。
        """
        close = data["close"]
        displacement = close - close.shift(window)
        total_distance = (close - close.shift(1)).abs().rolling(window=window).sum()
        return pd.DataFrame({"displacement_ratio": displacement / (total_distance + 1e-9)}, index=data.index)

    @staticmethod
    def bullish_alignment_ratio(data, windows=[5, 10, 20, 60, 120], lookback=20):
        """
        多头排列得分 (Bullish MA Alignment Score)
        逻辑: 类似 PMI 定义，不再是 0/1 判定，而是根据均线排列情况给出连续得分。
        计算每一天满足 MA_i > MA_{i+1} 的组合数量占比。
        例如 5 条均线有 4 个邻位关系，若全部满足则为 1.0，满足 3 个则为 0.75。
        """
        close = data["close"]
        # 计算各周期均线
        mas = [close.rolling(window=w, min_periods=min(w, 10)).mean() for w in windows]
        
        # 计算每一对邻近均线的得分 (MA_short > MA_long)
        alignment_scores = []
        for i in range(len(mas) - 1):
            # 满足条件为 1, 不满足为 0, 缺失值为 NaN
            score = (mas[i] > mas[i+1]).astype(float)
            # 只有当两根均线都有值时才计入
            score.loc[mas[i].isna() | mas[i+1].isna()] = np.nan
            alignment_scores.append(score)
            
        # 计算当日综合得分 (0.0 - 1.0)
        daily_score = pd.concat(alignment_scores, axis=1).mean(axis=1)
        
        # 对得分进行平滑 (lookback 周期均值)
        ratio = daily_score.rolling(window=lookback, min_periods=1).mean()
        
        # 填充 NaN 并添加极小扰动以确保 qcut 稳定性
        ratio = ratio.fillna(0) + np.random.normal(0, 1e-9, len(ratio))
        
        return pd.DataFrame({"bullish_alignment_ratio": ratio}, index=data.index)


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
    def volatility_compression(data, short_window=5, long_window=20):
        """
        绝对波动收敛度 (Absolute Volatility Compression)
        逻辑: ATR(S) / ATR(L)
        衡量短期波动相对于中期波动的比例。
        物理意义: 值越小代表波动越极端收敛。
        """
        high, low, close = data["high"], data["low"], data["close"]
        p_close = close.shift(1).replace(0, np.nan)
        tr = pd.concat([(high - low) / p_close, (high - p_close).abs() / p_close, (p_close - low).abs() / p_close], axis=1).max(axis=1)
        atr_s = tr.rolling(window=short_window).mean()
        atr_l = tr.rolling(window=long_window).mean()
        compression_ratio = atr_s / (atr_l + 1e-9)
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

    @staticmethod
    def volatility_ratio(data, short_window=5, long_window=20):
        """
        波动率收缩比 (Volatility Ratio)
        逻辑: std(5) / std(20)
        """
        ret = data["close"].pct_change()
        v_short = ret.rolling(window=short_window).std()
        v_long = ret.rolling(window=long_window).std()
        return pd.DataFrame({"volatility_ratio": v_short / (v_long + 1e-9)}, index=data.index)

    @staticmethod
    def amplitude_ratio(data, short_window=5, long_window=20):
        """
        振幅收缩比 (Amplitude Ratio)
        逻辑: mean(high-low, 5) / mean(high-low, 20)
        """
        amp = data["high"] - data["low"]
        a_short = amp.rolling(window=short_window).mean()
        a_long = amp.rolling(window=long_window).mean()
        return pd.DataFrame({"amplitude_ratio": a_short / (a_long + 1e-9)}, index=data.index)

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
