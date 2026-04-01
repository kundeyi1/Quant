import sys
sys.path.append('D:/code/Package/')
import pandas as pd
import numpy as np
import os
from datetime import datetime
from OrangePackage.DatabaseConnectionAPI import GetDBConnection

class GXPitMom:
    def __init__(
        self,
        data_dir='D:/code/GX_PIT_MOM/',
        db_name='JYDB',
        start_date='20170101',
        end_date='20260330',
        sectors=['zx_yj', 'zx_ej'],
        half_life=10,
    ):
        self.data_dir = data_dir
        self.db_name = db_name
        self.start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        self.end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        self.sectors = sectors
        self.half_life = half_life
        self.index_inner_code = 14110
        self.index_mapping = {14110: '000985'}
        self.zx_ej_codes = [
            'CI005101', 'CI005102', 'CI005104', 'CI005105', 'CI005106', 'CI005107', 'CI005109', 'CI005110',
            'CI005111', 'CI005113', 'CI005117', 'CI005122', 'CI005124', 'CI005127', 'CI005129', 'CI005133',
            'CI005134', 'CI005135', 'CI005136', 'CI005137', 'CI005138', 'CI005139', 'CI005140', 'CI005143',
            'CI005144', 'CI005145', 'CI005146', 'CI005152', 'CI005153', 'CI005154', 'CI005155', 'CI005156',
            'CI005160', 'CI005162', 'CI005163', 'CI005164', 'CI005165', 'CI005166', 'CI005168', 'CI005170',
            'CI005171', 'CI005172', 'CI005173', 'CI005178', 'CI005181', 'CI005185', 'CI005187', 'CI005188',
            'CI005189', 'CI005190', 'CI005191', 'CI005192', 'CI005193', 'CI005194', 'CI005195', 'CI005196',
            'CI005197', 'CI005198', 'CI005199', 'CI005800', 'CI005801', 'CI005802', 'CI005803', 'CI005804',
            'CI005805', 'CI005806', 'CI005807', 'CI005808', 'CI005809', 'CI005810', 'CI005811', 'CI005812',
            'CI005813', 'CI005814', 'CI005815', 'CI005816', 'CI005817', 'CI005818', 'CI005819', 'CI005820',
            'CI005821', 'CI005822', 'CI005823', 'CI005824', 'CI005825', 'CI005826', 'CI005827', 'CI005828',
            'CI005829', 'CI005830', 'CI005831', 'CI005832', 'CI005834', 'CI005835', 'CI005836', 'CI005837',
            'CI005838', 'CI005839', 'CI005840', 'CI005841', 'CI005842', 'CI005843', 'CI005844', 'CI005845',
            'CI005846', 'CI005847', 'CI005848', 'CI005849'
        ]
        self.connection = GetDBConnection(self.db_name)

    def read_existing_file(self, file_path):
        if os.path.exists(file_path):
            try:
                return -1, pd.read_csv(file_path, index_col=0 if 'price' in file_path else None)
            except Exception:
                return 0, pd.DataFrame()
        return 0, pd.DataFrame()

    def get_industry_info(self, file_path, industry_type):
        status, df_info = self.read_existing_file(file_path)
        if status == -1:
            mapping = df_info.set_index('InnerCode')['ChiNameAbbr'].to_dict()
            inner_codes = tuple(df_info['InnerCode'].tolist())
            return mapping, inner_codes

        if industry_type == 'zx_yj':
            sql = """
            SELECT SecuCode, InnerCode, ChiNameAbbr
            FROM SecuMain
            WHERE SecuMarket = 84
            AND SecuCode >= 'CI005001' AND SecuCode <= 'CI005028'
            """
        elif industry_type == 'zx_ej':
            sql = f"""
            SELECT SecuCode, InnerCode, ChiNameAbbr
            FROM SecuMain
            WHERE SecuMarket = 84
            AND SecuCode IN {tuple(self.zx_ej_codes)}
            """
        else:
            raise ValueError(f'Unsupported industry_type: {industry_type}')

        df_info = pd.read_sql(sql, self.connection)
        df_info.to_csv(file_path, index=False)
        mapping = df_info.set_index('InnerCode')['ChiNameAbbr'].to_dict()
        inner_codes = tuple(df_info['InnerCode'].tolist())
        return mapping, inner_codes

    def update_index_prices(self, file_path, inner_codes, start_date, end_date):
        status, df_prices = self.read_existing_file(file_path)
        last_date = start_date
        if status == -1:
            last_date = str(df_prices.index.max())
            if last_date >= end_date:
                mask = (df_prices.index >= start_date) & (df_prices.index <= end_date)
                return df_prices.loc[mask]

        inner_code = inner_codes[0] if isinstance(inner_codes, (tuple, list)) else inner_codes
        sql_price = f"""
        SELECT TradingDay, OpenPrice as [open], HighPrice as [high], LowPrice as [low],
               ClosePrice as [close], PrevClosePrice as [pre_close]
        FROM QT_IndexQuote
        WHERE InnerCode = {inner_code}
        AND TradingDay > '{last_date}' AND TradingDay <= '{end_date}'
        """
        df_raw = pd.read_sql(sql_price, self.connection)
        if df_raw.empty:
            return df_prices

        df_raw['TradingDay'] = df_raw['TradingDay'].astype(str)
        df_new = df_raw.set_index('TradingDay').sort_index().astype(float)
        if status == -1:
            df_prices = pd.concat([df_prices, df_new]).sort_index()
            df_prices = df_prices[~df_prices.index.duplicated(keep='last')]
        else:
            df_prices = df_new

        df_prices.to_csv(file_path, index=True)
        mask = (df_prices.index >= start_date) & (df_prices.index <= end_date)
        return df_prices.loc[mask]

    def update_sector_prices(self, file_path, inner_codes, mapping, start_date, end_date):
        status, df_prices = self.read_existing_file(file_path)
        last_date = start_date
        if status == -1:
            last_date = str(df_prices.index.max())
            if last_date >= end_date:
                mask = (df_prices.index >= start_date) & (df_prices.index <= end_date)
                return df_prices.loc[mask]

        if isinstance(inner_codes, (tuple, list)):
            inner_codes_sql = f"({inner_codes[0]})" if len(inner_codes) == 1 else str(tuple(inner_codes))
        else:
            inner_codes_sql = f"({inner_codes})"

        sql_price = f"""
        SELECT InnerCode, TradingDay, ClosePrice
        FROM QT_IndexQuote
        WHERE InnerCode IN {inner_codes_sql}
        AND TradingDay > '{last_date}' AND TradingDay <= '{end_date}'
        """
        df_raw = pd.read_sql(sql_price, self.connection)
        if df_raw.empty:
            return df_prices

        df_new = df_raw.pivot(index='TradingDay', columns='InnerCode', values='ClosePrice')
        df_new.index = df_new.index.astype(str)
        df_new.columns = [mapping.get(c, c) for c in df_new.columns]
        df_new = df_new.astype(float)

        if status == -1:
            df_prices = pd.concat([df_prices, df_new]).sort_index()
            df_prices = df_prices[~df_prices.index.duplicated(keep='last')]
        else:
            df_prices = df_new

        df_prices.to_csv(file_path, index=True)
        mask = (df_prices.index >= start_date) & (df_prices.index <= end_date)
        return df_prices.loc[mask]

    def _gx_atr(self, data, n=60):
        p_close = data['close'].shift(1).replace(0, np.nan)
        tr = pd.concat(
            [
                (data['high'] - data['low']) / p_close,
                (data['high'] - p_close).abs() / p_close,
                (p_close - data['low']).abs() / p_close,
            ],
            axis=1,
        ).max(axis=1)
        return tr.rolling(n, min_periods=1).mean()

    def gx_pit_rebound(self, data, u=0.005, d=0.05):
        close, returns = data['close'], data['close'].pct_change()
        atr = self._gx_atr(data, n=60).fillna(0)
        scale = pd.Series(1.0, index=data.index)
        scale.loc[atr < 0.01] = np.sqrt(atr / 0.01)
        scale.loc[atr > 0.02] = np.sqrt(atr / 0.02)
        u_eff = u * scale
        d_eff = d * scale

        rebound_trigger = returns > u_eff
        signal = pd.Series(0, index=data.index)
        trigger_indices = np.where(rebound_trigger)[0]

        for t_idx in trigger_indices:
            if t_idx < 4:
                continue
            pre_returns = returns.iloc[:t_idx]
            last_rebound = np.where(pre_returns > u_eff.iloc[t_idx])[0]
            m_start_idx = last_rebound[-1] if len(last_rebound) > 0 else 0
            m_close = close.iloc[m_start_idx:t_idx]
            if len(m_close) <= 3:
                continue

            c_high = m_close.max()
            m_after_high = m_close.loc[m_close.idxmax():]
            if len(m_after_high) > 2 and (1 - m_after_high.min() / c_high) > d_eff.iloc[t_idx]:
                signal.iloc[t_idx] = 1

        return signal

    def gx_pit_rotation(self, benchmark_data, sector_prices, n_decrease=3):
        common = benchmark_data.index.intersection(sector_prices.index)
        bench_data = benchmark_data.loc[common]
        bench_returns = bench_data['close'].pct_change()

        high_1y = sector_prices.loc[common].rolling(252, min_periods=1).max()
        new_high_diff = ((sector_prices.loc[common] >= high_1y).astype(int).sum(axis=1)).diff()
        atr = self._gx_atr(bench_data, n=60)
        return ((new_high_diff <= -n_decrease) & (bench_returns < -atr)).astype(int)

    def gx_pit_breakout(self, data, threshold_pre=0.01, threshold_break=0.01, window=5):
        high = data['high']
        low = data['low']
        returns = data['close'].pct_change()

        vola_compression = (returns.abs() < threshold_pre).rolling(window).sum() == window
        channel_width = high.rolling(window).max() - low.rolling(window).min()
        squeeze = (channel_width.shift(1) < channel_width.shift(2)).fillna(False)
        return (vola_compression.shift(1) & squeeze & (returns > threshold_break)).astype(int)

    def calculate_fused_signals(self, sector_prices, signals_dict, half_life=None, start_date=None):
        half_life = half_life if half_life is not None else self.half_life
        start_date = start_date if start_date is not None else self.start_date

        rets = sector_prices.pct_change().dropna()
        all_dates = sector_prices.index

        combined_trigger = pd.Series(False, index=all_dates)
        for sig_series in signals_dict.values():
            combined_trigger |= (sig_series.reindex(all_dates) == 1)

        potential_trigger_dates = all_dates[combined_trigger]
        potential_trigger_dates = potential_trigger_dates[potential_trigger_dates >= pd.to_datetime(start_date)]

        raw_value_cache = {}
        rank_cache = {}
        for sig_name, timing_series in signals_dict.items():
            trigger_days = timing_series[timing_series == 1].index
            for d in trigger_days:
                if d not in rets.index:
                    continue

                if sig_name == 'rebound':
                    avg_prev = rets.shift(1).rolling(20).mean()
                    row_val = (rets - avg_prev).loc[d].dropna()
                else:
                    row_val = rets.loc[d].dropna()

                if not row_val.empty:
                    raw_value_cache[(d, sig_name)] = row_val
                    rank_cache[(d, sig_name)] = row_val.rank(pct=True)

        sector_signals = []
        for d in potential_trigger_dates:
            if d not in rets.index:
                continue

            d_idx = all_dates.get_loc(d)
            start_idx = max(0, d_idx - half_life + 1)
            window_dates = all_dates[start_idx:d_idx + 1] # 信号触发当天也算在内

            found_signals = []
            for sig_name in signals_dict.keys():
                if any((t, sig_name) in rank_cache for t in window_dates):
                    found_signals.append(sig_name)

            if not found_signals:
                continue

            if len(found_signals) == 1:
                sig_name = found_signals[0]
                if (d, sig_name) in raw_value_cache:
                    final_series = raw_value_cache[(d, sig_name)]
                else:
                    latest_t = next((t for t in reversed(window_dates) if (t, sig_name) in raw_value_cache), None)
                    final_series = raw_value_cache[(latest_t, sig_name)] if latest_t is not None else pd.Series()
                sig_type_str = sig_name
            else:
                combined_factor = pd.Series(0.0, index=sector_prices.columns)
                total_weight = 0.0
                for t in window_dates:
                    n = d_idx - all_dates.get_loc(t)
                    weight = 2 ** (-n / half_life)
                    for sig_name in found_signals:
                        if (t, sig_name) in rank_cache:
                            combined_factor = combined_factor.add(rank_cache[(t, sig_name)] * weight, fill_value=0)
                            total_weight += weight

                final_series = (combined_factor / total_weight) if total_weight > 0 else pd.Series()
                sig_type_str = '+'.join(sorted(found_signals))

            if not final_series.empty:
                final_series = final_series.dropna()
                for code, val in final_series.items():
                    sector_signals.append(
                        {
                            'date': d,
                            'code': code,
                            'factor_value': val,
                            'signal_type': sig_type_str,
                        }
                    )
        return sector_signals

    def save_today_trigger_report(self):
        today = pd.to_datetime(self.end_date).normalize()
        day_str = today.strftime('%Y%m%d')
        result_files = {
            'zx_yj': self.data_dir + 'result_zx_yj.csv',
            'zx_ej': self.data_dir + 'result_zx_ej.csv',
        }

        today_data = {}
        for sector, file_path in result_files.items():
            if not os.path.exists(file_path):
                continue

            df = pd.read_csv(file_path)
            if df.empty or 'date' not in df.columns:
                continue

            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
            if df.empty:
                continue

            latest_date = df['date'].max().normalize()
            if latest_date != today:
                continue

            day_df = df[df['date'].dt.normalize() == today].copy()
            if day_df.empty:
                continue

            day_df = day_df.sort_values(by='factor_value', ascending=False)
            today_data[sector] = day_df

        if not today_data:
            return

        report_output_dir = os.path.join(os.getcwd(), f'trigger_reports_{day_str}')
        os.makedirs(report_output_dir, exist_ok=True)

        for sector, day_df in today_data.items():
            if sector == 'zx_yj':
                day_df.to_excel(os.path.join(report_output_dir, f'行业时点动量表_中信一级行业_{day_str}.xlsx'), index=False)
            elif sector == 'zx_ej':
                day_df.to_excel(os.path.join(report_output_dir, f'行业时点动量表_中信二级行业_{day_str}.xlsx'), index=False)

        signal_logic = {
            'breakout': '出现波动压缩与通道收敛后，当天向上突破',
            'rebound': '在前期连续下跌后，当天出现反弹',
            'rotation': '：中信一级行业新高数量相较前一天明显回落，且当天中证全指走弱',
        }
        signal_name_cn = {
            'breakout': '三角形突破',
            'rebound': '大跌反弹',
            'rotation': '顶部切换',
        }

        signal_types = set()
        for df in today_data.values():
            signal_types.update(df['signal_type'].dropna().astype(str).unique().tolist())

        base_signals = sorted({s for t in signal_types for s in t.split('+') if s})
        signal_types_cn = []
        for t in sorted(signal_types):
            signal_types_cn.append('+'.join([signal_name_cn.get(x, x) for x in t.split('+') if x]))

        signal_line = '、'.join(signal_types_cn) if signal_types_cn else '无'
        logic_line = '；'.join([
            f'{signal_name_cn.get(s, s)}：{signal_logic.get(s, "信号逻辑见策略定义")}'
            for s in base_signals
        ]) if base_signals else '无'

        def format_top(df, n):
            if df is None or df.empty:
                return '无'
            top_df = df.head(n)
            return '、'.join([f"{row['code']}({row['factor_value']:.4f})" for _, row in top_df.iterrows()])

        zx_yj_top5 = format_top(today_data.get('zx_yj'), 5)
        zx_ej_top10 = format_top(today_data.get('zx_ej'), 10)

        report_lines = [
            '老师您好，以下是今日时点动量信号报告，旨在帮助您快速定位当下更值得优先跟踪的行业方向。',
            '',
            f'日期：{today.strftime("%Y-%m-%d")}',
            f'触发择时信号：{signal_line}',
            f'信号逻辑：{logic_line}',
            '',
            f'根据动量因子排名的前五个中信一级行业（行业代码(因子值)），依次为：',
            f'{zx_yj_top5}',
            '',
            f'根据动量因子排名的前十个中信二级行业（行业代码(因子值)），依次为：',
            f'{zx_ej_top10}',
            '',
            f'附件为今天的中证一级和二级行业详细列表，包含行业名称、行业因子值和当天信号类型。',
            '',
            f'-----------',
            '报告概述：',
            '本报告是中证全指在今日触发择时信号后的中信行业横截面的对比结果汇总。',
            '这份结果可理解为：我们先判断市场是否出现值得关注的择时信号；当信号触发后，再按动量因子对行业进行排序。因子值越高、排名越靠前，代表当下相对更强。',
            '根据历史数据回测，择时信号触发当天，排名靠前的行业在未来20个交易日内表现显著更好。'  
        ]

        report_path = os.path.join(report_output_dir, f'trigger_summary_{day_str}.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

    def run_update(self):
        index_data = self.update_index_prices(
            self.data_dir + '000985_prices.csv',
            self.index_inner_code,
            self.start_date,
            self.end_date,
        )

        zx_yj_mapping, zx_yj_inner_codes = self.get_industry_info(self.data_dir + 'zx_yj_info.csv', 'zx_yj')
        zx_yj_df = self.update_sector_prices(
            self.data_dir + 'zx_yj_prices.csv',
            zx_yj_inner_codes,
            zx_yj_mapping,
            self.start_date,
            self.end_date,
        )

        zx_ej_mapping, zx_ej_inner_codes = self.get_industry_info(self.data_dir + 'zx_ej_info.csv', 'zx_ej')
        zx_ej_df = self.update_sector_prices(
            self.data_dir + 'zx_ej_prices.csv',
            zx_ej_inner_codes,
            zx_ej_mapping,
            self.start_date,
            self.end_date,
        )

        index_data.index = pd.to_datetime(index_data.index)
        zx_yj_df.index = pd.to_datetime(zx_yj_df.index)
        zx_ej_df.index = pd.to_datetime(zx_ej_df.index)

        signal_breakout = self.gx_pit_breakout(index_data)
        signal_rebound = self.gx_pit_rebound(index_data)
        signal_rotation = self.gx_pit_rotation(index_data, zx_yj_df)

        signals_dict = {
            'breakout': signal_breakout,
            'rebound': signal_rebound,
            'rotation': signal_rotation,
        }

        for sector in self.sectors:
            sector_prices = zx_yj_df if sector == 'zx_yj' else zx_ej_df
            sector_signals = self.calculate_fused_signals(sector_prices, signals_dict)

            if sector_signals:
                final_df = pd.DataFrame(sector_signals).sort_values(by=['date', 'factor_value'], ascending=[False, False])
                output_file = self.data_dir + f'result_{sector}.csv'
                final_df.to_csv(output_file, index=False)
                self.save_today_trigger_report()
                print(f'Results saved to {output_file}')


if __name__ == '__main__':
    day = datetime.now().strftime('%Y-%m-%d')
    day = '2026-03-24'
    runner = GXPitMom(end_date = day)

    print(f'当前日期为{day}')
    runner.run_update()
