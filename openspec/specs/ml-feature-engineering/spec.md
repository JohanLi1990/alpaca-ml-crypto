## ADDED Requirements

### Requirement: Compute realized volatility percentile via regime module
When `compute_features` is called with `extended=True` alongside the regime feature pipeline, the system SHALL support an optional `regime=True` parameter that calls `compute_regime_features` to append `vol_percentile`, `trend_slope`, and `atr_normalized_return` to the output DataFrame.

#### Scenario: Regime features appended when regime=True
- **WHEN** `compute_features(df, extended=True, regime=True)` is called
- **THEN** the returned DataFrame contains all 9 Phase 2 feature columns plus `vol_percentile`, `trend_slope`, and `atr_normalized_return`

#### Scenario: Existing Phase 2 features unchanged
- **WHEN** `compute_features(df, extended=True, regime=False)` is called (default)
- **THEN** the returned DataFrame contains exactly the same 9 columns as Phase 2, with no change in behavior

### Requirement: No NaN values in any feature column after warm-up drop
After computing all features (base + extended + regime), all rows where any selected feature column is NaN SHALL be dropped before the DataFrame is returned.

#### Scenario: Regime warm-up rows dropped
- **WHEN** regime features are included and their warm-up period extends beyond the Phase 2 warm-up period
- **THEN** only rows where all selected feature columns are non-NaN are returned
