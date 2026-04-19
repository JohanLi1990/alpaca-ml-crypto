## ADDED Requirements

### Requirement: Provide volatility-adjusted labeling as an alternative to quantile labeling
The system SHALL expose a `make_vol_adjusted_labels` function in `bot/features/labeling.py` with the same return-value contract as the existing `make_labels` function, but using ATR-normalized forward returns as the labeling signal. The existing `make_labels` function SHALL remain unchanged.

#### Scenario: Vol-adjusted labeling is additive
- **WHEN** `make_vol_adjusted_labels` is imported and called
- **THEN** it does not affect the behavior of `make_labels`

#### Scenario: make_vol_adjusted_labels accepts same split-threshold API
- **WHEN** `make_vol_adjusted_labels(df_train, compute_thresholds=True)` is called
- **THEN** it returns `(X, y, lower_threshold, upper_threshold)` in the same structure as `make_labels`

#### Scenario: make_vol_adjusted_labels threshold passthrough for test split
- **WHEN** `make_vol_adjusted_labels(df_test, lower=lower_threshold, upper=upper_threshold)` is called
- **THEN** it returns `(X, y)` using the provided thresholds without recomputation
