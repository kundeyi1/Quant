## Context

Currently, the data pipeline in `run_gx_hotspot_standard_test.py` manually filters CSV data. This project aims to integrate "Universe Filtering" directly into `DataManager.py`. Two major indices, CSI 500 (`000905_comp.csv`) and CSI 1000 (`000852_comp.csv`), are the initial targets. These constituent files follow an `indate`/`outdate` format to track dynamic memberships.

## Goals / Non-Goals

**Goals:**
- Implement a `UniverseManager` component within `core/DataManager.py`.
- Support CSI 500 and CSI 1000 constituent files in `D:\DATA\INDEX_COMP\`.
- Provide a unified filtering method: `get_filtered_data(..., universe='000905')`.
- Ensure date filtering (start/end) is managed within `DataManager`.

**Non-Goals:**
- Changing the underlying CSV file structure.
- Migrating to a SQL database for this specific task.
- Implementing complex sector/industry rotations (out of scope for this universe filter).

## Decisions

### 1. Integration into `DataManager.py`
We will add a `UniverseManager` class inside `core/DataManager.py`. This avoids file bloat while keeping the logic encapsulated. `DataProvider` (the existing class) will hold an instance or methods to call this manager.

### 2. Temporal Filtering Logic
For a given `target_date`, a stock is in the universe if:
`indate <= target_date` AND (`outdate > target_date` OR `outdate` is null/empty).
Instead of per-day loops, we will use vectorized pandas operations for better performance when filtering long time series.

### 3. Unified Data Loading API
The new recommended way to load research data will be:
```python
loader = DataProvider()
df = loader.get_universe_data(
    filename="all_stock_data.csv",
    universe="000905",
    start_date="2020-01-01",
    end_date="2025-12-31"
)
```

## Risks / Trade-offs

- **[Risk] Data Format Mismatch** → **Mitigation**: Use `_read_raw_file` and `_clean_wind_metadata` from the existing `DataProvider` to ensure constituent files are parsed correctly.
- **[Performance] Large Join/Filter** → **Mitigation**: Perform universe filtering *immediately* after loading the main price data to minimize memory footprint.
- **[Empty Universe]** → **Mitigation**: If no stocks are found for a specific date in a specific universe, raise a clear warning in the logger.
