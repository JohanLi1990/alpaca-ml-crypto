## MODIFIED Requirements

### Requirement: Compute rolling mean on close price
The system SHALL compute a rolling arithmetic mean of the `close` column over a fixed configurable window (default: 20 bars).

#### Scenario: Rolling mean computed
- **WHEN** feature computation runs on the DataFrame
- **THEN** a `rolling_mean` column is present containing the rolling mean for each row

### Requirement: Compute rolling standard deviation on close price
The system SHALL compute a rolling standard deviation of the `close` column over the same window as the rolling mean.

#### Scenario: Rolling std computed
- **WHEN** feature computation runs on the DataFrame
- **THEN** a `rolling_std` column is present containing the rolling std for each row

### Requirement: Compute z-score from rolling statistics
The system SHALL compute a z-score for each bar as `(close - rolling_mean) / rolling_std`.

#### Scenario: Z-score computed
- **WHEN** rolling_mean and rolling_std are available for a row
- **THEN** the `zscore` column equals `(close - rolling_mean) / rolling_std`

### Requirement: Compute bar-over-bar returns
The system SHALL compute the percentage return for each bar as `(close - prev_close) / prev_close`.

#### Scenario: Return computed
- **WHEN** a prior bar exists
- **THEN** the `return` column contains the fractional price change from the previous close

### Requirement: Compute extended ML features when requested
The system SHALL compute additional ML feature columns when `extended=True` is passed to `compute_features`: `return_lag1`, `return_lag2`, `return_lag3`, `momentum_12h`, `volume_zscore_20`.

#### Scenario: Extended features computed
- **WHEN** `compute_features(df, extended=True)` is called
- **THEN** all 7 feature columns are present: the 4 base features plus `return_lag1`, `return_lag2`, `return_lag3`, `momentum_12h`, `volume_zscore_20`

#### Scenario: Base features unchanged when extended=False
- **WHEN** `compute_features(df)` is called without `extended=True`
- **THEN** only the original 4 Phase 1 feature columns are returned, preserving Phase 1 behavior

### Requirement: Drop warm-up rows before signal generation
All rows where any derived feature column contains NaN SHALL be dropped before signal generation begins.

#### Scenario: Warm-up rows removed
- **WHEN** feature computation is complete
- **THEN** the DataFrame passed to signal generation contains no NaN values in feature columns

#### Scenario: Minimum viable rows
- **WHEN** warm-up rows are dropped
- **THEN** the resulting DataFrame contains at least 100 rows (Phase 1) or the caller-specified minimum; otherwise the system raises an error
