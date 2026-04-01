# Tasks: Refactor DataManager for Atomization

## Preparation
- [x] Backup current `core/DataManager.py`.
- [x] Identify all calling sites for `get_stock_data` and `get_wide_table`.

## Implementation (Core/DataManager.py)
- [x] Create internal utility `_fix_broken_excel(path)` to isolate Excel repair logic.
- [x] Create internal utility `_read_raw_file(path)` to handle both CSV (GBK/UTF-8) and Excel files.
- [x] Create internal utility `_clean_wind_metadata(df)` based on spec.
- [x] Create internal utility `_parse_date_index(df)` to centralize date logic and Excel serial handling.
- [x] Create internal utility `_standardize_ohlc(df, asset_name)` using the mapping dict.
- [x] Implement `get_ohlc_data(filename, name)`:
    - [x] Call `_read_raw_file`.
    - [x] Call `_clean_wind_metadata`.
    - [x] Call `_parse_date_index`.
    - [x] Call `_standardize_ohlc`.
- [x] Refactor `get_wide_table(filename, index_col)`:
    - [x] Use `_read_raw_file`.
    - [x] Use `_clean_wind_metadata`.
    - [x] Use `_parse_date_index`.
- [x] Update `get_stock_data` to call `get_ohlc_data` (deprecated alias for backward compatibility during transition).
- [x] Remove `load_and_preprocess` (it's monolithic and will be replaced by the atomized internal methods).

## Refactoring Calls (Updating Scripts)
- [x] Update `run_sparse_momentum_test.py`: Replace `dp.get_stock_data` with `dp.get_ohlc_data`.
- [x] Update `run_sparse_momentum_test_old.py`: Replace `dm.get_stock_data` with `dm.get_ohlc_data`.
- [x] Update `core/TSCompare.py`: Replace `dp.get_stock_data` with `dp.get_ohlc_data`.
- [x] Update `core/DataManager.py`: Ensure internal batch calls use new entries.

## Verification
- [x] Verify `get_ohlc_data` returns identical results to the old `get_stock_data`.
- [x] Verify `get_wide_table` returns identical results to the old version.
- [x] Confirm Wind header/footer rows are correctly dropped.
