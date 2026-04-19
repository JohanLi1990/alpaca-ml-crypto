## MODIFIED Requirements

### Requirement: Compute realized volatility percentile via regime module
When `compute_features` is called with `extended=True` alongside the regime feature pipeline, the system SHALL support an optional `regime=True` parameter that calls `compute_regime_features` to append `vol_percentile`, `trend_slope`, and `atr_normalized_return` to the output DataFrame. When `timeframe="daily"` is specified, the regime module SHALL use daily-scaled lookback windows: `vol_percentile` uses a 60-bar rolling window, `trend_slope` uses a 10-bar window, and `atr_normalized_return` uses a 14-bar ATR.

#### Scenario: Regime features appended when regime=True (hourly, default)
- **WHEN** `compute_features(df, extended=True, regime=True)` is called without a `timeframe` argument
- **THEN** the returned DataFrame contains all 9 Phase 2 feature columns plus `vol_percentile`, `trend_slope`, and `atr_normalized_return` using 252-bar, 24-bar, and 14-bar windows respectively

#### Scenario: Regime features appended with daily-scaled windows
- **WHEN** `compute_features(df, extended=True, regime=True, timeframe="daily")` is called
- **THEN** the returned DataFrame contains the same set of feature columns but computed with 60-bar, 10-bar, and 14-bar windows for `vol_percentile`, `trend_slope`, and `atr_normalized_return` respectively

#### Scenario: Existing Phase 2 features unchanged
- **WHEN** `compute_features(df, extended=True, regime=False)` is called (default)
- **THEN** the returned DataFrame contains exactly the same 9 columns as Phase 2, with no change in behavior

### Requirement: No NaN values in any feature column after warm-up drop
After computing all features (base + extended + regime), all rows where any selected feature column is NaN SHALL be dropped before the DataFrame is returned.

#### Scenario: Regime warm-up rows dropped
- **WHEN** regime features are included and their warm-up period extends beyond the Phase 2 warm-up period
- **THEN** only rows where all selected feature columns are non-NaN are returned
