This file is a merged representation of the entire codebase, combined into a single document by Repomix.
The content has been processed where content has been compressed (code blocks are separated by ⋮---- delimiter).

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
bot/
  __init__.py
  __main__.py
  config.py
  credentials.py
  features.py
  fetcher.py
  logger.py
  main.py
  signals.py
openspec/
  changes/
    phase-1-signal-bot/
      specs/
        bar-fetching/
          spec.md
        credential-loading/
          spec.md
        dry-run-guard/
          spec.md
        feature-computation/
          spec.md
        run-logging/
          spec.md
        signal-generation/
          spec.md
      .openspec.yaml
      design.md
      proposal.md
      tasks.md
  config.yaml
.env.example
.gitignore
.repomixignore
main.py
README.md
requirements.txt
```

# Files

## File: bot/__init__.py
```python

```

## File: bot/__main__.py
```python

```

## File: bot/config.py
```python
SYMBOL = "BTC/USD"
BAR_LIMIT = 300          # bars to request; enough to survive warm-up + 100 usable rows
ROLLING_WINDOW = 20      # bars used for rolling mean / std
ZSCORE_UPPER = 1.0       # zscore > ZSCORE_UPPER  -> BUY
ZSCORE_LOWER = -1.0      # zscore < ZSCORE_LOWER  -> SELL
MIN_BARS_AFTER_FETCH = 150
MIN_BARS_AFTER_FEATURES = 100
```

## File: bot/credentials.py
```python
def load_credentials() -> tuple[str, str]
⋮----
"""Load Alpaca API credentials from environment (with optional .env support).

    Returns:
        (api_key, secret_key) tuple.

    Raises:
        EnvironmentError: if either required variable is missing.
    """
load_dotenv()  # no-op if .env absent
⋮----
required = ["APCA_API_KEY_ID", "APCA_API_SECRET_KEY"]
missing = [name for name in required if not os.environ.get(name)]
⋮----
# Values are read but never logged
api_key = os.environ["APCA_API_KEY_ID"]
secret_key = os.environ["APCA_API_SECRET_KEY"]
```

## File: bot/features.py
```python
_FEATURE_COLS = ["rolling_mean", "rolling_std", "zscore", "return"]
⋮----
def compute_features(df: pd.DataFrame) -> pd.DataFrame
⋮----
"""Add rolling statistics and drop warm-up (NaN) rows.

    Derived columns added:
        rolling_mean  — rolling mean of close over ROLLING_WINDOW bars
        rolling_std   — rolling std of close over ROLLING_WINDOW bars
        zscore        — (close - rolling_mean) / rolling_std
        return        — bar-over-bar fractional return on close

    Returns:
        DataFrame with feature columns, NaN warm-up rows removed.

    Raises:
        ValueError: if fewer than MIN_BARS_AFTER_FEATURES rows remain.
    """
df = df.copy()
⋮----
# Drop warm-up rows where any feature is undefined
df = df.dropna(subset=_FEATURE_COLS).reset_index(drop=True)
```

## File: bot/fetcher.py
```python
"""Fetch recent closed OHLCV bars for *symbol* from Alpaca.

    Uses a start date anchored ``limit`` hours ago so the request returns a
    full historical window regardless of account tier. The last
    (still-forming) bar is dropped before returning.

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume.
        Rows are sorted ascending by UTC timestamp.

    Raises:
        ValueError: if fewer than MIN_BARS_AFTER_FETCH rows remain after
                    preprocessing.
    """
