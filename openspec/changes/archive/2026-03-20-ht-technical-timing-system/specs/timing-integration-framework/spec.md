## ADDED Requirements

### Requirement: Hybrid Timing Output Format
The system SHALL establish a convention where timing functions support both discrete (0/1) and continuous outputs, depending on their original methodology (HT vs GX-PIT).

#### Scenario: HT series continuous output
- **WHEN** an HT-indexed function (e.g., `ht_rsrs_norm`) is called
- **THEN** it SHOULD return the raw indicator value or composite score as a `pd.Series` to preserve information.

#### Scenario: GX-PIT series discrete output
- **WHEN** a GX-PIT-indexed function (e.g., `gx_pit_breakout`) is called
- **THEN** it MUST return a `0/1` discrete signal as it represents a pattern recognition trigger.

#### Scenario: Flat Function Structure
- **WHEN** a user imports a timing method from `timing.market_timing`
- **THEN** it MUST be accessible as a top-level function without requiring class instantiation.
