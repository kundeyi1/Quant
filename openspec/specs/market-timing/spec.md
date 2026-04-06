# Market Timing

## Purpose
The Market Timing capability provides a unified framework for tactical asset allocation and risk management signals. It integrates diverse timing methodologies, including Huatai's Resistance Support Relative Strength (RSRS) and trend/volume regimes, as well as GX-PIT technical breakout and rebound filters.

## Requirements

### Requirement: Huatai RSRS Normalization Timing
The system SHALL provide a method `ht_rsrs_norm` to calculate the Resistance Support Relative Strength (RSRS) normalized score (Z-Score) based on the Huatai methodology.

#### Scenario: RSRS continuous score output
- **WHEN** the 18-day rolling regression slope of High on Low prices (default params) is calculated
- **AND** normalized by its 600-day rolling mean and std
- **THEN** the system SHALL output the continuous Z-Score series.

### Requirement: Huatai Trend Regime Scoring
The system SHALL provide a method `ht_trend_regime` to calculate market trend strength based on the Huatai dual-MA crossover methodology (default 5/60 window).

#### Scenario: Huatai Trend Score calculation
- **WHEN** the short-term and long-term SMAs are calculated using default parameters
- **THEN** the system SHALL output a score representing the trend strength.

### Requirement: Huatai Volume Regime Scoring
The system SHALL provide a method `ht_volume_regime` to calculate volume-price scores as defined in the Huatai timing system.

#### Scenario: Huatai Volume score output
- **WHEN** current volume is compared to its historical moving average using relative expansion logic
- **THEN** the system SHALL output a relative volume score.

### Requirement: Hybrid Timing Output Format
系统 MUST 支持将 Huatai 风格的连续 Z-Score 信号转换为离散的择时打分信号（例如 0/1），以支持离散信号回测框架。

#### Scenario: HT series discrete output
- **WHEN** an HT-indexed function (e.g., `ht_rsrs_norm`) is used for signal generation
- **THEN** it SHOULD support returning a `0/1` discrete signal series (e.g., via thresholding) to represent clear entry/exit triggers.

#### Scenario: HT series continuous output
- **WHEN** an HT-indexed function (e.g., `ht_rsrs_norm`) is called for detailed analysis
- **THEN** it SHOULD return the raw indicator value or composite score as a `pd.Series` to preserve information.

#### Scenario: GX-PIT series discrete output
- **WHEN** a GX-PIT-indexed function (e.g., `gx_pit_breakout`) is called
- **THEN** it MUST return a `0/1` discrete signal as it represents a pattern recognition trigger.

#### Scenario: Flat Function Structure
- **WHEN** a user imports a timing method from `timing.market_timing`
- **THEN** it MUST be accessible as a top-level function without requiring class instantiation.

### Requirement: Timing Signal Integration
The system SHALL support the aggregation of multiple technical timing triggers into a unified entry matrix.

#### Scenario: Physical Trigger Execution
- **WHEN** the `market_timing` module is called with specific physical thresholds
- **THEN** it MUST correctly apply filters like `f_vola < 0.75` or `f_dist_high > -0.005` to generate the 0/1 binary series

### Requirement: Idempotent signal calculation
在开始任何耗时的计算前，系统必须（SHALL）检查目标存储路径。若已存在完全匹配的信号文件，则应当跳过（SHALL skip）计算。

#### Scenario: Skip existing rebound signal
- **WHEN** 调用计算 `gx_pit_rebound` 且对应文件已存在于 `D:\DATA\TIMING`
- **THEN** 系统直接加载该文件并返回，不重新执行计算逻辑

### Requirement: Index Physical Factor Calculation
The system MUST provide objective, absolute metrics based on raw data to describe index states across multiple dimensions (Price, Volume, Trend).

#### Scenario: Price Distance Calculation
- **WHEN** the `PriceFactors.price_dist_high` logic is invoked
- **THEN** it SHALL return raw percentage distance `(Price / HHV - 1)` instead of quantile rank

#### Scenario: Volume Dryness Calculation
- **WHEN** the `VolumeFactors.volume_abs_dryness` logic is invoked
- **THEN** it SHALL return a value representing `Volume / MA(Volume)` to detect absolute liquidity exhaustion

### Requirement: Two-Stage Momentum Filter
The system SHALL implement a multi-step logic where a technical setup is only activated if it is followed by a confirmed price momentum on the same day.

#### Scenario: Positive Confirmation
- **WHEN** a technical signal (e.g., volume_dry < 0.7) is triggered AND the index daily return is >= 3%
- **THEN** the composite signal SHALL be marked as 1; otherwise, it SHALL be 0
