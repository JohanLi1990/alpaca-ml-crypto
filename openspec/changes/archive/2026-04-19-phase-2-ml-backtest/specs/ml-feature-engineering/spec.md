## ADDED Requirements

### Requirement: Compute lagged returns
The system SHALL compute bar-over-bar fractional return lags for the 3 most recent preceding bars: `return_lag1`, `return_lag2`, `return_lag3`.

#### Scenario: Lagged returns computed
- **WHEN** feature computation runs on a DataFrame with sufficient history
- **THEN** columns `return_lag1`, `return_lag2`, and `return_lag3` are present with values equal to the return shifted by 1, 2, and 3 bars respectively

#### Scenario: Lag warm-up NaN handling
- **WHEN** insufficient prior bars exist for a given row
- **THEN** the lag columns contain NaN for those warm-up rows, which are subsequently dropped

### Requirement: Compute 12-bar momentum
The system SHALL compute `momentum_12h` as the sum of the last 12 bar returns, representing a half-day directional trend.

#### Scenario: Momentum computed
- **WHEN** at least 12 prior bars are available
- **THEN** `momentum_12h` equals the arithmetic sum of returns over the last 12 bars

### Requirement: Compute volume z-score
The system SHALL compute `volume_zscore_20` as the z-score of the `volume` column over a rolling 20-bar window.

#### Scenario: Volume z-score computed
- **WHEN** feature computation runs on a DataFrame with at least 20 bars
- **THEN** `volume_zscore_20` equals `(volume - rolling_mean(volume, 20)) / rolling_std(volume, 20)`

### Requirement: No future leakage in any feature
All features SHALL be computed using only data available at or before bar `t`. No feature at row `t` may reference any value from row `t+1` or later.

#### Scenario: Rolling window boundary
- **WHEN** any rolling or lag feature is computed
- **THEN** the computation window closes at bar `t` and does not include bar `t+1`

### Requirement: Drop all warm-up rows after extended feature set
After computing all new features, all rows where any feature column is NaN SHALL be dropped before labeling or model training.

#### Scenario: All NaN rows removed
- **WHEN** the extended feature computation is complete
- **THEN** the returned DataFrame contains no NaN values in any feature column
