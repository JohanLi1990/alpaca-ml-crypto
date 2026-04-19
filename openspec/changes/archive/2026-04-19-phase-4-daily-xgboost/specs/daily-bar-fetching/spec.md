## ADDED Requirements

### Requirement: Fetch OHLCV bars at daily timeframe for a configurable symbol and date range
`fetch_bars_range` SHALL support `TimeFrame.Day` as a valid timeframe argument. When called with `timeframe=TimeFrame.Day`, it SHALL return daily OHLCV bars for the specified symbol between `start` and `end` dates.

#### Scenario: Daily bars returned for BTC/USD
- **WHEN** `fetch_bars_range("BTC/USD", TimeFrame.Day, start=<2-years-ago>, end=<today>)` is called
- **THEN** the returned DataFrame contains one row per calendar day where crypto markets were open, with columns: timestamp, open, high, low, close, volume

#### Scenario: At least 600 bars available for walk-forward harness
- **WHEN** a 2-year daily lookback is requested
- **THEN** the returned DataFrame contains at least 600 rows after preprocessing (sufficient for 3 walk-forward folds at train=400/val=100/test=100)

### Requirement: Provide a daily-bar convenience wrapper with 2-year default lookback
The system SHALL expose a `fetch_daily_bars(symbol, days_back=730)` function in `bot/data/fetcher.py` that calls `fetch_bars_range` with `TimeFrame.Day` and a date range anchored to today minus `days_back` calendar days.

#### Scenario: Default 2-year lookback
- **WHEN** `fetch_daily_bars("BTC/USD")` is called with no date arguments
- **THEN** the system fetches daily bars starting approximately 730 days before today
- **AND** the result is equivalent to calling `fetch_bars_range("BTC/USD", TimeFrame.Day, start=today-730d, end=today)`

#### Scenario: Incomplete (partial) bar excluded
- **WHEN** the fetch response includes a bar for today's date and the current time is before market close
- **THEN** the final row in the returned DataFrame is dropped, preserving the Phase 1 exclude-last-bar convention
