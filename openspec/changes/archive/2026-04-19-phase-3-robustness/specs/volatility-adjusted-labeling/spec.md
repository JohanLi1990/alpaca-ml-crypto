## ADDED Requirements

### Requirement: Compute ATR as the volatility normalization denominator
The system SHALL compute a 14-bar Average True Range (ATR) at each bar `t` using only close prices available at or before bar `t`. ATR is defined as the rolling 14-bar mean of `abs(close_t - close_{t-1})`.

#### Scenario: ATR computed without future leakage
- **WHEN** ATR is computed on a bar sequence
- **THEN** the ATR value at row `t` uses only bars `t-13` through `t`, and the value is strictly positive

#### Scenario: ATR warm-up rows excluded
- **WHEN** fewer than 14 prior bars exist for a row
- **THEN** the ATR is NaN for those warm-up rows, which are dropped before labeling

### Requirement: Normalize forward return by ATR to produce a volatility-adjusted signal
The system SHALL compute a volatility-adjusted forward signal as `forward_return_t / ATR_t` for each bar. This normalized signal SHALL be used for threshold comparison instead of the raw forward return.

#### Scenario: Normalized signal computed
- **WHEN** `make_vol_adjusted_labels` is called on a DataFrame
- **THEN** each bar's normalized signal equals `(close_{t+1} - close_t) / close_t / ATR_t`

#### Scenario: Normalized signal not included in output features
- **WHEN** the labeled dataset is returned
- **THEN** neither `forward_return` nor the normalized signal column is present in the output `X`

### Requirement: Derive quantile thresholds from normalized signal on training data only
The system SHALL compute the 30th and 70th percentile thresholds of the volatility-adjusted signal distribution exclusively from the training split. These thresholds SHALL be returned so they can be applied to any subsequent split without recomputation.

#### Scenario: Thresholds derived from training normalized distribution
- **WHEN** `make_vol_adjusted_labels(df, compute_thresholds=True)` is called on the training split
- **THEN** the function returns `(X, y, lower_threshold, upper_threshold)` where thresholds are computed from the normalized signal distribution of that split

#### Scenario: Thresholds applied to test data using training values
- **WHEN** `make_vol_adjusted_labels(df, lower=lower_threshold, upper=upper_threshold)` is called on the test split
- **THEN** the training-derived thresholds are used with no recomputation on test data

### Requirement: Label bars using volatility-adjusted quantile thresholds
The system SHALL assign binary labels: `1` (long) when the normalized signal exceeds the upper threshold, `0` (flat) when it is below the lower threshold. Bars in the middle band SHALL be excluded.

#### Scenario: Long label assigned for large relative up move
- **WHEN** a bar's normalized forward signal is strictly greater than the upper threshold
- **THEN** the bar is labeled `1`

#### Scenario: Flat label assigned for large relative down move
- **WHEN** a bar's normalized forward signal is strictly less than the lower threshold
- **THEN** the bar is labeled `0`

#### Scenario: Middle-band bars excluded
- **WHEN** a bar's normalized signal falls between the thresholds (inclusive)
- **THEN** that bar is excluded from both `X` and `y`

### Requirement: Minimum labeled fraction guard
The system SHALL raise a warning (not an error) if the labeled fraction of input bars falls below 20%, as this may indicate the ATR thresholds are too tight.

#### Scenario: Adequate labeled fraction
- **WHEN** at least 20% of input bars are labeled after filtering
- **THEN** labeling proceeds silently

#### Scenario: Low labeled fraction warning
- **WHEN** fewer than 20% of input bars are labeled after filtering
- **THEN** a `UserWarning` is raised with a message indicating the labeled fraction and suggesting looser quantile cutoffs

### Requirement: Output aligned (X, y) pair with no NaN
The labeled dataset SHALL be returned as a feature matrix `X` and label vector `y` that are aligned row-for-row with no NaN values in either.

#### Scenario: X and y are aligned
- **WHEN** `make_vol_adjusted_labels` returns `(X, y, ...)`
- **THEN** `X.index` equals `y.index`

#### Scenario: No NaN in y
- **WHEN** the label vector is returned
- **THEN** `y.isna().sum() == 0`
