## ADDED Requirements

### Requirement: Compute realized volatility percentile bucket
The system SHALL compute `vol_percentile` as the rolling 252-bar percentile rank of the 20-bar realized volatility (`rolling_std_20`) at each bar `t`. The result SHALL be bucketed into three integer labels: `0` (low: < 33rd percentile), `1` (medium: 33rd–66th), `2` (high: > 66th).

#### Scenario: Volatility percentile computed
- **WHEN** `compute_regime_features` is called on a DataFrame with at least 252 bars
- **THEN** column `vol_percentile` is present with values in `{0, 1, 2}`, using only data up to bar `t`

#### Scenario: Warm-up rows excluded
- **WHEN** fewer than 252 prior bars exist for a row
- **THEN** `vol_percentile` is NaN for those rows, which are dropped before labeling

### Requirement: Compute trend slope feature
The system SHALL compute `trend_slope` as the OLS slope of the close price over the last 24 bars at each bar `t`, normalized by the rolling 20-bar standard deviation of close (`rolling_std`). This captures the direction and strength of recent trend while being scale-neutral.

#### Scenario: Trend slope computed
- **WHEN** `compute_regime_features` is called on a DataFrame with sufficient history
- **THEN** column `trend_slope` is present with values equal to `OLS_slope(close[t-23:t+1]) / rolling_std_t`

#### Scenario: No future leakage in slope
- **WHEN** trend slope is computed at bar `t`
- **THEN** the slope uses bars `t-23` through `t` only, and `t+1` onward is not accessible

### Requirement: Compute ATR-normalized return
The system SHALL compute `atr_normalized_return` as the bar return at `t` divided by the 14-bar ATR at `t`, providing a volatility-adjusted measure of each bar's price movement.

#### Scenario: ATR-normalized return computed
- **WHEN** `compute_regime_features` is called on a DataFrame with at least 14 prior bars
- **THEN** column `atr_normalized_return` is present with values equal to `return_t / ATR_t`

#### Scenario: ATR-normalized return is leakage-free
- **WHEN** ATR-normalized return is computed at bar `t`
- **THEN** both `return_t` and `ATR_t` use only information available at the close of bar `t`

### Requirement: All regime features use only data at or before bar t
Every regime feature SHALL be computed using only data available at the close of bar `t`. No regime feature may reference any value from bar `t+1` or later.

#### Scenario: Rolling window boundary enforced
- **WHEN** any regime feature is computed
- **THEN** the computation window closes at bar `t` and does not include bar `t+1`

### Requirement: Regime features returned in a DataFrame compatible with existing feature columns
`compute_regime_features` SHALL return the input DataFrame with the regime feature columns added alongside existing feature columns, with NaN warm-up rows dropped.

#### Scenario: Regime features appended to input DataFrame
- **WHEN** `compute_regime_features(df)` is called
- **THEN** the returned DataFrame contains all original columns plus `vol_percentile`, `trend_slope`, and `atr_normalized_return`

#### Scenario: No NaN in regime feature columns
- **WHEN** the returned DataFrame is examined after warm-up drop
- **THEN** `vol_percentile`, `trend_slope`, and `atr_normalized_return` contain no NaN values
