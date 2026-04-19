## MODIFIED Requirements

### Requirement: Fetch OHLCV bars for BTC/USD
The system SHALL fetch historical OHLCV bars for a configurable symbol (default: BTC/USD) from the Alpaca crypto data API, over a configurable date range and at a configurable timeframe (default: `TimeFrame.Minute` for Phase 1 live mode, `TimeFrame.Hour` for historical/ML mode).

#### Scenario: Successful fetch with explicit date range
- **WHEN** valid credentials are configured, the Alpaca API is reachable, and `start`/`end` are provided
- **THEN** the system returns a non-empty collection of bars for the specified symbol within that range

#### Scenario: Successful fetch anchored to now (Phase 1 behavior)
- **WHEN** no `start`/`end` are provided and `timeframe=TimeFrame.Minute`
- **THEN** the system requests bars anchored `limit` minutes in the past, preserving Phase 1 behavior

#### Scenario: Configurable bar count
- **WHEN** a bar limit is specified (default: 300)
- **THEN** the system requests at least that many bars to ensure enough remain after preprocessing

### Requirement: Normalize bars into a pandas DataFrame
The system SHALL convert the raw Alpaca response into a pandas DataFrame with the following columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`.

#### Scenario: Column contract
- **WHEN** the fetch response is normalized
- **THEN** the resulting DataFrame contains exactly the columns: timestamp, open, high, low, close, volume with no extra undocumented columns

#### Scenario: Numeric column types
- **WHEN** the DataFrame is constructed
- **THEN** open, high, low, close, and volume columns are cast to float64

### Requirement: Timestamps normalized to UTC
All bar timestamps SHALL be stored as timezone-aware UTC datetime values.

#### Scenario: UTC normalization
- **WHEN** bars are received from Alpaca
- **THEN** all timestamp values in the DataFrame are UTC-aware and consistent

### Requirement: Bars sorted ascending by timestamp
The system SHALL sort the DataFrame by timestamp in ascending order after fetch, regardless of API response ordering.

#### Scenario: Sort enforcement
- **WHEN** bars are fetched and placed into a DataFrame
- **THEN** the rows are ordered from oldest to newest timestamp

### Requirement: Exclude the last incomplete bar
The system SHALL drop the most recent bar from the DataFrame before any feature computation (applicable in live/Phase 1 mode; may be skipped when fetching full historical ranges for training).

#### Scenario: Last bar removed in live mode
- **WHEN** the normalized DataFrame is prepared for live feature computation
- **THEN** the final row (highest timestamp) is removed so only closed bars are processed

### Requirement: Minimum bar count validation
After preprocessing, the system SHALL validate that the returned DataFrame meets a minimum row count appropriate to the calling context (150 for Phase 1 live mode, 500 for Phase 2 historical mode), raising a descriptive error if not.

#### Scenario: Sufficient bars (live mode)
- **WHEN** the cleaned DataFrame contains 150 or more rows in live mode
- **THEN** processing continues normally

#### Scenario: Insufficient bars
- **WHEN** the cleaned DataFrame contains fewer than the required minimum
- **THEN** the system raises a ValueError with a message stating the expected and actual bar count
