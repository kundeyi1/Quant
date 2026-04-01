## 1. Setup and Infrastructure

- [x] 1.1 Create `UniverseManager` class in `core/DataManager.py` to handle loading and indexing of `000905_comp.csv` and `000852_comp.csv`.
- [x] 1.2 Implement dynamic filtering logic for member inclusion/exclusion by date (`indate`, `outdate`).

## 2. Core Implementation

- [x] 2.1 Add `get_universe_data` method to `DataProvider` in `core/DataManager.py`.
- [x] 2.2 Incorporate full-market data loading with the new `UniverseManager` to allow filtering of long-term time series by universe.
- [x] 2.3 Add support for date range filtering (`start_date`, `end_date`) into the loading stream.

## 3. Integration

- [x] 3.1 Refactor `run_gx_hotspot_standard_test.py` to use `DataProvider.get_universe_data()`.
- [x] 3.2 Add parameterization to the main script to allow easy switching between `None` (full market), `000905` (CSI 500), and `000852` (CSI 1000).

## 4. Validation

- [x] 4.1 Verify stock count matches expected values when filtering CSI 500 for a sample date.
- [x] 4.2 Ensure no duplicate records remain after joining the universe and price data.
- [x] 4.3 Run `run_gx_hotspot_standard_test.py` with CSI 1000 to confirm full-pipeline execution.
