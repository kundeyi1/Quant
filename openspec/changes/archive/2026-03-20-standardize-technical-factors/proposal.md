## Why

The current `factors/technical_factors.py` file has grown organically, leading to inconsistent classification, redundant methods (e.g., multiple `calculate_ma_arrangement`), and a lack of clear logical boundaries. This makes it difficult to maintain the codebase and for researchers to locate specific indicators. Standardizing the factor organization into six defined categories (Price, Volume, Trend, Volatility, Crowding, Alpha101) will improve discoverability and scalability.

## What Changes

- **Restructure Classes**: Rename and regroup existing factor classes into the following:
    - `PriceFactors`: Indicators based on price position, relative levels, and specific price patterns.
    - `VolumeFactors`: Indicators focused on turnover, volume spikes, and volume-price relationships.
    - `TrendFactors`: Directional and persistence indicators, including moving averages and regression slopes.
    - `VolatilityFactors`: Measures of dispersion and range.
    - `CrowdingFactors`: Sentiment and positioning risk metrics.
    - `Alpha101Factors`: Implementation of the WorldQuant 101 framework.
- **Factor Function Renaming**: Rename all factor calculation methods to remove the `calculate_` prefix (e.g., `calculate_ma_arrangement` -> `ma_arrangement`). This provides a more concise API within the classes. **BREAKING**.
- **Move Factors**:
    - Move `symmetry`, `ma_compression`, `yellow_line`, `white_line`, and all MA variants (`sma`, `ema`, `wma`) into `TrendFactors`.
    - Move `overhead_supply` into `PriceFactors`.
    - Regroup other indicators according to the refined logic (e.g., `adx` and `rsrs_norm` to `TrendFactors`).
- **Cleanup**: Remove duplicate methods (redundant `ma_arrangement`) and ensure consistent docstring formatting.

## Capabilities

### New Capabilities
- `technical-factor-catalog`: Definition of the standardized classification system for all technical indicators in the system.

### Modified Capabilities
- `technical-factors`: Update the requirements for how technical factors are organized and stored in the library.

## Impact

- `factors/technical_factors.py`: Primary file being refactored.
- `FactorTester.py` & `FactorVisualizer.py`: Any direct references to old category classes will need reconciliation.
- Strategy files: Any code importing factors from `technical_factors.py` by class name.
