## 1. Project Setup

- [x] 1.1 Add `alpaca-py`, `pandas`, and `python-dotenv` to `requirements.txt`
- [x] 1.2 Create top-level package directory `src/` (or `bot/`) with `__init__.py`
- [x] 1.3 Create `config.py` module with rolling window size, z-score thresholds, default bar limit, and symbol constants
- [x] 1.4 Create `.env.example` with placeholder keys `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY`

## 2. Credential Loading

- [x] 2.1 Create `credentials.py` module that loads `.env` via `python-dotenv` then reads `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` from `os.environ`
- [x] 2.2 Raise a descriptive `EnvironmentError` if either variable is missing, naming the missing key
- [x] 2.3 Verify credential values are never included in any log or print statement

## 3. Bar Fetching

- [x] 3.1 Create `fetcher.py` module that initializes the Alpaca `CryptoHistoricalDataClient` using loaded credentials
- [x] 3.2 Implement `fetch_bars(symbol, limit)` that requests OHLCV bars via `CryptoBarsRequest`
- [x] 3.3 Normalize the Alpaca response into a pandas DataFrame with columns: `timestamp`, `open`, `high`, `low`, `close`, `volume`
- [x] 3.4 Cast `open`, `high`, `low`, `close`, `volume` to `float64`
- [x] 3.5 Normalize all timestamps to UTC-aware datetimes and sort ascending by `timestamp`
- [x] 3.6 Drop the last row (most recent incomplete bar) from the DataFrame
- [x] 3.7 Validate that at least 150 rows remain; raise a descriptive error if not

## 4. Feature Computation

- [x] 4.1 Create `features.py` module with `compute_features(df)` function
- [x] 4.2 Add `rolling_mean` column: rolling mean of `close` over configurable window (from `config.py`)
- [x] 4.3 Add `rolling_std` column: rolling std of `close` over the same window
- [x] 4.4 Add `zscore` column: `(close - rolling_mean) / rolling_std`
- [x] 4.5 Add `return` column: `(close - close.shift(1)) / close.shift(1)`
- [x] 4.6 Drop all rows where any feature column is NaN (warm-up rows)
- [x] 4.7 Validate that at least 100 rows remain after dropping NaN rows; raise a descriptive error if not

## 5. Signal Generation

- [x] 5.1 Create `signals.py` module with `generate_signals(df)` function
- [x] 5.2 Add `signal` column: BUY where `zscore > upper_threshold`, SELL where `zscore < lower_threshold`, HOLD otherwise (using thresholds from `config.py`)
- [x] 5.3 Verify no NaN values appear in the `signal` column after generation
- [x] 5.4 Verify signal generation is deterministic: same input always yields same `signal` column

## 6. Logging

- [x] 6.1 Create `logger.py` module with `log_bar(row, dry_run)` function
- [x] 6.2 Format each line with: `timestamp | close (2dp) | signal | zscore (4dp) | rolling_mean (2dp) | rolling_std (2dp)`
- [x] 6.3 Prefix the startup/header line with `[DRY-RUN]` when dry-run mode is active
- [x] 6.4 Write a `log_run(df, dry_run)` helper that iterates rows and calls `log_bar` for each

## 7. Dry-Run Guard

- [x] 7.1 Implement execution guard in `main.py` that checks dry-run flag before any order logic
- [x] 7.2 Wire `--dry-run` / `--live` CLI flags via `argparse`
- [x] 7.3 Fall back to `DRY_RUN` environment variable when no CLI flag is given
- [x] 7.4 Default to dry-run mode when neither CLI flag nor env var is set
- [x] 7.5 Verify no Alpaca order API call is reachable when dry-run mode is active

## 8. Main Entry Point

- [x] 8.1 Create `main.py` that wires the full pipeline: credentials → fetch → features → signals → log
- [x] 8.2 Print a startup banner showing symbol, bar limit, rolling window, thresholds, and dry-run status
- [x] 8.3 Add a `if __name__ == "__main__"` guard and make the script runnable via `python -m bot` or `python main.py`

## 9. Acceptance Criteria Verification

- [x] 9.1 Run the app and confirm it fetches bars from Alpaca without error
- [x] 9.2 Inspect the DataFrame to confirm all expected OHLCV columns with UTC timestamps are present
- [x] 9.3 Run signal generation on at least 100 bars and confirm no errors
- [x] 9.4 Run twice on the same fetched dataset (saved to CSV) and confirm identical output
- [x] 9.5 Run in dry-run mode and confirm no orders appear in Alpaca paper account activity

## 10. Package Organization Refactor

- [x] 10.1 Group modules by purpose into `bot/data`, `bot/features`, `bot/strategies`, and `bot/utils`
- [x] 10.2 Move data fetch logic to `bot/data/fetcher.py`
- [x] 10.3 Move feature computation logic to `bot/features/rolling.py`
- [x] 10.4 Move signal generation logic to `bot/strategies/zscore.py`
- [x] 10.5 Move credentials and logging logic to `bot/utils/credentials.py` and `bot/utils/logger.py`
- [x] 10.6 Update imports and entrypoints to use the new package structure
