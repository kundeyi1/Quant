import pickle, os
import pandas as pd
import seaborn as sns
import sys
sys.path.append(r"D:\code\Package\OrangePackage")
import DataFetchAPI as fetchConn
import DatabaseConnectionAPI as dbConn
import DataGeneralToolsAPI as toolConn
from tqdm import tqdm
from matplotlib import pyplot as plt

plt.rcParams['figure.figsize'] = [10, 6]
plt.rcParams['font.size'] = 10

class FactorTest:
    def __init__(self, start_date, end_date, quote_path, fig_path, codes_list = None):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.codes_list = codes_list
        self.quote_path = quote_path
        self.download_quote_data(self.codes_list)
        self.interval_mapping = {'D':1, 'W':5, 'M':20}
        self.fig_path = fig_path

    def download_quote_data(self, codes_list):
        trading_days = fetchConn.GetTradingDay(self.start_date, self.end_date)['TradingDate']
        existed_quotes = os.listdir(self.quote_path)
        for date in tqdm(trading_days):
            if f"{date.strftime('%Y-%m-%d')}.m" not in existed_quotes:
                stock_quote = fetchConn.GetStockDailyPrice(codes_list, begin_date=date, end_date=date)
                stock_quote['Vwap'] = stock_quote['Amount'] * 1e4 / stock_quote['Volume']
                pickle.dump(stock_quote, open(os.path.join(self.quote_path, f"{date.strftime('%Y-%m-%d')}.m"), "wb"))
        print(f"======更新完毕:{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}======")

    def read_price_data(self, codes_list = None, interval_tag = 'W', price_type='Close'):
        sample_dates = fetchConn.GetTradingDay(self.start_date, self.end_date, freq=interval_tag)['TradingDate']
        interval = self.interval_mapping[interval_tag]
        stock_quote = []
        trading_days = fetchConn.GetTradingDay(self.start_date, self.end_date)['TradingDate']
        for date in tqdm(trading_days):
            daily_stock_quote = pickle.load(open(os.path.join(self.quote_path, f"{date.strftime('%Y-%m-%d')}.m"), "rb"))
            stock_quote.append(daily_stock_quote)
        stock_quote = pd.concat(stock_quote)
        if codes_list:
            stock_quote = stock_quote.loc[stock_quote['SecCode'].isin(codes_list)]
        stock_quote[f'PostAdj{price_type}'] = stock_quote[f'{price_type}'] * stock_quote['AdjFactor']
        stock_post_price = stock_quote.pivot_table(index='FDate', columns='SecCode',
                                                   values=f'PostAdj{price_type}')
        stock_r = stock_post_price.shift(-interval) / stock_post_price - 1
        stock_r = stock_r.loc[sample_dates]
        stock_r = stock_r.unstack().reset_index()
        stock_r.columns = ['SecCode', 'FDate', 'r']
        return stock_r

    def backtest(self, factor_name, factor_data, interval_tag, groups, price_type='Close', stock_r=None, if_plot=True):
        """
        数据格式：
        factor_name: str, 因子名称
        factor_data: DataFrame, 包含SecCode, FDate, FValue三列
        interval_tag: D, W, M，对应1， 5， 20
        groups: 分几组
        price_type：用哪种价格测试
        """
        # stock_pool = sorted(list(factor_data['SecCode'].drop_duplicates()))
        interval = self.interval_mapping[interval_tag]
        # sample_dates = fetchConn.GetTradingDay(self.start_date, self.end_date, freq=interval_tag)['TradingDate']

        # print('======读取行情数据======')
        # stock_quote = []
        # trading_days = fetchConn.GetTradingDay(self.start_date, self.end_date)['TradingDate']
        # for date in tqdm(trading_days):
        #     daily_stock_quote = pickle.load(open(os.path.join(self.quote_path, f"{date.strftime('%Y-%m-%d')}.m"), "rb"))
        #     stock_quote.append(daily_stock_quote)
        # stock_quote = pd.concat(stock_quote)
        # stock_quote = stock_quote.loc[stock_quote['SecCode'].isin(stock_pool)]
        # stock_quote[f'PostAdj{price_type}'] = stock_quote[f'{price_type}'] * stock_quote['AdjFactor']
        # stock_post_price = stock_quote.pivot_table(index='FDate', columns='SecCode',
        #                                            values=f'PostAdj{price_type}')
        # stock_r = stock_post_price.shift(-interval) / stock_post_price - 1
        # stock_r = stock_r.loc[sample_dates]
        # stock_r = stock_r.unstack().reset_index()
        # stock_r.columns = ['SecCode', 'FDate', 'r']
        
        factor_data = factor_data.merge(stock_r, on=['SecCode', 'FDate'], how='right')
        factor_data.dropna(subset=['FValue'], inplace=True)
        factor_data.sort_values(by=['FDate', 'SecCode'], inplace=True)

        print(f'======输出{factor_name}因子绩效======')
        # ic rankic
        factor_data['FRank'] = factor_data.groupby('FDate')['FValue'].rank(pct=True)
        factor_group = factor_data.groupby('FDate')

        ic = factor_group.apply(lambda x: x['r'].corr(x['FValue'], method='pearson')).mean()
        rankic = factor_group.apply(lambda x: x['r'].corr(x['FRank'], method='spearman')).mean()
        ic_std = factor_group.apply(lambda x: x['r'].corr(x['FValue'], method='pearson')).std()
        rankic_std = factor_group.apply(lambda x: x['r'].corr(x['FRank'], method='spearman')).std()
        icir = (250 / interval) ** 0.5 * ic / ic_std
        rank_icir = (250 / interval) ** 0.5 * rankic / rankic_std

        # 分组
        factor_group_eval = pd.DataFrame(index=factor_data['FDate'].unique())
        for i in range(groups):
            factor_group_eval[f'group{i+1}'] = factor_data.loc[(factor_data['FRank'] >= (1-(i+1)/groups)) &
                                                               (factor_data['FRank'] <= (1-i/groups))].groupby('FDate')['r'].mean()
        factor_group_eval = factor_group_eval.shift(1)
        factor_group_eval_nav = (1+factor_group_eval).cumprod()

        # 最大回撤
        factor_draw_back = factor_group_eval_nav['group1'] / factor_group_eval_nav['group1'].cummax() - 1
        factor_max_draw_back = min(factor_draw_back.dropna())
        # 年化收益
        factor_annual_return = factor_group_eval_nav['group1'].iloc[-1] ** (1/(interval*len(factor_group_eval_nav)/250)) - 1
        # 因子单期IC
        single_period_ic = factor_group.apply(lambda x: x['r'].corr(x['FValue'], method='pearson'))
        # 分组收益
        group_average_return = factor_group_eval.median(axis=0)

        # 画图
        # 1. 分组净值
        factor_group_eval_nav.fillna(1, inplace=True)
        if if_plot:
            ax_nav = factor_group_eval_nav.plot()
            ax_nav.legend(ncol=2)
            ax_single_ic = plt.twinx()

            single_period_ic = factor_group.apply(lambda x: x['r'].corr(x['FRank'], method='spearman'))
            ax_single_ic.bar(single_period_ic.index, single_period_ic.values, width=5, color='dodgerblue', alpha=0.5)


            # ax_single_ic.bar(single_period_ic, width=5, color='dodgerblue', alpha=0.5)
            ax_nav.set_title(f'{factor_name}: 分组净值+因子IC')
            plt.savefig(os.path.join(self.fig_path, f'{factor_name}_净值+因子IC.png'))
            plt.close()

            # 2. 分组收益
            ax_group_return = group_average_return.plot(kind='bar', color='dodgerblue')
            ax_group_return.set_title(f'{factor_name}: 分组收益')
            plt.savefig(os.path.join(self.fig_path, f'{factor_name}_分组收益.png'))
            plt.close()

        # 3. 因子绩效
        eval_metrics = pd.DataFrame([ic, icir, rankic, rank_icir, factor_max_draw_back, factor_annual_return]).T
        eval_metrics.columns=['IC', 'ICIR', 'RankIC', 'RankICIR', '多头组最大回撤', '多头组年化收益']

        # 因子单期IC
        return eval_metrics, factor_group_eval_nav