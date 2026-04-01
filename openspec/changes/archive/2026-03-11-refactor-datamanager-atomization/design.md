# Design: Refactored DataManager Structure

The target architecture for `DataManager.py` centers around a clean split between high-level handlers (Entry Points) and internal utilities (Private Methods).

## ASCII Structure

```text
DataManager.py
├── DataProvider (Class)
│   ├── Internal Private Methods
│   │   ├── _read_raw_file(path) -> df
│   │   │   # Try different encodings for CSV, handle Excel formats
│   │   ├── _fix_broken_excel(path) -> df/buffer
│   │   │   # Repair corrupted xlsx by removing xl/styles.xml
│   │   ├── _clean_wind_metadata(df) -> df
│   │   │   # Drop first N rows with "Unit", "Title", etc.
│   │   │   # Clean footers like "Data Source: Wind"
│   │   ├── _parse_date_index(df, col_name_search) -> df
│   │   │   # Handle various date formats (Excel serials, ISO, etc.)
│   │   │   # Set 'date' as the index
│   │   └── _standardize_ohlc(df, asset_name) -> df
│   │       # Map columns (OHLCV + Amount) using ohlc_map
│   │
│   └── High-Level Entry Points
│       ├── get_ohlc_data(filename, name) -> df
│       │   # Returns standardized OHLCV Dataframe for a single asset
│       │   # (Replaces get_stock_data)
│       └── get_wide_table(filename, index_col='date') -> df
│           # Returns cross-sectional data with date index
│           # Cleaned and numeric-only
```

## Internal Workflow

1.  **Read**: `_read_raw_file` attempts to load file, calling `_fix_broken_excel` if it fails with specific "NoneType" or "NamedCellStyle" errors.
2.  **Clean**: `_clean_wind_metadata` searches the top rows for metadata keywords (Indicator Name, Unit, etc.) and footers (Data Source).
3.  **Parse**: `_parse_date_index` identifies the date column, converts formats, and sets the index.
4.  **Map**: Depending on the entry point, `_standardize_ohlc` maps columns to standard names.
