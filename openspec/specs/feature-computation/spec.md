## ADDED Requirements

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

#### Scenario: Z-score undefined during warm-up
- **WHEN** the rolling window has not yet accumulated enough bars (first N-1 rows)
- **THEN** the `zscore` column contains NaN for those rows

### Requirement: Compute bar-over-bar returns
The system SHALL compute the percentage return for each bar as `(close - prev_close) / prev_close`.

#### Scenario: Return computed
- **WHEN** a prior bar exists
- **THEN** the `return` column contains the fractional price change from the previous close

#### Scenario: First bar return
- **WHEN** there is no prior bar
- **THEN** the `return` column contains NaN for the first row

### Requirement: Drop warm-up rows before signal generation
All rows where any derived feature column contains NaN SHALL be dropped before signal generation begins.

#### Scenario: Warm-up rows removed
- **WHEN** feature computation is complete
- **THEN** the DataFrame passed to signal generation contains no NaN values in feature columns

#### Scenario: Minimum viable rows
- **WHEN** warm-up rows are dropped
- **THEN** the resulting DataFrame contains at least 100 rows; otherwise the system raises an error
