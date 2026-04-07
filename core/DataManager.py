import pandas as pd
import numpy as np
import os
import warnings
from pathlib import Path
from core.Logger import logger

class UniverseManager:
    """
    股票池管理器：负责加载指数成分股并按时间过滤
    支持格式：IndexCode, IndexName, SecCode, SecName, InDate, OutDate
    """
    def __init__(self, base_path = 'D:/DATA'):
        self.base_path = base_path 
        self._cache = {}

    def get_constituents(self, universe_id: str):
        """
        读取特定指数的成分股文件
        universe_id: '000905' or '000852'
        """
        if universe_id in self._cache:
            return self._cache[universe_id]
        
        filename = f"{universe_id}_comp.csv"
        path = self.base_path / filename
        
        if not path.exists():
            logger.error(f"Universe file not found: {path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(path)
            # 标准化列名映射
            col_map = {
                'seccode': 'code',
                'indate': 'indate',
                'outdate': 'outdate'
            }
            # 统一列名为小写方便匹配
            raw_cols = {c.lower(): c for c in df.columns}
            rename_dict = {}
            for target, standard in col_map.items():
                if target in raw_cols:
                    rename_dict[raw_cols[target]] = standard
            
            df = df.rename(columns=rename_dict)
            
            # 转换日期
            df['indate'] = pd.to_datetime(df['indate'])
            df['outdate'] = pd.to_datetime(df['outdate'])
            # 格式化代码
            df['code'] = df['code'].astype(str).str.zfill(6)
            
            self._cache[universe_id] = df
            return df
        except Exception as e:
            logger.error(f"Error reading universe file {path}: {e}")
            return pd.DataFrame()

    def filter_by_date(self, universe_id: str, target_date: pd.Timestamp):
        """
        获取特定日期在股票池中的代码列表
        """
        df = self.get_constituents(universe_id)
        if df.empty:
            return []
            
        # 逻辑：indate <= target_date AND (outdate > target_date OR outdate is null)
        mask = (df['indate'] <= target_date) & ((df['outdate'] > target_date) | (df['outdate'].isna()))
        return df.loc[mask, 'code'].tolist()

class DataProvider:
    """
    数据接入层：负责统一管理本地数据读取、缓存和基础清洗
    """
    def __init__(self, base_data_path: str = None):
        # 如果没有指定路径，尝试定位到 D:\DATA 目录
        if base_data_path is None:
            potential_data_path = Path("D:/DATA")
            if potential_data_path.exists():
                self.base_path = potential_data_path
            else:
                # 兼容旧路径或相对路径逻辑
                current_file = Path(__file__).resolve()
                project_root = current_file.parent.parent
                self.base_path = project_root
        else:
            self.base_path = Path(base_data_path)
            
        self.universe_mgr = UniverseManager(self.base_path)

    def _read_raw_file(self, path: Path):
        """
        [Internal] 原子化读取原始文件，处理编码和 Excel 损坏。
        """
        path_str = str(path)
        if path_str.endswith('.csv'):
            try:
                return pd.read_csv(path, encoding='gbk')
            except UnicodeDecodeError:
                return pd.read_csv(path, encoding='utf-8')
        elif path_str.endswith('.xlsx') or path_str.endswith('.xls'):
            try:
                return pd.read_excel(path)
            except Exception as e:
                if "NamedCellStyle" in str(e) or "NoneType" in str(e):
                    return self._fix_broken_excel(path)
                else:
                    logger.error(f"读取Excel出错 {path}: {e}")
                    return pd.DataFrame()
        else:
            logger.error(f"不支持的文件格式: {path}")
            return pd.DataFrame()

    def _fix_broken_excel(self, path: Path):
        """
        [Internal] 修复损坏的 Excel 样式：移除 xl/styles.xml。
        """
        import zipfile
        import io
        try:
            with zipfile.ZipFile(path, 'r') as zin:
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, 'w') as zout:
                    for item in zin.infolist():
                        if item.filename != 'xl/styles.xml':
                            zout.writestr(item, zin.read(item.filename))
                        else:
                            zout.writestr(item, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"></styleSheet>')
                buffer.seek(0)
                return pd.read_excel(buffer, engine='openpyxl')
        except Exception as e:
            logger.error(f"修复Excel并读取失败 {path}: {e}")
            return pd.DataFrame()

    def _clean_wind_metadata(self, df: pd.DataFrame):
        """
        清洗 standard OHLC 导出文件的元数据（表头描述行及表尾备注）。
        """
        if df.empty:
            return df
            
        # 1. 处理多行表头元数据
        metadata_keywords = ['指标名称', '频率', '单位', '指标id', '来源', '指标ID', '数据来源', '开始日期', '截止日期', '证券代码', '证券简称']
        date_keywords = ['日期', 'date', '时间', 'time', 'trade_date', 'trade_dt', 's_info_date']
        ohlc_kws = ['开盘', '最高', '最低', '收盘', '成交量', '成交额', 'open', 'high', 'low', 'close', 'vol', 'amt', 'value']

        header_row_idx = None
        # 扫描前 30 行寻找真正的表头
        for i in range(min(30, len(df))):
            row_vals = [str(x).lower().strip() for x in df.iloc[i].values if pd.notna(x)]
            if any(k in row_vals for k in date_keywords):
                if any(k in row_vals for k in ohlc_kws):
                    header_row_idx = i
                    logger.info(f"Detected standard OHLC header at row {i}")
                    break
        
        if header_row_idx is not None:
            # 提取表头及其后的数据
            new_df = df.iloc[header_row_idx+1:].copy()
            new_df.columns = [str(c).strip() for c in df.iloc[header_row_idx].values]
            
            # 检查下一行是否是辅助表头（如英文名）
            if len(new_df) > 0:
                next_row_vals = [str(x).lower().strip() for x in new_df.iloc[0].values if pd.notna(x)]
                if any(k in next_row_vals for k in ['date', 'open', 'high', 'low', 'close', 'volume', 'amt', 'amount']):
                    # 优先取下一行（通常是英文标识）作为列名，除非它是空
                    final_cols = []
                    for col_idx in range(len(new_df.columns)):
                        val_en = str(new_df.iloc[0, col_idx]).strip() if pd.notna(new_df.iloc[0, col_idx]) else ""
                        val_zh = str(new_df.columns[col_idx]).strip() if pd.notna(new_df.columns[col_idx]) else ""
                        final_cols.append(val_en if val_en else val_zh)
                    new_df = new_df.iloc[1:].reset_index(drop=True)
                    new_df.columns = final_cols
                else:
                    new_df = new_df.reset_index(drop=True)
            return new_df

        # 兜底：兼容旧版本的单行关键词剔除逻辑
        rows_to_drop = []
        for i in range(min(15, len(df))):
            first_val = str(df.iloc[i, 0]).lower().strip() if pd.notna(df.iloc[i, 0]) else ""
            if any(k.lower() in first_val for k in metadata_keywords):
                rows_to_drop.append(i)
        
        if rows_to_drop:
            df = df.drop(rows_to_drop).reset_index(drop=True)
            logger.info(f"Dropped {len(rows_to_drop)} legacy metadata header rows.")
            
        return df

    def _clean_wide_table_metadata(self, df: pd.DataFrame):
        """
        [Internal] 专门用于处理“宽表”（如中信一级行业指数）的元数据清洗。
        特点：寻找首列为“指标名称”的那一行作为表头，且不修改列名内容。
        """
        if df.empty:
            return df
            
        header_row_idx = None
        # 扫描前 30 行寻找包含“指标名称”的行
        for i in range(min(30, len(df))):
            first_val = str(df.iloc[i, 0]).strip()
            if first_val == '指标名称':
                header_row_idx = i
                logger.info(f"Detected wide table header at row {i} with '指标名称'")
                break
        
        if header_row_idx is not None:
            # 提取数据部分并设置列名（保留原始列名，不做删改）
            new_df = df.iloc[header_row_idx + 1:].copy()
            new_df.columns = [str(c).strip() for c in df.iloc[header_row_idx].values]
            return new_df.reset_index(drop=True)
            
        return df

    def _parse_date_index(self, df: pd.DataFrame):
        """
        [Internal] 自动识别日期列并设为 Index，处理 Excel 数字日期转换。
        """
        if df.empty:
            return df
            
        # 寻找日期列候选者
        date_candidates = ['date', '日期', '指标名称', 'time', '时间', 'trade_date', 'trade_dt', 's_info_date']
        date_col = None
        
        # 统一列名为小写方便匹配
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        for cand in date_candidates:
            if cand in df.columns:
                date_col = cand
                break
        
        if not date_col:
            # 尝试将第一列设为日期
            date_col = df.columns[0]
            
        # 转换日期，过滤掉无效行（处理 Wind 表尾备注的核心逻辑）
        try:
            # 如果是数字类型（Excel 序列号）
            if pd.api.types.is_numeric_dtype(df[date_col]):
                df[date_col] = pd.to_datetime(df[date_col], unit='D', origin='1899-12-30').dt.normalize()
            else:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except:
             df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        df = df.dropna(subset=[date_col])
        df = df.set_index(date_col)
        df.index.name = 'date'
        return df.sort_index()

    def _standardize_ohlc(self, df: pd.DataFrame, asset_name: str):
        """
        [Internal] 强制映射 OHLCV 列名，进行归一化。
        """
        ohlc_map = {
            'open': ['open', '开盘', '开盘价', 's_dq_open', 's_info_open', '开盘价(元)'],
            'high': ['high', '最高', '最高价', 's_dq_high', 's_info_high', '最高价(元)'],
            'low': ['low', '最低', '最低价', 's_dq_low', 's_info_low', '最低价(元)'],
            'close': ['close', '收盘', '收盘价', '最新价', '成交价', 'value', 'price', '收盘价(元)', asset_name.lower()],
            'volume': ['volume', '成交量', 'vol', 'qty', 's_dq_volume', 's_info_vol', '成交量(股)'],
            'amount': ['amount', '成交额', 'amt', 'turnover', 's_dq_amount', 's_info_amt', '成交额(元)']
        }
        
        result_df = pd.DataFrame(index=df.index)
        for standard_name, keywords in ohlc_map.items():
            found_col = None
            for kw in keywords:
                if kw in df.columns:
                    found_col = kw
                    break
            if not found_col:
                # 模糊匹配
                for actual_col in df.columns:
                    if any(kw in actual_col for kw in keywords):
                        found_col = actual_col
                        break
            
            if found_col:
                result_df[standard_name] = pd.to_numeric(df[found_col], errors='coerce')
            else:
                result_df[standard_name] = np.nan
        
        # 兜底：如果 close 为空，尝试取第一列数值列
        if result_df['close'].isna().all():
            for col in df.columns:
                temp = pd.to_numeric(df[col], errors='coerce')
                if not temp.isna().all():
                    result_df['close'] = temp
                    break
                    
        return result_df.ffill()

    def get_ohlc_data(self, filename: str, name: str = "stock"):
        """
        获取标准 OHLC 格式的行情数据 (单标的模式)。
        """
        path = self.base_path / filename
        if not path.exists():
            # 尝试在子目录搜索或处理绝对路径
            if os.path.isabs(filename):
                path = Path(filename)
            else:
                logger.error(f"Data file not found: {path}")
                return None
                
        logger.info(f"Loading OHLC data: {path}")
        
        # 1. 读取原始文件 (含 Excel 自动修复)
        df = self._read_raw_file(path)
        
        # 2. 清洗元数据 (Wind Header/Footer)
        df = self._clean_wind_metadata(df)
        
        # 3. 寻找并解析日期索引
        df = self._parse_date_index(df)
        
        # 4. 映射 OHLC 直到标准输出
        return self._standardize_ohlc(df, name)

    def get_batch_data(self, filenames: list):
        """
        批量加载数据示例
        """
        data_dict = {}
        for f in filenames:
            name = Path(f).stem
            data_dict[name] = self.get_ohlc_data(f, name)
        return data_dict

    def get_wide_table(self, filename: str, index_col: str = "date"):
        """
        [Entry Point] 获取宽表数据。
        专门针对包含 “指标名称” 描述行的宽表进行读取，且不修改列名。
        """
        path = self.base_path / filename
        if not path.exists():
            if os.path.isabs(filename):
                path = Path(filename)
            else:
                logger.error(f"Wide table not found: {path}")
                return None
                
        logger.info(f"Loading wide table (flexible lookup): {path}")
        
        # 1. 读取原始文件
        df = self._read_raw_file(path)
        
        # 2. 调用专门的宽表清洗逻辑
        df = self._clean_wide_table_metadata(df)
        
        # 3. 解析日期并设为 Index
        df = self._parse_date_index(df)
            
        # 4. 确保数据部分全为数值（处理逗号并强制转换，跳过非空行）
        df = df.replace({',': ''}, regex=True).apply(pd.to_numeric, errors='coerce')
        
        return df

    def get_fundamental_data(self, filename: str = "FUNDAMENTAL/ROE.csv", value_col: str = "ROE"):
        """
        获取基本面数据（标准化模式：code, date, value）
        """
        path = self.base_path / filename
        if not path.exists():
            logger.error(f"Fundamental data not found: {path}")
            return None
            
        logger.info(f"Loading fundamental data: {path}")
        
        if path.suffix == '.csv':
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
            
        # 标准化列名映射
        col_map = {
            'secucode': 'code',
            '证券代码': 'code',
            '代码': 'code',
            'enddate': 'date',
            '截止日期': 'date',
            '报告期': 'date',
            value_col.lower(): 'value'
        }
        
        # 统一列名为小写进行匹配
        df.columns = [str(c).lower().strip() for c in df.columns]
        df.rename(columns=col_map, inplace=True)
        
        # 提取关键列
        if 'code' not in df.columns or 'date' not in df.columns:
            # 尝试回退逻辑：如果列名不匹配，按位置取 (假设 2, 3, 4 列分别是 code, date, value)
            # 或者寻找包含这些关键词的原始列
            found_cols = {}
            for target in ['code', 'date', 'value']:
                for c in df.columns:
                    if target in c or any(kw in c for kw in col_map.keys() if col_map[kw] == target):
                        found_cols[target] = c
                        break
            
            if len(found_cols) >= 2:
                df.rename(columns=found_cols, inplace=True)
                
        # 最终筛选有效列
        required = ['code', 'date']
        if 'value' not in df.columns:
            # 如果没有找到明确的 value 列，尝试将除 code/date 外的第一列数值列作为 value
            for col in df.columns:
                if col not in required:
                    temp = pd.to_numeric(df[col], errors='coerce')
                    if not temp.isna().all():
                        df['value'] = temp
                        break
        
        df = df.dropna(subset=['code', 'date'])
        
        # 格式化日期和代码
        df['date'] = pd.to_datetime(df['date'])
        df['code'] = df['code'].astype(str).str.split('.').str[0].str.zfill(6)
        
        # 过滤掉非数值 value
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df[value_col.lower()] if value_col.lower() in df.columns else df['value'], errors='coerce')
            
        return df[['code', 'date', 'value']].sort_values(['code', 'date'])

    def get_trading_calendar(self, start_date: str = None, end_date: str = None):
        """
        获取 A 股交易日历信息（基于上证指数 000001.SH）。
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            dict: {
                'total_days': int,
                'trade_days': List[pd.Timestamp]
            }
        """
        # 使用上证指数作为交易日历基准
        index_file = "INDEX/STOCK/000001.SH.xlsx"
        
        # 利用已有的 get_wide_table，它会自动处理日期解析、Wind元数据清洗和排序
        # 注意：这里不使用 get_ohlc_data 是为了保持轻量，只取日期索引即可
        df = self.get_wide_table(index_file)
        
        if df is None or df.empty:
            logger.error(f"无法从 {index_file} 获取交易日历")
            return {'total_days': 0, 'trade_days': []}
            
        all_days = df.index
        
        # 转换输入日期为 pd.Timestamp 方便比较
        if start_date:
            all_days = all_days[all_days >= pd.to_datetime(start_date)]
        if end_date:
            all_days = all_days[all_days <= pd.to_datetime(end_date)]
            
        trade_days_list = all_days.tolist()
        
        return {
            'total_days': len(trade_days_list),
            'trade_days': trade_days_list
        }

    def get_universe_data(self, filename: str, universe: str = None, start_date: str = None, end_date: str = None):
        """
        [Entry Point] 强化版数据加载，支持 Universe 过滤和时间范围过滤。
        """
        # 1. 加载全量数据
        path = self.base_path / filename
        if not path.exists():
            if os.path.isabs(filename):
                path = Path(filename)
            else:
                logger.error(f"Data file not found: {path}")
                return None

        logger.info(f"Loading full data from {path} for universe filtering...")
        
        # 使用 standard reading logic
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        df['code'] = df['code'].astype(str).str.zfill(6)
        
        # 2. 时间过滤
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]
            
        # 3. 股票池过滤
        if universe and universe != 'ALL':
            logger.info(f"Applying universe filter: {universe}")
            u_df = self.universe_mgr.get_constituents(universe)
            
            if u_df.empty:
                logger.warning(f"Universe {universe} data is empty, returning empty result.")
                return pd.DataFrame()
                
            # 执行矢量化拼接过滤
            # 我们将 df 与 u_df 进行 inner join，连接键包含 code，且 date 在 [indate, outdate) 之间
            # 为了更高效，我们先合并基本信息，再通过列逻辑过滤
            merged = df.merge(u_df[['code', 'indate', 'outdate']], on='code', how='inner')
            # 过滤符合日期范围的行
            mask = (merged['date'] >= merged['indate']) & ((merged['date'] < merged['outdate']) | (merged['outdate'].isna()))
            df = merged.loc[mask, df.columns].copy()
            
        return df.set_index(['date', 'code']).sort_index()

    def load_file_data(self, file_path: str):
        """
        通用的文件读取函数：读取指定路径的文件并返回 DataFrame。
        不强制索引名，仅做基础的日期解析和读取。
        返回: (dataframe, flag)
        - flag = -1: 成功读取数据
        - flag = 0: 文件不存在或读取为空
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return pd.DataFrame(), 0
        
        try:
            # 自动识别格式并读取 (优先处理 CSV，如果有 MultiIndex 会自动识别)
            if path.suffix.lower() == '.csv':
                # 尝试读取，不预设 index_col，由调用方处理或保持原始状态
                df = pd.read_csv(path)
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(path)
            else:
                df = pd.DataFrame()

            if df.empty:
                return pd.DataFrame(), 0
            
            return df, -1
        except Exception as e:
            logger.error(f"Error loading file {path}: {e}")
            return pd.DataFrame(), 0

def load_and_preprocess(path, asset_name):
    """
    加载并预处理数据
    统一日期格式，处理缺失值，输出规范化的 OHLC 结果
    适配不同数据源的格式差异，加入Excel内容识别与清洗功能
    """
    warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
    
    if path.endswith('.csv'):
        df = pd.read_csv(path, encoding='gbk')
    elif path.endswith('.xlsx') or path.endswith('.xls'):
        # 尝试使用 openpyxl 或 xlrd
        try:
            df = pd.read_excel(path)
        except Exception as e:
            if "NamedCellStyle" in str(e) or "NoneType" in str(e):
                try:
                    import zipfile
                    import io
                    # 修复损坏的 Excel 样式：移除 xl/styles.xml
                    with zipfile.ZipFile(path, 'r') as zin:
                        buffer = io.BytesIO()
                        with zipfile.ZipFile(buffer, 'w') as zout:
                            for item in zin.infolist():
                                if item.filename != 'xl/styles.xml':
                                    zout.writestr(item, zin.read(item.filename))
                                else:
                                    zout.writestr(item, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"></styleSheet>')
                        buffer.seek(0)
                        df = pd.read_excel(buffer, engine='openpyxl')
                except Exception as e2:
                    logger.error(f"修复Excel并读取失败 {path}: {e2}")
                    return pd.DataFrame()
            else:
                logger.error(f"读取Excel出错 {path}: {e}")
                return pd.DataFrame()
    else:
        logger.error(f"不支持的文件格式: {path}")
        return pd.DataFrame()

    # --- Excel 内容识别与清洗 ---
    
    # 1. 如果第一行或多行为空/无效，尝试寻找包含关键词的行作为表头
    # 常见于 Wind/Ifind 导出会有几行标题
    if df.shape[0] > 0:
        # 搜索包含 '日期', 'date', 'Date', '指标名称' 的行
        potential_header_keywords = ['日期', 'date', '指标名称', '时间', 'time']
        header_row_idx = -1
        
        # 检查前 5 行，应对更复杂的表头
        for i in range(min(5, len(df))):
            row_values = [str(val).strip() for val in df.iloc[i].values]
            if any(any(kw in val for kw in potential_header_keywords) for val in row_values):
                header_row_idx = i
                break
        
        if header_row_idx != -1:
            # 重新设表头
            new_columns = df.iloc[header_row_idx].values
            # 处理可能的 NaN 列名或数值列名
            new_columns = [str(c).strip() if pd.notna(c) else f"unnamed_{i}" for i, c in enumerate(new_columns)]
            df = df.iloc[header_row_idx+1:].copy()
            df.columns = new_columns

    # 统一列名清洗
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    # 2. 日期列识别
    date_col = None
    date_candidates = ['date', '日期', '指标名称', 'time', '时间', 'trade_date']
    for cand in date_candidates:
        if cand in df.columns:
            date_col = cand
            break
    
    if date_col:
        df.rename(columns={date_col: 'date'}, inplace=True)
        # 如果是数字类型（可能是 Excel 序列号），尝试转换
        if pd.api.types.is_numeric_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], unit='D', origin='1899-12-30').dt.normalize()
        else:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        # 如果没找到显式的日期列，尝试将第一列作为日期
        df.rename(columns={df.columns[0]: 'date'}, inplace=True)
        if pd.api.types.is_numeric_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'], unit='D', origin='1899-12-30').dt.normalize()
        else:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # 处理缺失日期行
    df = df.dropna(subset=['date'])
    df = df.sort_values('date').set_index('date')
    
    # 3. 规范化输出结果
    ohlc_map = {
        'open': ['open', '开盘', '开盘价', 's_dq_open', 's_info_open'],
        'high': ['high', '最高', '最高价', 's_dq_high', 's_info_high'],
        'low': ['low', '最低', '最低价', 's_dq_low', 's_info_low'],
        'close': ['close', '收盘', '收盘价', '最新价', '成交价', 'value', 'price', 's_dq_close', 's_info_close', asset_name.lower()],
        'volume': ['volume', '成交量', 'vol', 'qty', 's_dq_volume', 's_info_vol'],
        'amount': ['amount', '成交额', 'amt', 'turnover', 's_dq_amount', 's_info_amt']
    }
    
    # 增加 Wind 特殊列映射 (日期、代码)
    wind_date_candidates = ['trade_dt', 's_info_date', 's_info_tradedate']
    for cand in wind_date_candidates:
        if cand in df.columns and 'date' not in df.columns:
            df.rename(columns={cand: 'date'}, inplace=True)
            break
            
    result_df = pd.DataFrame(index=df.index)
    
    for standard_name, keywords in ohlc_map.items():
        found_col = None
        # 优先精确匹配
        for kw in keywords:
            if kw in df.columns:
                found_col = kw
                break
        # 模糊匹配
        if not found_col:
            for actual_col in df.columns:
                if any(kw in actual_col for kw in keywords):
                    found_col = actual_col
                    break
        
        if found_col:
            result_df[standard_name] = pd.to_numeric(df[found_col], errors='coerce')
        else:
            result_df[standard_name] = np.nan

    # 如果 close 还是空的，尝试取第一列数值列
    if result_df['close'].isna().all():
        for col in df.columns:
            temp = pd.to_numeric(df[col], errors='coerce')
            if not temp.isna().all():
                result_df['close'] = temp
                break

    # 去重并确定 datetime 索引
    result_df = result_df[~result_df.index.duplicated(keep='first')]
    result_df.index = pd.to_datetime(result_df.index, errors='coerce')
    result_df = result_df.sort_index()

    # 前向填充缺失价格，但不dropna（ohlc中允许部分nan）
    result_df = result_df.ffill()
     
    return result_df


def normalize_series(df_or_ser):
    """
    将时间序列（价格或净值）归一化，起始值设为 1
    支持 pd.Series 和 pd.DataFrame
    """
    if isinstance(df_or_ser, pd.Series):
        valid_data = df_or_ser.dropna()
        if valid_data.empty or valid_data.iloc[0] == 0:
            return df_or_ser
        return df_or_ser / valid_data.iloc[0]
    
    elif isinstance(df_or_ser, pd.DataFrame):
        norm_df = df_or_ser.copy()
        for col in norm_df.columns:
            valid_data = norm_df[col].dropna()
            if not valid_data.empty and valid_data.iloc[0] != 0:
                norm_df[col] = norm_df[col] / valid_data.iloc[0]
            else:
                norm_df[col] = np.nan
        return norm_df
    return df_or_ser
