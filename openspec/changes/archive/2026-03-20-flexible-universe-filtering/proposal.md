## Why

<!-- Explain the motivation for this change. What problem does this solve? Why now? -->
Currently, the factor testing scripts (like `run_gx_hotspot_standard_test.py`) use hardcoded full-market data loading and manual date filtering. There is no flexible way to restrict analysis to specific stock universes (e.g., CSI 500, CSI 1000) that change over time (dynamic constituents). This change centralizes universe management and data filtering within `DataManager` to enable flexible, multi-universe backtesting.

## What Changes

<!-- Describe what will change. Be specific about new capabilities, modifications, or removals. -->
- **Enhance `DataProvider` in `core/DataManager.py`**: Add a dedicated `UniverseManager` class (or extend `DataProvider` with universe methods) to handle dynamic constituent loading and filtering.
- **Dynamic Constituent Loading**: Implement logic to read `000905_comp.csv` (CSI 500) and `000852_comp.csv` (CSI 1000) using `indate` and `outdate` logic.
- **Integrated Filtering**: Add a `get_universe_filtered_data` method to `DataProvider` that combines full-market data loading with universe and date range filtering.
- **Standardized API**: Update the research workflow to call these new methods instead of manual `pd.read_csv` and manual filtering.

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->
- `dynamic-universe-management`: Ability to define and load time-varying stock universes from constituent files.
- `integrated-data-filtering`: Unified entry point for loading price/factor data with built-in temporal and universe constraints.

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `data-pipeline`: Update the data loading requirements to support universe-based scoping.

## Impact

<!-- Affected code, APIs, dependencies, systems -->
- `core/DataManager.py`: Significant modification/addition of logic.
- `run_gx_hotspot_standard_test.py` (and similar scripts): Refactoring to use the new `DataManager` API.
- Data directory structure: Relies on `D:\DATA\INDEX_COMP\` for constituent files.
