# Proposal: Refactor DataManager for Atomization

## Goal
The current `DataManager.py` (specifically `DataProvider` and `load_and_preprocess`) contains monolithic logic for data loading, Excel repair, and Wind/iFind-specific header/footer cleaning. This leads to code duplication and fragility when handling different data sources.

The goal of this refactor is to **atomize** these processes by extracting internal utilities for file reading, metadata cleaning, and date parsing. This will improve robustness and maintainability while streamlining the high-level API.

## Scope
- **Atomization**: Extract logical units into internal private functions.
- **Robustness**: Better handle corrupted Excel files and metadata (headers/trailers).
- **Standardization**: Enforce two entry points: `get_ohlc_data` and `get_wide_table`.
- **API Clean-up**: Update calling sites to reflect the new standardized methods.
- **NO Caching**: Explicitly remove or avoid adding caching logic to keep it simple and deterministic.

## Reasoning
1. **Maintenance**: Private utilities like `_clean_wind_metadata` can be tested and updated independently of the main data loading flow.
2. **Consistency**: Using standardized entry points ensures that all scripts consume data in the same format (OHLC vs. Wide Table).
3. **Robustness**: Centralizing `_fix_broken_excel` avoids repeating repair logic in multiple places.
