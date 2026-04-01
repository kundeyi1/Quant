
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt

class FactorVisualizer:
    """
    因子可视化工具类
    """
    
    def __init__(self, price_data: pd.DataFrame, factor_data: pd.Series, factor_name: str = "Factor"):
        """
        初始化可视化器
        :param price_data: 资产的价格数据，必须包含 ['Open', 'High', 'Low', 'Close', 'Volume'] 列，索引为 DatetimeIndex
        :param factor_data: 因子值序列，索引为 DatetimeIndex
        :param factor_name: 因子名称，用于显示
        """
        self.price_data = price_data.copy()
        self.factor_data = factor_data.copy()
        self.factor_name = factor_name
        
        # 确保索引为 DatetimeIndex 并排序
        if not isinstance(self.price_data.index, pd.DatetimeIndex):
            self.price_data.index = pd.to_datetime(self.price_data.index)
        self.price_data.sort_index(inplace=True)
            
        if not isinstance(self.factor_data.index, pd.DatetimeIndex):
            self.factor_data.index = pd.to_datetime(self.factor_data.index)
        self.factor_data.sort_index(inplace=True)

        # 统一列名为 mplfinance 要求的格式 (首字母大写)
        col_map = {c: c.capitalize() for c in self.price_data.columns}
        self.price_data.rename(columns=col_map, inplace=True)
        
        # 对齐数据时间段
        common_index = self.price_data.index.intersection(self.factor_data.index)
        if len(common_index) == 0:
            raise ValueError("价格数据与因子数据没有重叠的时间段")
            
        self.price_data = self.price_data.loc[common_index]
        self.factor_data = self.factor_data.loc[common_index]

    def plot(self, title: str = None, save_path: str = None, lookback: int = None):
        """
        绘制K线图与因子副图
        :param title: 图表标题
        :param save_path: 图片保存路径，如果为 None 则直接显示
        :param lookback: 仅绘制最近 N 个周期的数据
        """
        plot_data = self.price_data
        plot_factor = self.factor_data
        
        if lookback:
            plot_data = plot_data.iloc[-lookback:]
            plot_factor = plot_factor.iloc[-lookback:]
            
        if title is None:
            title = f"{self.factor_name} Analysis"

        # 设置K线颜色（涨红跌绿 - 中国习惯）
        # up: 阳线颜色, down: 阴线颜色
        # edge: 蜡烛边框颜色, wick: 上下影线颜色
        market_colors = mpf.make_marketcolors(up='red', down='green', 
                                              edge={'up':'red', 'down':'green'},
                                              wick={'up':'red', 'down':'green'},
                                              volume={'up':'red', 'down':'green'})
                                              
        my_style = mpf.make_mpf_style(marketcolors=market_colors, gridstyle='--', y_on_right=True)

        # 创建副图 (addplot)
        # panel 0: 主图(K线)

        # panel 1: 成交量 (mplfinance默认如果volume=True则在panel 1)
        # panel 2: 因子图
        ap = mpf.make_addplot(plot_factor, panel=2, color='blue', secondary_y=False, ylabel=self.factor_name, width=1.5)

        # 绘图
        kwargs = dict(
            type='candle',
            style=my_style,
            title=title,
            ylabel='Price',
            volume=True,
            addplot=ap,
            panel_ratios=(6, 2, 2), # 主图:成交量:因子图 高度比例
            figscale=1.5,
            scale_padding={'left': 0.3, 'top': 0.8, 'right': 2.5, 'bottom': 0.8},
            tight_layout=True,
            returnfig=True,
            datetime_format='%Y-%m-%d'
        )
        
        fig, axes = mpf.plot(plot_data, **kwargs)

        
        # 如果需要保存图片
        if save_path:
            fig.savefig(save_path, bbox_inches='tight', dpi=150)
            plt.close(fig)
        else:
            plt.show() # 在交互式环境中显示

