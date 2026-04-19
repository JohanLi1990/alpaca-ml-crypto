## ADDED Requirements

### Requirement: Fetch OHLCV bars over a configurable date range
The system SHALL support fetching historical OHLCV bars for a given symbol between explicit `start` and `end` UTC datetimes, defaulting to the past 6 months when not specified.

#### Scenario: Explicit date range fetch
- **WHEN** `start` and `end` datetimes are provided to the fetch function
- **THEN** the returned DataFrame contains only bars within that date range

#### Scenario: Default 6-month window
- **WHEN** no `start` or `end` is specified
- **THEN** the system anchors `start` to 6 months before the current UTC time and `end` to now

### Requirement: Support configurable bar timeframe
The system SHALL accept a `timeframe` parameter (e.g., `TimeFrame.Hour`, `TimeFrame.Minute`) so callers can fetch data at any supported granularity.

#### Scenario: Hourly bars requested
- **WHEN** `timeframe=TimeFrame.Hour` is passed to the fetch function
- **THEN** the returned DataFrame contains one row per hour

#### Scenario: Default timeframe preserved for Phase 1
- **WHEN** no `timeframe` is specified and the function is called in Phase 1 live-bot mode
- **THEN** behavior defaults to `TimeFrame.Minute` to preserve Phase 1 compatibility

### Requirement: Return a clean, time-indexed DataFrame
The historical fetch SHALL return a DataFrame with no duplicate timestamps, no missing rows within the requested window (gaps in API data are accepted but not inserted), UTC-normalized timestamps, and ascending sort order.

#### Scenario: No duplicate timestamps
- **WHEN** the API response is normalized
- **THEN** each timestamp value appears at most once in the DataFrame

#### Scenario: Ascending sort order
- **WHEN** the DataFrame is returned
- **THEN** rows are sorted from oldest to newest timestamp

### Requirement: Minimum bar count validation for training
After fetching and cleaning, the system SHALL validate that the returned DataFrame contains at least 500 bars when used for ML training, raising a descriptive error if not.

#### Scenario: Sufficient historical bars
- **WHEN** the fetch returns 500 or more bars after deduplication and sort
- **THEN** the DataFrame is returned normally

#### Scenario: Insufficient historical bars
- **WHEN** the fetch returns fewer than 500 bars after deduplication and sort
- **THEN** the system raises a `ValueError` describing the shortfall and suggests widening the date range
