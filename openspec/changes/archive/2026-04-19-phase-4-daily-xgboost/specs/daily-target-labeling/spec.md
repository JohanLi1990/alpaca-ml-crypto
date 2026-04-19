## ADDED Requirements

### Requirement: Label daily bars using 5-day ATR-normalised forward return
The system SHALL expose a `make_daily_vol_adjusted_labels` function in `bot/features/labeling.py` with the same return-value contract as `make_vol_adjusted_labels`, but using a 5-day forward return horizon and a 14-day ATR computed from daily close prices.

#### Scenario: Labels derived from 5-day forward return
- **WHEN** `make_daily_vol_adjusted_labels(df, compute_thresholds=True)` is called on a daily-bar DataFrame
- **THEN** each bar is labeled using `forward_return_5d / atr_14d` where `forward_return_5d = close[t+5] - close[t]` and `atr_14d` is the 14-day rolling mean of `|close[t] - close[t-1]|`

#### Scenario: Thresholds derived from training data only
- **WHEN** `compute_thresholds=True` is set
- **THEN** the upper and lower quantile thresholds are computed from the training slice and returned as the third and fourth return values
- **AND** no forward data is used in threshold computation

### Requirement: Apply pre-computed thresholds at test time without leakage
`make_daily_vol_adjusted_labels` SHALL accept `lower` and `upper` keyword arguments. When provided, it SHALL apply them directly without recomputing from the input DataFrame.

#### Scenario: Thresholds applied at test time
- **WHEN** `make_daily_vol_adjusted_labels(df_test, lower=lower_thresh, upper=upper_thresh)` is called
- **THEN** only `X_test` and `y_test` are returned (no threshold recalculation)
- **AND** the same label values as would be produced from a matching training-derived threshold are assigned
