#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
单因子测试模块 - 增强版（包含相关性分析和缺失情况分析）
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
import os
from datetime import datetime
import concurrent.futures
import time


class SingleFactorTester:
    """**单因子测试器 - 优化版（修复Windows多进程问题）**"""

    def __init__(self, factor_names_or_dict, close_df, output_dir="factor_results",
                 factor_dir="factor_data", use_local_factors=True, use_parallel=True, n_jobs=4):
        """初始化单因子测试器"""
        self.close_df = close_df
        self.output_dir = output_dir
        self.factor_dir = factor_dir
        self.use_local_factors = use_local_factors
        self.use_parallel = use_parallel  # 是否使用并行处理
        self.n_jobs = min(n_jobs, 16)  # 限制最大并行作业数

        os.makedirs(output_dir, exist_ok=True)

        # 根据参数类型加载因子数据
        if use_local_factors:
            if isinstance(factor_names_or_dict, list):
                self.factor_names = factor_names_or_dict
                self.factors = self._load_factors_from_local()
            else:
                raise ValueError("当use_local_factors=True时，factor_names_or_dict必须是因子名称列表")
        else:
            if isinstance(factor_names_or_dict, dict):
                self.factors = factor_names_or_dict
                self.factor_names = list(factor_names_or_dict.keys())
            else:
                raise ValueError("当use_local_factors=False时，factor_names_or_dict必须是因子数据字典")

        # 显示中文
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        print(f"初始化完成，共加载 {len(self.factors)} 个因子")

    def _load_factors_from_local(self):
        """**从本地文件加载因子数据 - 使用线程池**"""
        print("从本地文件加载因子数据...")

        if not os.path.exists(self.factor_dir):
            raise FileNotFoundError(f"因子数据目录不存在: {self.factor_dir}")

        loaded_factors = {}
        failed_factors = []

        # 使用线程池并行加载因子数据（线程池在Windows上更安全）
        if self.use_parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                future_results = {}

                # 提交所有任务
                for factor_name in self.factor_names:
                    future = executor.submit(self._load_single_factor, factor_name)
                    future_results[factor_name] = future

                # 收集结果
                for factor_name, future in future_results.items():
                    try:
                        factor_df = future.result()
                        if factor_df is not None:
                            loaded_factors[factor_name] = factor_df
                            print(f"✓ 成功加载因子: {factor_name}")
                        else:
                            failed_factors.append(factor_name)
                    except Exception as e:
                        print(f"✗ 加载因子 {factor_name} 失败: {e}")
                        failed_factors.append(factor_name)
        else:
            # 顺序执行 - 不使用并行
            for factor_name in self.factor_names:
                try:
                    factor_df = self._load_single_factor(factor_name)
                    if factor_df is not None:
                        loaded_factors[factor_name] = factor_df
                        print(f"✓ 成功加载因子: {factor_name}")
                    else:
                        failed_factors.append(factor_name)
                except Exception as e:
                    print(f"✗ 加载因子 {factor_name} 失败: {e}")
                    failed_factors.append(factor_name)

        if failed_factors:
            print(f"\n警告：以下因子加载失败: {failed_factors}")
            print("请检查因子名称是否正确，或重新运行因子计算步骤")

        if not loaded_factors:
            raise ValueError("没有成功加载任何因子数据")

        print(f"成功加载 {len(loaded_factors)} 个因子")
        return loaded_factors

    def _load_single_factor(self, factor_name):
        """**加载单个因子 - 供并行处理使用**"""
        # 创建安全的文件名
        safe_name = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in factor_name)
        file_path = f"{self.factor_dir}/{safe_name}.csv"

        if os.path.exists(file_path):
            # 读取CSV文件
            factor_df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            return factor_df
        else:
            print(f"✗ 文件不存在: {file_path}")
            return None

    def run_comprehensive_test(self, n_groups=5, save_all_group_charts=False,
                               skip_data_analysis=False, skip_correlation_analysis=False,
                               fast_mode=True, only_test_periods=None):
        """
        **运行完整的单因子测试流程 - 性能优化版**

        Parameters:
        -----------
        n_groups : int
            分组数量
        save_all_group_charts : bool
            是否保存所有因子的分组图表
        skip_data_analysis : bool
            是否跳过数据质量分析（耗时步骤）
        skip_correlation_analysis : bool
            是否跳过因子相关性分析（耗时步骤）
        fast_mode : bool
            快速模式，仅计算关键指标
        only_test_periods : list or None
            仅测试指定的预测期，如 ['20d_M']
        """
        start_time = time.time()
        print("====== 开始单因子测试 ======")
        print(f"测试因子数量: {len(self.factors)}")

        # 性能优化：可选跳过耗时步骤
        if not skip_data_analysis:
            print("\n【数据质量分析】")
            self._analyze_data_quality()
        else:
            print("\n【跳过数据质量分析】")

        if not skip_correlation_analysis:
            print("\n【因子相关性分析】")
            self._analyze_factor_correlation()
        else:
            print("\n【跳过因子相关性分析】")

        # 计算未来收益率
        print("\n【计算未来收益率】")
        forward_returns = self._calculate_forward_returns()

        # 如果只测试特定周期
        if only_test_periods:
            forward_returns = {k: v for k, v in forward_returns.items() if k in only_test_periods}
            print(f"仅测试以下周期: {list(forward_returns.keys())}")

        # 标准化因子
        print("\n【标准化因子】")
        std_factors = self._standardize_factors(fast_mode=fast_mode)

        # 批量测试
        print("\n【批量因子测试】")
        test_results = self._batch_test(std_factors, forward_returns, n_groups, fast_mode=fast_mode)

        # 汇总结果
        print("\n【汇总结果】")
        summary_results = self._summarize_results(test_results)

        # 保存结果
        print("\n【保存结果】")
        self._save_results(summary_results, test_results)

        # 可视化
        print("\n【生成可视化图表】")
        self._visualize_results(test_results, summary_results)

        # 保存分组净值数据
        if not fast_mode:
            print("\n【保存分组净值数据】")
            self._save_group_nav_data(test_results)

        elapsed_time = time.time() - start_time
        print(f"\n单因子测试完成！总耗时: {elapsed_time:.2f}秒")

        return {
            'factors': std_factors,
            'test_results': test_results,
            'summary': summary_results
        }

    def _analyze_data_quality(self):
        """**分析数据质量 - 包含缺失情况分析**"""
        print("分析因子数据质量...")

        # 创建数据质量分析目录
        quality_dir = f"{self.output_dir}/data_quality"
        os.makedirs(quality_dir, exist_ok=True)

        # 1. 整体缺失统计
        overall_stats = self._calculate_overall_missing_stats()

        # 2. 按因子的缺失分析
        factor_missing_stats = self._analyze_factor_missing()

        # 3. 按资产的缺失分析
        asset_missing_stats = self._analyze_asset_missing()

        # 4. 时间序列完整性分析
        time_series_stats = self._analyze_time_series_completeness()

        # 5. 保存到Excel
        self._save_data_quality_analysis(overall_stats, factor_missing_stats,
                                         asset_missing_stats, time_series_stats)

        # 6. 生成可视化
        self._visualize_data_quality()

        print("数据质量分析完成")

    def _calculate_overall_missing_stats(self):
        """**计算整体缺失统计**"""
        stats = {}

        for factor_name, factor_df in self.factors.items():
            total_cells = factor_df.shape[0] * factor_df.shape[1]
            missing_cells = factor_df.isna().sum().sum()

            stats[factor_name] = {
                '总单元格数': total_cells,
                '缺失单元格数': missing_cells,
                '缺失比例': missing_cells / total_cells,
                '有效行数': factor_df.dropna(how='all').shape[0],
                '有效列数': factor_df.dropna(how='all', axis=1).shape[1],
                '数据开始时间': factor_df.dropna(how='all').index.min(),
                '数据结束时间': factor_df.dropna(how='all').index.max(),
                '数据天数': len(factor_df.dropna(how='all'))
            }

        return pd.DataFrame(stats).T

    def _analyze_factor_missing(self):
        """**按因子分析缺失情况**"""
        factor_stats = {}

        for factor_name, factor_df in self.factors.items():
            # 按列（资产）统计缺失
            column_missing = factor_df.isna().sum()
            column_missing_pct = factor_df.isna().mean()

            # 按行（时间）统计缺失
            row_missing = factor_df.isna().sum(axis=1)
            row_missing_pct = factor_df.isna().mean(axis=1)

            factor_stats[factor_name] = {
                '资产缺失统计': pd.DataFrame({
                    '缺失天数': column_missing,
                    '缺失比例': column_missing_pct,
                    '有效天数': len(factor_df) - column_missing,
                    '数据开始时间': factor_df.apply(
                        lambda x: x.dropna().index.min() if not x.dropna().empty else pd.NaT),
                    '数据结束时间': factor_df.apply(
                        lambda x: x.dropna().index.max() if not x.dropna().empty else pd.NaT)
                }),
                '时间缺失统计': pd.DataFrame({
                    '缺失资产数': row_missing,
                    '缺失比例': row_missing_pct,
                    '有效资产数': factor_df.shape[1] - row_missing
                }),
                '缺失资产列表': column_missing[column_missing > 0].index.tolist(),
                '完全缺失资产': column_missing[column_missing == len(factor_df)].index.tolist()
            }

        return factor_stats

    def _analyze_asset_missing(self):
        """**按资产分析缺失情况**"""
        # 获取所有资产
        all_assets = set()
        for factor_df in self.factors.values():
            all_assets.update(factor_df.columns)
        all_assets = sorted(all_assets)

        asset_stats = {}

        for asset in all_assets:
            asset_data = {}

            for factor_name, factor_df in self.factors.items():
                if asset in factor_df.columns:
                    asset_series = factor_df[asset]
                    asset_data[factor_name] = {
                        '缺失天数': asset_series.isna().sum(),
                        '缺失比例': asset_series.isna().mean(),
                        '有效天数': asset_series.count(),
                        '数据开始时间': asset_series.dropna().index.min() if not asset_series.dropna().empty else pd.NaT,
                        '数据结束时间': asset_series.dropna().index.max() if not asset_series.dropna().empty else pd.NaT
                    }
                else:
                    asset_data[factor_name] = {
                        '缺失天数': len(list(self.factors.values())[0]),
                        '缺失比例': 1.0,
                        '有效天数': 0,
                        '数据开始时间': pd.NaT,
                        '数据结束时间': pd.NaT
                    }

            asset_stats[asset] = pd.DataFrame(asset_data).T

        return asset_stats

    def _analyze_time_series_completeness(self):
        """**时间序列完整性分析**"""
        time_stats = {}

        # 按月统计数据完整性
        for factor_name, factor_df in self.factors.items():
            monthly_completeness = factor_df.groupby(pd.Grouper(freq='M')).apply(
                lambda x: 1 - x.isna().mean().mean()
            )

            # 按年统计
            yearly_completeness = factor_df.groupby(pd.Grouper(freq='Y')).apply(
                lambda x: 1 - x.isna().mean().mean()
            )

            time_stats[factor_name] = {
                '月度完整性': monthly_completeness,
                '年度完整性': yearly_completeness,
                '数据覆盖率': 1 - factor_df.isna().mean().mean()
            }

        return time_stats

    def _save_data_quality_analysis(self, overall_stats, factor_missing_stats,
                                    asset_missing_stats, time_series_stats):
        """**保存数据质量分析结果**"""
        excel_path = f"{self.output_dir}/data_quality/数据质量分析报告.xlsx"

        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # 1. 整体统计
            overall_stats.to_excel(writer, sheet_name='整体缺失统计')

            # 2. 因子缺失详情
            for factor_name, stats in factor_missing_stats.items():
                # 资产缺失统计
                sheet_name = f'{factor_name[:20]}_资产缺失'  # 限制sheet名长度
                stats['资产缺失统计'].to_excel(writer, sheet_name=sheet_name)

                # 时间缺失统计（选择部分数据，避免过大）
                if len(stats['时间缺失统计']) > 1000:  # 如果数据太多，只保存摘要
                    summary_time = stats['时间缺失统计'].describe()
                    summary_time.to_excel(writer, sheet_name=f'{factor_name[:20]}_时间摘要')
                else:
                    stats['时间缺失统计'].to_excel(writer, sheet_name=f'{factor_name[:20]}_时间缺失')

            # 3. 资产缺失汇总
            asset_summary = {}
            for asset, stats in asset_missing_stats.items():
                asset_summary[asset] = {
                    '平均缺失比例': stats['缺失比例'].mean(),
                    '最大缺失比例': stats['缺失比例'].max(),
                    '完全缺失因子数': (stats['缺失比例'] == 1.0).sum(),
                    '有效因子数': (stats['缺失比例'] < 1.0).sum()
                }

            asset_summary_df = pd.DataFrame(asset_summary).T
            asset_summary_df.to_excel(writer, sheet_name='资产缺失汇总')

            # 4. 时间序列完整性
            time_completeness = {}
            for factor_name, stats in time_series_stats.items():
                time_completeness[factor_name] = {
                    '整体覆盖率': stats['数据覆盖率'],
                    '月度覆盖率均值': stats['月度完整性'].mean(),
                    '月度覆盖率最小值': stats['月度完整性'].min(),
                    '年度覆盖率均值': stats['年度完整性'].mean(),
                    '年度覆盖率最小值': stats['年度完整性'].min()
                }

            time_completeness_df = pd.DataFrame(time_completeness).T
            time_completeness_df.to_excel(writer, sheet_name='时间序列完整性')

            # 5. 数据开始时间汇总
            start_times = {}
            for factor_name, factor_df in self.factors.items():
                start_times[factor_name] = {}
                for asset in factor_df.columns:
                    first_valid = factor_df[asset].dropna().index.min()
                    start_times[factor_name][asset] = first_valid

            start_times_df = pd.DataFrame(start_times)
            start_times_df.to_excel(writer, sheet_name='数据开始时间')

        print(f"数据质量分析已保存至: {excel_path}")

    def _visualize_data_quality(self):
        """**可视化数据质量**"""
        # 1. 因子缺失热图
        plt.figure(figsize=(14, 10))

        # 准备缺失比例数据
        missing_matrix = {}
        for factor_name, factor_df in self.factors.items():
            missing_matrix[factor_name] = factor_df.isna().mean()

        missing_df = pd.DataFrame(missing_matrix).fillna(1.0)  # 用1.0填充不存在的资产

        # 只显示前30个资产（避免图表过大）
        if len(missing_df) > 50:
            missing_df = missing_df.head(50)

        sns.heatmap(missing_df, annot=True, fmt='.2f', cmap='Reds',
                    cbar_kws={'label': '缺失比例'})
        plt.title('因子数据缺失热图（前50个资产）')
        plt.xlabel('因子')
        plt.ylabel('资产')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/data_quality/因子缺失热图.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2. 因子整体缺失比例柱状图
        plt.figure(figsize=(12, 6))

        factor_missing_rates = {}
        for factor_name, factor_df in self.factors.items():
            factor_missing_rates[factor_name] = factor_df.isna().mean().mean()

        factors = list(factor_missing_rates.keys())
        rates = list(factor_missing_rates.values())

        bars = plt.bar(range(len(factors)), rates, color='skyblue', alpha=0.7)
        plt.xlabel('因子')
        plt.ylabel('缺失比例')
        plt.title('各因子整体缺失比例')
        plt.xticks(range(len(factors)), factors, rotation=45)
        plt.grid(True, alpha=0.3)

        # 添加数值标签
        for bar, rate in zip(bars, rates):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                     f'{rate:.1%}', ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/data_quality/因子缺失比例.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 3. 数据开始时间分布
        plt.figure(figsize=(14, 8))

        start_times = []
        factor_names = []

        for factor_name, factor_df in self.factors.items():
            start_time = factor_df.dropna(how='all').index.min()
            if pd.notna(start_time):
                start_times.append(start_time)
                factor_names.append(factor_name)

        if start_times:
            # 按时间排序
            sorted_data = sorted(zip(start_times, factor_names))
            start_times, factor_names = zip(*sorted_data)

            plt.figure(figsize=(12, 8))
            y_pos = np.arange(len(factor_names))

            bars = plt.barh(y_pos, [(t - min(start_times)).days for t in start_times],
                            color='lightgreen', alpha=0.7)

            plt.yticks(y_pos, factor_names)
            plt.xlabel('数据开始时间（相对于最早开始时间的天数）')
            plt.title('各因子数据开始时间分布')
            plt.grid(True, alpha=0.3)

            # 添加实际日期标签
            for i, (bar, start_time) in enumerate(zip(bars, start_times)):
                plt.text(bar.get_width() + 10, bar.get_y() + bar.get_height() / 2,
                         start_time.strftime('%Y-%m-%d'),
                         va='center', ha='left', fontsize=8)

        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/data_quality/数据开始时间分布.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _analyze_factor_correlation(self):
        """**分析因子相关性**"""
        print("分析因子相关性...")

        # 创建相关性分析目录
        corr_dir = f"{self.output_dir}/correlation"
        os.makedirs(corr_dir, exist_ok=True)

        # 1. 计算因子相关性矩阵
        correlation_matrix = self._calculate_factor_correlation_matrix()

        # 2. 识别高相关因子对
        high_corr_pairs = self._identify_high_correlation_pairs(correlation_matrix)

        # 3. 因子聚类分析
        factor_clusters = self._perform_factor_clustering(correlation_matrix)

        # 4. 保存相关性分析结果
        self._save_correlation_analysis(correlation_matrix, high_corr_pairs, factor_clusters)

        # 5. 可视化相关性
        self._visualize_factor_correlation(correlation_matrix, high_corr_pairs)

        print("因子相关性分析完成")

    def _calculate_factor_correlation_matrix(self):
        """**计算因子相关性矩阵**"""
        # 将所有因子数据合并
        all_factor_data = {}

        for factor_name, factor_df in self.factors.items():
            if factor_df is None or factor_df.empty:
                continue
            # 将二维因子数据转为一维序列
            try:
                factor_values = factor_df.stack().dropna()
            except Exception:
                continue
            factor_values.name = factor_name
            all_factor_data[factor_name] = factor_values

        # 创建因子数据矩阵
        if not all_factor_data:
            return pd.DataFrame()
        factor_matrix = pd.DataFrame(all_factor_data)

        # 计算相关性矩阵（使用Spearman相关性）
        correlation_matrix = factor_matrix.corr(method='spearman').replace([np.inf, -np.inf], np.nan).fillna(0.0)

        return correlation_matrix

    def _identify_high_correlation_pairs(self, correlation_matrix, threshold=0.7):
        """**识别高相关因子对**"""
        high_corr_pairs = []

        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                factor1 = correlation_matrix.columns[i]
                factor2 = correlation_matrix.columns[j]
                corr = correlation_matrix.iloc[i, j]

                if abs(corr) >= threshold:
                    high_corr_pairs.append({
                        'factor1': factor1,
                        'factor2': factor2,
                        'correlation': corr,
                        'abs_correlation': abs(corr)
                    })

        # 按相关性绝对值排序
        high_corr_pairs.sort(key=lambda x: x['abs_correlation'], reverse=True)

        return high_corr_pairs

    def _perform_factor_clustering(self, correlation_matrix):
        """**执行因子聚类分析（健壮版）**"""
        from sklearn.cluster import AgglomerativeClustering
        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import squareform
        import numpy as np
        import pandas as pd

        num_factors = correlation_matrix.shape[0]
        if num_factors < 3:
            print("因子数过少，跳过聚类分析。")
            return {
                'clusters': {},
                'linkage_matrix': None,
                'labels': []
            }

        # 构造相关性距离矩阵，处理非有限值
        corr = correlation_matrix.copy()
        corr = corr.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        corr.values[np.diag_indices_from(corr.values)] = 1.0

        distance_matrix = 1 - np.abs(corr)
        # 将非有限值置0（完全相似）并裁剪到[0,1]
        distance_matrix = distance_matrix.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        distance_matrix = distance_matrix.clip(lower=0.0, upper=1.0)

        # 转为condensed距离向量以进行层次聚类
        try:
            condensed = squareform(distance_matrix.values, checks=False)
        except Exception:
            # 如仍失败，则跳过聚类
            print("距离矩阵格式不合法，跳过聚类分析。")
            return {
                'clusters': {},
                'linkage_matrix': None,
                'labels': []
            }

        # 使用average链接（适合一般相异度），避免ward对欧氏距离的要求
        try:
            linkage_matrix = linkage(condensed, method='average')
        except Exception as e:
            print(f"构建层次聚类链时出错: {e}，跳过聚类分析。")
            return {
                'clusters': {},
                'linkage_matrix': None,
                'labels': []
            }

        # 使用预计算距离进行凝聚聚类
        n_clusters = min(5, num_factors)
        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='precomputed',
                linkage='average'
            )
            cluster_labels = clustering.fit_predict(distance_matrix)
        except Exception:
            # 回退：基于阈值的简单切分（全部归为一类）
            cluster_labels = np.zeros(num_factors, dtype=int)

        factor_clusters = {}
        for i, factor in enumerate(correlation_matrix.columns):
            cluster_id = int(cluster_labels[i])
            factor_clusters.setdefault(cluster_id, []).append(factor)

        return {
            'clusters': factor_clusters,
            'linkage_matrix': linkage_matrix,
            'labels': cluster_labels
        }

    def _save_correlation_analysis(self, correlation_matrix, high_corr_pairs, factor_clusters):
        """**保存相关性分析结果**"""
        excel_path = f"{self.output_dir}/correlation/因子相关性分析.xlsx"

        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # 1. 相关性矩阵
            correlation_matrix.to_excel(writer, sheet_name='相关性矩阵')

            # 2. 高相关因子对
            if high_corr_pairs:
                high_corr_df = pd.DataFrame(high_corr_pairs)
                high_corr_df.to_excel(writer, sheet_name='高相关因子对', index=False)

            # 3. 因子聚类结果
            cluster_results = []
            for cluster_id, factors in factor_clusters['clusters'].items():
                for factor in factors:
                    cluster_results.append({
                        'cluster_id': cluster_id,
                        'factor_name': factor,
                        'factor_category': self._categorize_factor(factor)
                    })

            cluster_df = pd.DataFrame(cluster_results)
            cluster_df.to_excel(writer, sheet_name='因子聚类结果', index=False)

            # 4. 聚类摘要
            cluster_summary = {}
            for cluster_id, factors in factor_clusters['clusters'].items():
                categories = [self._categorize_factor(f) for f in factors]
                cluster_summary[f'Cluster_{cluster_id}'] = {
                    '因子数量': len(factors),
                    '主要类别': max(set(categories), key=categories.count),
                    '因子列表': ', '.join(factors[:5])  # 只显示前5个
                }

            cluster_summary_df = pd.DataFrame(cluster_summary).T
            cluster_summary_df.to_excel(writer, sheet_name='聚类摘要')

        print(f"相关性分析已保存至: {excel_path}")

    def _visualize_factor_correlation(self, correlation_matrix, high_corr_pairs):
        """**可视化因子相关性**"""
        # 1. 相关性热图
        plt.figure(figsize=(16, 14))

        # 创建掩码，只显示下三角
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))

        # 绘制热图
        sns.heatmap(correlation_matrix, mask=mask, annot=True, fmt='.2f',
                    cmap='RdBu_r', center=0, square=True, linewidths=0.5,
                    cbar_kws={"shrink": .8})

        plt.title('因子相关性热图', fontsize=16)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/correlation/因子相关性热图.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2. 高相关因子对网络图
        if high_corr_pairs:
            plt.figure(figsize=(14, 10))

            # 准备网络图数据
            import networkx as nx

            G = nx.Graph()

            # 添加节点
            factors = set()
            for pair in high_corr_pairs:
                factors.add(pair['factor1'])
                factors.add(pair['factor2'])

            G.add_nodes_from(factors)

            # 添加边
            for pair in high_corr_pairs[:20]:  # 只显示前20个高相关对
                G.add_edge(pair['factor1'], pair['factor2'],
                           weight=pair['abs_correlation'])

            # 绘制网络图
            pos = nx.spring_layout(G, k=2, iterations=50)

            # 绘制节点
            nx.draw_networkx_nodes(G, pos, node_color='lightblue',
                                   node_size=1000, alpha=0.7)

            # 绘制边
            edges = G.edges()
            nx.draw_networkx_edges(G, pos, width=1.5,
                                   alpha=0.6, edge_color='gray')

            # 绘制标签
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

            plt.title('高相关因子网络图')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/correlation/高相关因子网络图.png', dpi=300, bbox_inches='tight')
            plt.close()

        # 3. 相关性分布直方图
        plt.figure(figsize=(10, 6))

        # 提取上三角相关系数
        upper_triangle = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)]

        plt.hist(upper_triangle, bins=50, alpha=0.7, edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.8, label='零相关')
        plt.axvline(x=0.7, color='orange', linestyle='--', alpha=0.8, label='高正相关阈值')
        plt.axvline(x=-0.7, color='orange', linestyle='--', alpha=0.8, label='高负相关阈值')

        plt.xlabel('相关系数')
        plt.ylabel('频数')
        plt.title('因子相关系数分布')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/correlation/相关系数分布.png', dpi=300, bbox_inches='tight')
        plt.close()

    # 原有的其他方法保持不变...
    def _calculate_forward_returns(self):
        """计算未来收益率"""
        print("计算未来收益率...")
        forward_returns = {}

        # 日度收益
        forward_returns['20d'] = self.close_df.shift(-20) / self.close_df - 1

        # 周度调仓收益
        weekly_dates = self.close_df.groupby(pd.Grouper(freq='W')).apply(
            lambda x: x.index[-1] if len(x) > 0 else None).dropna().tolist()

        weekly_returns = pd.DataFrame(index=self.close_df.index, columns=self.close_df.columns)
        for i, date in enumerate(weekly_dates[:-1]):
            next_date = weekly_dates[i + 1]
            if date in self.close_df.index and next_date in self.close_df.index:
                weekly_returns.loc[date] = self.close_df.loc[next_date] / self.close_df.loc[date] - 1

        forward_returns['5d_W'] = weekly_returns

        # 月度调仓收益
        monthly_dates = self.close_df.groupby(pd.Grouper(freq='M')).apply(
            lambda x: x.index[-1] if len(x) > 0 else None).dropna().tolist()

        monthly_returns = pd.DataFrame(index=self.close_df.index, columns=self.close_df.columns)
        for i, date in enumerate(monthly_dates[:-1]):
            next_date = monthly_dates[i + 1]
            if date in self.close_df.index and next_date in self.close_df.index:
                monthly_returns.loc[date] = self.close_df.loc[next_date] / self.close_df.loc[date] - 1

        forward_returns['20d_M'] = monthly_returns

        print("未来收益率计算完成")
        return forward_returns

    def _standardize_factors(self, fast_mode=False):
        """**标准化因子 - 性能优化版**"""
        print("因子标准化中...")
        start_time = time.time()
        std_factors = {}

        # 使用线程池代替进程池
        if self.use_parallel:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                futures = []

                # 提交所有任务
                for name, factor_df in self.factors.items():
                    future = executor.submit(self._standardize_single_factor, factor_df, fast_mode)
                    futures.append((name, future))

                # 收集结果
                for name, future in futures:
                    try:
                        std_df = future.result()
                        std_factors[name] = std_df
                    except Exception as e:
                        print(f"标准化因子 {name} 时出错: {e}")
        else:
            # 顺序执行
            for name, factor_df in self.factors.items():
                try:
                    std_df = self._standardize_single_factor(factor_df, fast_mode)
                    std_factors[name] = std_df
                except Exception as e:
                    print(f"标准化因子 {name} 时出错: {e}")

        elapsed_time = time.time() - start_time
        print(f"因子标准化完成, 耗时: {elapsed_time:.2f}秒")
        return std_factors

    def _standardize_single_factor(self, factor_df, fast_mode=False):
        """**标准化单个因子 - 供并行处理使用**"""
        std_df = factor_df.copy()

        # 如果是快速模式，只处理调仓日（假设月末为调仓日）
        if fast_mode:
            # 找出可能的月末日期
            month_end_dates = std_df.groupby(pd.Grouper(freq='M')).apply(
                lambda x: x.index[-1] if len(x) > 0 else None).dropna().tolist()
            dates_to_process = month_end_dates
        else:
            dates_to_process = std_df.index

        for date in dates_to_process:
            if date not in std_df.index:
                continue

            row = std_df.loc[date].dropna()
            if len(row) > 2:
                # 3-sigma缩尾
                mean, std = row.mean(), row.std()
                if std > 0:
                    lower, upper = mean - 3 * std, mean + 3 * std
                    winsorized = np.clip(row, lower, upper)

                    # 标准化
                    win_mean, win_std = winsorized.mean(), winsorized.std()
                    if win_std > 0:
                        std_df.loc[date] = (winsorized - win_mean) / win_std

        return std_df

    def _batch_test(self, factors, forward_returns, n_groups, fast_mode=False):
        """**批量测试因子 - 使用线程池而非进程池**"""
        print("执行批量因子测试...")
        start_time = time.time()
        results = {}

        self.forward_returns = forward_returns

        for period, return_df in forward_returns.items():
            print(f"测试 {period} 期收益...")
            period_start_time = time.time()
            period_results = {}

            if self.use_parallel:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.n_jobs) as executor:
                    futures = []

                    # 提交所有任务
                    for name, factor_df in factors.items():
                        future = executor.submit(
                            self._single_factor_test, factor_df, return_df, n_groups, period, fast_mode
                        )
                        futures.append((name, future))

                    # 收集结果
                    completed = 0
                    for name, future in futures:
                        try:
                            result = future.result()
                            period_results[name] = result
                            completed += 1
                            # 每完成5个或所有任务完成时显示进度
                            if completed % 5 == 0 or completed == len(futures):
                                print(f"  进度: {completed}/{len(futures)} ({completed / len(futures) * 100:.1f}%)")
                        except Exception as e:
                            print(f"✗ 测试因子 {name} 失败: {e}")
            else:
                # 顺序执行
                for i, (name, factor_df) in enumerate(factors.items()):
                    try:
                        
                        result = self._single_factor_test(factor_df, return_df, n_groups, period, fast_mode)
                        period_results[name] = result
                        # 每完成5个或所有任务完成时显示进度
                        if (i + 1) % 5 == 0 or (i + 1) == len(factors):
                            print(f"  进度: {i + 1}/{len(factors)} ({(i + 1) / len(factors) * 100:.1f}%)")
                    except Exception as e:
                        print(f"✗ 测试因子 {name} 失败: {e}")

            results[period] = period_results
            period_elapsed = time.time() - period_start_time
            print(f"  {period} 测试完成, 耗时: {period_elapsed:.2f}秒")

        total_elapsed = time.time() - start_time
        print(f"批量因子测试完成, 总耗时: {total_elapsed:.2f}秒")
        return results

    def _single_factor_test(self, factor_df, return_df, n_groups, period, fast_mode=False):
        """**单因子测试 - 不使用静态方法**"""
        # 计算IC
        ic_series = self._calculate_ic(factor_df, return_df, fast_mode)

        # 分组回测
        group_returns = self._calculate_group_returns(factor_df, return_df, n_groups, fast_mode)
        # 构建结果
        long_short = group_returns[f'G{n_groups}'] - group_returns['G1']
        top_group = group_returns[f'G{n_groups}']

        # 计算年化指标
        if 'W' in period:
            annual_factor = 52
        elif 'M' in period:
            annual_factor = 12
        else:
            annual_factor = 252

        results = {
            'IC': ic_series,
            'IC_mean': ic_series.mean(),
            'IC_std': ic_series.std(),
            'IC_IR': ic_series.mean() / ic_series.std() if ic_series.std() > 0 else np.nan,
            'group_returns': group_returns,
            'long_short_returns': long_short,
            'top_group_returns': top_group,
            'top_group_cumulative': (1 + top_group.fillna(0)).cumprod(),
            'long_short_cumulative': (1 + long_short.fillna(0)).cumprod(),
            'top_group_annual_return': (1 + top_group.mean()) ** annual_factor - 1,
            'long_short_annual_return': (1 + long_short.mean()) ** annual_factor - 1,
            'top_group_annual_vol': top_group.std() * np.sqrt(annual_factor),
            'long_short_annual_vol': long_short.std() * np.sqrt(annual_factor),
            'top_group_win_rate': (top_group > 0).mean(),
            'long_short_win_rate': (long_short > 0).mean()
        }

        # 计算夏普比率
        results['top_group_sharpe'] = results['top_group_annual_return'] / results['top_group_annual_vol'] if results[
                                                                                                                  'top_group_annual_vol'] > 0 else np.nan
        results['long_short_sharpe'] = results['long_short_annual_return'] / results['long_short_annual_vol'] if \
        results['long_short_annual_vol'] > 0 else np.nan

        # 计算最大回撤
        cum_top = results['top_group_cumulative']
        cum_ls = results['long_short_cumulative']

        results['top_group_max_drawdown'] = ((cum_top / cum_top.cummax() - 1).min() if len(cum_top) > 0 else np.nan)
        results['long_short_max_drawdown'] = ((cum_ls / cum_ls.cummax() - 1).min() if len(cum_ls) > 0 else np.nan)

        return results

    def _calculate_ic(self, factor_df, return_df, fast_mode=False):
        """**计算IC值**"""
        ic_series = pd.Series(index=factor_df.index)

        # 如果是快速模式，只计算调仓日的IC
        if fast_mode:
            # 只处理return_df中有值的日期（通常是调仓日）
            dates_to_process = return_df.dropna(how='all').index
        else:
            dates_to_process = factor_df.index

        for date in dates_to_process:
            if date not in factor_df.index or date not in return_df.index:
                continue

            factor_values = factor_df.loc[date].dropna()
            returns = return_df.loc[date].reindex(factor_values.index).dropna()

            common_assets = set(factor_values.index) & set(returns.index)
            if len(common_assets) < 5:
                continue

            factor_values = factor_values.reindex(list(common_assets))
            returns = returns.reindex(list(common_assets))

            try:
                fv = np.asarray(factor_values.to_numpy(), dtype=float)
                rv = np.asarray(returns.to_numpy(), dtype=float)
                corr, _ = spearmanr(fv, rv)
                if not np.isnan(corr):
                    ic_series[date] = corr
            except:
                continue

        return ic_series

    def _calculate_group_returns(self, factor_df, return_df, n_groups, fast_mode=False):
        """**计算分组收益**"""
        group_returns = pd.DataFrame(index=factor_df.index)
        group_cols = [f'G{i + 1}' for i in range(n_groups)]
        group_returns = group_returns.reindex(columns=group_cols)

        # 如果是快速模式，只计算调仓日的分组收益
        if fast_mode:
            # 只处理return_df中有值的日期（通常是调仓日）
            dates_to_process = return_df.dropna(how='all').index
        else:
            dates_to_process = factor_df.index
        self.factor_df = factor_df
        self.return_df = return_df
        for date in dates_to_process:
            if date not in factor_df.index or date not in return_df.index:
                continue

            factor_values = factor_df.loc[date].dropna()
            
            returns = return_df.loc[date].reindex(factor_values.index).dropna()

            common_assets = set(factor_values.index) & set(returns.index)
            if len(common_assets) < n_groups:
                continue

            factor_values = factor_values.reindex(list(common_assets))
            returns = returns.reindex(list(common_assets))
            try:
                bins = pd.qcut(
                    factor_values,
                    n_groups,
                    labels=[f'G{i + 1}' for i in range(n_groups)]
                    )
                group_rets = returns.groupby(bins).mean()

                for group, ret in group_rets.items():
                    group_returns.loc[date, group] = ret
            except:
                pass
        return group_returns
    def _summarize_results(self, test_results):
        """汇总测试结果"""
        summary_results = {}

        for period, period_results in test_results.items():
            summary = pd.DataFrame(index=period_results.keys())

            for factor, result in period_results.items():
                summary.loc[factor, 'IC_mean'] = result['IC_mean']
                summary.loc[factor, 'IC_IR'] = result['IC_IR']
                summary.loc[factor, 'top_group_annual_return'] = result['top_group_annual_return']
                summary.loc[factor, 'long_short_annual_return'] = result['long_short_annual_return']
                summary.loc[factor, 'top_group_sharpe'] = result['top_group_sharpe']
                summary.loc[factor, 'long_short_sharpe'] = result['long_short_sharpe']
                summary.loc[factor, 'top_group_win_rate'] = result['top_group_win_rate']
                summary.loc[factor, 'top_group_max_drawdown'] = result['top_group_max_drawdown']

            summary = summary.sort_values('IC_IR', ascending=False)
            summary_results[period] = summary

        return summary_results

    def _save_results(self, summary_results, test_results):
        """保存测试结果"""
        print("保存测试结果...")

        with pd.ExcelWriter(f'{self.output_dir}/单因子测试结果.xlsx', engine='xlsxwriter') as writer:
            for period, summary in summary_results.items():
                # 添加因子分类
                summary['因子类别'] = summary.index.map(self._categorize_factor)
                summary.to_excel(writer, sheet_name=f'{period}期收益')

        print(f"测试结果已保存至 {self.output_dir}/单因子测试结果.xlsx")

    def _visualize_results(self, test_results, summary_results, top_n=5):
        """可视化结果"""
        print("生成可视化图表...")

        # 获取表现最好的因子
        period = '5d_W'
        if period in test_results:
            period_results = test_results[period]
            factor_ic_ir = [(name, result['IC_IR'])
                            for name, result in period_results.items()
                            if not np.isnan(result['IC_IR'])]
            top_factors = sorted(factor_ic_ir, key=lambda x: x[1], reverse=True)[:top_n]
            top_factor_names = [x[0] for x in top_factors]

            # IC时间序列图
            plt.figure(figsize=(12, 6))
            for factor_name in top_factor_names:
                ic_series = period_results[factor_name]['IC']
                plt.plot(ic_series.index, ic_series.values, label=factor_name)

            plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
            plt.title(f'Top {top_n} 因子 IC 时间序列')
            plt.xlabel('日期')
            plt.ylabel('IC值')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/top_factors_IC.png', dpi=300)
            plt.close()

            # 累积收益图
            plt.figure(figsize=(12, 6))
            for factor_name in top_factor_names:
                cum_returns = period_results[factor_name]['top_group_cumulative']
                plt.plot(cum_returns.index, cum_returns.values, label=factor_name)

            plt.title(f'Top {top_n} 因子多头组合累积收益')
            plt.xlabel('日期')
            plt.ylabel('累积收益')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/top_factors_returns.png', dpi=300)
            plt.close()

            # **新增：绘制分组净值图**
            self._plot_group_performance(period_results, top_factor_names, period)

        # **新增：为所有因子绘制分组净值图**
        self._plot_all_factors_group_performance(test_results,save_all=True)
        
        # **新增：绘制多头组相对等权基准的超额曲线**
        self._plot_excess_return_curves(test_results, top_factor_names, period)

    def _calculate_equal_weight_returns(self, period):
        """**计算等权基准收益 - 周度再平衡**"""
        try:
            # 获取对应的收益率数据
            if period in self.forward_returns:
                return_df = self.forward_returns[period]
            else:
                print(f"警告：未找到 {period} 期的收益率数据")
                return None

            # 计算等权收益：每个调仓日，所有有收益数据的资产等权重
            equal_weight_returns = pd.Series(index=return_df.index, dtype=float)

            for date in return_df.index:
                if date not in return_df.index:
                    continue

                # 获取当日所有资产的收益率
                daily_returns = return_df.loc[date].dropna()
                
                if len(daily_returns) > 0:
                    # 等权重：每个资产权重相等
                    equal_weight_returns[date] = daily_returns.mean()
                else:
                    equal_weight_returns[date] = np.nan

            return equal_weight_returns

        except Exception as e:
            print(f"计算等权基准收益时出错: {e}")
            return None

    def _plot_excess_return_curve(self, factor_name, factor_result, equal_weight_returns, period, group_dir):
        """**绘制多头组相对等权的超额曲线**"""
        if equal_weight_returns is None:
            print(f"跳过 {factor_name} 超额曲线：等权基准数据不可用")
            return

        # 获取多头组收益
        top_group_returns = factor_result['top_group_returns'].fillna(0)
        
        # 统一时间索引：找到所有数据的共同时间范围
        common_dates = top_group_returns.index.intersection(equal_weight_returns.index)
        if len(common_dates) == 0:
            print(f"跳过 {factor_name} 超额曲线：没有共同的时间数据")
            return
            
        # 对齐数据到共同时间范围
        top_group_returns_aligned = top_group_returns.loc[common_dates]
        equal_weight_returns_aligned = equal_weight_returns.loc[common_dates]
        
        # 计算超额收益
        excess_returns = top_group_returns_aligned - equal_weight_returns_aligned.fillna(0)
        
        # 计算累积净值
        cumulative_excess = (1 + excess_returns).cumprod()
        cumulative_top = (1 + top_group_returns_aligned).cumprod()
        cumulative_equal = (1 + equal_weight_returns_aligned.fillna(0)).cumprod()

        # 绘制净值曲线对比图
        plt.figure(figsize=(14, 10))

        # 主图：净值曲线对比
        plt.subplot(2, 2, 1)
        plt.plot(cumulative_top.index, cumulative_top.values, 
                label='多头组净值', linewidth=2, color='blue', alpha=0.8)
        plt.plot(cumulative_equal.index, cumulative_equal.values, 
                label='等权基准净值', linewidth=2, color='red', alpha=0.8)
        plt.title(f'{factor_name} - 净值曲线对比 ({period})')
        plt.ylabel('累积净值')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图1：超额净值曲线
        plt.subplot(2, 2, 2)
        plt.plot(cumulative_excess.index, cumulative_excess.values, 
                label='多头组超额净值', linewidth=2, color='green', alpha=0.8)
        plt.axhline(y=1, color='black', linestyle='--', alpha=0.5, label='基准线')
        plt.title(f'{factor_name} - 超额净值曲线 ({period})')
        plt.ylabel('累积超额净值')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图2：超额收益分布
        plt.subplot(2, 2, 3)
        plt.hist(excess_returns.dropna(), bins=30, alpha=0.7, color='lightblue', edgecolor='black')
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.8, label='零超额线')
        plt.xlabel('超额收益')
        plt.ylabel('频数')
        plt.title('超额收益分布')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 子图3：滚动超额收益（12期移动平均）
        plt.subplot(2, 2, 4)
        rolling_excess = excess_returns.rolling(window=12).mean()
        plt.plot(rolling_excess.index, rolling_excess.values, 
                label='12期滚动超额收益', linewidth=2, color='orange', alpha=0.8)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5, label='零线')
        plt.title(f'{factor_name} - 滚动超额收益 ({period})')
        plt.ylabel('滚动超额收益')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # 保存图片
        safe_name = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in factor_name)
        plt.savefig(f'{group_dir}/{safe_name}_超额曲线.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 计算超额收益统计指标
        self._calculate_excess_return_stats(factor_name, excess_returns, cumulative_excess, period, group_dir)

        print(f"✓ 已保存 {factor_name} 超额曲线图")

    def _calculate_excess_return_stats(self, factor_name, excess_returns, cumulative_excess, period, group_dir):
        """**计算超额收益统计指标**"""
        # 计算年化因子
        if 'W' in period:
            annual_factor = 52
        elif 'M' in period:
            annual_factor = 12
        else:
            annual_factor = 252

        # 计算统计指标
        stats = {
            '平均超额收益': excess_returns.mean(),
            '超额收益标准差': excess_returns.std(),
            '年化超额收益': (1 + excess_returns.mean()) ** annual_factor - 1,
            '年化超额收益波动率': excess_returns.std() * np.sqrt(annual_factor),
            '信息比率': excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else np.nan,
            '胜率': (excess_returns > 0).mean(),
            '最大超额收益': excess_returns.max(),
            '最小超额收益': excess_returns.min(),
            '最大回撤': ((cumulative_excess / cumulative_excess.cummax() - 1).min() if len(cumulative_excess) > 0 else np.nan)
        }

        # 保存统计结果
        stats_items = list(stats.items())
        stats_df = pd.DataFrame(stats_items, columns=['指标', '数值'])
        safe_name = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in factor_name)
        stats_df.to_csv(f'{group_dir}/{safe_name}_超额收益统计.csv', index=False, encoding='utf-8-sig')

        print(f"✓ 已保存 {factor_name} 超额收益统计")
        print(f"  年化超额收益: {stats['年化超额收益']:.2%}")
        print(f"  信息比率: {stats['信息比率']:.3f}")
        print(f"  胜率: {stats['胜率']:.2%}")
        print(f"  最大回撤: {stats['最大回撤']:.2%}")

    def _plot_group_performance(self, period_results, top_factor_names, period, n_groups=5):
        """**绘制Top因子的分组净值表现**"""
        print("绘制分组净值图...")

        # 创建分组净值图目录
        group_dir = f"{self.output_dir}/group_performance"
        os.makedirs(group_dir, exist_ok=True)

        # 为每个Top因子绘制分组净值图
        for factor_name in top_factor_names:
            if factor_name not in period_results:
                continue

            group_returns = period_results[factor_name]['group_returns']

            if group_returns.empty:
                print(f"跳过 {factor_name}：无分组收益数据")
                continue

            # 计算各组累积净值
            plt.figure(figsize=(14, 8))

            # 使用tab10调色板，循环取色
            cmap = plt.get_cmap('tab10')
            colors = [cmap((i - 1) % 10) for i in range(1, n_groups + 1)]

            for i in range(1, n_groups + 1):
                group_col = f'G{i}'
                if group_col in group_returns.columns:
                    group_ret = group_returns[group_col].fillna(0)
                    cum_nav = (1 + group_ret).cumprod()

                    plt.plot(cum_nav.index, cum_nav.values,
                             label=f'第{i}组{"(多头)" if i == n_groups else ("(空头)" if i == 1 else "")}',
                             linewidth=2, color=colors[i - 1], alpha=0.8)

            # 添加多空组合
            long_short_ret = period_results[factor_name]['long_short_returns'].fillna(0)
            long_short_nav = (1 + long_short_ret).cumprod()
            plt.plot(long_short_nav.index, long_short_nav.values,
                     label='多空组合', linewidth=3, color='red', linestyle='--', alpha=0.9)

            plt.title(f'{factor_name} - 分组净值表现 ({period})')
            plt.xlabel('日期')
            plt.ylabel('累积净值')
            plt.legend(loc='best')
            plt.grid(True, alpha=0.3)

            # 添加绩效统计信息
            ic_ir = period_results[factor_name]['IC_IR']
            annual_ret = period_results[factor_name]['top_group_annual_return']
            sharpe = period_results[factor_name]['top_group_sharpe']
            max_dd = period_results[factor_name]['top_group_max_drawdown']

            info_text = f'IC_IR: {ic_ir:.3f}\n多头年化收益: {annual_ret:.2%}\n多头夏普比率: {sharpe:.2f}\n多头最大回撤: {max_dd:.2%}'
            plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes,
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()

            # 保存图片
            safe_name = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in factor_name)
            plt.savefig(f'{group_dir}/{safe_name}_分组净值.png', dpi=300, bbox_inches='tight')
            plt.close()

            print(f"✓ 已保存 {factor_name} 分组净值图")

    def _plot_excess_return_curves(self, test_results, top_factor_names, period):
        """**绘制多头组相对等权基准的超额曲线**"""
        print("绘制多头组相对等权基准的超额曲线...")

        # 创建分组净值图目录
        group_dir = f"{self.output_dir}/group_performance"
        os.makedirs(group_dir, exist_ok=True)

        # 计算等权基准收益
        equal_weight_returns = self._calculate_equal_weight_returns(period)

        if equal_weight_returns is None:
            print("警告：无法计算等权基准收益，跳过超额曲线绘制")
            return

        # 为每个Top因子绘制超额曲线
        for factor_name in top_factor_names:
            if factor_name not in test_results[period]:
                continue

            factor_result = test_results[period][factor_name]
            self._plot_excess_return_curve(factor_name, factor_result, equal_weight_returns, period, group_dir)

    def _plot_all_factors_group_performance(self, test_results, save_all=False):
        """**为所有因子绘制分组净值表现（可选）**"""

        if not save_all:
            print("跳过所有因子分组净值图绘制（如需绘制，请设置save_all=True）")
            return

        print("为所有因子绘制分组净值图...")

        period = '20d_M'
        if period not in test_results:
            return

        period_results = test_results[period]
        all_group_dir = f"{self.output_dir}/all_factors_group_performance"
        os.makedirs(all_group_dir, exist_ok=True)

        for factor_name, result in period_results.items():
            group_returns = result['group_returns']

            if group_returns.empty:
                continue

            try:
                plt.figure(figsize=(12, 6))

                # 只绘制第1组、第5组和多空组合（简化版本）
                if 'G1' in group_returns.columns and 'G5' in group_returns.columns:
                    g1_nav = (1 + group_returns['G1'].fillna(0)).cumprod()
                    g5_nav = (1 + group_returns['G5'].fillna(0)).cumprod()
                    ls_nav = (1 + result['long_short_returns'].fillna(0)).cumprod();

                    plt.plot(g1_nav.index, g1_nav.values, label='第1组(空头)', color='red', alpha=0.7)
                    plt.plot(g5_nav.index, g5_nav.values, label='第5组(多头)', color='blue', alpha=0.7)
                    plt.plot(ls_nav.index, ls_nav.values, label='多空组合', color='green', linewidth=2)

                    plt.title(f'{factor_name} - 分组净值')
                    plt.xlabel('日期')
                    plt.ylabel('累积净值')
                    plt.legend()
                    plt.grid(True, alpha=0.3)

                    safe_name = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in factor_name)
                    plt.savefig(f'{all_group_dir}/{safe_name}_简化分组净值.png', dpi=200, bbox_inches='tight')

                plt.close()

            except Exception as e:
                print(f"绘制 {factor_name} 分组净值图时出错: {e}")
                plt.close()
                continue

    def _save_group_nav_data(self, test_results):
        """**保存分组净值数据到Excel**"""
        print("保存分组净值数据...")

        period = '20d_M'
        if period not in test_results:
            return

        period_results = test_results[period]
        nav_excel_path = f"{self.output_dir}/分组净值数据.xlsx"

        with pd.ExcelWriter(nav_excel_path, engine='xlsxwriter') as writer:

            for factor_name, result in period_results.items():
                group_returns = result['group_returns']

                if group_returns.empty:
                    continue

                # 计算各组累积净值
                group_nav_data = {}

                # 各分组净值
                for col in group_returns.columns:
                    if col.startswith('G'):
                        group_ret = group_returns[col].fillna(0)
                        group_nav_data[f'{col}组净值'] = (1 + group_ret).cumprod()

                # 多空组合净值
                long_short_ret = result['long_short_returns'].fillna(0)
                group_nav_data['多空组合净值'] = (1 + long_short_ret).cumprod()

                # 多头组合净值
                top_group_ret = result['top_group_returns'].fillna(0)
                group_nav_data['多头组合净值'] = (1 + top_group_ret).cumprod()

                if group_nav_data:
                    nav_df = pd.DataFrame(group_nav_data)

                    # 限制sheet名称长度
                    sheet_name = factor_name[:25] if len(factor_name) > 25 else factor_name
                    sheet_name = "".join(c if c.isalnum() or c in ['-', '_', ' '] else '_' for c in sheet_name)

                    nav_df.to_excel(writer, sheet_name=sheet_name, index=True)

        print(f"分组净值数据已保存至: {nav_excel_path}")

    def _categorize_factor(self, factor_name):
        """因子分类"""
        if 'momentum' in factor_name or '动量' in factor_name:
            return '动量类'
        elif 'reversal' in factor_name or '反转' in factor_name:
            return '反转类'
        elif 'ma' in factor_name or 'MA' in factor_name:
            return '均线类'
        elif 'vol' in factor_name or '波动' in factor_name:
            return '波动率类'
        elif 'volume' in factor_name or '量价' in factor_name or 'turn' in factor_name:
            return '量价类'
        elif 'atr' in factor_name or 'bb_' in factor_name:
            return 'OHLC类'
        elif 'CAPM' in factor_name:
            return 'CAPM类'
        else:
            return '其他类'