client = CryptoHistoricalDataClient(api_key=api_key, secret_key=secret_key)
⋮----
# Anchor to limit hours ago so the API returns a full window
start = datetime.now(tz=timezone.utc) - timedelta(hours=limit + 1)
⋮----
request = CryptoBarsRequest(
bars = client.get_crypto_bars(request)
df = bars.df  # MultiIndex (symbol, timestamp)
⋮----
# Flatten MultiIndex produced by alpaca-py
⋮----
df = df.xs(symbol, level="symbol").reset_index()
⋮----
df = df.reset_index()
⋮----
# Keep only the required columns
df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
⋮----
# Cast numeric columns to float64
⋮----
# Normalize timestamps to UTC-aware datetimes
⋮----
# Sort ascending — do not rely on API ordering
df = df.sort_values("timestamp").reset_index(drop=True)
⋮----
# Drop the last incomplete (still-forming) bar
df = df.iloc[:-1].copy()
```

## File: bot/logger.py
```python
def log_bar(row: pd.Series, dry_run: bool) -> None
⋮----
"""Print one structured log line for a single processed bar."""
⋮----
def log_run(df: pd.DataFrame, dry_run: bool) -> None
⋮----
"""Emit one log line per bar in *df*."""
```

## File: bot/main.py
```python
def _resolve_dry_run(args: argparse.Namespace) -> bool
⋮----
"""Determine dry-run mode from CLI flags → env var → default (True)."""
⋮----
env_val = os.environ.get("DRY_RUN", "").strip().lower()
⋮----
return True  # safe default
⋮----
def main() -> None
⋮----
parser = argparse.ArgumentParser(
mode = parser.add_mutually_exclusive_group()
⋮----
args = parser.parse_args()
⋮----
dry_run = _resolve_dry_run(args)
mode_label = "[DRY-RUN]" if dry_run else "[LIVE]"
⋮----
# ── Startup banner ────────────────────────────────────────────────────────
⋮----
# ── Pipeline ──────────────────────────────────────────────────────────────
⋮----
df = fetch_bars(api_key, secret_key)
⋮----
df = compute_features(df)
⋮----
df = generate_signals(df)
⋮----
# ── Execution guard ───────────────────────────────────────────────────────
⋮----
# Order placement is out of scope for Phase 1 — guard is here for future phases.
```

## File: bot/signals.py
```python
def generate_signals(df: pd.DataFrame) -> pd.DataFrame
⋮----
"""Assign a BUY / SELL / HOLD action signal to each bar.

    Rules (strict inequalities — boundary values map to HOLD):
        zscore >  ZSCORE_UPPER  -> BUY
        zscore <  ZSCORE_LOWER  -> SELL
        otherwise               -> HOLD

    Returns:
        DataFrame with an additional ``signal`` column (no NaN values).
    """
df = df.copy()
```

## File: openspec/changes/phase-1-signal-bot/specs/bar-fetching/spec.md
```markdown
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
```

## File: openspec/changes/phase-1-signal-bot/specs/credential-loading/spec.md
```markdown
## ADDED Requirements

### Requirement: Load API credentials from environment
The system SHALL load `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` from the process environment before making any Alpaca API calls.

#### Scenario: Both credentials present
- **WHEN** both `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are set in the environment
- **THEN** the system reads their values and proceeds without error

#### Scenario: API key missing
- **WHEN** `APCA_API_KEY_ID` is not set in the environment
- **THEN** the system raises an error with a message identifying the missing variable and exits before making any API call

#### Scenario: API secret missing
- **WHEN** `APCA_API_SECRET_KEY` is not set in the environment
- **THEN** the system raises an error with a message identifying the missing variable and exits before making any API call

### Requirement: Support .env file for local development
The system SHALL attempt to load a `.env` file from the working directory before reading environment variables, allowing local development without exporting credentials in the shell.

#### Scenario: .env file present
- **WHEN** a `.env` file exists in the working directory containing credential variables
- **THEN** those variables are loaded into the environment and used for the API client

#### Scenario: .env file absent
- **WHEN** no `.env` file exists
- **THEN** the system silently continues, relying on already-set environment variables

### Requirement: Credentials never logged
The system SHALL NOT write API key or secret values to any log output, stdout, or stderr at any log level.

#### Scenario: Startup log
- **WHEN** the application starts and credentials are loaded
- **THEN** the log confirms credentials were loaded (e.g., "Credentials loaded") without printing their values
```

## File: openspec/changes/phase-1-signal-bot/specs/dry-run-guard/spec.md
```markdown
## ADDED Requirements

### Requirement: Dry-run mode prevents order placement
When dry-run mode is enabled, the system SHALL NOT call any Alpaca order placement endpoint under any circumstance.

#### Scenario: Signal triggers no order in dry-run
- **WHEN** dry-run mode is enabled and a BUY or SELL signal is generated
- **THEN** no order is submitted to Alpaca and no order-related API call is made

#### Scenario: Signal logs intent in dry-run
- **WHEN** dry-run mode is enabled and a BUY or SELL signal is generated
- **THEN** the system logs that it would place an order but does not do so

### Requirement: Dry-run mode is enabled by default
The system SHALL default to dry-run mode so that accidental live execution is not possible without an explicit opt-in.

#### Scenario: Default behavior
- **WHEN** the application is run without any execution mode flag
- **THEN** dry-run mode is active and no orders can be placed

### Requirement: Dry-run mode is configurable via CLI flag or environment variable
The system SHALL allow dry-run mode to be explicitly set via a `--dry-run` / `--live` CLI flag or a `DRY_RUN` environment variable.

#### Scenario: Explicit dry-run flag
- **WHEN** the application is started with `--dry-run`
- **THEN** dry-run mode is active regardless of the environment variable value

#### Scenario: Explicit live flag
- **WHEN** the application is started with `--live`
- **THEN** dry-run mode is disabled (live execution mode is active)

#### Scenario: Environment variable override
- **WHEN** `DRY_RUN=true` is set in the environment and no CLI flag is given
- **THEN** dry-run mode is active
```

## File: openspec/changes/phase-1-signal-bot/specs/feature-computation/spec.md
```markdown
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
```

## File: openspec/changes/phase-1-signal-bot/specs/run-logging/spec.md
```markdown
## ADDED Requirements

### Requirement: Emit one log line per processed bar
The system SHALL emit exactly one plain-text log line for each bar that has a computed signal.

#### Scenario: One line per bar
- **WHEN** signal generation completes for N bars
- **THEN** exactly N log lines are emitted to stdout (or the configured output stream)

### Requirement: Log line contains required fields
Each log line SHALL include the following fields in a fixed order: timestamp, close price, signal, zscore, rolling_mean, rolling_std.

#### Scenario: Field presence
- **WHEN** a log line is emitted
- **THEN** it contains timestamp, close, signal, zscore, rolling_mean, and rolling_std values

### Requirement: Consistent decimal precision in log output
Numeric values in log lines SHALL be formatted with fixed decimal precision to ensure consistent output across runs.

#### Scenario: Price precision
- **WHEN** close, rolling_mean, and rolling_std are logged
- **THEN** they are formatted to 2 decimal places

#### Scenario: Z-score precision
- **WHEN** zscore is logged
- **THEN** it is formatted to 4 decimal places

### Requirement: Dry-run mode is marked in log output
When the application runs in dry-run mode, each log line or the startup header SHALL include a visible DRY-RUN marker.

#### Scenario: Dry-run marker present
- **WHEN** dry-run mode is active and a log line is emitted
- **THEN** the line or the preceding startup line contains the text "DRY-RUN"

#### Scenario: No marker in live mode
- **WHEN** dry-run mode is not active
- **THEN** log lines do not contain the "DRY-RUN" marker
```

## File: openspec/changes/phase-1-signal-bot/specs/signal-generation/spec.md
```markdown
## ADDED Requirements

### Requirement: Generate BUY/SELL/HOLD action signals
The system SHALL assign an action signal to each bar based on its z-score value. The signal vocabulary is BUY, SELL, and HOLD.

#### Scenario: BUY signal
- **WHEN** a bar's `zscore` is strictly greater than the upper threshold (default: 1.0)
- **THEN** the signal for that bar is BUY

#### Scenario: SELL signal
- **WHEN** a bar's `zscore` is strictly less than the lower threshold (default: -1.0)
- **THEN** the signal for that bar is SELL

#### Scenario: HOLD signal
- **WHEN** a bar's `zscore` is greater than or equal to the lower threshold and less than or equal to the upper threshold
- **THEN** the signal for that bar is HOLD

### Requirement: Signal thresholds are configurable
Upper and lower z-score thresholds SHALL be defined in a fixed configuration location (e.g., config file or constants module) so they can be changed without modifying signal logic.

#### Scenario: Threshold change
- **WHEN** the upper threshold is changed from 1.0 to 1.5 in the config
- **THEN** BUY signals are only generated for z-scores above 1.5 with no code changes in the signal function

### Requirement: Signal generation is deterministic
Given identical input feature values, the system SHALL always produce the same signal output.

#### Scenario: Reproducibility
- **WHEN** the same DataFrame with the same feature values is passed to signal generation twice
- **THEN** the `signal` column produced is identical in both runs

### Requirement: Signal generation handles at least 100 bars
The signal engine SHALL process a minimum of 100 fully-featured bars without error.

#### Scenario: 100-bar run
- **WHEN** a DataFrame with exactly 100 rows of complete features is passed to signal generation
- **THEN** all 100 rows receive a signal value and no errors are raised
```

## File: openspec/changes/phase-1-signal-bot/.openspec.yaml
```yaml
schema: spec-driven
created: 2026-04-18
```

## File: openspec/changes/phase-1-signal-bot/design.md
```markdown
## Context

Greenfield implementation. No existing application code. The Alpaca Python client (`alpaca-py`) provides the data API. Phase 1 is intentionally scoped to a deterministic rule-based signal pipeline as the testable foundation for future ML phases. Key constraint: output must be fully reproducible given the same input dataset.

## Goals / Non-Goals

**Goals:**
- Establish a working end-to-end pipeline: credentials → data → features → signal → log
- Ensure reproducible output for the same input dataset
- Enforce a hard dry-run execution gate with no order side effects
- Keep the architecture flat and readable (no over-abstraction for phase 1)

**Non-Goals:**
- Machine learning, model training, or inference
- Multi-symbol or multi-timeframe support
- Portfolio optimization or position sizing
- Live order placement (deferred to future phase)
- Deployment, containerization, or scheduling
- Advanced risk engine or stop-loss logic

## Decisions

### D1: Action signals (BUY/SELL/HOLD) over state signals (LONG/SHORT/FLAT)

**Chosen**: Action semantics — BUY, SELL, HOLD.

**Rationale**: Action signals represent intent at each bar boundary, making them directly interpretable in logs and future broker integration. State signals (LONG/SHORT/FLAT) describe portfolio position and require tracking prior state to be meaningful. For a stateless phase 1 pipeline this creates unnecessary complexity.

**Alternative considered**: LONG/SHORT/FLAT — rejected because it implies persistent position tracking which is out of scope.

---

### D2: Exclude the last incomplete bar

**Chosen**: Always drop the most recent bar before feature computation.

**Rationale**: The last bar in any real-time fetch is typically still forming. Including it causes non-deterministic results for the same nominal time window across multiple runs. Excluding it makes the dataset stable and reproducible given the same fetch timestamp.

**Alternative considered**: Include all bars — rejected because it breaks the reproducibility acceptance criterion.

---

### D3: Z-score threshold rule for signal generation

**Chosen**: Compute a rolling z-score on close price and apply symmetric upper/lower thresholds to classify each bar.

**Rationale**: Simple, interpretable, deterministic, and parameter-transparent. Threshold values are fixed in config so the same dataset always produces the same signals.

**Alternatives considered**:
- Raw price crossover — too sensitive to absolute price levels across time.
- Percent change threshold — reasonable, but z-score provides automatic normalization.

---

### D4: Plain-text structured log lines

**Chosen**: Each processed bar emits one human-readable log line with a fixed field order.

**Rationale**: Readable in terminal, trivially parseable with `grep` or `awk`, no dependencies. Sufficient for phase 1 where the audience is the developer, not a monitoring system.

**Alternative considered**: JSON structured logging — deferred to a later phase.

---

### D5: Warm-up rows with NaN features are silently dropped

**Chosen**: Rows where rolling statistics are undefined (the initial warm-up window) are excluded from signal generation and logging.

**Rationale**: NaN-based signals are undefined. Dropping these rows ensures the signal loop always operates on fully-defined feature vectors. The fetch size must be large enough that at least 100 fully-computed rows remain after warm-up.

---

### D6: Credentials loaded strictly from environment variables

**Chosen**: `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` loaded via `os.environ` or `.env` file via `python-dotenv`.

**Rationale**: Keeps credentials out of source code and config files. Fails fast with a clear error message if either variable is missing.

## Risks / Trade-offs

- **Fewer than 100 usable bars after warm-up** → Mitigation: validate bar count after dropping incomplete bar and warm-up rows, raise explicit error if count < 100.
- **Alpaca API response ordering** → Mitigation: always sort ascending by timestamp after fetch, do not rely on API sort order.
- **Timezone inconsistency** → Mitigation: normalize all timestamps to UTC immediately after fetch.
- **Threshold boundary equality** → Mitigation: define exact rule in spec (`>` for BUY, `<` for SELL, else HOLD) so boundary-touching values always resolve to HOLD.
- **Float formatting drift in logs** → Mitigation: fix decimal precision for logged fields in the run-logging spec.
```

## File: openspec/changes/phase-1-signal-bot/proposal.md
```markdown
## Why

Alpaca supports crypto trading via a Python client but lacks any tooling for systematic signal generation. Phase 1 establishes a deterministic, reproducible data-to-signal pipeline for BTC/USD so we have a testable foundation before introducing machine learning in later phases.

## What Changes

- Add credential loading from environment variables (API key + secret)
- Add OHLCV bar fetching for BTC/USD via the Alpaca data API, excluding the last incomplete bar
- Add a pandas DataFrame normalization layer with explicit column types and UTC timestamps
- Add a rolling statistics feature layer (mean, std, z-score, returns)
- Add a threshold-based action signal generator producing BUY, SELL, or HOLD
- Add plain-text structured logging of timestamp, price, signal, and derived values per bar
- Add a dry-run execution guard that prevents any order placement

## Capabilities

### New Capabilities

- `credential-loading`: Load and validate Alpaca API credentials from environment variables
- `bar-fetching`: Fetch and normalize recent BTC/USD OHLCV bars from Alpaca, excluding incomplete bar
- `feature-computation`: Compute rolling statistics (mean, std, z-score, returns) on close prices
- `signal-generation`: Generate BUY/SELL/HOLD action signals from derived features using fixed thresholds
- `run-logging`: Emit plain-text log lines containing timestamp, price, signal, and derived values
- `dry-run-guard`: Enforce dry-run mode so no orders are placed during signal generation runs

### Modified Capabilities

## Impact

- **New dependencies**: `alpaca-py`, `pandas`, `python-dotenv` (or `os.environ` only)
- **No existing code affected**: greenfield phase
- **No order placement**: all Alpaca trade endpoints are out of scope
- **No ML, multi-symbol, portfolio, or deployment concerns** in this phase
```

## File: openspec/changes/phase-1-signal-bot/tasks.md
```markdown
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
```

## File: openspec/config.yaml
```yaml
schema: spec-driven

# Project context (optional)
# This is shown to AI when creating artifacts.
# Add your tech stack, conventions, style guides, domain knowledge, etc.
# Example:
#   context: |
#     Tech stack: TypeScript, React, Node.js
#     We use conventional commits
#     Domain: e-commerce platform

# Per-artifact rules (optional)
# Add custom rules for specific artifacts.
# Example:
#   rules:
#     proposal:
#       - Keep proposals under 500 words
#       - Always include a "Non-goals" section
#     tasks:
#       - Break tasks into chunks of max 2 hours
```

## File: .env.example
```
APCA_API_KEY_ID=your_api_key_here
APCA_API_SECRET_KEY=your_secret_key_here
# Optional: set to "true" to force dry-run mode regardless of CLI flag
# DRY_RUN=true
```

## File: .gitignore
```
*.vscode/*
*.env
```

## File: .repomixignore
```
# Dev tooling
.vscode/
.idea/

# CI/CD
.github/

# Git internals
.git/

# Python cache
__pycache__/
*.pyc

# Logs / temp
logs/
tmp/

# Dependencies
node_modules/

# Others
.env
LICENSE
```

## File: main.py
```python

```

## File: requirements.txt
```
alpaca-py
pandas
python-dotenv
```

## File: README.md
```markdown
# alapac-ml-crypto-project
Alpaca crypto trading toy project
```
