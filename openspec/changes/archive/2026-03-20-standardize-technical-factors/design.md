## Context

The current `factors/technical_factors.py` contains multiple classes with some overlapping logic and inconsistent method naming (some use `calculate_`, some are missing it, or have redundant implementations). The system needs a strictly categorized, clean API where each factor is a static method without the `calculate_` prefix, returning a `pd.DataFrame` or `pd.Series` with the same index as the input.

## Goals / Non-Goals

**Goals:**
- **Standardized Naming**: Remove `calculate_` prefix from all factor methods.
- **Logical Grouping**: Reorganize all methods into 6 classes: `PriceFactors`, `VolumeFactors`, `TrendFactors`, `VolatilityFactors`, `CrowdingFactors`, and `Alpha101Factors`.
- **Deduplication**: Identify and remove identical implementations (e.g., duplicated `ma_arrangement`).
- **Consistent Interface**: All factors should accept a `data` DataFrame (with OHLCV) and return a time-series result.

**Non-Goals:**
- Changing the mathematical logic of the factors (unless fixing a bug).
- Optimizing performance beyond simple vectorization improvements.
- Adding entirely new factors not discussed in the proposal.

## Decisions

- **Decision 1: Static Method Access**: Continue using `@staticmethod` for all factors. This allows calling `TrendFactors.ma_arrangement(data)` without instantiation, maintaining a functional programming style while providing namespace organization.
- **Decision 2: Return Types**: Methods will return `pd.Series` when it's a single scalar indicator and `pd.DataFrame` when multi-column (like MACD or Bollinger Bands). This matches the current usage pattern in the `FactorTester`.
- **Decision 3: Namespace Separation**: Avoid top-level functions in `technical_factors.py`. Every indicator must belong to one of the 6 classes.

## Risks / Trade-offs

- **[Risk] Breaking Changes**: Removing `calculate_` and moving methods will break existing imports in `FactorTestAPI_new.py` or strategy files.
    - **Mitigation**: Perform a global search and replace for common usages during the implementation phase.
- **[Risk] Name Collisions**: Removing `calculate_` might lead to name collisions with local variables (e.g., `sma` function vs `sma` variable).
    - **Mitigation**: Use descriptive variable names like `sma_series` or `sma_val` inside functions.
- **[Risk] Circular Imports**: Moving factors might introduce circular dependencies if categories are too granular.
    - **Mitigation**: Keep all 6 classes in the single `factors/technical_factors.py` file for now to avoid cross-file import issues.

## Migration Plan

1. **Phase 1: Structure**: Define the 6 empty classes in `technical_factors.py`.
2. **Phase 2: Migration**: Move existing methods into the new classes, stripping the `calculate_` prefix and updating `talib` calls.
3. **Phase 3: Cleanup**: Remove the old class definitions and leftover code.
4. **Phase 4: Update Callers**: Update `timing/market_timing.py` and other entry points to use the new naming convention.
