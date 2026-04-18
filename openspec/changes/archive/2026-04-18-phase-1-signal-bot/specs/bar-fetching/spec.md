## ADDED Requirements

### Requirement: Fetch OHLCV bars for BTC/USD
The system SHALL fetch historical OHLCV bars for the BTC/USD symbol from the Alpaca crypto data API.

#### Scenario: Successful fetch
- **WHEN** valid credentials are configured and the Alpaca API is reachable
- **THEN** the system returns a non-empty collection of bars for BTC/USD

#### Scenario: Configurable bar count
- **WHEN** a bar limit is specified (default: 200)
- **THEN** the system requests at least that many bars to ensure at least 100 remain after preprocessing

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
The system SHALL drop the most recent bar from the DataFrame before any feature computation.

#### Scenario: Last bar removed
- **WHEN** the normalized DataFrame is prepared for feature computation
- **THEN** the final row (highest timestamp) is removed so only closed bars are processed

### Requirement: Minimum bar count validation
After dropping the incomplete bar, the system SHALL validate that at least 150 bars remain to allow warm-up rows plus 100 fully-computed rows.

#### Scenario: Sufficient bars
- **WHEN** the cleaned DataFrame contains 150 or more rows
- **THEN** processing continues normally

#### Scenario: Insufficient bars
- **WHEN** the cleaned DataFrame contains fewer than 150 rows
- **THEN** the system raises an error with a message stating the expected and actual bar count, and exits
