import pandas as pd
import numpy as np
import os
from core.DataManager import DataProvider

class FundamentalFactors:
    """
    基本面因子计算类。
    """
    def __init__(self, roe_file="FUNDAMENTAL/ROE.csv", pe_dir=r"D:\DATA\MARKET_VALUE"):
        self.provider = DataProvider()
        self.roe_file = roe_file
        self.pe_dir = pe_dir
        self._roe_pivoted = None

    def _get_annual_roe(self):
        """
        获取年度 ROE 数据并转换为宽表 (Row: Code, Col: Year)
        """
        if self._roe_pivoted is not None:
            return self._roe_pivoted
            
        df = self.provider.get_fundamental_data(self.roe_file)
        if df is None:
            return pd.DataFrame()
            
        # 仅保留年报数据 (12-31)
        df = df[df['date'].dt.month == 12].copy()
        df['year'] = df['date'].dt.year
        
        # 透视表：Code 为索引，年份为列
        pivoted = df.pivot(index='code', columns='year', values='value')
        self._roe_pivoted = pivoted
        return pivoted

    def get_roe_10y_stable_factor(self, target_date, threshold=15.0):
        """
        策略 1: 连续 10 年 ROE > 15%。
        """
        df = self._get_annual_roe()
        if df.empty:
            return pd.Series()
            
        target_dt = pd.to_datetime(target_date)
        # 5月1日披露规则：5月前用前前年，5月后用前年
        report_year = target_dt.year - 1 if target_dt.month >= 5 else target_dt.year - 2
        
        # 筛选过去 10 年
        hist_years = list(range(report_year - 9, report_year + 1))
        available_years = [y for y in hist_years if y in df.columns]
        
        if len(available_years) < 10:
            # print(f"Warning: Only {len(available_years)} years of ROE data available for {target_date}")
            return pd.Series(0, index=df.index)
            
        # 满足条件的截面
        mask = (df[available_years] > threshold).all(axis=1)
        return mask.astype(int)

    def get_roe_enhanced_factor(self, target_date, pe_limit=60, div_yield_limit=0.015):
        """
        策略 2: ROE 稳定 + 低 PE + 高股息。
        """
        # 1. 基础筛选
        roe_stable = self.get_roe_10y_stable_factor(target_date)
        eligible_codes = roe_stable[roe_stable == 1].index.tolist()
        
        if not eligible_codes:
            return pd.Series(0, index=roe_stable.index)
            
        # 2. 读取当日行情/估值数据 (Feather 格式)
        date_str = pd.to_datetime(target_date).strftime('%Y%m%d')
        pe_file = os.path.join(self.pe_dir, f"{date_str}.feather")
        
        if not os.path.exists(pe_file):
            return pd.Series(0, index=roe_stable.index)
            
        df_val = pd.read_feather(pe_file)
        df_val['code'] = df_val['S_INFO_WINDCODE'].str.split('.').str[0]
        df_val = df_val[df_val['code'].isin(eligible_codes)]
        
        # PE 和 股息率 过滤
        # 股息率 = 1 / S_PRICE_DIV_DPS
        df_val['pe_ok'] = df_val['S_VAL_PE_TTM'] < pe_limit
        df_val['div_yield'] = 1.0 / df_val['S_PRICE_DIV_DPS'].replace(0, np.nan)
        df_val['div_ok'] = df_val['div_yield'] > div_yield_limit
        
        selected = df_val[df_val['pe_ok'] & df_val['div_ok']]['code'].tolist()
        
        res = pd.Series(0, index=roe_stable.index)
        res.loc[res.index.isin(selected)] = 1
        return res

def calculate_fundamental_factors(data, factors_to_calc=None):
        # S_PRICE_DIV_DPS: 股价/每股股息 -> 股息率 = 1 / S_PRICE_DIV_DPS
        df_pe = df_pe[df_pe['code'].isin(eligible_codes)]
        
        # PE 限制
        df_pe['pe_ok'] = df_pe['S_VAL_PE_TTM'] < pe_limit
        
        # 股息率限制 (假设用户说的 15% 是年化分红率或者误指 1.5% 股息率，此处默认参数可调)
        # 如果 S_PRICE_DIV_DPS = 0 说明没分红
        df_pe['div_yield'] = 1.0 / df_pe['S_PRICE_DIV_DPS'].replace(0, np.nan)
        df_pe['div_ok'] = df_pe['div_yield'] > div_yield_limit
        
        final_mask = df_pe[df_pe['pe_ok'] & df_pe['div_ok']]['code'].tolist()
        
        res = pd.Series(0, index=s1_mask.index)
        res.loc[res.index.isin(final_mask)] = 1
        return res

def calculate_fundamental_factors(data, factors_to_calc=None):
    """
    外部调用接口，由回测框架在每个时间点调用。
    :param data: 包含当前日期和基础信息的 DataFrame 或 dict
    :param factors_to_calc: 需要计算的因子列表
    """
    if factors_to_calc is None:
        factors_to_calc = ['roe_10y_stable', 'roe_enhanced']
        
    date = data['date'].iloc[0] if isinstance(data, pd.DataFrame) else data['date']
    
    engine = FundamentalFactors()
    results = {}
    
    if 'roe_10y_stable' in factors_to_calc:
        results['roe_10y_stable'] = engine.get_roe_10y_stable_factor(date)
    
    if 'roe_enhanced' in factors_to_calc:
        results['roe_enhanced'] = engine.get_roe_enhanced_factor(date)
        
    return results
