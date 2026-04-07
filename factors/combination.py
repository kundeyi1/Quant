import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class FactorCombiner:
    """
    因子合成工具类 (Synthesis & Combination)
    所有方法按横截面 (date) 进行处理，确保无未来函数。
    """

    @staticmethod
    def _standardize(df):
        """横截面 Z-score 标准化 - 修复 groupby 索引叠加问题"""
        # 使用 transform 保持原始 index 结构
        return df.groupby(level=0).transform(lambda x: (x - x.mean()) / x.std() if x.std() != 0 else 0)

    @staticmethod
    def compute_env_trigger_score(factors_df, env_list, trigger_list):
        """
        计算 env_score 和 trigger_score
        1. 对 factors_df 做横截面 z-score
        2. env_score = env_list 对应列的均值
        3. trigger_score = trigger_list 对应列的均值
        """
        z_factors = FactorCombiner._standardize(factors_df)
        
        # 确保仅计算存在的列
        valid_env = [c for c in env_list if c in z_factors.columns]
        valid_tri = [c for c in trigger_list if c in z_factors.columns]
        
        env_score = z_factors[valid_env].mean(axis=1)
        trigger_score = z_factors[valid_tri].mean(axis=1)
        
        return env_score, trigger_score

    @staticmethod
    def compute_multiplicative_alpha(factors_df, env_list, trigger_list):
        """
        乘法alpha
        alpha = env_score * trigger_score
        """
        env_score, trigger_score = FactorCombiner.compute_env_trigger_score(factors_df, env_list, trigger_list)
        return env_score * trigger_score

    @staticmethod
    def compute_adjusted_alpha(factors_df, env_list, trigger_list):
        """
        改进版乘法alpha
        alpha = (1 + env_score) * trigger_score
        """
        env_score, trigger_score = FactorCombiner.compute_env_trigger_score(factors_df, env_list, trigger_list)
        return (1 + env_score) * trigger_score

    @staticmethod
    def equal_weight(factors_df):
        """
        1. 等权组合 (Equal Weight)
        金融含义：认为所有因子对未来收益的贡献度一致。
        """
        # 横截面 Z-score
        z_factors = FactorCombiner._standardize(factors_df)
        # 直接取均值
        composite_alpha = z_factors.mean(axis=1)
        return composite_alpha

    @staticmethod
    def ic_ir_weight(factors_df, ic_ir_dict):
        """
        2. IC_IR 加权组合
        金融含义：按因子的风险调整后收益能力分配权重。
        """
        z_factors = FactorCombiner._standardize(factors_df)
        
        # 提取权重并归一化
        weights = pd.Series(ic_ir_dict)
        weights = weights / weights.abs().sum()
        
        # 加权求和
        composite_alpha = (z_factors * weights).sum(axis=1)
        return composite_alpha

    @staticmethod
    def orthogonalize_factors(factors_df, factor_order=None):
        """
        3. 顺序正交化 (Sequential Orthogonalization)
        金融含义：去除因子间的共线性，提取每个因子相对于前序因子的独立边际增量 Alpha。
        """
        if factor_order is None:
            factor_order = factors_df.columns.tolist()
        
        # 预备标准化后的数据
        z_factors = FactorCombiner._standardize(factors_df[factor_order])
        
        def _ortho_daily(df_daily):
            """逐日执行 Gram-Schmidt"""
            ortho_data = {}
            for i, col in enumerate(factor_order):
                if i == 0:
                    ortho_data[col] = df_daily[col]
                else:
                    # 准备自变量 (之前所有的正交化结果)
                    X = pd.DataFrame(ortho_data)
                    y = df_daily[col]
                    
                    # 剔除 NaN 对
                    valid = ~(X.isna().any(axis=1) | y.isna())
                    if valid.sum() > len(factor_order):
                        model = LinearRegression(fit_intercept=False)
                        model.fit(X[valid], y[valid])
                        # 取残差作为独立信息
                        ortho_data[col] = y - model.predict(X).flatten()
                    else:
                        ortho_data[col] = y # 样本不足则保留原值
            return pd.DataFrame(ortho_data, index=df_daily.index)

        # 按日期分组执行
        result = z_factors.groupby(level=0, group_keys=False).apply(_ortho_daily)
        return result

    @staticmethod
    def compute_multiplicative_alpha(factors_df, env_list, trigger_list):
        """
        4. 分层乘法结构 (Environment × Trigger)
        金融含义：环境评分作为交易的“背景倍率”，触发信号决定具体的入场强弱。
        """
        z_factors = FactorCombiner._standardize(factors_df)
        
        env_score = z_factors[env_list].mean(axis=1)
        trigger_score = z_factors[trigger_list].mean(axis=1)
        
        # 乘法合成
        alpha_mul = env_score * trigger_score
        return alpha_mul

    @staticmethod
    def compute_sigmoid_gate_alpha(factors_df, env_list, trigger_list, k=3):
        """
        5. Sigmoid Gate 门控模型
        金融含义：用环境评分决定触发信号的“开放程度”，Sigmoid 提供平滑的软过滤逻辑。
        """
        z_factors = FactorCombiner._standardize(factors_df)
        
        env_score = z_factors[env_list].mean(axis=1)
        trigger_score = z_factors[trigger_list].mean(axis=1)
        
        # 构建 Gate (0, 1)
        gate = 1 / (1 + np.exp(-k * env_score))
        
        # 门控合成
        alpha_gate = gate * trigger_score
        return alpha_gate

    @staticmethod
    def optimization_regression(factors_df, future_returns):
        """
        6. 回归加权 (Cross-sectional Regression)
        金融含义：寻找在横截面上对未来收益率解释力最好的线性组合。
        """
        z_factors = FactorCombiner._standardize(factors_df)
        
        # 强制对齐 MultiIndex 名称以兼容不同来源的数据 (如 DataManager vs FactorTester)
        z_factors.index.names = ['date', 'stock']
        if isinstance(future_returns, (pd.Series, pd.DataFrame)):
            future_returns.index.names = ['date', 'stock']
            
        # 对齐数据
        data = z_factors.join(future_returns.rename('target'), how='inner')
        
        def _reg_daily(df_daily):
            """逐日回归提取系数"""
            X = df_daily.drop(columns='target')
            y = df_daily['target']
            
            valid = ~(X.isna().any(axis=1) | y.isna())
            if valid.sum() > len(X.columns):
                model = LinearRegression(fit_intercept=False)
                model.fit(X[valid], y[valid])
                return pd.Series(model.coef_, index=X.columns)
            return pd.Series([np.nan] * len(X.columns), index=X.columns)

        # 得到每日回归系数的时间序列
        daily_coefs = data.groupby(level=0).apply(_reg_daily)
        
        # 计算全局平均系数 (或可扩展为滚动平均)
        mean_weights = daily_coefs.mean()
        mean_weights = mean_weights / mean_weights.abs().sum()
        
        print(f"Regression Weights Optimized: \n{mean_weights}")
        
        # 使用全局权重生成复合 Alpha
        composite_alpha = (z_factors * mean_weights).sum(axis=1)
        return composite_alpha
