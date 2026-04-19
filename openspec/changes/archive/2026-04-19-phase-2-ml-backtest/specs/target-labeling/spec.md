## ADDED Requirements

### Requirement: Compute forward return for labeling
The system SHALL compute a 1-bar-ahead forward return for each row as `(close_{t+1} - close_t) / close_t`. This forward return is used only for label generation and SHALL NOT be included as a feature.

#### Scenario: Forward return computed
- **WHEN** target labeling runs on a feature DataFrame
- **THEN** a temporary `forward_return` column is computed and used solely for threshold comparison

#### Scenario: Forward return not in output features
- **WHEN** the labeled dataset is returned
- **THEN** the `forward_return` column is not present in the output DataFrame

### Requirement: Compute quantile thresholds from training data only
The system SHALL compute the 30th and 70th percentile of the `forward_return` distribution exclusively from the training split. These thresholds SHALL be returned alongside the labeled DataFrame so they can be applied to the test split without recomputation.

#### Scenario: Thresholds derived from training data
- **WHEN** `make_labels(df, compute_thresholds=True)` is called on the training split
- **THEN** the function returns the labeled DataFrame plus `(lower_threshold, upper_threshold)` computed from that split's forward return distribution

#### Scenario: Thresholds applied to test data
- **WHEN** `make_labels(df, lower=lower_threshold, upper=upper_threshold)` is called on the test split
- **THEN** the same threshold values from training are used, with no recomputation on test data

### Requirement: Label bars using quantile thresholds
The system SHALL assign binary labels: `1` (long) when forward return exceeds the upper threshold, `0` (flat) when it is below the lower threshold. Bars in the middle band SHALL be excluded from the labeled dataset.

#### Scenario: BUY label assigned
- **WHEN** a bar's forward return is strictly greater than the upper (70th percentile) threshold
- **THEN** the bar is labeled `1`

#### Scenario: FLAT label assigned
- **WHEN** a bar's forward return is strictly less than the lower (30th percentile) threshold
- **THEN** the bar is labeled `0`

#### Scenario: Neutral bars excluded
- **WHEN** a bar's forward return falls between the lower and upper thresholds (inclusive)
- **THEN** that bar is removed from the labeled dataset and does not appear in `X` or `y`

### Requirement: Output aligned (X, y) pair
The labeled dataset SHALL be returned as a feature matrix `X` and label vector `y` that are aligned row-for-row, with no NaN values in either.

#### Scenario: X and y are aligned
- **WHEN** `make_labels` returns `(X, y)`
- **THEN** `X.index` equals `y.index` and both have the same number of rows

#### Scenario: No NaN in y
- **WHEN** the label vector is returned
- **THEN** `y.isna().sum() == 0`
