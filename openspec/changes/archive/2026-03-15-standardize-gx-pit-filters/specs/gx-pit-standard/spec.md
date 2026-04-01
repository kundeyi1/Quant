## ADDED Requirements

### Requirement: Standardized Data Input Adapter
All `calculate_gx_pit_*` filters SHALL use a standardized internal mechanism to handle both OHLC DataFrames and single-column price wide tables. If a wide table is provided, it SHALL be treated as the 'close' price, with 'high' and 'low' defaulted to 'close' if missing.

#### Scenario: OHLC DataFrame Input
- **WHEN** a DataFrame with 'high', 'low', 'close' columns is passed to a filter
- **THEN** the filter accurately extracts these columns for calculation

#### Scenario: Wide Table (Price Series) Input
- **WHEN** a single-column Series or a wide table (symbols as columns) is passed
- **THEN** the filter treats the input as 'close' and derives 'high'/'low' from it for compatibility

### Requirement: Unified ATR Dynamic Scaling
All GX PIT filters implementing ATR-based threshold adjustment SHALL use the following scale formula consistently:
- Scale = 1.0 (if 1% <= ATR <= 2%)
- Scale = sqrt(ATR / 1%) (if ATR < 1%)
- Scale = sqrt(ATR / 2%) (if ATR > 2%)
The ATR MUST be calculated using `RiskFactors.calculate_gx_atr_factor` with `n=60`.

#### Scenario: Low Volatility Scaling
- **WHEN** ATR 60 is 0.5% (below 1%)
- **THEN** the effective thresholds (u, d) are multiplied by sqrt(0.005 / 0.01) ≈ 0.707

#### Scenario: High Volatility Scaling
- **WHEN** ATR 60 is 4% (above 2%)
- **THEN** the effective thresholds (u, d) are multiplied by sqrt(0.04 / 0.02) ≈ 1.414

### Requirement: Deprecation of Standalone ATR Filter
The `atr_volatility_filter` SHALL NOT exist as a standalone public static method in `SignalFilters`. Its functionality SHALL be moved to an internal private method or integrated directly into relevant filters to reduce API clutter.

#### Scenario: Refactored signal_filters.py
- **WHEN** developers inspect the `SignalFilters` class
- **THEN** `atr_volatility_filter` is either removed or prefixed with an underscore to indicate internal use
