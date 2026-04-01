import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
import warnings
from scipy.stats import spearmanr
import statsmodels.api as sm

import alphalens
from alphalens.utils import get_clean_factor_and_forward_returns
from alphalens.performance import factor_information_coefficient, mean_return_by_quantile

warnings.filterwarnings('ignore')

class FactorTester:
    """
    基于 Alphalens 的因子测试与组合框架
    整合了单因子测试、数据质量分析、相关性分析以及基于 Rolling ICIR 的多因子组合功能。
    """
    def __init__(self, factor_data=None, prices=None, output_dir="factor_results", n_jobs=4):
        """
        初始化
        :param factor_data: dict of DataFrame or DataFrame. 
                            如果是dict，key为因子名，value为DataFrame(index=date, columns=asset)
                            如果是DataFrame，需包含 ['FDate', 'SecCode', 'factor1', 'factor2', ...]
        :param prices: DataFrame, 价格数据，index=date, columns=asset
        :param output_dir: str, 输出目录
        :param n_jobs: int, 并行数
        """
        self.output_dir = output_dir
        self.n_jobs = min(n_jobs, 16)
        os.makedirs(output_dir, exist_ok=True)
        
        self.prices = prices
        self.factors = {}
        
        if isinstance(factor_data, dict):
            self.factors = factor_data
        elif isinstance(factor_data, pd.DataFrame):
            df = factor_data.copy()
            if 'FDate' in df.columns and 'SecCode' in df.columns:
                df['FDate'] = pd.to_datetime(df['FDate'])
                factor_cols = [c for c in df.columns if c not in ['FDate', 'SecCode']]
                for col in factor_cols:
                    pivot_df = df.pivot(index='FDate', columns='SecCode', values=col)
                    self.factors[col] = pivot_df
            else:
                raise ValueError("DataFrame 必须包含 'FDate' 和 'SecCode' 列")
                
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        print(f"初始化完成，共加载 {len(self.factors)} 个因子")

    def preprocess_factors(self, method="zscore", winsorize_limit=0.01):
        """
        对所有因子进行去极值、标准化处理 (向量化加速)
        """
        print("开始预处理因子数据...")
        start_time = time.time()
        processed_factors = {}
        
        for name, df in self.factors.items():
            # 替换 inf
            df = df.replace([np.inf, -np.inf], np.nan)
            
            # 截尾
            lower = df.quantile(winsorize_limit, axis=1)
            upper = df.quantile(1 - winsorize_limit, axis=1)
            clipped = df.clip(lower=lower, upper=upper, axis=0)
            
            # 填充缺失值 (用截面中位数)
            med = clipped.median(axis=1)
            filled = clipped.apply(lambda x: x.fillna(med), axis=0)
            
            if method == "zscore":
                mean = filled.mean(axis=1)
                std = filled.std(axis=1).replace(0, np.nan).fillna(1.0)
                z = filled.sub(mean, axis=0).div(std, axis=0)
                processed_factors[name] = z
            elif method == "rank":
                z = filled.rank(axis=1, pct=True) - 0.5
                processed_factors[name] = z
            else:
                processed_factors[name] = filled
                
        self.factors = processed_factors
        print(f"因子预处理完成, 耗时: {time.time() - start_time:.2f}秒")
        return self.factors

    def analyze_data_quality(self):
        """分析数据质量 - 包含缺失情况分析"""
        print("分析因子数据质量...")
        quality_dir = f"{self.output_dir}/data_quality"
        os.makedirs(quality_dir, exist_ok=True)

        stats = {}
        for factor_name, factor_df in self.factors.items():
            total_cells = factor_df.shape[0] * factor_df.shape[1]
            missing_cells = factor_df.isna().sum().sum()
            stats[factor_name] = {
                '总单元格数': total_cells,
                '缺失单元格数': missing_cells,
                '缺失比例': missing_cells / total_cells if total_cells > 0 else 1,
                '有效行数': factor_df.dropna(how='all').shape[0],
                '有效列数': factor_df.dropna(how='all', axis=1).shape[1],
                '数据开始时间': factor_df.dropna(how='all').index.min(),
                '数据结束时间': factor_df.dropna(how='all').index.max(),
            }
            
        overall_stats = pd.DataFrame(stats).T
        excel_path = f"{quality_dir}/数据质量分析报告.xlsx"
        overall_stats.to_excel(excel_path)
        print(f"数据质量分析已保存至: {excel_path}")
        return overall_stats

    def analyze_factor_correlation(self):
        """分析因子相关性"""
        print("分析因子相关性...")
        corr_dir = f"{self.output_dir}/correlation"
        os.makedirs(corr_dir, exist_ok=True)

        all_factor_data = {}
        for factor_name, factor_df in self.factors.items():
            if factor_df is None or factor_df.empty:
                continue
            try:
                factor_values = factor_df.stack().dropna()
                factor_values.name = factor_name
                all_factor_data[factor_name] = factor_values
            except Exception:
                continue

        if not all_factor_data:
            return pd.DataFrame()
            
        factor_matrix = pd.DataFrame(all_factor_data)
        correlation_matrix = factor_matrix.corr(method='spearman').replace([np.inf, -np.inf], np.nan).fillna(0.0)
        
        # 保存相关性矩阵
        correlation_matrix.to_excel(f"{corr_dir}/因子相关性矩阵.xlsx")
        
        # 绘制热图
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0)
        plt.title('因子相关性热图')
        plt.tight_layout()
        plt.savefig(f'{corr_dir}/因子相关性热图.png', dpi=300)
        plt.close()
        
        print("因子相关性分析完成")
        return correlation_matrix

    def run_alphalens_test(self, periods=(1, 5, 20), quantiles=5, filter_zscore=20, save_tearsheets=False, max_loss=0.35):
        """
        使用 Alphalens 进行单因子测试
        """
        if self.prices is None:
            raise ValueError("必须提供 prices 数据才能运行 Alphalens 测试")
            
        print("开始 Alphalens 单因子测试...")
        start_time = time.time()
        results = {}
        summary_list = []
        
        for name, factor_df in self.factors.items():
            print(f"测试因子: {name}")
            try:
                factor_series = factor_df.stack()
                factor_series.index.names = ['date', 'asset']
                factor_series.name = name
                
                # 确保时区一致或无时区
                if factor_series.index.levels[0].tz is not None:
                    factor_series.index = factor_series.index.set_levels(factor_series.index.levels[0].tz_localize(None), level=0)
                if self.prices.index.tz is not None:
                    self.prices.index = self.prices.index.tz_localize(None)
                
                clean_factor_data = get_clean_factor_and_forward_returns(
                    factor_series,
                    self.prices,
                    quantiles=quantiles,
                    periods=periods,
                    filter_zscore=filter_zscore,
                    max_loss=max_loss
                )
                
                # 计算 IC
                ic = factor_information_coefficient(clean_factor_data)
                ic_mean = ic.mean()
                ic_std = ic.std()
                ic_ir = ic_mean / ic_std
                
                # 计算分组收益
                mean_ret_quantile, std_quantile = mean_return_by_quantile(clean_factor_data, by_date=True)
                
                results[name] = {
                    'clean_data': clean_factor_data,
                    'ic': ic,
                    'ic_mean': ic_mean,
                    'ic_ir': ic_ir,
                    'mean_ret_quantile': mean_ret_quantile
                }
                
                # 汇总数据
                summary_dict = {'Factor': name}
                for p in periods:
                    col = f'{p}D' if f'{p}D' in ic_mean.index else p
                    summary_dict[f'IC_Mean_{p}'] = ic_mean.get(col, np.nan)
                    summary_dict[f'IC_IR_{p}'] = ic_ir.get(col, np.nan)
                summary_list.append(summary_dict)
                
                if save_tearsheets:
                    factor_dir = os.path.join(self.output_dir, "tearsheets", name)
                    os.makedirs(factor_dir, exist_ok=True)
                    
                    # 绘制各分组累积收益图
                    for p in periods:
                        col = f'{p}D' if f'{p}D' in mean_ret_quantile.columns else p
                        if col in mean_ret_quantile.columns:
                            ret_q = mean_ret_quantile[col].unstack('factor_quantile')
                            cum_ret_q = (1 + ret_q).cumprod()
                            
                            plt.figure(figsize=(10, 6))
                            for q in cum_ret_q.columns:
                                plt.plot(cum_ret_q.index, cum_ret_q[q], label=f'Q{q}')
                            
                            # 多空组合 (最高组 - 最低组)
                            if len(ret_q.columns) >= 2:
                                long_short = ret_q[ret_q.columns[-1]] - ret_q[ret_q.columns[0]]
                                cum_ls = (1 + long_short).cumprod()
                                plt.plot(cum_ls.index, cum_ls, label='Long-Short', linestyle='--', color='black')
                            
                            plt.title(f'{name} - Cumulative Returns by Quantile ({col})')
                            plt.legend()
                            plt.grid(True, alpha=0.3)
                            plt.tight_layout()
                            plt.savefig(f"{factor_dir}/cumulative_returns_{col}.png", dpi=300)
                            plt.close()
                    
            except Exception as e:
                print(f"因子 {name} 测试失败: {e}")
                import traceback
                traceback.print_exc() # 打印详细错误栈以便排查数据问题

        if not summary_list:
            print("错误: 所有因子测试均未成功，请检查因子数据与价格数据的时间戳和资产代码是否对齐。")
            return {}, pd.DataFrame()

        summary_df = pd.DataFrame(summary_list).set_index('Factor')
        summary_df.to_excel(f"{self.output_dir}/Alphalens_单因子测试汇总.xlsx")
        print(f"Alphalens 测试完成, 耗时: {time.time() - start_time:.2f}秒")
        
        return results, summary_df

    def combine_factors_rolling_icir(self, forward_returns, top_quantile=0.1, window=6, stability_k=5, weight_shrinkage=0.2):
        """
        基于 Rolling ICIR 的因子组合
        :param forward_returns: DataFrame, 提前计算好的未来收益率，index=date, columns=asset
        """
        print("开始 Rolling ICIR 因子组合...")
        start_time = time.time()
        
        # 1. 计算每个因子每期的 IC
        ic_dict = {}
        for name, factor_df in self.factors.items():
            # 对齐数据
            common_dates = factor_df.index.intersection(forward_returns.index)
            ic_series = pd.Series(index=common_dates, dtype=float)
            
            for date in common_dates:
                f_val = factor_df.loc[date].dropna()
                r_val = forward_returns.loc[date].dropna()
                common_assets = f_val.index.intersection(r_val.index)
                if len(common_assets) > 30:
                    corr, _ = spearmanr(f_val[common_assets], r_val[common_assets])
                    ic_series[date] = corr
            ic_dict[name] = ic_series
            
        ic_df = pd.DataFrame(ic_dict)
        
        # 2. 滚动选择 Top 因子
        ic_rank = ic_df.rank(axis=1, pct=True)
        top_bool = ic_rank >= (1 - top_quantile)
        
        combined_factors = pd.DataFrame(index=ic_df.index, columns=forward_returns.columns)
        
        dates = sorted(ic_df.index)
        for i, d in enumerate(dates):
            start_idx = max(0, i - window)
            past_dates = dates[start_idx:i]
            
            if len(past_dates) == 0:
                continue
                
            # 稳定性过滤
            counts = top_bool.loc[past_dates].sum(axis=0)
            stable_factors = counts[counts >= stability_k].index.tolist()
            
            if not stable_factors:
                stable_factors = counts[counts > 0].index.tolist()
                if not stable_factors:
                    continue
                    
            # 计算权重 (基于过去 IC 均值)
            ic_vals = ic_df.loc[past_dates, stable_factors].mean()
            w = ic_vals.abs().fillna(0)
            if w.sum() == 0:
                w = pd.Series(1.0, index=stable_factors)
            w = w / w.sum()
            
            # Shrinkage
            n = len(w)
            uniform = pd.Series(1.0 / n, index=w.index)
            w = (1 - weight_shrinkage) * w + weight_shrinkage * uniform
            w = w / w.sum()
            
            # 组合因子
            sub_factors = {f: self.factors[f].loc[d] for f in stable_factors if d in self.factors[f].index}
            sub_df = pd.DataFrame(sub_factors)
            
            if not sub_df.empty:
                combined_val = sub_df.fillna(0).mul(w).sum(axis=1)
                combined_factors.loc[d, combined_val.index] = combined_val
                
        print(f"Rolling ICIR 组合完成, 耗时: {time.time() - start_time:.2f}秒")
        return combined_factors

    def run_comprehensive_test(self, forward_returns=None, n_groups=5):
        """
        运行完整的测试流程
        """
        self.analyze_data_quality()
        self.analyze_factor_correlation()
        self.preprocess_factors()
        
        self.run_alphalens_test(quantiles=n_groups)
            
        if forward_returns is not None:
            combined = self.combine_factors_rolling_icir(forward_returns)
            combined.to_csv(f"{self.output_dir}/combined_factors_rolling_icir.csv")
            return combined
            
        return None

    def analyze_fama_macbeth(self, style_df, industry_mapping=None, target_factor=None):
        """
        基于 Fama-MacBeth 回归进行 Barra 风格因子归因
        
        Parameters:
        -----------
        style_df : pd.DataFrame
            风格因子数据，Index 为 (date, asset)，Columns 为风格名称
        industry_mapping : pd.DataFrame or pd.Series, optional
            行业分类数据。如果是 Series，Index 为 asset，Values 为行业分类；
            如果是 DataFrame，需要包含 date 列或 Index 为 (date, asset)。
        target_factor : str, optional
            需要归因的目标因子名称。若不指定，默认使用 self.factors 中的第一个因子。
            
        Returns:
        --------
        results_df : pd.DataFrame
            回归统计量的 DataFrame
        pure_factor_ret : pd.Series
            剥离风格后的目标因子纯收益序列
        """
        print("开始 Barra 风格归因分析 (Fama-MacBeth)...")
        start_time = time.time()
        
        # 0. 准备输出目录
        attribution_dir = f"{self.output_dir}/attribution"
        os.makedirs(attribution_dir, exist_ok=True)
        
        # 1. 确定目标因子
        if target_factor is None:
            target_factor = list(self.factors.keys())[0]
        
        if target_factor not in self.factors:
            raise ValueError(f"目标因子 {target_factor} 不在因子列表中")
            
        factor_data = self.factors[target_factor] # expected index=date, columns=asset
        
        # 2. 准备回归所需的 Y (下期收益率)
        if self.prices is None:
            raise ValueError("必须提供 prices 数据才能进行归因分析")
            
        returns = self.prices.pct_change().shift(-1) # T期的因子对应 T+1 期的收益
        
        # 3. 对齐数据
        # 将 factor_data 和 returns 转为 stack 格式 (date, asset)
        # 注意: factor_data 在 preprocess_factors 中可能已经是 (date, asset) 的宽表
        # stack 后变成 MultiIndex Series
        factor_stack = factor_data.stack()
        factor_stack.name = target_factor
        
        returns_stack = returns.stack()
        returns_stack.name = 'forward_ret'
        
        # 确保索引命名一致
        factor_stack.index.names = ['date', 'asset']
        returns_stack.index.names = ['date', 'asset']
        
        # 检查 style_df 格式
        # style_df 必须是 MultiIndex (date, asset)
        if not isinstance(style_df.index, pd.MultiIndex):
             # 尝试转换 stack
             print("警告: style_df 不是 MultiIndex，尝试 stack 转换...")
             style_df = style_df.stack()
             if isinstance(style_df, pd.Series):
                 style_df = style_df.to_frame()
        
        style_df.index.names = ['date', 'asset']

        # 合并 target, returns, styles
        # 使用 join='inner' 确保三者都有数据
        combined = pd.concat([returns_stack, factor_stack, style_df], axis=1, join='inner')
        
        # 处理行业哑变量
        if industry_mapping is not None:
            print("正在处理行业哑变量...")
            if isinstance(industry_mapping, pd.Series):
                # 静态行业分类，扩展到所有日期
                # industry_mapping index=asset, val=industry
                ind_dummies = pd.get_dummies(industry_mapping, prefix='IND')
                
                # 广播: index=asset -> index=(date, asset)
                # 使用 merge 可能会内存溢出，改用 reindex + fillna (如果 combined 很大)
                # 或者 join
                # combined index level 1 是 asset
                combined = combined.join(ind_dummies, on='asset', how='inner')
                
            elif isinstance(industry_mapping, pd.DataFrame):
                # 假设宽表 index=date, columns=asset values=industry
                ind_stack = industry_mapping.stack()
                ind_stack.name = 'industry'
                ind_stack.index.names = ['date', 'asset']
                
                ind_dummies = pd.get_dummies(ind_stack, prefix='IND')
                combined = combined.join(ind_dummies, how='inner')

        combined.dropna(inplace=True)
        
        if combined.empty:
            print("错误: 数据对齐后为空，无法进行回归分析")
            return pd.DataFrame(), pd.Series()
            
        print(f"数据对齐完成，样本数: {len(combined)}")
        
        # 4. 逐期回归 (Cross-Sectional Regression)
        results = []
        # 找出所有自变量列 (排除 Y 和 date/asset 索引)
        # Y = forward_ret
        # X = [target_factor] + style_cols + industry_dummies
        feature_cols = [c for c in combined.columns if c != 'forward_ret']
        
        # 确保 target_factor 在第一位或者特定位置方便提取
        # 我们用 feature_cols 列表记录顺序
        
        dates = combined.index.get_level_values(0).unique().sort_values()
        
        for date in dates:
            daily_data = combined.loc[date]
            if len(daily_data) < len(feature_cols) + 10: # 样本过少跳过
                continue
            
            # 截面回归: R_{t+1} = \alpha + \beta * Styles + \gamma * Target + \epsilon
            Y = daily_data['forward_ret']
            X = daily_data[feature_cols]
            X = sm.add_constant(X) # 增加截距项
            
            try:
                model = sm.OLS(Y, X).fit()
                
                # 记录系数 (Risk Premia / Factor Return)
                res = model.params.to_dict()
                tvals = model.tvalues.to_dict()
                
                # 给 t 值加后缀区分
                row = {'date': date, 'R2': model.rsquared, 'n': len(daily_data)}
                row.update(res)
                for k, v in tvals.items():
                    row[f'{k}_t'] = v
                
                results.append(row)
            except Exception as e:
                # print(f"回归失败 {date}: {e}")
                pass
                
        if not results:
            print("错误: 所有日期的回归均失败")
            return pd.DataFrame(), pd.Series()
            
        results_df = pd.DataFrame(results).set_index('date')
        
        # 5. 分析结果
        # 提取 target_factor 的纯收益 (即回归系数 gamma)
        # 注意: target_factor 列名即为因子名
        if target_factor in results_df.columns:
            pure_factor_ret = results_df[target_factor]
            
            avg_ret = pure_factor_ret.mean() * 252 # 年化
            avg_t = results_df[f'{target_factor}_t'].mean()
            win_rate = (pure_factor_ret > 0).mean()
            
            print(f"回归分析完成。")
            print(f"目标因子: {target_factor}")
            print(f"纯因子收益(年化): {avg_ret:.4f}, t值均值: {avg_t:.2f}, 胜率: {win_rate:.2%}")
            
            # 6. 保存结果
            results_df.to_csv(f"{attribution_dir}/attribution_summary.csv")
            
            # 7. 可视化
            # (1) 纯 Alpha 累计收益
            cum_pure_ret = (1 + pure_factor_ret).cumprod()
            cum_raw_ret = None
            
            plt.figure(figsize=(10, 6))
            plt.plot(cum_pure_ret.index, cum_pure_ret, label='Pure Alpha (Risk-Adjusted)', color='red', linewidth=2)
            plt.axhline(y=1, color='grey', linestyle='--', alpha=0.5)
            plt.title(f'{target_factor} - Pure Alpha Cumulative Return (Barra Adjusted)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f"{attribution_dir}/gx_hotspot_pure_alpha.png", dpi=300)
            plt.close()
            
            # (2) 风格暴露图
            # 计算 target_factor 与 各风格因子的截面相关性均值
            # 排除 const 和 industry dummies
            style_cols = [c for c in style_df.columns]
            corrs = []
            
            for date in dates:
                daily_data = combined.loc[date]
                if len(daily_data) > 10:
                    # 计算 Spearman 相关
                    c = daily_data[[target_factor] + style_cols].corr(method='spearman')[target_factor]
                    corrs.append(c)
            
            if corrs:
                avg_corrs = pd.DataFrame(corrs).mean().drop(target_factor)
                
                plt.figure(figsize=(12, 6))
                avg_corrs.plot(kind='bar', color='skyblue', edgecolor='black')
                plt.title(f'{target_factor} - Average Exposure to Barra Styles')
                plt.axhline(y=0, color='black', linewidth=0.8)
                plt.tight_layout()
                plt.savefig(f"{attribution_dir}/style_exposures.png", dpi=300)
                plt.close()
                
            print(f"归因分析结果已保存至: {attribution_dir}")
            return results_df, pure_factor_ret
        else:
             print(f"警告: 结果中未找到 {target_factor} 的系数")
             return results_df, pd.Series()
