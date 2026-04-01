## ADDED Requirements

### Requirement: Standardized Factor Classification
All technical indicators in the system SHALL be categorized into six distinct classes: `PriceFactors`, `VolumeFactors`, `TrendFactors`, `VolatilityFactors`, `CrowdingFactors`, and `Alpha101Factors`.

#### Scenario: Correct class separation
- **WHEN** user wants to calculate a trend-following factor
- **THEN** it MUST be located in the `TrendFactors` class
- **WHEN** user wants to calculate a volume-based factor
- **THEN** it MUST be located in the `VolumeFactors` class

### Requirement: Renamed Factor Methods
Factor methods within the standardized classes SHALL NOT include the `calculate_` prefix.

#### Scenario: Direct method naming
- **WHEN** user wants to call the MA arrangement factor
- **THEN** they MUST call `TrendFactors.ma_arrangement(data)` instead of `calculate_ma_arrangement`

### Requirement: Factor Categorization Logic
The system SHALL regroup specific indicators according to the refined logic:
1. `PriceFactors`: Includes `overhead_supply`, `price_percentile`, `price_bias`.
2. `VolumeFactors`: Includes `obv`, `volume_bias`, `volume_volatility`, `volume_breakout`, `intraday_strength`.
3. `TrendFactors`: Includes `symmetry`, `ma_compression`, `yellow_line`, `white_line`, `sma`, `ema`, `wma`, `ma_arrangement`, `macd`, `sar`, `adx`, `rsrs_norm`.
4. `VolatilityFactors`: Includes `bollinger_bands`, `bollinger_breakout`, `gx_atr_factor`.
5. `CrowdingFactors`: Includes `high_pos_vol_risk`, `gx_hotspot`.
6. `Alpha101Factors`: Includes `alpha3` through `alpha55` sub-set.

#### Scenario: Specific relocation
- **WHEN** `overhead_supply` is requested
- **THEN** it MUST be located in `PriceFactors`
- **WHEN** `symmetry` (Symmetry Factor) is requested
- **THEN** it MUST be in `TrendFactors`
